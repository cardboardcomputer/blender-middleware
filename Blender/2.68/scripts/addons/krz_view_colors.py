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
        if obj.type == 'MESH':
            layer = krz.colors.Manager(obj).get_layer(color_layer)
            if layer:
                layer.activate()

def get_default_color_layer(objects):
    freq = {}
    for obj in objects:
        if obj.type == 'MESH':
            layer = krz.colors.Manager(obj).get_active_layer(False)
            if not layer:
                continue
            if layer.name not in freq:
                freq[layer.name] = 0
            freq[layer.name] += 1

    freq_items = list(freq.items())
    freq_items.sort(key=lambda c: -c[1])

    if freq_items:
        return freq_items[0][0]
    else:
        return ''

def get_shared_color_layers(objects):
    setlist = []
    for obj in objects:
        if obj.type == 'MESH':
            layers = krz.colors.Manager(obj).list_layers()
            setlist.append(set(layers))
    if not setlist:
        return []
    common = set.intersection(*setlist)
    layers = list(common)
    layers.sort()
    return layers

def shared_color_layer_items(scene, context):
    layers = get_shared_color_layers(context.selected_objects)
    enum = []
    for name in layers:
        enum.append((name, name, name))
    return enum

class ViewColorsMenu(bpy.types.Menu):
    bl_label = "Vertex Colors"
    bl_idname = "CC_MT_view_colors"

    @classmethod
    def poll(cls, context):
        layers = get_shared_color_layers(context.selected_objects)
        return len(layers)

    def draw(self, context):
        layout = self.layout
        layout.operator_enum('cc.view_colors', 'color_layer')

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
        self.color_layer = get_default_color_layer(context.selected_objects)
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
    # bpy.types.VIEW3D_MT_object_specials.append(menu_func)
    # bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    # bpy.types.VIEW3D_MT_object_specials.remove(menu_func)
    # bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()
