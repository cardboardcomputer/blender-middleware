import bpy

bl_info = {
    'name': 'Adjust Vertex Colors',
    'author': 'Tamas Kemenczy',
    'version': (0, 1),
    'blender': (2, 6, 1),
    'location': 'View3D > Specials > Adjust Vertex Colors',
    'description': 'HSV vertex color adjustment of the selected faces',
    'category': 'Mesh'
}

def adjust_vertex_colors(obj, h, s, v, multiply_value=False):
    colors = obj.data.vertex_colors.active.data
    for p in obj.data.polygons:
        if p.select:
            for i in p.loop_indices:
                colors[i].color.h += h
                colors[i].color.s += s
                if multiply_value:
                    colors[i].color.v *= (v * 0.5 + 0.5) * 2
                else:
                    colors[i].color.v += v

class AdjustVertexColors(bpy.types.Operator):
    bl_idname = 'mesh.adjust_vertex_colors'
    bl_label = 'Adjust Vertex Colors'
    bl_options = {'REGISTER', 'UNDO'}

    h = bpy.props.FloatProperty(name='Hue', min=-1, max=1, step=1)
    s = bpy.props.FloatProperty(name='Saturation', min=-1, max=1, step=1)
    v = bpy.props.FloatProperty(name='Value', min=-1, max=1, step=1)
    multiply_value = bpy.props.BoolProperty(name='Multiply Value', default=False)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        adjust_vertex_colors(context.active_object, self.h, self.s, self.v, self.multiply_value)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(AdjustVertexColors.bl_idname, text='Adjust Vertex Colors')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)

if __name__ == "__main__":
    register()
