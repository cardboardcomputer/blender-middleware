import bpy
import krz

bl_info = {
    'name': 'Transfer Normals',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Transfer Normals',
    'description': 'Generate line normals from reference mesh',
    'category': 'Cardboard'
}

@krz.ops.editmode
def transfer_normals(obj, ref, select='VERTEX'):
    normals = krz.lines.normals(obj)
    for vert in obj.data.vertices:
        if vert.select:
            point, normal, face = ref.closest_point_on_mesh(vert.co)
            normals.set(vert.index, normal.x, normal.y, normal.z)

class TransferNormals(bpy.types.Operator):
    bl_idname = 'cc.transfer_normals'
    bl_label = 'Transfer Normals'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=krz.ops.ENUM_SELECT,
        name='Select', default='VERTEX')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if len(context.selected_objects) == 2:
            ref = list(context.selected_objects)
            ref.remove(context.active_object)
            ref = ref[0]
        else:
            ref = None
        return krz.lines.is_line(obj) and ref and ref.type == 'MESH'

    def execute(self, context):
        aux_objects = list(context.selected_objects)
        aux_objects.remove(context.active_object)

        obj = context.active_object
        ref = aux_objects[0]

        transfer_normals(obj, ref, select=self.select)

        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(TransferNormals.bl_idname, text='Transfer Normals')

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