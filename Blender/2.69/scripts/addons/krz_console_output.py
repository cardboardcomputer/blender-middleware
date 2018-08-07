import bpy
import sys

bl_info = {
    'name': 'Console Output',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 9),
    'description': 'Reroute stdout/stderr to Blender console',
    'category': 'Cardboard'
}

def register():
    import log
    sys.stdout = log.info
    sys.stderr = log.error

def unregister():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__
