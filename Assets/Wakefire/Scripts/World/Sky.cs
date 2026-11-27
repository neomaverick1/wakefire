// The sky over the whole world. Light and weather are a state of the story, not of a place: when
// it rains it rains on every street of Ashkel, on the cliffs and on the Hill of Sleepers alike,
// because somewhere one man is asleep on his feet with a rain stick in his hand. Under a roof
// there is no weather, only the sound of it on the roof. And it does not rain in a dream.
using UnityEngine;

namespace Wakefire
{
    public class Sky : MonoBehaviour
    {
        public static Sky I;

        // ---- what the story says (flags, so a journey remembers its weather)
        public static bool Raining => Story.Has("sky_rain");
        public static bool Cold => Story.Has("sky_cold");
        public static bool Day => Story.Has("sky_day");

        /// <summary>0..1, eased: how much of each is in the picture this instant.</summary>
        public float rain, snow, day;
        /// <summary>For a scene that wants the weather to arrive in its own time (seconds to come or go).</summary>
        public float ease = 2.5f;

        static readonly System.Collections.Generic.HashSet<string> OpenMaps = new System.Collections.Generic.HashSet<string>
            { "ashkel", "lowtown", "cliffs", "terraces", "temple_yard", "necro_road", "necropolis", "zig_3" };

        /// <summary>Is there sky over this place? (The streets, the terraces, the cliffs, the hill, the yard, the summit.)</summary>
        public static bool Open(string map) => map != null && OpenMaps.Contains(map);
        public static bool Outdoors => Game.I && Open(Game.I.CurrentMap);
        /// <summary>Is rain coming down on this piece of ground? (Outdoors, and awake.)</summary>
        public static bool WetAt(Vector2 at) => Raining && Outdoors && !(Dream.I && Dream.I.IsDreamAt(at));
        /// <summary>...or is it under the cold?</summary>
        public static bool ColdAt(Vector2 at) => Cold && Outdoors && !(Dream.I && Dream.I.IsDreamAt(at));

        static readonly Color Moonlit = new Color(0.80f, 0.82f, 0.97f);
        Color lastSet = Moonlit;
        bool mine;
        AudioSource wet, roof, wind;
        float thunderIn = 20f, drip;
        string wasMap;

        public static void Ensure()
        {
            if (I) return;
            var go = new GameObject("Sky");
            DontDestroyOnLoad(go);
            I = go.AddComponent<Sky>();
            I.wet = I.Loop("rain_loop");
            I.roof = I.Loop("rain_roof_loop");
            I.wind = I.Loop("wind_loop");
        }

        AudioSource Loop(string name)
        {
            var s = gameObject.AddComponent<AudioSource>();
            s.clip = Sfx.Clip(name);
            s.loop = true; s.playOnAwake = false; s.volume = 0f;
            return s;
        }

        /// <summary>The story changes the weather. Nothing else does.</summary>
        public static void Set(string what, bool on)
        {
            Ensure();
            if (on) Story.Set("sky_" + what); else Story.Clear("sky_" + what);
        }

        /// <summary>No easing: the picture is already what the story says (a journey loaded, a test).</summary>
        public void Snap()
        {
            rain = Raining ? 1 : 0; snow = Cold ? 1 : 0; day = Day ? 1 : 0;
            mine = false;
        }

        /// <summary>The light the sky gives a street this instant.</summary>
        public Color Light()
        {
            var night = Moonlit;
            var noon = new Color(1.12f, 1.05f, 0.93f);
            var c = Color.Lerp(night, noon, day);
            // rain: lower, and greyer
            c = Color.Lerp(c, new Color(c.r * 0.60f, c.g * 0.64f, c.b * 0.74f), rain);
            // snow on the ground gives the night back some of its light, and takes the warmth out of the day
            c = Color.Lerp(c, Color.Lerp(new Color(0.84f, 0.90f, 1.04f), new Color(1.08f, 1.10f, 1.14f), day), snow * 0.8f);
            return c;
        }

        void Update()
        {
            float dt = Time.unscaledDeltaTime;
            // (behind the title the world stands still, and so does its weather)
            bool open = Outdoors && !Title.I;
            string map = Game.I && !Title.I ? Game.I.CurrentMap : null;
            if (map != wasMap) { wasMap = map; Snap(); }
            float step = dt / Mathf.Max(0.05f, ease);
            rain = Mathf.MoveTowards(rain, Raining ? 1 : 0, step);
            snow = Mathf.MoveTowards(snow, Cold ? 1 : 0, step);
            day = Mathf.MoveTowards(day, Day ? 1 : 0, step);
            Shader.SetGlobalVector("_WF_Sky", new Vector4(open ? rain : 0, open ? snow : 0, day, open ? 1 : 0));

            // the light of a street is the sky's to give; a room gives its own. Anything that borrows the light for a
            // moment (a Snuffer coming down, the dawn) hands it back as it found it, and then it is the sky's again.
            var v = PixelView.I;
            if (v && open)
            {
                var want = Light();
                if (!mine && (Near(v.ambient, Moonlit) || Near(v.ambient, lastSet))) { mine = true; lastSet = v.ambient; }
                if (mine)
                {
                    if (Near(v.ambient, lastSet)) { v.ambient = want; lastSet = want; }
                    else mine = false;
                }
            }
            else mine = false;

            // the sound of it: on the street, or on the roof
            float loud = Sfx.Volume * (Game.Paused ? 0.4f : 1f);
            bool dreaming = Dream.I && Dream.I.Dreaming;
            Fade(wet, open && !dreaming ? rain * 0.55f * loud : 0f, dt);
            Fade(roof, !open && map != null && Raining && !dreaming && Sheltered(map) ? 0.34f * loud : 0f, dt);
            Fade(wind, open && !dreaming ? snow * 0.5f * loud : 0f, dt);
            if (open && rain > 0.9f && !dreaming && !(Story.I && Story.I.Running) && (thunderIn -= dt) <= 0)
            {
                thunderIn = Random.Range(26f, 60f);
                Sfx.Play("thunder_far", Random.Range(0.35f, 0.6f), 0.12f);
            }
        }

        /// <summary>Houses have roofs for the rain to be heard on. A tomb is under a hill: nothing is heard there.</summary>
        static bool Sheltered(string map) => map.EndsWith("_in");

        static bool Near(Color a, Color b) => Mathf.Abs(a.r - b.r) + Mathf.Abs(a.g - b.g) + Mathf.Abs(a.b - b.b) < 0.012f;

        static void Fade(AudioSource s, float to, float dt)
        {
            if (!s || !s.clip) return;
            s.volume = Mathf.MoveTowards(s.volume, to, dt * 0.6f);
            if (s.volume > 0.001f && !s.isPlaying) s.Play();
            else if (s.volume <= 0.001f && s.isPlaying) s.Stop();
        }
    }
}
