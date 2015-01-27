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
        if bpy.context.mode != 'OBJECT':
            bpy.ops.object.editmode_toggle()
            toggled = True
        ret = func(*args, **kwargs)
        if toggled:
            bpy.ops.object.editmode_toggle()

        # again for mysterious update bug
        bpy.ops.object.editmode_toggle()
        bpy.ops.object.editmode_toggle()

        return ret
    return wrapped
