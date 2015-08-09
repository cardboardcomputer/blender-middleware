import bpy
import krz

bl_info = {
    'name': 'Add Colors',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Add Colors',
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
    alpha = bpy.props.BoolProperty(name='Alpha', default=False)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        add_colors(context.active_object, self.name, self.alpha)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.name = krz.colors.Manager(context.active_object).get_unique_name(self.name)
        self.alpha = krz.lines.is_line(context.active_object)
        return context.window_manager.invoke_props_dialog(self)

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
