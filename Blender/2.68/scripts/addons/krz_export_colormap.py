import os
import bpy
import krz

bl_info = {
    'name': 'Export Colormap (.png)',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'File > Import-Export > Colormap (.png)',
    'description': 'Export an object\'s vertex colormap',
    'category': 'Cardboard',
}

def export_colormap(obj, filepath, colormap=''):
    if not colormap:
        colormap = krz.colors.Manager(obj).get_export_colormap()
        if colormap:
            colormap = colormap.name
    colormap = krz.colors.colormap(obj, colormap)
    image = colormap.generate_image()
    image.filepath_raw = filepath
    image.save()
    image.user_clear()
    bpy.data.images.remove(image)

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
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_import)
    bpy.types.INFO_MT_file_export.append(menu_export)

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_import)
    bpy.types.INFO_MT_file_export.remove(menu_export)

if __name__ == "__main__":
    register()