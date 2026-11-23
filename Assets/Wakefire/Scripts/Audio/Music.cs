// The score: every place has a waking track and a dream track written to the same bar lines,
// played together in lockstep. Nodding off crossfades from one to the other mid-phrase, so the
// music changes worlds with Azar instead of starting over.
using UnityEngine;

namespace Wakefire
{
    public class Music : MonoBehaviour
    {
        static Music I;
        AudioSource wake, dream, oldWake, oldDream, amb, oldAmb;
        string ambName;
        float ambIn = 1, ambOut;
        public static float AmbVolume = 0.5f;
        string current;
        float fadeIn = 1, fadeOut;
        public static float Volume = 0.65f;
        static float duckTo = 1f, duckUntil, duckNow = 1f;

        /// <summary>Pull the music down under a fanfare for a few seconds; it comes back by itself.</summary>
        public static void Duck(float level, float seconds) { duckTo = level; duckUntil = Time.unscaledTime + seconds; }

        // loudness trims (dB) measured from the rendered tracks, so every place sits at the same level,
        // waking and dream versions match for the crossfade, and the boss hits a little harder
        static readonly System.Collections.Generic.Dictionary<string, float> TrimDb = new System.Collections.Generic.Dictionary<string, float>
        {
            { "boss", +2.8f },
            { "dungeon", +0.0f },
            { "dungeon_dream", -2.1f },
            { "ending", -0.5f },
            { "hills", -2.3f },
            { "hill", -2.7f },
            { "hill_dream", -2.1f },
            { "tomb", +1.3f },
            { "tomb_dream", -1.8f },
            { "king", +0.4f },
            { "dawn", +0.4f },
            { "hills_dream", -1.7f },
            { "sea", -3.3f },
            { "sea_dream", -0.9f },
            { "summit", +0.2f },
            { "temple", +1.6f },
            { "temple_dream", -0.7f },
            { "title", +1.5f },
            { "town", +0.4f },
            { "town_dream", -1.5f },
        };

        static float Trim(AudioSource s) => s.clip && TrimDb.TryGetValue(s.clip.name, out var db) ? Mathf.Pow(10f, db / 20f) : 1f;

        static void Ensure()
        {
            if (I) return;
            var go = new GameObject("Music");
            DontDestroyOnLoad(go);
            I = go.AddComponent<Music>();
            AudioSource Src() { var s = go.AddComponent<AudioSource>(); s.loop = true; s.playOnAwake = false; s.volume = 0; return s; }
            I.wake = Src(); I.dream = Src(); I.oldWake = Src(); I.oldDream = Src(); I.amb = Src(); I.oldAmb = Src();
        }

        /// <summary>The bed of night sounds under the music: crickets, the sea, wind, dripping water.</summary>
        public static void Ambience(string name)
        {
            Ensure();
            if (name == I.ambName) return;
            I.ambName = name;
            (I.oldAmb, I.amb) = (I.amb, I.oldAmb);
            I.ambOut = 1; I.ambIn = 0;
            var c = string.IsNullOrEmpty(name) ? null : Resources.Load<AudioClip>("Audio/amb_" + name);
            I.amb.clip = c;
            if (c) I.amb.Play(); else I.amb.Stop();
        }

        public static string AmbienceFor(string music) => music switch
        {
            "town" => "night", "title" => "night", "sea" => "sea", "hills" => "hills", "temple" => "temple",
            "dungeon" => "dungeon", "summit" => "dungeon", "hill" => "wind", "tomb" => "dungeon", "crypt" => "dungeon", _ => null,
        };

        public static void Play(string name, bool loop = true)
        {
            if (string.IsNullOrEmpty(name)) return;
            Ensure();
            if (name == I.current) return;
            var w = Resources.Load<AudioClip>("Music/" + name);
            if (!w) return;
            var d = Resources.Load<AudioClip>("Music/" + name + "_dream");
            I.current = name;
            var a = AmbienceFor(name);
            if (a != null || name == "boss" || name == "ending" || name == "king" || name == "dawn") Ambience(a);
            // the old pair fades out while the new one comes in
            (I.oldWake, I.wake) = (I.wake, I.oldWake);
            (I.oldDream, I.dream) = (I.dream, I.oldDream);
            I.fadeOut = 1;
            I.fadeIn = 0;
            I.wake.clip = w; I.wake.loop = loop; I.wake.Play();
            I.dream.clip = d; I.dream.loop = loop;
            if (d) I.dream.Play(); else I.dream.Stop();
        }

        public static void Stop() { if (I) { I.current = null; (I.oldWake, I.wake) = (I.wake, I.oldWake); (I.oldDream, I.dream) = (I.dream, I.oldDream); I.fadeOut = 1; I.wake.Stop(); I.dream.Stop(); } }

        void Update()
        {
            float dt = Time.unscaledDeltaTime;
            fadeIn = Mathf.MoveTowards(fadeIn, 1, dt / 0.9f);
            fadeOut = Mathf.MoveTowards(fadeOut, 0, dt / 0.7f);
            float amt = Dream.I ? Dream.I.Amount : 0;
            bool hasDream = dream.clip && dream.isPlaying;
            duckNow = Mathf.MoveTowards(duckNow, Time.unscaledTime < duckUntil ? duckTo : 1f, dt / 0.35f);
            float duck = (DialogueBox.I && DialogueBox.I.Busy ? 0.8f : 1f) * duckNow;
            // equal-power crossfade between the worlds, so there's no dip halfway through nodding off
            float wg = Mathf.Cos(amt * Mathf.PI * 0.5f), dg = Mathf.Sin(amt * Mathf.PI * 0.5f);
            wake.volume = Volume * Trim(wake) * fadeIn * duck * (hasDream ? wg : 1);
            dream.volume = Volume * Trim(dream) * fadeIn * duck * dg;
            if (hasDream && wake.isPlaying && Mathf.Abs(dream.timeSamples - wake.timeSamples) > 2048 && dream.clip.samples == wake.clip.samples)
                dream.timeSamples = wake.timeSamples;
            oldWake.volume = Volume * Trim(oldWake) * fadeOut * (oldDream.clip ? wg : 1);
            oldDream.volume = Volume * Trim(oldDream) * fadeOut * dg;
            if (fadeOut <= 0) { if (oldWake.isPlaying) oldWake.Stop(); if (oldDream.isPlaying) oldDream.Stop(); }
            ambIn = Mathf.MoveTowards(ambIn, 1, dt / 1.5f);
            ambOut = Mathf.MoveTowards(ambOut, 0, dt / 1.2f);
            amb.volume = AmbVolume * ambIn * (1 - 0.65f * amt);
            oldAmb.volume = AmbVolume * ambOut * (1 - 0.65f * amt);
            if (ambOut <= 0 && oldAmb.isPlaying) oldAmb.Stop();
        }
    }
}
