import bpy
import krz

bl_info = {
    'name': 'Upgrade Legacy KRZ Scenes',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Legacy Upgrade',
    'description': 'Upgrade legacy KRZ scenes',
    'category': 'Cardboard'
}

@krz.ops.editmode
def legacy_upgrade():
    krz.legacy.upgrade()

class TransferColors(bpy.types.Operator):
    bl_idname = 'cc.legacy_upgrade'
    bl_label = 'Upgrade Legacy KRZ Scenes'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        return {'FINISHED'}

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
