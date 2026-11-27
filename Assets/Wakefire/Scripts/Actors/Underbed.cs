// The Underbed, all of it, as near as anybody gets. At the end of the crawl is the room where it
// keeps what it takes, and in the middle of that room is the first bed of the First Watch: the
// one the others were copied from. Nobody is in it. What is under it is longer than the bed.
//
// It feels for him with two arms at a time, and they stop at the edge of the light like any
// other; cut there, they go back under. Cut often enough, the bed loses its temper: it gets up
// on every arm it has and comes across the room in three jumps, each of which comes down hard.
// After the third it has no breath left and lies with its arms out on the floor like a dropped
// puppet, and that is when it can be hurt as often as there are hands in reach.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Underbed : Enemy
    {
        public enum S { Wake, Feel, Rattle, Hop, Land, Winded, Sink }
        public S s;
        public readonly List<Reach> arms = new List<Reach>();
        // (all four come from the middle of it: the bed is drawn over the part of each that is under the bed)
        static readonly Vector2[] Side = { new Vector2(0, -0.06f), new Vector2(-0.06f, 0), new Vector2(0.06f, 0), new Vector2(0, 0.06f) };
        static readonly Vector2[] Out = { Vector2.down, Vector2.left, Vector2.right, Vector2.up };
        // (where each hand goes down when the bed gets up on them: one at each corner of it)
        static readonly Vector2[] Corner = { new Vector2(-1.65f, -0.4f), new Vector2(-1.7f, 0.95f), new Vector2(1.7f, 0.95f), new Vector2(1.65f, -0.4f) };
        int cutsThisRound, hops, turn;
        float cutAt = -9f;
        float feelFor;
        Vector2 hopFrom, hopTo;
        /// <summary>0..1 through a jump (for the model: it comes up on its arms and tips forward).</summary>
        public float Air { get; private set; }
        public float Jolt { get; private set; }
        public bool Angry => health.hp <= health.max / 2;

        public static Underbed Spawn(Vector2 at) => Make<Underbed>("moth", "idle", at, WorldLayer.Waking, 12, "bedstead");

        protected override void Init()
        {
            speed = 0f; half = new Vector2(1.2f, 0.6f); touchDamage = 0; roams = false; flying = true;
            for (int i = 0; i < Side.Length; i++)
            {
                var a = Reach.Spawn(pos + Side[i]);
                a.owner = this; a.mouth = Out[i]; a.hand = Out[i] * 0.05f;
                a.health.max = a.health.hp = 99;
                arms.Add(a);
            }
            s = S.Wake;
        }

        public override bool Sleeps => false;
        protected override bool WaitsOutStories => true;
        protected override float KnockScale => 0f;
        public override Rect HitBox => new Rect(pos.x - 1.3f, pos.y - 0.2f, 2.6f, 2.0f);
        /// <summary>The bed is a bed. A blade rings off it; it is what is under it that can be cut.</summary>
        protected override bool Accepts(HitInfo h) { Jolt = 0.2f; return false; }
        public bool Winded => s == S.Winded;
        public bool Jumping => s == S.Rattle || s == S.Hop || s == S.Land;

        /// <summary>One of its hands has been cut.</summary>
        public void Cut(Reach arm)
        {
            // (one cut at a time: two hands under one swing are one cut)
            if (health.Dead || Time.time < cutAt + 0.45f) return;
            cutAt = Time.time;
            health.hp = Mathf.Max(0, health.hp - 1);
            flash = 0.15f; Jolt = 0.3f;
            cutsThisRound++;
            PixelView.I.Shake(1, 0.12f);
            if (health.Dead) { Rooms.Slain(this); Die(); }
        }

        protected override void Think(float dt, Player p)
        {
            if (Jolt > 0) Jolt -= dt;
            for (int i = 0; i < arms.Count; i++) if (arms[i]) arms[i].Root(pos + Side[i]);
            var d = p.pos - pos;
            switch (s)
            {
                case S.Wake:
                    // it lets him get well into the room
                    Hold(-1);
                    if (stateClock > 0.8f && CanSee(p, 7.5f)) { s = S.Feel; stateClock = 0; feelFor = 0; cutsThisRound = 0; }
                    break;

                case S.Feel:
                {
                    // two arms at a time (three when it is angry): the ones on his side of the bed
                    feelFor += dt;
                    int want = Angry ? 3 : 2, let = 0;
                    var order = new List<int> { 0, 1, 2, 3 };
                    order.Sort((a, b) => Vector2.Dot(Out[b], d.normalized).CompareTo(Vector2.Dot(Out[a], d.normalized)));
                    foreach (int i in order)
                    {
                        if (!arms[i]) continue;
                        if (let < want) { arms[i].Leash(false); let++; } else arms[i].Leash(true);
                    }
                    if (cutsThisRound >= (Angry ? 2 : 3) || feelFor > 16f)
                    {
                        s = S.Rattle; stateClock = 0; hops = 0;
                        Hold(-1);
                        for (int i = 0; i < arms.Count; i++) if (arms[i]) arms[i].Brace(Corner[i]);
                        Sfx.Play("bed_rattle", 1f, 0.03f);
                        if (Story.I) Story.I.UnderbedGetsUp();
                    }
                    break;
                }

                case S.Rattle:
                    // every arm back under it, and the whole bed shaking: it is getting its hands on the floor
                    Jolt = 0.2f;
                    if (Random.value < dt * 14f) Fx.Dust(pos + new Vector2(Random.Range(-0.8f, 0.8f), Random.Range(-0.5f, 0.1f)), 1);
                    if (stateClock > 0.9f) Jump(p);
                    break;

                case S.Hop:
                {
                    float k = Mathf.Clamp01(stateClock / 0.52f);
                    Air = Mathf.Max(0.001f, k);
                    pos = Vector2.Lerp(hopFrom, hopTo, Mathf.SmoothStep(0, 1, k));
                    hover = Mathf.Sin(k * Mathf.PI) * 1.35f;
                    if (k < 1f) break;
                    Air = 0; hover = 0;
                    s = S.Land; stateClock = 0;
                    Sfx.Play("bed_slam", 1f, 0.03f);
                    Noise.Make(pos, 12f);
                    PixelView.I.Shake(3, 0.22f);
                    Fx.Dust(pos + new Vector2(-0.8f, -0.4f), 5); Fx.Dust(pos + new Vector2(0.8f, -0.4f), 5); Fx.Dust(pos + new Vector2(0, -0.6f), 6);
                    if (Present && Mathf.Abs(p.pos.x - pos.x) < 1.75f && p.pos.y > pos.y - 0.9f && p.pos.y < pos.y + 2.1f && Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos))
                        p.Hurt(new HitInfo { damage = 2, from = pos, knockback = 8f, kind = HitKind.Crush, source = gameObject });
                    break;
                }

                case S.Land:
                    if (stateClock < (Angry ? 0.28f : 0.4f)) break;
                    if (++hops < (Angry ? 4 : 3)) { Jump(p); break; }
                    // out of breath: every arm it has, out on the floor
                    s = S.Winded; stateClock = 0;
                    Sfx.Play("bed_winded", 0.9f, 0.04f);
                    for (int i = 0; i < arms.Count; i++)
                        if (arms[i]) arms[i].Flop(Out[i] * Random.Range(1.5f, 2.1f) + new Vector2(Random.Range(-0.4f, 0.4f), Random.Range(-0.3f, 0.3f)));
                    break;

                case S.Winded:
                    if (stateClock > (Angry ? 2.4f : 3.0f))
                    {
                        foreach (var a in arms) if (a) a.Away(1.2f);
                        s = S.Feel; stateClock = 0; feelFor = 0; cutsThisRound = 0;
                    }
                    break;

                case S.Sink:
                    break;
            }
        }

        /// <summary>All of them under, and staying there (-1: every arm).</summary>
        void Hold(int except)
        {
            for (int i = 0; i < arms.Count; i++) if (arms[i] && i != except) arms[i].Leash(true);
        }

        void Jump(Player p)
        {
            s = S.Hop; stateClock = 0;
            hopFrom = pos;
            // at where he is, no further than a bed can jump, and not into a wall
            var to = pos + Vector2.ClampMagnitude(p.pos - pos, 3.2f);
            for (int i = 0; i < 6 && Solids.Overlaps(new Rect(to - half, half * 2), to, this); i++) to = Vector2.Lerp(to, pos, 0.25f);
            hopTo = to;
            Sfx.Play("bed_hop", 0.9f, 0.05f);
        }

        /// <summary>It goes down on its two walls for the last time, and what it has had for four hundred years comes
        /// out from under it.</summary>
        protected override void Die()
        {
            foreach (var a in arms) if (a) Destroy(a.gameObject);
            arms.Clear();
            Sfx.Play("bed_slam", 1f, 0.02f);
            Sfx.Play("reach_gone", 1f, 0.02f);
            PixelView.I.Shake(3, 0.35f);
            for (int i = 0; i < 26; i++)
                Fx.Spawn(pos + new Vector2(Random.Range(-0.8f, 0.8f), -0.3f), new Vector2(Random.Range(-3.5f, 3.5f), Random.Range(-4f, 1f)), 0.1f, Random.Range(2f, 6f), Random.Range(0.6f, 1.2f),
                    i % 3 == 0 ? new Color(0.50f, 0.34f, 0.20f) : new Color(0.36f, 0.24f, 0.15f), new Color(0.2f, 0.14f, 0.10f), 18f, 2);          // sandals. Lefts.
            for (int i = 0; i < 5; i++) Pickup.Drop(Pickup.Kind.Shekel, pos + new Vector2(Random.Range(-1f, 1f), Random.Range(-1.2f, -0.5f)));
            Pickup.Chance(pos + new Vector2(0, -0.9f), 0f, 1f);
            if (Story.I) Story.I.DenCleared();
            if (spawnId != null) Story.Set("dead_" + spawnId);
            // the bed stays where it stopped: it is only a bed now
            Story.SetCount("underbed_x", Mathf.RoundToInt(pos.x * 16f));
            Story.SetCount("underbed_y", Mathf.RoundToInt(pos.y * 16f));
            if (Story.I) Story.I.BedAtRest();
            Destroy(gameObject);
        }
    }

    /// <summary>The first bed of the First Watch: a slab on two low walls, a head-stone, a red blanket nobody has
    /// been under for four hundred years, and a dark under it that goes back a long way.</summary>
    public class BedProp : IPoser
    {
        Transform bed;
        Underbed who;
        bool looked;
        float time, lean;

        public static BedProp Make(ModelActor a)
        {
            var c = new BedProp();
            var go = new GameObject("bed");
            go.transform.SetParent(a.rig, false);
            c.bed = go.transform;
            a.bones["bed"] = c.bed;
            Color stone = new Color(0.60f, 0.53f, 0.42f), top = new Color(0.70f, 0.63f, 0.50f), dark = new Color(0.02f, 0.02f, 0.035f);
            Color red = new Color(0.50f, 0.09f, 0.09f), fold = new Color(0.36f, 0.06f, 0.07f), linen = new Color(0.84f, 0.80f, 0.70f), gold = new Color(0.88f, 0.66f, 0.22f);
            var kit = new Kit(a, a.rig, new[] { c.bed });
            kit.On("bed");
            const float W = 0.98f, L = 1.30f;                 // half its width, half its length (the foot is towards the lens)
            // the two walls it stands on, and the dark between them
            kit.Paint(stone).Box(new Vector3(-W + 0.08f, 0.14f, 0), new Vector3(0.16f, 0.28f, L * 2f)).Box(new Vector3(W - 0.08f, 0.14f, 0), new Vector3(0.16f, 0.28f, L * 2f));
            kit.Paint(dark).Box(new Vector3(0, 0.13f, 0.03f), new Vector3(W * 2f - 0.30f, 0.26f, L * 2f - 0.04f));
            // the slab, its head-stone
            kit.Paint(top).Box(new Vector3(0, 0.34f, 0), new Vector3(W * 2f, 0.12f, L * 2f));
            kit.Paint(stone).Box(new Vector3(0, 0.62f, -L + 0.10f), new Vector3(W * 2f, 0.68f, 0.20f));
            kit.Paint(gold, 1).Egg(new Vector3(0, 0.74f, -L + 0.205f), new Vector3(0.22f, 0.22f, 0.02f), 12, 4);      // the watch's sun, on the head-stone
            // linen, a red blanket folded back, a line of gold on the fold, and the pillow nobody has dented
            kit.Paint(linen).Box(new Vector3(0, 0.415f, 0.08f), new Vector3(W * 2f - 0.10f, 0.03f, L * 2f - 0.34f));
            kit.Paint(red).Box(new Vector3(0, 0.44f, 0.36f), new Vector3(W * 2f - 0.06f, 0.035f, L * 2f - 0.90f));
            kit.Paint(fold).Box(new Vector3(0, 0.465f, -0.16f), new Vector3(W * 2f - 0.06f, 0.03f, 0.16f));
            kit.Paint(gold, 1).Box(new Vector3(0, 0.468f, -0.07f), new Vector3(W * 2f - 0.06f, 0.012f, 0.03f));
            kit.Paint(linen).Egg(new Vector3(0, 0.46f, -L + 0.36f), new Vector3(0.30f, 0.07f, 0.15f), 10, 5);
            // the blanket hangs over the foot, a hand's width short of the floor
            kit.Paint(red).Box(new Vector3(0, 0.30f, L + 0.012f), new Vector3(W * 2f - 0.06f, 0.26f, 0.024f));
            kit.Paint(gold, 1).Box(new Vector3(0, 0.18f, L + 0.026f), new Vector3(W * 2f - 0.06f, 0.02f, 0.01f));
            kit.Wear("Bed");
            return c;
        }

        public void Pose(ModelActor a, string anim, float n, float dt)
        {
            if (!looked) { looked = true; who = a.sr ? a.sr.GetComponentInParent<Underbed>() : null; }
            time += dt;
            float jolt = who ? Mathf.Clamp01(who.Jolt / 0.3f) : 0f;
            float air = who ? who.Air : 0f;
            // something under it is breathing; hit or angry, it shakes; in the air it tips towards where it is going
            float breath = Mathf.Sin(time * 1.3f) * 0.012f + 0.012f;
            float shake = jolt * Mathf.Sin(time * 61f) * 0.03f;
            lean = Mathf.Lerp(lean, air > 0 ? Mathf.Sin(air * Mathf.PI) * 16f : who && who.Winded ? -5f : 0f, 1f - Mathf.Exp(-10f * dt));
            bed.localPosition = new Vector3(shake, breath + Mathf.Abs(shake) * 0.5f, 0);
            bed.localRotation = Quaternion.Euler(lean, 0, shake * 60f);
        }
    }
}
