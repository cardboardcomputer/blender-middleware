import bpy
import krz
import mathutils

bl_info = {
    'name': 'Sample Color',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 9),
    'location': 'View3D > Specials > Sample Color',
    'description': 'Hand-sample color on lines and polygons',
    'category': 'Cardboard'
}

@krz.ops.editmode
def sample_color(context, event, ray_max=1000.0):
    result = krz.utils.find(context, event, 10000)
    if result is not None:
        obj, origin, target = result
        if obj.data.vertex_colors.active:
            with krz.colors.Sampler(obj) as sampler:
                return  sampler.raycast(origin, target)
    return mathutils.Color((0, 0, 0))

@krz.ops.editmode
def set_colors(obj, color, alpha=None, select='POLYGON'):
    colors = krz.colors.layer(obj)

    for sample in colors.itersamples():
        if sample.is_selected(select.lower()):
            sample.color = color
            if alpha is not None:
                sample.alpha = alpha

class SampleColor(bpy.types.Operator):
    bl_idname = 'cc.sample_color'
    bl_label = 'Sample Color'
    bl_options = {'REGISTER', 'UNDO'}

    def update_color(self, context):
        self.hex_value = krz.colors.color_to_hex(self.color)

    ref = bpy.props.FloatVectorProperty(
        name="Color", subtype='COLOR_GAMMA',
        min=0, max=1, step=1)
    color = bpy.props.FloatVectorProperty(
        name="Color", subtype='COLOR_GAMMA',
        min=0, max=1, step=1, update=update_color)
    hex_value = bpy.props.StringProperty(
        name="Hex", default='')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def invoke(self, context, event):
        self.color = self.ref = sample_color(context, event)

        wm = context.window_manager
        wm.invoke_props_dialog(self, width=140)

        return {'RUNNING_MODAL'}

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            obj = context.object
            if obj.type == 'MESH':
                vertex, edge, face = context.tool_settings.mesh_select_mode
                select = 'VERTEX'
                if face and not vertex:
                    select = 'POLYGON'
                set_colors(obj, self.color, None, select=select)
                return {'FINISHED'}

        elif context.mode == 'PAINT_VERTEX':
            context.tool_settings.vertex_paint.brush.color = self.color

        return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        layout.template_color_picker(self, 'color', True)

        row = layout.row(align=True)
        r = row.column(align=True)
        r.enabled = False
        r.prop(self, 'ref', '')
        row.prop(self, 'color', '')

        layout.prop(self, 'hex_value', '')

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
