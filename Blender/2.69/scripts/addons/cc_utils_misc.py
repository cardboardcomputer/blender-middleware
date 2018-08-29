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

@bpy.app.handlers.persistent
def load_pre(scene):
    cc.ops.quicksaving = False
    cc.ops.quicksave = ''

@bpy.app.handlers.persistent
def save_post(scene):
    if not cc.ops.quicksaving:
        bpy.ops.cc.quicksave()

class Quicksave(bpy.types.Operator):
    bl_idname = 'cc.quicksave'
    bl_label = 'Quicksave'
    bl_options = {'REGISTER'}

    def execute(self, context):
        if not bpy.data.is_dirty:
            return {'CANCELLED'}

        if 'BLENDER_QUICKSAVE_PATH' not in os.environ:
            self.report({'ERROR'}, 'BLENDER_QUICKSAVE_PATH environment variable not set.')
            return {'CANCELLED'}

        dirpath = os.environ['BLENDER_QUICKSAVE_PATH']
        basename = bpy.path.basename(bpy.path.ensure_ext(bpy.data.filepath, ''))
        if not basename:
            basename = 'untitled'
        timestamp = ('%.2f' % time.time()).replace('.', '')
        filename = '%s.%s.blend' % (basename, timestamp)

        path = os.path.join(dirpath, filename)

        cc.ops.quicksaving = True
        bpy.ops.wm.save_as_mainfile(
            filepath=path,
            check_existing=False,
            compress=True,
            copy=True,
        )
        cc.ops.quicksaving = False
        cc.ops.quicksave = path

        self.report({'INFO'}, 'Quicksave: %s' % path)
        return {'FINISHED'}

def quicksave_info(panel, context):
    layout = panel.layout
    if cc.ops.quicksave:
        layout.label('(%s)' % cc.ops.quicksave)

def register():
    cc.utils.register(__REGISTER__)

    bpy.app.handlers.load_pre.append(load_pre)
    bpy.app.handlers.save_post.append(save_post)
    bpy.types.INFO_HT_header.append(quicksave_info)

def unregister():
    cc.utils.unregister(__REGISTER__)

    bpy.app.handlers.load_pre.remove(load_pre)
    bpy.app.handlers.save_post.remove(save_post)
    bpy.types.INFO_HT_header.remove(quicksave_info)

__REGISTER__ = (
    Quicksave,
)
