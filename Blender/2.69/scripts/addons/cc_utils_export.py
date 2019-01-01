import os
import cc
import bpy
import mathutils

bl_info = {
    'name': 'Utils: Export',
    'author': 'Cardboard Computer',
    'blender': (2, 69, 0),
    'description': 'Various export utilities',
    'category': 'Cardboard'
}

EXPORT_SCENE_NAMES = (
    'Export', 'export',
    '_Export', '_export',
    '__Export__', '__export__',
)

def update_autoexport_prop(self, context):
    if self.autoexport and export not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(export)
    if not self.autoexport and export in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.remove(export)

PROP_AUTOEXPORT = bpy.props.BoolProperty(
    name='Auto-export', update=update_autoexport_prop,
    description='Auto export lines and colormap textures on save'
)

def get_export_scene():
    for name in EXPORT_SCENE_NAMES:
        if name in bpy.data.scenes:
            return bpy.data.scenes[name]
    return bpy.context.scene

def export(datapath=None):
    blendname = os.path.splitext(os.path.basename(bpy.data.filepath))[0]

    if datapath is None:
        datapath = os.path.join(os.path.dirname(bpy.data.filepath), '%s.data' % blendname)
        infopath = '%s.data' % blendname
    else:
        infopath = datapath

    lines = []
    colormaps = []
    scene = get_export_scene()

    for obj in scene.objects:
        if cc.lines.is_line(obj):
            lines.append(obj)
        if obj.type == 'MESH':
            colormap = cc.colors.Manager(obj).get_export_colormap()
            if colormap:
                colormaps.append(obj)

    if lines or colormaps:
        if not os.path.exists(datapath):
            os.mkdir(datapath)

    if lines:
        import cc_export_lines
        for obj in lines:
            objname = obj.name
            if objname.endswith('.Lines'):
                objname = objname[:-6]
            elif objname.endswith('Lines'):
                objname = objname[:-5]
            objname = cc.utils.normalize_varname(objname.replace('.', ''))
            name = '%s%s' % (blendname, objname)
            filename = '%s.lines' % name
            filepath = os.path.join(datapath, filename)
            cc_export_lines.export_unity_lines(obj, filepath)
            print('Exported %s' % os.path.join(infopath, filename))

    if colormaps:
        import cc_export_colormap
        for obj in colormaps:
            objname = cc.utils.normalize_varname(obj.name.replace('.', ''))
            name = '%s%s' % (blendname, objname)
            filename = '%s.png' % name
            filepath = os.path.join(datapath, filename)
            cc_export_colormap.export_colormap(obj, filepath)
            colormap = cc.colors.Manager(obj).get_export_colormap()
            print('Exported %s' % os.path.join(infopath, filename))

    return lines, colormaps

class ExportData(bpy.types.Operator):
    bl_idname = 'cc.export'
    bl_label = 'Export Ancillary Data'
    bl_options = {'REGISTER'}

    def execute(self, context):
        lines, colormaps = export()
        if lines or colormaps:
            self.report({'INFO'}, "Exported %i lines, %i colormaps" % (len(lines), len(colormaps)))
        return {'FINISHED'}

@cc.ops.editmode
def set_export(objects, layer, aux, colormap):
    for obj in objects:
        if obj.type == 'MESH':
            m = cc.colors.Manager(obj)
            if layer:
                m.set_export_layer(layer)
            if aux:
                if aux == '__NONE__':
                    aux = None
                m.set_aux_layer(aux)
            if colormap:
                if colormap == '__NONE__':
                    colormap = None
                m.set_export_colormap(colormap)

def shared_colormap_items(scene, context):
    colormaps = cc.colors.find_shared_colormaps(context.selected_objects)
    enum = [('__NONE__', '', '')]
    for name in colormaps:
        enum.append((name, name, name))
    return enum

def shared_layer_items(scene, context):
    layers = cc.colors.find_shared_layers(context.selected_objects)
    enum = [('__NONE__', '', '')]
    for name in layers:
        enum.append((name, name, name))
    return enum

class SetExport(bpy.types.Operator):
    bl_idname = 'cc.set_export'
    bl_label = 'Set Export'
    bl_options = {'REGISTER', 'UNDO'}

    layer = bpy.props.EnumProperty(
        items=shared_layer_items, name='Main Color Layer')

    aux = bpy.props.EnumProperty(
        items=shared_layer_items, name='Aux Color Layer')

    colormap = bpy.props.EnumProperty(
        items=shared_colormap_items, name='Color Map')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def invoke(self, context, event):
        shared_layers = cc.colors.find_shared_layers(
            context.selected_objects)
        default_layer = cc.colors.find_default_layer(
            context.selected_objects, for_export=True)
        default_aux = cc.colors.find_default_layer(
            context.selected_objects, for_aux=True)

        shared_colormaps = cc.colors.find_shared_colormaps(
            context.selected_objects)
        default_colormap = cc.colors.find_default_colormap(
            context.selected_objects, for_export=True)

        if default_layer and default_layer in shared_layers:
            self.layer = default_layer
        if default_aux and default_aux in shared_layers:
            self.aux = default_aux
        if default_colormap and default_colormap in shared_colormaps:
            self.colormap = default_colormap

        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        set_export(context.selected_objects, self.layer, self.aux, self.colormap)
        return {'FINISHED'}

class ExportMenu(bpy.types.Menu):
    bl_label = 'Export'
    bl_idname = 'CC_MT_export'

    def draw(self, context):
        layout = self.layout
        layout.operator_context = 'INVOKE_DEFAULT'
        layout.operator(ExportData.bl_idname, text='Export Ancillary Data')
        layout.operator(SetExport.bl_idname, text='Export Options')
        layout.prop(get_export_scene(), 'autoexport')

def cardboard_menu_ext(self, context):
    self.layout.menu('CC_MT_export')

@bpy.app.handlers.persistent
def setup_autoexport(scene):
    scene = get_export_scene()
    if scene and scene.autoexport and export not in bpy.app.handlers.save_pre:
        bpy.app.handlers.save_pre.append(export)

def register():
    cc.utils.register(__REGISTER__)
    cc.ui.CardboardMenu.add_section(cardboard_menu_ext, 1000)
    bpy.app.handlers.load_post.append(setup_autoexport)

def unregister():
    cc.utils.unregister(__REGISTER__)
    cc.ui.CardboardMenu.remove_section(cardboard_menu_ext)
    bpy.app.handlers.load_post.remove(setup_autoexport)

__REGISTER__ = (
    ExportMenu,
    ExportData,
    SetExport,
    (bpy.types.Scene, 'autoexport', PROP_AUTOEXPORT),
)
