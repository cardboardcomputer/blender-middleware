import bpy
import cc
import mathutils
import re

bl_info = {
    'name': 'Utils: Object',
    'author': 'Cardboard Computer',
    'blender': (2, 69, 0),
    'description': 'Various (inter)object utilities',
    'category': 'Cardboard'
}

EXCLUDE = (
  cc.colors.METADATA_PROP,
)

@cc.ops.editmode
def copy_properties(i, o, pattern='.*', obj=True, data=True):
    p = re.compile(pattern)

    if obj:
        props = {}
        for k, v in i.items():
            if k.startswith('_RNA'):
                continue
            if k in EXCLUDE:
                continue
            if p.match(k):
                props[k] = v
        for k, v in props.items():
            for n in o:
                n[k] = v

    if data and i.data:
        props = {}
        for k, v in i.data.items():
            if k.startswith('_RNA'):
                continue
            if k in EXCLUDE:
                continue
            if p.match(k):
                props[k] = v
        for k, v in props.items():
            for n in o:
                if n.data:
                    n.data[k] = v

class CopyProperties(bpy.types.Operator):
    bl_idname = 'cc.copy_properties'
    bl_label = 'Copy Properties'
    bl_options = {'REGISTER', 'UNDO'}

    pattern = bpy.props.StringProperty(
        name='Pattern', default='.*')
    obj = bpy.props.BoolProperty(
        name="Object", default=True)
    data = bpy.props.BoolProperty(
        name="Object Data", default=True)

    @classmethod
    def poll(cls, context):
        return len(context.selected_objects) > 1

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        copy_properties(context.active_object, context.selected_objects, pattern=self.pattern, obj=self.obj, data=self.data)
        return {'FINISHED'}

def copy_transform(i, o):
    basis = i.matrix_basis
    world = i.matrix_world
    for obj in o:
        obj.matrix_basis = basis.copy()
        obj.matrix_world = world.copy()

class CopyTransform(bpy.types.Operator):
    bl_idname = 'cc.copy_transform'
    bl_label = 'Copy Transform'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return len(bpy.context.selected_objects) > 1

    def execute(self, context):
        copy_transform(context.active_object, context.selected_objects)
        return {'FINISHED'}

@cc.ops.editmode
def transfer_normals(obj, ref, select='VERTEX', from_colors=False):
    normals = cc.lines.normals(obj)

    if from_colors:
        with cc.colors.Sampler(ref) as sampler:
            colors = cc.colors.layer(obj)
            for sample in colors.itersamples():
                if sample.is_selected(select.lower()):
                    point = sample.obj.matrix_world * sample.vertex.co
                    color = sampler.closest(point)
                    normals.set(sample.vertex.index, color.r * 2 - 1, color.g * 2 - 1, color.b * 2 - 1)

    else:
        to_ref = ref.matrix_world.inverted()
        # rotate = ref.matrix_world.to_quaternion()
        for vert in obj.data.vertices:
            if vert.select:
                co = to_ref * (obj.matrix_world * vert.co)
                point, normal, face = ref.closest_point_on_mesh(co)
                # normal = rotate * normal
                normals.set(vert.index, normal.x, normal.y, normal.z)

class TransferNormals(bpy.types.Operator):
    bl_idname = 'cc.transfer_normals'
    bl_label = 'Transfer Normals'
    bl_options = {'REGISTER', 'UNDO'}

    select = bpy.props.EnumProperty(
        items=cc.ops.ENUM_SELECT,
        name='Select', default='VERTEX')
    from_colors = bpy.props.BoolProperty(
        name='From Colors', default=False)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        if not obj:
            return False
        if len(context.selected_objects) == 2:
            ref = list(context.selected_objects)
            ref.remove(context.active_object)
            ref = ref[0]
        else:
            ref = None
        return cc.lines.is_line(obj) and ref and ref.type == 'MESH'

    def execute(self, context):
        aux_objects = list(context.selected_objects)
        aux_objects.remove(context.active_object)

        obj = context.active_object
        ref = aux_objects[0]

        transfer_normals(obj, ref, select=self.select, from_colors=self.from_colors)

        return {'FINISHED'}

class ObjectMenu(bpy.types.Menu):
    bl_label = 'Object'
    bl_idname = 'CC_MT_object'

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'

        layout.operator(CopyProperties.bl_idname, text='Copy Properties')
        layout.operator(CopyTransform.bl_idname, text='Copy Transform')
        layout.operator(TransferNormals.bl_idname, text='Transfer Normals')
        layout.operator('cc.gradient_object', text='Add/Set Gradient')
        layout.operator('cc.gradient_apply', text='Apply Gradients')

def cardboard_menu_ext(self, context):
    self.layout.menu('CC_MT_object')

def register():
    cc.utils.register(__REGISTER__)
    cc.ui.CardboardMenu.add_section(cardboard_menu_ext, 1)

def unregister():
    cc.utils.unregister(__REGISTER__)
    cc.ui.CardboardMenu.remove_section(cardboard_menu_ext)

__REGISTER__ = (
    CopyProperties,
    CopyTransform,
    TransferNormals,
    ObjectMenu,
)
