import bpy
import bmesh

NAME = '(Plot)'

def line(gen, name=NAME):
    """Plot arbitrary x,y values as line"""
    with Plotter(name) as p:
        for x, y in gen:
            p.extend(x, y)
        p.link(bpy.context.scene)
  
def plot(fn, res=1024, extents=1, name=NAME):
    """Plot y values as a function of x"""
    with Plotter(name) as p:
        for x in range(res * (extents * 2 + 1) + 1):
            x -= res * extents
            x = float(x) / float(res)
            try:
                y = fn(x)
            except ZeroDivisionError:
                p.clip()
                continue
            except ValueError as e:
                if str(e) == 'math domain error':
                    p.clip()
                    continue
                else:
                    raise e
            p.extend(x, y)
        p.link(bpy.context.scene)

class Plotter:
    def __init__(self, name):
        self.name = name

    def __enter__(self):
        if self.name in bpy.data.objects:
            self.obj = bpy.data.objects[self.name]
            self.data = self.obj.data
        else:
            self.data = bpy.data.meshes.new(self.name)
            self.obj = bpy.data.objects.new(self.name, self.data)

        self.mesh = bmesh.new()
        self.mesh.from_mesh(self.data)
        self.mesh.clear()
        self.last = None

        return self

    def __exit__(self, t, v, e):
        self.mesh.to_mesh(self.data)
        self.mesh.free()
        self.obj.data.update()

    def link(self, scene):
        if self.obj.name not in scene.objects:
            scene.objects.link(self.obj)
            scene.update()
        self.obj.select = True

    def extend(self, x, y):
        vert = self.mesh.verts.new((x, 0, y))
        if self.last is not None:
             self.mesh.edges.new((self.last, vert))
        self.last = vert

    def clip(self):
        self.last = None

__all__ = ('line', 'plot', 'Plotter')
