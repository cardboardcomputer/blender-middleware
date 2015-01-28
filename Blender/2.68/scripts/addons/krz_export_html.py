import os
import bpy
import krz
import math
import html
import json
import bmesh
import struct
import subprocess
import mathutils as m

from krz_export_lines import (
    Color,
    Vertex,
    Edge,
    Line,
    floats_to_strings
)

bl_info = {
    'name': 'Export HTML (.html)',
    'author': 'Cardboard Computer',
    'version': (0, 1),
    'blender': (2, 6, 8),
    'location': 'File > Import-Export > HTML (.html)',
    'description': 'Export selection to HTML',
    'category': 'Cardboard'
}

THREEJS_URL = 'https://cdnjs.cloudflare.com/ajax/libs/three.js/r70/three.min.js'

def lens_to_fov(lens):
    return 2 * math.atan(16 / lens) * (180 / math.pi)

def mesh_triangulate(me):
    bm = bmesh.new()
    bm.from_mesh(me)
    bmesh.ops.triangulate(bm, faces=bm.faces)
    bm.to_mesh(me)
    bm.free()

def export_html(context, name, fp, antialias=False, scale=1.0, include_threejs=False):
    # collect scene and objects

    if context.selected_objects:
        scene = context.scene
        selected_objects = list(context.selected_objects)
    elif 'Export' in bpy.data.scenes:
        scene = bpy.data.scenes['Export']
        selected_objects = list(scene.objects)

    # disable color management (gamma correction)

    dd = scene.display_settings.display_device
    scene.display_settings.display_device = 'None'

    # aspects

    app_width = context.window_manager.windows[0].width
    app_height = context.window_manager.windows[0].height
    app_aspect = app_width / app_height

    # webgl settings

    webgl = {}
    if antialias:
        webgl['antialias'] = antialias

    # html header

    fp.write('<!DOCTYPE html>')
    fp.write('<html>')
    fp.write('<head>')
    fp.write('<title>')
    fp.write(html.escape(name))
    fp.write('</title>')
    fp.write('<meta name="viewport" content="width=device-width, initial-scale=1, minimum-scale=1, maximum-scale=1, user-scalable=no">')
    fp.write('<style type="text/css">')
    fp.write('html,body{margin:0;padding:0;overflow:hidden}body{position:relative}')
    fp.write('canvas{display:block;margin:0;padding:0;border:0;width:100% !important;height:100% !important}')
    fp.write('</style>')
    if not include_threejs:
        fp.write('<script type="text/javascript" src="%s"></script>' % THREEJS_URL)
    else:
        from urllib import request
        response = request.urlopen(THREEJS_URL)
        threejs_source = response.read().decode('utf-8')
        fp.write('<script type="text/javascript">%s</script>' % threejs_source)

    # basic unlit shaders

    fp.write('<script type="x-shader/x-fragment" id="vertex-solid">')
    fp.write('varying vec3 vColor;')
    fp.write('void main(){vColor=color;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}')
    fp.write('</script>')

    fp.write('<script type="x-shader/x-fragment" id="fragment-solid">')
    fp.write('varying vec3 vColor;')
    fp.write('void main(){gl_FragColor=vec4(vColor,1);}')
    fp.write('</script>')

    # vertex alpha shaders

    fp.write('<script type="x-shader/x-fragment" id="vertex-alpha">')
    fp.write('attribute float alpha;')
    fp.write('varying vec3 vColor;')
    fp.write('varying float vAlpha;')
    fp.write('void main(){vColor=color;vAlpha=alpha;gl_Position=projectionMatrix*modelViewMatrix*vec4(position,1.0);}')
    fp.write('</script>')

    fp.write('<script type="x-shader/x-fragment" id="fragment-alpha">')
    fp.write('varying vec3 vColor;')
    fp.write('varying float vAlpha;')
    fp.write('void main() {gl_FragColor=vec4(vColor,vAlpha);}')
    fp.write('</script>')

    fp.write('<script type="text/javascript">')

    # shortcuts

    fp.write('var T=THREE;');
    fp.write('devicePixelRatio=window.devicePixelRatio||1;');

    # collect basic scene/camera info

    viewport = None
    for area in context.screen.areas:
        if area.type == 'VIEW_3D':
            for region in area.regions:
                if region.type == 'WINDOW':
                    viewport_width = region.width
                    viewport_height = region.height
                    viewport_aspect = viewport_width / viewport_height
            viewport = area.spaces[0]

    view_lens = viewport.lens
    view_location = viewport.region_3d.view_location
    view_rotation = viewport.region_3d.view_rotation
    view_eulers = view_rotation.to_euler('XZY')
    view_distance = viewport.region_3d.view_distance
    view_perspective = viewport.region_3d.is_perspective
    view_near = viewport.clip_start
    view_far = viewport.clip_end
    if scene.world:
        background_color = scene.world.horizon_color.copy()
        # background_color.v = math.sqrt(background_color.v)
        background_color.r = math.sqrt(background_color.r)
        background_color.g = math.sqrt(background_color.g)
        background_color.b = math.sqrt(background_color.b)
    else:
        background_color = (0,0,0)
    app_scale = app_aspect / viewport_aspect

    # scene/camera/renderer globals

    fp.write('var scene=new T.Scene();')
    if view_perspective:
        fp.write('var camera=new T.PerspectiveCamera(%.6f,window.innerWidth/window.innerHeight,%.6f,%.6f);' % (lens_to_fov(view_lens) * app_scale, view_near, view_far))
    else:
        o = view_distance * (math.radians(lens_to_fov(view_lens)) / 2) * app_scale
        fp.write('var camera=new T.OrthographicCamera(-%.6f*(window.innerWidth/window.innerHeight),%.6f*(window.innerWidth/window.innerHeight),%.6f,-%.6f,%.6f,%.6f);' % (o,o,o,o,view_near,view_far))
        fp.write('camera.fov=%.6f;' % (lens_to_fov(view_lens) * app_scale))
    fp.write('var renderer=new T.WebGLRenderer(%s);' % json.dumps(webgl))
    fp.write('renderer.setSize(window.innerWidth*devicePixelRatio*%.6f,window.innerHeight*devicePixelRatio*%.6f);' % (scale, scale))
    fp.write('renderer.setClearColor(new T.Color(%.4f,%.4f,%.4f),1);' % tuple(background_color))

    fp.write('var view=new T.Object3D();')
    fp.write('scene.add(view);');
    fp.write('view.add(camera);');
    fp.write('camera.position.z=%.6f;' % view_distance)
    fp.write('view.position.x=%.6f;' % view_location.x)
    fp.write('view.position.y=%.6f;' % view_location.y)
    fp.write('view.position.z=%.6f;' % view_location.z)
    fp.write('view.rotation.order=\'ZYX\';')
    fp.write('view.setRotationFromEuler(new T.Euler(%.6f,%.6f,%.6f,\'ZYX\'));' % tuple(view_eulers))

    # objects

    fp.write('var objects={};')

    fp.write('(function(){')

    indirect = []
    objects = selected_objects

    for obj in objects:
        t = obj
        while t.parent:
            if t.parent not in indirect and t.parent not in objects:
                indirect.append(t.parent)
            t = t.parent

    for obj in indirect:
        fp.write('var o=new T.Object3D();')
        write_transform(fp, obj)

    for obj in objects:
        if obj.type != 'MESH':
            fp.write('var o=new T.Object3D();')
            write_transform(fp, obj)
            continue

        mesh = obj.to_mesh(scene=scene, apply_modifiers=True, settings='PREVIEW', calc_tessface=True)

        for k, v in obj.data.items():
            mesh[k] = v

        if (len(mesh.polygons) == 0):
            write_lines(fp, obj, mesh)
        else:
            write_triangles(fp, obj, mesh)

    for obj in indirect:
        write_hierarchy(fp, obj)
    for obj in objects:
        write_hierarchy(fp, obj)

    fp.write('})();');

    # events

    fp.write('function resize(e){')
    fp.write('renderer.setSize(window.innerWidth*devicePixelRatio*%.6f,window.innerHeight*devicePixelRatio*%.6f);' % (scale, scale))
    fp.write('camera.aspect=window.innerWidth/window.innerHeight;')
    fp.write('camera.left=-camera.top*(window.innerWidth/window.innerHeight);')
    fp.write('camera.right=camera.top*(window.innerWidth/window.innerHeight);')
    fp.write('camera.updateProjectionMatrix();')
    fp.write('}')
    fp.write('window.addEventListener(\'resize\',resize);');
    fp.write('window.addEventListener(\'orientationchange\',resize);');

    # start func

    fp.write('function start(){document.body.appendChild(renderer.domElement);}')

    # html footer

    fp.write('function render(){requestAnimationFrame(render);renderer.render(scene,camera);}');
    fp.write('</script>')

    # custom html footer

    for text_name in bpy.data.texts.keys():
        if text_name.lower() == 'html':
            for line in bpy.data.texts[text_name].lines:
                if line.body.startswith('#include'):
                    path = line.body.lstrip('#include ').strip()
                    if path in bpy.data.texts:
                        fp.write(bpy.data.texts[path].as_string())
                    else:
                        path = os.path.realpath(os.path.expanduser(path))
                        if os.path.exists(path):
                            with open(path) as i:
                                fp.write(i.read())
                if line.body.startswith('#include-js'):
                    path = line.body[len('#include-js'):].strip()
                    if path.endswith('.js'):
                        if path in bpy.data.texts:
                            js = get_minified_js_source(bpy.data.texts[path].as_string())
                        else:
                            path = os.path.realpath(os.path.expanduser(path))
                            js = get_minified_js(path)
                        fp.write('<script type="text/javascript">%s</script>' % js)
                else:
                    fp.write(line.body + '\n')

    fp.write('</head>')
    fp.write('<body>')
    fp.write('<script type="text/javascript">start();render();</script>')
    fp.write('</body>')
    fp.write('</html>')

    # restore color management (gamma correction)

    scene.display_settings.display_device = dd

def shader_constructor(name, include='', alpha=False, additive=False):
    extra = ''
    if alpha:
        extra = (
            'transparent:true,'
            'depthWrite:false,'
            'blending:T.NormalBlending,'
        )
    if additive:
        extra = (
            'transparent:true,'
            'depthWrite:false,'
            'blending:T.AdditiveBlending,'
        )
    if include and not include.endswith(','):
        include += ','
    return (
        'new T.ShaderMaterial({'
        '%(extra)s'
        '%(include)s'
        'vertexColors:T.VertexColors,'
        'vertexShader:document.getElementById("vertex-%(name)s").textContent,'
        'fragmentShader:document.getElementById("fragment-%(name)s").textContent'
        '})') % {'name': name, 'extra': extra, 'include': include}

def write_transform(fp, obj):
    fp.write('objects[\'%s\']=o;' % obj.name)
    fp.write('o.position.set(%s);' % ','.join(floats_to_strings(obj.location)))
    if obj.rotation_mode == 'QUATERNION':
        fp.write('o.setRotationFromQuaternion(new T.Quaternion(%s));' % ','.join(floats_to_strings((
                    obj.rotation_quaternion.x, obj.rotation_quaternion.y,
                    obj.rotation_quaternion.z, obj.rotation_quaternion.w))))
    else:
        fp.write('o.setRotationFromEuler(new T.Euler(%s,\'%s\'));' % (
                ','.join(floats_to_strings(obj.rotation_euler)), obj.rotation_mode))
    fp.write('o.up.set(0,0,1);')
    fp.write('o.scale.set(%s);' % ','.join(floats_to_strings(obj.scale)))

def write_hierarchy(fp, obj):
    if obj.parent:
        fp.write('objects[\'%s\'].add(objects[\'%s\']);' % (obj.parent.name, obj.name))
    else:
        fp.write('scene.add(objects[\'%s\']);' % obj.name)

def write_triangles(fp, obj, mesh):
    mesh_triangulate(mesh)

    fp.write('var g=new T.BufferGeometry();')

    # shader kwargs

    shader_name = 'solid'
    shader_kwargs = {}

    # vertex array (non-indexed)

    verts = []
    for i, poly in enumerate(mesh.polygons):
        for idx, ptr in enumerate(poly.vertices):
            # p = obj.matrix_world * mesh.vertices[ptr].co
            # verts += list(p)
            verts += list(mesh.vertices[ptr].co)
    fp.write('var v=new Float32Array([')
    fp.write(','.join(floats_to_strings(verts)))
    fp.write(']);')
    fp.write('g.addAttribute(\'position\',new T.BufferAttribute(v,3));');

    # color array

    layer = None
    for vc in mesh.vertex_colors:
        if vc.active_render:
            layer = vc

    colors = []
    for i, p in enumerate(mesh.polygons):
        for x in p.loop_indices:
            if layer:
                colors += list(layer.data[x].color)
            else:
                colors += [0, 0, 0]
    fp.write('var k=new Float32Array([')
    fp.write(','.join(floats_to_strings(colors)))
    fp.write(']);')
    fp.write('g.addAttribute(\'color\',new T.BufferAttribute(k,3));');

    # alpha attribute
    alpha_colors = None
    if layer:
        alpha_name = '%s.Alpha' % layer.name
        if alpha_name in mesh.vertex_colors:
            alpha_colors = mesh.vertex_colors[alpha_name]
    if not alpha_colors:
        if '_Alpha' in mesh.vertex_colors:
            alpha_colors = mesh.vertex_colors['_Alpha']
        elif 'Alpha' in mesh.vertex_colors:
            alpha_colors = mesh.vertex_colors['Alpha']
    if alpha_colors:
        alpha = []
        data = alpha_colors.data
        for i, p in enumerate(mesh.polygons):
            for x in p.loop_indices:
                alpha.append(data[x].color.v)
        fp.write('var a=new Float32Array([')
        fp.write(','.join(floats_to_strings(alpha)))
        fp.write(']);')
        fp.write('g.addAttribute(\'alpha\',new T.BufferAttribute(a,1));');
        shader_name = 'alpha'
        shader_kwargs['alpha'] = True
        shader_kwargs['include'] = 'attributes:{alpha:{type:\'f\',value:[]}}'

    if layer and layer.name in ('Add', '_Add', 'Additive', '_Additive'):
        shader_kwargs['alpha'] = False
        shader_kwargs['additive'] = True

    fp.write('var o=new T.Mesh(g,%s);' % shader_constructor(shader_name, **shader_kwargs))
    write_transform(fp, obj)

def write_lines(fp, obj, mesh):
    vertices = []
    edges = []
    lines = []

    fp.write('var g=new T.BufferGeometry();')

    # shader kwargs

    shader_name = 'solid'
    shader_kwargs = {}

    # vertices

    layer = krz.colors.Manager(obj).get_export_layer()
    transparent = False
    if not layer:
        for i, v in enumerate(mesh.vertices):
            color = Color(1, 1, 1, 1)
            vertices.append(Vertex(i, v.co, color, v.normal))
    else:
        for s in layer.itersamples():
            if s.alpha < 1:
                transparent = True
            color = Color(s.color.r, s.color.g, s.color.b, s.alpha)
            vertices.append(Vertex(s.vertex.index, s.vertex.co, color, s.vertex.normal))

    for edge in mesh.edges:
        a = vertices[edge.vertices[0]]
        b = vertices[edge.vertices[1]]
        edges.append(Edge(a, b))

    verts = []
    for edge in edges:
        # verts += list(obj.matrix_world * edge.a.co)
        # verts += list(obj.matrix_world * edge.b.co)
        verts += list(edge.a.co)
        verts += list(edge.b.co)
    fp.write('var v=new Float32Array([')
    fp.write(','.join(floats_to_strings(verts)))
    fp.write(']);')
    fp.write('g.addAttribute(\'position\',new T.BufferAttribute(v,3));');

    # colors

    colors = []
    for edge in edges:
        colors += list(edge.a.color)[:3]
        colors += list(edge.b.color)[:3]
    fp.write('var k=new Float32Array([')
    fp.write(','.join(floats_to_strings(colors)))
    fp.write(']);')
    fp.write('g.addAttribute(\'color\',new T.BufferAttribute(k,3));');

    if transparent:
        alpha = []
        for edge in edges:
            alpha.append(list(edge.a.color)[3])
            alpha.append(list(edge.b.color)[3])
        fp.write('var a=new Float32Array([')
        fp.write(','.join(floats_to_strings(alpha)))
        fp.write(']);')
        fp.write('g.addAttribute(\'alpha\',new T.BufferAttribute(a,1));');
        shader_name = 'alpha'
        shader_kwargs['alpha'] = True
        shader_kwargs['include'] = 'attributes:{alpha:{type:\'f\',value:[]}}'

    if layer and layer.name in ('Add', '_Add', 'Additive', '_Additive'):
        shader_kwargs['alpha'] = False
        shader_kwargs['additive'] = True

    fp.write('var o=new T.Line(g,%s,T.LinePieces);' % shader_constructor(shader_name, **shader_kwargs))
    write_transform(fp, obj)

def get_minified_js(path):
    temp = path + '.min'
    with open(path) as i:
        with open(temp, 'w') as o:
            p = subprocess.Popen(['jsmin'], stdin=i, stdout=o)
            p.wait()
    with open(temp) as fp:
        source = fp.read()
    os.remove(temp)
    return source

def get_minified_js_source(source):
    import tempfile
    src = open(tempfile.mktemp(), 'w')
    src_path = src.name
    src.write(source)
    src.close()
    src = open(src_path, 'r')
    dst = open(tempfile.mktemp(), 'w')
    dst_path = dst.name
    p = subprocess.Popen(['jsmin'], stdin=src, stdout=dst)
    p.wait()
    src.close()
    dst.close()
    dst = open(dst_path, 'r')
    source = dst.read()
    dst.close()
    os.remove(src_path)
    os.remove(dst_path)
    return source

class HtmlExporter(bpy.types.Operator):
    bl_idname = 'cc.export_html'
    bl_label = 'Export HTML'

    filepath = bpy.props.StringProperty(
        subtype='FILE_PATH',)

    check_existing = bpy.props.BoolProperty(
        name="Check Existing",
        description="Check and warn on overwriting existing files",
        default=True,
        options={'HIDDEN'},)

    include_threejs = bpy.props.BoolProperty(
        name="Include three.js",
        description="Include three.js source in html",
        default=False,)

    precision = bpy.props.IntProperty(
        name="Precision",
        description="Enable antialiasing for WebGL renderer",
        default=6,)

    antialias = bpy.props.BoolProperty(
        name="Antialias",
        description="Enable antialiasing for WebGL renderer",
        default=False,)

    scale = bpy.props.FloatProperty(
        name="Resolution Scale",
        description="Downscale canvas by this factor",
        default=1.0,)

    def execute(self, context):
        with open(self.filepath, 'w') as fp:
            name = os.path.basename(self.filepath[:-len('.html')])
            export_html(context, name, fp, antialias=self.antialias, scale=self.scale, include_threejs=self.include_threejs)
            fp.flush()
        return {'FINISHED'}

    def invoke(self, context, event):
        if not self.filepath:
            self.filepath = bpy.path.ensure_ext(bpy.data.filepath, ".html")
        wm = context.window_manager
        wm.fileselect_add(self)
        return {'RUNNING_MODAL'}

def menu_export(self, context):
    self.layout.operator(HtmlExporter.bl_idname, text="HTML (.html)")

def register():
    bpy.utils.register_module(__name__)

    bpy.types.INFO_MT_file_export.append(menu_export)

def unregister():
    bpy.utils.unregister_module(__name__)

    bpy.types.INFO_MT_file_export.remove(menu_export)

if __name__ == "__main__":
    register()
