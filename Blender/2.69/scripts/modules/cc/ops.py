import bpy

ENUM_SELECT = (
    ('ALL', 'All', 'All'),
    ('POLYGON', 'Polygon', 'Polygon'),
    ('VERTEX', 'Vertex', 'Vertex'),
)

def editmode(func):
    """
    Temporarily escape editmode to allow programmatic manipulation of
    mesh data, like vertex groups and colors.
    """
    def wrapped(*args, **kwargs):
        toggled = False
        if bpy.context.mode.startswith('EDIT_'):
            bpy.ops.object.editmode_toggle()
            toggled = True
        ret = func(*args, **kwargs)
        if toggled:
            bpy.ops.object.editmode_toggle()
        # again for mysterious update bug
        if toggled:
            bpy.ops.object.editmode_toggle()
            bpy.ops.object.editmode_toggle()
        return ret
    return wrapped

def show_tool_props(context):
    """
    Show the toolshelf if it isn't already visible.
    """
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for space in area.spaces:
                if space.type == 'VIEW_3D':
                    break
            for region in area.regions:
                if region.type == 'TOOLS':
                    if region.width == 1:
                        ctx = dict(
                            window=context.window,
                            screen=context.screen,
                            area=area,
                            region=region,
                            space_data=space)
                        bpy.ops.view3d.toolshelf(ctx)
                if region.type == 'TOOL_PROPS':
                    if region.height == 1:
                        region.height = 300

def view_text(text):
    if isinstance(text, str):
        text = bpy.data.texts[text]

        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'TEXT_EDITOR':
                    bpy.context.window.screen = screen

                    for space in area.spaces:
                        if space.type == 'TEXT_EDITOR':
                            space.text = text

def get_active_text(screen=None):
    if not screen:
        for screen in bpy.data.screens:
            for area in screen.areas:
                if area.type == 'TEXT_EDITOR':
                    break
    for area in screen.areas:
        if area.type == 'TEXT_EDITOR':
            for space in area.spaces:
                if space.type == 'TEXT_EDITOR':
                    return space.text

class EditmodeContext:
    def __init__(self, mode_wanted):
        self.mode_wanted = mode_wanted
        self.toggled = False

    def __enter__(self):
        self.mode_original = bpy.context.mode
        if self.mode_wanted != self.mode_original:
            bpy.ops.object.editmode_toggle()
            self.toggled = True
        bpy.context.scene.update()
        return self

    def __exit__(self, type, value, traceback):
        if self.toggled:
            bpy.ops.object.editmode_toggle()
        bpy.context.scene.update()
        self.toggled = False

mode_object = EditmodeContext('OBJECT')
mode_edit_mesh = EditmodeContext('EDIT_MESH')
