import bpy
import krz
import mathutils
from bgl import *

line_renderer = None

def _flag(obj): pass
flag = _flag

class LineRenderer:
    def __init__(self):
        self.handler = None
        self.obj_cache = {}
        self.mesh_cache = {}
        self.draw_handler = None
        self.last_mode = None

    def attach(self):
        self.draw_handler = bpy.types.SpaceView3D.draw_handler_add(
            self.draw, tuple(), 'WINDOW', 'POST_VIEW')
        bpy.app.handlers.scene_update_post.append(self.update)

    def detach(self):
        if self.draw_handler:
            bpy.types.SpaceView3D.draw_handler_remove(
                self.draw_handler, 'WINDOW')
            self.draw_handler = None
        if self.update in bpy.app.handlers.scene_update_post:
            bpy.app.handlers.scene_update_post.remove(self.update)

    def flag(self, obj):
        cache = self.obj_cache.get(obj.name)
        if cache is not None:
            cache.update = True
        else:
            cache = self.mesh_cache.get(obj.name)
            if cache is not None:
                cache.update = True

    def draw(self):
        context = bpy.context
        scene = context.scene
        view = context.area.spaces.active

        if context.mode != self.last_mode:
            self.last_mode = context.mode
            self.cleanup()

        if view.viewport_shade != 'TEXTURED':
            return

        glPushAttrib(GL_CLIENT_ALL_ATTRIB_BITS)
        glShadeModel(GL_SMOOTH)

        for obj in context.visible_objects:
            if (obj.type == 'MESH' and
                obj.data.edges and not
                obj.data.polygons and not
                obj.select and not
                obj == context.edit_object):

                cache = self.obj_cache.get(obj)
                if cache is None:
                    cache = LineObjCache(self, obj)
                    self.obj_cache[obj.name] = cache
                cache.draw()

        glPopAttrib()

    def update(self, scene):
        obj = scene.objects.active

        if (obj and
            obj.type == 'MESH' and
            obj.data.edges and not
            obj.data.polygons):
            if obj.is_updated:
                self.flag(obj)
            if obj.is_updated_data:
                self.flag(obj.data)

    def cleanup(self):
        real = set(bpy.data.objects.keys())
        cache = set(self.obj_cache.keys())
        stale = cache.difference(real)
        for k in stale:
            del self.obj_cache[k]

        real = set(bpy.data.meshes.keys())
        cache = set(self.mesh_cache.keys())
        stale = cache.difference(real)
        for k in stale:
            del self.mesh_cache[k]

class LineObjCache:
    def __init__(self, renderer, obj):
        self.renderer = renderer
        self.obj = obj
        self.update = True
        self.m = Buffer(GL_FLOAT, 16)

    def __del__(self):
        if hasattr(self, 'm'):
            del self.m

    def cache(self):
        matrix = self.obj.matrix_world.transposed()
        self.m[:] = sum((list(v) for v in matrix), [])
        self.update = False

    def draw(self):
        if self.update:
            self.cache()

        obj = self.obj
        renderer = self.renderer

        mesh = renderer.mesh_cache.get(obj.data)
        if mesh is None:
            mesh = LineMeshCache(obj.data)
            renderer.mesh_cache[obj.data.name] = mesh

        glPushMatrix()
        glMultMatrixf(self.m)
        mesh.draw(obj)
        glPopMatrix()

class LineMeshCache:
    def __init__(self, mesh):
        self.mesh = mesh
        self.update = True
        self.list = glGenLists(1)

    def __del__(self):
        if self.list != 0:
            glDeleteLists(self.list, 1)
            self.list = 0

    def cache(self, obj):
        mesh = self.mesh
        layer = krz.colors.Manager(obj).get_active_layer(False)
        if layer:
            samples = layer.samples
        verts = mesh.vertices

        glNewList(self.list, GL_COMPILE)
        glBegin(GL_LINES)
        for edge in mesh.edges:
            x = verts[edge.vertices[0]]
            y = verts[edge.vertices[1]]
            if layer:
                x_color = samples[x.index].color
                y_color = samples[y.index].color
            else:
                x_color = y_color = (1, 1, 1)
            glColor3f(*x_color)
            glVertex3f(*(x.co))
            glColor3f(*y_color)
            glVertex3f(*(y.co))
        glEnd()
        glEndList()

        self.update = False

    def draw(self, obj):
        if self.update:
            self.cache(obj)
        glCallList(self.list)

def install_line_renderer():
    global line_renderer
    global flag

    uninstall_line_renderer()

    line_renderer = LineRenderer()
    line_renderer.attach()
    flag = line_renderer.flag

def uninstall_line_renderer():
    global line_renderer
    global flag, _flag

    if line_renderer is not None:
        line_renderer.detach()
        line_renderer = None
        flag = _flag

def ui_heading(self, context):
    # self.layout.separator()
    self.layout.label('')
    self.layout.separator()

@bpy.app.handlers.persistent
def setup_line_renderer(scene):
    install_line_renderer()

bpy.types.VIEW3D_MT_object_specials.append(ui_heading)
bpy.types.VIEW3D_MT_edit_mesh_specials.append(ui_heading)
bpy.app.handlers.load_post.append(setup_line_renderer)
