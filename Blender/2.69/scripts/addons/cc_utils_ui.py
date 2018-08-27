import bpy
import cc

bl_info = {
    'name': 'Utils: UI',
    'author': 'Cardboard Computer',
    'blender': (2, 69, 0),
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

_VIEW3D_HT_header_draw = bpy.types.VIEW3D_HT_header.draw

def view3d_header_draw(self, context):
    _VIEW3D_HT_header_draw(self, context)

    s = context.scene
    obj = context.active_object
    layout = self.layout

    row = layout.row(align=True)
    row.prop(s, 'show_header_object', '', icon='OBJECT_DATAMODE', toggle=True)
    if s.show_header_object and obj:
        row = row.row(align=True)
        row.scale_x = 0.8
        r = row.row(align=True)
        r.scale_x = 0.8
        r.prop(obj, 'name', '')
        data = obj.data
        if data:
            icon = '%s_DATA' % obj.type
            row.prop(data, 'name', '', icon=icon)
            if obj.type == 'ARMATURE':
                row.prop(context.active_bone, 'name', '', icon='BONE_DATA')

    row = layout.row(align=True)
    row.prop(s, 'show_header_cursor', '', icon='CURSOR', toggle=True)
    if s.show_header_cursor:
        row.prop(s, 'cursor_location', 'X', index=0)
        row.prop(s, 'cursor_location', 'Y', index=1)
        row.prop(s, 'cursor_location', 'Z', index=2)

def install_view3d_header():
    bpy.types.Scene.show_header_cursor = bpy.props.BoolProperty()
    bpy.types.Scene.show_header_object = bpy.props.BoolProperty()
    bpy.types.VIEW3D_HT_header.draw = view3d_header_draw

def uninstall_view3d_header():
    if hasattr(bpy.types.Scene, 'show_header_cursor'):
        delattr(bpy.types.Scene, 'show_header_cursor')

    if hasattr(bpy.types.Scene, 'show_header_object'):
        delattr(bpy.types.Scene, 'show_header_object')

    bpy.types.VIEW3D_HT_header.draw = _VIEW3D_HT_header_draw

def object_specials_menu_ext(self, context):
    self.layout.menu(DrawTypeMenu.bl_idname)

def editmesh_specials_menu_ext(self, context):
    self.layout.menu('CC_MT_colors')

def register():
    cc.utils.register(__REGISTER__)

    cc.ui.install_line_renderer()
    cc.log.install_output_capture()

    install_view3d_header()

    bpy.types.VIEW3D_MT_object_specials.prepend(cc.ui.draw_cardboard_menu)
    bpy.types.VIEW3D_MT_object_specials.prepend(object_specials_menu_ext)
    bpy.types.VIEW3D_MT_edit_mesh_specials.prepend(editmesh_specials_menu_ext)

def unregister():
    cc.utils.unregister(__REGISTER__)

    cc.ui.uninstall_line_renderer()
    cc.log.uninstall_output_capture()

    uninstall_view3d_header()

    bpy.types.VIEW3D_MT_object_specials.remove(object_specials_menu_ext)
    bpy.types.VIEW3D_MT_object_specials.remove(cc.ui.draw_cardboard_menu)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(editmesh_specials_menu_ext)

__REGISTER__ = (
    cc.ui.CardboardMenu,
    DrawTypeMenu,
)
