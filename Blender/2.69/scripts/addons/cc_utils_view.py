import bpy
import cc
import math
import mathutils as mu

bl_info = {
    'name': 'Utils: View',
    'author': 'Cardboard Computer',
    'blender': (2, 69, 0),
    'description': 'View/navigation operators for Y-up space',
    'category': 'Cardboard'
}

_original_unit_draw = None

def unit_draw(self, context):
    global _original_unit_draw
    _original_unit_draw(self, context)
    self.layout.separator()
    self.layout.prop(context.scene, 'y_up', toggle=True)

def update_y_prop(self, context):
    global y_up_active

    scene = context.scene

    y = scene.gravity.y
    z = scene.gravity.z
    scene.gravity.y = z
    scene.gravity.z = y

    if scene.y_up and not y_up_active:
        y_up_activate()
    elif not scene.y_up and y_up_active:
        y_up_deactivate()

_z_kmi = []
_y_kmi = []
_scene = None
y_up_active = False

def collect_kmi():
    global _z_kmi
    global _y_kmi

    _z_kmi = []
    _y_kmi = []

    keyconfig = bpy.context.window_manager.keyconfigs.user

    for keymap in keyconfig.keymaps:
        for kmi in keymap.keymap_items:
            if kmi.idname == 'view3d.rotate':
                _z_kmi.append(kmi)
            if kmi.idname == 'view3d.viewnumpad':
                _z_kmi.append(kmi)
            if kmi.idname == 'view3d.view_orbit':
                _z_kmi.append(kmi)
            if kmi.idname == 'cc.view3d_rotate':
                _y_kmi.append(kmi)

@bpy.app.handlers.persistent
def on_scene_change(scene):
    global _scene
    global y_up_active

    if _scene != scene:
        if scene.y_up and not y_up_active:
            y_up_activate()
        elif not scene.y_up and y_up_active:
            y_up_deactivate()

    _scene = scene

def y_up_activate():
    global _z_kmi
    global _y_kmi
    global y_up_active

    collect_kmi()
    for kmi in _z_kmi:
        kmi.active = False
    for kmi in _y_kmi:
        kmi.active = True
    y_up_active = True

def y_up_deactivate():
    global _z_kmi
    global _y_kmi
    global y_up_active

    collect_kmi()
    for kmi in _z_kmi:
        kmi.active = True
    for kmi in _y_kmi:
        kmi.active = False
    y_up_active = False

PROP_Y_UP = bpy.props.BoolProperty(name='Y-axis is Up', update=update_y_prop)

class ViewRotate(bpy.types.Operator):
    bl_idname = 'cc.view3d_rotate'
    bl_label = 'Rotate View'
    bl_options = {'REGISTER', 'INTERNAL'}

    noninteractive = bpy.props.BoolProperty(name='Noninteractive')
    absolute = bpy.props.BoolProperty(name='Absolute')
    eulers = bpy.props.FloatVectorProperty(name='Eulers', subtype='EULER')

    def execute(self, context):
        r3d = context.space_data.region_3d

        eulers = mu.Euler(self.eulers, 'XYZ')

        if self.absolute:
            # hack to make grid appear
            smooth_view = context.user_preferences.view.smooth_view
            context.user_preferences.view.smooth_view = 0
            bpy.ops.view3d.viewnumpad(type='TOP')
            context.user_preferences.view.smooth_view = smooth_view
            r3d.view_rotation = eulers.to_quaternion()
        else:
            # hack to make grid disappear
            bpy.ops.view3d.view_roll()
            turntable = r3d.view_rotation.to_euler('XYZ')
            turntable.x += eulers.x
            turntable.y += eulers.y
            turntable.z += eulers.z
            r3d.view_rotation = turntable.to_quaternion()

        return {'FINISHED'}

    def invoke(self, context, event):
        if self.noninteractive:
            return self.execute(context)

        else:
            wm = context.window_manager
            r3d = context.space_data.region_3d

            if r3d.view_perspective == 'CAMERA':
                r3d.view_perspective = 'PERSP'

            self.mouse_last_pos = mu.Vector((event.mouse_region_x, event.mouse_region_y))
            self.turntable = r3d.view_rotation.to_euler('XYZ')
            context.window_manager.modal_handler_add(self)

            return {'RUNNING_MODAL'}

    def modal(self, context, event):
        r3d = context.space_data.region_3d

        if event.type == 'MOUSEMOVE':
            mouse_pos = mu.Vector((event.mouse_region_x, event.mouse_region_y))
            mouse_delta = mouse_pos - self.mouse_last_pos
            self.mouse_last_pos = mouse_pos
            factor = 200.0
            if event.ctrl:
                factor *= 100
            pitch = mouse_delta.y / factor
            yaw = -mouse_delta.x / factor
            self.turntable.x += pitch
            self.turntable.y += yaw

            turntable = mu.Euler((self.turntable.x, self.turntable.y, 0), 'XYZ')
            if event.alt:
                turntable.x = cc.utils.roundq(turntable.x, math.radians(5))
                turntable.y = cc.utils.roundq(turntable.y, math.radians(5))

            r3d.view_rotation = turntable.to_quaternion()
            r3d.update()

            # hack to make grid disappear
            bpy.ops.view3d.view_roll()

        if event.type in {'LEFTMOUSE', 'MIDDLEMOUSE', 'RIGHTMOUSE', 'ESC'}:
            return {'FINISHED'}

        return {'RUNNING_MODAL'}

def register():
    global _original_unit_draw
    cc.utils.register(__REGISTER__)
    _original_unit_draw = bpy.types.SCENE_PT_unit.draw
    bpy.types.SCENE_PT_unit.draw = unit_draw
    bpy.app.handlers.scene_update_post.append(on_scene_change)

def unregister():
    global _original_unit_draw
    cc.utils.unregister(__REGISTER__)
    bpy.types.SCENE_PT_unit.draw = _original_unit_draw
    bpy.app.handlers.scene_update_post.remove(on_scene_change)

__REGISTER__ = (
    ViewRotate,
    (bpy.types.Scene, 'y_up', PROP_Y_UP),
)
