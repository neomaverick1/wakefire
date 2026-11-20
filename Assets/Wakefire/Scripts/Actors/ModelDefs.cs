// Which model plays each character, and which stretch of which clip plays each of the game's
// animation names. The names (run, attack1, nod...) and their frame counts are the ones the
// game logic already uses, so a strike still lands on the frame it always landed on.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    /// <summary>One game animation, as a stretch of a clip.</summary>
    public class ClipMap
    {
        public string clip;
        public AnimationClip asset;
        public float t0, t1;                 // the stretch used, in seconds (t1 = 0: to the end)
        public bool own;                     // runs on its own clock instead of following the sprite frames
        public bool loop = true;
        public float speed = 1f;
        public float phase;                  // for strides that follow the frames: where frame 0 falls in the cycle
        public float[] warp;                 // pairs (fraction of the frames, fraction of the stretch): pins a strike to its frame,
                                             // or slows the planted part of a stride so the foot doesn't slide
        public float shift;                  // after warping a loop: where in the clip the cycle starts
        public float fps;                    // frames a second for the game's clock (0: the usual table)
        public int frames;                   // how many frames the game counts (0: as the sprite sheet has)
        public float fade = 0.09f;           // seconds to blend in from whatever came before
        public float step = 30f;             // poses a second; drawn animation moves in steps, not a blur
        public Action<ModelActor, float> pose;   // a gesture layered on by hand (a nodding head, a shrug)

        public float End => t1 > 0 ? t1 : asset.length;

        public float At(float n, float clock)
        {
            float a = t0, b = End;
            if (own) return a + (loop ? Mathf.Repeat(clock, b - a) : Mathf.Min(clock, b - a));
            float k = loop ? Mathf.Repeat(n + phase, 1f) : Mathf.Clamp01(n);
            if (warp != null)
            {
                for (int i = 0; i + 3 < warp.Length; i += 2)
                    if (k <= warp[i + 2]) { k = Mathf.Lerp(warp[i + 1], warp[i + 3], Mathf.InverseLerp(warp[i], warp[i + 2], k)); break; }
            }
            if (loop) k = Mathf.Repeat(k + shift, 1f);
            return a + (b - a) * k;
        }
    }

    public class ModelDef
    {
        public string model;
        public float scale = 1.45f;          // world units to a metre of model
        public float forward = 180f;         // which way the model faces as imported (these face backwards)
        public int span = 1;                 // squares of the stage along each side
        public readonly Dictionary<string, ClipMap> anims = new Dictionary<string, ClipMap>();
        public Action<ModelActor> dress;

        public ClipMap Map(string anim)
        {
            if (anims.TryGetValue(anim, out var m) && m.asset) return m;
            return anims.TryGetValue("idle", out m) ? m : null;
        }

        /// <summary>A stride or pose that follows the sprite's frames.</summary>
        public ClipMap Fit(string anim, string clip, float t0 = 0, float t1 = 0, bool loop = false, float phase = 0, float[] warp = null, float fade = 0.07f)
        {
            var m = new ClipMap { clip = clip, t0 = t0, t1 = t1, loop = loop, phase = phase, warp = warp, fade = fade };
            anims[anim] = m;
            return m;
        }

        /// <summary>A clip that runs at its own pace for as long as the animation is showing.</summary>
        public ClipMap Own(string anim, string clip, float t0 = 0, float t1 = 0, bool loop = true, float speed = 1f, float fade = 0.12f)
        {
            var m = new ClipMap { clip = clip, t0 = t0, t1 = t1, own = true, loop = loop, speed = speed, fade = fade };
            anims[anim] = m;
            return m;
        }
    }

    public static class ModelDefs
    {
        static Dictionary<string, ModelDef> defs;
        public static bool Off;

        public static ModelDef For(string sheet)
        {
            if (Off || !ModelLibrary.I) return null;
            if (defs == null) Build();
            return defs.TryGetValue(sheet, out var d) ? d : null;
        }

        static void Add(string sheet, ModelDef d)
        {
            var lib = ModelLibrary.I;
            if (!lib.Prefab(d.model)) return;
            foreach (var m in d.anims.Values) m.asset = lib.Clip(m.clip);
            defs[sheet] = d;
        }

        static void Build()
        {
            defs = new Dictionary<string, ModelDef>();
            Off = Boot.Flag("-sprites");
            if (Off) return;
            Add("azar", Azar());
        }

        static ModelDef Azar()
        {
            var d = new ModelDef { model = "UAL1", scale = 1.45f };
            d.Own("idle", "Idle_Loop");
            // Eight frames to a stride; the left foot lands as frame 2 begins, the right as frame 6 does.
            // The clip is a bounding 5.3 m/s run. Azar covers 5.4 tiles a second, so the planted part
            // of each step is slowed until the foot stays where it lands, and the airborne part is
            // quickened to keep a runner's cadence (about 160 steps a minute).
            var run = d.Fit("run", "Jog_Fwd_Loop", loop: true, phase: -0.25f, warp: new[] { 0f, 0f, 0.269f, 0.15f, 0.5f, 0.49f, 0.769f, 0.64f, 1f, 1f });
            run.shift = 0.03f;
            run.fps = 8f / 0.736f;
            d.Fit("attack1", "Sword_Attack", 0.26f, 0.80f, warp: new[] { 0f, 0f, 0.333f, 0.30f, 1f, 1f }, fade: 0.04f);
            d.Fit("attack2", "Sword_Attack", 0.26f, 0.80f, warp: new[] { 0f, 0f, 0.333f, 0.30f, 1f, 1f }, fade: 0.04f);
            d.Fit("attack3", "Sword_Attack", 0.10f, 0.95f, warp: new[] { 0f, 0f, 0.43f, 0.38f, 1f, 1f }, fade: 0.04f);
            d.Fit("roll", "Roll", 0.30f, 1.02f, fade: 0.05f);
            d.Own("hurt", "Hit_Chest", loop: false, fade: 0.03f);
            d.Own("death", "Death01", loop: false, fade: 0.08f);
            d.Own("push", "Push_Loop");
            d.Own("use", "Spell_Simple_Shoot", loop: false, fade: 0.05f);
            d.Own("itemget", "Idle_Torch_Loop");
            d.dress = Cast.Azar;
            return d;
        }
    }
}
