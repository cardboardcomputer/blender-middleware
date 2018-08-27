import bpy
import cc

bl_info = {
    'name': 'Utils: Misc',
    'author': 'Cardboard Computer',
    'blender': (2, 69, 0),
    'description': 'Various (inter)object utilities',
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
    cc.utils.register(__REGISTER__)

def unregister():
    cc.utils.unregister(__REGISTER__)

__REGISTER__ = (
    LegacyUpgrade,
)
