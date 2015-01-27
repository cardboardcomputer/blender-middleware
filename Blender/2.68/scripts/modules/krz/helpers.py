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
