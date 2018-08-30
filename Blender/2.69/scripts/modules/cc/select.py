import bpy
import bmesh
import cc

BASENAME = 'Sel'

def new(obj, name):
    sel = obj.data.selections.add()
    sel.name = get_unique_name(obj.data, name)
    sel.id = get_unique_id(obj.data)
    return sel

def save(obj, name):
    if name not in obj.data.selections:
        sel = new(obj.data, name)
    else:
        sel = obj.data.selections[name]
    sel.save()
    return sel

def load(obj, name):
    if name in obj.data.selections:
        sel = obj.data.selections[name]
        sel.load()
        return sel

def clear(obj, name):
    if name in obj.data.selections:
        sel = obj.data.selections[name]
        sel.clear()
        return sel

def delete(obj, name):
    if name in obj.data.selections:
        sel = obj.data.selections[name]
        selections = list(obj.data.selections)
        obj.data.selections.remove(selections.index(sel))

def get_unique_name(data, name):
    if name in data.selections:
        count = 1
        while True:
            n = '%s.%03d' % (name, count)
            if n in data.selections:
                count += 1
                continue
            else:
                name = n
                break
    return name

def get_unique_id(data):
    used = [sel.id for sel in data.selections]
    num = 0
    while True:
        if num in used:
            num += 1
            continue
        else:
            break
    return num

def check_unique_name(self, context):
    name = self.name
    data = self.id_data

    if '__sel_renaming__' in data:
        return

    names = [sel.name for sel in data.selections if sel != self]

    if name in names:
        data['__sel_renaming__'] = True
        count = 1
        while True:
            n = '%s.%03d' % (name, count)
            if n in names:
                count += 1
                continue
            else:
                name = n
                break
        self.name = name
        del data['__sel_renaming__']

class Selection(bpy.types.PropertyGroup):
    id = bpy.props.IntProperty()
    name = bpy.props.StringProperty(name='Name', update=check_unique_name)
    mode = bpy.props.BoolVectorProperty(name='Mode')

    def save(self):
        data = self.id_data

        self.mode = list(bpy.context.tool_settings.mesh_select_mode)

        with cc.utils.Bmesh(data) as bm:
            v, e, f = self._get_or_create_layers(bm)

            for vert in bm.verts:
                if vert.select:
                    vert[v] = 1
                else:
                    vert[v] = 0
            for edge in bm.edges:
                if edge.select:
                    edge[e] = 1
                else:
                    edge[e] = 0
            for face in bm.faces:
                if face.select:
                    face[f] = 1
                else:
                    face[f] = 0

    def load(self):
        data = self.id_data

        if self.mode == (False, False, False):
            return

        bpy.context.tool_settings.mesh_select_mode = self.mode

        with cc.utils.Bmesh(data) as bm:
            for vert in bm.verts:
                vert.select = False
            for edge in bm.edges:
                edge.select = False
            for face in bm.faces:
                face.select = False

            v, e, f = self._get_or_create_layers(bm)

            if self.mode[0]:
                for vert in bm.verts:
                    if vert[v]:
                        vert.select = True
            if self.mode[1]:
                for edge in bm.edges:
                    if edge[e]:
                        edge.select = True
            if self.mode[2]:
                for face in bm.faces:
                    if face[f]:
                        face.select = True

    def clear(self):
        data = self.id_data
        self.mode = (False, False, False)
        with cc.utils.Bmesh(data) as bm:
            v, e, f = self._get_or_create_layers(bm)
            for vert in bm.verts:
                vert[v] = 0
            for edge in bm.edges:
                edge[e] = 0
            for face in bm.faces:
                face[f] = 0

    def free(self):
        data = self.id_data
        with cc.utils.Bmesh(data) as bm:
            self._delete_layers(bm)

    def _get_or_create_layers(self, bm):
        vert_name = 'sel_vert_%s' % self.id
        edge_name = 'sel_edge_%s' % self.id
        face_name = 'sel_face_%s' % self.id

        if vert_name not in bm.verts.layers.int:
            vert_layer = bm.verts.layers.int.new(vert_name)
        else:
            vert_layer = bm.verts.layers.int[vert_name]

        if edge_name not in bm.edges.layers.int:
            edge_layer = bm.edges.layers.int.new(edge_name)
        else:
            edge_layer = bm.edges.layers.int[edge_name]

        if face_name not in bm.faces.layers.int:
            face_layer = bm.faces.layers.int.new(face_name)
        else:
            face_layer = bm.faces.layers.int[face_name]

        return (vert_layer, edge_layer, face_layer)

    def _delete_layers(self, bm):
        vert_name = 'sel_vert_%s' % self.id
        edge_name = 'sel_edge_%s' % self.id
        face_name = 'sel_face_%s' % self.id

        if vert_name in bm.verts.layers.int:
            vert_layer = bm.verts.layers.int[vert_name]
            bm.verts.layers.int.remove(vert_layer)

        if edge_name in bm.edges.layers.int:
            edge_layer = bm.edges.layers.int[edge_name]
            bm.edges.layers.int.remove(edge_layer)

        if face_name in bm.faces.layers.int:
            face_layer = bm.faces.layers.int[face_name]
            bm.faces.layers.int.remove(face_layer)

def _get_active_selection(self):
    selections = list(self.selections)
    if not selections:
        return None
    if self.active_selection_index > len(selections) - 1:
        return None
    return selections[self.active_selection_index]

def _set_active_selection(self, value):
    selections = list(self.selections)
    self.active_selection_index = selections.index(value)

bpy.utils.register_class(Selection)
bpy.types.Mesh.selections = bpy.props.CollectionProperty(type=Selection)
bpy.types.Mesh.active_selection = property(_get_active_selection, _set_active_selection)
bpy.types.Mesh.active_selection_index = bpy.props.IntProperty()
