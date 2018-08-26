import bpy
import cc
import random
import math
import mathutils
from bpy_extras import view3d_utils

bl_info = {
    'name': 'Add Debris',
    'author': 'Cardboard Computer',
    'blender': (2, 6, 9),
    'description': 'Interactively place objects onto a mesh surface',
    'category': 'Cardboard'
}

PROP_SELECT = bpy.props.EnumProperty(
    items=(
        ('RANDOM', 'Random', 'Random'),
        ('LOOP', 'Loop', 'Loop'),
        ('MANUAL', 'Manual', 'Manual'),),
    name='Select', default='RANDOM')

PROP_GROUP_NAME = bpy.props.StringProperty(name='Group', default='')

PROP_OBJECT_NAME = bpy.props.StringProperty(name='Object', default='')

# monkeypatch Scene with persisted debris properties
bpy.types.Scene.debris_select = PROP_SELECT
bpy.types.Scene.debris_group_name = PROP_GROUP_NAME
bpy.types.Scene.debris_object_name = PROP_OBJECT_NAME

class DebrisPanel(bpy.types.Panel):
    bl_label = "Debris"
    bl_space_type = 'VIEW_3D'
    bl_region_type = 'TOOLS'

    def draw(self, context):
        layout = self.layout
        scene = context.scene

        layout.prop(scene, 'debris_select', '')

        col = layout.column(align=True)
        col.prop_search(scene, 'debris_group_name', bpy.data, 'groups', '')

        if scene.debris_group_name:
            data = bpy.data.groups[scene.debris_group_name]
        else:
            data = bpy.data
            col.enabled = False

        col.prop_search(scene, 'debris_object_name', data, 'objects', '')

        layout.operator('cc.add_debris')

bpy.utils.register_class(DebrisPanel)

class AddDebris(bpy.types.Operator):
    bl_idname = 'cc.add_debris'
    bl_label = 'Add Debris'
    bl_options = {'REGISTER', 'UNDO'}

    select = PROP_SELECT
    group_name = PROP_GROUP_NAME
    object_name = PROP_OBJECT_NAME

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return context.mode == 'EDIT_MESH' and obj and obj.type == 'MESH'

    def draw(self, context):
        # hiding props in update panel because tweaks here don't
        # really make sense because this tool is heavily modal and
        # props really need to be configured before invoking; see
        # DebrisPanel
        self.layout.label('(See Debris Options panel)')
        pass

    def execute(self, context):
        scene = context.scene
        scene.debris_select = self.select
        scene.debris_group_name = self.group_name
        scene.debris_object_name = self.object_name

        return {'FINISHED'}

    def setup(self, context, event):
        point, normal = self.raycast_mouse(context, event)
        self.clone = self.obj.copy()
        self.clone.name = '__Debris__'
        self.clone.show_wire = True
        self.clone.rotation_mode = 'QUATERNION'
        self.clone.select = True

        q = mathutils.Quaternion((0, 0, 1), math.radians(self.turn))

        self.clone.location = point
        self.clone.rotation_quaternion = normal.to_track_quat('Z', 'X') * q
        self.clone.scale = mathutils.Vector((1, 1, 1)) * self.scale

        scene = context.scene
        scene.objects.link(self.clone)
        scene.update()

    def cleanup(self, context, event):
        scene = context.scene
        if self.clone:
            scene.objects.unlink(self.clone)
            bpy.data.objects.remove(self.clone)
            self.clone = None

    def select_object(self, context, event, direction):
        index = list(self.group.objects.keys()).index(self.object_name)
        index += direction
        if index >= len(self.group.objects):
            index = 0
        elif index < 0:
            index = len(self.group.objects) - 1
        self.obj = self.group.objects.values()[index]
        self.object_name = self.obj.name

        self.cleanup(context, event)
        self.setup(context, event)

    def raycast_mouse(self, context, event):
        scene = context.scene
        region = context.region
        region_3d = context.space_data.region_3d
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)

        direction = view3d_utils.region_2d_to_vector_3d(region, region_3d, mouse_pos)
        endpoint = view3d_utils.region_2d_to_location_3d(region, region_3d, mouse_pos, region_3d.view_location)

        if region_3d.is_perspective:
            direction = -direction
            origin = endpoint + direction * region_3d.view_distance
            farpoint = origin + direction * 1000
        else:
            origin = endpoint + direction * region_3d.view_distance
            farpoint = origin - direction * 1000

        if self.clone:
            self.clone.hide = True

        result, obj, matrix, surface, normal = scene.ray_cast(origin, farpoint)

        if self.clone:
            self.clone.hide = False

        if result:
            endpoint = surface
        else:
            normal = mathutils.Vector((0, 0, 1))

        return (endpoint, normal)

    def invoke(self, context, event):
        scene = context.scene

        self.select = scene.debris_select
        self.group_name = scene.debris_group_name
        self.object_name = scene.debris_object_name

        self.clone = None
        self.turn = 0
        self.scale = 1

        if not self.group_name:
            self.report('ERROR', 'Please select a group in the Debris panel.')
            return {'CANCELLED'}
        self.group = bpy.data.groups[self.group_name]

        if len(self.group.objects) == 0:
            self.report('ERROR', 'Selected group has no objects.')
            return {'CANCELLED'}

        if self.select == 'RANDOM':
            self.obj = random.choice(self.group.objects)
            self.object_name = self.obj.name

        elif self.object_name:
            if self.select == 'LOOP':
                index = list(self.group.objects.keys()).index(self.object_name)
                index += 1
                if index >= len(self.group.objects):
                    index = 0
                self.obj = self.group.objects.values()[index]
                self.object_name = self.obj.name
            else: # MANUAL
                self.obj = self.group.objects[self.object_name]

        else:
            self.obj = self.group.objects.values()[0]
            self.object_name = self.obj.name

        self.setup(context, event)
        context.window_manager.modal_handler_add(self)

        return {'RUNNING_MODAL'}

    def modal(self, context, event):
        ret = 'PASS_THROUGH'

        point, normal = self.raycast_mouse(context, event)
        mouse_pos = (event.mouse_region_x, event.mouse_region_y)

        if event.type == 'WHEELUPMOUSE':
            if event.ctrl:
                self.scale *= 0.9
            elif event.shift:
                self.select_object(context, event, -1)
            else:
                self.turn += 10
            ret = 'RUNNING_MODAL'
        if event.type == 'WHEELDOWNMOUSE':
            if event.ctrl:
                self.scale *= 1.1
            elif event.shift:
                self.select_object(context, event, 1)
            else:
                self.turn -= 10
            ret = 'RUNNING_MODAL'
        q = mathutils.Quaternion((0, 0, 1), math.radians(self.turn))

        self.clone.location = point
        self.clone.rotation_quaternion = normal.to_track_quat('Z', 'X') * q
        self.clone.scale = mathutils.Vector((1, 1, 1)) * self.scale

        if event.type == 'RIGHTMOUSE' or event.type == 'ESC' and event.value == 'PRESS':
            self.cleanup(context, event)
            return {'CANCELLED'}

        if event.type == 'LEFTMOUSE':
            bpy.ops.mesh.select_all(action='DESELECT')

            for poly in self.clone.data.polygons:
                poly.select = True

            @cc.ops.editmode
            def join():
                bpy.ops.object.join()
            join()

            self.execute(context)
            return {'FINISHED'}

        return {ret}
 
def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
