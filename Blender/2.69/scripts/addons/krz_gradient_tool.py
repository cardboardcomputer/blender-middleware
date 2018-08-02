import bpy
import bgl
import krz
import mathutils
from bpy_extras import view3d_utils
from krz_sample_color import sample_color

bl_info = {
    'name': 'Gradient Tool',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 9),
    'location': 'View3D > Specials > Gradient Tool',
    'description': 'Apply gradients on lines/polygon colors',
    'category': 'Cardboard'
}

@krz.ops.editmode
def gradient_colors(
    obj,
    point_a,
    point_b,
    color_a,
    alpha_a,
    color_b,
    alpha_b,
    blend_type,
    blend_method,
    bias, scale,
    select='POLYGON'):

    colors = krz.colors.layer(obj)

    m = mathutils
    p1 = m.Vector(point_a)
    p2 = m.Vector(point_b)
    direction = p2 - p1

    for s in colors.itersamples():
        if not s.is_selected(select.lower()):
            continue

        vert = obj.matrix_world * s.vertex.co
        delta = vert - p1

        if blend_type == 'LINEAR':
            distance = delta.dot(direction.normalized())
            atten = max(min(distance / direction.length, 1), 0)
        if blend_type == 'RADIAL':
            distance = krz.utils.magnitude(delta)
            atten = max(min(distance / direction.length, 1), 0)

        atten = max(min((atten - bias) / scale, 1), 0)

        color = m.Color((0, 0, 0))
        color_ab = m.Color((0, 0, 0))
        color_ab = krz.utils.lerp(color_a, color_b, atten)
        alpha_ab = krz.utils.lerp(alpha_a, alpha_b, atten)

        if blend_method == 'REPLACE':
            s.color = color_ab
            s.alpha = alpha_ab

        if blend_method == 'MIX':
            s.color = krz.utils.lerp(s.color, color_ab, alpha_ab)

        if blend_method == 'MULTIPLY':
            s.color.r *= color_ab.r;
            s.color.g *= color_ab.g;
            s.color.b *= color_ab.b;

        if blend_method == 'ADD':
            s.color.r += color_ab.r;
            s.color.g += color_ab.g;
            s.color.b += color_ab.b;

        if blend_method == 'SUBTRACT':
            s.color.r -= color_ab.r;
            s.color.g -= color_ab.g;
            s.color.b -= color_ab.b;

PROP_SELECT = bpy.props.EnumProperty(
    items=krz.ops.ENUM_SELECT,
    name='Select', default='POLYGON')

PROP_BLEND_TYPE = bpy.props.EnumProperty(
    items=(
        ('LINEAR', 'Linear', 'Linear'),
        ('RADIAL', 'Radial', 'Radial'),),
    name='Type', default='LINEAR')

PROP_BLEND_METHOD = bpy.props.EnumProperty(
    items=(
        ('SUBTRACT', 'Subtract', 'Subtract'),
        ('ADD', 'Add', 'Add'),
        ('MULTIPLY', 'Multiply', 'Multiply'),
        ('MIX', 'Mix', 'Mix'),
        ('REPLACE', 'Replace', 'Replace'),),
    name='Method', default='REPLACE')

PROP_COLOR_A = bpy.props.FloatVectorProperty(
    name="Start Color", subtype='COLOR_GAMMA',
    min=0, max=1, step=1,)

PROP_ALPHA_A = bpy.props.FloatProperty(
    name="Start Alpha", min=0, max=1, step=0.1, default=1)

PROP_COLOR_B = bpy.props.FloatVectorProperty(
    name="End Color", subtype='COLOR_GAMMA',
    min=0, max=1, step=1, default=(1, 1, 1),)

PROP_ALPHA_B = bpy.props.FloatProperty(
    name="End Alpha", min=0, max=1, step=0.1, default=1)

PROP_BIAS = bpy.props.FloatProperty(
    name="Bias", min=0, max=1, step=0.1, default=0)

PROP_SCALE = bpy.props.FloatProperty(
    name="Scale", min=0, max=1, step=0.1, default=1)

# monkeypatch Scene with persisted debris properties
bpy.types.Scene.gradient_select = PROP_SELECT
bpy.types.Scene.gradient_blend_type = PROP_BLEND_TYPE
bpy.types.Scene.gradient_blend_method = PROP_BLEND_METHOD
bpy.types.Scene.gradient_color_a = PROP_COLOR_A
bpy.types.Scene.gradient_alpha_a = PROP_ALPHA_A
bpy.types.Scene.gradient_color_b = PROP_COLOR_B
bpy.types.Scene.gradient_alpha_b = PROP_ALPHA_B
bpy.types.Scene.gradient_bias = PROP_BIAS
bpy.types.Scene.gradient_scale = PROP_SCALE

class GradientPanel(bpy.types.Panel):
    bl_label = "Gradient Options"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout
        data = context.scene

        layout.label('Mask:')

        layout.prop(data, 'gradient_select', '')

        layout.label('Blending:')

        col = layout.box()

        col.prop(data, 'gradient_blend_type')
        col.prop(data, 'gradient_blend_method')
        col.prop(data, 'gradient_bias')
        col.prop(data, 'gradient_scale')

        layout.label('Start/Stop Colors:')

        col = layout.box()

        row = col.row()
        row.prop(data, 'gradient_color_a', '')
        row.prop(data, 'gradient_alpha_a', '')

        row = col.row()
        row.prop(data, 'gradient_color_b', '')
        row.prop(data, 'gradient_alpha_b', '')

bpy.utils.register_class(GradientPanel)

class GradientTool(bpy.types.Operator):
    bl_idname = 'cc.gradient_tool'
    bl_label = 'Gradient Tool'
    bl_options = {'REGISTER', 'UNDO', 'PRESET'}

    select = PROP_SELECT
    blend_type = PROP_BLEND_TYPE
    blend_method = PROP_BLEND_METHOD
    color_a = PROP_COLOR_A
    alpha_a = PROP_ALPHA_A
    color_b = PROP_COLOR_B
    alpha_b = PROP_ALPHA_B
    bias = PROP_BIAS
    scale = PROP_SCALE

    point_a = bpy.props.FloatVectorProperty(
        name='Start Point', default=(0.0, 0.0, 0.0))
    point_b = bpy.props.FloatVectorProperty(
        name='End Point', default=(0.0, 0.0, 0.0))

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def __init__(self):
        self._draw_3d = None
        self._draw_2d = None
        self.mouse_a = (0, 0)
        self.mouse_b = (0, 0)
        self.mouse_now = (0, 0)
        self.started = False

    def __del__(self):
        self.del_viewport_handler()

    def draw(self, context):
        layout = self.layout

        layout.label('Mask:')

        layout.prop(self, 'select', '')

        layout.label('Blending:')

        col = layout.box()

        col.prop(self, 'blend_type')
        col.prop(self, 'blend_method')
        col.prop(self, 'bias')
        col.prop(self, 'scale')

        layout.label('Start/Stop Colors:')

        col = layout.box()

        row = col.row()
        row.prop(self, 'color_a', '')
        row.prop(self, 'alpha_a', '')

        row = col.row()
        row.prop(self, 'color_b', '')
        row.prop(self, 'alpha_b', '')

    def execute(self, context):
        gradient_colors(
            context.active_object,
            self.point_a, self.point_b,
            self.color_a, self.alpha_a,
            self.color_b, self.alpha_b,
            self.blend_type, self.blend_method,
            self.bias, self.scale,
            self.select)

        theme = context.user_preferences.themes[0].view_3d
        theme.face_select[3] = self.face_select
        theme.editmesh_active[3] = self.editmesh_active
        context.area.tag_redraw()

        context.scene.gradient_select = self.select
        context.scene.gradient_blend_type = self.blend_type
        context.scene.gradient_blend_method = self.blend_method
        context.scene.gradient_color_a = self.color_a
        context.scene.gradient_alpha_a = self.alpha_a
        context.scene.gradient_color_b = self.color_b
        context.scene.gradient_alpha_b = self.alpha_b
        context.scene.gradient_bias = self.bias
        context.scene.gradient_scale = self.scale

        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene

        self.select = scene.gradient_select
        self.blend_type = scene.gradient_blend_type
        self.blend_method = scene.gradient_blend_method
        self.color_a = scene.gradient_color_a
        self.alpha_a = scene.gradient_alpha_a
        self.color_b = scene.gradient_color_b
        self.alpha_b = scene.gradient_alpha_b
        self.bias = scene.gradient_bias
        self.scale = scene.gradient_scale

        theme = context.user_preferences.themes[0].view_3d
        self.face_select = theme.face_select[3]
        self.editmesh_active = theme.editmesh_active[3]
        theme.face_select[3] = 0
        theme.editmesh_active[3] = 0
        context.area.tag_redraw()

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        if self._draw_3d is None:
            self.add_viewport_handler(context)

        context.area.tag_redraw()
        context.window.cursor_set('CROSSHAIR')

        region = bpy.context.region
        region_3d = bpy.context.space_data.region_3d
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)

        self.mouse_now = mouse_pos

        direction = view3d_utils.region_2d_to_vector_3d(region, region_3d, mouse_pos)
        endpoint = view3d_utils.region_2d_to_location_3d(region, region_3d, mouse_pos, region_3d.view_location)

        if region_3d.is_perspective:
            origin = endpoint - direction * region_3d.view_distance
            farpoint = origin + direction * 1000
        else:
            origin = endpoint + direction * region_3d.view_distance
            farpoint = origin - direction * 1000

        if event.ctrl:
            result, obj, matrix, location, normal = context.scene.ray_cast(origin, farpoint)
            if result:
                endpoint = location

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.started = True
            self.point_a = endpoint
            self.mouse_a = mouse_pos
            self.mouse_b = mouse_pos

        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            if event.shift:
                self.color_b = sample_color(context, event)
            else:
                self.color_a = sample_color(context, event)

        if event.type == 'MOUSEMOVE':
            self.point_b = endpoint
            self.mouse_b = mouse_pos

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.point_b = endpoint
            self.mouse_b = mouse_pos
            if self.mouse_a != self.mouse_b:
                self.execute(context)
            self.modal_cleanup(context, event)
            return {'FINISHED'}

        if event.type == 'ESC' or event.type == 'RIGHTMOUSE':
            self.modal_cleanup(context, event)
            return {'CANCELLED'}

        return {'RUNNING_MODAL'}

    def modal_cleanup(self, context, event):
        self.del_viewport_handler()
        context.window.cursor_set('DEFAULT')

        theme = context.user_preferences.themes[0].view_3d
        theme.face_select[3] = self.face_select
        theme.editmesh_active[3] = self.editmesh_active
        context.area.tag_redraw()

    def draw_viewport_2d(self, context):
        bgl.glPushAttrib(
            bgl.GL_DEPTH_BUFFER_BIT |
            bgl.GL_LINE_BIT |
            bgl.GL_COLOR_BUFFER_BIT |
            bgl.GL_CURRENT_BIT)

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glDepthFunc(bgl.GL_ALWAYS)
        bgl.glLineWidth(1)

        if self.started:
            ax, ay = self.mouse_a
            bx, by = self.mouse_b

            bgl.glBegin(bgl.GL_LINES)

            bgl.glColor4f(0, 0, 0, 1)
            bgl.glVertex2f(ax + 1, ay)
            bgl.glVertex2f(bx + 1, by)
            bgl.glVertex2f(ax - 1, ay)
            bgl.glVertex2f(bx - 1, by)
            bgl.glVertex2f(ax, ay + 1)
            bgl.glVertex2f(bx, by + 1)
            bgl.glVertex2f(ax, ay - 1)
            bgl.glVertex2f(bx, by - 1)

            bgl.glColor4f(1, 1, 1, 1)
            bgl.glVertex2f(ax, ay)
            bgl.glVertex2f(bx, by)

            bgl.glEnd()

        mx, my = self.mouse_now
        my -= 16

        bgl.glBegin(bgl.GL_QUADS)
        bgl.glColor3f(0, 0, 0)
        bgl.glVertex2f(mx - 9, my - 8)
        bgl.glVertex2f(mx, my + 1)
        bgl.glVertex2f(mx + 9, my - 8)
        bgl.glVertex2f(mx, my - 17)
        bgl.glEnd()

        bgl.glBegin(bgl.GL_TRIANGLES)
        bgl.glColor3f(*self.color_a)
        bgl.glVertex2f(mx - 8, my - 8)
        bgl.glVertex2f(mx, my)
        bgl.glVertex2f(mx, my - 16)
        bgl.glEnd()

        bgl.glBegin(bgl.GL_TRIANGLES)
        bgl.glColor3f(*self.color_b)
        bgl.glVertex2f(mx, my)
        bgl.glVertex2f(mx + 8, my - 8)
        bgl.glVertex2f(mx, my - 16)
        bgl.glEnd()

        bgl.glPopAttrib();

    def draw_viewport_3d(self, context):
        pass

    def add_viewport_handler(self, context):
        self._draw_3d = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_viewport_3d, (context,), 'WINDOW', 'POST_VIEW')
        self._draw_2d = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_viewport_2d, (context,), 'WINDOW', 'POST_PIXEL')

    def del_viewport_handler(self):
        if self._draw_3d:
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_3d, 'WINDOW')
            self._draw_3d = None
        if self._draw_2d:
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_2d, 'WINDOW')
            self._draw_2d = None

def menu_func(self, context):
    self.layout.operator(GradientTool.bl_idname, text='Gradient Tool')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)

if __name__ == "__main__":
    register()
