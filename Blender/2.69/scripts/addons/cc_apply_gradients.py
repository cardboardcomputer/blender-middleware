import bpy
import cc
import mathutils

bl_info = {
    'name': 'Apply Gradients',
    'author': 'Cardboard Computer',
    'blender': (2, 6, 9),
    'description': 'Apply selected gradients to selected geometry',
    'category': 'Cardboard'
}

def apply_gradients(objects, select='POLYGON'):
    import cc_gradient_colors

    meshes = []
    gradients = []

    for obj in objects:
        if 'Gradient' in obj:
            gradients.append(obj)
        elif obj.type == 'MESH':
            meshes.append(obj)

    gradients.sort(key=lambda o: o.name)

    for ref in gradients:
        kwargs = cc_gradient_colors.gradient_to_kwargs(ref)
        for obj in meshes:
            cc_gradient_colors.gradient_colors(
                obj, ref,
                select=select, update_gradient=False,
                **kwargs)

class ApplyGradients(bpy.types.Operator):
    bl_idname = 'cc.apply_gradients'
    bl_label = 'Apply Gradients'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=cc.ops.ENUM_SELECT,
        name='Select', default='POLYGON')

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 1

    def execute(self, context):
        apply_gradients(context.selected_objects, select=self.select)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(ApplyGradients.bl_idname, text='Apply Gradients')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)

if __name__ == "__main__":
    register()
