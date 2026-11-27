// Wicks. Every lamp on the Olive Terraces was left burning the night the city went down, and
// nobody has trimmed one since. After forty nights the flames stopped waiting and walked up to
// where the oil comes from. A Wick is a lamp flame as tall as a child, on the black stub it
// stands on. It has no face and no plans. It burns what it touches.
//
// A blade goes through it and only moves the air, which moves the flame: it can be driven, not
// cut. The mirror shield it will not go near. Driven up to a cold fire bowl it goes home, and
// the bowl is lit as if Azar had lit it himself, including the ones he cannot reach.
// The overhead chop that ends a combo takes the wick out from under it.
using UnityEngine;

namespace Wakefire
{
    public class Wick : Enemy
    {
        enum S { Feed, Hover, Dart, Shy, Home, Blown, Low }
        S s;
        Vector2 dir, roam, blown;
        float next, orbit, parted, ember;
        Prop bowl;
        LightBlob glow;
        Vector2 leapFrom;

        public static Wick Spawn(Vector2 at) => Make<Wick>("moth", "idle", at, WorldLayer.Waking, 1, "wick");

        protected override void Init()
        {
            speed = 2.6f; half = new Vector2(0.2f, 0.12f); touchDamage = 0; roams = true;
            orbit = Random.value * 6f;
            glow = LightBlob.Create(transform, pos, 3.4f, new Color(1f, 0.74f, 0.36f), 0.8f, true);
            glow.height = 0.6f;
            if (shadow) { Destroy(shadow.gameObject); shadow = null; }      // (it is the light: it has none)
        }

        public override bool Sleeps => false;

        protected override bool WaitsOutStories => true;
        protected override Color BurstColor => new Color(0.55f, 0.52f, 0.55f);
        protected override string HurtSound => "wick_out";
        /// <summary>How lately a blade went through it (the model opens round the cut).</summary>
        public float Parted => parted;
        /// <summary>Blown nearly out, and getting its height back.</summary>
        public bool Low => s == S.Low || s == S.Blown;
        /// <summary>In the air on its way into a bowl: how far through the leap (0 when it is not).</summary>
        public float Leap { get; private set; }

        /// <summary>Only the chop that comes straight down, or bronze thrown or thrown back, finds the wick.</summary>
        protected override bool Accepts(HitInfo h) => h.kind == HitKind.Heavy || h.kind == HitKind.Thrown || h.kind == HitKind.Reflected;

        /// <summary>A cut goes through a flame. It moves the air, and the air moves the flame.</summary>
        protected override bool Untouchable(HitInfo h)
        {
            if (Accepts(h) || s == S.Home) return s == S.Home;
            var away = (pos - (Vector2)h.from);
            blown = (away.sqrMagnitude > 0.001f ? away.normalized : Vector2.up) * 7.5f;
            s = S.Blown; stateClock = 0; parted = 0.3f;
            Sfx.Play("wick_whip", 0.6f, 0.12f);
            for (int i = 0; i < 5; i++)
                Fx.Spawn(pos + new Vector2(Random.Range(-0.15f, 0.15f), 0), blown * 0.25f + Random.insideUnitCircle, Random.Range(0.3f, 0.9f), Random.Range(0.5f, 2f),
                    Random.Range(0.2f, 0.4f), new Color(1f, 0.9f, 0.5f), new Color(0.95f, 0.35f, 0.1f), 6f);
            return true;
        }

        /// <summary>Fire does not stop for furniture: fences, bars, hedges, the edge of a terrace. A wall is a wall.</summary>
        void Drift(Vector2 v, float dt)
        {
            vel = v;
            var to = pos + v * dt;
            var box = new Rect(to - half, half * 2);
            foreach (var sd in Solids.All)
            {
                if (!sd.enabled || sd.pit || sd.low || !sd.r.Overlaps(box)) continue;
                if (sd.owner == this) continue;
                if (sd.owner is Prop pr && (pr.Kind == "bars" || pr.Kind == "brazier" || pr.Kind == "bush" || pr.Kind == "fence")) continue;
                if (sd.layer == WorldLayer.Dream) continue;
                // slide along whatever it was
                var tx = new Vector2(to.x, pos.y);
                var ty = new Vector2(pos.x, to.y);
                if (!sd.r.Overlaps(new Rect(tx - half, half * 2))) to = tx;
                else if (!sd.r.Overlaps(new Rect(ty - half, half * 2))) to = ty;
                else to = pos;
                box = new Rect(to - half, half * 2);
            }
            var m = Map.Current;
            if (m && !m.bounds.Contains(to)) to = pos;
            pos = to;
        }

        Prop ColdBowl(float within)
        {
            var map = Map.Current;
            if (!map) return null;
            Prop best = null;
            float bd = within;
            foreach (var pr in map.props)
            {
                if (!pr || pr.Kind != "brazier" || pr.lit || pr.data.layer == 2) continue;
                float d = Vector2.Distance(pr.basePos, pos);
                if (d < bd) { bd = d; best = pr; }
            }
            return best;
        }

        protected override void Think(float dt, Player p)
        {
            if (parted > 0) parted -= dt;
            next -= dt;
            if ((ember -= dt) <= 0) { ember = Random.Range(0.2f, 0.5f); Fx.Embers(pos + new Vector2(Random.Range(-0.1f, 0.1f), 0.2f), 1); }
            glow.transform.position = pos;
            var d = p.pos - pos;
            bool sees = CanSee(p, 6.5f);
            if (sees && Story.I) Story.I.WickSeen();
            // the mirror: it will not go near its own light coming back at it
            bool shied = sees && p.Guarding && d.magnitude < 3.6f && Vector2.Dot(p.Dir, -d.normalized) > 0.25f;

            if (s != S.Home && s != S.Blown)
            {
                // a cold bowl within a stride: home
                var b = ColdBowl(1.6f);
                if (b) { bowl = b; s = S.Home; stateClock = 0; leapFrom = pos; anim.Play("leap", facing, true); Sfx.Play("wick_leap", 0.8f, 0.08f); }
                else if (shied && s != S.Shy) { s = S.Shy; stateClock = 0; }
            }

            switch (s)
            {
                case S.Feed:
                    anim.Play("idle", facing);
                    if (sees && d.magnitude < 5.5f) { s = S.Hover; stateClock = 0; next = Random.Range(0.8f, 1.6f); break; }
                    if (next <= 0)
                    {
                        next = Random.Range(1.2f, 3f);
                        roam = Vector2.Distance(pos, home) > 3.5f ? (home - pos).normalized : Random.value < 0.5f ? Vector2.zero : Random.insideUnitCircle.normalized;
                    }
                    if (roam != Vector2.zero) Drift(roam * speed * 0.5f, dt); else vel = Vector2.zero;
                    break;

                case S.Hover:
                {
                    if (!sees) { s = S.Feed; break; }
                    // round him at a little distance, the way a flame goes round a draught
                    orbit += dt * 1.3f;
                    var want = p.pos + new Vector2(Mathf.Cos(orbit), Mathf.Sin(orbit) * 0.7f) * 2.7f - pos;
                    Drift(want.normalized * Mathf.Min(speed * 1.25f, want.magnitude * 3f), dt);
                    if (next <= 0 && d.magnitude < 3.6f)
                    {
                        s = S.Dart; stateClock = 0; dir = d.normalized;
                        anim.Play("dart", facing, true);
                        Sfx.Play("wick_dart", 0.7f, 0.1f);
                    }
                    break;
                }

                case S.Dart:
                    // a short breath in, then straight through where he was standing
                    if (stateClock < 0.22f) { vel = Vector2.zero; break; }
                    Drift(dir * 8.2f * Mathf.Lerp(1f, 0.35f, (stateClock - 0.22f) / 0.5f), dt);
                    if (Present && Vector2.Distance(pos, p.pos) < 0.5f && Mathf.Abs(pos.y - p.pos.y) < 0.45f)
                        p.Hurt(new HitInfo { damage = 1, from = pos, knockback = 5f, kind = HitKind.Fire, source = gameObject });
                    if (stateClock > 0.72f) { s = S.Hover; stateClock = 0; next = Random.Range(1.3f, 2.4f); anim.Play("idle", facing, true); }
                    break;

                case S.Shy:
                    // it keeps the mirror at arm's length and goes the way the mirror is pointed
                    if (!shied && stateClock > 0.35f) { s = S.Hover; stateClock = 0; next = 1.4f; break; }
                    {
                        var awayFrom = -d.normalized;
                        var go = (awayFrom * 0.7f + p.Dir * 0.6f).normalized;
                        float keep = Mathf.InverseLerp(3.4f, 1.2f, d.magnitude);
                        Drift(go * Mathf.Lerp(1.2f, 5.2f, keep), dt);
                    }
                    break;

                case S.Blown:
                    Drift(blown, dt);
                    blown *= Mathf.Exp(-6f * dt);
                    if (stateClock > 0.45f) { s = S.Low; stateClock = 0; }
                    break;

                case S.Low:
                    // blown nearly out: it stays where the wind left it until it has its height back
                    vel = Vector2.zero;
                    if (stateClock > 1.0f) { s = S.Hover; stateClock = 0; next = 1.2f; }
                    break;

                case S.Home:
                {
                    if (!bowl || bowl.lit) { s = S.Hover; Leap = 0; hover = 0; break; }
                    float k = Mathf.Clamp01(stateClock / 0.42f);
                    Leap = Mathf.Max(0.001f, k);
                    pos = Vector2.Lerp(leapFrom, bowl.basePos + new Vector2(0, -0.04f), k);
                    hover = Mathf.Sin(k * Mathf.PI) * 0.9f + k * 0.75f;
                    vel = Vector2.zero;
                    if (k >= 1f)
                    {
                        if (!Sky.WetAt(bowl.basePos) && bowl.Ignite())
                        {
                            Sfx.Play("ignite");
                            Fx.Embers(bowl.basePos + new Vector2(0, 1f), 12);
                            if (p) p.Notify(bowl);
                        }
                        if (spawnId != null) Story.Set("dead_" + spawnId);
                        if (Story.I) Story.I.WickHome(this, bowl);
                        Rooms.Slain(this);
                        Destroy(gameObject);
                    }
                    break;
                }
            }
            // a cold bowl close by draws it, whatever else it was doing: it remembers what a bowl is for
            if (s != S.Home && s != S.Dart)
            {
                var drawn = ColdBowl(3.4f);
                if (drawn)
                {
                    var keep = vel;
                    Drift((drawn.basePos - pos).normalized * 1.7f, dt);
                    vel = keep + (drawn.basePos - pos).normalized * 1.7f;
                }
            }
            if (s != S.Home)
            {
                hover = 0;
                if (vel.sqrMagnitude > 0.05f) facing = FaceOf(vel);
                if (anim.anim != "dart" || s != S.Dart) anim.Play(s == S.Feed && vel == Vector2.zero ? "idle" : "walk", facing);
            }
        }

        public override void Blocked(Player p)
        {
            // off the bronze, and it does not come back for a while
            blown = (pos - p.pos).normalized * 9f;
            s = S.Blown; stateClock = -0.2f;
            Sfx.Play("reflect", 0.6f, 0.08f);
        }

        protected override void Die()
        {
            // the wick is cut: what is left is smoke
            for (int i = 0; i < 12; i++)
                Fx.Spawn(pos + new Vector2(Random.Range(-0.12f, 0.12f), 0), new Vector2(Random.Range(-0.4f, 0.4f), 0.3f), Random.Range(0.2f, 0.7f), Random.Range(0.6f, 1.6f),
                    Random.Range(0.6f, 1.2f), new Color(0.70f, 0.68f, 0.70f, 0.9f), new Color(0.3f, 0.3f, 0.34f, 0f), -0.8f, i % 3 == 0 ? 2 : 1);
            Sfx.Play("wick_out", 0.9f, 0.05f);
            Pickup.Chance(pos, 0.5f, 0.2f);
            if (spawnId != null) Story.Set("dead_" + spawnId);
            Destroy(gameObject);
        }
    }

    // ------------------------------------------------------------------------------- the model
    /// <summary>A lamp flame as tall as a child, on the black stub it stands on: blue where it leaves the
    /// wick, white above that, yellow, and red at the tip. Three joints up its length, so that it trails
    /// behind the way it is going and leans back into a draught.</summary>
    public class WickProp : IPoser
    {
        Transform stub, f0, f1, f2, lickA, lickB, t0, t1;
        Vector2 trail;
        Wick who;
        bool looked;
        float time, flick;
        Vector2 lean;
        float tall = 1f, part;

        static Transform Bone(string name, Transform parent, Vector3 at)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = at;
            return go.transform;
        }

        public static WickProp Make(ModelActor a)
        {
            var c = new WickProp();
            var rig = a.rig;
            c.stub = Bone("stub", rig, Vector3.zero);
            c.f0 = Bone("f0", c.stub, new Vector3(0, 0.13f, 0));
            c.f1 = Bone("f1", c.f0, new Vector3(0, 0.22f, 0));
            c.f2 = Bone("f2", c.f1, new Vector3(0, 0.22f, 0));
            c.lickA = Bone("lickA", c.f0, new Vector3(-0.07f, 0.10f, 0));
            c.lickB = Bone("lickB", c.f0, new Vector3(0.08f, 0.06f, 0));
            c.t0 = Bone("t0", rig, new Vector3(0, 0.02f, -0.03f));
            c.t1 = Bone("t1", c.t0, new Vector3(0, 0, -0.17f));
            var bones = new[] { c.stub, c.f0, c.f1, c.f2, c.lickA, c.lickB, c.t0, c.t1 };
            foreach (var t in bones) a.bones[t.name] = t;

            Color black = new Color(0.05f, 0.04f, 0.05f), char2 = new Color(0.16f, 0.10f, 0.08f), coal = new Color(1f, 0.38f, 0.10f);
            Color blue = new Color(0.30f, 0.52f, 1f), white = new Color(1f, 0.98f, 0.84f), yellow = new Color(1f, 0.84f, 0.34f), orange = new Color(1f, 0.56f, 0.14f), red = new Color(0.95f, 0.28f, 0.08f);
            var kit = new Kit(a, rig, bones);
            // the stub: a twist of burnt flax, thicker where it was dipped, one red point at the top
            kit.On("stub").Paint(black).Stain(p => p.y < 0.035f ? char2 : (Color?)null);
            kit.Tube(new[] { new Vector3(0.012f, 0, 0), new Vector3(-0.012f, 0.06f, 0.006f), new Vector3(0.008f, 0.12f, -0.004f), new Vector3(0, 0.17f, 0) }, new[] { 0.034f, 0.028f, 0.024f, 0.012f }, 6);
            kit.Stain(null);
            kit.Paint(coal, 0, 1.8f).Egg(new Vector3(0, 0.165f, 0), Vector3.one * 0.022f, 5, 4);
            // the rest of the wick: flax that has not burnt yet, dragging behind it, paler the further from the fire
            Color flax = new Color(0.66f, 0.58f, 0.40f), singed = new Color(0.30f, 0.22f, 0.16f);
            kit.On("t0").Paint(singed).Tube(new[] { new Vector3(0, 0.03f, -0.02f), new Vector3(0, 0.022f, -0.20f) }, new[] { 0.026f, 0.022f }, 5);
            kit.On("t1").Paint(flax).Tube(new[] { new Vector3(0, 0.022f, -0.20f), new Vector3(0.01f, 0.02f, -0.30f), new Vector3(-0.01f, 0.016f, -0.40f) }, new[] { 0.022f, 0.020f, 0.012f }, 5);
            kit.Wear("Stub");

            // the flame: one skin from root to tip, shared between the three joints by height
            var fk = new Kit(a, rig, bones);
            int i0 = 1, i1 = 2, i2 = 3;         // f0, f1, f2 in the bone list
            fk.On(p =>
            {
                float y = p.y;
                if (y < 0.35f) { float k = Mathf.InverseLerp(0.13f, 0.35f, y); return new BoneWeight { boneIndex0 = i0, weight0 = 1f - k * 0.5f, boneIndex1 = i1, weight1 = k * 0.5f }; }
                if (y < 0.57f) { float k = Mathf.InverseLerp(0.35f, 0.57f, y); return new BoneWeight { boneIndex0 = i1, weight0 = 1f - k * 0.5f, boneIndex1 = i2, weight1 = k * 0.5f }; }
                return new BoneWeight { boneIndex0 = i2, weight0 = 1 };
            });
            (float r, float y)[] prof =
            {
                (0.010f, 0.115f), (0.060f, 0.14f), (0.105f, 0.20f), (0.128f, 0.28f), (0.126f, 0.36f), (0.108f, 0.45f),
                (0.084f, 0.54f), (0.058f, 0.63f), (0.034f, 0.72f), (0.014f, 0.80f), (0.002f, 0.86f),
            };
            Color[] ring = { blue, blue, white, white, yellow, yellow, orange, orange, red, red, red };
            fk.Paint(white, 0, 2.6f).Turned(Vector3.zero, prof, 10, 0.8f, 0, 360, (i, j) => ring[i]);
            c.flame = fk.Wear("Flame");
            // two tongues that come and go at its sides
            foreach (var (bone, x, y0) in new[] { ("lickA", -0.085f, 0.20f), ("lickB", 0.09f, 0.17f) })
            {
                var lk = new Kit(a, rig, bones);
                lk.On(bone).Paint(orange, 0, 2.4f).Turned(new Vector3(x, 0, 0), new[] { (0.006f, y0), (0.040f, y0 + 0.05f), (0.034f, y0 + 0.12f), (0.014f, y0 + 0.20f), (0.002f, y0 + 0.26f) }, 6, 0.8f, 0, 360,
                    (i, j) => i < 2 ? yellow : i < 4 ? orange : red);
                if (bone == "lickA") c.rA = lk.Wear("LickA"); else c.rB = lk.Wear("LickB");
            }
            return c;
        }

        Renderer flame, rA, rB;

        public void Pose(ModelActor a, string anim, float n, float dt)
        {
            if (!looked) { looked = true; who = a.sr ? a.sr.GetComponentInParent<Wick>() : null; }
            time += dt;
            // fire does not move smoothly: twelve shapes a second
            if ((flick -= dt) <= 0) flick = 1f / 12f;
            float t = Mathf.Floor(time * 12f);
            float n1 = Mathf.PerlinNoise(t * 0.37f, 1.3f) - 0.5f, n2 = Mathf.PerlinNoise(t * 0.53f, 7.1f) - 0.5f, n3 = Mathf.PerlinNoise(t * 0.71f, 3.9f) - 0.5f;
            // it trails behind the way it is going (the creature's own frame: x right, z ahead)
            float yaw = a.yaw * Mathf.Deg2Rad;
            Vector2 v = a.velocity / a.def.scale;
            Vector2 ahead = new Vector2(Mathf.Sin(yaw), Mathf.Cos(yaw)), side = new Vector2(ahead.y, -ahead.x);
            var want = new Vector2(Vector2.Dot(v, side), Vector2.Dot(v, ahead)) * -9f;
            want = Vector2.ClampMagnitude(want, 46f);
            lean = Vector2.Lerp(lean, want, 1f - Mathf.Exp(-9f * dt));
            float dart = anim == "dart" ? 1f : 0f, leap = who ? who.Leap : anim == "leap" ? n : 0f;
            float wantTall = who && who.Low ? 0.55f : anim == "dart" ? (n < 0.3f ? 0.72f : 1.35f) : leap > 0 ? 1.25f : 1f + n1 * 0.22f;
            tall = Mathf.Lerp(tall, wantTall, 1f - Mathf.Exp(-16f * dt));
            part = Mathf.Lerp(part, who && who.Parted > 0 ? 1f : anim == "part" ? 1f : 0f, 1f - Mathf.Exp(-20f * dt));

            stub.localRotation = Quaternion.Euler(lean.y * 0.12f, 0, -lean.x * 0.12f);
            // the tail lies where it has just been: straight back when it is going, wandering a little when it is not
            var back = new Vector2(Vector2.Dot(v, side), Vector2.Dot(v, ahead));
            trail = Vector2.Lerp(trail, back.sqrMagnitude > 0.01f ? back.normalized : new Vector2(Mathf.Sin(time * 0.7f) * 0.5f, 1f).normalized, 1f - Mathf.Exp(-5f * dt));
            float swing = Mathf.Atan2(-trail.x, trail.y) * Mathf.Rad2Deg;
            t0.localRotation = Quaternion.Euler(0, swing * 0.6f, 0);
            t1.localRotation = Quaternion.Euler(0, swing * 0.5f + Mathf.Sin(time * 3f) * 6f, 0);
            f0.localRotation = Quaternion.Euler(lean.y * 0.30f + n2 * 8f, 0, -lean.x * 0.30f + n1 * 9f + part * 16f);
            f1.localRotation = Quaternion.Euler(lean.y * 0.40f + n3 * 12f, 0, -lean.x * 0.40f + n2 * 13f - part * 22f);
            f2.localRotation = Quaternion.Euler(lean.y * 0.45f + n1 * 16f, 0, -lean.x * 0.45f + n3 * 18f);
            f0.localScale = new Vector3(1f + n3 * 0.10f + part * 0.25f, Mathf.Lerp(1f, tall, 0.5f), 1f + n3 * 0.10f);
            f1.localScale = new Vector3(1f, tall, 1f);
            f2.localScale = new Vector3(1f, tall, 1f);
            // the tongues: there, not there
            if (rA) rA.enabled = Mathf.Repeat(t * 0.37f + 0.2f, 1f) < 0.55f;
            if (rB) rB.enabled = Mathf.Repeat(t * 0.29f + 0.6f, 1f) < 0.45f;
            lickA.localRotation = Quaternion.Euler(0, 0, 14f + n2 * 20f);
            lickB.localRotation = Quaternion.Euler(0, 0, -12f + n1 * 20f);
        }
    }
}
