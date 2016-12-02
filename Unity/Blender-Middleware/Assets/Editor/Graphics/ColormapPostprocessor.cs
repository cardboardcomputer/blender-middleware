using UnityEngine;
using UnityEditor;
using System;
using System.IO;

public class ColormapPostprocessor : AssetPostprocessor
{
  void OnPostprocessTexture(Texture2D texture)
  {
    TextureImporter importer = assetImporter as TextureImporter;
    string path = importer.assetPath;

    if (Application.platform == RuntimePlatform.WindowsEditor) 
        path = path.Replace("/", "\\");

    StreamReader reader = new StreamReader(path);
    string data = reader.ReadToEnd();
    reader.Close();
    int eof = data.LastIndexOf('\x1a');

    Texture tex = (Texture)AssetDatabase.LoadAssetAtPath(path, typeof(Texture));

    if (eof != -1)
      {
        string nfo = data.Substring(eof + 1);
        string[] tokens = nfo.Split('\0');
        if (tokens.Length > 0 && tokens[0] == "COLORMAP")
          {
            importer.filterMode = FilterMode.Point;
            importer.textureCompression = TextureImporterCompression.Uncompressed;

            UnityEngine.Object asset = AssetDatabase.LoadAssetAtPath(path, typeof(Texture2D));
            if (asset)
              EditorUtility.SetDirty(asset);

            int size = Int32.Parse(tokens[1]);
            int stride = Int32.Parse(tokens[2]);
            float normalizedStride = (float)stride / (float)size;

            string materialsPath =
              Directory.GetParent(Directory.GetParent(path).ToString()).ToString() +
              Path.DirectorySeparatorChar +
              "Materials";

            DirectoryInfo dir = new DirectoryInfo(materialsPath);
            if (!dir.Exists) dir = Directory.CreateDirectory(materialsPath);
            string[] dirContents = Directory.GetFiles(dir.FullName);

            foreach (string file in dirContents)
              {
                string ext = Path.GetExtension(file);
                if (ext == ".mat")
                  {
                    string assetPath = file.Substring(Application.dataPath.Length - 6);
                    Material mat = (Material)AssetDatabase.LoadAssetAtPath(assetPath, typeof(Material));

                    UnityEngine.Object[] deps = EditorUtility.CollectDependencies(new UnityEngine.Object[] { (UnityEngine.Object)mat });

                    foreach (UnityEngine.Object obj in deps)
                      {
                        if (tex && obj && tex.GetInstanceID() == obj.GetInstanceID())
                          {
                            int numProps = ShaderUtil.GetPropertyCount(mat.shader);
                            for (int i = 0; i < numProps; i++)
                              {
                                ShaderUtil.ShaderPropertyType t = ShaderUtil.GetPropertyType(mat.shader, i);
                                if (t == ShaderUtil.ShaderPropertyType.TexEnv)
                                  {
                                    string propName = ShaderUtil.GetPropertyName(mat.shader, i);
                                    Texture assignedTex = mat.GetTexture(propName);
                                    if (assignedTex == tex && mat.HasProperty("_Stride"))
                                      mat.SetFloat("_Stride", normalizedStride);
                                  }
                              }
                          }
                      }
                  }
              }
          }
      }
  }
}
