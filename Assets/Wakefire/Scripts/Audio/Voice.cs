// Character voices for the text: tiny vowel-shaped blips synthesised at startup (a pitch and
// a throat per character), so a gruff captain, a frightened boy and a smug oracle sound like
// themselves while their words type out. Dream-selves get a soft echo.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public static class Voice
    {
        struct Profile { public float f0, dur, breath, vibrato, gain; public Profile(float f, float d, float b = 0, float v = 0, float g = 1) { f0 = f; dur = d; breath = b; vibrato = v; gain = g; } }

        static readonly Dictionary<string, Profile> profiles = new Dictionary<string, Profile>
        {
            { "narrator", new Profile(520, 0.022f, 0.0f, 0, 0.35f) },
            { "azar", new Profile(132, 0.060f, 0.05f, 0, 0.9f) },
            { "dur", new Profile(98, 0.070f, 0.22f, 0, 0.9f) },
            { "child", new Profile(330, 0.048f, 0.02f, 0.02f, 0.75f) },
            { "baker", new Profile(240, 0.055f, 0.04f, 0, 0.8f) },
            { "potter", new Profile(150, 0.062f, 0.10f, 0.03f, 0.85f) },
            { "oracle", new Profile(205, 0.065f, 0.06f, 0.06f, 0.8f) },
            { "fisher", new Profile(160, 0.058f, 0.08f, 0, 0.85f) },
            { "priest", new Profile(112, 0.072f, 0.05f, 0.02f, 0.9f) },
            { "man", new Profile(145, 0.058f, 0.06f, 0, 0.85f) },
            { "woman", new Profile(225, 0.055f, 0.04f, 0.01f, 0.8f) },
            { "merchant", new Profile(175, 0.050f, 0.05f, 0, 0.85f) },
            { "dog", new Profile(165, 0.055f, 0.32f, 0.04f, 0.85f) },
            { "god", new Profile(62, 0.150f, 0.30f, 0.015f, 1.0f) },
            // the dead: more breath than voice, and an echo they bring with them
            { "clerk", new Profile(128, 0.064f, 0.26f, 0.0f, 0.8f) },
            { "ghost", new Profile(150, 0.066f, 0.34f, 0.03f, 0.75f) },
            { "ghost_f", new Profile(232, 0.062f, 0.30f, 0.03f, 0.72f) },
            { "ghost_old", new Profile(196, 0.074f, 0.38f, 0.06f, 0.72f) },
            { "general", new Profile(92, 0.072f, 0.30f, 0.0f, 0.85f) },
            { "king", new Profile(54, 0.130f, 0.36f, 0.01f, 1.0f) },
            { "robber", new Profile(168, 0.050f, 0.07f, 0, 0.85f) },
        };

        // formant pairs for a, e, i, o, u
        static readonly Vector2[] vowels = { new Vector2(760, 1200), new Vector2(520, 1850), new Vector2(330, 2250), new Vector2(520, 920), new Vector2(340, 800) };
        static readonly Dictionary<string, AudioClip[]> clips = new Dictionary<string, AudioClip[]>();
        static AudioSource src;
        static float last;
        public static float Volume = 0.55f;
        const int Rate = 44100;

        static AudioSource Src
        {
            get
            {
                if (src) return src;
                var go = new GameObject("Voice");
                Object.DontDestroyOnLoad(go);
                src = go.AddComponent<AudioSource>();
                src.playOnAwake = false;
                src.volume = 0.55f;
                return src;
            }
        }

        static AudioClip[] Get(string voice, bool dream)
        {
            // the dead always sound as if they are speaking from the next room
            if (voice == "clerk" || voice == "king" || voice == "general" || voice.StartsWith("ghost")) dream = true;
            string key = voice + (dream ? "~" : "");
            if (clips.TryGetValue(key, out var arr)) return arr;
            if (!profiles.TryGetValue(voice, out var p)) p = profiles["narrator"];
            arr = new AudioClip[vowels.Length];
            var rng = new System.Random(voice.GetHashCode());
            for (int v = 0; v < vowels.Length; v++) arr[v] = Make(key + v, p, vowels[v], dream, rng);
            clips[key] = arr;
            return arr;
        }

        static AudioClip Make(string name, Profile p, Vector2 formant, bool dream, System.Random rng)
        {
            float tail = dream ? 0.16f : 0f;
            int n = (int)((p.dur + tail) * Rate);
            var data = new float[n];
            bool tick = p.f0 > 400;
            int voiced = (int)(p.dur * Rate);
            double phase = 0;
            for (int i = 0; i < voiced; i++)
            {
                float t = i / (float)Rate;
                float env = Mathf.Min(1f, t / 0.006f) * Mathf.Exp(-t / (p.dur * 0.45f));
                if (tick)
                {
                    data[i] = Mathf.Sin(2 * Mathf.PI * p.f0 * t) * Mathf.Exp(-t / 0.006f) * 0.5f;
                    continue;
                }
                float f0 = p.f0 * (1f - 0.12f * t / p.dur) * (1f + p.vibrato * Mathf.Sin(2 * Mathf.PI * 7f * t));
                phase += f0 / Rate;
                float s = 0;
                for (int k = 1; k * f0 < 3600; k++)
                {
                    float fk = k * f0;
                    float a = Res(fk, formant.x, 110) + 0.7f * Res(fk, formant.y, 160) + 0.15f / k;
                    s += a * Mathf.Sin((float)(2 * System.Math.PI * phase * k));
                }
                s += p.breath * ((float)rng.NextDouble() * 2 - 1);
                data[i] = s * env;
            }
            // normalise, then an echo for dream-selves
            float peak = 0.0001f;
            for (int i = 0; i < n; i++) peak = Mathf.Max(peak, Mathf.Abs(data[i]));
            for (int i = 0; i < n; i++) data[i] = data[i] / peak * 0.5f * p.gain;
            if (dream)
            {
                int d1 = (int)(0.045f * Rate), d2 = (int)(0.11f * Rate);
                for (int i = n - 1; i >= 0; i--)
                {
                    if (i - d1 >= 0) data[i] += data[i - d1] * 0.35f;
                    if (i - d2 >= 0) data[i] += data[i - d2] * 0.2f;
                }
            }
            var clip = AudioClip.Create("voice_" + name, n, 1, Rate, false);
            clip.SetData(data, 0);
            return clip;
        }

        static float Res(float f, float center, float bw)
        {
            float x = (f - center) / bw;
            return 1f / (1f + x * x);
        }

        /// <summary>One syllable of a character's voice; called as letters appear.</summary>
        public static void Blip(string voice, char c, bool dream)
        {
            if (string.IsNullOrEmpty(voice) || voice == "none") return;
            if (Time.unscaledTime - last < 0.045f) return;
            last = Time.unscaledTime;
            var arr = Get(voice, dream);
            int v = char.ToLowerInvariant(c) switch { 'a' => 0, 'e' => 1, 'i' => 2, 'y' => 2, 'o' => 3, 'u' => 4, 'w' => 4, _ => Mathf.Abs(c * 7) % 5 };
            var s = Src;
            if (Volume <= 0) return;
            s.volume = Volume;
            s.pitch = 1f + Random.Range(-0.06f, 0.06f);
            s.PlayOneShot(arr[v], 1f);
        }
    }
}
