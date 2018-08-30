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
_save_main = False

def save_blendfile_copy(path):
    global _save_lock
    global _save_main

    _save_lock = True
    _save_main = False
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
    if path.endswith('.blend'):
        dirname = os.path.dirname(path)
    else:
        dirname = path
    if os.path.isdir(dirname):
        return len([name for name in os.listdir(dirname) if name.endswith('.blend')])
    else:
        return 0

def update_backups_prop(self, context):
    for scene in bpy.data.scenes:
        if scene.backups != self.backups:
            scene.backups = self.backups

PROP_BACKUPS = bpy.props.BoolProperty(name='Backups', update=update_backups_prop)

@bpy.app.handlers.persistent
def load_post(scene):
    global _save_path
    global _save_iter
    _save_path = None
    _save_iter = 0
    path = get_scratch_path()
    if os.path.isdir(path):
        _save_path = path
        _save_iter = count_scratch_iterations(path)

@bpy.app.handlers.persistent
def save_post(scene):
    global _save_lock
    global _save_path
    global _save_iter
    global _save_main
    if not _save_lock and bpy.context.scene.backups:
        filename = save_scratch_blendfile(dirty_only=True)
        if filename:
            _save_path = os.path.dirname(filename)
            _save_iter = count_scratch_iterations(_save_path)
        _save_main = True

class Quicksave(bpy.types.Operator):
    bl_idname = 'cc.quicksave'
    bl_label = 'Quicksave'
    bl_options = {'REGISTER'}

    def execute(self, context):
        global _save_path
        global _save_iter
        global _save_main
        filename = save_scratch_blendfile(dirty_only=True and not _save_main)
        if filename:
            _save_path = os.path.dirname(filename)
            _save_iter = count_scratch_iterations(_save_path)
            self.report({'INFO'}, 'Quicksave: %s' % os.path.basename(filename))
        return {'FINISHED'}

class DeleteScratch(bpy.types.Operator):
    bl_idname = 'cc.delete_scratch'
    bl_label = 'Delete Scratch Files'
    bl_options = {'REGISTER'}

    def execute(self, context):
        global _save_path
        global _save_iter
        path = get_scratch_path()
        if os.path.isdir(path):
            names = [name for name in os.listdir(path) if name.endswith('.blend')]
            for name in names:
                filename = os.path.join(path, name)
                os.remove(filename)
            _save_path = ''
            _save_iter = 0
            self.report({'INFO'}, 'Scratch files deleted: %s' % len(names))
        return {'FINISHED'}

def quicksave_info(panel, context):
    global _save_path
    global _save_iter
    layout = panel.layout
    if _save_path:
        layout.label('(%s) %s' % (_save_iter, _save_path))

def cardboard_menu_ext(self, context):
    self.layout.prop(context.scene, 'backups')

def register():
    cc.utils.register(__REGISTER__)
    cc.ui.CardboardMenu.add_section(cardboard_menu_ext, 9000)

    bpy.app.handlers.load_post.append(load_post)
    bpy.app.handlers.save_post.append(save_post)
    bpy.types.INFO_HT_header.append(quicksave_info)

def unregister():
    cc.utils.unregister(__REGISTER__)
    cc.ui.CardboardMenu.remove_section(cardboard_menu_ext)

    bpy.app.handlers.load_post.remove(load_post)
    bpy.app.handlers.save_post.remove(save_post)
    bpy.types.INFO_HT_header.remove(quicksave_info)

__REGISTER__ = (
    Quicksave,
    DeleteScratch,
    (bpy.types.Scene, 'backups', PROP_BACKUPS),
)
