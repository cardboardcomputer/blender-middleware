import os
import re
import bpy
import json

bl_info = {
    'name': 'Export: Unity Events (.events)',
    'author': 'Cardboard Computer',
    'blender': (2, 6, 9),
    'description': 'Export timeline markers as Unity events',
    'category': 'Cardboard',
}

def export_unity_events(scene, filepath):
    events = []

    for e in scene.timeline_markers:
        kwargs = parse_marker(e)
        events.append(kwargs)

    with open(filepath, 'w') as fp:
        fp.write(json.dumps({'events': events}, indent=4))

def get_export_scene():
    scene = None

    if 'Export' in bpy.data.scenes:
        scene = bpy.data.scenes['Export']
    elif '_Export' in bpy.data.scenes:
        scene = bpy.data.scenes['_Export']
    else:
        scene = bpy.context.scene

    return scene

def parse_marker(marker):
    kwargs = {}

    # func, float, int, string, object

    kwargs['frame'] = marker.frame
    kwargs['label'] = marker.name

    match = re.match('^(\w+)\(?([^\)]*)\)?', marker.name)
    func, arg = match.groups()

    kwargs['function'] = func
    kwargs['integerValue'] = 0
    kwargs['floatValue'] = 0.0
    kwargs['stringValue'] = ''
    kwargs['objectValue'] = None

    if arg.startswith('i:'):
        kwargs['integerValue'] = int(arg[2:])
    elif arg.startswith('f:'):
        kwargs['floatValue'] = float(arg[2:])
    elif arg.startswith('s:'):
        kwargs['stringValue'] = arg[2:]
    elif arg.startswith('o:'):
        kwargs['floatValue'] = arg[2:]
    else:
        kwargs['stringValue'] = arg

    return kwargs

class UnityEventExporter(bpy.types.Operator):
    bl_idname = 'cc.export_unity_events'
    bl_label = 'Export Unity Events'

    filepath = bpy.props.StringProperty(
        subtype='FILE_PATH',)
    check_existing = bpy.props.BoolProperty(
        name="Check Existing",
        description="Check and warn on overwriting existing files",
        default=True,
        options={'HIDDEN'},)
    
    @classmethod
    def poll(cls, context):
        return True;

    def execute(self, context):
        export_unity_events(get_export_scene(), self.filepath)
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = bpy.path.ensure_ext(bpy.data.filepath, ".events")

        path = os.path.dirname(self.filepath)
        name = os.path.splitext(os.path.basename(bpy.data.filepath))[0]
        filename = '%s.events' % name
        self.filepath = os.path.join(path, filename)

        wm = context.window_manager
        wm.fileselect_add(self)

        return {'RUNNING_MODAL'}

def menu_import(self, context):
    self.layout.operator(UnityEventExporter.bl_idname, text="Unity Events (.events)")

def menu_export(self, context):
    self.layout.operator(UnityEventExporter.bl_idname, text="Unity Events (.events)")

def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_import.append(menu_import)
    bpy.types.INFO_MT_file_export.append(menu_export)

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_import.remove(menu_import)
    bpy.types.INFO_MT_file_export.remove(menu_export)

if __name__ == "__main__":
    register()
