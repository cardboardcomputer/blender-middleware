import bpy
import math
import mathutils

bl_info = {
    'name': 'Light Vertex Colors',
    'author': 'Tamas Kemenczy',
    'version': (0, 1),
    'blender': (2, 6, 3),
    'location': 'View3D > Specials > Light Vertex Colors',
    'description': 'Apply per-vertex lighting',
    'category': 'Mesh'
}

def magnitude(v):
    return math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)

def get_lights():
    lights = []
    for o in bpy.context.scene.objects:
        if o.type == 'LAMP' and not o.hide_render:
            lights.append(o)
    return lights

def get_or_create_line_color_groups(obj, index):
    red_name = 'red_%i' % index
    green_name = 'green_%i' % index
    blue_name = 'blue_%i' % index
    alpha_name = 'alpha_%i' % index

    if red_name not in obj.vertex_groups:
        bpy.ops.object.vertex_group_add()
        red = obj.vertex_groups[-1]
        red.name = red_name
    else:
        red = obj.vertex_groups[red_name]
    if green_name not in obj.vertex_groups:
        bpy.ops.object.vertex_group_add()
        green = obj.vertex_groups[-1]
        green.name = green_name
    else:
        green = obj.vertex_groups[green_name]
    if blue_name not in obj.vertex_groups:
        bpy.ops.object.vertex_group_add()
        blue = obj.vertex_groups[-1]
        blue.name = blue_name
    else:
        blue = obj.vertex_groups[blue_name]
    if alpha_name not in obj.vertex_groups:
        bpy.ops.object.vertex_group_add()
        alpha = obj.vertex_groups[-1]
        alpha.name = alpha_name
    else:
        alpha = obj.vertex_groups[alpha_name]

    return red, green, blue, alpha

def light_vertex_colors_mesh(obj, use_normals=True, use_ref_colors=''):
    lights = get_lights()
    vcolors = obj.data.vertex_colors.active.data
    use_ref_colors = use_ref_colors or obj.data.get('base_vertex_colors', '')
    if use_ref_colors:
        rcolors = []
        for x in obj.data.vertex_colors[use_ref_colors].data:
            rcolors.append(x.color)
    else:
        rcolors = []
        for i in range(len(vcolors)):
            rcolors.append(mathutils.Color((1, 1, 1)))

    for poly in obj.data.polygons:
        if poly.select:
            for idx, ptr in enumerate(poly.loop_indices):
                vcolors[ptr].color = mathutils.Color((0, 0, 0))

    for light in lights:
        center = light.location
        radius = light.data.distance
        lcolor = light.data.color * light.data.energy

        for poly in obj.data.polygons:
            if poly.select:
                colors = []

                for idx in poly.vertices:
                    position = obj.data.vertices[idx].co
                    position_abs = obj.matrix_world * position
                    if use_normals:
                        light_dir = (position_abs - center).normalized()
                        normal = obj.data.vertices[idx].normal
                        n_dot_l = 1 - normal.dot(light_dir)
                    else:
                        n_dot_l = 1
                    distance = magnitude(position_abs - center)
                    atten = 1 - min(distance / radius, 1)
                    color = lcolor.copy()
                    color.v *= atten * n_dot_l
                    colors.append(color)

                for idx, ptr in enumerate(poly.loop_indices):
                    color = colors[idx]
                    vcolor = vcolors[ptr].color.copy()
                    rcolor = rcolors[ptr]
                    vcolor.r += color.r * rcolor.r
                    vcolor.g += color.g * rcolor.g
                    vcolor.b += color.b * rcolor.b
                    vcolors[ptr].color = vcolor

def light_vertex_colors_lines(obj, line_color_index=0, line_ref_color_index=0):
    base_vertex_colors = obj.data.get('base_vertex_colors')
    if base_vertex_colors is not None:
        line_ref_color_index = int(base_vertex_colors)
    lights = get_lights()
    red, green, blue, alpha = get_or_create_line_color_groups(obj, line_color_index)
    red_, green_, blue_, alpha_ = get_or_create_line_color_groups(obj, line_ref_color_index)

    red.add([v.index for v in obj.data.vertices], 0, type='REPLACE')
    green.add([v.index for v in obj.data.vertices], 0, type='REPLACE')
    blue.add([v.index for v in obj.data.vertices], 0, type='REPLACE')
    alpha.add([v.index for v in obj.data.vertices], 0, type='REPLACE')

    for light in lights:
        center = light.location
        radius = light.data.distance
        lcolor = light.data.color * light.data.energy

        for vertex in obj.data.vertices:
            if vertex.select:
                position = vertex.co
                position_abs = obj.matrix_world * position
                distance = magnitude(position_abs - center)
                atten = 1 - min(distance / radius, 1)
                color = lcolor.copy()
                color.v *= atten
                r = red.weight(vertex.index)
                g = green.weight(vertex.index)
                b = blue.weight(vertex.index)
                a = alpha.weight(vertex.index)
                r += color.r * red_.weight(vertex.index)
                g += color.g * green_.weight(vertex.index)
                b += color.b * blue_.weight(vertex.index)
                a = alpha_.weight(vertex.index)
                red.add([vertex.index], r, type='REPLACE')
                green.add([vertex.index], g, type='REPLACE')
                blue.add([vertex.index], b, type='REPLACE')
                alpha.add([vertex.index], a, type='REPLACE')

class LightVertexColors(bpy.types.Operator):
    bl_idname = 'mesh.light_vertex_colors'
    bl_label = 'Light Vertex Colors'
    bl_options = {'REGISTER', 'UNDO'}

    use_normals = bpy.props.BoolProperty(name='Use Normals', default=True)
    use_ref_colors = bpy.props.StringProperty(name='Use Reference Colors', default='')

    line_color_index = bpy.props.IntProperty(name='Line Color Index', default=0)
    line_ref_color_index = bpy.props.IntProperty(name='Reference Line Color Index', default=0)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        if len(context.active_object.data.polygons):
            light_vertex_colors_mesh(
                context.active_object,
                use_normals=self.use_normals,
                use_ref_colors=self.use_ref_colors)
        else:
            light_vertex_colors_lines(
                context.active_object,
                line_color_index=self.line_color_index,
                line_ref_color_index=self.line_ref_color_index)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(LightVertexColors.bl_idname, text='Light Vertex Colors')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)

if __name__ == "__main__":
    register()
