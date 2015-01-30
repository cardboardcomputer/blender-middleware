class Color:
    def __init__(self, r, g, b, a):
        self.r = r
        self.g = g
        self.b = b
        self.a = a

    def __eq__(self, other):
        return (self.r, self.g, self.b, self.a) == other

    def __iter__(self):
        return iter((self.r, self.g, self.b, self.a))

class Vertex:
    def __init__(self, index, co, color, normal):
        self.index = index
        self.co = co
        self.color = color
        self.normal = normal

class Edge:
    def __init__(self, a, b):
        self.a = a
        self.b = b

class Line:
    def __init__(self, edge):
        self.vertices = [edge.a, edge.b]

    def is_connected(self, edge):
        head = self.vertices[0]
        tail = self.vertices[-1]
        return (head == edge.a or head == edge.b or
                tail == edge.a or tail == edge.b)

    def extend(self, edge):
        if self.is_connected(edge):
            a, b = edge.a, edge.b
            head = self.vertices[0]
            tail = self.vertices[-1]
            if a == head:
                self.vertices.insert(0, b)
            elif b == head:
                self.vertices.insert(0, a)
            elif a == tail:
                self.vertices.append(b)
            else:
                self.vertices.append(a)
            return True
        else:
            return False

    def consume(self, edges):
        consumed = -1
        remaining = list(edges)
        while consumed:
            consumed = 0
            for edge in list(remaining):
                if self.extend(edge):
                    consumed += 1
                    remaining.remove(edge)
        return remaining

def floats_to_strings(floats, precision=6):
    fmt = '%%.%if' % precision
    ret = map(lambda f: (fmt % f).rstrip('0').rstrip('.'), floats)
    ret = map(lambda s: '0' if s == '-0' else s, ret)
    return ret
