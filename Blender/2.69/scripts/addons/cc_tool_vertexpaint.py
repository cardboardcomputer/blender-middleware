import bpy
import bgl
import cc
import math
import time
import bmesh
import itertools
import mathutils as mu

from bpy import ops
from bpy_extras import view3d_utils
from cc.utils import lerp

bl_info = {
    'name': 'Tool: Vertex Paint',
    'author': 'Cardboard Computer',
    'blender': (2, 69, 0),
    'description': 'Homebrew vertex painting tool',
    'category': 'Cardboard'
}

TOOL_KMI = None

class EditmodeContext:
    def __init__(self, mode_wanted):
        self.mode_wanted = mode_wanted
        self.toggled = False

    def __enter__(self):
        self.mode_original = bpy.context.mode
        if self.mode_wanted != self.mode_original:
            ops.object.editmode_toggle()
            self.toggled = True
        bpy.context.scene.update()
        return self

    def __exit__(self, type, value, traceback):
        if self.toggled:
            ops.object.editmode_toggle()
        bpy.context.scene.update()
        self.toggled = False

OBJECT_MODE = EditmodeContext('OBJECT')
EDIT_MODE = EditmodeContext('EDIT_MESH')

BLEND_ITEMS = (
    ('MIX', 'Mix', 'Mix'),
    ('MULTIPLY', 'Multiply', 'Multiply'),
    ('ADD', 'Add', 'Add'),
    ('SUBTRACT', 'Subtract', 'Subtract'),
)

FALLOFF_ITEMS = (
    ('LINEAR', 'Linear', 'Linear'),
    ('SMOOTH', 'Smooth', 'Smooth'),
    ('SHARP', 'Sharp', 'Sharp'),
    ('ROOT', 'Root', 'Root'),
)

MASK_ITEMS = (
    ('OCCLUDE', 'Occlude', 'Occlude'),
    ('ALL', 'All', 'All'),
    ('NORMAL', 'Normal', 'Normal'),
)

NORMAL_ITEMS = (
    ('VERTEX', 'Vertex', 'Vertex'),
    ('FACE', 'Face', 'Face'),
)

STROKE_METHOD_ITEMS = (
    ('SHIFT', 'Shift', 'Shift'),
    ('TIME', 'Time', 'Time'),
)

@cc.ops.editmode
def sample_color(context, event, ray_max=1000.0):
    result = cc.utils.find(context, event, 10000)
    if result is not None:
        obj, origin, target = result
        if obj.data.vertex_colors.active:
            with cc.colors.Sampler(obj) as sampler:
                return sampler.raycast(origin, target)
    return mu.Color((0, 0, 0))

class VertexPaintSettings(bpy.types.PropertyGroup):
    color = bpy.props.FloatVectorProperty(name="Color", subtype='COLOR_GAMMA', min=0, max=1, step=1,)
    blend = bpy.props.EnumProperty(name='Blend', items=BLEND_ITEMS, default='MIX')
    radius = bpy.props.IntProperty(name='Radius', min=0, default=32)
    strength = bpy.props.FloatProperty(name='Strength', min=0, max=1, step=1, default=1)
    bias = bpy.props.FloatProperty(name='Bias', min=0, max=1, step=1, default=0)
    scale = bpy.props.FloatProperty(name='Scale', min=0, max=1, step=1, default=1)
    falloff = bpy.props.EnumProperty(name='Falloff', items=FALLOFF_ITEMS, default='LINEAR')
    mask = bpy.props.EnumProperty(name='Mask', items=MASK_ITEMS, default='OCCLUDE')
    normal = bpy.props.EnumProperty(name='Normal', items=NORMAL_ITEMS, default='VERTEX')
    normal_bias = bpy.props.FloatProperty(name='Bias', min=0, max=1, step=1, default=0)
    normal_scale = bpy.props.FloatProperty(name='Scale', min=0, max=1, step=1, default=1)
    stroke_method = bpy.props.EnumProperty(name='Stroke Method', items=STROKE_METHOD_ITEMS, default='SHIFT')
    stroke_spacing = bpy.props.IntProperty(name='Stroke Spacing', default=3, min=1)
    stroke_timestep = bpy.props.FloatProperty(name='Stroke Timestep', default=0.02)

def vertex_paint_preset_selected(self, context):
    s = context.scene
    d = context.active_object.data

    if d.vertex_paint_active_preset:
        preset = d.vertex_paint_presets[d.vertex_paint_active_preset]
        for prop in s.vertex_paint.keys():
            setattr(s.vertex_paint, prop, getattr(preset, prop))

PROP_VERTEX_PAINT_SETTINGS = bpy.props.PointerProperty(type=VertexPaintSettings)

PROP_VERTEX_PAINT_PRESETS = bpy.props.CollectionProperty(type=VertexPaintSettings)

PROP_VERTEX_PAINT_ACTIVE_PRESET = bpy.props.StringProperty(name='Preset', default='', update=vertex_paint_preset_selected)

class VertexPaintPanel(bpy.types.Panel):
    bl_label = 'Vertex Paint'
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return context.mode == 'EDIT_MESH'

    def draw(self, context):
        layout = self.layout
        data = context.active_object.data
        vps = data.vertex_paint_settings

        c = layout.column(align=True)
        r = c.row(align=True)
        r.prop_search(data, 'vertex_paint_active_preset', data, 'vertex_paint_presets', '', icon='SETTINGS')
        r.operator('cc.vertex_paint_preset_add', '', icon='ZOOMIN')
        r.operator('cc.vertex_paint_preset_remove', '', icon='X')
        if data.vertex_paint_active_preset:
            r = c.row(align=True)
            r.operator('cc.vertex_paint_preset_update', 'Update', icon='COPYDOWN')
            r.operator('cc.vertex_paint_preset_revert', 'Revert', icon='PASTEDOWN')

        layout.template_color_picker(vps, 'color', value_slider=True)

        layout.prop(vps, 'color', '')

        col = layout.column(align=True)
        col.prop(vps, 'radius')
        col.prop(vps, 'strength')

        col = layout.column(align=True)
        col.prop(vps, 'blend', '')
        col.prop(vps, 'falloff', '')

        col = layout.column(align=True)
        col.prop(vps, 'bias')
        col.prop(vps, 'scale')
        row = col.row(align=True)
        row.prop(vps, 'stroke_method', expand=True)
        if vps.stroke_method == 'SHIFT':
            col.prop(vps, 'stroke_spacing', 'Spacing')
        elif vps.stroke_method == 'TIME':
            col.prop(vps, 'stroke_timestep', 'Timestep')

        col = layout.column(align=True)
        col.prop(vps, 'mask', '')
        if vps.mask == 'NORMAL':
            col.prop(vps, 'normal_bias')
            col.prop(vps, 'normal_scale')
            row = col.row(align=True)
            row.prop(vps, 'normal', expand=True)

class VertexPaintPresetAdd(bpy.types.Operator):
    bl_idname = 'cc.vertex_paint_preset_add'
    bl_label = 'Add Preset'
    bl_options = {'UNDO'}

    name = bpy.props.StringProperty(name='Name')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return context.mode == 'EDIT_MESH' and obj and obj.type == 'MESH'

    def invoke(self, context, event):
        wm = context.window_manager
        return wm.invoke_props_dialog(self)

    def execute(self, context):
        s = context.active_object.data
        preset = s.vertex_paint_presets.add()
        for prop in s.vertex_paint_settings.keys():
            setattr(preset, prop, getattr(s.vertex_paint_settings, prop))
        preset.name = self.name
        s.vertex_paint_active_preset = preset.name
        return {'FINISHED'}

class VertexPaintPresetRemove(bpy.types.Operator):
    bl_idname = 'cc.vertex_paint_preset_remove'
    bl_label = 'Remove Preset'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return context.mode == 'EDIT_MESH' and obj and obj.type == 'MESH'

    def execute(self, context):
        s = context.active_object.data
        if s.vertex_paint_active_preset:
            idx = s.vertex_paint_presets.find(s.vertex_paint_active_preset)
            s.vertex_paint_presets.remove(idx)
        s.vertex_paint_active_preset = ''
        self.report({'INFO'}, 'Preset removed.')
        return {'FINISHED'}

class VertexPaintPresetUpdate(bpy.types.Operator):
    bl_idname = 'cc.vertex_paint_preset_update'
    bl_label = 'Update Preset'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return context.mode == 'EDIT_MESH' and obj and obj.type == 'MESH'

    def execute(self, context):
        s = context.active_object.data
        if not s.vertex_paint_active_preset:
            self.report({'ERROR'}, 'No preset active.')
            return {'CANCELLED'}
        preset = s.vertex_paint_presets[s.vertex_paint_active_preset]
        for prop in s.vertex_paint_settings.keys():
            setattr(preset, prop, getattr(s.vertex_paint_settings, prop))
        self.report({'INFO'}, 'Preset updated.')
        return {'FINISHED'}

class VertexPaintPresetRevert(bpy.types.Operator):
    bl_idname = 'cc.vertex_paint_preset_revert'
    bl_label = 'Load Preset'
    bl_options = {'UNDO'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return context.mode == 'EDIT_MESH' and obj and obj.type == 'MESH'

    def execute(self, context):
        s = context.active_object.data
        if not s.vertex_paint_active_preset:
            self.report({'ERROR'}, 'No preset active.')
            return {'CANCELLED'}
        preset = s.vertex_paint_presets[s.vertex_paint_active_preset]
        for prop in s.vertex_paint_settings.keys():
            setattr(s.vertex_paint_settings, prop, getattr(preset, prop))
        self.report({'INFO'}, 'Reverted to preset.')
        return {'FINISHED'}

class VertexPaintTool(bpy.types.Operator):
    bl_idname = 'cc.vertex_paint_tool'
    bl_label = 'Vertex Paint Tool'
    bl_options = {'REGISTER'}

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return context.mode == 'EDIT_MESH' and obj and obj.type == 'MESH'

    def __init__(self):
        self._draw_3d = None
        self._draw_2d = None
        self._timer = None
        self._handers_installed = False

        self.obj = None
        self.mesh = None

        self.mouse_pos = (0, 0)
        self.painting = False
        self.touched = False

        self.vert_select = []
        self.edge_select = []
        self.face_select = []
        self.select_some = False
        self.select_none = False
        self.select_all = False
        self.mesh_changed = False
        self.select_changed = False

        self.weights = {}
        self.mask_daub_verts = set()
        self.mask_daub_faces = set()
        self.mask_select_verts = set()
        self.mask_select_faces = set()
        self.last_daub_time = 0;
        self.last_daub_position = mu.Vector((0, 0))

    def __del__(self):
        self.del_viewport_handlers()

    def execute(self, context):
        return {'FINISHED'}

    def invoke(self, context, event):
        global TOOL_KMI

        obj = context.active_object

        if not obj.data.vertex_colors.active:
            self.report({'ERROR'}, 'No vertex colors.')
            return {'CANCELLED'}

        self.theme = context.user_preferences.themes['Default']

        self.original_viewport_shade = context.space_data.viewport_shade
        self.original_show_faces = obj.data.show_faces
        self.original_editmesh_active = self.theme.view_3d.editmesh_active[3]

        obj.data.show_faces = False
        context.space_data.viewport_shade = 'TEXTURED'
        self.theme.view_3d.editmesh_active[3] = 0

        context.window_manager.modal_handler_add(self)

        if TOOL_KMI is None:
            wm = context.window_manager
            for kc in wm.keyconfigs:
                for keymap in kc.keymaps:
                    for kmi in keymap.keymap_items:
                        if kmi.idname == 'cc.vertex_paint_tool':
                            TOOL_KMI = kmi

        return {'RUNNING_MODAL'}

    def cleanup(self, context, event):
        if context.mode == 'EDIT_MESH':
            bmesh.update_edit_mesh(self.obj.data)
        self.del_viewport_handlers(context)
        context.space_data.viewport_shade = self.original_viewport_shade
        self.obj.data.show_faces = self.original_show_faces
        self.theme.view_3d.editmesh_active[3] = self.original_editmesh_active
        context.window.cursor_modal_restore()
        context.area.tag_redraw()

    def toggled(self, context, event):
        if TOOL_KMI:
            if (TOOL_KMI.type == event.type and
                TOOL_KMI.value == event.value and
                TOOL_KMI.ctrl == event.ctrl and
                TOOL_KMI.shift == event.shift and
                TOOL_KMI.alt == event.alt):
                return True
        return False

    def modal(self, context, event):
        if not self._handers_installed:
            self.add_viewport_handlers(context)

        context.window.cursor_modal_set('CROSSHAIR')
        context.area.tag_redraw()

        if context.mode != 'EDIT_MESH' or self.toggled(context, event):
            self.cleanup(context, event)
            if self.touched:
                return {'FINISHED'}
            else:
                return {'CANCELLED'}
            
        update_mesh = False

        if self.obj != context.active_object:
            self.obj = context.active_object
            update_mesh = True
        if self.mesh_changed:
            update_mesh = True
            self.select_changed = True
            self.mesh_changed = False

        if update_mesh:
            self.mesh = bmesh.from_edit_mesh(self.obj.data)
            self.select_changed = True

        obj = self.obj
        mesh = self.mesh
        scene = context.scene
        vps = obj.data.vertex_paint_settings
        radius = float(vps.radius)

        region = context.region
        region_3d = context.space_data.region_3d
        mouse_pos = mouse_x, mouse_y = (event.mouse_region_x, event.mouse_region_y)
        to_obj = obj.matrix_world.inverted()
        direction = to_obj * view3d_utils.region_2d_to_vector_3d(region, region_3d, mouse_pos).normalized()
        mouse = mu.Vector(mouse_pos)

        self.mouse_pos = mouse_pos

        if event.type in ('RIGHTMOUSE', 'A') and event.value == 'RELEASE':
            self.mesh_changed = True

        if not self.painting and (
                mouse_x < 0 or mouse_x > region.width or
                mouse_y < 0 or mouse_y > region.height):
            return {'PASS_THROUGH'}

        if event.type == 'LEFTMOUSE':
            if event.value == 'PRESS':
                self.last_daub_position = mu.Vector((-1000, -1000))
                self.last_daub_time = 0
                self.painting = True

            elif event.value == 'RELEASE':
                ops.ed.undo_push()
                bmesh.update_edit_mesh(obj.data)
                scene.update()
                self.painting = False

        if self.painting:
            self.touched = True

            update_mask = False
            apply_daub = False

            if event.type in ('LEFTMOUSE', 'MOUSEMOVE'):
                if vps.stroke_method == 'SHIFT':
                    delta = (mouse - self.last_daub_position).magnitude
                    if delta < vps.stroke_spacing:
                        return {'RUNNING_MODAL'}
                    else:
                        self.last_daub_position = mouse
                        apply_daub = True
                        update_mask = True
                else:
                    update_mask = True
    
            if vps.stroke_method == 'TIME' and event.type == 'TIMER':
                now = time.time()
                delta = now - self.last_daub_time
                if delta < vps.stroke_timestep:
                    return {'RUNNING_MODAL'}
                else:
                    self.last_daub_time = now
                    apply_daub = True

            if update_mask:
                if self.select_changed:
                    mesh.verts.index_update()
                    mesh.edges.index_update()
                    mesh.faces.index_update()
                    self.vert_select = [v.select for v in mesh.verts]
                    self.edge_select = [e.select for e in mesh.edges]
                    self.face_select = [f.select for f in mesh.faces]
                    self.select_none = (
                        (True not in self.vert_select) and
                        (True not in self.edge_select) and
                        (True not in self.face_select))
                    self.select_all = (
                        (False not in self.vert_select) and
                        (False not in self.edge_select) and
                        (False not in self.face_select))
                    self.select_some = not (self.select_none or self.select_all)
                    if self.select_some:
                        self.mask_select_verts = set(v.index for v in mesh.verts if v.select)
                        self.mask_select_faces = set(f.index for f in mesh.faces if f.select)
                    self.select_changed = False

                occlude = (vps.mask == 'OCCLUDE')

                mesh_select_mode = tuple(context.tool_settings.mesh_select_mode)
                use_occlude_geometry = context.space_data.use_occlude_geometry
                context.tool_settings.mesh_select_mode = (True, True, True)
                context.space_data.use_occlude_geometry = occlude
                ops.mesh.select_all(action='DESELECT')
                ops.view3d.select_circle(x=mouse_x, y=mouse_y, radius=radius, gesture_mode=3)
                self.mask_daub_verts = set([vert.index for vert in mesh.verts if vert.select])
                self.mask_daub_faces = set([face.index for face in mesh.faces if face.select])
                context.tool_settings.mesh_select_mode = mesh_select_mode
                context.space_data.use_occlude_geometry = use_occlude_geometry
                ops.mesh.select_all(action='DESELECT')

                if self.select_all:
                    ops.mesh.select_all(action='SELECT')
                    scene.update()

                elif not self.select_none:
                    if mesh_select_mode[0]:
                        [v.select_set(s) for (v, s) in zip(mesh.verts, self.vert_select) if s]
                    if mesh_select_mode[1]:
                        [e.select_set(s) for (e, s) in zip(mesh.edges, self.edge_select) if s]
                    if mesh_select_mode[2]:
                        [f.select_set(s) for (f, s) in zip(mesh.faces, self.face_select) if s]

                bias = vps.bias
                scale = vps.scale
                weights = self.weights = {}

                if self.select_some:
                    verts = self.mask_select_verts.intersection(self.mask_daub_verts)
                else:
                    verts = self.mask_daub_verts

                falloff = lambda x: x

                if vps.falloff == 'SMOOTH':
                    falloff = cc.utils.smooth
                elif vps.falloff == 'SHARP':
                    falloff = math.sqrt
                elif vps.falloff == 'ROOT':
                    falloff = lambda x: x * x

                for vid in verts:
                    vert = mesh.verts[vid]
                    p = obj.matrix_world * vert.co
                    p = view3d_utils.location_3d_to_region_2d(region, region_3d, p)
                    dist = min(1, max(0, (p - mouse).magnitude / radius))
                    dist = max(min((dist - bias) / scale, 1), 0)
                    dist = falloff(dist)
                    weights[vid] = 1 - dist

            if apply_daub:
                weights = self.weights
                layer = mesh.loops.layers.color.active
            
                if self.select_some:
                    faces = self.mask_select_faces.intersection(self.mask_daub_faces)
                else:
                    faces = self.mask_daub_faces

                b = vps.color
                white = mu.Color((1, 1, 1))
                black = mu.Color((0, 0, 0))
                strength = vps.strength
                nbias = vps.normal_bias
                nscale = vps.normal_scale

                if vps.mask == 'NORMAL':
                    if vps.normal == 'VERTEX':
                        normal_mask = lambda f, v: max(min((
                            (direction.dot(v.normal) * 0.5 + 0.5) -
                            nbias) / nscale, 1), 0)
                    else:
                        normal_mask = lambda f, v: max(min((
                            (direction.dot(f.normal) * 0.5 + 0.5) -
                            nbias) / nscale, 1), 0)
                else:
                    normal_mask = lambda f, v: 1

                if vps.blend == 'MIX':
                    for fid in faces:
                        face = mesh.faces[fid]
                        for loop in face.loops:
                            weight = weights[loop.vert.index]
                            mask = normal_mask(face, loop.vert)
                            a = loop[layer]
                            a.r = lerp(a.r, b.r, weight * strength * mask)
                            a.g = lerp(a.g, b.g, weight * strength * mask)
                            a.b = lerp(a.b, b.b, weight * strength * mask)

                if vps.blend == 'MULTIPLY':
                    for fid in faces:
                        face = mesh.faces[fid]
                        for loop in face.loops:
                            weight = weights[loop.vert.index]
                            mask = normal_mask(face, loop.vert)
                            a = loop[layer]
                            a.r *= lerp(1, b.r, weight * strength * mask)
                            a.g *= lerp(1, b.g, weight * strength * mask)
                            a.b *= lerp(1, b.b, weight * strength * mask)

                if vps.blend == 'ADD':
                    for fid in faces:
                        face = mesh.faces[fid]
                        for loop in face.loops:
                            weight = weights[loop.vert.index]
                            mask = normal_mask(face, loop.vert)
                            a = loop[layer]
                            a.r += lerp(0, b.r, weight * strength * mask)
                            a.g += lerp(0, b.g, weight * strength * mask)
                            a.b += lerp(0, b.b, weight * strength * mask)

                if vps.blend == 'SUBTRACT':
                    for fid in faces:
                        face = mesh.faces[fid]
                        for loop in face.loops:
                            weight = weights[loop.vert.index]
                            mask = normal_mask(face, loop.vert)
                            a = loop[layer]
                            a.r -= lerp(0, b.r, weight * strength * mask)
                            a.g -= lerp(0, b.g, weight * strength * mask)
                            a.b -= lerp(0, b.b, weight * strength * mask)

                bmesh.update_edit_mesh(obj.data)

            return {'RUNNING_MODAL'}

        else:
            if event.type == 'D' and event.value == 'PRESS':
                vps.color = sample_color(context, event)
                return {'RUNNING_MODAL'}
    
            if event.type == 'WHEELUPMOUSE' and event.ctrl:
                vps.radius = max(1, math.floor(vps.radius * 0.9))
                return {'RUNNING_MODAL'}

            if event.type == 'WHEELDOWNMOUSE' and event.ctrl:
                vps.radius = max(1, math.ceil(vps.radius * 1.1))
                return {'RUNNING_MODAL'}

            if event.type == 'ESC':
                self.cleanup(context, event)
                return {'CANCELLED'}

            if event.type == 'SPACE':
                self.cleanup(context, event)
                return {'FINISHED'}

        return {'PASS_THROUGH'}

    def draw_viewport_2d(self, context):
        data = context.active_object.data
        vps = data.vertex_paint_settings

        bgl.glPushAttrib(
            bgl.GL_DEPTH_BUFFER_BIT |
            bgl.GL_LINE_BIT |
            bgl.GL_COLOR_BUFFER_BIT |
            bgl.GL_CURRENT_BIT)

        bgl.glEnable(bgl.GL_BLEND)
        bgl.glDepthFunc(bgl.GL_ALWAYS)
        bgl.glLineWidth(1)

        bgl.glBegin(bgl.GL_LINES)

        mx, my = self.mouse_pos
        radius = vps.radius
        ticks = radius
        if ticks % 2 != 0:
            ticks -= 1
        ticks = min(512, max(16, ticks))

        bgl.glColor4f(0, 0, 0, 1)
        for i in range(ticks):
            v = i / float(ticks)
            x = mx + math.cos(v * math.pi * 2) * radius
            y = my + math.sin(v * math.pi * 2) * radius
            bgl.glVertex2f(x, y)

        bgl.glVertex2f(x, y)

        bgl.glColor4f(1, 1, 1, 1)
        for i in range(ticks):
            v = i / float(ticks)
            x = mx + math.cos(v * math.pi * 2) * radius
            y = my + math.sin(v * math.pi * 2) * radius
            bgl.glVertex2f(x, y)

        bgl.glEnd()

        bgl.glPopAttrib();

    def draw_viewport_3d(self, context):
        pass

    def on_mesh_changed(self, scene):
        try:
            if self.obj and (self.obj.is_updated or self.obj.is_updated_data):
                self.mesh_changed = True
        except:
            try:
                if self.on_mesh_changed in bpy.app.handlers.scene_update_post:
                    bpy.app.handlers.scene_update_post.remove(self.on_mesh_changed)
            except:
                pass

    def add_viewport_handlers(self, context):
        self._draw_3d = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_viewport_3d, (context,), 'WINDOW', 'POST_VIEW')
        self._draw_2d = bpy.types.SpaceView3D.draw_handler_add(
            self.draw_viewport_2d, (context,), 'WINDOW', 'POST_PIXEL')
        self._timer = context.window_manager.event_timer_add(0.01, context.window)

        bpy.app.handlers.scene_update_post.append(self.on_mesh_changed)
        
        self._handers_installed = True

    def del_viewport_handlers(self, context=None):
        if not context:
            context = bpy.context

        if self._draw_3d:
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_3d, 'WINDOW')
            self._draw_3d = None
        if self._draw_2d:
            bpy.types.SpaceView3D.draw_handler_remove(self._draw_2d, 'WINDOW')
            self._draw_2d = None
        if self._timer:
            context.window_manager.event_timer_remove(self._timer)
            self._timer = None

        if self.on_mesh_changed in bpy.app.handlers.scene_update_post:
            bpy.app.handlers.scene_update_post.remove(self.on_mesh_changed)

        self._handers_installed = False

def register():
    cc.utils.register(__REGISTER__)

def unregister():
    cc.utils.unregister(__REGISTER__)

__REGISTER__ = (
    VertexPaintSettings,
    VertexPaintPanel,
    VertexPaintPresetAdd,
    VertexPaintPresetRemove,
    VertexPaintPresetUpdate,
    VertexPaintPresetRevert,
    VertexPaintTool,
    (bpy.types.Mesh, 'vertex_paint_settings', PROP_VERTEX_PAINT_SETTINGS),
    (bpy.types.Mesh, 'vertex_paint_presets', PROP_VERTEX_PAINT_PRESETS),
    (bpy.types.Mesh, 'vertex_paint_active_preset', PROP_VERTEX_PAINT_ACTIVE_PRESET),
)
