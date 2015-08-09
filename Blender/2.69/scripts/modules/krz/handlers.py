import bpy
import krz

@bpy.app.handlers.persistent
def update_aux_colors(scene):
    for obj in bpy.context.selected_objects:
        if (obj.type == 'MESH' and
            obj.is_updated_data):
            manager = krz.colors.Manager(obj)
            layer = manager.get_aux_layer()
            if layer and layer.name in obj.data.uv_textures:
                krz.colors.bake_to_uvmap(obj, layer.name, layer.name)

if update_aux_colors not in bpy.app.handlers.scene_update_post:
    bpy.app.handlers.scene_update_post.append(update_aux_colors)
