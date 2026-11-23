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
        public bool bounce;                  // an own-clock clip that plays forward then back (hands working at something)
        public float stride;                 // for walks and runs: the ground speed (units a second) the clip is true at; the
                                             // legs then keep pace with however fast the actor is really moving
        public float paceMin = 0.4f, paceMax = 1.3f;
        public float yaw;                    // the body is turned this much from the way the actor faces (someone lying across the road)
        public Vector3 nudge;                // and moved this far (metres, in its own frame), to lie where the actor stands
        public float fps;                    // frames a second for the game's clock (0: the usual table)
        public int frames;                   // how many frames the game counts (0: as the sprite sheet has)
        public float fade = 0.09f;           // seconds to blend in from whatever came before
        public float step = 30f;             // poses a second; drawn animation moves in steps, not a blur
        public Action<ModelActor, float> pose;   // a gesture layered on by hand (a nodding head, a shrug)

        public float End => t1 > 0 ? t1 : asset.length;

        public float At(float n, float clock)
        {
            float a = t0, b = End;
            if (own) return a + (bounce ? Mathf.PingPong(clock, b - a) : loop ? Mathf.Repeat(clock, b - a) : Mathf.Min(clock, b - a));
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
        /// <summary>For a creature with no stock model: builds its skeleton and skin, and returns what will pose it.</summary>
        public Func<ModelActor, IPoser> build;

        public ClipMap Map(string anim)
        {
            if (anims.TryGetValue(anim, out var m) && (m.asset || build != null)) return m;
            return anims.TryGetValue("idle", out m) ? m : null;
        }

        /// <summary>For a built creature: how the game's clock runs for one of its animations.</summary>
        public ClipMap Time(string anim, float fps, int frames, float stride = 0, float paceMax = 3f)
        {
            var m = new ClipMap { fps = fps, frames = frames, stride = stride, paceMax = paceMax, paceMin = 0.2f };
            anims[anim] = m;
            return m;
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

    public static partial class ModelDefs
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
            if (d.build != null) { defs[sheet] = d; return; }
            if (!lib.Prefab(d.model)) return;
            foreach (var m in d.anims.Values) m.asset = lib.Clip(m.clip);
            defs[sheet] = d;
        }

        static void Build()
        {
            defs = new Dictionary<string, ModelDef>();
            Off = Boot.Flag("-sprites");
            if (Off) return;
            Add("azar", Azar(1.33f));            // the same build as the people he guards; the helmet does the rest
            var portrait = Azar(2.5f);          // the same man, nearer the lens: the title screen and the cover
            portrait.span = 2;
            Add("azar_title", portrait);
            Add("captain", Human(1.40f, Cast.Dur));
            var sentinel = Human(1.52f, Cast.Sentinel);
            Run(sentinel, 1.52f, 6.5f).With(Gesture.Level);
            Add("sentinel", sentinel);
            // the Herdsman: half as tall again as the men he was cast to outlast
            var herd = Human(1.95f, Cast.Herdsman);
            herd.span = 2;
            Walk(herd, "walk", 1.95f);
            herd.Own("raise", "Sword_Regular_C", 0.02f, 0.40f, loop: false, speed: 0.75f, fade: 0.08f);
            herd.Own("sweep", "Sword_Regular_B", 0.12f, 0.62f, loop: false, speed: 1.1f, fade: 0.04f);
            herd.Own("lean", "Idle_Loop", speed: 0.5f).With(Gesture.Leaning);
            herd.Own("call", "Idle_Torch_Loop", fade: 0.1f);
            Add("herdsman", herd);
            foreach (var who in new[] { "baker", "potter", "oracle", "fisher", "priest", "sleeper_a", "sleeper_b", "sleeper_c" })
                Add(who, Human(1.33f, Cast.Person(who)));
            Add("captain_child", Human(0.98f, Cast.Person("captain_child")));
            var god = Human(4.2f, Cast.Person("god"));
            god.span = 2;
            Add("god", god);
            Add("goat", Built(1.30f, a => Beast.Make<Goat>(a, Goat.Body)));
            Add("dog", Built(1.30f, a => Beast.Make<Dog>(a, Dog.Body)));
            Add("jackal", Built(1.35f, a => Beast.Make<JackalBeast>(a, JackalBeast.Body)));
            Add("den_mother", Built(2.3f, a => Beast.Make<JackalBeast>(a, JackalBeast.Mother), 2));
            Add("bull", Built(1.60f, a => Beast.Make<BullBeast>(a, BullBeast.Body), 2));
            Add("crab", Built(1.50f, a => CrabBeast.Make(a)));
            Add("moth", Built(1.60f, a => MothBeast.Make(a)));
            Hill();
        }

        /// <summary>A creature whose skeleton and skin are made by code.</summary>
        static ModelDef Built(float scale, Func<ModelActor, IPoser> build, int span = 1) =>
            new ModelDef { scale = scale, forward = 0f, build = build, span = span };

        /// <summary>A walk that keeps its feet under it: eight frames to the stride, true at the pace the clip was made for.</summary>
        static ClipMap Walk(ModelDef d, string anim, float scale)
        {
            var m = d.Fit(anim, "Walk_Loop", loop: true, fade: 0.14f);
            m.fps = 8f / 1.333f;
            m.frames = 8;
            m.stride = 0.9f * scale;
            m.paceMax = 3f;
            return m;
        }

        /// <summary>The run. The clip is a bounding 5.3 m/s; the planted part of each step is slowed to
        /// the true ground speed and the airborne part quickened, so feet stay where they land and
        /// the cadence stays a runner's (about 160 steps a minute at Azar's pace).</summary>
        static ClipMap Run(ModelDef d, float scale, float speed = 5.4f)
        {
            float natural = 5.26f * scale;                       // ground speed the clip's planted foot implies
            float plant = 0.14f * natural / speed;               // seconds each foot must stay down at our speed
            float air = Mathf.Clamp(0.34f - plant * 0.85f, 0.10f, 0.30f);
            float cycle = 2f * (plant + air);
            float a = plant / cycle, h = 0.5f;
            // the left foot lands as frame 2 begins, the right as frame 6 does
            var m = d.Fit("run", "Jog_Fwd_Loop", loop: true, phase: -0.25f, warp: new[] { 0f, 0f, a, 0.15f, h, 0.49f, h + a, 0.64f, 1f, 1f });
            m.shift = 0.03f;
            m.fps = 8f / cycle;
            m.frames = 8;
            m.stride = speed;
            return m;
        }

        static ClipMap With(this ClipMap m, Action<ModelActor, float> pose) { m.pose = pose; return m; }

        /// <summary>What every human in the game can do; each character adds or replaces as needed.</summary>
        static ModelDef Human(float scale, Action<ModelActor> dress)
        {
            var d = new ModelDef { model = "UAL1", scale = scale, dress = dress };
            d.Own("idle", "Idle_Loop");
            d.Own("talk", "Idle_Talking_Loop");
            d.Own("sleep", "Idle_Loop", speed: 0.5f).With(Gesture.Asleep());
            d.Own("lean", "Idle_Loop", speed: 0.5f).With(Gesture.Leaning);
            var lie = d.Own("lie", "Death01", 2.30f, 2.40f, loop: false, fade: 0f).With(Gesture.Lying);
            lie.yaw = 90f;
            lie.nudge = new Vector3(0, 0, -0.55f);
            Walk(d, "walk", scale);
            Walk(d, "sleepwalk", scale).With(Gesture.Sleepwalk);
            var knead = d.Own("knead", "PickUp_Table", 0.10f, 0.42f, speed: 0.75f).With(Gesture.Kneading);
            knead.bounce = true;
            d.Own("cower", "Crouch_Idle_Loop").With(Gesture.Cower);
            d.Own("point", "Idle_Loop").With(Gesture.Point);
            d.Own("shrug", "Idle_Loop").With(Gesture.Shrug);
            d.Own("sigh", "Idle_Loop").With(Gesture.Sigh);
            d.Own("itemget", "Idle_Torch_Loop");
            d.Own("open", "Chest_Open", loop: false, fade: 0.08f);
            d.Own("hurt", "Hit_Chest", loop: false, fade: 0.03f);
            d.Own("death", "Death01", loop: false, fade: 0.08f);
            return d;
        }

        static ModelDef Azar(float scale)
        {
            var d = Human(scale, Cast.Azar);
            Run(d, scale);
            // the three cuts, chained the way a swordsman chains them: a rising cut from the left hip,
            // a backhand cut across at the shoulder, and an overhead chop that ends it. Each clip begins
            // where the one before left the blade; the strike of each falls on the frame the game hits on.
            d.Fit("attack1", "Sword_Regular_A", 0.10f, 0.433f, warp: new[] { 0f, 0f, 0.333f, 0.45f, 1f, 1f }, fade: 0.04f);
            d.Fit("attack2", "Sword_Regular_B", 0.12f, 0.533f, warp: new[] { 0f, 0f, 0.333f, 0.363f, 1f, 1f }, fade: 0.04f);
            var chop = d.Fit("attack3", "Sword_Regular_C", 0.22f, 1.02f, warp: new[] { 0f, 0f, Player.ChopHit / (float)Player.ChopFrames, 0.54f, 1f, 1f }, fade: 0.05f);
            chop.frames = Player.ChopFrames;
            chop.fps = 17f;
            d.Fit("roll", "Roll", 0.30f, 1.02f, fade: 0.05f);
            d.Own("push", "Push_Loop");
            d.Own("use", "Spell_Simple_Shoot", loop: false, fade: 0.06f);
            d.Own("block", "Idle_Shield_Loop", fade: 0.05f);
            d.Own("guard", "Idle_Shield_Loop", fade: 0.07f);
            d.Own("throw", "OverhandThrow", 0.10f, 1.05f, loop: false, fade: 0.05f);
            d.Own("nod", "Idle_Loop", fade: 0.05f).With(Gesture.NodOff);
            d.Own("wake", "Idle_Loop", fade: 0.03f).With(Gesture.WakeUp);
            d.Own("doze", "Idle_Loop", speed: 0.5f).With(Gesture.Doze);
            d.Own("yawn", "Idle_Loop").With(Gesture.Yawn);
            d.Own("idle_nod", "Idle_Loop").With(Gesture.CatchHimself);
            return d;
        }
    }
}
