import bpy
import krz

bl_info = {
    'name': 'Process Colors',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Process Colors',
    'description': 'Apply color operatos on lines/polygon colors',
    'category': 'Cardboard'
}

@krz.ops.editmode
def process_colors(obj):
    krz.colors.Manager(obj).exec_color_ops()

class ProcessColors(bpy.types.Operator):
    bl_idname = 'cc.process_colors'
    bl_label = 'Process Colors'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        process_colors(context.active_object)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(ProcessColors.bl_idname, text='Process Colors')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()
