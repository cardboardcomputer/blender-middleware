import cc
import bpy

bl_info = {
    'name': 'Utils: Text',
    'author': 'Cardboard Computer',
    'blender': (2, 69, 0),
    'description': 'Various text input features for text editor/console',
    'category': 'Cardboard'
}

T = bpy.ops.text

def set_caret(x, y):
    T.jump(line=y + 1)
    T.move(type='LINE_BEGIN')
    for i in range(x):
        T.move(type='NEXT_CHARACTER')

def delete_line(text):
    line = text.current_line
    lineno = text.current_line_index
    length = len(line.body)
    start = text.current_character
    remaining = length - start

    if remaining == 0:
        T.move_select(type='NEXT_CHARACTER')
    else:
        for i in range(remaining):
            T.move_select(type='NEXT_CHARACTER')
    T.copy()
    T.delete(type='PREVIOUS_CHARACTER')

def have_selection(text):
    return not (
        text.current_line == text.select_end_line and
        text.current_character == text.select_end_character)

def get_selection_range(self):
    sx = self.current_character
    sy = self.current_line_index
    ex = self.select_end_character
    ey = list(self.lines).index(self.select_end_line)

    return ((sx, sy), (ex, ey))

class TextEditorOperator(bpy.types.Operator):
    @classmethod
    def poll(cls, context):
        return (
            type(context.space_data) == bpy.types.SpaceTextEditor and
            context.space_data.text is not None)

class Cut(TextEditorOperator):
    bl_idname = 'text.cut_cc'
    bl_label = 'Cut'

    def execute(self, context):
        space = context.space_data
        text = space.text
        bpy.ops.text.cut()
        text.select_active = False
        return {'FINISHED'}

class Deselect(TextEditorOperator):
    bl_idname = 'text.deselect'
    bl_label = 'Deselect'

    def execute(self, context):
        space = context.space_data
        text = space.text
        start, end = text.get_selection_range()
        char, line = end
        set_caret(char, line)
        text.select_active = False
        return {'FINISHED'}

class DeleteLine(TextEditorOperator):
    bl_idname = 'text.delete_line'
    bl_label = 'Delete Line'
    bl_options = {'UNDO'}

    def execute(self, context):
        space = context.space_data
        text = space.text
        delete_line(text)
        return {'FINISHED'}

class MoveIndent(TextEditorOperator):
    bl_idname = 'text.move_indent'
    bl_label = 'Move To Indent'

    def execute(self, context):
        space = context.space_data
        text = space.text
        start, end = text.get_selection_range()
        char, line = end
        body = text.lines[line].body
        char = len(body) - len(body.lstrip())

        if text.select_active:
            T.move_select(type='LINE_BEGIN')
            for i in range(char):
                T.move_select(type='NEXT_CHARACTER')
        else:
            T.move(type='LINE_BEGIN')
            for i in range(char):
                T.move(type='NEXT_CHARACTER')

        return {'FINISHED'}

MOVE_TYPE_ENUM =  (
    ('LINE_BEGIN', 'Line Begin', 'Line Begin'),
    ('LINE_END', 'Line End', 'Line End'),
    ('FILE_TOP', 'File Top', 'File Top'),
    ('FILE_BOTTOM', 'File Bottom', 'File Bottom'),
    ('PREVIOUS_CHARACTER', 'Previous Character', 'Previous Character'),
    ('NEXT_CHARACTER', 'Next Character', 'Next Character'),
    ('PREVIOUS_WORD', 'Previous Word', 'Previous Word'),
    ('NEXT_WORD', 'Next Word', 'Next Word'),
    ('PREVIOUS_LINE', 'Previous Line', 'Previous Line'),
    ('NEXT_LINE', 'Next Line', 'Next Line'),
    ('PREVIOUS_PAGE', 'Previous Page', 'Previous Page'),
    ('NEXT_PAGE', 'Next Page', 'Next Page'),
)

SELECT_ACTIVE_PROP = bpy.props.BoolProperty()

class ToggleSelect(TextEditorOperator):
    bl_idname = 'text.toggle_select'
    bl_label = 'Toggle Select'

    def execute(self, context):
        space = context.space_data
        text = space.text
        start, end = text.get_selection_range()
        char, line = end
        set_caret(char, line)

        if start == end:
            text.select_active = not text.select_active

        return {'FINISHED'}

class MoveMaybeSelect(TextEditorOperator):
    bl_idname = 'text.move_maybe_select'
    bl_label = 'Move (Maybe) Select'

    type = bpy.props.EnumProperty(name='Type', items=MOVE_TYPE_ENUM, default='LINE_BEGIN')

    def execute(self, context):
        space = context.space_data
        text = space.text

        if text.select_active:
            T.move_select(type=self.type)
        else:
            T.move(type=self.type)

        return {'FINISHED'}

class CopyDeselect(TextEditorOperator):
    bl_idname = 'text.copy_deselect'
    bl_label = 'Copy-Deselect'

    def execute(self, context):
        T.copy()
        T.deselect()
        return {'FINISHED'}

class ToggleComment(TextEditorOperator):
    bl_idname = 'text.toggle_comment'
    bl_label = 'Toggle Comment'

    def execute(self, context):
        space = context.space_data
        text = space.text

        comment = False
        start, end = text.get_selection_range()
        lines = range(start[1], end[1] + 1)

        for lineno in lines:
            body = text.lines[lineno].body
            if body.isspace() or body == '':
                continue
            if not body.strip().startswith('#'):
                comment = True
                break

        if comment:
            T.comment()
            for lineno in lines:
                line = text.lines[lineno]
                body = line.body
                if body.strip() == '#':
                    line.body = ''
        else:
            T.uncomment()

        char, line = end
        set_caret(char + 1, line)
        text.select_active = False

        return {'FINISHED'}

class ConsoleOperator(bpy.types.Operator):
    @classmethod
    def poll(cls, context):
        return type(context.space_data) == bpy.types.SpaceConsole

class ConsoleDeleteForward(ConsoleOperator):
    bl_idname = 'console.delete_forward'
    bl_label = 'Delete Forward'

    def execute(self, context):
        s = context.space_data
        readline = s.history[len(s.history) - 1]
        start = readline.current_character
        readline.body = readline.body[:start]
        return {'FINISHED'}

def register():
    cc.utils.register(__REGISTER__)

def unregister():
    cc.utils.unregister(__REGISTER__)

__REGISTER__ = (
    Cut,
    Deselect,
    DeleteLine,
    MoveIndent,
    ToggleSelect,
    MoveMaybeSelect,
    CopyDeselect,
    ToggleComment,
    ConsoleDeleteForward,
    (bpy.types.Text, 'get_selection_range', get_selection_range),
    (bpy.types.Text, 'select_active', SELECT_ACTIVE_PROP),
)
