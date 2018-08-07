import os
import sys
import bpy

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

reset()
