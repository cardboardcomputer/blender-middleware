import bpy
import bmesh
import mathutils as mu
from krz.utils import lerp

bl_info = {
    'name': 'Make Edge/Face',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 9),
    'location': 'View3D > Mesh > Make Edge/Face ',
    'description': 'Improved Make Edge/Face operator',
    'category': 'Cardboard'
}

class EdgeFaceAdd(bpy.types.Operator):
    bl_idname = 'cc.edge_face_add'
    bl_label = 'Make Edge/Face'
    bl_options = {'REGISTER', 'UNDO'}

    @classmethod
    def poll(cls, context):
        return context.mode == 'EDIT_MESH'

    def execute(self, context):
        changed = False

        obj = bpy.context.active_object
        bm = bmesh.from_edit_mesh(obj.data)

        selected_verts = [vert for vert in bm.verts if vert.select]

        # when only two vertices on a common face are selected, split
        # the face instead of just creating a new loose edge between
        # them (default behavior)

        if len(selected_verts) == 2:
            vert_a, vert_b = selected_verts
            vert_a_faces = set(vert_a.link_faces)
            vert_b_faces = set(vert_b.link_faces)
            common_faces = list(vert_a_faces.intersection(vert_b_faces))
            if common_faces:
                face, loop = bmesh.utils.face_split(common_faces[0], vert_a, vert_b)
                vert_a_edges = set(vert_a.link_edges)
                vert_b_edges = set(vert_b.link_edges)
                common_edges = list(vert_a_edges.intersection(vert_b_edges))
                if common_edges:
                    common_edges[0].select_set(True)
                    changed = True

        if not changed:
            created = {}
            mesh_select_mode = list(context.tool_settings.mesh_select_mode)

            if mesh_select_mode.count(True) == 1:
                if mesh_select_mode[0] == True:
                    created = bmesh.ops.contextual_create(bm, geom=selected_verts)
                elif mesh_select_mode[1] == True:
                    created = bmesh.ops.contextual_create(bm, geom=(e for e in bm.edges if e.select))
                elif mesh_select_mode[2] == True:
                    created = bmesh.ops.contextual_create(bm, geom=(f for f in bm.edges if f.select))
            elif mesh_select_mode[1] == True:
                created = bmesh.ops.contextual_create(bm, geom=(e for e in bm.edges if e.select))
            else:
                created = bmesh.ops.contextual_create(bm, geom=selected_verts)

            if created and (created['edges'] or created['faces']):
                changed = True

                # if there are vertex colors present, extend
                # surrounding/nearby colors onto the newly created
                # face

                if len(bm.loops.layers.color):
                    for face in created['faces']:
                        start = None
                        updated = {}

                        for loop in face.loops:
                            link_loops = list(loop.vert.link_loops)
                            link_loops.remove(loop)

                            if link_loops:
                                colors = {}
                                for layer in bm.loops.layers.color.items():
                                    base = mu.Color((0, 0, 0))
                                    corners = 0
                                    for l in link_loops:
                                        color = l[layer]
                                        base.r += color.r
                                        base.g += color.g
                                        base.b += color.b
                                        corners += 1
                                    base.r /= corners
                                    base.g /= corners
                                    base.b /= corners
                                    loop[layer] = base
                                    colors[layer.name] = base
                                updated[loop] = colors
                                start = loop

                        if start:
                            boundaries = []
                            chain = []
                            loop = start.link_loop_next
                            distance = start.edge.calc_length()
                            colors_a = colors_b = updated[start]

                            while True:
                                length = loop.edge.calc_length()
                                if loop in updated:
                                    colors_b = updated[loop]
                                    if chain:
                                        boundaries.append((chain, colors_a, colors_b, distance + length))
                                    if loop == start:
                                        break
                                    chain = []
                                    colors_a = colors_b
                                    distance = length
                                else:
                                    chain.append((loop, distance))
                                    distance += length
                                loop = loop.link_loop_next

                            for chain, colors_a, colors_b, length_total in boundaries:
                                for loop, length in chain:
                                    blend = length / length_total
                                    for layer in bm.loops.layers.color.items():
                                        loop[layer] = lerp(colors_a[layer.name], colors_b[layer.name], blend)

        bmesh.update_edit_mesh(obj.data)

        if changed:
            return {'FINISHED'}
        else:
            return {'CANCELLED'}

bpy.utils.register_class(EdgeFaceAdd)

def register():
    pass