import bpy
import math

bl_info = {
    'name': 'Map Loose Vertex Colors',
    'author': 'Tamas Kemenczy',
    'version': (0, 1),
    'blender': (2, 6, 3),
    'location': 'View3D > Specials > Map Loose Vertex Colors',
    'description': 'Bake vertex colors to active uv texture image',
    'category': 'Mesh'
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

def get_loose_vertex_color(obj, vertex):
    if 'red' in obj.vertex_groups:
        red = obj.vertex_groups['red']
    else:
        return
    if 'green' in obj.vertex_groups:
        green = obj.vertex_groups['green']
    else:
        return
    if 'blue' in obj.vertex_groups:
        blue = obj.vertex_groups['blue']
    else:
        return
    if 'alpha' in obj.vertex_groups:
        alpha = obj.vertex_groups['alpha']
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

def map_loose_vertex_colors(obj, image_name, index=0):
    vertices = obj.data.vertices;
    image = bpy.data.images[image_name]
    width = image.size[0]
    pixels = image.pixels
    stride = int(image.depth / 8)
    offset = int(math.ceil(len(vertices) / width) * width * stride * index)

    for i, v in enumerate(vertices):
        color = get_loose_vertex_color(obj, v)
        if color is None:
            color = Color(1, 1, 1, 1)
        p = offset + i * stride
        image.pixels[p + 0] = color.r
        image.pixels[p + 1] = color.g
        image.pixels[p + 2] = color.b
        if stride == 4:
            image.pixels[p + 3] = color.a

class MapLooseVertexColors(bpy.types.Operator):
    bl_idname = 'mesh.map_loose_vertex_colors'
    bl_label = 'Map Loose Vertex Colors'
    bl_options = {'REGISTER', 'UNDO'}

    image = bpy.props.StringProperty(name='Image name')
    index = bpy.props.IntProperty(name='Index', default=0)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        map_loose_vertex_colors(context.active_object, self.image, self.index)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(MapLooseVertexColors.bl_idname, text='Map Loose Vertex Colors')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)

if __name__ == "__main__":
    register()
