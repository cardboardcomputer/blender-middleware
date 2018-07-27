import bpy
import krz
import bmesh

bl_info = {
    'name': 'Mesh Boolean',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 9),
    'location': 'View3D > Specials > Boolean',
    'description': 'Edit-mode boolean operations',
    'category': 'Cardboard'
}

PART_A = '_Boolean.A'
PART_B = '_Boolean.B'

@krz.ops.editmode
def mesh_boolean(ctx, obj, mode='DIFFERENCE'):
    # remember state
    active = ctx.active_object
    selected = ctx.selected_objects

    # clean up existing temp objects, reset state
    for name in (PART_A, PART_B):
        if name in ctx.scene.objects:
            ctx.scene.objects.unlink(ctx.scene.objects[name])
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name])
        if name in bpy.data.meshes:
            bpy.data.meshes.remove(bpy.data.meshes[name])

    # create new temp objects
    mesh_a = obj.data.copy()
    mesh_a.name = PART_A
    obj_a = bpy.data.objects.new(PART_A, mesh_a)
    ctx.scene.objects.link(obj_a)
    ctx.scene.update()

    # clear selection
    bpy.ops.object.select_all(action='DESELECT')

    # select part a
    obj_a.select = True
    ctx.scene.objects.active = obj_a
    ctx.scene.update();

    # separate selection into part b
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.separate(type='SELECTED')
    obj_b = ctx.scene.objects['%s.001' % PART_A]
    obj_b.name = PART_B
    mesh_b = obj_b.data
    mesh_b.name = PART_B
    bpy.ops.object.editmode_toggle()

    # add and apply boolean modifier
    mod = obj_a.modifiers.new(name='Boolean', type='BOOLEAN')
    mod.operation = mode
    mod.object = obj_b
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

    # revert selection
    bpy.ops.object.select_all(action='DESELECT')

    for obj in selected:
        obj.select = True
    ctx.scene.objects.active = active

    # update in place
    mesh = bmesh.new()
    mesh.from_mesh(mesh_a)
    mesh.to_mesh(obj.data)

    # remove temp objects
    ctx.scene.objects.unlink(obj_b)
    bpy.data.objects.remove(obj_b)
    bpy.data.meshes.remove(mesh_b)
    ctx.scene.objects.unlink(obj_a)
    bpy.data.objects.remove(obj_a)
    bpy.data.meshes.remove(mesh_a)

class MeshBoolean(bpy.types.Operator):
    bl_idname = 'cc.mesh_boolean'
    bl_label = 'Mesh Boolean'
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.EnumProperty(
        items=(('DIFFERENCE', 'Difference', 'Difference'),
               ('UNION', 'Union', 'Union'),
               ('INTERSECT', 'Intersect', 'Intersect')),
        name='Operation', default='DIFFERENCE')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        mesh_boolean(context, context.active_object, self.mode)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(MeshBoolean.bl_idname, text='Boolean')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()
