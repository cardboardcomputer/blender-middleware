import cc
import bpy
import bgl
import bmesh
import math
import mathutils
import mathutils as mu
from bpy_extras import view3d_utils

bl_info = {
    'name': 'Tool: Gradient',
    'author': 'Cardboard Computer',
    'blender': (2, 69, 0),
    'description': 'Apply gradients on lines/polygon colors',
    'category': 'Cardboard'
}

def apply_gradient(gra, obj, select=None):
    point_a = gra.location
    point_b = gra.matrix_world * mu.Vector((0, 0, 1))

    g = gra.data.gradient_settings

    if select is None:
        select = g.select

    gradient_colors(
        obj, point_a, point_b,
        g.color_a, g.alpha_a,
        g.color_b, g.alpha_b,
        g.blend_type, g.blend_method, g.blend_falloff,
        g.bias, g.scale, g.mirror,
        select
    )

def gen_mesh_directional(bm, res=32):
    bm.clear()

    for i in range(res + 1):
        t = i / float(res)
        bm.verts.new(mu.Vector((0, 0, t)))
    for i in range(res):
        v1 = bm.verts[i]
        v2 = bm.verts[i + 1]
        e = bm.edges.new((v1, v2))
    tip = v2
    v1 = bm.verts.new(mu.Vector((0.05, 0, 0.9)))
    v2 = bm.verts.new(mu.Vector((-0.05, 0, 0.9)))
    e = bm.edges.new((tip, v1))
    e = bm.edges.new((tip, v2))

def gen_mesh_radial(bm, res=64):
    bm.clear()

    for i in range(res):
        t = i / float(res)
        x = math.cos(t * math.pi * 2)
        y = math.sin(t * math.pi * 2)
        bm.verts.new(mu.Vector((x, 0, y)))
    for i in range(res - 1):
        v1 = bm.verts[i]
        v2 = bm.verts[i + 1]
        e = bm.edges.new((v1, v2))
    v1 = v2
    v2 = bm.verts[0]
    e = bm.edges.new((v1, v2))

    for i in range(res):
        t = i / float(res)
        x = math.cos(t * math.pi * 2)
        y = math.sin(t * math.pi * 2)
        bm.verts.new(mu.Vector((x, y, 0)))
    for i in range(res, res * 2 - 1):
        v1 = bm.verts[i]
        v2 = bm.verts[i + 1]
        e = bm.edges.new((v1, v2))
    v1 = v2
    v2 = bm.verts[res]
    e = bm.edges.new((v1, v2))

    for i in range(res):
        t = i / float(res)
        x = math.cos(t * math.pi * 2)
        y = math.sin(t * math.pi * 2)
        bm.verts.new(mu.Vector((0, x, y)))
    for i in range(res * 2, res * 3 - 1):
        v1 = bm.verts[i]
        v2 = bm.verts[i + 1]
        e = bm.edges.new((v1, v2))
    v1 = v2
    v2 = bm.verts[res * 2]
    e = bm.edges.new((v1, v2))

    for i in range(res + 1):
        t = i / float(res) * 2 - 1
        bm.verts.new(mu.Vector((0, 0, t)))
    for i in range(res * 3, res * 4):
        v1 = bm.verts[i]
        v2 = bm.verts[i + 1]
        e = bm.edges.new((v1, v2))

@cc.ops.editmode
def sample_color(context, event, ray_max=1000.0):
    result = cc.utils.find(context, event, 10000)
    if result is not None:
        obj, origin, target = result
        if obj.data.vertex_colors.active:
            with cc.colors.Sampler(obj) as sampler:
                return  sampler.raycast(origin, target)
    return mathutils.Color((0, 0, 0))

@cc.ops.editmode
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
    blend_falloff,
    bias, scale, mirror,
    select='POLYGON'):

    colors = cc.colors.layer(obj)

    m = mathutils
    to_obj = obj.matrix_world.inverted()
    p1 = to_obj * m.Vector(point_a)
    p2 = to_obj * m.Vector(point_b)
    direction = p2 - p1

    for s in colors.itersamples():
        if not s.is_selected(select.lower()):
            continue

        vert = s.vertex.co
        delta = vert - p1

        if blend_type == 'DIRECTIONAL':
            distance = delta.dot(direction.normalized())
            atten = max(min(distance / direction.length, 1), 0)
        if blend_type == 'RADIAL':
            distance = cc.utils.magnitude(delta)
            atten = max(min(distance / direction.length, 1), 0)

        atten = max(min((atten - bias) / scale, 1), 0)

        if mirror:
            atten = 1 - abs(atten % 1 * 2 - 1)

        if blend_falloff == 'SHARP':
            atten = atten * atten
        if blend_falloff == 'ROOT':
            atten = math.sqrt(atten)
        if blend_falloff == 'SMOOTH':
            atten = math.cos(atten * math.pi + math.pi) / 2 + .5

        color_ab = cc.utils.lerp(color_a, color_b, atten)
        alpha_ab = cc.utils.lerp(alpha_a, alpha_b, atten)

        if blend_method == 'REPLACE':
            s.color = color_ab

        if blend_method == 'MIX':
            s.color = cc.utils.lerp(s.color, color_ab, alpha_ab)

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

@cc.ops.editmode
def set_gradient_object(
    obj,
    point_a,
    point_b,
    color_a,
    alpha_a,
    color_b,
    alpha_b,
    blend_type,
    blend_method,
    blend_falloff,
    bias, scale, mirror,
    select='ALL'):

    mesh = obj.data
    g = mesh.gradient_settings

    if not obj.is_gradient or g.blend_type != blend_type:
        bm = bmesh.new()
        bm.from_mesh(mesh)
        if blend_type == 'DIRECTIONAL':
            gen_mesh_directional(bm)
        elif blend_type == 'RADIAL':
            gen_mesh_radial(bm)
        bm.to_mesh(mesh)
        bm.free()

    obj.is_gradient = True

    g.color_a = color_a
    g.alpha_a = alpha_a
    g.color_b = color_b
    g.alpha_b = alpha_b
    g.blend_type = blend_type
    g.blend_method = blend_method
    g.blend_falloff = blend_falloff
    g.bias = bias
    g.scale = scale
    g.mirror = mirror
    g.select = select

    line = mu.Vector(point_b - point_a)
    quat = line.normalized().to_track_quat('Z', 'Y')
    length = line.length

    obj.rotation_mode = 'QUATERNION'
    obj.rotation_quaternion = quat
    obj.location = point_a
    obj.scale = mu.Vector((length, length, length))

    mesh.update()
    obj.update_tag()
    bpy.context.scene.update()

    colors = cc.colors.layer(obj)

    for s in colors.itersamples():
        vert = s.vertex.co
        if blend_type == 'DIRECTIONAL':
            atten = vert.z
        if blend_type == 'RADIAL':
            atten = vert.length
        atten = max(min((atten - bias) / scale, 1), 0)
        if mirror:
            atten = 1 - abs(atten % 1 * 2 - 1)
        if blend_falloff == 'SHARP':
            atten = atten * atten
        if blend_falloff == 'ROOT':
            atten = math.sqrt(atten)
        if blend_falloff == 'SMOOTH':
            atten = math.cos(atten * math.pi + math.pi) / 2 + .5
        s.color = cc.utils.lerp(color_a, color_b, atten)

    return obj

@cc.ops.editmode
def gen_gradient_object(*args, **kwargs):
    mesh = bpy.data.meshes.new('Gradient')
    obj = bpy.data.objects.new('Gradient', mesh)
    set_gradient_object(obj, *args, **kwargs)
    return obj

PROP_SELECT = bpy.props.EnumProperty(
    items=cc.ops.ENUM_SELECT,
    name='Select', default='POLYGON')

PROP_BLEND_TYPE = bpy.props.EnumProperty(
    items=(
        ('DIRECTIONAL', 'Directional', 'Directional', 'CURVE_PATH', 0),
        ('RADIAL', 'Radial', 'Radial', 'MESH_UVSPHERE', 1),),
    name='Type', default='DIRECTIONAL')

PROP_BLEND_METHOD = bpy.props.EnumProperty(
    items=(
        ('SUBTRACT', 'Subtract', 'Subtract'),
        ('ADD', 'Add', 'Add'),
        ('MULTIPLY', 'Multiply', 'Multiply'),
        ('MIX', 'Mix', 'Mix'),
        ('REPLACE', 'Replace', 'Replace'),),
    name='Method', default='REPLACE')

PROP_BLEND_FALLOFF = bpy.props.EnumProperty(
    items=(
        ('LINEAR', 'Linear', 'Linear', 'LINCURVE', 0),
        ('SHARP', 'Sharp', 'Add', 'SHARPCURVE', 1),
        ('ROOT', 'Root', 'Root', 'ROOTCURVE', 2),
        ('SMOOTH', 'Smooth', 'Smooth', 'SMOOTHCURVE', 3),),
    name='Fallof', default='LINEAR')

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

PROP_MIRROR = bpy.props.BoolProperty(
    name='Mirror', default=False)

class GradientSettings(bpy.types.PropertyGroup):
    select = PROP_SELECT
    blend_type = PROP_BLEND_TYPE
    blend_method = PROP_BLEND_METHOD
    blend_falloff = PROP_BLEND_FALLOFF
    color_a = PROP_COLOR_A
    alpha_a = PROP_ALPHA_A
    color_b = PROP_COLOR_B
    alpha_b = PROP_ALPHA_B
    bias = PROP_BIAS
    scale = PROP_SCALE
    mirror = PROP_MIRROR

def gradient_preset_selected(self, context):
    s = context.scene
    if s.gradient_active_preset:
        preset = s.gradient_presets[s.gradient_active_preset]
        for prop in s.gradient_settings.keys():
            setattr(s.gradient_settings, prop, getattr(preset, prop))

PROP_GRADIENT_SETTINGS = bpy.props.PointerProperty(type=GradientSettings)

PROP_GRADIENT_PRESETS = bpy.props.CollectionProperty(type=GradientSettings)

PROP_GRADIENT_ACTIVE_PRESET = bpy.props.StringProperty(name='Preset', default='', update=gradient_preset_selected)

PROP_IS_GRADIENT = bpy.props.BoolProperty()

def draw_gradient_settings(context, layout, data):
    s = context.scene

    layout.prop(data, 'select', '')

    col = layout.column(align=True)

    col.prop(data, 'blend_method', '', icon='COLOR')
    col.prop(data, 'blend_type', '')
    col.prop(data, 'blend_falloff', '')

    col.prop(data, 'bias')
    col.prop(data, 'scale')
    col.prop(data, 'mirror', toggle=True)

    col = layout.column(align=True)

    row = col.row(align=True)
    row.prop(data, 'color_a', '')
    row.prop(data, 'color_b', '')

    row = col.row(align=True)
    row.prop(data, 'alpha_a', '')
    row.prop(data, 'alpha_b', '')

    return col

class GradientPanel(bpy.types.Panel):
    bl_label = "Gradient"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        l = self.layout
        s = context.scene

        c = l.column(align=True)
        r = c.row(align=True)
        r.prop_search(s, 'gradient_active_preset', s, 'gradient_presets', '', icon='SETTINGS')
        r.operator('cc.gradient_preset_add', '', icon='ZOOMIN')
        r.operator('cc.gradient_preset_remove', '', icon='X')
        if s.gradient_active_preset:
            r = c.row(align=True)
            r.operator('cc.gradient_preset_update', 'Update', icon='COPYDOWN')
            r.operator('cc.gradient_preset_revert', 'Revert', icon='PASTEDOWN')

        c = draw_gradient_settings(context, self.layout, context.scene.gradient_settings)
        c.operator('cc.gradient_swap', '', icon='ARROW_LEFTRIGHT')

        op = l.operator('cc.gradient_object', 'Create')
        op.create = True
        op.override = False

        obj = context.active_object
        if obj and obj.is_gradient:
            c = l.row(align=True)
            op = c.operator('cc.gradient_object', 'Update')
            op.override = True
            op.create = False
            op = c.operator('cc.gradient_object', 'Adjust')
            op.override = False
            op.create = False
            c.operator('cc.gradient_load', 'Load')

        if len(context.selected_objects) > 1:
            l.operator('cc.gradient_apply', 'Apply')

class GradientPresetAdd(bpy.types.Operator):
    bl_idname = 'cc.gradient_preset_add'
    bl_label = 'Add Preset'
    bl_options = {'UNDO'}

    name = bpy.props.StringProperty(name='Name')

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        s = context.scene
        preset = s.gradient_presets.add()
        for prop in s.gradient_settings.keys():
            setattr(preset, prop, getattr(s.gradient_settings, prop))
        preset.name = self.name
        s.gradient_active_preset = preset.name
        return {'FINISHED'}

class GradientPresetRemove(bpy.types.Operator):
    bl_idname = 'cc.gradient_preset_remove'
    bl_label = 'Remove Preset'
    bl_options = {'UNDO'}

    def execute(self, context):
        s = context.scene
        if s.gradient_active_preset:
            idx = s.gradient_presets.find(s.gradient_active_preset)
            s.gradient_presets.remove(idx)
        s.gradient_active_preset = ''
        self.report({'INFO'}, 'Preset removed.')
        return {'FINISHED'}

class GradientPresetUpdate(bpy.types.Operator):
    bl_idname = 'cc.gradient_preset_update'
    bl_label = 'Update Preset'
    bl_options = {'UNDO'}

    def execute(self, context):
        s = context.scene
        if not s.gradient_active_preset:
            self.report({'ERROR'}, 'No preset active.')
            return {'CANCELLED'}
        preset = s.gradient_presets[s.gradient_active_preset]
        for prop in s.gradient_settings.keys():
            setattr(preset, prop, getattr(s.gradient_settings, prop))
        self.report({'INFO'}, 'Preset updated.')
        return {'FINISHED'}

class GradientPresetRevert(bpy.types.Operator):
    bl_idname = 'cc.gradient_preset_revert'
    bl_label = 'Load Preset'
    bl_options = {'UNDO'}

    def execute(self, context):
        s = context.scene
        if not s.gradient_active_preset:
            self.report({'ERROR'}, 'No preset active.')
            return {'CANCELLED'}
        preset = s.gradient_presets[s.gradient_active_preset]
        for prop in s.gradient_settings.keys():
            setattr(s.gradient_settings, prop, getattr(preset, prop))
        self.report({'INFO'}, 'Reverted to preset.')
        return {'FINISHED'}

class GradientObject(bpy.types.Operator):
    bl_idname = 'cc.gradient_object'
    bl_label = 'Add/Set Gradient'
    bl_options = {'REGISTER', 'UNDO'}

    select = PROP_SELECT
    blend_type = PROP_BLEND_TYPE
    blend_method = PROP_BLEND_METHOD
    blend_falloff = PROP_BLEND_FALLOFF
    color_a = PROP_COLOR_A
    alpha_a = PROP_ALPHA_A
    color_b = PROP_COLOR_B
    alpha_b = PROP_ALPHA_B
    bias = PROP_BIAS
    scale = PROP_SCALE
    mirror = PROP_MIRROR

    create = bpy.props.BoolProperty()
    override = bpy.props.BoolProperty()

    @classmethod
    def poll(cls, context):
        return context.mode == 'OBJECT'

    def draw(self, context):
        draw_gradient_settings(context, self.layout, self)

    def execute(self, context):
        obj = context.active_object

        args = (
            self.color_a, self.alpha_a,
            self.color_b, self.alpha_b,
            self.blend_type, self.blend_method, self.blend_falloff,
            self.bias, self.scale, self.mirror,
            self.select
        )

        if obj and obj.is_gradient and not self.create:
            point_a = obj.location
            point_b = obj.matrix_world * mu.Vector((0, 0, 1))
            set_gradient_object(obj, point_a, point_b, *args)
        else:
            point_a = context.scene.cursor_location
            point_b = point_a + mu.Vector((0, 0, 1))
            obj = gen_gradient_object(point_a, point_b, *args)
            context.scene.objects.link(obj)

        bpy.ops.object.select_all(action='DESELECT')
        obj.select = True
        context.scene.objects.active = obj
        context.scene.update()

        return {'FINISHED'}

    def invoke(self, context, event):
        obj = context.active_object
        scene = context.scene

        context.space_data.viewport_shade = 'TEXTURED'

        if obj and obj.is_gradient and not self.override:
            g = obj.data.gradient_settings
        else:
            g = scene.gradient_settings

        self.select = g.select
        self.blend_type = g.blend_type
        self.blend_method = g.blend_method
        self.blend_falloff = g.blend_falloff
        self.color_a = g.color_a
        self.alpha_a = g.alpha_a
        self.color_b = g.color_b
        self.alpha_b = g.alpha_b
        self.bias = g.bias
        self.scale = g.scale
        self.mirror = g.mirror

        return self.execute(context)

class GradientLoad(bpy.types.Operator):
    bl_idname = 'cc.gradient_load'
    bl_label = 'Load Gradient'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return context.mode == 'OBJECT' and obj and obj.is_gradient

    def execute(self, context):
        obj = context.active_object.data.gradient_settings
        scene = context.scene.gradient_settings

        scene.select = obj.select
        scene.blend_type = obj.blend_type
        scene.blend_method = obj.blend_method
        scene.blend_falloff = obj.blend_falloff
        scene.color_a = obj.color_a
        scene.alpha_a = obj.alpha_a
        scene.color_b = obj.color_b
        scene.alpha_b = obj.alpha_b
        scene.bias = obj.bias
        scene.scale = obj.scale
        scene.mirror = obj.mirror

        return {'FINISHED'}

class GradientApply(bpy.types.Operator):
    bl_idname = 'cc.gradient_apply'
    bl_label = 'Apply Gradient'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 0

    def execute(self, context):
        objects = context.selected_objects
        meshes = []
        gradients = []

        for obj in objects:
            if obj.is_gradient:
                gradients.append(obj)
            elif obj.type == 'MESH':
                meshes.append(obj)

        gradients.sort(key=lambda o: o.name)

        for gra in gradients:
            for obj in meshes:
                gra.apply_gradient(obj)

        return {'FINISHED'}

class GradientSwap(bpy.types.Operator):
    bl_idname = 'cc.gradient_swap'
    bl_label = 'Swap Gradient Colors'
    bl_options = {'REGISTER'}

    def execute(self, context):
        g = context.scene.gradient_settings

        color_a = g.color_a.copy()
        alpha_a = g.alpha_a
        color_b = g.color_b.copy()
        alpha_b = g.alpha_b

        g.color_a = color_b
        g.alpha_a = alpha_b
        g.color_b = color_a
        g.alpha_b = alpha_a

        return {'FINISHED'}

class GradientTool(bpy.types.Operator):
    bl_idname = 'cc.gradient_tool'
    bl_label = 'Gradient Tool'
    bl_options = {'REGISTER', 'UNDO'}

    select = PROP_SELECT
    blend_type = PROP_BLEND_TYPE
    blend_method = PROP_BLEND_METHOD
    blend_falloff = PROP_BLEND_FALLOFF
    color_a = PROP_COLOR_A
    alpha_a = PROP_ALPHA_A
    color_b = PROP_COLOR_B
    alpha_b = PROP_ALPHA_B
    bias = PROP_BIAS
    scale = PROP_SCALE
    mirror = PROP_MIRROR

    point_a = bpy.props.FloatVectorProperty(
        name='Start Point', default=(0.0, 0.0, 0.0))
    point_b = bpy.props.FloatVectorProperty(
        name='End Point', default=(0.0, 0.0, 0.0))

    create = bpy.props.BoolProperty()

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
        draw_gradient_settings(context, self.layout, self)

    def execute(self, context):
        args = (
            mu.Vector(self.point_a), mu.Vector(self.point_b),
            self.color_a, self.alpha_a,
            self.color_b, self.alpha_b,
            self.blend_type, self.blend_method, self.blend_falloff,
            self.bias, self.scale, self.mirror,
            self.select,
        )

        gradient_colors(context.active_object, *args)
        if self.create:
            obj = gen_gradient_object(*args)
            context.scene.objects.link(obj)
            context.scene.update()

        theme = context.user_preferences.themes[0].view_3d
        theme.face_select[3] = self.face_select
        theme.editmesh_active[3] = self.editmesh_active
        context.area.tag_redraw()

        g = context.scene.gradient_settings
        g.select = self.select
        g.blend_type = self.blend_type
        g.blend_method = self.blend_method
        g.blend_falloff = self.blend_falloff
        g.color_a = self.color_a
        g.alpha_a = self.alpha_a
        g.color_b = self.color_b
        g.alpha_b = self.alpha_b
        g.bias = self.bias
        g.scale = self.scale
        g.mirror = self.mirror

        return {'FINISHED'}

    def invoke(self, context, event):
        scene = context.scene

        context.space_data.viewport_shade = 'TEXTURED'

        self.select = scene.gradient_settings.select
        self.blend_type = scene.gradient_settings.blend_type
        self.blend_method = scene.gradient_settings.blend_method
        self.blend_falloff = scene.gradient_settings.blend_falloff
        self.color_a = scene.gradient_settings.color_a
        self.alpha_a = scene.gradient_settings.alpha_a
        self.color_b = scene.gradient_settings.color_b
        self.alpha_b = scene.gradient_settings.alpha_b
        self.bias = scene.gradient_settings.bias
        self.scale = scene.gradient_settings.scale
        self.mirror = scene.gradient_settings.mirror

        theme = context.user_preferences.themes[0].view_3d
        self.face_select = theme.face_select[3]
        self.editmesh_active = theme.editmesh_active[3]
        theme.face_select[3] = 0
        theme.editmesh_active[3] = 0
        context.area.tag_redraw()

        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        ret = {'PASS_THROUGH'}

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
            ret = {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE' and event.value == 'PRESS':
            self.started = True
            self.point_a = endpoint
            self.mouse_a = mouse_pos
            self.mouse_b = mouse_pos
            ret = {'RUNNING_MODAL'}

        if event.type == 'MOUSEMOVE':
            self.point_b = endpoint
            self.mouse_b = mouse_pos

        if event.type == 'RIGHTMOUSE' and event.value == 'PRESS':
            if event.shift:
                self.color_b = sample_color(context, event)
            else:
                self.color_a = sample_color(context, event)
            return {'RUNNING_MODAL'}

        if event.type == 'LEFTMOUSE' and event.value == 'RELEASE':
            self.point_b = endpoint
            self.mouse_b = mouse_pos
            self.create = event.alt
            if self.mouse_a != self.mouse_b:
                self.execute(context)
            self.modal_cleanup(context, event)
            return {'FINISHED'}

        if event.type == 'ESC':
            self.modal_cleanup(context, event)
            return {'CANCELLED'}

        return ret

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

def register():
    cc.utils.register(__REGISTER__)

def unregister():
    cc.utils.unregister(__REGISTER___)

__REGISTER__ = (
    GradientSettings,
    GradientPanel,
    GradientPresetAdd,
    GradientPresetRemove,
    GradientPresetUpdate,
    GradientPresetRevert,
    GradientObject,
    GradientLoad,
    GradientApply,
    GradientSwap,
    GradientTool,
    (bpy.types.Scene, 'gradient_settings', PROP_GRADIENT_SETTINGS),
    (bpy.types.Scene, 'gradient_presets', PROP_GRADIENT_PRESETS),
    (bpy.types.Scene, 'gradient_active_preset', PROP_GRADIENT_ACTIVE_PRESET),
    (bpy.types.Mesh, 'gradient_settings', PROP_GRADIENT_SETTINGS),
    (bpy.types.Object, 'is_gradient', PROP_IS_GRADIENT),
    (bpy.types.Object, 'apply_gradient', apply_gradient),
)
