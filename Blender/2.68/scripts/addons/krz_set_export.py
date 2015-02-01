import bpy
import krz
import mathutils

bl_info = {
    'name': 'Set Export',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Set Export',
    'description': 'Set export info on object',
    'category': 'Cardboard'
}

@krz.ops.editmode
def set_export(objects, layer, colormap):
    for obj in objects:
        if obj.type == 'MESH':
            m = krz.colors.Manager(obj)
            if layer:
                m.set_export_layer(layer)
            if colormap:
                m.set_export_colormap(colormap)

def shared_colormap_items(scene, context):
    colormaps = krz.colors.find_shared_colormaps(context.selected_objects)
    enum = []
    for name in colormaps:
        enum.append((name, name, name))
    return enum

def shared_layer_items(scene, context):
    layers = krz.colors.find_shared_layers(context.selected_objects)
    enum = []
    for name in layers:
        enum.append((name, name, name))
    return enum

class SetExport(bpy.types.Operator):
    bl_idname = 'cc.set_export'
    bl_label = 'Set Export'
    bl_options = {'REGISTER', 'UNDO'}

    layer = bpy.props.EnumProperty(
        items=shared_layer_items, name='Color Layer')

    colormap = bpy.props.EnumProperty(
        items=shared_colormap_items, name='Color Map')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def invoke(self, context, event):
        shared_layers = krz.colors.find_shared_layers(
            context.selected_objects)
        default_layer = krz.colors.find_default_layer(
            context.selected_objects, for_export=True)

        shared_colormaps = krz.colors.find_shared_colormaps(
            context.selected_objects)
        default_colormap = krz.colors.find_default_colormap(
            context.selected_objects, for_export=True)

        if default_layer and default_layer in shared_layers:
            self.layer = default_layer
        if default_colormap and default_colormap in shared_colormaps:
            self.colormap = default_colormap

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        set_export(context.selected_objects, self.layer, self.colormap)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(SetExport.bl_idname, text='Set Export')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)

if __name__ == "__main__":
    register()
