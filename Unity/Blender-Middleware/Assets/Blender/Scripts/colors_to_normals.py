import bpy
import krz

obj = bpy.context.active_object
colors = krz.colors.layer(obj)
normals = krz.lines.normals(obj)

for sample in colors.itersamples():
    normals.set(
        sample.vertex.index, 
        -(sample.color.r * 2 - 1),
        sample.color.g * 2 - 1,
        sample.color.b * 2 - 1)
