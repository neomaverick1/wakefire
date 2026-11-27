// The Dragnet. The fishermen of the Sea Cliffs dream, all of them, the same dream: that they
// left a net out. They did. Forty nights unattended, it has gone on fishing. It lies on the sand
// among the nets that are only nets, looking like one of them, except that there is money in it:
// whatever it has caught, it keeps. When something worth catching walks past it stands up, with
// nobody inside it and nobody holding it, and throws itself.
//
// Caught, he is hauled towards the sea. The blade cuts him out, a strand at a time; the Wakefire
// burns him out at once. A cast that misses leaves it spread on the ground with its cords open
// to a blade, and that is when it can be killed.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Dragnet : Enemy
    {
        public enum S { Flat, Rise, Cast, Spent, Gather, Creep, Wrap, Sink }
        public S s { get; private set; }
        Vector2 castFrom, castTo, sea;
        bool haveSea;
        int cuts;
        float squeeze, cool;
        /// <summary>Told once what it was, the first time it stands up.</summary>
        public static bool Told;

        public static Dragnet Spawn(Vector2 at) => Make<Dragnet>("moth", "flat", at, WorldLayer.Waking, 4, "dragnet");

        protected override void Init()
        {
            speed = 1.5f; half = new Vector2(0.3f, 0.15f); touchDamage = 0;
            if (shadow) { Destroy(shadow.gameObject); shadow = null; }
            // where the water is: the nearest edge of it
            float best = 22f;
            foreach (var sd in Solids.All)
            {
                if (!sd.pit || !sd.enabled || sd.layer == WorldLayer.Dream) continue;
                var q = new Vector2(Mathf.Clamp(pos.x, sd.r.xMin, sd.r.xMax), Mathf.Clamp(pos.y, sd.r.yMin, sd.r.yMax));
                float d = Vector2.Distance(q, pos);
                if (d < best) { best = d; sea = q; haveSea = true; }
            }
        }

        /// <summary>How far through its throw (0..1), and how far it has to go: the model spins itself open on the way.</summary>
        public float Flight { get; private set; }
        /// <summary>Somebody is in it.</summary>
        public bool Full => s == S.Wrap;
        /// <summary>The way it is hauling (for the lean of the thing).</summary>
        public Vector2 Haul { get; private set; }
        public float Jolt { get; private set; }

        public override bool Sleeps => false;

        protected override bool WaitsOutStories => true;
        protected override float KnockScale => 0f;
        protected override string HurtSound => "net_cut";
        protected override Color BurstColor => new Color(0.42f, 0.33f, 0.22f);
        public override Rect HitBox => s == S.Flat || s == S.Spent || s == S.Sink
            ? new Rect(pos.x - 1.1f, pos.y - 0.6f, 2.2f, 1.2f)
            : new Rect(pos.x - 0.6f, pos.y - 0.2f, 1.2f, 2.3f);

        /// <summary>Lying as a net it is a net: a blade wakes it and nothing more. Standing, it has nothing in it to cut.
        /// Spread on the ground after a throw, every cord is there to be cut.</summary>
        protected override bool Untouchable(HitInfo h)
        {
            if (s == S.Flat) { Wake(); return true; }
            if (s == S.Wrap) return true;                      // (his own cuts from inside are counted where he makes them)
            if (s == S.Spent || s == S.Gather || s == S.Sink) return false;
            if (h.kind == HitKind.Fire || h.kind == HitKind.Reflected || h.kind == HitKind.Thrown) return false;
            // a hood of cord with nobody in it: the blade goes in one side and out the other
            Jolt = 0.25f;
            Sfx.Play("net_swish", 0.6f, 0.1f);
            return true;
        }

        void Wake()
        {
            if (s != S.Flat) return;
            s = S.Rise; stateClock = 0;
            anim.Play("rise", Facing.Down, true);
            Sfx.Play("net_rise", 0.9f, 0.05f);
            Fx.Dust(pos, 8);
            if (!Told && Story.I && !Story.I.Running) { Told = true; Story.I.DragnetStoodUp(this); }
        }

        protected override void Think(float dt, Player p)
        {
            if (Jolt > 0) Jolt -= dt;
            cool -= dt;
            var d = p.pos - pos;
            switch (s)
            {
                case S.Flat:
                    anim.Play("flat", Facing.Down);
                    // something worth catching, close enough to catch
                    if (cool <= 0 && CanSee(p, 2.7f) && p.state != Player.State.Roll) Wake();
                    break;

                case S.Rise:
                    if (stateClock > 0.75f) Throw(p);
                    break;

                case S.Cast:
                {
                    float k = Mathf.Clamp01(stateClock / 0.5f);
                    Flight = Mathf.Max(0.001f, k);
                    pos = Vector2.Lerp(castFrom, castTo, k);
                    hover = Mathf.Sin(k * Mathf.PI) * 1.5f;
                    if (k < 1f) break;
                    Flight = 0; hover = 0;
                    Sfx.Play("net_land", 0.9f, 0.05f);
                    Fx.Dust(pos, 10);
                    bool got = Present && Vector2.Distance(p.pos, pos) < 0.95f && Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos) && p.Hold(this, "push");
                    if (got)
                    {
                        s = S.Wrap; stateClock = 0; cuts = 0; squeeze = 1.6f;
                        pos = p.pos + new Vector2(0, -0.02f);
                        anim.Play("wrap", Facing.Down, true);
                        PixelView.I.Shake(1, 0.15f);
                    }
                    else { s = S.Spent; stateClock = 0; anim.Play("spent", Facing.Down, true); }
                    break;
                }

                case S.Spent:
                    // spread on the ground with nothing in it: this is the moment
                    if (stateClock > 1.7f) { s = S.Gather; stateClock = 0; anim.Play("rise", Facing.Down, true); Sfx.Play("net_rise", 0.6f, 0.08f); }
                    break;

                case S.Gather:
                    if (stateClock > 0.7f) { s = S.Creep; stateClock = 0; }
                    break;

                case S.Creep:
                    // it comes after him the only way a net can: gathering itself up and letting itself down
                    anim.Play("creep", Facing.Down);
                    if (!CanSee(p, 9f))
                    {
                        var h = home - pos;
                        if (h.magnitude < 0.3f) { s = S.Sink; stateClock = 0; anim.Play("spent", Facing.Down, true); }
                        else Move(h.normalized * speed, dt);
                        break;
                    }
                    if (d.magnitude > 3.0f) Move(d.normalized * speed * (0.6f + 0.8f * Mathf.Abs(Mathf.Sin(stateClock * 4.5f))), dt);
                    else if (stateClock > 0.9f && p.state != Player.State.Roll) Throw(p);
                    break;

                case S.Wrap:
                    Wrapped(dt, p);
                    break;

                case S.Sink:
                    if (stateClock > 0.8f) { s = S.Flat; stateClock = 0; cool = 2.5f; anim.Play("flat", Facing.Down, true); }
                    break;
            }
        }

        void Throw(Player p)
        {
            s = S.Cast; stateClock = 0;
            castFrom = pos;
            // where he is going to be, if he keeps going; not further than a net flies
            var lead = p.pos + (p.anim.model ? p.anim.model.velocity : Vector2.zero) * 0.28f;
            castTo = pos + Vector2.ClampMagnitude(lead - pos, 4.6f);
            anim.Play("cast", Facing.Down, true);
            Sfx.Play("net_cast", 0.9f, 0.06f);
        }

        /// <summary>He is in it. It hauls for the water; he cuts. Three cuts, or one touch of the Wakefire, and he is out.</summary>
        void Wrapped(float dt, Player p)
        {
            if (!p.HeldBy(this)) { Let(p, false); return; }
            if (Controls.Down(Controls.Attack) && p.hasSword)
            {
                cuts++;
                Jolt = 0.25f;
                Sfx.Play("net_cut", 0.9f, 0.08f);
                PixelView.I.Shake(1, 0.1f);
                for (int i = 0; i < 6; i++)
                    Fx.Spawn(p.pos + new Vector2(Random.Range(-0.3f, 0.3f), 0), Random.insideUnitCircle * 2.5f, Random.Range(0.4f, 1.3f), Random.Range(1f, 4f), Random.Range(0.3f, 0.6f),
                        new Color(0.55f, 0.45f, 0.30f), new Color(0.2f, 0.14f, 0.10f), 16f);
                health.hp = Mathf.Max(1, health.hp - 1);
                if (cuts >= 3) { Let(p, true); return; }
            }
            if (Controls.Down(Controls.Item) && p.hasLantern && Items.Current != null && Items.Current.id == "wakefire")
            {
                // a net is tarred: it does not argue with fire
                Sfx.Play("ignite", 0.9f, 0.05f);
                Fx.Embers(p.pos + new Vector2(0, 0.8f), 14);
                health.hp = Mathf.Max(1, health.hp - 2);
                Let(p, true);
                return;
            }
            // the haul: a heave, a rest, a heave
            float heave = Mathf.Max(0f, Mathf.Sin(stateClock * 3.6f));
            var to = haveSea ? sea - p.pos : home - p.pos;
            Haul = to.sqrMagnitude > 0.01f ? to.normalized : Vector2.zero;
            if (to.magnitude > 0.25f)
            {
                var before = p.pos;
                p.pos = Solids.Move(p.pos, Haul * (0.3f + 1.8f * heave) * dt, p.half, p);
                if (heave > 0.9f && (p.pos - before).sqrMagnitude > 0.00001f && Random.value < 0.2f) Fx.Dust(p.pos, 1);
            }
            pos = p.pos + new Vector2(0, -0.02f);
            // at the water's edge it has what it came for
            bool atSea = haveSea && Vector2.Distance(p.pos, sea) < 0.75f;
            if (atSea)
            {
                var into = sea + Haul * 0.7f;
                Let(p, false);
                p.pos = into;                                   // (the ground gives out under him, and the game does the rest)
                Sfx.Play("splash", 0.9f, 0.05f);
                s = S.Sink; stateClock = -1.5f;
                return;
            }
            // kept long enough, it tightens
            if (!haveSea || stateClock > 6f)
            {
                squeeze -= dt;
                if (squeeze <= 0)
                {
                    squeeze = 1.6f;
                    Let(p, false);
                    p.Hurt(new HitInfo { damage = 1, from = pos + Vector2.up * 0.1f, knockback = 4f, kind = HitKind.Crush, source = gameObject });
                    s = S.Spent; stateClock = 0.6f; anim.Play("spent", Facing.Down, true);
                }
            }
        }

        void Let(Player p, bool cutOut)
        {
            if (p) p.Release(this);
            Haul = Vector2.zero;
            if (!cutOut) { if (s == S.Wrap) { s = S.Spent; stateClock = 0.4f; anim.Play("spent", Facing.Down, true); } return; }
            // cut out or burnt out: it falls open round him, and he has the first move
            s = S.Spent; stateClock = 0.2f;
            anim.Play("spent", Facing.Down, true);
            if (p) p.health.invulnerable = Mathf.Max(p.health.invulnerable, 0.6f);
            if (health.hp <= 0) { Rooms.Slain(this); Die(); }
        }

        protected override void OnHurt(HitInfo h)
        {
            Jolt = 0.3f;
            for (int i = 0; i < 7; i++)
                Fx.Spawn(pos + new Vector2(Random.Range(-0.7f, 0.7f), Random.Range(-0.3f, 0.3f)), Random.insideUnitCircle * 2.2f, 0.1f, Random.Range(1f, 3f), Random.Range(0.3f, 0.6f),
                    new Color(0.55f, 0.45f, 0.30f), new Color(0.2f, 0.14f, 0.10f), 16f);
            if (s == S.Spent) stateClock = Mathf.Max(stateClock, 1.1f);      // it starts pulling itself together
        }

        protected override void Die()
        {
            if (Player.I) Player.I.Release(this);
            // what it had caught before
            int n = Random.Range(4, 8);
            for (int i = 0; i < n; i++) Pickup.Drop(Pickup.Kind.Shekel, pos + Random.insideUnitCircle * 0.9f);
            if (Random.value < 0.35f) Pickup.Drop(Pickup.Kind.Flame, pos + Random.insideUnitCircle * 0.5f);
            for (int i = 0; i < 18; i++)
                Fx.Spawn(pos + Random.insideUnitCircle * 0.8f, Random.insideUnitCircle * 3.2f, Random.Range(0.1f, 0.9f), Random.Range(1.5f, 5f), Random.Range(0.4f, 0.9f),
                    i % 3 == 0 ? new Color(0.62f, 0.50f, 0.32f) : new Color(0.30f, 0.22f, 0.15f), new Color(0.12f, 0.09f, 0.08f), 17f, i % 4 == 0 ? 2 : 1);
            Sfx.Play("net_die", 1f, 0.04f);
            if (Story.I) Story.I.DragnetDone(this);
            if (spawnId != null) Story.Set("dead_" + spawnId);
            Destroy(gameObject);
        }

        protected override void OnDestroy()
        {
            if (Player.I) Player.I.Release(this);
            base.OnDestroy();
        }
    }

    // ------------------------------------------------------------------------------- the model
    /// <summary>A cast net of tarred cord: a hub, eight spokes, rings between them, a rim rope with a stone at
    /// every spoke to carry it down and a cork between to bring it back up. Lying, standing with nobody in it,
    /// thrown, and wrapped round somebody. Metres; y up.</summary>
    public class DragnetProp : IPoser
    {
        const int N = 8;
        const float RN = 1.05f;
        Transform hub;
        readonly Transform[] mid = new Transform[N], rim = new Transform[N];
        readonly float[] fold = new float[N];
        Dragnet who;
        bool looked, live;
        float time, spin;
        // the shape it is in now, and the one it is on its way to: hub height, mid ring (radius, height), rim (radius, height)
        Vector3 nowHub, nowMid, nowRim;
        float mess, nowMess;

        static Transform Bone(string name, Transform parent, Vector3 at)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = at;
            return go.transform;
        }

        static float Hash(float x) => Mathf.Repeat(Mathf.Sin(x * 91.7f) * 43758.5453f, 1f);

        static Vector3 Ring(int k, float r, float y) { float a = k * Mathf.PI * 2f / N; return new Vector3(Mathf.Cos(a) * r, y, Mathf.Sin(a) * r); }

        /// <summary>live: there is money in it.</summary>
        public static DragnetProp Make(ModelActor a, bool live = true)
        {
            var c = new DragnetProp { live = live };
            var rig = a.rig;
            c.hub = Bone("hub", rig, new Vector3(0, 0.04f, 0));
            var bones = new List<Transform> { c.hub };
            for (int k = 0; k < N; k++)
            {
                c.mid[k] = Bone("m" + k, rig, Ring(k, RN * 0.5f, 0.04f));
                c.rim[k] = Bone("n" + k, rig, Ring(k, RN, 0.04f));
                c.fold[k] = Hash(k * 3.1f + (live ? 0.37f : 1.9f));
                bones.Add(c.mid[k]);
                bones.Add(c.rim[k]);
            }
            foreach (var t in bones) a.bones[t.name] = t;

            Color tar = new Color(0.22f, 0.15f, 0.11f), worn = new Color(0.46f, 0.36f, 0.24f), hemp = new Color(0.62f, 0.50f, 0.32f);
            Color stone = new Color(0.47f, 0.47f, 0.50f), cork = new Color(0.74f, 0.55f, 0.34f), gold = new Color(0.98f, 0.80f, 0.30f), weed = new Color(0.20f, 0.42f, 0.30f);
            var kit = new Kit(a, rig, bones.ToArray());
            // every point of the net hangs between the hub, the two mid points and the two rim points it lies between
            kit.On(p =>
            {
                float r = new Vector2(p.x, p.z).magnitude, f = Mathf.Clamp01(r / RN);
                float ang = Mathf.Repeat(Mathf.Atan2(p.z, p.x) / (Mathf.PI * 2f) * N, N);
                int k0 = Mathf.FloorToInt(ang) % N, k1 = (k0 + 1) % N;
                float t = ang - Mathf.Floor(ang);
                int m0 = 1 + k0 * 2, m1 = 1 + k1 * 2, r0 = 2 + k0 * 2, r1 = 2 + k1 * 2;
                if (f < 0.5f)
                {
                    float u = f / 0.5f;
                    return new BoneWeight { boneIndex0 = 0, weight0 = 1f - u, boneIndex1 = m0, weight1 = u * (1f - t), boneIndex2 = m1, weight2 = u * t };
                }
                float w = (f - 0.5f) / 0.5f;
                return new BoneWeight { boneIndex0 = m0, weight0 = (1f - w) * (1f - t), boneIndex1 = m1, weight1 = (1f - w) * t, boneIndex2 = r0, weight2 = w * (1f - t), boneIndex3 = r1, weight3 = w * t };
            });
            const float y = 0.04f;
            // spokes
            for (int k = 0; k < N; k++)
            {
                kit.Paint(k % 3 == 0 ? worn : tar);
                kit.Tube(new[] { Ring(k, 0.03f, y), Ring(k, RN * 0.25f, y), Ring(k, RN * 0.5f, y), Ring(k, RN * 0.75f, y), Ring(k, RN - 0.01f, y) }, new[] { 0.030f, 0.028f, 0.028f, 0.028f, 0.028f }, 4);
            }
            // rings: three of cord, and the rim rope
            foreach (var (f, thick, colour) in new[] { (0.25f, 0.024f, tar), (0.5f, 0.026f, tar), (0.75f, 0.024f, worn), (1f, 0.042f, hemp) })
                for (int k = 0; k < N; k++)
                {
                    var p0 = Ring(k, RN * f, y);
                    var p1 = Ring(k + 1, RN * f, y);
                    kit.Paint(colour).Tube(new[] { p0, Vector3.Lerp(p0, p1, 0.5f), p1 }, new[] { thick, thick, thick }, 4);
                }
            // (and the half-way knots of the mesh between the outer rings, so it reads as net and not as a wheel)
            for (int k = 0; k < N; k++)
            {
                var a0 = Vector3.Lerp(Ring(k, RN * 0.5f, y), Ring(k + 1, RN * 0.5f, y), 0.5f);
                var b0 = Vector3.Lerp(Ring(k, RN * 0.75f, y), Ring(k + 1, RN * 0.75f, y), 0.5f);
                var c0 = Vector3.Lerp(Ring(k, RN, y), Ring(k + 1, RN, y), 0.5f);
                kit.Paint(tar).Tube(new[] { a0, b0, c0 }, new[] { 0.022f, 0.022f, 0.022f }, 4);
            }
            // a stone at every spoke, a cork between
            for (int k = 0; k < N; k++)
            {
                kit.Paint(stone).Egg(Ring(k, RN, y + 0.01f), new Vector3(0.07f, 0.055f, 0.07f), 6, 4);
                kit.Paint(cork).Egg(Vector3.Lerp(Ring(k, RN, y + 0.02f), Ring(k + 1, RN, y + 0.02f), 0.5f), new Vector3(0.05f, 0.04f, 0.05f), 5, 4);
            }
            // weed it has dragged up
            kit.Paint(weed).Tube(new[] { Ring(1, RN * 0.6f, y + 0.02f), Ring(1, RN * 0.72f, y + 0.03f) + new Vector3(0.05f, 0, 0.06f), Ring(2, RN * 0.8f, y + 0.02f) }, new[] { 0.02f, 0.026f, 0.012f }, 4);
            kit.Paint(weed).Tube(new[] { Ring(5, RN * 0.4f, y + 0.02f), Ring(5, RN * 0.55f, y + 0.03f) + new Vector3(-0.04f, 0, 0.05f) }, new[] { 0.022f, 0.012f }, 4);
            // what it has caught: the one thing that tells it from a net that is only a net
            if (live)
                foreach (var (k, f) in new[] { (0, 0.38f), (3, 0.62f), (6, 0.30f), (4, 0.82f) })
                    kit.Paint(gold, 1, 0.5f).Egg(Vector3.Lerp(Ring(k, RN * f, y + 0.035f), Ring(k + 1, RN * f, y + 0.035f), 0.4f), new Vector3(0.05f, 0.02f, 0.05f), 6, 3);
            kit.Wear("Net");
            c.nowHub = new Vector3(0, 0.04f, 0); c.nowMid = new Vector3(RN * 0.5f, 0.04f, 0); c.nowRim = new Vector3(RN, 0.04f, 0);
            return c;
        }

        public void Pose(ModelActor a, string anim, float n, float dt)
        {
            if (!looked) { looked = true; who = a.sr ? a.sr.GetComponentInParent<Dragnet>() : null; }
            time += dt;
            // the shape each state wants: (hub height), (mid radius, height), (rim radius, height)
            float hubY = 0.04f, midR = RN * 0.5f, midY = 0.04f, rimR = RN, rimY = 0.04f, wantMess = 0.35f, quick = 7f, dangle = 0f, turn = 0f;
            float jolt = who ? Mathf.Clamp01(who.Jolt / 0.3f) : 0f;
            switch (anim)
            {
                case "flat": break;
                case "spent": wantMess = 1f; quick = 14f; break;
                case "rise": hubY = 1.50f; midR = 0.40f; midY = 1.02f; rimR = 0.46f; rimY = 0.16f; dangle = 1f; quick = 5.5f; wantMess = 0f; break;
                case "creep":
                {
                    float g = 0.5f + 0.5f * Mathf.Sin(time * 4.5f);
                    hubY = Mathf.Lerp(0.85f, 1.35f, g); midR = Mathf.Lerp(0.62f, 0.42f, g); midY = Mathf.Lerp(0.45f, 0.9f, g); rimR = Mathf.Lerp(0.85f, 0.5f, g); rimY = Mathf.Lerp(0.05f, 0.14f, g);
                    dangle = 0.6f; wantMess = 0.2f; quick = 9f;
                    break;
                }
                case "cast":
                {
                    float k = who ? who.Flight : n;
                    float open = Mathf.Clamp01(k * 1.6f);
                    hubY = 0.75f; midR = Mathf.Lerp(0.35f, RN * 0.52f, open); midY = 0.70f; rimR = Mathf.Lerp(0.42f, RN * 1.06f, open); rimY = Mathf.Lerp(0.5f, 0.62f, open);
                    turn = 900f; quick = 18f; wantMess = 0f;
                    break;
                }
                case "wrap": hubY = 1.72f; midR = 0.36f; midY = 1.15f; rimR = 0.33f; rimY = 0.22f; dangle = 0.5f; quick = 16f; wantMess = 0f; break;
            }
            float e = 1f - Mathf.Exp(-quick * dt);
            nowHub = Vector3.Lerp(nowHub, new Vector3(0, hubY, 0), e);
            nowMid = Vector3.Lerp(nowMid, new Vector3(midR, midY, 0), e);
            nowRim = Vector3.Lerp(nowRim, new Vector3(rimR, rimY, 0), e);
            nowMess = Mathf.Lerp(nowMess, wantMess, e);
            spin += turn * dt;
            // hauling, the whole of it leans the way it is going
            Vector3 lean = Vector3.zero;
            if (who && who.Haul != Vector2.zero)
            {
                float yaw = a.yaw * Mathf.Deg2Rad;
                Vector2 ahead = new Vector2(Mathf.Sin(yaw), Mathf.Cos(yaw)), side = new Vector2(ahead.y, -ahead.x);
                lean = new Vector3(Vector2.Dot(who.Haul, side), 0, Vector2.Dot(who.Haul, ahead)) * (0.20f + 0.10f * Mathf.Sin(time * 3.6f));
            }
            var hp = nowHub + lean * 1.0f + new Vector3(jolt * Mathf.Sin(time * 60f) * 0.03f, 0, 0);
            hub.localPosition = hp;
            float sp = spin * Mathf.Deg2Rad;
            for (int k = 0; k < N; k++)
            {
                float ang = k * Mathf.PI * 2f / N + sp;
                // thrown down, it does not lie in a circle: some of the rim is folded in under itself
                float foldIn = 1f - nowMess * 0.42f * fold[k];
                float sway = dangle * 0.06f * Mathf.Sin(time * 2.4f + k * 1.7f) + jolt * 0.05f * Mathf.Sin(time * 50f + k);
                var m = new Vector3(Mathf.Cos(ang) * nowMid.x, nowMid.y, Mathf.Sin(ang) * nowMid.x) + lean * 0.55f;
                var r = new Vector3(Mathf.Cos(ang) * (nowRim.x * foldIn + sway), nowRim.y + dangle * 0.03f * Mathf.Sin(time * 3.1f + k * 2.3f), Mathf.Sin(ang) * (nowRim.x * foldIn + sway));
                mid[k].localPosition = m;
                rim[k].localPosition = r;
            }
        }
    }
}
