import os
import bpy
import krz

from krz_export_lines import (
    Color,
    Vertex,
    Edge,
    Line,
    floats_to_strings,
)

bl_info = {
    'name': 'Export Unity Lines (.cs)',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'File > Import-Export > Unity Lines (.cs)',
    'description': 'Export loose edges of a mesh as Unity GL immediate-mode commands',
    'category': 'Cardboard',
}

def export_unity_lines_cs(
    obj,
    filepath,
    precision=6,
    base_class='Line',
    color_layer=''):

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
        color_layer = krz.colors.Manager(obj).get_export_layer().name

    krz.legacy.upgrade_line_attributes(obj)
    colors = krz.colors.layer(obj, color_layer)

    (min_x, min_y, min_z) = (max_x, max_y, max_z) = obj.data.vertices[0].co

    for i, v in enumerate(obj.data.vertices):
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

        cd = colors.samples[v.index]
        color = Color(cd.color.r, cd.color.g, cd.color.b, cd.alpha)

        vertices.append(Vertex(i, v.co, color, (0, 0, 0)))

    for edge in obj.data.edges:
        a = vertices[edge.vertices[0]]
        b = vertices[edge.vertices[1]]
        edges.append(Edge(a, b))

    while edges:
        line = Line(edges.pop(0))
        edges = line.consume(edges)
        lines.append(line)

    with open(filepath, 'w') as fp:
        class_name = os.path.basename(filepath)[:-3]
        fp.write('using UnityEngine;\n\n')
        fp.write('public class %s : %s {\n' % (class_name, base_class))

        min_x, min_y, min_z = floats_to_strings((-min_x, min_y, min_z), precision)
        max_x, max_y, max_z = floats_to_strings((-max_x, max_y, max_z), precision)

        fp.write('  public override Vector3 GetMinPoint()\n')
        fp.write('  {\n')
        fp.write('    return new Vector3(%sF, %sF, %sF);\n' % (min_x, min_y, min_z))
        fp.write('  }\n\n')

        fp.write('  public override Vector3 GetMaxPoint()\n')
        fp.write('  {\n')
        fp.write('    return new Vector3(%sF, %sF, %sF);\n' % (max_x, max_y, max_z))
        fp.write('  }\n\n')

        fp.write('  public override void OnDrawLines()\n')
        fp.write('  {\n')
        fp.write('    GL.Begin(GL.LINES);\n')

        color = None
        last_vertex = None
        for line in lines:
            for i in range(len(line.vertices) - 1):
                vertices = [line.vertices[i], line.vertices[i + 1]]
                for vertex in vertices:
                    if vertex.color != color:
                        color = vertex.color
                        r, g, b, a = floats_to_strings(color, precision)
                        fp.write('      GL.Color(new Color(%sF, %sF, %sF, %sF));\n' % (r, g, b, a))
                    if export_colormap and last_vertex != vertex:
                        u = int(vertex.index % map_size) / map_size + bias
                        v = int(vertex.index / map_size) / map_size + bias
                        u, v = floats_to_strings((u, v), precision)
                        fp.write('      GL.TexCoord2(%sF, %sF);\n' % (u, v))
                        last_vertex = vertex
                    x, y, z = floats_to_strings((-vertex.co.x, vertex.co.y, vertex.co.z), precision)
                    fp.write('      GL.Vertex3(%sF, %sF, %sF);\n' % (x, y, z))

        fp.write('    GL.End();\n')
        fp.write('  }\n')
        fp.write('}\n')

class UnityCsLineExporter(bpy.types.Operator):
    bl_idname = 'cc.export_unity_lines_cs'
    bl_label = 'Export Unity C# Lines'

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
    base_class = bpy.props.StringProperty(
        name="Base Unity Class",
        description="The base Unity class to extend",
        default="Line")
    color_layer = bpy.props.StringProperty(
        name='Color Layer', default='')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        export_unity_lines_cs(
            context.active_object,
            self.filepath,
            self.precision,
            self.base_class,
            self.color_layer)
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = bpy.path.ensure_ext(bpy.data.filepath, ".cs")
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_import(self, context):
    self.layout.operator(UnityCsLineExporter.bl_idname, text="Unity Lines (.cs)")

def menu_export(self, context):
    self.layout.operator(UnityCsLineExporter.bl_idname, text="Unity Lines (.cs)")

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
