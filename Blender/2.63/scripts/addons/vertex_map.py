import bpy

bl_info = {
    'name': 'Vertex Data Map',
    'author': 'Tamas Kemenczy',
    'version': (0, 1),
    'blender': (2, 6, 3),
    'location': 'View3D > Specials > Vertex Data Map',
    'description': 'Generate vertex data map UV texture',
    'category': 'Mesh'
}

def vertex_data_map(obj, width=1024):
    bias = 1. / width * 0.5
    uv_layer = obj.data.uv_layers.active
    for i, uv in enumerate(uv_layer.data):
        x = int(i % width) / width
        y = int(i / width) / width
        uv.uv.x = x + bias
        uv.uv.y = y + bias

class VertexDataMap(bpy.types.Operator):
    bl_idname = 'mesh.vertex_data_map'
    bl_label = 'Vertex Data Map'
    bl_options = {'REGISTER', 'UNDO'}

    width = bpy.props.IntProperty(name='Width', default=1024)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        vertex_data_map(context.active_object, self.width)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(VertexDataMap.bl_idname, text='Vertex Data Map')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)

if __name__ == "__main__":
    register()
