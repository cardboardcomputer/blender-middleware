import cc
import bpy
import bmesh
import mathutils as mu
from bpy_extras import view3d_utils as v3du
from cc.utils import lerp

bl_info = {
    'name': 'Utils: Mesh',
    'author': 'Cardboard Computer',
    'blender': (2, 69, 0),
    'description': 'Various mesh-editing utilities',
    'category': 'Cardboard'
}

def lerp(a, b, v):
    return a * (1. - v) + b * v

def magnitude(v):
    return math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)

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

PART_A = '_Boolean.A'
PART_B = '_Boolean.B'

@cc.ops.editmode
def mesh_boolean(ctx, obj, mode='DIFFERENCE'):
    # remember state
    active = ctx.active_object
    selected = ctx.selected_objects

    # clean up existing temp objects, reset state
    for name in (PART_A, PART_B):
        if name in ctx.scene.objects:
            ctx.scene.objects.unlink(ctx.scene.objects[name])
        if name in bpy.data.objects:
            bpy.data.objects.remove(bpy.data.objects[name])
        if name in bpy.data.meshes:
            bpy.data.meshes.remove(bpy.data.meshes[name])

    # create new temp objects
    mesh_a = obj.data.copy()
    mesh_a.name = PART_A
    obj_a = bpy.data.objects.new(PART_A, mesh_a)
    ctx.scene.objects.link(obj_a)
    ctx.scene.update()

    # clear selection
    bpy.ops.object.select_all(action='DESELECT')

    # select part a
    obj_a.select = True
    ctx.scene.objects.active = obj_a
    ctx.scene.update();

    # separate selection into part b
    bpy.ops.object.editmode_toggle()
    bpy.ops.mesh.separate(type='SELECTED')
    obj_b = ctx.scene.objects['%s.001' % PART_A]
    obj_b.name = PART_B
    mesh_b = obj_b.data
    mesh_b.name = PART_B
    bpy.ops.object.editmode_toggle()

    # add and apply boolean modifier
    mod = obj_a.modifiers.new(name='Boolean', type='BOOLEAN')
    mod.operation = mode
    mod.object = obj_b
    bpy.ops.object.modifier_apply(apply_as='DATA', modifier="Boolean")

    # revert selection
    bpy.ops.object.select_all(action='DESELECT')

    for obj in selected:
        obj.select = True
    ctx.scene.objects.active = active

    # update in place
    mesh = bmesh.new()
    mesh.from_mesh(mesh_a)
    mesh.to_mesh(obj.data)

    # remove temp objects
    ctx.scene.objects.unlink(obj_b)
    bpy.data.objects.remove(obj_b)
    bpy.data.meshes.remove(mesh_b)
    ctx.scene.objects.unlink(obj_a)
    bpy.data.objects.remove(obj_a)
    bpy.data.meshes.remove(mesh_a)

class MeshBoolean(bpy.types.Operator):
    bl_idname = 'cc.mesh_boolean'
    bl_label = 'Mesh Boolean'
    bl_options = {'REGISTER', 'UNDO'}

    mode = bpy.props.EnumProperty(
        items=(('DIFFERENCE', 'Difference', 'Difference'),
               ('UNION', 'Union', 'Union'),
               ('INTERSECT', 'Intersect', 'Intersect')),
        name='Operation', default='DIFFERENCE')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH')

    def execute(self, context):
        mesh_boolean(context, context.active_object, self.mode)
        return {'FINISHED'}

    def invoke(self, context, event):
        self.execute(context)
        return {'FINISHED'}

@cc.ops.editmode
def select_by_normal_ref(obj, ref, threshold):
    p1 = ref.location
    p2 = ref.matrix_world * m.Vector((0, 0, 1))
    direction = (p2 - p1).normalized()

    for poly in obj.data.polygons:
        f = direction.dot(poly.normal)
        if f >= threshold:
            poly.select = True

@cc.ops.editmode
def select_by_normal_dir(obj, direction, threshold):
    for poly in obj.data.polygons:
        f = direction.dot(poly.normal)
        if f >= threshold:
            poly.select = True

class SelectByNormal(bpy.types.Operator):
    bl_idname = 'cc.select_by_normal'
    bl_label = 'Select By Normal'
    bl_options = {'REGISTER', 'UNDO'}

    threshold = bpy.props.FloatProperty(name="Threshold", min=-1, max=1, step=0.1, default=0)

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return (obj and obj.type == 'MESH'
                and not cc.lines.is_line(obj))

    def execute(self, context):
        if len(context.selected_objects) == 2:
            aux_objects = list(context.selected_objects)
            aux_objects.remove(context.active_object)
            select_by_normal_ref(
                context.active_object,
                aux_objects[0],
                self.threshold)
        else:
            region_3d = bpy.context.space_data.region_3d
            direction = region_3d.view_rotation * m.Vector((0, 0, 1))
            select_by_normal_dir(context.active_object, direction, self.threshold)
        return {'FINISHED'}

def register():
    cc.utils.register(__REGISTER__)

def unregister():
    cc.utils.unregister(__REGISTER__)

__REGISTER__ = (
    BisectEdge,
    EdgeFaceAdd,
    MeshBoolean,
    SelectByNormal,
)
