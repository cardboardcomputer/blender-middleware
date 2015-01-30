import bpy
import krz
import mathutils
from bpy_extras import view3d_utils
import krz_set_colors

bl_info = {
    'name': 'Sample Color',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'View3D > Specials > Sample Color',
    'description': 'Hand-sample color on lines and polygons',
    'category': 'Cardboard'
}

def find(context, event, ray_max=1000.0):
    scene = context.scene
    region = context.region
    rv3d = context.region_data
    coord = event.mouse_region_x, event.mouse_region_y

    view_vector = view3d_utils.region_2d_to_vector_3d(region, rv3d, coord)
    ray_origin = view3d_utils.region_2d_to_origin_3d(region, rv3d, coord)

    # https://developer.blender.org/rB61baf6e8135d11bc53cbfa45c75f910a99e57971
    if rv3d.view_perspective == 'ORTHO':
        view_vector = -view_vector
        ray_origin = ray_origin - (view_vector * (ray_max / 2.0))
    else:
        view_vector = view_vector.normalized()

    ray_target = ray_origin + (view_vector * ray_max)

    def visible_objects_and_duplis():
        """Loop over (object, matrix) pairs (mesh only)"""

        for obj in context.visible_objects:
            if obj.type == 'MESH':
                yield (obj, obj.matrix_world.copy())

        if obj.dupli_type != 'NONE':
            obj.dupli_list_create(scene)
            for dob in obj.dupli_list:
                obj_dupli = dob.object
                if obj_dupli.type == 'MESH':
                    yield (obj_dupli, dob.matrix.copy())

            obj.dupli_list_clear()

    # cast rays and find the closest object
    best_length_squared = ray_max * ray_max
    best_obj = best_point = best_normal = best_face = None
    best_ray_origin = best_ray_target = None

    for obj, matrix in visible_objects_and_duplis():
        if obj.type == 'MESH' and len(obj.data.polygons):
            matrix_inv = obj.matrix_world.inverted()
            ray_origin_obj = matrix_inv * ray_origin
            ray_target_obj = matrix_inv * ray_target
            hit, normal, face_index = obj.ray_cast(ray_origin_obj, ray_target_obj)
            if face_index != -1:
                length_squared = (hit - ray_origin).length_squared
                if length_squared < best_length_squared:
                    best_length_squared = length_squared
                    best_obj = obj
                    best_point = hit
                    best_normal = normal
                    best_face = face_index
                    best_ray_origin = ray_origin_obj
                    best_ray_target = ray_target_obj

    if best_obj is not None:
        return best_obj, best_ray_origin, best_ray_target

@krz.ops.editmode
def sample_color(context, event, ray_max=1000.0):
    result = find(context, event, 10000)
    if result is not None:
        obj, origin, target = result
        if obj.data.vertex_colors.active:
            with krz.colors.Sampler(obj) as sampler:
                return  sampler.raycast(origin, target)
    return mathutils.Color((0, 0, 0))

class SampleColor(bpy.types.Operator):
    bl_idname = 'cc.sample_color'
    bl_label = 'Sample Color'
    bl_options = {'REGISTER', 'UNDO'}

    def update_color(self, context):
        self.hex_value = krz.colors.color_to_hex(self.color)

    ref = bpy.props.FloatVectorProperty(
        name="Color", subtype='COLOR_GAMMA',
        min=0, max=1, step=1)
    color = bpy.props.FloatVectorProperty(
        name="Color", subtype='COLOR_GAMMA',
        min=0, max=1, step=1, update=update_color)
    hex_value = bpy.props.StringProperty(
        name="Hex", default='')

    @classmethod
    def poll(cls, context):
        obj = context.active_object
        return obj and obj.type == 'MESH'

    def invoke(self, context, event):
        self.color = self.ref = sample_color(context, event)

        wm = context.window_manager
        wm.invoke_props_dialog(self, width=140)

        return {'RUNNING_MODAL'}

    def execute(self, context):
        if context.mode == 'EDIT_MESH':
            obj = context.object
            if obj.type == 'MESH':
                vertex, edge, face = context.tool_settings.mesh_select_mode
                select = 'VERTEX'
                if face and not vertex:
                    select = 'POLYGON'
                krz_set_colors.set_colors(obj, self.color, None, select=select)
                return {'FINISHED'}
    
        elif context.mode == 'PAINT_VERTEX':
            context.tool_settings.vertex_paint.brush.color = self.color

        return {'CANCELLED'}

    def draw(self, context):
        layout = self.layout
        layout.template_color_picker(self, 'color', True)

        row = layout.row(align=True)
        r = row.column(align=True)
        r.enabled = False
        r.prop(self, 'ref', '')
        row.prop(self, 'color', '')

        layout.prop(self, 'hex_value', '')

def register():
    bpy.utils.register_module(__name__)

def unregister():
    bpy.utils.unregister_module(__name__)

if __name__ == "__main__":
    register()
