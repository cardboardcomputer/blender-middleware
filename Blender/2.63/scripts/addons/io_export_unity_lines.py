import os
import bpy

bl_info = {
    'name': 'Unity Lines (.cs)',
    'author': 'Tamas Kemenczy',
    'version': (0, 1),
    'blender': (2, 6, 3),
    'location': 'File > Import-Export > Unity Lines (.cs)',
    'description': 'Export loose edges of a mesh as Unity GL immediate-mode commands',
    'category': 'Import-Export',
}

class Color(object):
    def __init__(self, r, g, b, a):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def __eq__(self, other):
        return (self.r, self.g, self.b, self.a) == other

    def __iter__(self):
        return iter((self.r, self.g, self.b, self.a))

class Vertex(object):
    def __init__(self, index, co, color):
        self.index = index
        self.co = co
        self.color = color

class Edge(object):
    def __init__(self, a, b):
        self.a = a
        self.b = b

class Line(object):
    def __init__(self, edge):
        self.vertices = [edge.a, edge.b]

    def is_connected(self, edge):
        head = self.vertices[0]
        tail = self.vertices[-1]
        return (head == edge.a or head == edge.b or
                tail == edge.a or tail == edge.b)

    def extend(self, edge):
        if self.is_connected(edge):
            a, b = edge.a, edge.b
            head = self.vertices[0]
            tail = self.vertices[-1]
            if a == head:
                self.vertices.insert(0, b)
            elif b == head:
                self.vertices.insert(0, a)
            elif a == tail:
                self.vertices.append(b)
            else:
                self.vertices.append(a)
            return True
        else:
            return False

    def consume(self, edges):
        consumed = -1
        remaining = list(edges)
        while consumed:
            consumed = 0
            for edge in list(remaining):
                if self.extend(edge):
                    consumed += 1
                    remaining.remove(edge)
        return remaining

def floats_to_strings(floats, precision=6):
    fmt = '%%.%if' % precision
    ret = map(lambda f: (fmt % f).rstrip('0').rstrip('.'), floats)
    ret = map(lambda s: '0' if s == '-0' else s, ret)
    return ret

def get_loose_vertex_color(obj, vertex, index):
    red_name = 'red_%i' % index
    green_name = 'green_%i' % index
    blue_name = 'blue_%i' % index
    alpha_name = 'alpha_%i' % index

    if red_name in obj.vertex_groups:
        red = obj.vertex_groups[red_name]
    else:
        return
    if green_name in obj.vertex_groups:
        green = obj.vertex_groups[green_name]
    else:
        return
    if blue_name in obj.vertex_groups:
        blue = obj.vertex_groups[blue_name]
    else:
        return
    if alpha_name in obj.vertex_groups:
        alpha = obj.vertex_groups[alpha_name]
    else:
        return

    groups = [g.group for g in vertex.groups.values()]
    if (red.index in groups and
        green.index in groups and
        blue.index in groups and
        alpha.index in groups):

        r = red.weight(vertex.index)
        g = green.weight(vertex.index)
        b = blue.weight(vertex.index)
        a = alpha.weight(vertex.index)
        return Color(r, g, b, a)

def export_unity_lines(
    obj,
    filepath,
    precision,
    base_class,
    apply_modifiers,
    export_colors,
    export_map,
    map_size,
    color_index):

    bias = 1. / map_size * 0.5
    vertices = []
    edges = []
    lines = []

    (min_x, min_y, min_z) = (max_x, max_y, max_z) = obj.data.vertices[0].co

    for i, v in enumerate(obj.data.vertices):
        color = get_loose_vertex_color(obj, v, color_index)
        if color is None:
            color = Color(1, 1, 1, 1)
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
        vertices.append(Vertex(i, v.co, color))

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
                    if export_map and last_vertex != vertex:
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

class UnityLineExporter(bpy.types.Operator):
    bl_idname = 'export_mesh.unity_lines'
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
    base_class = bpy.props.StringProperty(
        name="Base Unity Class",
        description="The base Unity class to extend",
        default="Line")
    apply_modifiers = bpy.props.BoolProperty(
        name="Apply Modifiers",
        description="Use transformed mesh data from each object",
        default=True,)
    export_colors = bpy.props.BoolProperty(
        name='Export vertex colors',
        description='Export vertex colors',
        default=True)
    export_map = bpy.props.BoolProperty(
        name='Export vertex data map',
        description='Export vertex data map',
        default=False)
    map_size = bpy.props.IntProperty(
        name='Vertex data map size',
        description='Vertex data map size',
        default=1024)
    color_index = bpy.props.IntProperty(
        name='Color Index', default=0)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        export_unity_lines(
            context.active_object,
            self.filepath,
            self.precision,
            self.base_class,
            self.apply_modifiers,
            self.export_colors,
            self.export_map,
            self.map_size,
            self.color_index)
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = bpy.path.ensure_ext(bpy.data.filepath, ".cs")
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_import(self, context):
    self.layout.operator(UnityLineExporter.bl_idname, text="Unity Lines (.cs)")

def menu_export(self, context):
    self.layout.operator(UnityLineExporter.bl_idname, text="Unity Lines (.cs)")

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
