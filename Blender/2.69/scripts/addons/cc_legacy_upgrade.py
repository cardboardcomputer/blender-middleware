import bpy
import cc

bl_info = {
    'name': 'Upgrade Legacy CC Scenes',
    'author': 'Cardboard Computer',
    'blender': (2, 6, 9),
    'description': 'Upgrade legacy CC scenes',
    'category': 'Cardboard'
}

@cc.ops.editmode
def legacy_upgrade():
    cc.legacy.upgrade()

class LegacyUpgrade(bpy.types.Operator):
    bl_idname = 'cc.legacy_upgrade'
    bl_label = 'Upgrade Legacy CC Scenes'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return True

    def execute(self, context):
        legacy_upgrade()
        return {'FINISHED'}

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
