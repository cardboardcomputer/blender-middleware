import bpy
import krz

bl_info = {
    'name': 'Adjust HSV',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Adjust HSV',
    'description': 'HSV vertex color adjustment of the selected faces',
    'category': 'Cardboard'
}

@krz.ops.editmode
def adjust_hsv(obj, h, s, v, multiply=False, select='POLYGON'):
    colors = krz.colors.layer(obj)
    for sample in colors.itersamples():
        if sample.is_selected(select.lower()):
            sample.color.h += h
            sample.color.s += s
            if multiply:
                sample.color.v *= (v * 0.5 + 0.5) * 2
            else:
                sample.color.v += v

class AdjustHsv(bpy.types.Operator):
    bl_idname = 'cc.adjust_hsv'
    bl_label = 'Adjust HSV'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=krz.ops.ENUM_SELECT,
        name='Select', default='POLYGON')
    h = bpy.props.FloatProperty(name='Hue', min=-1, max=1, step=1)
    s = bpy.props.FloatProperty(name='Saturation', min=-1, max=1, step=1)
    v = bpy.props.FloatProperty(name='Value', min=-1, max=1, step=1)
    multiply = bpy.props.BoolProperty(name='Multiply Value', default=False)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def __init__(self):
        context = bpy.context
        if context.mode == 'EDIT_MESH':
            vertex, edge, face = context.tool_settings.mesh_select_mode
            self.select = 'VERTEX'
            if face and not vertex:
                self.select = 'POLYGON'

    def execute(self, context):
        adjust_hsv(context.active_object, self.h, self.s, self.v, self.multiply, self.select)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(AdjustHsv.bl_idname, text='Adjust HSV')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()
