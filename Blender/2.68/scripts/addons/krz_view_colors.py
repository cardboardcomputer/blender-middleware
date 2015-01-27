import bpy
import krz

bl_info = {
    'name': 'View Colors',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > View Colors',
    'description': 'Set the active color layer common to all selected objects',
    'category': 'Cardboard'
}

@krz.ops.editmode
def view_colors(objects, color_layer):
    for obj in objects:
        layer = krz.colors.Manager(obj).get_layer(color_layer)
        if layer:
            layer.activate()

def shared_color_layer_items(scene, context):
    setlist = []
    for obj in context.selected_objects:
        if obj.type == 'MESH':
            layers = krz.colors.Manager(obj).list_layers()
            setlist.append(set(layers))
    common = set.intersection(*setlist)
    layers = list(common)
    layers.sort()

    enum = []
    for name in layers:
        enum.append((name, name, name))
    return enum

class ViewColors(bpy.types.Operator):
    bl_idname = 'cc.view_colors'
    bl_label = 'View Colors'
    bl_options = {'REGISTER', 'UNDO'}

    color_layer = bpy.props.EnumProperty(
        items=shared_color_layer_items, name='Color Layer')

    @classmethod
    def poll(cls, context):
        return 'MESH' in [o.type for o in context.selected_objects]

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        view_colors(context.selected_objects, self.color_layer)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(ViewColors.bl_idname, text='View Colors')

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
