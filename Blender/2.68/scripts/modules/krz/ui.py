import bpy

def ui_heading(self, context):
    # self.layout.separator()
    self.layout.label('')
    self.layout.separator()

bpy.types.VIEW3D_MT_object_specials.append(ui_heading)
bpy.types.VIEW3D_MT_edit_mesh_specials.append(ui_heading)
