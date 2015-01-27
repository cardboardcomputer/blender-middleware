import krz
import krz.colors

ATTR_COLORS = (krz.colors.BASENAME, 'R', 'G', 'B', 'A')
ATTR_NORMAL = ('Normal', 'X', 'Y', 'Z')

def is_line(obj):
    return (
        obj.type == 'MESH' and
        len(obj.data.polygons) == 0 and
        len(obj.data.edges) > 0)

def colors(obj):
    return LineAttribute(obj, *ATTR_COLORS)

def normals(obj):
    attrs = LineAttribute(obj, *ATTR_NORMAL)
    attrs.set_filter = lambda v: v * 0.5 + 0.5
    attrs.get_filter = lambda v: v * 2.0 - 1.0
    return attrs

class LineAttribute:
    """
    Single or multi-dimensional float arrays stored as vertex groups.

    Limitiation is that values have to be from 0-1, since vertex
    groups only store normalized values.
    """
    def __init__(self, obj, base, *channels):
        self.obj = obj
        self.data = obj.data
        self.base = base
        self.channels = channels
        self._exists = None

    def exists(self):
        if self._exists is not None:
            return self._exists
        v = self.obj.vertex_groups
        for channel in self.get_channel_names():
            if channel not in v:
                self._exists = False
                return False
        else:
            self._exists = True
            return True

    def single(self):
        return not self.channels

    def create(self):
        if self.exists():
            return

        v = self.obj.vertex_groups
        active = v.active_index

        kwargs = {'type': 'ADD'}
        vindices = [v.index for v in self.data.vertices]
        for channel in self.get_channel_names():
            g = v.new()
            g.name = channel
            g.add(vindices, self.set_filter(0), **kwargs)

        v.active_index = active
        self._exists = True

    def destroy(self):
        v = self.obj.vertex_groups
        if self.exists():
            for channel in self.get_channel_names():
                v.remove(v[channel])
        self._exists = False

    def activate(self):
        v = self.obj.vertex_groups
        v.active_index = v[self.get_channel_names()[0]].index

    def get_channel_names(self):
        if self.channels:
            return ('%s.%s' % (self.base, c) for c in self.channels)
        else:
            return (self.base,)

    def get_filter(self, value):
        return value

    def set_filter(self, value):
        return value

    def get(self, index):
        if not self.exists():
            self.create()
        v = self.obj.vertex_groups
        if self.single():
            return self.get_filter(v[self.base].weight(index))
        else:
            o = {}
            for c in self.channels:
                o[c] = self.get_filter(v['%s.%s' % (self.base, c)].weight(index))
            return o

    def set(self, index, *values, **valueskw):
        if not self.exists():
            self.create()
        v = self.obj.vertex_groups
        kwargs = {'type': 'REPLACE'}
        if self.single():
            v[self.base].add([index], self.set_filter(values[0]), **kwargs)
        else:
            o = {}
            for i, value in enumerate(values):
                c = self.channels[i]
                o[c] = v['%s.%s' % (self.base, c)].add(
                    [index], self.set_filter(value), **kwargs)
            for c, value in kwargs.items():
                if c in self.channels:
                    o[c] = v['%s.%s' % (self.base, c)].add(
                        [index], self.set_filter(value), **kwargs)
