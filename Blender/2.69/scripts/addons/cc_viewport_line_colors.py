import bpy
import cc

bl_info = {
    'name': 'Viewport Line Colors',
    'author': 'Cardboard Computer',
    'blender': (2, 6, 9),
    'description': 'Draw lines colors in the viewport when available',
    'category': 'Cardboard'
}

def register():
    cc.ui.install_line_renderer()

def unregister():
    cc.ui.uninstall_line_renderer()

if __name__ == "__main__":
    register()
