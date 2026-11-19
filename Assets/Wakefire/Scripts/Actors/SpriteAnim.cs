// Sprite sheets rendered from the Blender rigs: rows are (animation, direction), columns are
// frames. Right-facing frames are the left ones mirrored, the way 32-bit games did it.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public enum Facing { Down, Up, Left, Right }

    [Serializable] public class SheetJson { public int size; public float[] pivot; public AnimJson[] anims; }
    [Serializable] public class AnimJson { public string name, dir; public int row, frames; }

    public class SpriteSheet
    {
        public readonly Dictionary<string, Sprite[]> anims = new Dictionary<string, Sprite[]>();
        public string name;
        static readonly Dictionary<string, SpriteSheet> cache = new Dictionary<string, SpriteSheet>();

        public static SpriteSheet Load(string name)
        {
            if (cache.TryGetValue(name, out var s)) return s;
            s = new SpriteSheet { name = name };
            var tex = Resources.Load<Texture2D>("Sprites/" + name);
            tex.filterMode = FilterMode.Point;
            var meta = JsonUtility.FromJson<SheetJson>(Resources.Load<TextAsset>("Sprites/" + name).text);
            int S = meta.size;
            var pivot = new Vector2(meta.pivot[0] / S, 1f - meta.pivot[1] / S);
            foreach (var a in meta.anims)
            {
                var arr = new Sprite[a.frames];
                for (int i = 0; i < a.frames; i++)
                {
                    var rect = new Rect(i * S, tex.height - (a.row + 1) * S, S, S);
                    arr[i] = Sprite.Create(tex, rect, pivot, 16f, 0, SpriteMeshType.FullRect);
                }
                s.anims[a.name + ":" + a.dir] = arr;
            }
            cache[name] = s;
            return s;
        }

        public Sprite[] Get(string anim, Facing f, out bool flip)
        {
            flip = f == Facing.Right;
            string d = f == Facing.Down ? "down" : f == Facing.Up ? "up" : "left";
            if (anims.TryGetValue(anim + ":" + d, out var arr)) return arr;
            if (anims.TryGetValue(anim + ":down", out arr)) { flip = false; return arr; }
            return null;
        }
    }

    public class SpriteAnim : MonoBehaviour
    {
        public SpriteRenderer sr;
        public SpriteSheet sheet;
        public string anim = "idle";
        public Facing facing = Facing.Down;
        public float fps = 8f;
        public bool loop = true;
        public float time;
        public int Frame { get; private set; }
        public int FrameCount { get; private set; }
        public bool Done => !loop && time * fps >= FrameCount;
        Sprite[] frames;
        public event Action<string, int> FrameChanged;

        public static readonly Dictionary<string, (float fps, bool loop)> Timing = new Dictionary<string, (float, bool)>
        {
            { "idle", (3f, true) }, { "run", (14f, true) }, { "walk", (10f, true) }, { "attack1", (20f, false) }, { "attack2", (20f, false) },
            { "attack3", (17f, false) }, { "roll", (24f, false) }, { "hurt", (10f, false) }, { "death", (8f, false) }, { "nod", (12f, false) },
            { "wake", (12f, false) }, { "use", (10f, false) }, { "itemget", (2f, false) }, { "push", (8f, true) }, { "block", (8f, false) },
            { "doze", (9f, false) }, { "yawn", (7f, false) }, { "shrug", (2f, false) }, { "point", (2f, false) }, { "sigh", (3f, false) },
            { "idle_nod", (8f, false) },
            // townsfolk
            { "sleep", (1.6f, true) }, { "lean", (1.4f, true) }, { "lie", (0.7f, true) }, { "talk", (7f, true) }, { "knead", (5f, true) },
            { "sleepwalk", (6f, true) }, { "cower", (3f, true) },
            // the goat
            { "goat:idle", (6f, true) }, { "goat:walk", (9f, true) }, { "stare", (0.5f, true) }, { "eat", (5f, true) }, { "bleat", (6f, false) },
            { "butt", (14f, false) },
        };

        public void Play(string name, Facing f, bool restart = false)
        {
            if (name == anim && f == facing && !restart && frames != null) return;
            anim = name;
            facing = f;
            var t = Timing.TryGetValue(sheet.name + ":" + name, out var tm) ? tm : Timing.TryGetValue(name, out tm) ? tm : (8f, true);
            fps = t.Item1;
            loop = t.Item2;
            frames = sheet.Get(name, f, out bool flip);
            sr.flipX = flip;
            FrameCount = frames != null ? frames.Length : 1;
            if (restart || true) { time = 0; Frame = -1; }
            Tick(0);
        }

        public void SetFacing(Facing f)
        {
            if (f == facing) return;
            float keep = time;
            int keepFrame = Frame;
            frames = sheet.Get(anim, f, out bool flip);
            facing = f;
            sr.flipX = flip;
            time = keep;
            Frame = keepFrame;
            if (frames != null && Frame >= 0) sr.sprite = frames[Mathf.Clamp(Frame, 0, frames.Length - 1)];
        }

        public void Tick(float dt)
        {
            if (frames == null || frames.Length == 0) return;
            time += dt;
            int f = (int)(time * fps);
            f = loop ? f % frames.Length : Mathf.Min(f, frames.Length - 1);
            if (f != Frame)
            {
                Frame = f;
                sr.sprite = frames[f];
                FrameChanged?.Invoke(anim, f);
            }
        }
    }
}
