import bpy
import krz
import atexit
import mathutils
from bgl import *
from krz.colors import colormeta, Manager

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

    def clear(self):
        for cache in self.obj_cache.values():
            cache.__del__()
        for cache in self.mesh_cache.values():
            cache.__del__()

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
        cache = self.obj_cache.get(hash(obj))
        if cache is not None:
            cache.update = True
        else:
            cache = self.mesh_cache.get(hash(obj))
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

                cache = self.obj_cache.get(hash(obj))
                if cache is None:
                    cache = LineObjCache()
                    self.obj_cache[hash(obj)] = cache
                cache.draw(self, obj)

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
        real = set(hash(o) for o in bpy.data.objects)
        cache = set(self.obj_cache.keys())
        stale = cache.difference(real)
        for k in stale:
            del self.obj_cache[k]

        real = set(hash(o) for o in bpy.data.meshes)
        cache = set(self.mesh_cache.keys())
        stale = cache.difference(real)
        for k in stale:
            del self.mesh_cache[k]

class LineObjCache:
    def __init__(self):
        self.update = True
        self.m = Buffer(GL_FLOAT, 16)

    def __del__(self):
        if hasattr(self, 'm'):
            del self.m

    def cache(self, renderer, obj):
        matrix = obj.matrix_world.transposed()
        self.m[:] = sum((list(v) for v in matrix), [])
        self.update = False

    def draw(self, renderer, obj):
        if self.update:
            self.cache(renderer, obj)

        data = obj.data
        if data:
            mesh = renderer.mesh_cache.get(hash(obj.data))
            if mesh is None:
                mesh = LineMeshCache()
                renderer.mesh_cache[hash(obj.data)] = mesh

            glPushMatrix()
            glMultMatrixf(self.m)
            mesh.draw(renderer, obj)
            glPopMatrix()

class LineMeshCache:
    def __init__(self):
        self.update = True
        self.list = glGenLists(1)

    def __del__(self):
        if self.list != 0:
            glDeleteLists(self.list, 1)
            self.list = 0

    def cache(self, renderer, obj):
        scene = bpy.context.scene
        layer = Manager(obj).get_active_layer(False)

        if layer is not None:
            name = colormeta(obj)['active_line_color']
    
            orig_mesh = obj.data
            mesh = obj.data = obj.to_mesh(
                scene=scene,
                apply_modifiers=True,
                settings='PREVIEW')
            scene.update()

            layer = Manager(obj).get_layer(name)
            samples = layer.samples
            verts = mesh.vertices

            glNewList(self.list, GL_COMPILE)
            glBegin(GL_LINES)
            for edge in mesh.edges:
                x = verts[edge.vertices[0]]
                y = verts[edge.vertices[1]]
                x_color = samples[x.index].color
                y_color = samples[y.index].color
                glColor3f(*x_color)
                glVertex3f(*(x.co))
                glColor3f(*y_color)
                glVertex3f(*(y.co))
            glEnd()
            glEndList()

            obj.data = orig_mesh
            scene.update()

        self.update = False

    def draw(self, renderer, obj):
        if self.update:
            self.cache(renderer, obj)
        if self.list != 0:
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

def clear_line_renderer():
    global line_renderer
    if line_renderer is not None:
        line_renderer.clear()

bpy.types.VIEW3D_MT_object_specials.append(ui_heading)
bpy.types.VIEW3D_MT_edit_mesh_specials.append(ui_heading)
bpy.app.handlers.load_post.append(setup_line_renderer)
atexit.register(clear_line_renderer)
