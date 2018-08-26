import bpy
import cc

bl_info = {
    'name': 'Draw Type Menu',
    'author': 'Cardboard Computer',
    'blender': (2, 6, 9),
    'description': 'Shortcut menu setting the maxiumum draw type',
    'category': 'Cardboard'
}

class SetDrawTypeMenu(bpy.types.Menu):
    bl_label = "Draw Type"
    bl_idname = "CC_MT_set_draw_type"

    @classmethod
    def poll(cls, context):
        return context.object

    def draw(self, context):
        layout = self.layout
        layout.props_enum(context.object, 'draw_type')

def menu_func(self, context):
    self.layout.menu(SetDrawTypeMenu.bl_idname)

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.prepend(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_specials.prepend(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()
