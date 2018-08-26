import bpy
import cc

def upgrade():
    for obj in bpy.data.objects:
        upgrade_obj(obj)

def upgrade_obj(obj):
    if obj.type == 'MESH':
        upgrade_mesh_colors(obj)
        upgrade_line_attributes(obj)

def upgrade_mesh_colors(obj):
    if len(obj.data.vertex_colors):
        main = obj.data.vertex_colors[0]
        main.active_render = True
        alpha_name = '%s.Alpha' % main.name
        for layer in obj.data.vertex_colors:
            if layer.name in ('_Alpha', 'Alpha'):
                layer.name = alpha_name

def upgrade_line_attributes(obj):
    for v in obj.vertex_groups:
        tokens = v.name.split('_')
        if len(tokens) == 2:
            if (tokens[0] in ('red', 'green', 'blue', 'alpha') and
                tokens[1].isdigit()):
                i = int(tokens[1])
                if i == 0:
                    layer = cc.colors.BASENAME
                else:
                    layer = '%s.%03d' % (cc.colors.BASENAME, i)
                v.name = '%s.%s' % (layer, tokens[0][:1].upper())
            if tokens[0] == 'normal' and tokens[1] in ('x', 'y', 'z'):
                v.name = '%s.%s' % (tokens[0].capitalize(), tokens[1].upper())
