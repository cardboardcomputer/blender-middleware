import bpy
import krz

bl_info = {
    'name': 'Process Colors',
    'author': 'Cardboard Computer',
    'blender': (2, 6, 9),
    'description': 'Apply color operatos on lines/polygon colors',
    'category': 'Cardboard'
}

@krz.ops.editmode
def process_colors(objects):
    for obj in objects:
        if obj.type == 'MESH':
            krz.colors.Manager(obj).exec_color_ops(get_ops(obj))

def get_ops(obj):
    ops = list(obj.data.vertex_color_ops)
    ops.sort(key=lambda o: o.index)
    return [o.op for o in ops if o.op]

def set_ops(obj, ops):
    while obj.data.vertex_color_ops:
        obj.data.vertex_color_ops.remove(0)
    for i, o in enumerate(ops):
        op = obj.data.vertex_color_ops.add()
        op.op = o
        op.index = i

class ColorOp(bpy.types.PropertyGroup):
    op = bpy.props.StringProperty()
    index = bpy.props.IntProperty()

bpy.utils.register_class(ColorOp)

bpy.types.Mesh.vertex_color_ops = bpy.props.CollectionProperty(type=ColorOp)

class ColorOpPanel(bpy.types.Panel):
    bl_label = 'Vertex Color Operations'
    bl_space_type = 'PROPERTIES'
    bl_region_type = 'WINDOW'
    bl_context = 'data'

    @classmethod
    def poll(self, context):
        return context.active_object.type == 'MESH'

    def draw(self, context):
        layout = self.layout
        obj = bpy.context.active_object
        ops = list(obj.data.vertex_color_ops.values())
        ops.sort(key=lambda o: o.index)

        column = layout.column(align=True)

        for op in ops:
            row = column.row(align=True)
            row.prop(op, 'op', '')
            row.operator('cc.color_op_up', '', icon='TRIA_UP').index = op.index
            row.operator('cc.color_op_down', '', icon='TRIA_DOWN').index = op.index
            row.operator('cc.color_op_remove', '', icon='X').index = op.index

        column.operator('cc.color_op_add', 'Add')

        layout.operator('cc.process_colors')

bpy.utils.register_class(ColorOpPanel)

class ColorOpAdd(bpy.types.Operator):
    bl_idname = 'cc.color_op_add'
    bl_label = 'Add Color Op'
    bl_options = {'INTERNAL', 'UNDO'}

    def execute(self, context):
        obj = bpy.context.active_object
        index = len(obj.data.vertex_color_ops)
        op = obj.data.vertex_color_ops.add()
        op.index = index
        return {'FINISHED'}

bpy.utils.register_class(ColorOpAdd)

class ColorOpRemove(bpy.types.Operator):
    bl_idname = 'cc.color_op_remove'
    bl_label = 'Remove Color Op'
    bl_options = {'INTERNAL', 'UNDO'}

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = bpy.context.active_object
        for op in obj.data.vertex_color_ops:
            if op.index == self.index:
                idx = list(obj.data.vertex_color_ops).index(op)
                obj.data.vertex_color_ops.remove(idx)
                break
        for i, op in enumerate(obj.data.vertex_color_ops):
            op.index = i
        return {'FINISHED'}

bpy.utils.register_class(ColorOpRemove)

class ColorOpUp(bpy.types.Operator):
    bl_idname = 'cc.color_op_up'
    bl_label = 'Move Color Op Up'
    bl_options = {'INTERNAL', 'UNDO'}

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = bpy.context.active_object
        ops = get_ops(obj)
        index = self.index
        op = ops[index]
        ops.remove(op)
        index = max(0, index - 1)
        ops.insert(index, op)
        set_ops(obj, ops)
        return {'FINISHED'}

bpy.utils.register_class(ColorOpUp)

class ColorOpDown(bpy.types.Operator):
    bl_idname = 'cc.color_op_down'
    bl_label = 'Move Color Op Down'
    bl_options = {'INTERNAL', 'UNDO'}

    index = bpy.props.IntProperty()

    def execute(self, context):
        obj = bpy.context.active_object
        ops = get_ops(obj)
        index = self.index
        op = ops[index]
        ops.remove(op)
        index = min(len(ops) + 1, index + 1)
        ops.insert(index, op)
        set_ops(obj, ops)
        return {'FINISHED'}

bpy.utils.register_class(ColorOpDown)

class ProcessColors(bpy.types.Operator):
    bl_idname = 'cc.process_colors'
    bl_label = 'Process Colors'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return 'MESH' in (obj.type for obj in context.selected_objects)

    def execute(self, context):
        process_colors(context.selected_objects)
        return {'FINISHED'}

def menu_func(self, context):
    self.layout.operator(ProcessColors.bl_idname, text='Process Colors')

def register():
    bpy.utils.register_module(__name__)
    bpy.types.VIEW3D_MT_edit_mesh_specials.append(menu_func)
    bpy.types.VIEW3D_MT_object_specials.append(menu_func)

def unregister():
    bpy.utils.unregister_module(__name__)
    bpy.types.VIEW3D_MT_object_specials.remove(menu_func)
    bpy.types.VIEW3D_MT_edit_mesh_specials.remove(menu_func)

if __name__ == "__main__":
    register()
