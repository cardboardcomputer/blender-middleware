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

def light_vertex_colors(obj, use_normals=True, use_ref_colors=''):
    lights = []
    for o in bpy.context.scene.objects:
        if o.type == 'LAMP' and not o.hide_render:
            lights.append(o)

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
        lcolor = light.data.color

        for poly in obj.data.polygons:
            if poly.select:
                colors = []

                for idx in poly.vertices:
                    position = obj.data.vertices[idx].co
                    position_abs = position * obj.matrix_world
                    if use_normals:
                        light_dir = (position_abs - center).normalized()
                        normal = obj.data.vertices[idx].normal
                        n_dot_l = 1 - normal.dot(light_dir)
                    else:
                        n_dot_l = 1
                    distance = magnitude(position - center)
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

class LightVertexColors(bpy.types.Operator):
    bl_idname = 'mesh.light_vertex_colors'
    bl_label = 'Light Vertex Colors'
    bl_options = {'REGISTER', 'UNDO'}

    use_normals = bpy.props.BoolProperty(name='Use Normals', default=True)
    use_ref_colors = bpy.props.StringProperty(name='Use Reference Colors', default='')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        light_vertex_colors(context.active_object, use_normals=self.use_normals, use_ref_colors=self.use_ref_colors)
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
