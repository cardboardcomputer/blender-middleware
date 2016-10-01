using UnityEngine;
using UnityEditor;
using System.IO;

public class LinesPostprocessor : AssetPostprocessor
{
  private static void OnPostprocessAllAssets(
    string[] importedAssets,
    string[] deletedAssets,
    string[] movedAssets,
    string[] movedFromPath)
  {
    foreach (string path in importedAssets)
      {
        if (path.EndsWith(".lines"))
          ProcessLineAsset(path);
      }
  }

  private static void ProcessLineAsset(string path)
  {
    int size;
    int[] indices;
    string[] buffer;
    Vector3[] vertices;
    Vector3[] normals;
    Color[] colors;
    Vector2[] uv;
    Mesh mesh;

    StreamReader reader = new StreamReader(path);
    string data = reader.ReadToEnd();
    reader.Close();

    string assetPath = path.Replace(".lines", ".asset");
    string[] bits = assetPath.Replace(".asset", "").Split('/');
    string name = bits[bits.Length - 1];
    
    mesh = (Mesh)AssetDatabase.LoadAssetAtPath(assetPath, typeof(Mesh));
    if (!mesh)
      {
        mesh = new Mesh();
        mesh.name = name;
        AssetDatabase.CreateAsset(mesh, assetPath);
      }
    else
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
            uv[i] = ColorUtils.Color2UV(new Color(
              float.Parse(buffer[i * 4]),
              float.Parse(buffer[i * 4 + 1]),
              float.Parse(buffer[i * 4 + 2]),
              float.Parse(buffer[i * 4 + 3])));
          }
        mesh.uv2 = uv;
      }

    AssetDatabase.SaveAssets();
  }
}
