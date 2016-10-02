import bpy
import krz
import math
import mathutils as m

bl_info = {
    'name': 'Select By Normal',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Select By Normal',
    'description': 'Select faces via normals',
    'category': 'Cardboard'
}

def lerp(a, b, v):
    return a * (1. - v) + b * v

def magnitude(v):
    return math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)

def select_by_normal(obj, ref, threshold):
    p1 = ref.location
    p2 = ref.matrix_world * m.Vector((0, 0, 1))
    direction = (p2 - p1).normalized()

    bpy.ops.object.editmode_toggle()

    for poly in obj.data.polygons:
        f = direction.dot(poly.normal)
        if f >= threshold:
            poly.select = True

    bpy.ops.object.editmode_toggle()

class SelectByNormal(bpy.types.Operator):
    bl_idname = 'cc.select_by_normal'
    bl_label = 'Select By Normal'
    bl_options = {'REGISTER', 'UNDO'}

    threshold = bpy.props.FloatProperty(name="Threshold", min=-1, max=1, step=0.1, default=0)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH'
                and not krz.lines.is_line(obj)
                and len(context.selected_objects) == 2)

    def execute(self, context):
        aux_objects = list(context.selected_objects)
        aux_objects.remove(context.active_object)
        select_by_normal(
            context.active_object,
            aux_objects[0],
            self.threshold)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(SelectByNormal.bl_idname, text='Select By Normal')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()