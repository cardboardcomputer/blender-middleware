import bpy
import krz
import mathutils

bl_info = {
    'name': 'Light Colors',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Light Colors',
    'description': 'Apply gradients on lines/polygon colors',
    'category': 'Cardboard'
}

DEFAULT_ENERGY = 1.0
DEFAULT_COLOR = mathutils.Color((1, 1, 1))

@krz.ops.editmode
def light_colors(
    obj,
    use_normals=True,
    light_prefix='Light',
    color_layer='',
    select='POLYGON'):

    select = select.lower()

    lights = []
    for l in bpy.context.scene.objects:
        if (l.type == 'EMPTY' and
            l.name.startswith(light_prefix) and
            not l.hide_render):
            lights.append(l)

    final = krz.colors.layer(obj)
    temp = krz.colors.new(obj, '_Temp')
    base = krz.colors.layer(obj, color_layer)

    for sample in temp.itersamples():
        sample.color *= 0

    for light in lights:

        center = light.matrix_world * mathutils.Vector((0, 0, 0))
        radius = (light.scale.x + light.scale.y + light.scale.z) / 3
        if 'color' in light:
            lcolor = krz.colors.hex_to_color(light['color'])
        else:
            lcolor = DEFAULT_COLOR.copy()
        lcolor *= light.get('energy', DEFAULT_ENERGY)

        print(center, radius, lcolor)

        for i, s in enumerate(temp.itersamples()):
            if not s.is_selected(select):
                continue

            vert = obj.matrix_world * s.vertex.co

            if use_normals:
                light_dir = (vert - center).normalized()
                normal = s.vertex.normal
                n_dot_l = 1 - normal.dot(light_dir)
            else:
                n_dot_l = 1

            distance = krz.magnitude(vert - center)
            atten = 1 - min(distance / radius, 1)

            color = lcolor.copy()
            color.v *= atten * n_dot_l

            rcolor = base.samples[i].color

            s.color.r += color.r * rcolor.r
            s.color.g += color.g * rcolor.g
            s.color.b += color.b * rcolor.b

    for i, s in enumerate(final.itersamples()):
        if not sample.is_selected(select):
            continue
        s.color = temp.samples[i].color

    temp.destroy()

class LightColors(bpy.types.Operator):
    bl_idname = 'cc.light_colors'
    bl_label = 'Light Colors'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=krz.ops.ENUM_SELECT,
        name='Select', default='POLYGON')
    use_normals = bpy.props.BoolProperty(name='Use Normals', default=True)
    light_prefix = bpy.props.StringProperty(name='Light Prefix', default='Light')
    color_layer = bpy.props.StringProperty(name='Color Layer', default='')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        aux_objects = list(context.selected_objects)
        aux_objects.remove(context.active_object)

        light_colors(
            context.active_object,
            use_normals=self.use_normals,
            light_prefix=self.light_prefix,
            color_layer=self.color_layer,
            select=self.select)

        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(LightColors.bl_idname, text='Light Colors')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)

if __name__ == "__main__":
    register()
