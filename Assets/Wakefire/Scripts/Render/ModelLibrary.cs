// Every rigged model and animation clip the game uses, gathered into one asset by the editor
// (Wakefire.EditorTools.Models.Build) so the game can ask for them by name.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class ModelLibrary : ScriptableObject
    {
        [Serializable] public class Model { public string name; public GameObject prefab; }

        public List<Model> models = new List<Model>();
        public List<AnimationClip> clips = new List<AnimationClip>();
        public List<Mesh> meshes = new List<Mesh>();
        public List<Texture2D> textures = new List<Texture2D>();
        public Material material;

        static ModelLibrary lib;
        static bool looked;
        Dictionary<string, AnimationClip> clipByName;
        Dictionary<string, Mesh> meshByName;

        public static ModelLibrary I
        {
            get
            {
                if (!looked) { looked = true; lib = Resources.Load<ModelLibrary>("Models/Library"); }
                return lib;
            }
        }

        public GameObject Prefab(string name)
        {
            foreach (var m in models) if (m.name == name) return m.prefab;
            return null;
        }

        public AnimationClip Clip(string name)
        {
            if (clipByName == null)
            {
                clipByName = new Dictionary<string, AnimationClip>();
                foreach (var c in clips) if (c) clipByName[Short(c.name)] = c;
            }
            return clipByName.TryGetValue(name, out var clip) ? clip : null;
        }

        public Mesh Mesh(string name)
        {
            if (meshByName == null)
            {
                meshByName = new Dictionary<string, Mesh>();
                foreach (var m in meshes) if (m) meshByName[m.name] = m;
            }
            return meshByName.TryGetValue(name, out var mesh) ? mesh : null;
        }

        public Texture2D Texture(string name)
        {
            foreach (var t in textures) if (t && t.name == name) return t;
            return null;
        }

        /// <summary>Clips arrive as "Armature|Walk_Loop"; the game knows them as "Walk_Loop".</summary>
        public static string Short(string clip)
        {
            int bar = clip.LastIndexOf('|');
            return bar >= 0 ? clip.Substring(bar + 1) : clip;
        }
    }
}
