import bpy
import krz
import mathutils

bl_info = {
    'name': 'Set Colors',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Set Colors',
    'description': 'Hand-set colors on lines and polygons',
    'category': 'Cardboard'
}

@krz.ops.editmode
def default_color(obj, select='POLYGON'):
    colors = krz.colors.layer(obj)

    freq = {}
    for sample in colors.itersamples():
        if not sample.is_selected(select.lower()):
            continue

        color = (
            sample.color.r,
            sample.color.g,
            sample.color.b,
            sample.alpha)
        if color not in freq:
            freq[color] = 0
        freq[color] += 1

    freq_items = list(freq.items())
    freq_items.sort(key=lambda c: -c[1])

    if freq_items:
        color = freq_items[0][0]
        return mathutils.Color((color[0], color[1], color[2])), color[3]
    else:
        return None, None

@krz.ops.editmode
def set_colors(obj, color, alpha=None, select='POLYGON'):
    colors = krz.colors.layer(obj)

    for sample in colors.itersamples():
        if sample.is_selected(select.lower()):
            sample.color = color
            if alpha is not None:
                sample.alpha = alpha

class SetColors(bpy.types.Operator):
    bl_idname = 'cc.set_colors'
    bl_label = 'Set Colors'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=krz.ops.ENUM_SELECT,
        name='Select', default='POLYGON')
    color = bpy.props.FloatVectorProperty(
        name="Color", subtype='COLOR_GAMMA',
        min=0, max=1, step=1,)
    alpha = bpy.props.FloatProperty(
        name="Alpha",
        min=0, max=1, step=1, default=1,)

    def __init__(self):
        color, alpha = default_color(bpy.context.active_object)
        if color is not None and alpha is not None:
            self.color = color
            self.alpha = alpha

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def invoke(self, context, event):
        obj = context.object
        if obj.type == 'MESH':
            vertex, edge, face = context.tool_settings.mesh_select_mode
            select = 'VERTEX'
            if face and not vertex:
                select = 'POLYGON'
        self.select = select

        color, alpha = default_color(context.active_object, self.select)
        if color is not None and alpha is not None:
            self.color = color
            self.alpha = alpha

        wm = context.window_manager
        wm.invoke_props_dialog(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        set_colors(context.active_object, self.color, self.alpha, self.select)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(SetColors.bl_idname, text='Set Colors')

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
