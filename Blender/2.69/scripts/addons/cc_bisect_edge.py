import bpy
import bmesh
import mathutils as mu
from bpy_extras import view3d_utils as v3du

bl_info = {
    'name': 'Bisect Edge',
    'author': 'Cardboard Computer',
    'blender': (2, 6, 9),
    'description': 'Bisect closest edge to cursor',
    'category': 'Cardboard'
}

def distance_to_edge(v, w, p):
    d = w - v;
    l2 = d.length_squared
    pv = p - v
    if l2 == 0:
        return pv.length
    t = max(0, min(1, pv.dot(d) / l2))
    d = v + t * d
    return (p - d).length

class BisectEdge(bpy.types.Operator):
    bl_idname = 'cc.bisect_edge'
    bl_label = 'Bisect Edge'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        obj = context.active_object
        mesh = bmesh.from_edit_mesh(obj.data)

        region = bpy.context.region
        region_3d = bpy.context.space_data.region_3d
        mouse_x, mouse_y = event.mouse_region_x, event.mouse_region_y
        mouse = mu.Vector((mouse_x, mouse_y))

        bpy.ops.mesh.select_all(action='DESELECT')

        mesh_select_mode = list(context.tool_settings.mesh_select_mode)
        context.tool_settings.mesh_select_mode = (False, True, False)
        bpy.ops.view3d.select_circle(x=mouse_x, y=mouse_y, radius=32, gesture_mode=3)
        edges = [edge for edge in mesh.edges if edge.select]
        context.tool_settings.mesh_select_mode = mesh_select_mode

        bpy.ops.mesh.select_all(action='DESELECT')

        if not edges:
            return {'CANCELLED'}

        mesh_select_mode[0] = True
        context.tool_settings.mesh_select_mode = mesh_select_mode

        distances = []
        m = obj.matrix_world

        for edge in edges:
            v = v3du.location_3d_to_region_2d(region, region_3d, edge.verts[0].co * m)
            w = v3du.location_3d_to_region_2d(region, region_3d, edge.verts[1].co * m)
            d = distance_to_edge(v, w, mouse)
            distances.append((edge, d, v, w))

        distances.sort(key=lambda k: k[1])
        edge, d, v, w = distances[0]

        edge_vec = (w - v).normalized()
        mouse_vec = (mouse - v) / (w - v).length
        factor = max(0, min(1, edge_vec.dot(mouse_vec)))

        edge, vert = bmesh.utils.edge_split(edge, edge.verts[0], factor)

        vert.select_set(True)

        bmesh.update_edit_mesh(obj.data)

        return {'FINISHED'}

bpy.utils.register_class(BisectEdge)

def register():
    pass
