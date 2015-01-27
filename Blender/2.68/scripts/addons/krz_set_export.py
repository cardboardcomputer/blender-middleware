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

def set_export(obj, color_layer, color_map):
    m = krz.colors.Manager(obj)
    m.set_export_layer(color_layer)
    m.set_export_colormap(color_map)

def obj_color_items(scene, context):
    obj = context.active_object
    enum = []
    for o in krz.colors.Manager(obj).list_layers():
        if not o.endswith('.Alpha'):
            enum.append((o, o, o))
    return enum

def obj_colormap_items(scene, context):
    obj = context.active_object
    enum = []
    m = krz.colors.Manager(obj)
    keys = m.meta.get('colormaps', {}).keys()
    for o in keys:
        enum.append((o, o, o))
    return enum

class SetExport(bpy.types.Operator):
    bl_idname = 'cc.set_export'
    bl_label = 'Set Export'
    bl_options = {'REGISTER', 'UNDO'}

    color_layer = bpy.props.EnumProperty(
        items=obj_color_items, name='Color Layer')

    color_map = bpy.props.EnumProperty(
        items=obj_colormap_items, name='Color Map')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def invoke(self, context, event):
        m = krz.colors.Manager(context.active_object)

        export_layer = m.get_export_layer()
        if export_layer:
            self.color_layer = export_layer.name

        export_map = m.get_export_colormap()
        if export_map:
            self.color_map = export_map.name

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        set_export(context.active_object, self.color_layer, self.color_map)
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
