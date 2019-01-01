/*

  For use in conjunction with MeshFilter, this script will install
  additional vertex/edge data provided in lineData into the mesh held
  by the MeshFilter component, getting the best of both worlds, line
  colors and edges and bone weights all in one, etc.

  * Make sure 'optimize mesh' is disabled on the mesh import settings so
    loose vertices aren't culled during import.

  * Assuming vertex indices are the same in the fbx imported mesh and
    the line postprocessor importer.

  TODO: make an editor tool to do this before runtime.

 */

using UnityEngine;

public class LineFilter : MonoBehaviour
{
  public Mesh lineData;

  protected MeshFilter meshFilter;
  protected SkinnedMeshRenderer skinRenderer;

  public void Awake()
  {
    meshFilter = GetComponent<MeshFilter>();
    skinRenderer = GetComponent<SkinnedMeshRenderer>();

    Apply();
  }

  public void Apply()
  {
    Mesh src = new Mesh();
    if (meshFilter != null)
      src = meshFilter.sharedMesh;
    else if (skinRenderer != null)
      src = skinRenderer.sharedMesh;

    if (src != null && lineData != null)
      {
        Mesh dst = new Mesh();

        /* data from imported mesh */
        dst.vertices = src.vertices;
        dst.bindposes = src.bindposes;
        dst.boneWeights = src.boneWeights;

        /* data from imported line */
        dst.uv = lineData.uv;
        dst.uv2 = lineData.uv2;
        dst.normals = lineData.normals;
        dst.colors = lineData.colors;
        dst.SetIndices(lineData.GetIndices(0), MeshTopology.Lines, 0);

        if (meshFilter != null)
          meshFilter.mesh = dst;
        else if (skinRenderer != null)
          skinRenderer.sharedMesh = dst;
      }
  }
}
