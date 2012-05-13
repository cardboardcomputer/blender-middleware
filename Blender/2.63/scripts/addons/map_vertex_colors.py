import bpy

bl_info = {
    'name': 'Map Vertex Colors',
    'author': 'Tamas Kemenczy',
    'version': (0, 1),
    'blender': (2, 6, 1),
    'location': 'View3D > Specials > Map Vertex Colors',
    'description': 'Bake vertex colors to active uv texture image',
    'category': 'Mesh'
}

def map_vertex_colors(obj, index=0):
    image = obj.data.uv_textures.active.data[0].image
    width = image.size[0]
    pixels = image.pixels
    colors = obj.data.vertex_colors.active.data
    stride = int(image.depth / 8)
    offset = ((int((len(colors) - 1) / width)) * width * stride) * index

    for i, c in enumerate(colors):
        p = offset + i * stride
        image.pixels[p + 0] = c.color.r
        image.pixels[p + 1] = c.color.g
        image.pixels[p + 2] = c.color.b

class MapVertexColors(bpy.types.Operator):
    bl_idname = 'mesh.map_vertex_colors'
    bl_label = 'Map Vertex Colors'
    bl_options = {'REGISTER', 'UNDO'}

    index = bpy.props.IntProperty(name='Index', default=0)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        map_vertex_colors(context.active_object, self.index)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(MapVertexColors.bl_idname, text='Map Vertex Colors')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)

if __name__ == "__main__":
    register()
