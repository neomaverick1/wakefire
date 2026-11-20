// Gathers the rigged models, their clips, the loose gear meshes and their textures into
// Resources/Models/Library.asset. Run by every build, or by hand:
//   Unity -batchmode -quit -projectPath . -executeMethod Wakefire.EditorTools.Models.Build
using System.IO;
using System.Linq;
using UnityEditor;
using UnityEngine;

namespace Wakefire.EditorTools
{
    public static class Models
    {
        const string Dir = "Assets/Wakefire/Models";
        const string Out = "Assets/Wakefire/Resources/Models/Library.asset";

        [MenuItem("Wakefire/Build model library")]
        public static void Build()
        {
            if (!Directory.Exists(Dir)) return;
            Directory.CreateDirectory("Assets/Wakefire/Resources/Models");
            var lib = AssetDatabase.LoadAssetAtPath<ModelLibrary>(Out);
            if (!lib)
            {
                lib = ScriptableObject.CreateInstance<ModelLibrary>();
                AssetDatabase.CreateAsset(lib, Out);
            }
            lib.models.Clear();
            lib.clips.Clear();
            lib.meshes.Clear();
            lib.textures.Clear();
            foreach (var guid in AssetDatabase.FindAssets("t:Model", new[] { Dir }).Distinct())
            {
                string path = AssetDatabase.GUIDToAssetPath(guid);
                string name = Path.GetFileNameWithoutExtension(path);
                var all = AssetDatabase.LoadAllAssetsAtPath(path);
                if (path.Contains("/Gear/"))
                {
                    foreach (var o in all) if (o is Mesh mesh) lib.meshes.Add(mesh);
                    continue;
                }
                lib.models.Add(new ModelLibrary.Model { name = name, prefab = AssetDatabase.LoadAssetAtPath<GameObject>(path) });
                foreach (var o in all)
                    if (o is AnimationClip c && !c.name.StartsWith("__preview__")) lib.clips.Add(c);
            }
            foreach (var guid in AssetDatabase.FindAssets("t:Texture2D", new[] { Dir }).Distinct())
                lib.textures.Add(AssetDatabase.LoadAssetAtPath<Texture2D>(AssetDatabase.GUIDToAssetPath(guid)));

            const string matPath = "Assets/Wakefire/Resources/Materials/Model.mat";
            var shader = Shader.Find("Wakefire/Model");
            var mat = AssetDatabase.LoadAssetAtPath<Material>(matPath);
            if (!mat && shader)
            {
                mat = new Material(shader) { name = "Model" };
                AssetDatabase.CreateAsset(mat, matPath);
            }
            if (mat && shader) mat.shader = shader;
            lib.material = mat;
            const string shadePath = "Assets/Wakefire/Resources/Materials/Shade.mat";
            var shadeShader = Shader.Find("Wakefire/Shade");
            var shade = AssetDatabase.LoadAssetAtPath<Material>(shadePath);
            if (!shade && shadeShader)
            {
                shade = new Material(shadeShader) { name = "Shade" };
                AssetDatabase.CreateAsset(shade, shadePath);
            }
            if (shade && shadeShader) shade.shader = shadeShader;
            const string emberPath = "Assets/Wakefire/Resources/Materials/Ember.mat";
            var emberShader = Shader.Find("Hidden/Wakefire/Ember");
            var ember = AssetDatabase.LoadAssetAtPath<Material>(emberPath);
            if (!ember && emberShader)
            {
                ember = new Material(emberShader) { name = "Ember" };
                AssetDatabase.CreateAsset(ember, emberPath);
            }
            if (ember && emberShader) ember.shader = emberShader;
            // always in the same order, so the asset doesn't change from one build to the next
            lib.clips.Sort((a, b) => string.CompareOrdinal(a.name, b.name));
            lib.meshes.Sort((a, b) => string.CompareOrdinal(a.name, b.name));
            lib.textures.Sort((a, b) => string.CompareOrdinal(a.name, b.name));
            EditorUtility.SetDirty(lib);
            AssetDatabase.SaveAssets();
            Debug.Log($"[import] models: {string.Join(", ", lib.models.Select(m => m.name))}; {lib.clips.Count} clips; {lib.meshes.Count} gear meshes; {lib.textures.Count} textures");
        }

        /// <summary>Lists every clip with its length, and every bone of every model.</summary>
        public static void Report()
        {
            Build();
            var lib = AssetDatabase.LoadAssetAtPath<ModelLibrary>(Out);
            foreach (var c in lib.clips) Debug.Log($"[import] clip {c.name} {c.length:0.00}s legacy={c.legacy} loop={c.isLooping}");
            foreach (var m in lib.models)
            {
                var names = m.prefab.GetComponentsInChildren<Transform>(true).Select(t => t.name);
                Debug.Log($"[import] model {m.name}: {string.Join(" ", names)}");
                foreach (var t in m.prefab.GetComponentsInChildren<Transform>(true))
                    if (t.name == "Head" || t.name == "hand_r" || t.name == "hand_l" || t.name == "foot_l" || t.name == "pelvis" || t.name == "middle_01_r" || t.name == "thumb_01_r" || t.name == "Armature" || t.name == "root")
                        Debug.Log($"[import]   rest {t.name}: pos {m.prefab.transform.InverseTransformPoint(t.position).ToString("0.000")} rot {t.rotation.eulerAngles.ToString("0.0")} scale {t.lossyScale.ToString("0.000")}");
                foreach (var r in m.prefab.GetComponentsInChildren<Renderer>(true))
                {
                    var mesh = r is SkinnedMeshRenderer s ? s.sharedMesh : r.GetComponent<MeshFilter>()?.sharedMesh;
                    Debug.Log($"[import]   renderer {r.name}: {(mesh ? mesh.vertexCount : 0)} verts, {(mesh ? mesh.subMeshCount : 0)} parts, bounds {(mesh ? mesh.bounds.ToString() : "-")}, scale {r.transform.lossyScale}");
                }
            }
        }
    }
}
