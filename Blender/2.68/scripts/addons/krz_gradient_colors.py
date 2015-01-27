import bpy
import krz
import mathutils

bl_info = {
    'name': 'Gradient Colors',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Gradient Colors',
    'description': 'Apply gradients on lines/polygon colors',
    'category': 'Cardboard'
}

def gradient_colors(
    obj,
    ref,
    color_a,
    alpha_a,
    color_b,
    alpha_b,
    blend_type,
    blend_method,
    override=False,
    select='POLYGON'):

    colors = krz.colors.layer(obj)

    if not override:
        if 'blend_type' in ref:
            blend_type = ref['blend_type'].upper()
        if 'blend_method' in ref:
            blend_method = ref['blend_method'].upper()
        if 'color_a' in ref:
            color_a = hex_to_color(ref['color_a'])
        if 'alpha_a' in ref:
            alpha_a = ref['alpha_a']
        if 'color_b' in ref:
            color_b = hex_to_color(ref['color_b'])
        if 'alpha_b' in ref:
            alpha_b = ref['alpha_b']

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
            distance = krz.magnitude(delta)
            atten = max(min(distance / direction.length, 1), 0)

        color = m.Color((0, 0, 0))
        color_ab = m.Color((0, 0, 0))
        color_ab.r = krz.lerp(color_a.r, color_b.r, atten)
        color_ab.g = krz.lerp(color_a.g, color_b.g, atten)
        color_ab.b = krz.lerp(color_a.b, color_b.b, atten)
        alpha_ab = krz.lerp(alpha_a, alpha_b, atten)

        if blend_method == 'REPLACE':
            s.color = color_ab
            s.alpha = alpha_ab

        if blend_method == 'MIX':
            s.color.r = krz.lerp(s.color.r, color_ab.r, alpha_ab)
            s.color.g = krz.lerp(s.color.g, color_ab.g, alpha_ab)
            s.color.b = krz.lerp(s.color.b, color_ab.b, alpha_ab)

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

class GradientColors(bpy.types.Operator):
    bl_idname = 'cc.gradient_colors'
    bl_label = 'Gradient Colors'
    bl_options = {'REGISTER', 'UNDO'}

    override = bpy.props.BoolProperty(name='Override', default=False)

    select = bpy.props.EnumProperty(
        items=krz.ops.ENUM_SELECT,
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
    color_b = bpy.props.FloatVectorProperty(
        name="End Color", subtype='COLOR_GAMMA',
        min=0, max=1, step=1, default=(1, 1, 1),)

    alpha_a = bpy.props.FloatProperty(name="Start Alpha", min=0, max=1, step=0.1, default=1)
    alpha_b = bpy.props.FloatProperty(name="End Alpha", min=0, max=1, step=0.1, default=1)

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
            override=self.override,
            select=self.select)

        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(GradientColors.bl_idname, text='Gradient Colors')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)

if __name__ == "__main__":
    register()
