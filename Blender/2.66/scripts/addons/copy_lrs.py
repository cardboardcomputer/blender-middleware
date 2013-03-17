import bpy

bl_info = {
    'name': 'Copy Transform',
    'author': 'Tamas Kemenczy',
    'version': (0, 1),
    'blender': (2, 6, 1),
    'location': 'View3D > Specials > Copy Transform',
    'description': 'Copy a transform from one object to another',
    'category': 'Object'
}

def copy_transform(i, o):
    basis = i.matrix_basis
    world = i.matrix_world
    for obj in o:
        obj.matrix_basis = basis.copy()
        obj.matrix_world = world.copy()

class CopyTransform(bpy.types.Operator):
    bl_idname = 'object.copy_transform'
    bl_label = 'Copy Transform'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(bpy.context.selected_objects) > 1

    def execute(self, context):
        copy_transform(context.active_object, context.selected_objects)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(CopyTransform.bl_idname, text='Copy Transform')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)

if __name__ == "__main__":
    register()
