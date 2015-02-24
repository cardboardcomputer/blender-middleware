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
def view_colors(objects, layer_name):
    for obj in objects:
        if obj.type == 'MESH':
            layer = krz.colors.Manager(obj).get_layer(layer_name)
            if layer:
                layer.activate()

def shared_layer_items(scene, context):
    layers = krz.colors.find_shared_layers(context.selected_objects)
    enum = []
    for name in layers:
        enum.append((name, name, name))
    return enum

class ViewColorsMenu(bpy.types.Menu):
    bl_label = "Vertex Colors"
    bl_idname = "CC_MT_view_colors"

    @classmethod
    def poll(cls, context):
        layers = krz.colors.find_shared_layers(context.selected_objects)
        return len(layers)

    def draw(self, context):
        layout = self.layout
        layout.operator_enum('cc.view_colors', 'layer')

class ViewColors(bpy.types.Operator):
    bl_idname = 'cc.view_colors'
    bl_label = 'View Colors'
    bl_options = {'REGISTER', 'UNDO'}

    layer = bpy.props.EnumProperty(
        items=shared_layer_items, name='Color Layer')

    @classmethod
    def poll(cls, context):
        return 'MESH' in [o.type for o in context.selected_objects]

    def invoke(self, context, event):
        shared_layers = krz.colors.find_shared_layers(context.selected_objects)
        default_layer = krz.colors.find_default_layer(context.selected_objects)

        if default_layer and default_layer in shared_layers:
            self.layer = default_layer

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        view_colors(context.selected_objects, self.layer)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(ViewColors.bl_idname, text='View Colors')

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
