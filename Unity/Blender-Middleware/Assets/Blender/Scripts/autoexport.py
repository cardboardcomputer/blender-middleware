import os
import bpy
import cc
import cc_export_lines
import cc_export_colormap

def autoexport(scene):
    if 'Export' in bpy.data.scenes:
        scene = bpy.data.scenes['Export']
    if '_Export' in bpy.data.scenes:
        scene = bpy.data.scenes['_Export']

    for obj in scene.objects:
        if cc.lines.is_line(obj):
            export_line(obj)
        if obj.type == 'MESH':
            colormap = cc.colors.Manager(obj).get_export_colormap()
            if colormap:
                export_colormap(obj)

def export_line(obj):
    dirname = os.path.dirname(bpy.data.filepath)
    linespath = os.path.join(dirname, os.pardir, 'Lines')
    if not os.path.exists(linespath):
        os.mkdir(linespath)
    blendname = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    objname = obj.name
    if objname.endswith('.Lines'):
        objname = objname[:-6]
    elif objname.endswith('Lines'):
        objname = objname[:-5]
    objname = cc.utils.normalize_varname(objname.replace('.', ''))
    name = '%s%s' % (blendname, objname)
    filename = '%s.lines' % name
    filepath = os.path.join(linespath, filename)

    cc_export_lines.export_unity_lines(obj, filepath)

    print('Exported %s' % filepath)

def export_colormap(obj):
    dirname = os.path.dirname(bpy.data.filepath)
    texpath = os.path.join(dirname, os.pardir, 'Textures')
    if not os.path.exists(texpath):
        os.mkdir(texpath)
    blendname = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
    objname = cc.utils.normalize_varname(obj.name.replace('.', ''))
    name = '%s%s' % (blendname, objname)
    filename = '%s.png' % name
    filepath = os.path.join(texpath, filename)

    cc_export_colormap.export_colormap(obj, filepath)
    colormap = cc.colors.Manager(obj).get_export_colormap()

    print('Exported %s, stride: %s' % (filepath, colormap.get_stride()))

bpy.app.handlers.save_pre.append(autoexport)
