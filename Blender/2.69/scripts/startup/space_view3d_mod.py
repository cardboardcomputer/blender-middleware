import bpy

_VIEW3D_HT_header_draw = bpy.types.VIEW3D_HT_header.draw

bpy.types.Scene.show_header_cursor = bpy.props.BoolProperty()
bpy.types.Scene.show_header_object = bpy.props.BoolProperty()

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

bpy.types.VIEW3D_HT_header.draw = view3d_header_draw

def register():
    pass