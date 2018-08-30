import cc
import bpy

bl_info = {
    'name': 'Utils: Selection',
    'author': 'Cardboard Computer',
    'blender': (2, 69, 0),
    'description': 'Selection extensions',
    'category': 'Cardboard'
}

class MESH_UL_selections(bpy.types.UIList):
    def draw_item(self, context, layout, data, item, icon, active_data, active_propname):
        row = layout.row()

        column = row.column()
        column.label(text=item.name, icon='UV_SYNC_SELECT')

        column = row.column()
        column.alignment = 'RIGHT'
        row = column.row(align=True)
        row.alignment = 'RIGHT'
        if item.mode[0]:
            row.label(text='', icon='VERTEXSEL')
        else:
            row.label(text='', icon='LAYER_USED')
        row.separator()
        if item.mode[1]:
            row.label(text='', icon='EDGESEL')
        else:
            row.label(text='', icon='LAYER_USED')
        row.separator()
        if item.mode[2]:
            row.label(text='', icon='FACESEL')
        else:
            row.label(text='', icon='LAYER_USED')
        row.separator()
        row.separator()

class SelectionPanel(bpy.types.Panel):
    bl_label = 'Selections'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    @classmethod
    def poll(self, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def draw(self, context):
        layout = self.layout

        obj = bpy.context.active_object
        active = obj.data.active_selection

        row = layout.row()
        row.template_list('MESH_UL_selections', '', obj.data, 'selections', obj.data, 'active_selection_index')

        col = row.column(align=True)
        col.operator("cc.selection_add", icon='ZOOMIN', text='')
        col.operator("cc.selection_remove", icon='ZOOMOUT', text='')

        if active:
            layout.prop(active, 'name')

        if context.mode == 'EDIT_MESH':
            row = layout.row(align=True)
            row.operator('cc.selection_save', 'Save')
            row.operator('cc.selection_load', 'Load')

def get_unique_name(obj, name):
    if name in obj.data.selections:
        count = 1
        while True:
            n = '%s.%03d' % (name, count)
            if n in obj.data.selections:
                count += 1
                continue
            else:
                name = n
                break
    return name

class SelectionAdd(bpy.types.Operator):
    bl_idname = 'cc.selection_add'
    bl_label = 'Add Selection'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        sel = cc.select.new(obj, cc.select.BASENAME)
        sel.clear()
        obj.data.active_selection = sel
        return {'FINISHED'}

class SelectionRemove(bpy.types.Operator):
    bl_idname = 'cc.selection_remove'
    bl_label = 'Remove Selection'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        active = obj.data.active_selection
        if active:
            active.free()
            obj.data.selections.remove(obj.data.active_selection_index)
        obj.data.active_selection_index = max(0, obj.data.active_selection_index - 1)
        return {'FINISHED'}

class SelectionSave(bpy.types.Operator):
    bl_idname = 'cc.selection_save'
    bl_label = 'Save Selection'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        active = obj.data.active_selection
        if active:
            active.save()
        return {'FINISHED'}

class SelectionLoad(bpy.types.Operator):
    bl_idname = 'cc.selection_load'
    bl_label = 'Load Selection'
    bl_options = {'REGISTER', 'UNDO', 'INTERNAL'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        obj = context.active_object
        active = obj.data.active_selection
        if active:
            active.load()
        return {'FINISHED'}

def available_selections(scene, context):
    obj = context.active_object
    enum = []
    for sel in obj.data.selections:
        enum.append((sel.name, sel.name, sel.name))
    return enum

class SelectionLoadEnum(bpy.types.Operator):
    bl_idname = 'cc.selection_load_enum'
    bl_label = 'Load Selection'
    bl_options = {'REGISTER', 'UNDO'}

    name = bpy.props.EnumProperty(items=available_selections, name='Name')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH' and context.mode == 'EDIT_MESH'

    def execute(self, context):
        obj = context.active_object
        sel = obj.data.selections[self.name]
        sel.load()
        return {'FINISHED'}

class SelectionAddDialog(bpy.types.Operator):
    bl_idname = 'cc.selection_add_dialog'
    bl_label = 'Add Selection'
    bl_options = {'REGISTER', 'UNDO'}

    name = bpy.props.StringProperty(name='Name', default=cc.select.BASENAME)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        layout.prop(self, 'name', '')

    def execute(self, context):
        if not self.name:
            return {'CANCELLED'}
        else:
            cc.select.save(context.active_object, self.name)
            return {'FINISHED'}

    def invoke(self, context, event):
        self.name = get_unique_name(context.active_object, self.name)
        return context.window_manager.invoke_props_dialog(self, width=160)

class SelectionMenu(bpy.types.Menu):
    bl_label = "Selections"
    bl_idname = "CC_MT_selections"

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        self.layout.operator_enum('cc.selection_load_enum', 'name')

def register():
    cc.utils.register(__REGISTER__)

def unregister():
    cc.utils.unregister(__REGISTER__)

__REGISTER__ = (
    MESH_UL_selections,
    SelectionPanel,
    SelectionAdd,
    SelectionRemove,
    SelectionSave,
    SelectionLoad,
    SelectionLoadEnum,
    SelectionAddDialog,
    SelectionMenu,
)
