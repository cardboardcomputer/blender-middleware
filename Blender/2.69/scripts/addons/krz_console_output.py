import bpy
import sys
import log

bl_info = {
    'name': 'Console Output',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 9),
    'description': 'Reroute stdout/stderr to Blender console',
    'category': 'Cardboard'
}

def capture_streams():
    sys.stdout = log.info
    sys.stderr = log.error

def release_streams():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

_handle = None

@bpy.app.handlers.persistent
def install(*args, **kwargs):
    global _handle

    log.reset()

    context = log.get_console_context()

    if context:
        space = context['space_data']

        if _handle:
            space.draw_handler_remove(_handle)
        _handle = space.draw_handler_add(capture_streams, tuple(), 'WINDOW', 'POST_PIXEL')

        capture_streams()

def uninstall(*args, **kwargs):
    global _handle

    context = log.get_console_context()

    if context:
        space = context['space_data']

        if _handle:
            space.draw_handler_remove(_handle)

    release_streams()

def register():
    bpy.app.handlers.load_post.append(install)

def unregister():
    bpy.app.handlers.load_post.remove(install)
    uninstall()
