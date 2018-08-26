import bpy
import cc
import math
import bmesh
import struct
import mathutils

class ColorError(Exception): pass

BASENAME = 'Col'
METADATA_PROP = 'ColorMeta'
COLORMAP_MINSIZE = 16

def colormeta(obj):
    data = obj.data
    meta = data.get(METADATA_PROP)
    if meta is None:
        data[METADATA_PROP] = [{}]
        meta = data[METADATA_PROP]
    return meta[0]

def foreach(obj, *layers):
    return Manager(obj).foreach(*layers)

def new(obj, base=None, **kw):
    m = Manager(obj, base=base)
    name = m.get_unique_name()
    return m.add_layer(name, **kw)

def layer(obj, name=None, base=None, **kw):
    if not name:
        return Manager(obj, base=base).get_active_layer()
    else:
        return Manager(obj, base=base).get_or_add_layer(name, **kw)

def colormap(obj, name=None, base=None, **kw):
    if not name:
        return Manager(obj, base=base).get_active_colormap()
    else:
        return Manager(obj, base=base).get_or_add_colormap(name, **kw)

def color_to_hex(rgb):
    return '%02x%02x%02x' % (rgb[0] * 255, rgb[1] * 255, rgb[2] * 255)

def hex_to_color(val):
    try:
        val = str(val).lower()
    except ValueError:
        return mathutils.Color((1, 0, 1))

    if val == '0':
        val = '000000'
    if len(val) == 3:
        val = val[2] + val[2] + val[1] + val[1] + val[0] + val[0]

    try:
        t = struct.unpack('BBB', bytes.fromhex(val))
    except ValueError:
        return mathutils.Color((1, 0, 1))
    else:
        return mathutils.Color((t[0] / 255.0, t[1] / 255.0, t[2] / 255.0))

def rgba_to_uv(rgba, precision=4096):
    p = precision - 1
    r, g, b, a = rgba

    r = math.floor(r * p)
    g = math.floor(g * p)
    b = math.floor(b * p)
    a = math.floor(a * p)

    u = (r * precision) + g
    v = (b * precision) + a

    return u, v

def uv_to_rgba(uv, precision=4096):
    p = precision - 1
    u, v = uv

    r = math.floor(u / precision) / p
    g = (u % precision) / p
    b = math.floor(v / precision) / p
    a = (v % precision) / p

    return r, g, b, a

def bake_to_uvmap(obj, layer, uvmap):
    layer = Manager(obj).get_layer(layer)
    uvmap = obj.data.uv_layers[obj.data.uv_textures.keys().index(uvmap)]

    for i, s in enumerate(layer.itersamples()):
        uv = rgba_to_uv((s.color.r, s.color.g, s.color.b, s.alpha))
        uvmap.data[i].uv = uv

def find_default_layer(objects, for_export=False, for_aux=False):
    freq = {}

    for obj in objects:
        if obj.type == 'MESH':
            if for_aux:
                layer = Manager(obj).get_aux_layer()
            else:
                if for_export:
                    layer = Manager(obj).get_export_layer()
                else:
                    layer = Manager(obj).get_active_layer(False)
            if not layer:
                continue
            if layer.name not in freq:
                freq[layer.name] = 0
            freq[layer.name] += 1

    freq_items = list(freq.items())
    freq_items.sort(key=lambda c: -c[1])

    if freq_items:
        return freq_items[0][0]
    else:
        return None

def find_shared_layers(objects):
    setlist = []

    for obj in objects:
        if obj.type == 'MESH':
            layers = Manager(obj).list_layers()
            setlist.append(set(layers))
    if not setlist:
        return []

    common = set.intersection(*setlist)
    layers = list(common)
    layers.sort()

    return layers

def find_default_colormap(objects, for_export=False):
    freq = {}

    for obj in objects:
        if obj.type == 'MESH':
            if for_export:
                layer = Manager(obj).get_export_colormap()
            else:
                layer = Manager(obj).get_active_colormap(False)
            if not layer:
                continue
            if layer.name not in freq:
                freq[layer.name] = 0
            freq[layer.name] += 1

    freq_items = list(freq.items())
    freq_items.sort(key=lambda c: -c[1])

    if freq_items:
        return freq_items[0][0]
    else:
        return None

def find_shared_colormaps(objects):
    setlist = []

    for obj in objects:
        if obj.type == 'MESH':
            layers = Manager(obj).list_colormaps()
            setlist.append(set(layers))
    if not setlist:
        return []

    common = set.intersection(*setlist)
    layers = list(common)
    layers.sort()

    return layers

class Color(mathutils.Color):
    def __mul__(self, o):
        if hasattr(o, '__len__'):
            c = self.copy()
            c.r *= o[0]
            c.g *= o[1]
            c.b *= o[2]
            return c
        else:
            return super(Color, self).__mul__(o)

    def __div__(self, o):
        if hasattr(o, '__len__'):
            c = self.copy()
            c.r /= o[0]
            c.g /= o[1]
            c.b /= o[2]
            return c
        else:
            return super(Color, self).__div__(o)

    def __add__(self, o):
        if hasattr(o, '__len__'):
            return super(Color, self).__add__(o)
        else:
            return super(Color, self).__add__(Color(o, o, o))

    def __sub__(self, o):
        if hasattr(o, '__len__'):
            return super(Color, self).__sub__(o)
        else:
            return super(Color, self).__sub__(Color(o, o, o))

class Manager:
    def __init__(self, obj, base=None):
        self.obj = obj
        if obj.type != 'MESH':
            raise ColorError('object is not a mesh')
        if not base:
            base = BASENAME
        self.base = base
        self._meta = None

    @property
    def meta(self):
        if self._meta is None:
            self._meta = colormeta(self.obj)
        return self._meta

    def is_line(self):
        return (
            len(self.obj.data.polygons) == 0 and
            len(self.obj.data.edges) > 0)

    def get_unique_name(self, base=None, lookup=None):
        if lookup is None:
            lookup = self.list_layers()
        if not base:
            base = self.base
        if base not in lookup:
            return base
        i = 1
        while True:
            name = '%s.%03d' % (base, i)
            if name not in lookup:
                return name
            if i == 999:
                raise ColorError('wow this happened')
            i += 1

    def list_layers(self):
        if self.is_line():
            layers = []
            keys = self.obj.vertex_groups.keys()
            for key in keys:
                if key.endswith('.R'):
                    name = key[:-2]
                    if ('%s.G' % name in keys and
                        '%s.B' % name in keys and
                        '%s.A' % name in keys):
                        layers.append(name)
                        layers.append('%s.Alpha' % name)
            return layers
        else:
            return list(self.obj.data.vertex_colors.keys())

    def list_colormaps(self):
        return list(self.meta.get('colormaps', {}).keys())

    def exists(self, name):
        if self.is_line():
            n = name
            if n.endswith('.Alpha'):
                n = n[:-6]
            v = self.obj.vertex_groups

            return (
                ('%s.R' % n) in v and
                ('%s.G' % n) in v and
                ('%s.B' % n) in v and
                ('%s.A' % n) in v)
        else:
            return name in self.obj.data.vertex_colors

    def add_layer(self, name, **kw):
        if self.is_line():
            layer = LineColorLayer(self.obj, name)
            if METADATA_PROP not in self.obj.data:
                self.meta['export_line_color'] = layer.name
        else:
            layer = PolyColorLayer(self.obj, name)
        layer.create(**kw)
        return layer

    def get_layer(self, name):
        if self.is_line():
            layer = LineColorLayer(self.obj, name)
        else:
            layer = PolyColorLayer(self.obj, name)
        if layer.exists():
            return layer

    def get_or_add_layer(self, name=None, **kw):
        if not name:
            name = self.get_unique_name()
        layer = self.get_layer(name)
        if layer:
            return layer
        else:
            return self.add_layer(name, **kw)

    def remove_layer(self, name):
        layer = self.get_layer(name)
        if layer:
            layer.destroy()

    def get_active_layer(self, autoadd=True):
        layer = None
        if self.is_line():
            layer = self.get_active_layer_line()
        else:
            layer = self.get_active_layer_poly()
        if not layer and autoadd:
            layer = self.get_or_add_layer()
            layer.activate()
        return layer

    def get_active_layer_line(self):
        layer = None
        v = self.obj.vertex_groups
        meta = self.meta

        if v.active:
            n = v.active.name
            if (n.endswith('.R') or
                n.endswith('.G') or
                n.endswith('.B') or
                n.endswith('.A')):
                if n.endswith('.A'):
                    name = '%slpha' % n
                else:
                    name = n[:-2]
                layer = LineColorLayer(self.obj, name)
                if layer.exists():
                    meta['active_line_color'] = name
                else:
                    layer = None
            elif 'active_line_color' in meta:
                n = name = meta['active_line_color']
                if n.endswith('.Alpha'):
                    n = n[:-6]
                if '%s.R' % n in v:
                    layer = LineColorLayer(self.obj, name)

        if layer is None:
            layers = self.list_layers()
            if len(layers):
                layer = LineColorLayer(self.obj, layers[0])
                meta['active_line_color'] = layers[0]

        return layer

    def get_active_layer_poly(self):
        v = self.obj.data.vertex_colors
        if v.active:
            return PolyColorLayer(self.obj, v.active.name)

    def get_export_layer(self):
        if self.is_line():
            meta = self.meta
            if 'export_line_color' in meta:
                layer = LineColorLayer(self.obj, meta['export_line_color'])
                if layer.exists():
                    return layer
            layers = self.list_layers()
            if layers:
                name = layers[0]
                meta['export_line_color'] = name
                return LineColorLayer(self.obj, name)
        else:
            for layer in self.obj.data.vertex_colors:
                if layer.active_render:
                    return PolyColorLayer(self.obj, layer.name)

    def set_export_layer(self, name):
        if self.is_line():
            layer = LineColorLayer(self.obj, name)
            if layer.exists():
                self.meta['export_line_color'] = name
        else:
            if name in self.obj.data.vertex_colors:
                self.obj.data.vertex_colors[name].active_render = True

    def get_aux_layer(self):
        meta = self.meta
        if self.is_line():
            if 'aux_line_color' in meta:
                layer = LineColorLayer(self.obj, meta['aux_line_color'])
                if layer.exists():
                    return layer
        else:
            if 'aux_poly_color' in meta:
                layer = PolyColorLayer(self.obj, meta['aux_poly_color'])
                if layer.exists():
                    return layer

    def set_aux_layer(self, name):
        meta = self.meta
        if self.is_line():
            if name is None:
                if 'aux_line_color' in meta:
                    del meta['aux_line_color']
            else:
                layer = LineColorLayer(self.obj, name)
                if layer.exists():
                    meta['aux_line_color'] = name
        else:
            if name is None:
                if 'aux_line_color' in meta:
                    del meta['aux_poly_color']
            else:
                if name in self.obj.data.vertex_colors:
                    meta['aux_poly_color'] = name
                    if name not in self.obj.data.uv_textures:
                        uvtex = self.obj.data.uv_textures.new()
                        uvtex.name = name
                        index = self.obj.data.uv_textures.keys().index(name)
                        uvmap = self.obj.data.uv_layers[index]
                        uvmap.name = name
                        bake_to_uvmap(self.obj, name, name)

    def get_export_colormap(self):
        for uvmap in self.obj.data.uv_textures:
            if uvmap.active_render:
                if self.is_line():
                    colormap = LineColormap(self.obj, uvmap.name)
                else:
                    colormap = PolyColormap(self.obj, uvmap.name)
                if colormap.exists():
                    return colormap

    def set_export_colormap(self, name):
        if name is not None:
            colormap = self.get_colormap(name)
            if colormap:
                colormap.uvmap.active_render = True

    def add_colormap(self, name, **kw):
        if 'colormaps' not in self.meta:
            set_export = True
        else:
            set_export = False
        if self.is_line():
            colormap = LineColormap(self.obj, name)
        else:
            colormap = PolyColormap(self.obj, name)
        colormap.create(**kw)
        if set_export:
            colormap.uvmap.active_render = True
        return colormap

    def get_colormap(self, name):
        if self.is_line():
            colormap = LineColormap(self.obj, name)
        else:
            colormap = PolyColormap(self.obj, name)
        if colormap.exists():
            return colormap

    def get_or_add_colormap(self, name=None, **kw):
        if not name:
            name = self.get_unique_name(lookup=self.obj.data.uv_textures)
        colormap = self.get_colormap(name)
        if colormap:
            return colormap
        else:
            return self.add_colormap(name, **kw)

    def remove_colormap(self, name):
        colormap = self.get_colormap(name)
        if colormap:
            colormap.destroy()

    def get_active_colormap(self, autoadd=True):
        colormap = None
        v = self.obj.data.uv_textures
        if v.active:
            if self.is_line():
                colormap = LineColormap(self.obj, v.active.name)
            else:
                colormap = PolyColormap(self.obj, v.active.name)
        if not colormap and autoadd:
            colormap = self.get_or_add_colormap()
            colormap.activate()
        return colormap

    def foreach(self, *names):
        if not names:
            return
        generators = []
        for n in names:
            layer = self.get_layer(n)
            if not layer:
                raise ColorError('%s layer does not exist' % layer)
            generators.append(layer._generate_samples())
        while True:
            try:
                samples = [next(g) for g in generators]
            except StopIteration:
                break
            yield samples
            [s.save() for s in samples]

    def exec_color_ops(self, ops=None):
        if ops is None:
            ops = []
        names = []
        for key in self.obj.data.keys():
            if key.startswith('Color.'):
                names.append(key)
        names.sort()
        for name in names:
            ops.append(str(self.obj.data[name]))
        layers = self.list_layers()
        for op in ops:
            ColorOp(self.obj, op, layers).execute()

class LineColorLayer:
    def __init__(self, obj, name):
        self.alpha = False
        if name.endswith('.Alpha'):
            self.alpha = True
            name = name[:-6]

        self.obj = obj
        self._name = name
        self.data = obj.data
        self._samples = []

        if self.exists():
            self.r = obj.vertex_groups['%s.R' % name]
            self.g = obj.vertex_groups['%s.G' % name]
            self.b = obj.vertex_groups['%s.B' % name]
            self.a = obj.vertex_groups['%s.A' % name]

    @property
    def name(self):
        if self.alpha:
            return '%s.Alpha' % self._name
        else:
            return self._name

    def _generate_samples(self):
        obj = self.obj
        if not self.alpha:
            for vert in self.data.vertices:
                try:
                    color = Color((
                       self.r.weight(vert.index),
                       self.g.weight(vert.index),
                       self.b.weight(vert.index)))
                    alpha = self.a.weight(vert.index)
                except RuntimeError:
                    color = Color((1, 1, 1))
                    alpha = 1
                yield ColorLayerSample(obj, self, None, 0, vert, color, alpha)
        else:
            for vert in self.data.vertices:
                try:
                    alpha = self.a.weight(vert.index)
                except RuntimeError:
                    alpha = 1
                color = Color((alpha, alpha, alpha))
                yield ColorLayerSample(obj, self, None, 0, vert, color, 1)

    def _get_samples(self):
        self._samples = list(self._generate_samples())

    def _save_samples(self):
        kw = {'type': 'REPLACE'}
        if not self.alpha:
            for sample in self._samples:
                i = sample.vertex.index
                self.r.add([i], sample.color.r, **kw)
                self.g.add([i], sample.color.g, **kw)
                self.b.add([i], sample.color.b, **kw)
                self.a.add([i], sample.alpha, **kw)
        else:
            for sample in self._samples:
                i = sample.vertex.index
                self.a.add([i], sample.color.v, **kw)
        cc.ui.flag(self.data)

    def exists(self):
        n = self._name
        v = self.obj.vertex_groups

        return (
            ('%s.R' % n) in v and
            ('%s.G' % n) in v and
            ('%s.B' % n) in v and
            ('%s.A' % n) in v)

    def create(self, **kw):
        if self.exists():
            return

        n = self._name
        v = self.obj.vertex_groups

        active = v.active_index

        r_name = '%s.R' % n
        g_name = '%s.G' % n
        b_name = '%s.B' % n
        a_name = '%s.A' % n

        if r_name in v:
            v.remove(v[r_name])
        if g_name in v:
            v.remove(v[g_name])
        if b_name in v:
            v.remove(v[b_name])
        if a_name in v:
            v.remove(v[a_name])

        self.r = r = v.new()
        self.g = g = v.new()
        self.b = b = v.new()
        self.a = a = v.new()

        r.name = r_name
        g.name = g_name
        b.name = b_name
        a.name = a_name

        kw = {'type': 'ADD'}
        vindices = [v.index for v in self.data.vertices]
        for s in (r, g, b, a):
            s.add(vindices, 1, **kw)

        v.active_index = active

    def destroy(self):
        n = self._name
        v = self.obj.vertex_groups

        if self.exists():
            v.remove(v[('%s.R' % n)])
            v.remove(v[('%s.G' % n)])
            v.remove(v[('%s.B' % n)])
            v.remove(v[('%s.A' % n)])
            self._samples = []
            self.r = self.g = self.b = self.a = None

    def activate(self):
        obj = self.obj
        if self.alpha:
            name = '%s.Alpha' % self._name
            obj.vertex_groups.active_index = self.a.index
        else:
            name = self._name
            obj.vertex_groups.active_index = self.r.index
        colormeta(obj)['active_line_color'] = name
        cc.ui.flag(obj.data)

    def itersamples(self):
        if not self._samples:
            self._get_samples()
        for sample in self._samples:
            yield sample
        self._save_samples()

    @property
    def samples(self):
        if not self._samples:
            self._get_samples()
        return self._samples

class PolyColorLayer:
    def __init__(self, obj, name):
        self.obj = obj
        self.name = name
        self.data = obj.data
        self._samples = []

        if self.exists():
            self.colors = obj.data.vertex_colors[name]
            alpha = '%s.Alpha' % name
            self.alpha = obj.data.vertex_colors.get(alpha)

    def _generate_samples(self):
        obj = self.obj
        data = self.data
        colors = self.colors.data
        if self.alpha:
            alpha = self.alpha.data
        else:
            alpha = None

        if not len(colors):
            return

        for poly in data.polygons:
            for idx, ptr in enumerate(poly.loop_indices):
                vert = data.vertices[poly.vertices[idx]]
                color = Color(colors[ptr].color)
                if alpha:
                    alpha_ = alpha[ptr].color.v
                else:
                    alpha_ = 1
                yield ColorLayerSample(
                    obj, self, poly, ptr, vert, color.copy(), alpha_)

    def _get_samples(self):
        self._samples = list(self._generate_samples())

    def _save_samples(self):
        colors = self.colors.data
        if self.alpha:
            alpha = self.alpha.data
        else:
            alpha = None

        for sample in self._samples:
            colors[sample.poly_index].color = mathutils.Color(sample.color)
            if alpha:
                a = sample.alpha
                alpha[sample.poly_index].color = mathutils.Color((a, a, a))

    def exists(self):
        return self.name in self.data.vertex_colors

    def create(self, **kw):
        if self.exists():
            return

        data = self.data.vertex_colors
        create_alpha = kw.get('alpha')

        active_index = data.active_index

        colors = data.new()
        colors.name = self.name
        if create_alpha:
            alpha_name = '%s.Alpha' % self.name
            alpha = data.new()
            alpha.name = alpha_name

        if active_index > -1:
            data.active_index = active_index

        self.colors = data[self.name]
        if create_alpha:
            self.alpha = data[alpha_name]
        else:
            self.alpha = None

    def destroy(self):
        v = self.data.vertex_colors
        if self.exists():
            v.remove(v[self.name])
            a = '%s.Alpha' % self.name
            if a in v:
                v.remove(v[a])
            self.colors = None
            self.alpha = None
            self._samples = []

    def activate(self):
        self.colors.active = True

    def itersamples(self):
        if not self._samples:
            self._get_samples()
        for sample in self._samples:
            yield sample
        self._save_samples()

    @property
    def samples(self):
        if not self._samples:
            self._get_samples()
        return self._samples

class ColorLayerSample:
    def __init__(self, obj, layer, poly, poly_index, vertex, color, alpha):
        self.obj = obj
        self.layer = layer
        self.poly = poly
        self.poly_index = poly_index
        self.vertex = vertex
        self.color = color
        self.alpha = alpha

    def is_selected(self, mode='all'):
        if mode == 'all':
            return True
        elif mode == 'polygon' and self.poly:
            return self.poly.select
        else:
            return self.vertex.select

    def save(self):
        if isinstance(self.layer, LineColorLayer):
            self._save_line()
        else:
            self._save_poly()

    def _save_line(self):
        layer = self.layer
        kw = {'type': 'REPLACE'}
        i = self.vertex.index
        if not layer.alpha:
            layer.r.add([i], self.color.r, **kw)
            layer.g.add([i], self.color.g, **kw)
            layer.b.add([i], self.color.b, **kw)
            layer.a.add([i], self.alpha, **kw)
        else:
            layer.a.add([i], self.color.v, **kw)
        cc.ui.flag(self.obj.data)

    def _save_poly(self):
        colors = self.layer.colors.data
        colors[self.poly_index].color = mathutils.Color(self.color)
        if self.layer.alpha:
            a = self.alpha
            self.layer.alpha.data[self.poly_index].color = mathutils.Color((a, a, a))

class ColorOp:
    def rgb(*args):
        if not args:
            return Color()
        elif len(args) == 1:
            v = args[0]
            return Color((v, v, v))
        elif len(args) == 2:
            args += (args[1],)
        return Color(args[:3])

    def hsv(h, s, v):
        c = Color()
        c.v = v
        c.s = s
        c.h = h
        return c

    env = {
        'lerp': cc.utils.lerp,
        'rgb': rgb,
        'hsv': hsv,
    }

    def __init__(self, obj, source, layers):
        self.obj = obj
        self.source = source
        self.layers = layers

    def execute(self):
        obj = self.obj
        layers = self.layers
        source = self.source

        needed = []
        params = []
        for i, key in enumerate(layers):
            var = cc.utils.normalize_varname(key, lower=True)
            macro = '[%s]' % key
            if macro in source:
                params.append(var)
                needed.append(key)
            source = source.replace(macro, var)

        op = compile(source, '<string>', 'exec')

        for symbols in foreach(self.obj, *needed):
            env = dict(zip(params, symbols))
            exec(op, self.env, env)

class Colormap:
    def __init__(self, obj, name):
        self.obj = obj
        self.name = name
        self.data = obj.data

        self.update_colormap_data()

        if self.exists():
            self.props = self.colormap_data[self.name]
            self.uvmap = self.data.uv_textures[self.name]

    def update_colormap_data(self):
        data = self.data
        meta = colormeta(self.obj)

        if 'colormaps' not in meta:
            meta['colormaps'] = {}
        self.colormap_data = meta['colormaps']

        for tex in self.colormap_data.keys():
            if tex not in data.uv_layers:
                # removed from ui list
                del self.colormap_data[tex]
            elif tex not in data.uv_textures:
                # renamed in ui list
                index = data.uv_layers.keys().index(tex)
                name = data.uv_textures[index].name
                data.uv_layers[tex].name = name
                self.colormap_data[name] = self.colormap_data[tex]
                del self.colormap_data[tex]
            else:
                # not a colormap
                pass

    def exists(self):
        return (
            self.name in self.data.uv_textures and
            self.name in self.colormap_data)

    def create(self):
        if self.exists():
            return

        data = self.data.uv_textures

        active_index = data.active_index

        if self.name in data:
            data.remove(data[self.name])

        self.uvmap = uvmap = data.new()
        uvmap.name = self.name
        uvmap_index = data.values().index(uvmap)
        self.data.uv_layers[uvmap_index].name = self.name

        self.colormap_data[self.name] = {}
        self.props = self.colormap_data[self.name]
        self.props['size'] = COLORMAP_MINSIZE
        self.props['layers'] = []

        if active_index > -1:
            data.active_index = active_index

    def destroy(self):
        if self.exists():
            self.data.uv_textures.remove(self.uvmap)

    def activate(self):
        self.uvmap.active = True

    def get_size(self):
        return self.props['size']

    def set_size(self, size):
        self.props['size'] = cc.utils.nearest_pow_2(size)

    def get_layers(self):
        layers = self.props['layers']
        if not layers:
            return []
        else:
            return layers

    def set_layers(self, layers):
        self.props['layers'] = layers

    def fit_size(self, frag_count, layer_count):
        if frag_count == 0 or layer_count == 0:
            return COLORMAP_MINSIZE

        total = frag_count * layer_count
        approx = int(math.sqrt(total))
        size = cc.utils.nearest_pow_2(approx)

        index = layer_count - 1
        offset = int(math.ceil(frag_count / size) * size * index)
        last = offset + frag_count

        if last > (size * size):
            size = cc.utils.nearest_pow_2(size + 1)

        return max(size, COLORMAP_MINSIZE)

    def resize(self):
        layers = self.get_layers()
        self.set_size(self.fit_size(
            len(self.data.uv_layers[self.name].data),
            len(layers)))

    def get_stride(self):
        self.resize()

    def generate_image(self):
        self.resize()
        name = '%s.%s' % (self.obj.name, self.name)
        if name in bpy.data.images:
            image = bpy.data.images[name]
            image.user_clear()
            bpy.data.images.remove(image)
        size = self.get_size()
        image = bpy.data.images.new(name, size, size, alpha=True)
        return image

class PolyColormap(Colormap):
    def update_uv_coords(self):
        size = self.get_size()
        bias = 1. / size * 0.5
        uv_layer = self.data.uv_layers[self.name]
        for i, uv in enumerate(uv_layer.data):
            x = int(i % size) / size
            y = int(i / size) / size
            uv.uv.x = x + bias
            uv.uv.y = y + bias

    def create(self):
        super(PolyColormap, self).create()
        self.update_uv_coords()

    def set_size(self, size):
        super(PolyColormap, self).set_size(size)
        self.update_uv_coords()

    def set_layers(self, layers):
        super(PolyColormap, self).set_layers(layers)
        self.set_size(self.fit_size(
            len(self.data.uv_layers[self.name].data),
            len(layers)))

    def get_stride(self):
        super(PolyColormap, self).get_stride()
        size = self.get_size()
        vcolors = self.data.vertex_colors
        if not vcolors.active:
            return 0
        else:
            return int(math.ceil(len(vcolors.active.data) / size))

    def generate_image(self):
        image = super(PolyColormap, self).generate_image()

        self.update_uv_coords()

        vcolors = self.data.vertex_colors
        size = self.get_size()
        layers = self.get_layers()
        pixels = image.pixels
        stride = int(image.depth / 8)

        for index, layer in enumerate(layers):
            if layer not in vcolors:
                continue
            colors = vcolors[layer].data
            alpha_layer = '%s.Alpha' % layer
            if alpha_layer in vcolors:
                alpha = vcolors[alpha_layer].data
            else:
                alpha = None

            offset = int(math.ceil(
                len(colors) / size) * size * stride * index)

            for i, c in enumerate(colors):
                p = offset + i * stride
                image.pixels[p + 0] = c.color.r
                image.pixels[p + 1] = c.color.g
                image.pixels[p + 2] = c.color.b
                if alpha:
                    image.pixels[p + 3] = alpha[i].color.v
                else:
                    image.pixels[p + 3] = 1

        return image

class LineColormap(Colormap):
    def resize(self):
        with cc.utils.modified_mesh(self.obj) as mesh:
            super(LineColormap, self).resize()

    def set_layers(self, layers):
        super(LineColormap, self).set_layers(layers)
        with cc.utils.modified_mesh(self.obj) as mesh:
            self.set_size(self.fit_size(
                len(mesh.vertices),
                len(layers)))

    def get_stride(self):
        super(LineColormap, self).get_stride()
        size = self.get_size()
        return int(math.ceil(len(self.data.vertices) / size))

    def generate_image(self):
        image = super(LineColormap, self).generate_image()

        with cc.utils.modified_mesh(self.obj) as mesh:
            size = self.get_size()
            layers = self.get_layers()
            pixels = image.pixels
            stride = int(image.depth / 8)

            for index, layer in enumerate(layers):
                colors = Manager(self.obj).get_layer(layer)
                if not colors:
                    continue

                offset = int(math.ceil(
                    len(colors.samples) / size) * size * stride * index)

                for i, s in enumerate(colors.samples):
                    p = offset + i * stride
                    image.pixels[p + 0] = s.color.r
                    image.pixels[p + 1] = s.color.g
                    image.pixels[p + 2] = s.color.b
                    image.pixels[p + 3] = s.alpha

        return image

class Sampler:
    def __init__(self, obj, layer=None):
        self.obj = obj
        data = self.obj.data.vertex_colors
        if obj.type != 'MESH':
            raise ColorError('object is not a mesh')
        if layer is None:
            if not data.active:
                raise ColorError('no available colors')
            layer = data.active.name
        elif layer not in data:
            raise ColorError('invalid color layer')
        self.layer = layer
        self.modifier_settings = []

    def __enter__(self):
        self.install_triangulated()
        return self

    def __exit__(self, type_, value, tb):
        self.install_original()

    def install_triangulated(self):
        obj = self.obj
        self.mesh_original = obj.data
        self.mesh = obj.to_mesh(
            scene=bpy.context.scene,
            apply_modifiers=True,
            settings='PREVIEW')

        settings = self.modifier_settings
        for m in obj.modifiers:
            settings.append(m.show_viewport)
            m.show_viewport = False

        bm = bmesh.new()
        bm.from_mesh(self.mesh)
        bmesh.ops.triangulate(bm, faces=bm.faces, use_beauty=True)
        bm.to_mesh(self.mesh)
        bm.free()

        obj.data = self.mesh
        bpy.context.scene.update()
        self.layer = self.mesh.vertex_colors[self.layer]

    def install_original(self):
        obj = self.obj
        obj.data = self.mesh_original
        bpy.context.scene.update()
        bpy.data.meshes.remove(self.mesh)
        settings = self.modifier_settings
        for i, m in enumerate(obj.modifiers):
            m.show_viewport = settings[i]

    def closest(self, point, layer=None):
        m = self.obj.matrix_world.inverted()
        point = m * point
        return self.sample(layer=layer, *self.obj.closest_point_on_mesh(point))

    def raycast(self, start, end, layer=None):
        return self.sample(layer=layer, *self.obj.ray_cast(start, end))

    def sample(self, point, normal, face, layer=None):
        if face == -1:
            return mathutils.Color((0, 0, 0))

        obj = self.obj
        mesh = self.mesh
        colors = self.layer.data

        if layer is not None:
            colors = mesh.vertex_colors[layer].data

        poly = mesh.polygons[face]
        vert_a = mesh.vertices[poly.vertices[0]].co
        vert_b = mesh.vertices[poly.vertices[1]].co
        vert_c = mesh.vertices[poly.vertices[2]].co
        color_a = colors[poly.loop_indices[0]].color
        color_b = colors[poly.loop_indices[1]].color
        color_c = colors[poly.loop_indices[2]].color
        total_area = poly.area
        area_a = mathutils.geometry.area_tri(point, vert_b, vert_c)
        area_b = mathutils.geometry.area_tri(point, vert_a, vert_c)
        area_c = mathutils.geometry.area_tri(point, vert_a, vert_b)
        r = (color_a.r * area_a + color_b.r * area_b + color_c.r * area_c) / total_area
        g = (color_a.g * area_a + color_b.g * area_b + color_c.g * area_c) / total_area
        b = (color_a.b * area_a + color_b.b * area_b + color_c.b * area_c) / total_area

        return mathutils.Color((r, g, b))
