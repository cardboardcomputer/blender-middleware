import bpy
import krz

bl_info = {
    'name': 'Transfer Colors',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Transfer Colors',
    'description': 'Transfer colors from a reference mesh to another',
    'category': 'Cardboard'
}

@krz.ops.editmode
def transfer_colors(obj, ref, select='ALL'):
    with krz.colors.Sampler(ref) as sampler:
        colors = krz.colors.layer(obj)

        ref_layer_name = krz.colors.layer(ref).name
        ref_alpha_name = '%s.Alpha' % ref_layer_name
        if ref_alpha_name in ref.data.vertex_colors:
            ref_sample_alpha = True
        else:
            ref_sample_alpha = False

        for sample in colors.itersamples():
            if sample.is_selected(select.lower()):
                point = sample.obj.matrix_world * sample.vertex.co
                sample.color = sampler.closest(point)
                if ref_sample_alpha:
                    sample.alpha = sampler.closest(point, layer=ref_alpha_name).v

class TransferColors(bpy.types.Operator):
    bl_idname = 'cc.transfer_colors'
    bl_label = 'Transfer Colors'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=krz.ops.ENUM_SELECT,
        name='Select', default='ALL')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if len(context.selected_objects) == 2:
            ref = list(context.selected_objects)
            ref.remove(context.active_object)
            ref = ref[0]
        else:
            ref = None
        return obj and obj.type == 'MESH' and ref and ref.type == 'MESH'

    def execute(self, context):
        aux_objects = list(context.selected_objects)
        aux_objects.remove(context.active_object)

        obj = context.active_object
        ref = aux_objects[0]

        transfer_colors(obj, ref, select=self.select)

        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(TransferColors.bl_idname, text='Transfer Colors')

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
