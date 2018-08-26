import bpy
import krz
import mathutils

bl_info = {
    'name': 'Set Normals',
    'author': 'Cardboard Computer',
    'blender': (2, 6, 9),
    'description': 'Hand-set normals on lines',
    'category': 'Cardboard'
}

@krz.ops.editmode
def set_normals(obj, ref, select='POLYGON'):
    normals = krz.lines.normals(obj)

    normal = ref.matrix_world * mathutils.Vector((0, 0, 1))
    normal -= ref.location
    normal += obj.location

    m = obj.matrix_world.copy()
    m.invert()
    m.transpose()

    normal = normal * m
    normal.normalize()

    for vert in obj.data.vertices:
        if vert.select:
            normals.set(vert.index, normal.x, normal.y, normal.z)

class SetNormals(bpy.types.Operator):
    bl_idname = 'cc.set_normals'
    bl_label = 'Set Normals'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=krz.ops.ENUM_SELECT,
        name='Select', default='POLYGON')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH' and len(context.selected_objects) == 2)

    def execute(self, context):
        aux_objects = list(context.selected_objects)
        aux_objects.remove(context.active_object)
        set_normals(context.active_object, aux_objects[0], self.select)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(SetNormals.bl_idname, text='Set Normals')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()
