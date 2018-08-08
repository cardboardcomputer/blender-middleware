import os
import sys
import bpy

output = None
input = None
info = None
error = None
write = None

def reset():
    global output
    global input
    global info
    global error
    global write

    output = Stream('OUTPUT')
    input = Stream('INPUT')
    info = Stream('INFO')
    error = Stream('ERROR')
    write = output.write

class Stream:
    def __init__(self, enum, context=None):
        self.text = ''
        self.enum = enum
        self.line = None
        self.newline = False
        self.context = context
        if not self.context:
            self.context = get_console_context()

    def write(self, text):
        try:
            if not self.context:
                self.context = get_console_context()

            if self.context:
                self.console = getattr(
                    self.context, 'space_data',
                    self.context['space_data'])
                self.scrollback = self.console.scrollback
            else:
                if self.enum == 'ERROR':
                    return sys.__stderr__.write(text)
                else:
                    return sys.__stdout__.write(text)

            line = self.line
            sb = self.scrollback

            if len(sb) == 0:
                return

            text = str(text)
            lines = text.replace('\r\n', '\n').split('\n')

            if ((line and not
                line == sb[len(sb) - 1]) or self.newline):
                self.newline = False
                self.line = line = None

            if line:
                line.body += lines[0]
                lines = lines[1:]

            if lines and lines[len(lines) - 1] == '':
                self.newline = True
                lines = lines[:-1]

            for l in lines:
                bpy.ops.console.scrollback_append(
                    self.context, text=l, type=self.enum)

            self.line = sb[len(sb) - 1]
        except:
            import traceback
            traceback.print_exc(file=sys.__stderr__)

    # no-op interface

    def flush(self):
        pass

    def tell(self):
        return 0

    def read(self, size=-1):
        return ''

    def seek(self, offset, whence=0):
        pass

    def truncate(self, size=None):
        pass

    @property
    def name(self):
        return self.enum

def get_console_context():
    # do nothing while _RestrictContext
    if not hasattr(bpy.context, 'window'):
        return {}

    context = {
        'window': bpy.context.window,
    }

    for screen in bpy.data.screens:
        for area in screen.areas:
            if area.type == 'CONSOLE':
                context['area'] = area
                context['screen'] = screen
                for space in area.spaces:
                    if space.type == 'CONSOLE':
                        context['space_data'] = space
                for region in area.regions:
                    if region.type == 'WINDOW':
                        context['region'] = region
                        return context

    return {}

def capture_streams():
    sys.stdout = info
    sys.stderr = error

def release_streams():
    sys.stdout = sys.__stdout__
    sys.stderr = sys.__stderr__

_console_draw_handle = None

@bpy.app.handlers.persistent
def install(*args, **kwargs):
    global _console_draw_handle

    wm = bpy.context.window_manager

    if wm.capture_console_output:
        reset()

        context = get_console_context()

        if context:
            space = context['space_data']

            if _console_draw_handle:
                space.draw_handler_remove(_console_draw_handle, 'WINDOW')
            _console_draw_handle = space.draw_handler_add(capture_streams, tuple(), 'WINDOW', 'POST_PIXEL')

            capture_streams()

def uninstall(*args, **kwargs):
    global _console_draw_handle

    context = get_console_context()

    if context:
        space = context['space_data']

        if _console_draw_handle:
            space.draw_handler_remove(_console_draw_handle, 'WINDOW')
            _console_draw_handle = None

    release_streams()

def toggle_capture(self, context):
    if self.capture_console_output:
        install()
    else:
        uninstall()

bpy.types.WindowManager.capture_console_output = bpy.props.BoolProperty(
    name='Capture Standard Output', default=False, update=toggle_capture,
    description='Route system output (stdout/stderr) to this console',)

def console_header_draw(self, context):
    layout = self.layout.row()

    layout.template_header()

    if context.area.show_menus:
        layout.menu("CONSOLE_MT_console")

    layout.operator("console.autocomplete", text="Autocomplete")
    layout.prop(context.window_manager, 'capture_console_output')

bpy.types.CONSOLE_HT_header.draw = console_header_draw

def register():
    pass

def unregister():
    pass

reset()
