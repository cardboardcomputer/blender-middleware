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

    LineData.Parse(data, ref mesh);
    AssetDatabase.SaveAssets();
  }
}
