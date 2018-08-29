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

_save_iter = 0
_save_path = None
_save_lock = False

def save_blendfile_copy(path):
    global _save_lock

    _save_lock = True
    bpy.ops.wm.save_as_mainfile(
        filepath=path,
        check_existing=False,
        compress=True,
        copy=True,
    )
    _save_lock = False

def get_scratch_path():
    subdir = bpy.path.basename(bpy.path.ensure_ext(bpy.data.filepath, '.scratch'))
    if 'BLENDER_SCRATCH_PATH' in os.environ:
        dirname = os.environ['BLENDER_SCRATCH_PATH']
    elif bpy.data.filepath:
        dirname = os.path.dirname(bpy.data.filepath)
    else:
        dirname = bpy.context.user_preferences.filepaths.temporary_directory
        subdir = 'untitled.scratch'
    return os.path.join(dirname, subdir)

def get_filename_timestamp():
    basename = bpy.path.basename(bpy.path.ensure_ext(bpy.data.filepath, ''))
    if not basename:
        basename = 'untitled'
    timestamp = ('%.2f' % time.time()).replace('.', '')
    filename = '%s.%s.blend' % (basename, timestamp)
    return filename

def save_scratch_blendfile(dirpath=None, dirty_only=False):
    if dirty_only and not bpy.data.is_dirty:
        return None
    if not dirpath:
        dirpath = get_scratch_path()
    os.makedirs(dirpath, exist_ok=True)
    filename = get_filename_timestamp()
    path = os.path.join(dirpath, filename)
    save_blendfile_copy(path)
    return path

def count_scratch_iterations(path):
    dirname = os.path.dirname(path)
    return len([name for name in os.listdir(dirname) if name.endswith('.blend')])

def update_backups_prop(self, context):
    for scene in bpy.data.scenes:
        if scene.backups != self.backups:
            scene.backups = self.backups

PROP_BACKUPS = bpy.props.BoolProperty(name='Backups', update=update_backups_prop)

@bpy.app.handlers.persistent
def load_pre(scene):
    global _save_path
    global _save_iter
    _save_path = None
    _save_iter = 0

@bpy.app.handlers.persistent
def save_post(scene):
    global _save_lock
    global _save_path
    global _save_iter
    if not _save_lock and bpy.context.scene.backups:
        path = save_scratch_blendfile(dirty_only=True)
        if path:
            _save_path = path
            _save_iter = count_scratch_iterations(path)

class Quicksave(bpy.types.Operator):
    bl_idname = 'cc.quicksave'
    bl_label = 'Quicksave'
    bl_options = {'REGISTER'}

    def execute(self, context):
        global _save_path
        global _save_iter
        path = save_scratch_blendfile(dirty_only=True)
        if path:
            _save_path = path
            _save_iter = count_scratch_iterations(path)
            self.report({'INFO'}, 'Quicksave: %s' % os.path.basename(path))
        return {'FINISHED'}

def quicksave_info(panel, context):
    global _save_path
    global _save_iter
    layout = panel.layout
    if _save_path:
        layout.label('(%s) %s' % (_save_iter, os.path.dirname(_save_path)))

def cardboard_menu_ext(self, context):
    self.layout.prop(context.scene, 'backups')

def register():
    cc.utils.register(__REGISTER__)
    cc.ui.CardboardMenu.add_section(cardboard_menu_ext, 9000)

    bpy.app.handlers.load_pre.append(load_pre)
    bpy.app.handlers.save_post.append(save_post)
    bpy.types.INFO_HT_header.append(quicksave_info)

def unregister():
    cc.utils.unregister(__REGISTER__)
    cc.ui.CardboardMenu.remove_section(cardboard_menu_ext)

    bpy.app.handlers.load_pre.remove(load_pre)
    bpy.app.handlers.save_post.remove(save_post)
    bpy.types.INFO_HT_header.remove(quicksave_info)

__REGISTER__ = (
    Quicksave,
    (bpy.types.Scene, 'backups', PROP_BACKUPS),
)
