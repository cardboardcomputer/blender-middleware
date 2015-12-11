import bpy
import krz
import mathutils
import re

bl_info = {
    'name': 'Copy Properties',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Copy Properties',
    'description': 'Copy properties from one object to another',
    'category': 'Cardboard'
}

EXCLUDE = (
  krz.colors.METADATA_PROP,
)

@krz.ops.editmode
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

def menu_func(self, context):
    self.layout.operator_context = 'INVOKE_DEFAULT'
    self.layout.operator(CopyProperties.bl_idname, text='Copy Properties')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)

if __name__ == "__main__":
    register()
