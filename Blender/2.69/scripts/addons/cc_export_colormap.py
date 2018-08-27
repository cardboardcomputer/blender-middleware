import os
import bpy
import cc

bl_info = {
    'name': 'Export: Colormap (.png)',
    'author': 'Cardboard Computer',
    'blender': (2, 69, 0),
    'description': 'Export an object\'s vertex colormap',
    'category': 'Cardboard',
}

def export_colormap(obj, filepath, colormap=''):
    if not colormap:
        colormap = cc.colors.Manager(obj).get_export_colormap()
        if colormap:
            colormap = colormap.name

    colormap = cc.colors.colormap(obj, colormap)

    name, ext = os.path.splitext(filepath)
    filepath = '%s%s%s' % (name, colormap.name, ext)

    image = colormap.generate_image()
    image.filepath_raw = filepath
    image.save()
    image.user_clear()
    size = image.size[0]
    bpy.data.images.remove(image)

    with open(filepath, 'a') as fp:
        fp.write('\x1a')
        fp.write('COLORMAP\0')
        fp.write('%i' % size)
        fp.write('\0')
        fp.write('%i' % colormap.get_stride())
        fp.write('\0')
        fp.write('\0'.join(colormap.get_layers()))

class ColormapExporter(bpy.types.Operator):
    bl_idname = 'cc.export_colormap'
    bl_label = 'Export Colormap'

    filepath = bpy.props.StringProperty(
        subtype='FILE_PATH',)
    check_existing = bpy.props.BoolProperty(
        name="Check Existing",
        description="Check and warn on overwriting existing files",
        default=True,
        options={'HIDDEN'},)
    colormap = bpy.props.StringProperty(
        name='Colormap', default='')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def execute(self, context):
        export_colormap(
            context.active_object,
            self.filepath,
            self.colormap)
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = bpy.path.ensure_ext(bpy.data.filepath, ".png")
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_import(self, context):
    self.layout.operator(ColormapExporter.bl_idname, text="Colormap (.png)")

def menu_export(self, context):
    self.layout.operator(ColormapExporter.bl_idname, text="Colormap (.png)")

def register():
    cc.utils.register(__REGISTER__)

    bpy.types.INFO_MT_file_import.append(menu_import)
    bpy.types.INFO_MT_file_export.append(menu_export)

def unregister():
    cc.utils.unregister(__REGISTER__)

    bpy.types.INFO_MT_file_import.remove(menu_import)
    bpy.types.INFO_MT_file_export.remove(menu_export)

__REGISTER__ = (
    ColormapExporter,
)
