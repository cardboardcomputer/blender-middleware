import bpy
import math

def clamp(v, a, b):
    return min(max(v, a), b)

def lerp(a, b, v):
    return a * (1. - v) + b * v

def magnitude(v):
    return math.sqrt(v.x ** 2 + v.y ** 2 + v.z ** 2)

def nearest_pow_2(v):
    return 1 << (v - 1).bit_length()

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
    def __init__(self, obj, scene=None, apply_modifiers=True, settings='PREVIEW'):
        self.obj = obj
        self.scene = scene
        self.apply_modifiers = apply_modifiers
        self.settings = settings

    def __enter__(self):
        obj = self.obj
        scene = self.scene or bpy.context.scene

        self.orig_mesh = obj.data
        self.mod_mesh = obj.data = obj.to_mesh(
            scene=scene, apply_modifiers=self.apply_modifiers,
            settings=self.settings)
        scene.update()

        return obj.data

    def __exit__(self, type_, value, tb):
        self.obj.data = self.orig_mesh
        scene = self.scene or bpy.context.scene
        scene.update()

modified_mesh = ModifiedMesh
