import bpy
import cc
from mathutils import Color

bl_info = {
    'name': 'Select By Color',
    'author': 'Cardboard Computer',
    'blender': (2, 6, 9),
    'description': 'Select all faces with the same vertex color of the selected face',
    'category': 'Cardboard'
}

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

def menu_func(self, context):
    self.layout.operator(SelectByColor.bl_idname, text='Select By Color')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()
