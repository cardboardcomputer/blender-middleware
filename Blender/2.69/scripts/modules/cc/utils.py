import bpy
import bmesh
import math
import random
import mathutils
from bpy_extras import view3d_utils

def sign(v):
    if v < 0:
        return -1
    else:
        return 1

def roundq(v, q):
    return round(v / q) * q

def ceilq(v, q):
    return math.ceil(v / q) * q

def floorq(v, q):
    return math.floor(v / q) * q

def clamp(v, a, b):
    return min(max(v, a), b)

def lerp(a, b, v):
    return a * (1. - v) + b * v

def cubic(a, b, c, d, v):
    v_ = v * v
    a_ = d - c - a + b
    b_ = a - b - a_
    c_ = c - a
    d_ = b

    return a_ * v * v_ + b_ * v_ + c_ * v + d_

def cosine(a, b, v):
    v = (1. - math.cos(v * math.pi)) / 2.
    return a * (1. - v) + b * v

def smooth(v):
    return math.cos(v * math.pi + math.pi) / 2 + 0.5

def magnitude(v):
    return math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)

def nearest_pow_2(v):
    return 1 << (v - 1).bit_length()

def traverse(objects, children=False):
    def expand(obj):
        collected = []

        if children:
            for o in obj.children:
                collected += expand(o)

        if obj.dupli_group:
            for o in obj.dupli_group.objects:
                collected += expand(o)
        else:
            collected += [obj]

        return collected

    for obj in objects:
        for o in expand(obj):
            yield o

def normalize_varname(t, lower=False):
    tokens = []
    if not t:
        return ''
    if t[0].isdigit():
        t = '_%s' % t
    for c in t:
        if c.isalnum():
            if lower:
                c = c.lower()
            tokens.append(c)
        elif tokens[-1:] != '_':
            tokens.append('_')
    return ''.join(tokens)

def find(context, event, ray_max=1000.0):
    scene = context.scene
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y

    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

    # https://developer.blender.org/rB61baf6e8135d11bc53cbfa45c75f910a99e57971
    if rv3d.view_perspective == 'ORTHO':
        view_vector = -view_vector
        ray_origin = ray_origin - (view_vector * (ray_max / 2.0))
    else:
        view_vector = view_vector.normalized()

    ray_target = ray_origin + (view_vector * ray_max)

    def visible_objects_and_duplis():
        """Loop over (object, matrix) pairs (mesh only)"""

        for obj in context.visible_objects:
            if obj.draw_type != 'TEXTURED':
                continue

            if obj.type == 'MESH':
                yield (obj, obj.matrix_world.copy())

            if obj.dupli_type != 'NONE':
                obj.dupli_list_create(scene)
                for dob in obj.dupli_list:
                    obj_dupli = dob.object
                    if obj_dupli.type == 'MESH':
                        yield (obj_dupli, dob.matrix.copy())

            obj.dupli_list_clear()

    # cast rays and find the closest object
    best_length_squared = ray_max * ray_max
    best_obj = best_point = best_normal = best_face = None
    best_ray_origin = best_ray_target = None

    for obj, matrix in visible_objects_and_duplis():
        if obj.type == 'MESH' and len(obj.data.polygons):
            matrix_inv = obj.matrix_world.inverted()
            ray_origin_obj = matrix_inv * ray_origin
            ray_target_obj = matrix_inv * ray_target
            hit, normal, face_index = obj.ray_cast(ray_origin_obj, ray_target_obj)
            if face_index != -1:
                length_squared = (hit - ray_origin).length_squared
                if length_squared < best_length_squared:
                    best_length_squared = length_squared
                    best_obj = obj
                    best_point = hit
                    best_normal = normal
                    best_face = face_index
                    best_ray_origin = ray_origin_obj
                    best_ray_target = ray_target_obj

    if best_obj is not None:
        return best_obj, best_ray_origin, best_ray_target

class Swap:
    def __init__(self, obj, prop, val):
        self.obj = obj
        self.prop = prop
        self.val = val

    def __enter__(self):
        self.orig = getattr(self.obj, self.prop)
        setattr(self.obj, self.prop, self.val)
        return self

    def __exit__(self, type_, value, tb):
        setattr(self.obj, self.prop, self.orig)

swap = Swap

class ModifiedMesh:
    def __init__(
        self, obj, scene=None,
        triangulate=False,
        apply_modifiers=True,
        settings='PREVIEW'):

        self.obj = obj
        self.scene = scene
        self.triangulate = triangulate
        self.apply_modifiers = apply_modifiers
        self.settings = settings
        self.orig_mesh = self.mod_mesh = None
        self.modifier_settings = []

    def __enter__(self):
        return self.install()

    def __exit__(self, type_, value, tb):
        self.uninstall()

    def install(self):
        obj = self.obj
        scene = self.scene or bpy.context.scene

        self.orig_mesh = obj.data
        self.mod_mesh = obj.data = obj.to_mesh(
            scene=scene, apply_modifiers=self.apply_modifiers,
            settings=self.settings)

        if self.apply_modifiers:
            settings = self.modifier_settings
            for m in obj.modifiers:
                settings.append(m.show_viewport)
                m.show_viewport = False

        if self.triangulate:
            bm = bmesh.new()
            bm.from_mesh(self.mod_mesh)
            bmesh.ops.triangulate(bm, faces=bm.faces, use_beauty=True)
            bm.to_mesh(self.mod_mesh)
            bm.free()

        scene.update()

        return obj.data

    def uninstall(self):
        obj = self.obj
        obj.data = self.orig_mesh
        scene = self.scene or bpy.context.scene
        scene.update()

        if self.apply_modifiers:
            settings = self.modifier_settings
            for i, m in enumerate(obj.modifiers):
                m.show_viewport = settings[i]

modified_mesh = ModifiedMesh

class Noise:
    def __init__(self, size):
        self.size = size
        self.samples = []
        for i in range(size):
            self.samples.append(random.random())

    def sample(self, x):
        return self.samples[x % self.size]

    def linear(self, x):
        size = self.size
        x0 = int(x * size)
        x1 = x0 + 1
        s0 = self.samples[x0 % size]
        s1 = self.samples[x1 % size]
        return lerp(s0, s1, x * size - x0)

    def cosine(self, x):
        size = self.size
        x0 = int(x * size)
        x1 = x0 + 1
        s0 = self.samples[x0 % size]
        s1 = self.samples[x1 % size]
        return cosine(s0, s1, x * size - x0)

    def cubic(self, x):
        size = self.size
        x1 = int(x * size)
        x0 = x1 - 1
        x2 = x1 + 1
        x3 = x2 + 1
        s0 = self.samples[x0 % size]
        s1 = self.samples[x1 % size]
        s2 = self.samples[x2 % size]
        s3 = self.samples[x3 % size]
        return cubic(s0, s1, s2, s3, x * size - x1)

def register(objects):
    for obj in objects:
        if hasattr(obj, 'count'):
            cls, prop, value = obj
            setattr(cls, prop, value)
        else:
            bpy.utils.register_class(obj)

def unregister(objects):
    for obj in objects:
        if hasattr(obj, 'count'):
            cls, prop, value = obj
            if hasattr(cls, prop):
                delattr(cls, prop)
        else:
            bpy.utils.unregister_class(obj)

class Bmesh:
    def __init__(self, obj, context=None):
        if not context:
            context = bpy.context
        self.context = context
        self.obj = obj

    def __enter__(self):
        if self.context.mode == 'EDIT_MESH':
            self.bm = bmesh.from_edit_mesh(self.obj.data)
        else:
            self.bm = bmesh.new()
            self.bm.from_mesh(self.obj.data)
        return self.bm

    def __exit__(self, cls, value, tb):
        if self.context.mode == 'EDIT_MESH':
            bmesh.update_edit_mesh(self.obj.data)
        else:
            self.bm.to_mesh(self.obj.data)
        self.bm.free()
