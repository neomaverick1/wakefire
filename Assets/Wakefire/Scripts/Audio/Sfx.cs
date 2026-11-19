// Sound effects by name (Resources/Audio/sfx_<name>), played from a small pool with a little
// pitch variety so repeated swings and steps never sound copy-pasted.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Sfx : MonoBehaviour
    {
        static Sfx I;
        readonly List<AudioSource> pool = new List<AudioSource>();
        static readonly Dictionary<string, AudioClip> clips = new Dictionary<string, AudioClip>();
        public static float Volume = 0.9f;

        static void Ensure()
        {
            if (I) return;
            var go = new GameObject("Sfx");
            DontDestroyOnLoad(go);
            I = go.AddComponent<Sfx>();
            for (int i = 0; i < 12; i++) I.pool.Add(go.AddComponent<AudioSource>());
        }

        public static AudioClip Clip(string name)
        {
            if (clips.TryGetValue(name, out var c)) return c;
            c = Resources.Load<AudioClip>("Audio/sfx_" + name);
            clips[name] = c;
            return c;
        }

        public static void Play(string name, float vol = 1f, float pitchJitter = 0.05f)
        {
            var c = Clip(name);
            if (!c) return;
            Ensure();
            AudioSource src = null;
            foreach (var s in I.pool) if (!s.isPlaying) { src = s; break; }
            if (src == null) src = I.pool[0];
            src.clip = c;
            src.volume = vol * Volume;
            src.pitch = 1f + Random.Range(-pitchJitter, pitchJitter);
            src.Play();
        }
    }
}
