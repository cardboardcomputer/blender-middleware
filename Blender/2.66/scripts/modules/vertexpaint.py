def paint(mesh, fn):
    c = mesh.vertex_colors.active.data
    for p in mesh.polygons:
        if p.select:
            for i in p.loop_indices:
                c[i].color = fn(c[i].color)
