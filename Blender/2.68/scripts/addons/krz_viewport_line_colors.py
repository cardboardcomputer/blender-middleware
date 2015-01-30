import bpy
import krz

bl_info = {
    'name': 'Viewport Line Colors',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D',
    'description': 'Draw lines colors in the viewport when available',
    'category': 'Cardboard'
}

def register():
    krz.ui.install_line_renderer()

def unregister():
    krz.ui.uninstall_line_renderer()

if __name__ == "__main__":
    register()
