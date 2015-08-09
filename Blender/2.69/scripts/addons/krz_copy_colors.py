import bpy
import krz
import mathutils

bl_info = {
    'name': 'Copy Colors',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Copy Colors',
    'description': 'Copy colors from one layer to another',
    'category': 'Cardboard'
}

@krz.ops.editmode
def copy_colors(objects, from_layer, to_layer, select='POLYGON'):
    if from_layer == to_layer:
        return
    for obj in objects:
        if obj.type == 'MESH':
            a = krz.colors.layer(obj, from_layer)
            b = krz.colors.layer(obj, to_layer)
            for i, s in enumerate(b.itersamples()):
                if s.is_selected(select.lower()):
                    s.color = a.samples[i].color
                    s.alpha = a.samples[i].alpha

def shared_layer_items(scene, context):
    layers = krz.colors.find_shared_layers(context.selected_objects)
    enum = [('__NONE__', '', '')]
    for name in layers:
        enum.append((name, name, name))
    return enum

class CopyColors(bpy.types.Operator):
    bl_idname = 'cc.copy_colors'
    bl_label = 'Copy Colors'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=krz.ops.ENUM_SELECT,
        name='Select', default='POLYGON')
    from_layer = bpy.props.EnumProperty(
        items=shared_layer_items, name='From')
    to_layer = bpy.props.EnumProperty(
        items=shared_layer_items, name='To')

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        copy_colors(context.selected_objects, self.from_layer, self.to_layer, self.select)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(CopyColors.bl_idname, text='Copy Colors')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)

if __name__ == "__main__":
    register()
