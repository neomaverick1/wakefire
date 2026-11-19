// The score: every place has a waking track and a dream track written to the same bar lines,
// played together in lockstep. Nodding off crossfades from one to the other mid-phrase, so the
// music changes worlds with Azar instead of starting over.
using UnityEngine;

namespace Wakefire
{
    public class Music : MonoBehaviour
    {
        static Music I;
        AudioSource wake, dream, oldWake, oldDream;
        string current;
        float fadeIn = 1, fadeOut;
        public static float Volume = 0.65f;

        static void Ensure()
        {
            if (I) return;
            var go = new GameObject("Music");
            DontDestroyOnLoad(go);
            I = go.AddComponent<Music>();
            AudioSource Src() { var s = go.AddComponent<AudioSource>(); s.loop = true; s.playOnAwake = false; s.volume = 0; return s; }
            I.wake = Src(); I.dream = Src(); I.oldWake = Src(); I.oldDream = Src();
        }

        public static void Play(string name, bool loop = true)
        {
            if (string.IsNullOrEmpty(name)) return;
            Ensure();
            if (name == I.current) return;
            var w = Resources.Load<AudioClip>("Music/" + name);
            if (!w) return;
            var d = Resources.Load<AudioClip>("Music/" + name + "_dream");
            I.current = name;
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
            float duck = DialogueBox.I && DialogueBox.I.Busy ? 0.8f : 1f;
            wake.volume = Volume * fadeIn * duck * (hasDream ? 1 - amt : 1);
            dream.volume = Volume * fadeIn * duck * amt;
            if (hasDream && wake.isPlaying && Mathf.Abs(dream.timeSamples - wake.timeSamples) > 2048 && dream.clip.samples == wake.clip.samples)
                dream.timeSamples = wake.timeSamples;
            oldWake.volume = Volume * fadeOut * (1 - amt);
            oldDream.volume = Volume * fadeOut * amt;
            if (fadeOut <= 0) { if (oldWake.isPlaying) oldWake.Stop(); if (oldDream.isPlaying) oldDream.Stop(); }
        }
    }
}
