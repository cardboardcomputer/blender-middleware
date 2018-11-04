import cc
import bpy
import mathutils
import mathutils as mu
from mathutils import Color

bl_info = {
    'name': 'Utils: Colors',
    'author': 'Cardboard Computer',
    'blender': (2, 69, 0),
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

    def reset_func(self, context):
        if self.reset:
            self.h = 0
            self.s = 0
            self.v = 0
            self.multiply = True
            self.reset = False

    select = bpy.props.EnumProperty(
        items=cc.ops.ENUM_SELECT,
        name='Select', default='POLYGON')
    h = bpy.props.FloatProperty(name='Hue', min=-1, max=1, step=1)
    s = bpy.props.FloatProperty(name='Saturation', min=-1, max=1, step=1)
    v = bpy.props.FloatProperty(name='Value', min=-1, max=1, step=1)
    multiply = bpy.props.BoolProperty(name='Multiply Value', default=True)
    reset = bpy.props.BoolProperty(name='Reset', default=False, update=reset_func)

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

    def draw(self, context):
        l = self.layout
        l.prop(self, 'reset', toggle=True)
        c = l.column(align=True)
        c.prop(self, 'select', '')
        c.prop(self, 'h', 'H')
        c.prop(self, 's', 'S')
        c.prop(self, 'v', 'V')
        c.prop(self, 'multiply', 'Multiply', toggle=True)

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

    def update_hex_value(self, context):
        color = cc.colors.hex_to_color(self.hex_value)
        if self.color != color:
            self.color = color

    ref = bpy.props.FloatVectorProperty(
        name="Color", subtype='COLOR_GAMMA',
        min=0, max=1, step=1)
    color = bpy.props.FloatVectorProperty(
        name="Color", subtype='COLOR_GAMMA',
        min=0, max=1, step=1, update=update_color)
    hex_value = bpy.props.StringProperty(
        name="Hex", default='', update=update_hex_value)

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
def transfer_colors(obj, ref, alpha=True, select='ALL'):
    with cc.colors.Sampler(ref) as sampler:
        colors = cc.colors.layer(obj)

        ref_layer_name = cc.colors.layer(ref).name
        ref_alpha_name = '%s.Alpha' % ref_layer_name
        if ref_alpha_name in ref.data.vertex_colors:
            ref_sample_alpha = True
        else:
            ref_sample_alpha = False

        if not alpha:
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

    alpha = bpy.props.BoolProperty(
        name='Alpha', default=True)

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

        transfer_colors(obj, ref, alpha=self.alpha, select=self.select)

        return {'FINISHED'}

class ColorToGroup(bpy.types.Operator):
    bl_idname = 'cc.color_to_group'
    bl_label = 'Color To Group'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.active_object and context.active_object.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        layer = cc.colors.layer(obj)
        groups = obj.vertex_groups

        if groups.active_index >= 0:
            group = groups[groups.active_index]
        else:
            group = groups.new()
            group.name = layer.name

        for sample in layer.itersamples():
            group.add([sample.vertex.index], sample.color.v, type='REPLACE')

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
            cc.colors.Manager(obj).exec_color_ops(get_ops(obj.data))

def get_ops(data):
    # panel ops
    ops = list(data.vertex_color_ops)
    ops.sort(key=lambda o: o.index)

    # text ops
    text = data.vertex_color_ops_text
    ops = [o.op for o in ops if o.op]
    if text and text in bpy.data.texts:
        text = bpy.data.texts[text].as_string()
        if text:
            ops.insert(0, text)

    # data prop ops
    names = []
    for key in data.keys():
        if key.startswith('Color.'):
            names.append(key)
    names.sort()
    for name in names:
        ops.append(str(data[name]))

    return ops

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

PROP_VERTEX_COLOR_OPS = bpy.props.CollectionProperty(type=ColorOp)
PROP_VERTEX_COLOR_OPS_TEXT = bpy.props.StringProperty()

class ColorOpPanel(bpy.types.Panel):
    bl_label = 'Vertex Color Operations'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    @classmethod
    def poll(self, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        obj = bpy.context.active_object
        ops = list(obj.data.vertex_color_ops.values())
        ops.sort(key=lambda o: o.index)

        row = layout.row(align=True)
        row.prop_search(obj.data, 'vertex_color_ops_text', bpy.data, 'texts', '', icon='TEXT')
        row.operator('cc.color_op_text_add', '', icon='ZOOMIN')
        row.operator('cc.color_op_text_view', '', icon='RESTRICT_VIEW_OFF')

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

    @classmethod
    def poll(cls, context):
        obj = bpy.context.active_object
        return obj and obj.type == 'MESH'

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

    @classmethod
    def poll(cls, context):
        obj = bpy.context.active_object
        return obj and obj.type == 'MESH'

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

    @classmethod
    def poll(cls, context):
        obj = bpy.context.active_object
        return obj and obj.type == 'MESH'

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

    @classmethod
    def poll(cls, context):
        obj = bpy.context.active_object
        return obj and obj.type == 'MESH'

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
        obj = bpy.context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        objects = list(context.selected_objects)
        if obj and obj not in objects:
            objects.append(context.active_object)
        objects = [o for o in objects if o.type == 'MESH']
        if objects:
            apply_color_ops(objects)
            self.report({'INFO'}, 'Color operations applied.')
        return {'FINISHED'}

class ColorOpTextAdd(bpy.types.Operator):
    bl_idname = 'cc.color_op_text_add'
    bl_label = 'Add Color Op Text'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = bpy.context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        name = '%s.colors' % obj.name
        obj.data.vertex_color_ops_text = bpy.data.texts.new(name).name
        return {'FINISHED'}

class ColorOpTextView(bpy.types.Operator):
    bl_idname = 'cc.color_op_text_view'
    bl_label = 'View Color Op Text'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = bpy.context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        if obj.data.vertex_color_ops_text:
            cc.ops.view_text(obj.data.vertex_color_ops_text)
        return {'FINISHED'}

class ColorOpTextApply(bpy.types.Operator):
    bl_idname = 'cc.color_op_text_apply'
    bl_label = 'Apply Color Operators From Text'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        obj = context.active_object
        objects = list(context.selected_objects)
        if obj and obj not in objects:
            objects.append(context.active_object)
        objects = [o for o in objects if o.type == 'MESH']
        if context.space_data.type == 'TEXT_EDITOR':
            op = context.space_data.text.as_string()
        else:
            text = cc.ops.get_active_text(context.screen)
            if text:
                op = text.as_string()
            else:
                self.report({'ERROR'}, 'Could not find active text on screen to execute.')
                return {'CANCELLED'}
        if objects:
            with cc.ops.mode_object:
                for obj in objects:
                    if obj.type == 'MESH':
                        cc.colors.Manager(obj).exec_color_ops([op])
            self.report({'INFO'}, 'Color operations applied.')
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
        layout.operator(TransferColors.bl_idname, text='Transfer')
        layout.operator(ColorToGroup.bl_idname, text='To Group')
        layout.operator(ColorOpApply.bl_idname, text='Apply Ops')

def cardboard_menu_ext(self, context):
    self.layout.menu('CC_MT_colors')

def register():
    cc.utils.register(__REGISTER__)
    cc.ui.CardboardMenu.add_section(cardboard_menu_ext, 0)

def unregister():
    cc.utils.unregister(__REGISTER__)
    cc.ui.CardboardMenu.remove_section(cardboard_menu_ext)

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
    ColorToGroup,
    ColorOp,
    ColorOpPanel,
    ColorOpAdd,
    ColorOpRemove,
    ColorOpUp,
    ColorOpDown,
    ColorOpApply,
    ColorOpTextAdd,
    ColorOpTextView,
    ColorOpTextApply,
    ColorMenu,
    (bpy.types.Mesh, 'vertex_color_ops', PROP_VERTEX_COLOR_OPS),
    (bpy.types.Mesh, 'vertex_color_ops_text', PROP_VERTEX_COLOR_OPS_TEXT),
)
