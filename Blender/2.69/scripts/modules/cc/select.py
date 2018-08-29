import bpy
import bmesh
import cc

def save(obj, name, mode=(True, False, False)):
    if name not in obj.data.selections:
        sel = obj.data.selections.add()
        sel.name = name
        sel.mode = mode
    else:
        sel = obj.data.selections[name]
    sel.save(mode)
    return sel

def load(obj, name):
    if name in obj.data.selections:
        sel = obj.data.selections[name]
        sel.load()
        return sel

def delete(obj, name):
    if name in obj.data.selections:
        sel = obj.data.selections[name]
        selections = list(obj.data.selections)
        obj.data.selections.remove(selections.index(sel))

class Selection(bpy.types.PropertyGroup):
    name = bpy.props.StringProperty(name='Name')
    mode = bpy.props.BoolVectorProperty(name='Mode')

    def save(self):
        pass

    def load(self):
        pass

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
