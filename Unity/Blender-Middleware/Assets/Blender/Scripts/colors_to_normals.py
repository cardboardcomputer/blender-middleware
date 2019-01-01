import bpy
import cc

obj = bpy.context.active_object
colors = cc.colors.layer(obj)
normals = cc.lines.normals(obj)

for sample in colors.itersamples():
    normals.set(
        sample.vertex.index, 
        -(sample.color.r * 2 - 1),
        sample.color.g * 2 - 1,
        sample.color.b * 2 - 1)
