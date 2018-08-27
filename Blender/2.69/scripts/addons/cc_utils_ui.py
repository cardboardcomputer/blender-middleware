import bpy
import cc

bl_info = {
    'name': 'Utils: UI',
    'author': 'Cardboard Computer',
    'blender': (2, 6, 9),
    'description': 'Various global UI/menu additions',
    'category': 'Cardboard'
}

class DrawTypeMenu(bpy.types.Menu):
    bl_label = "Draw Type"
    bl_idname = "CC_MT_set_draw_type"

    @classmethod
    def poll(cls, context):
        return context.object

    def draw(self, context):
        layout = self.layout
        layout.props_enum(context.object, 'draw_type')

__REGISTER__ = (
    DrawTypeMenu,
)

def specials_menu_ext(self, context):
    self.layout.menu(DrawTypeMenu.bl_idname)

def register():
    cc.ui.install_line_renderer()

    for cls in __REGISTER__:
        bpy.utils.register_class(cls)

    bpy.types.VIEW3D_MT_object_specials.prepend(specials_menu_ext)

def unregister():
    cc.ui.uninstall_line_renderer()

    for cls in __REGISTER__:
        bpy.utils.unregister_class(cls)

    bpy.types.VIEW3D_MT_object_specials.remove(specials_menu_ext)
