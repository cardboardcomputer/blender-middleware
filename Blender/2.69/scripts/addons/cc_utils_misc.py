import cc
import os
import bpy
import time

bl_info = {
    'name': 'Utils: Misc',
    'author': 'Cardboard Computer',
    'blender': (2, 69, 0),
    'description': 'Various (inter)object utilities',
    'category': 'Cardboard'
}

class Quicksave(bpy.types.Operator):
    bl_idname = 'cc.quicksave'
    bl_label = 'Quicksave'
    bl_options = {'REGISTER'}

    def execute(self, context):
        dirpath = os.environ.get(
            'BLENDER_QUICKSAVE_PATH',
            context.user_preferences.filepaths.temporary_directory)
        basename = bpy.path.basename(bpy.path.ensure_ext(bpy.data.filepath, ''))
        if not basename:
            basename = 'untitled'
        timestamp = ('%.2f' %time.time()).replace('.', '')
        filename = '%s.%s.blend' % (basename, timestamp)

        path = os.path.join(dirpath, filename)

        bpy.ops.wm.save_as_mainfile(
            filepath=path,
            check_existing=False,
            compress=True,
            copy=True,
        )

        self.report({'INFO'}, 'Quicksave: %s' % path)
        return {'FINISHED'}

__REGISTER__ = (
    Quicksave,
)

def register():
    cc.utils.register(__REGISTER__)

def unregister():
    cc.utils.unregister(__REGISTER__)
