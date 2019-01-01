using UnityEngine;

public class LineData
{
  static public void Parse(string data, ref Mesh mesh)
  {
    int size;
    int[] indices;
    string[] buffer;
    Vector3[] vertices;
    Vector3[] normals;
    Color[] colors;
    Vector2[] uv;

    mesh.Clear();

    string[] lines = data.Split('\n');

    /* vertices */
    buffer = lines[0].Split(' ');
    size = buffer.Length / 3;
    vertices = new Vector3[size];
    for (int i = 0; i < size; i++)
      {
        vertices[i] = new Vector3(
          float.Parse(buffer[i * 3]),
          float.Parse(buffer[i * 3 + 1]),
          float.Parse(buffer[i * 3 + 2]));
      }
    mesh.vertices = vertices;

    /* colors */
    buffer = lines[1].Split(' ');
    size = buffer.Length / 4;
    colors = new Color[size];
    for (int i = 0; i < size; i++)
      {
        colors[i] = new Color(
          float.Parse(buffer[i * 4]),
          float.Parse(buffer[i * 4 + 1]),
          float.Parse(buffer[i * 4 + 2]),
          float.Parse(buffer[i * 4 + 3]));
      }
    mesh.colors = colors;

    /* uvs */
    buffer = lines[2].Split(' ');
    size = buffer.Length / 2;
    uv = new Vector2[size];
    for (int i = 0; i < size; i++)
      {
        uv[i] = new Vector2(
          float.Parse(buffer[i * 2]),
          float.Parse(buffer[i * 2 + 1]));
      }
    mesh.uv = uv;

    /* normals */
    normals = new Vector3[size];
    if (lines.Length >= 5)
      {
        buffer = lines[4].Split(' ');
        for (int i = 0; i < size; i++)
          {
            normals[i] = new Vector3(
              float.Parse(buffer[i * 3]),
              float.Parse(buffer[i * 3 + 1]),
              float.Parse(buffer[i * 3 + 2]));
          }
      }
    mesh.normals = normals;

    /* indices */
    buffer = lines[3].Split(' ');
    indices = new int[buffer.Length];
    for (int i = 0; i < buffer.Length; i++)
      indices[i] = int.Parse(buffer[i]);
    mesh.SetIndices(indices, MeshTopology.Lines, 0);

    /* aux colors */
    if (lines.Length == 6)
      {
        buffer = lines[5].Split(' ');
        size = buffer.Length / 4;
        uv = new Vector2[size];
        for (int i = 0; i < size; i++)
          {
            uv[i] = Color2UV(new Color(
              float.Parse(buffer[i * 4]),
              float.Parse(buffer[i * 4 + 1]),
              float.Parse(buffer[i * 4 + 2]),
              float.Parse(buffer[i * 4 + 3])));
          }
        mesh.uv2 = uv;
      }
  }

  static public Vector2 Color2UV(Color c)
  {
    int precision = 4096;
    int p = precision - 1;

    float r, g, b, a, u, v;

    r = Mathf.Floor(c.r * p);
    g = Mathf.Floor(c.g * p);
    b = Mathf.Floor(c.b * p);
    a = Mathf.Floor(c.a * p);

    u = (r * precision) + g;
    v = (b * precision) + a;

    return new Vector2(u, v);
  }
}
