import bpy
import math
import struct
import mathutils as m

bl_info = {
    'name': 'Set Loose Vertex Normals',
    'author': 'Tamas Kemenczy',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Set Loose Vertex Normals',
    'description': 'Set normals for the selected vertices',
    'category': 'Mesh'
}

def get_or_create_groups(obj):
    bpy.ops.object.editmode_toggle()

    x_name = 'normal_x'
    y_name = 'normal_y'
    z_name = 'normal_z'

    if x_name not in obj.vertex_groups:
        bpy.ops.object.vertex_group_add()
        x = obj.vertex_groups[-1]
        x.name = x_name
    else:
        x = obj.vertex_groups[x_name]

    if y_name not in obj.vertex_groups:
        bpy.ops.object.vertex_group_add()
        y = obj.vertex_groups[-1]
        y.name = y_name
    else:
        y = obj.vertex_groups[y_name]

    if z_name not in obj.vertex_groups:
        bpy.ops.object.vertex_group_add()
        z = obj.vertex_groups[-1]
        z.name = z_name
    else:
        z = obj.vertex_groups[z_name]

    bpy.ops.object.editmode_toggle()

    return x, y, z

def set_loose_vertex_normals(mesh_obj, gradient_obj):
    normal = gradient_obj.matrix_world * m.Vector((0, 0, 1))
    mesh_obj_matrix_inverse = mesh_obj.matrix_world.copy()
    mesh_obj_matrix_inverse.invert()
    mesh_obj_matrix_inverse.transpose()
    normal = normal * mesh_obj_matrix_inverse
    normal.x = normal.x * 0.5 + 0.5
    normal.y = normal.y * 0.5 + 0.5
    normal.z = normal.z * 0.5 + 0.5
    x_group, y_group, z_group = get_or_create_groups(mesh_obj)

    bpy.ops.object.editmode_toggle()

    vertices = [v.index for v in mesh_obj.data.vertices if v.select]
    x_group.add(vertices, normal.x, type='REPLACE')
    y_group.add(vertices, normal.y, type='REPLACE')
    z_group.add(vertices, normal.z, type='REPLACE')

    bpy.ops.object.editmode_toggle()

class SetLooseVertexNormals(bpy.types.Operator):
    bl_idname = 'mesh.set_line_normals'
    bl_label = 'Set Loose Vertex Normals'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH' and len(context.selected_objects) == 2)

    def execute(self, context):
        aux_objects = list(context.selected_objects)
        aux_objects.remove(context.active_object)
        set_loose_vertex_normals(context.active_object, aux_objects[0])
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(SetLooseVertexNormals.bl_idname, text='Set Loose Vertex Normals')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()
