import bpy
import krz

bl_info = {
    'name': 'Add Colors',
    'author': 'Cardboard Computer',
    'blender': (2, 6, 9),
    'description': 'Add a new color set',
    'category': 'Cardboard'
}

@krz.ops.editmode
def add_colors(obj, name, alpha=False):
    colors = krz.colors.new(obj, name, alpha=alpha)
    colors.activate()

class AddColors(bpy.types.Operator):
    bl_idname = 'cc.add_colors'
    bl_label = 'Add Colors'
    bl_options = {'REGISTER', 'UNDO'}

    name = bpy.props.StringProperty(name='Name', default=krz.colors.BASENAME)
    alpha = bpy.props.BoolProperty(name='Alpha', default=True)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def draw(self, context):
        layout = self.layout

        row = layout.split(align=True, percentage=0.7)
        row.prop(self, 'name', '')
        row.prop(self, 'alpha', toggle=True)

    def execute(self, context):
        context.space_data.viewport_shade = 'TEXTURED'
        add_colors(context.active_object, self.name, self.alpha)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.name = krz.colors.Manager(context.active_object).get_unique_name(self.name)
        self.alpha = krz.lines.is_line(context.active_object) or self.alpha
        return context.window_manager.invoke_props_dialog(self, width=160)

def menu_func(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(AddColors.bl_idname, text='Add Colors', icon='SPACE3')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()
