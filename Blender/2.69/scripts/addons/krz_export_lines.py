import os
import bpy
import krz

from krz.export import (
    Color,
    Vertex,
    Edge,
    Line,
    floats_to_strings,
)

bl_info = {
    'name': 'Export Unity Lines (.lines)',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 9),
    'location': 'File > Import-Export > Unity Lines (.lines)',
    'description': 'Export loose edges of a mesh for Unity',
    'category': 'Cardboard',
}

def export_unity_lines(
    obj,
    filepath,
    precision=6,
    color_layer=''):

    krz.legacy.upgrade_line_attributes(obj)

    export_colormap = krz.colors.Manager(obj).get_export_colormap()
    if export_colormap:
        map_size = export_colormap.get_size()
    else:
        map_size = 1
    bias = 1. / map_size * 0.5

    vertices = []
    edges = []
    lines = []

    if not color_layer:
        export_layer = krz.colors.Manager(obj).get_export_layer()
        if export_layer:
            color_layer = export_layer.name
    export_colors = krz.colors.Manager(obj).get_layer(color_layer) is not None

    aux_layer = krz.colors.Manager(obj).get_aux_layer()
    if aux_layer:
        have_aux_colors = True
        aux_layer_name = aux_layer.name
    else:
        have_aux_colors = False

    with krz.utils.modified_mesh(obj) as mesh:

        if export_colors:
            colors = krz.colors.layer(obj, color_layer)
        normals = krz.lines.normals(obj)
        export_normals = normals.exists()

        if have_aux_colors:
            aux_layer = krz.colors.layer(obj, aux_layer_name)

        (min_x, min_y, min_z) = (max_x, max_y, max_z) = mesh.vertices[0].co

        for i, v in enumerate(mesh.vertices):
            if v.co.x < min_x:
                min_x = v.co.x
            if v.co.x > max_x:
                max_x = v.co.x
            if v.co.y < min_y:
                min_y = v.co.y
            if v.co.y > max_y:
                max_y = v.co.y
            if v.co.z < min_z:
                min_z = v.co.z
            if v.co.z > max_z:
                max_z = v.co.z

            if export_colors:
                cd = colors.samples[v.index]
                color = Color(cd.color.r, cd.color.g, cd.color.b, cd.alpha)
            else:
                color = Color(1, 1, 1, 1)
            if have_aux_colors:
                cd = aux_layer.samples[v.index]
                aux_color = Color(cd.color.r, cd.color.g, cd.color.b, cd.alpha)
            else:
                aux_color = None

            if export_normals:
                nd = normals.get(v.index)
                normal = (nd['X'], nd['Y'], nd['Z'])
            else:
                normal = (0, 0, 1)

            vertices.append(Vertex(i, v.co, color, normal, aux_color=aux_color))

        for edge in mesh.edges:
            a = vertices[edge.vertices[0]]
            b = vertices[edge.vertices[1]]
            edges.append(Edge(a, b))

        while edges:
            line = Line(edges.pop(0))
            edges = line.consume(edges)
            lines.append(line)

        with open(filepath, 'w') as fp:
            class_name = os.path.basename(filepath)[:-3]

            for i, vertex in enumerate(vertices):
                x, y, z = floats_to_strings((-vertex.co.x, vertex.co.y, vertex.co.z), precision)
                fp.write('%s %s %s' % (x, y, z))
                if i < len(vertices) - 1:
                    fp.write(' ')
            fp.write('\n')

            for i, vertex in enumerate(vertices):
                r, g, b, a = floats_to_strings((vertex.color.r, vertex.color.g, vertex.color.b, vertex.color.a), precision)
                fp.write('%s %s %s %s' % (r, g, b, a))
                if i < len(vertices) - 1:
                    fp.write(' ')
            fp.write('\n')

            if export_colormap:
                for i, vertex in enumerate(vertices):
                    u = int(vertex.index % map_size) / map_size + bias
                    v = int(vertex.index / map_size) / map_size + bias
                    u, v = floats_to_strings((u, v), precision)
                    fp.write('%s %s' % (u, v))
                    if i < len(vertices) - 1:
                        fp.write(' ')
            elif aux_layer:
                for i, vertex in enumerate(vertices):
                    rgba = vertex.aux_color.r, vertex.aux_color.g, vertex.aux_color.b, vertex.aux_color.a
                    u, v = krz.colors.rgba_to_uv(rgba)
                    fp.write('%s %s' % (u, v))
                    if i < len(vertices) - 1:
                        fp.write(' ')
            else:
                fp.write(' '.join(['0'] * (len(vertices) * 2)))
            fp.write('\n')

            indices = []
            for line in lines:
                for i in range(len(line.vertices) - 1):
                    indices.extend([line.vertices[i].index, line.vertices[i + 1].index])
            fp.write(' '.join(map(str, indices)))
            fp.write('\n')

            for i, vertex in enumerate(vertices):
                x, y, z = floats_to_strings((-vertex.normal[0], vertex.normal[1], vertex.normal[2]), precision)
                fp.write('%s %s %s' % (x, y, z))
                if i < len(vertices) - 1:
                    fp.write(' ')

            if aux_layer:
                fp.write('\n')
                for i, vertex in enumerate(vertices):
                    r, g, b, a = floats_to_strings((vertex.aux_color.r, vertex.aux_color.g, vertex.aux_color.b, vertex.aux_color.a), precision)
                    fp.write('%s %s %s %s' % (r, g, b, a))
                    if i < len(vertices) - 1:
                        fp.write(' ')

class UnityLineExporter(bpy.types.Operator):
    bl_idname = 'cc.export_unity_lines'
    bl_label = 'Export Unity Lines'

    filepath = bpy.props.StringProperty(
        subtype='FILE_PATH',)
    check_existing = bpy.props.BoolProperty(
        name="Check Existing",
        description="Check and warn on overwriting existing files",
        default=True,
        options={'HIDDEN'},)
    precision = bpy.props.IntProperty(
        name="Float Precision",
        description="Float precision used for GL commands",
        default=6)
    color_layer = bpy.props.StringProperty(
        name='Color Layer', default='')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        export_unity_lines(
            context.active_object,
            self.filepath,
            self.precision,
            self.color_layer)
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = bpy.path.ensure_ext(bpy.data.filepath, ".lines")
        export_layer = krz.colors.Manager(context.active_object).get_export_layer()
        if export_layer:
            self.color_layer = export_layer.name

        path = os.path.dirname(self.filepath)
        blendname = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
        objname = context.active_object.name
        if objname.endswith('.Lines'):
            objname = objname[:-6]
        elif objname.endswith('Lines'):
            objname = objname[:-5]
        name = '%s%s' % (blendname, objname)
        filename = '%s.lines' % name
        self.filepath = os.path.join(path, filename)

        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_import(self, context):
    self.layout.operator(UnityLineExporter.bl_idname, text="Unity Lines (.lines)")

def menu_export(self, context):
    self.layout.operator(UnityLineExporter.bl_idname, text="Unity Lines (.lines)")

def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_import)
    bpy.types.INFO_MT_file_export.append(menu_export)

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_import)
    bpy.types.INFO_MT_file_export.remove(menu_export)

if __name__ == "__main__":
    register()
