import cc
import bpy
import mathutils
import mathutils as mu
from mathutils import Color

bl_info = {
    'name': 'Utils: Colors',
    'author': 'Cardboard Computer',
    'blender': (2, 6, 9),
    'description': 'Various tools to work with vertex colors.',
    'category': 'Cardboard'
}

@cc.ops.editmode
def add_colors(obj, name, alpha=False):
    colors = cc.colors.new(obj, name, alpha=alpha)
    colors.activate()

class AddColors(bpy.types.Operator):
    bl_idname = 'cc.add_colors'
    bl_label = 'Add Colors'
    bl_options = {'REGISTER', 'UNDO'}

    name = bpy.props.StringProperty(name='Name', default=cc.colors.BASENAME)
    alpha = bpy.props.BoolProperty(name='Alpha', default=True)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def draw(self, context):
        layout = self.layout

        row = layout.split(align=True, percentage=0.7)
        row.prop(self, 'name', '')
        row.prop(self, 'alpha', toggle=True)

    def execute(self, context):
        context.space_data.viewport_shade = 'TEXTURED'
        add_colors(context.active_object, self.name, self.alpha)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.name = cc.colors.Manager(context.active_object).get_unique_name(self.name)
        self.alpha = cc.lines.is_line(context.active_object) or self.alpha
        return context.window_manager.invoke_props_dialog(self, width=160)

@cc.ops.editmode
def adjust_hsv(obj, h, s, v, multiply=False, select='POLYGON'):
    colors = cc.colors.layer(obj)
    for sample in colors.itersamples():
        if sample.is_selected(select.lower()):
            sample.color.h += h
            sample.color.s += s
            if multiply:
                sample.color.v *= (v * 0.5 + 0.5) * 2
            else:
                sample.color.v += v

class AdjustHsv(bpy.types.Operator):
    bl_idname = 'cc.adjust_hsv'
    bl_label = 'Adjust HSV'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=cc.ops.ENUM_SELECT,
        name='Select', default='POLYGON')
    h = bpy.props.FloatProperty(name='Hue', min=-1, max=1, step=1)
    s = bpy.props.FloatProperty(name='Saturation', min=-1, max=1, step=1)
    v = bpy.props.FloatProperty(name='Value', min=-1, max=1, step=1)
    multiply = bpy.props.BoolProperty(name='Multiply Value', default=False)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def __init__(self):
        context = bpy.context
        if context.mode == 'EDIT_MESH':
            vertex, edge, face = context.tool_settings.mesh_select_mode
            self.select = 'VERTEX'
            if face and not vertex:
                self.select = 'POLYGON'

    def execute(self, context):
        cc.ops.show_tool_props(context)
        adjust_hsv(context.active_object, self.h, self.s, self.v, self.multiply, self.select)
        return {'FINISHED'}

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
def set_colors(obj, color, alpha=None, select='POLYGON'):
    colors = cc.colors.layer(obj)

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
        self.hex_value = cc.colors.color_to_hex(self.color)

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

def select_by_color(obj, threshold=0.01):
    # get wierd behavior/errors when in editmode
    bpy.ops.object.editmode_toggle()

    colors = obj.data.vertex_colors.active.data
    selected_polygons = list(filter(lambda p: p.select, obj.data.polygons))

    if len(selected_polygons):
        p = selected_polygons[0]
        r = g = b = 0
        for i in p.loop_indices:
            c = colors[i].color
            r += c.r
            g += c.g
            b += c.b
        r /= p.loop_total
        g /= p.loop_total
        b /= p.loop_total
        target = Color((r, g, b))

        for p in obj.data.polygons:
            r = g = b = 0
            for i in p.loop_indices:
                c = colors[i].color
                r += c.r
                g += c.g
                b += c.b
            r /= p.loop_total
            g /= p.loop_total
            b /= p.loop_total
            source = Color((r, g, b))

            if (abs(source.r - target.r) < threshold and
                abs(source.g - target.g) < threshold and
                abs(source.b - target.b) < threshold):

                p.select = True

    bpy.ops.object.editmode_toggle()

class SelectByColor(bpy.types.Operator):
    bl_idname = 'cc.select_by_color'
    bl_label = 'Select By Color'
    bl_options = {'REGISTER', 'UNDO'}

    threshold = bpy.props.FloatProperty(name='Threshold', default=0.01, min=0.001, max=1.0, step=1)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH'
                and not cc.lines.is_line(obj))

    def execute(self, context):
        select_by_color(context.active_object, self.threshold)
        return {'FINISHED'}

@cc.ops.editmode
def default_color(obj, select='POLYGON'):
    colors = cc.colors.layer(obj)

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

@cc.ops.editmode
def set_colors(obj, color, alpha=None, select='POLYGON'):
    colors = cc.colors.layer(obj)

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
        items=cc.ops.ENUM_SELECT,
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

@cc.ops.editmode
def invert_colors(obj, select='POLYGON'):
    colors = cc.colors.layer(obj)
    for sample in colors.itersamples():
        if sample.is_selected(select.lower()):
            sample.color.r = 1 - sample.color.r
            sample.color.g = 1 - sample.color.g
            sample.color.b = 1 - sample.color.b

class InvertColors(bpy.types.Operator):
    bl_idname = 'cc.invert_colors'
    bl_label = 'Invert Colors'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=cc.ops.ENUM_SELECT,
        name='Select', default='POLYGON')

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
        return self.execute(context)

    def execute(self, context):
        invert_colors(context.active_object, self.select)
        return {'FINISHED'}

@cc.ops.editmode
def light_colors(
    objects,
    use_normals=False,
    color_layer='',
    select='POLYGON'):
    for obj in objects:
        if obj.type == 'MESH':
            light_colors_obj(obj, use_normals, color_layer, select)

def light_colors_obj(
    obj,
    use_normals=False,
    color_layer='',
    select='POLYGON'):

    light_all = False
    select = select.lower()

    lights = []
    for l in cc.utils.traverse(bpy.context.scene.objects):
        if (l.type == 'LAMP' and
            not l.hide_render):
            lights.append(l)

    final = cc.colors.layer(obj)
    temp = cc.colors.new(obj, '_Temp')
    base = cc.colors.layer(obj, color_layer)

    if final.name == base.name:
        light_all = True
        for i, s in enumerate(base.itersamples()):
            s.color = mathutils.Color((1, 1, 1))

    for i, s in enumerate(temp.itersamples()):
        if light_all or s.is_selected(select):
            s.color *= 0

    for light in lights:

        center = light.matrix_world * mathutils.Vector((0, 0, 0))
        radius = light.data.distance
        lcolor = light.data.color * light.data.energy

        for i, s in enumerate(temp.itersamples()):
            if not light_all and not s.is_selected(select):
                continue

            vert = obj.matrix_world * s.vertex.co

            if use_normals:
                light_dir = (vert - center).normalized()
                normal = s.vertex.normal
                n_dot_l = 1 - normal.dot(light_dir)
            else:
                n_dot_l = 1

            distance = cc.utils.magnitude(vert - center)
            atten = 1 - min(distance / radius, 1)

            color = lcolor.copy()
            color.v *= atten * n_dot_l

            rcolor = base.samples[i].color

            s.color.r += color.r * rcolor.r
            s.color.g += color.g * rcolor.g
            s.color.b += color.b * rcolor.b

    for i, s in enumerate(final.itersamples()):
        if light_all or s.is_selected(select):
            s.color = temp.samples[i].color

    temp.destroy()

class LightColors(bpy.types.Operator):
    bl_idname = 'cc.light_colors'
    bl_label = 'Light Colors'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=cc.ops.ENUM_SELECT,
        name='Select', default='POLYGON')
    use_normals = bpy.props.BoolProperty(name='Use Normals', default=False)
    color_layer = bpy.props.StringProperty(name='Color Layer', default='')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        light_colors(
            context.selected_objects,
            use_normals=self.use_normals,
            color_layer=self.color_layer,
            select=self.select)

        return {'FINISHED'}

@cc.ops.editmode
def copy_colors(objects, from_layer, to_layer, select='POLYGON'):
    if from_layer == to_layer:
        return
    for obj in objects:
        if obj.type == 'MESH':
            a = cc.colors.layer(obj, from_layer)
            b = cc.colors.layer(obj, to_layer)
            for i, s in enumerate(b.itersamples()):
                if s.is_selected(select.lower()):
                    s.color = a.samples[i].color
                    s.alpha = a.samples[i].alpha

def shared_layer_items(scene, context):
    layers = cc.colors.find_shared_layers(context.selected_objects)
    enum = [('__NONE__', '', '')]
    for name in layers:
        enum.append((name, name, name))
    return enum

class CopyColors(bpy.types.Operator):
    bl_idname = 'cc.copy_colors'
    bl_label = 'Copy Colors'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=cc.ops.ENUM_SELECT,
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

@cc.ops.editmode
def transfer_colors(obj, ref, select='ALL'):
    with cc.colors.Sampler(ref) as sampler:
        colors = cc.colors.layer(obj)

        ref_layer_name = cc.colors.layer(ref).name
        ref_alpha_name = '%s.Alpha' % ref_layer_name
        if ref_alpha_name in ref.data.vertex_colors:
            ref_sample_alpha = True
        else:
            ref_sample_alpha = False

        for sample in colors.itersamples():
            if sample.is_selected(select.lower()):
                point = sample.obj.matrix_world * sample.vertex.co
                sample.color = sampler.closest(point)
                if ref_sample_alpha:
                    sample.alpha = sampler.closest(point, layer=ref_alpha_name).v

class TransferColors(bpy.types.Operator):
    bl_idname = 'cc.transfer_colors'
    bl_label = 'Transfer Colors'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=cc.ops.ENUM_SELECT,
        name='Select', default='ALL')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if len(context.selected_objects) == 2:
            ref = list(context.selected_objects)
            ref.remove(context.active_object)
            ref = ref[0]
        else:
            ref = None
        return (
            (obj and obj.type == 'MESH') and
            (ref and ref.type == 'MESH' and ref.data.polygons))

    def execute(self, context):
        aux_objects = list(context.selected_objects)
        aux_objects.remove(context.active_object)

        obj = context.active_object
        ref = aux_objects[0]

        transfer_colors(obj, ref, select=self.select)

        return {'FINISHED'}

def gradient_colors(
    obj,
    ref,
    color_a,
    alpha_a,
    color_b,
    alpha_b,
    blend_type,
    blend_method,
    select='POLYGON',
    update_gradient=True):

    colors = cc.colors.layer(obj)

    if update_gradient:
        ref['Gradient'] = {}
        d = ref['Gradient']
        d['blend_type'] = blend_type
        d['blend_method'] = blend_method
        d['color_a'] = list(color_a)
        d['color_b'] = list(color_b)
        d['alpha_a'] = alpha_a
        d['alpha_b'] = alpha_b

    m = mathutils
    p1 = ref.location
    p2 = ref.matrix_world * m.Vector((0, 0, 1))
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
            distance = cc.utils.magnitude(delta)
            atten = max(min(distance / direction.length, 1), 0)

        color = m.Color((0, 0, 0))
        color_ab = m.Color((0, 0, 0))
        color_ab = cc.utils.lerp(color_a, color_b, atten)
        alpha_ab = cc.utils.lerp(alpha_a, alpha_b, atten)

        if blend_method == 'REPLACE':
            s.color = color_ab
            s.alpha = alpha_ab

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

def gradient_to_kwargs(obj):
    g = {}
    if 'Gradient' in obj:
        d = obj['Gradient']
        g['blend_type'] = d['blend_type']
        g['blend_method'] = d['blend_method']
        g['color_a'] = mathutils.Color(d['color_a'])
        g['color_b'] = mathutils.Color(d['color_b'])
        g['alpha_a'] = d['alpha_a']
        g['alpha_b'] = d['alpha_b']
    return g

class GradientColors(bpy.types.Operator):
    bl_idname = 'cc.gradient_colors'
    bl_label = 'Gradient Colors'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=cc.ops.ENUM_SELECT,
        name='Select', default='POLYGON')

    blend_type = bpy.props.EnumProperty(
        items=(
            ('LINEAR', 'Linear', 'Linear'),
            ('RADIAL', 'Radial', 'Radial'),),
        name='Type', default='LINEAR')

    blend_method = bpy.props.EnumProperty(
        items=(
            ('SUBTRACT', 'Subtract', 'Subtract'),
            ('ADD', 'Add', 'Add'),
            ('MULTIPLY', 'Multiply', 'Multiply'),
            ('MIX', 'Mix', 'Mix'),
            ('REPLACE', 'Replace', 'Replace'),),
        name='Method', default='REPLACE')

    color_a = bpy.props.FloatVectorProperty(
        name="Start Color", subtype='COLOR_GAMMA',
        min=0, max=1, step=1,)
    alpha_a = bpy.props.FloatProperty(
        name="Start Alpha", min=0, max=1, step=0.1, default=1)

    color_b = bpy.props.FloatVectorProperty(
        name="End Color", subtype='COLOR_GAMMA',
        min=0, max=1, step=1, default=(1, 1, 1),)
    alpha_b = bpy.props.FloatProperty(
        name="End Alpha", min=0, max=1, step=0.1, default=1)

    def __init__(self):
        context = bpy.context
        aux_objects = list(context.selected_objects)
        aux_objects.remove(context.active_object)
        ref = aux_objects[0]

        if 'Gradient' in ref:
            d = ref['Gradient']
            self.blend_type = d['blend_type']
            self.blend_method = d['blend_method']
            self.color_a = mathutils.Color(d['color_a'])
            self.color_b = mathutils.Color(d['color_b'])
            self.alpha_a = d['alpha_a']
            self.alpha_b = d['alpha_b']

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH' and len(context.selected_objects) == 2)

    def execute(self, context):
        aux_objects = list(context.selected_objects)
        aux_objects.remove(context.active_object)

        gradient_colors(
            context.active_object,
            aux_objects[0],
            self.color_a,
            self.alpha_a,
            self.color_b,
            self.alpha_b,
            self.blend_type,
            self.blend_method,
            select=self.select)

        return {'FINISHED'}

def apply_gradients(objects, select='POLYGON'):
    import cc_gradient_colors

    meshes = []
    gradients = []

    for obj in objects:
        if 'Gradient' in obj:
            gradients.append(obj)
        elif obj.type == 'MESH':
            meshes.append(obj)

    gradients.sort(key=lambda o: o.name)

    for ref in gradients:
        kwargs = cc_gradient_colors.gradient_to_kwargs(ref)
        for obj in meshes:
            cc_gradient_colors.gradient_colors(
                obj, ref,
                select=select, update_gradient=False,
                **kwargs)

class ApplyGradients(bpy.types.Operator):
    bl_idname = 'cc.apply_gradients'
    bl_label = 'Apply Gradients'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=cc.ops.ENUM_SELECT,
        name='Select', default='POLYGON')

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 1

    def execute(self, context):
        apply_gradients(context.selected_objects, select=self.select)
        return {'FINISHED'}

@cc.ops.editmode
def view_colors(objects, layer_name):
    for obj in objects:
        if obj.type == 'MESH':
            layer = cc.colors.Manager(obj).get_layer(layer_name)
            if layer:
                layer.activate()

def shared_layer_items(scene, context):
    layers = cc.colors.find_shared_layers(context.selected_objects)
    enum = []
    for name in layers:
        enum.append((name, name, name))
    return enum

class ViewColorsMenu(bpy.types.Menu):
    bl_label = "Vertex Colors"
    bl_idname = "CC_MT_view_colors"

    @classmethod
    def poll(cls, context):
        layers = cc.colors.find_shared_layers(context.selected_objects)
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
        shared_layers = cc.colors.find_shared_layers(context.selected_objects)
        default_layer = cc.colors.find_default_layer(context.selected_objects)

        if default_layer and default_layer in shared_layers:
            self.layer = default_layer

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        view_colors(context.selected_objects, self.layer)
        return {'FINISHED'}

@cc.ops.editmode
def apply_color_ops(objects):
    for obj in objects:
        if obj.type == 'MESH':
            cc.colors.Manager(obj).exec_color_ops(get_ops(obj))

def get_ops(obj):
    ops = list(obj.data.vertex_color_ops)
    ops.sort(key=lambda o: o.index)
    return [o.op for o in ops if o.op]

def set_ops(obj, ops):
    while obj.data.vertex_color_ops:
        obj.data.vertex_color_ops.remove(0)
    for i, o in enumerate(ops):
        op = obj.data.vertex_color_ops.add()
        op.op = o
        op.index = i

class ColorOp(bpy.types.PropertyGroup):
    op = bpy.props.StringProperty()
    index = bpy.props.IntProperty()

class ColorOpPanel(bpy.types.Panel):
    bl_label = 'Vertex Color Operations'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    @classmethod
    def poll(self, context):
        return context.active_object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        obj = bpy.context.active_object
        ops = list(obj.data.vertex_color_ops.values())
        ops.sort(key=lambda o: o.index)

        column = layout.column(align=True)

        for op in ops:
            row = column.row(align=True)
            row.prop(op, 'op', '')
            row.operator('cc.color_op_up', '', icon='TRIA_UP').index = op.index
            row.operator('cc.color_op_down', '', icon='TRIA_DOWN').index = op.index
            row.operator('cc.color_op_remove', '', icon='X').index = op.index

        column.operator('cc.color_op_add', 'Add')

        layout.operator('cc.color_op_apply', 'Apply')

class ColorOpAdd(bpy.types.Operator):
    bl_idname = 'cc.color_op_add'
    bl_label = 'Add Color Op'
    bl_options = {'INTERNAL', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        index = len(obj.data.vertex_color_ops)
        op = obj.data.vertex_color_ops.add()
        op.index = index
        return {'FINISHED'}

class ColorOpRemove(bpy.types.Operator):
    bl_idname = 'cc.color_op_remove'
    bl_label = 'Remove Color Op'
    bl_options = {'INTERNAL', 'UNDO'}

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = bpy.context.active_object
        for op in obj.data.vertex_color_ops:
            if op.index == self.index:
                idx = list(obj.data.vertex_color_ops).index(op)
                obj.data.vertex_color_ops.remove(idx)
                break
        for i, op in enumerate(obj.data.vertex_color_ops):
            op.index = i
        return {'FINISHED'}

class ColorOpUp(bpy.types.Operator):
    bl_idname = 'cc.color_op_up'
    bl_label = 'Move Color Op Up'
    bl_options = {'INTERNAL', 'UNDO'}

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = bpy.context.active_object
        ops = get_ops(obj)
        index = self.index
        op = ops[index]
        ops.remove(op)
        index = max(0, index - 1)
        ops.insert(index, op)
        set_ops(obj, ops)
        return {'FINISHED'}

class ColorOpDown(bpy.types.Operator):
    bl_idname = 'cc.color_op_down'
    bl_label = 'Move Color Op Down'
    bl_options = {'INTERNAL', 'UNDO'}

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = bpy.context.active_object
        ops = get_ops(obj)
        index = self.index
        op = ops[index]
        ops.remove(op)
        index = min(len(ops) + 1, index + 1)
        ops.insert(index, op)
        set_ops(obj, ops)
        return {'FINISHED'}

class ColorOpApply(bpy.types.Operator):
    bl_idname = 'cc.color_op_apply'
    bl_label = 'Apply Color Operators'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return 'MESH' in (obj.type for obj in context.selected_objects)

    def execute(self, context):
        apply_color_ops(context.selected_objects)
        return {'FINISHED'}

class ColorMenu(bpy.types.Menu):
    bl_label = 'Colors'
    bl_idname = 'CC_MT_colors'

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'

        layout.operator(AddColors.bl_idname, text='Add')
        layout.operator(CopyColors.bl_idname, text='Copy')
        layout.operator(SetColors.bl_idname, text='Set')
        layout.operator(AdjustHsv.bl_idname, text='Adjust')
        layout.operator(InvertColors.bl_idname, text='Invert')
        layout.operator(SelectByColor.bl_idname, text='Select')

        layout.separator()

        layout.operator(TransferColors.bl_idname, text='Transfer')
        layout.operator(GradientColors.bl_idname, text='Set Gradient')
        layout.operator(ApplyGradients.bl_idname, text='Apply Gradient(s)')
        layout.operator(LightColors.bl_idname, text='Apply Lights')
        layout.operator(ColorOpApply.bl_idname, text='Apply Ops')

__REGISTER__ = (
    ViewColors,
    ViewColorsMenu,
    SampleColor,

    AddColors,
    CopyColors,
    SetColors,
    AdjustHsv,
    InvertColors,
    SelectByColor,

    TransferColors,
    LightColors,
    GradientColors,
    ApplyGradients,

    ColorOp,
    ColorOpPanel,
    ColorOpAdd,
    ColorOpRemove,
    ColorOpUp,
    ColorOpDown,
    ColorOpApply,

    ColorMenu,
)

def cardboard_menu_ext(self, context):
    self.layout.menu('CC_MT_colors')

def register():
    for cls in __REGISTER__:
        bpy.utils.register_class(cls)

    bpy.types.Mesh.vertex_color_ops = bpy.props.CollectionProperty(type=ColorOp)

    cc.ui.CardboardMenu.add_section(cardboard_menu_ext, 0)

def unregister():
    for cls in __REGISTER__:
        bpy.utils.unregister_class(cls)

    bpy.types.Mesh.vertex_color_ops = None

    cc.ui.CardboardMenu.remove_section(cardboard_menu_ext)
