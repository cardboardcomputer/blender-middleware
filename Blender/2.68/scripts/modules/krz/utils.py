import bpy
import bmesh
import math

def clamp(v, a, b):
    return min(max(v, a), b)

def lerp(a, b, v):
    return a * (1. - v) + b * v

def magnitude(v):
    return math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)

def nearest_pow_2(v):
    return 1 << (v - 1).bit_length()

def traverse(objects):
    def expand(obj):
        if obj.dupli_group:
            children = []
            for o in obj.dupli_group.objects:
                children += expand(o)
            return children
        else:
            return [obj]
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
