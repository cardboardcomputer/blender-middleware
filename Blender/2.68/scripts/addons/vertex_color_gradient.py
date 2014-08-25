import bpy
import math
import struct
import mathutils as m

bl_info = {
    'name': 'Vertex Color Gradient',
    'author': 'Tamas Kemenczy',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Vertex Color Gradient',
    'description': 'Apply gradients onto vertex colors',
    'category': 'Mesh'
}

def lerp(a, b, v):
    return a * (1. - v) + b * v

def magnitude(v):
    return math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)

def hex_to_color(val):
    try:
        val = str(val).lower()
    except ValueError:
        return m.Color((1, 0, 1))

    if val == '0':
        val = '000000'
    if len(val) == 3:
        val = val[2] + val[2] + val[1] + val[1] + val[0] + val[0]

    try:
        t = struct.unpack('BBB', bytes.fromhex(val))
    except ValueError:
        return m.Color((1, 0, 1))
    else:
        return m.Color((t[0] / 255.0, t[1] / 255.0, t[2] / 255.0))

def vertex_color_gradient(
    obj,
    ref,
    color_a,
    alpha_a,
    color_b,
    alpha_b,
    blend_type,
    blend_method,
    use_predefined_colors=False,
    use_ref_colors=''):

    p1 = ref.location
    p2 = ref.matrix_world * m.Vector((0, 0, 1))
    direction = p2 - p1

    dest_colors = base_colors = obj.data.vertex_colors.active.data

    if use_predefined_colors:
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

    base_colors_name = obj.data.get(use_ref_colors, '') or obj.data.get('base_vertex_colors', '')
    if base_colors_name in obj.data.vertex_colors:
        base_colors = obj.data.vertex_colors[base_colors_name].data

    for poly in obj.data.polygons:
        if not poly.select:
            continue

        attens = []

        if blend_type == 'LINEAR':
            for idx in poly.vertices:
                vert = obj.data.vertices[idx].co
                vert = obj.matrix_world * vert
                delta = vert - p1
                distance = delta.dot(direction.normalized())
                atten = max(min(distance / direction.length, 1), 0)
                attens.append(atten)

        if blend_type == 'RADIAL':
            for idx in poly.vertices:
                vert = obj.data.vertices[idx].co
                vert = obj.matrix_world * vert
                delta = vert - p1
                distance = magnitude(delta)
                atten = max(min(distance / direction.length, 1), 0)
                attens.append(atten)

        for idx, ptr in enumerate(poly.loop_indices):
            atten = attens[idx]
            color = m.Color((0, 0, 0))

            color_ab = m.Color((0, 0, 0))
            color_ab.r = lerp(color_a.r, color_b.r, atten)
            color_ab.g = lerp(color_a.g, color_b.g, atten)
            color_ab.b = lerp(color_a.b, color_b.b, atten)
            alpha_ab = lerp(alpha_a, alpha_b, atten)

            if blend_method == 'REPLACE':
                color = color_ab

            if blend_method == 'MIX':
                ref_color = base_colors[ptr].color.copy()
                color.r = lerp(ref_color.r, color_ab.r, alpha_ab)
                color.g = lerp(ref_color.g, color_ab.g, alpha_ab)
                color.b = lerp(ref_color.b, color_ab.b, alpha_ab)

            if blend_method == 'MULTIPLY':
                color = base_colors[ptr].color.copy()
                color.r *= color_ab.r;
                color.g *= color_ab.g;
                color.b *= color_ab.b;

            if blend_method == 'ADD':
                color = base_colors[ptr].color.copy()
                color.r += color_ab.r;
                color.g += color_ab.g;
                color.b += color_ab.b;

            if blend_method == 'SUBTRACT':
                color = base_colors[ptr].color.copy()
                color.r -= color_ab.r;
                color.g -= color_ab.g;
                color.b -= color_ab.b;

            dest_colors[ptr].color = color

class VertexColorGradient(bpy.types.Operator):
    bl_idname = 'mesh.vertex_color_gradient'
    bl_label = 'Vertex Color Gradient'
    bl_options = {'REGISTER', 'UNDO'}

    use_predefined_colors = bpy.props.BoolProperty(name='Use Predefined', default=False)

    blend_type = bpy.props.EnumProperty(
        items=(
            ('LINEAR', 'Linear', 'Linear'),
            ('RADIAL', 'Radial', 'Radial'),
            ),
        name='Type', default='LINEAR')

    blend_method = bpy.props.EnumProperty(
        items=(
            ('SUBTRACT', 'Subtract', 'Subtract'),
            ('ADD', 'Add', 'Add'),
            ('MULTIPLY', 'Multiply', 'Multiply'),
            ('MIX', 'Mix', 'Mix'),
            ('REPLACE', 'Replace', 'Replace'),
            ),
        name='Method', default='REPLACE')

    color_a = bpy.props.FloatVectorProperty(
        name="Start Color", subtype='COLOR_GAMMA',
        min=0, max=1, step=1,
    )
    color_b = bpy.props.FloatVectorProperty(
        name="End Color", subtype='COLOR_GAMMA',
        min=0, max=1, step=1, default=(1, 1, 1),
    )

    alpha_a = bpy.props.FloatProperty(name="Start Alpha", min=0, max=1, step=0.1, default=1)
    alpha_b = bpy.props.FloatProperty(name="End Alpha", min=0, max=1, step=0.1, default=1)

    use_ref_colors = bpy.props.StringProperty(name='Use Reference Colors', default='')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH' and len(context.selected_objects) == 2)

    def execute(self, context):
        aux_objects = list(context.selected_objects)
        aux_objects.remove(context.active_object)
        vertex_color_gradient(
            context.active_object,
            aux_objects[0],
            self.color_a,
            self.alpha_a,
            self.color_b,
            self.alpha_b,
            self.blend_type,
            self.blend_method,
            use_predefined_colors=self.use_predefined_colors,
            use_ref_colors=self.use_ref_colors)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(VertexColorGradient.bl_idname, text='Vertex Color Gradient')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)

if __name__ == "__main__":
    register()
