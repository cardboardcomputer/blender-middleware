import bpy
import mathutils

bl_info = {
    'name': 'Set Loose Vertex Colors',
    'author': 'Tamas Kemenczy',
    'version': (0, 1),
    'blender': (2, 6, 3),
    'location': 'View3D > Specials > Set Loose Vertex Colors',
    'description': 'Store loose vertex colors via vertex groups',
    'category': 'Mesh'
}

def get_or_create_groups(obj):
    bpy.ops.object.editmode_toggle()

    if 'red' not in obj.vertex_groups:
        bpy.ops.object.vertex_group_add()
        red = obj.vertex_groups[-1]
        red.name = 'red'
    else:
        red = obj.vertex_groups['red']
    if 'green' not in obj.vertex_groups:
        bpy.ops.object.vertex_group_add()
        green = obj.vertex_groups[-1]
        green.name = 'green'
    else:
        green = obj.vertex_groups['green']
    if 'blue' not in obj.vertex_groups:
        bpy.ops.object.vertex_group_add()
        blue = obj.vertex_groups[-1]
        blue.name = 'blue'
    else:
        blue = obj.vertex_groups['blue']
    if 'alpha' not in obj.vertex_groups:
        bpy.ops.object.vertex_group_add()
        alpha = obj.vertex_groups[-1]
        alpha.name = 'alpha'
    else:
        alpha = obj.vertex_groups['alpha']

    bpy.ops.object.editmode_toggle()

    return red, green, blue, alpha

def get_default_color_and_alpha(obj):
    red, green, blue, alpha = get_or_create_groups(obj)
    bpy.ops.object.editmode_toggle()

    freq = {}
    mesh = obj.data
    vertices = [v for v in mesh.vertices if v.select]
    for vertex in vertices:
        groups = [g.group for g in vertex.groups.values()]
        if (red.index in groups and
            green.index in groups and
            blue.index in groups and
            alpha.index in groups):

            r = red.weight(vertex.index)
            g = green.weight(vertex.index)
            b = blue.weight(vertex.index)
            a = alpha.weight(vertex.index)
            color = (r, g, b, a)
            if color not in freq:
                freq[color] = 0
            freq[color] += 1

    bpy.ops.object.editmode_toggle()

    colors = list(freq.items())
    colors.sort(key=lambda c: c[1])
    if colors:
        c = colors[0][0]
        return mathutils.Color((c[0], c[1], c[2])), c[3]
    else:
        return None, None

def set_loose_vertex_colors(obj, color, alpha_):
    red, green, blue, alpha = get_or_create_groups(obj)

    bpy.ops.object.editmode_toggle()

    mesh = obj.data
    vertices = [v.index for v in mesh.vertices if v.select]
    red.add(vertices, color.r, type='REPLACE')
    green.add(vertices, color.g, type='REPLACE')
    blue.add(vertices, color.b, type='REPLACE')
    alpha.add(vertices, alpha_, type='REPLACE')

    bpy.ops.object.editmode_toggle()
    

class SetLooseVertexColors(bpy.types.Operator):
    bl_idname = 'mesh.set_loose_vertex_colors'
    bl_label = 'Set Loose Vertex Colors'
    bl_options = {'REGISTER', 'UNDO'}

    color = bpy.props.FloatVectorProperty(
        name="Color", subtype='COLOR_GAMMA',
        min=0, max=1, step=1,
    )
    alpha = bpy.props.FloatProperty(
        name="Alpha",
        min=0, max=1, step=1, default=1,
    )

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def invoke(self, context, event):
        color, alpha = get_default_color_and_alpha(context.active_object)
        if color is not None and alpha is not None:
            self.color = color
            self.alpha = alpha

        wm = context.window_manager
        wm.invoke_props_dialog(self)
        return {'RUNNING_MODAL'}

    def execute(self, context):
        set_loose_vertex_colors(context.active_object, self.color, self.alpha)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(SetLooseVertexColors.bl_idname, text='Set Loose Vertex Colors')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()
