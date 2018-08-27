import cc
import bpy
import mathutils
import mathutils as mu
from mathutils import Color

bl_info = {
    'name': 'Utils: Legacy',
    'author': 'Cardboard Computer',
    'blender': (2, 69, 0),
    'description': 'Utilities and operators for legacy scenes',
    'category': 'Cardboard'
}

@cc.ops.editmode
def legacy_upgrade():
    cc.legacy.upgrade()

class LegacyUpgrade(bpy.types.Operator):
    bl_idname = 'cc.legacy_upgrade'
    bl_label = 'Upgrade Legacy CC Scenes'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        legacy_upgrade()
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
    meshes = []
    gradients = []

    for obj in objects:
        if 'Gradient' in obj:
            gradients.append(obj)
        elif obj.type == 'MESH':
            meshes.append(obj)

    gradients.sort(key=lambda o: o.name)

    for ref in gradients:
        kwargs = gradient_to_kwargs(ref)
        for obj in meshes:
            gradient_colors(
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

def register():
    cc.utils.register(__REGISTER__)

def unregister():
    cc.utils.unregister(__REGISTER__)

__REGISTER__ = (
    LegacyUpgrade,
    GradientColors,
    ApplyGradients,
    LightColors,
)
