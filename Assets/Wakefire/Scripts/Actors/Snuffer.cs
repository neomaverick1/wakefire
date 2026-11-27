// The Snuffer. The lamp seller of the gate square has had one bad dream every night for forty
// nights: the thing he puts his lamps out with, grown as tall as a doorway, walking about on its
// own account and putting out everything else. It is bronze. It has three legs, no face, and a
// ring where the handle used to hook on. It goes for the nearest flame, stands over it, and
// comes down.
//
// It cannot be hurt while it is on its feet: a bell is a bell, and rings. Up on its legs over
// its prey it is all balance, and a blow then puts it on its side, where the open end is the
// way in. Whatever it has put out is still burning inside it, and goes home when it breaks.
//
// The Wakefire never goes out. A Snuffer that comes down over the man carrying it finds that
// out from the inside.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Snuffer : Enemy
    {
        public enum S { Stand, Sniff, Walk, Rear, Drop, Cover, Rise, Tipped, Up }
        public S s { get; private set; }
        Prop prey;                              // the fire it is after...
        bool onAzar;                            // ...or it is his
        Vector2 mark, from;                     // where it is coming down, and where it stood before it stepped over
        readonly List<string> eaten = new List<string>();     // the ids of the fires inside it
        int unnamed;                            // (and any that had no name)
        bool holding;                           // Azar is under it
        int rings;
        float scan, wander, smoke, heat, cool;
        Vector2 roam;
        Color nightWas;
        bool darkened;
        LightBlob glow;
        public static bool Told;

        public const float Mouth = 0.69f;       // the radius of the open end, in tiles

        public static Snuffer Spawn(Vector2 at) => Make<Snuffer>("moth", "idle", at, WorldLayer.Waking, 3, "snuffer");

        protected override void Init()
        {
            speed = 1.9f; half = new Vector2(0.5f, 0.22f); touchDamage = 0; roams = true;
            glow = LightBlob.Create(transform, pos, 2.2f, new Color(1f, 0.42f, 0.14f), 0f, true);
            glow.height = 0.2f;
        }

        /// <summary>How many fires are inside it (the model shows it: a red line under the rim, a red throat).</summary>
        public int Hot => eaten.Count + unnamed;
        /// <summary>It has something in mind (the mouth comes round to face it).</summary>
        public bool Hunting => prey || onAzar;
        /// <summary>How long it has been rung from inside, lately (the model jolts).</summary>
        public float Jolt { get; private set; }
        public bool Holding => holding;

        public override bool Sleeps => false;                 // (it has nothing to sleep with)

        protected override bool WaitsOutStories => true;
        protected override float KnockScale => s == S.Tipped ? 0.25f : 0f;
        protected override string HurtSound => "snuffer_ring";
        protected override Color BurstColor => new Color(0.85f, 0.55f, 0.22f);
        public override Rect HitBox => s == S.Tipped
            ? new Rect(pos.x - 1.3f, pos.y - 0.3f, 2.6f, 1.6f)
            : new Rect(pos.x - 0.75f, pos.y - 0.25f, 1.5f, 2.6f);

        /// <summary>On its feet it only rings. Up on its legs it can be put over; on its side the open end is the way in.</summary>
        protected override bool Accepts(HitInfo h)
        {
            if (s == S.Tipped) return true;
            if (s == S.Rear && !holding) { Topple(((Vector2)h.from - pos).x > 0 ? -1 : 1); return false; }
            Sfx.Play("snuffer_ring", 0.7f, 0.06f);
            Noise.Make(pos, 10f);
            Jolt = 0.25f;
            return false;
        }

        void Topple(int side)
        {
            s = S.Tipped; stateClock = 0;
            anim.Play("tipped", side > 0 ? Facing.Right : Facing.Left, true);
            if (anim.model) anim.model.Aim(side > 0 ? Vector2.right : Vector2.left, true);
            Sfx.Play("snuffer_fall", 1f, 0.04f);
            Noise.Make(pos, 9f);
            PixelView.I.Shake(2, 0.22f);
            Fx.Dust(pos, 10);
            prey = null; onAzar = false;
        }

        /// <summary>The nearest thing burning: a lit bowl first, the man with the flame after.</summary>
        void Choose(Player p)
        {
            prey = null; onAzar = false;
            var map = Map.Current;
            float best = 15f;
            if (map)
                foreach (var pr in map.props)
                {
                    if (!pr || pr.Kind != "brazier" || !pr.lit) continue;
                    if (pr.data.layer == 2) continue;
                    float d = Vector2.Distance(pr.basePos, pos);
                    if (d < best) { best = d; prey = pr; }
                }
            if (cool <= 0 && p && p.hasLantern && CanSee(p, prey ? Mathf.Min(best, 5.5f) : 7.5f)) { prey = null; onAzar = true; }
        }

        protected override void Think(float dt, Player p)
        {
            cool -= dt;
            if (Jolt > 0) Jolt -= dt;
            if (Story.I && CanSee(p, 7f)) Story.I.SnufferSeen();
            switch (s)
            {
                case S.Stand:
                    anim.Play("idle", facing);
                    if ((scan -= dt) <= 0) { scan = 0.45f; Choose(p); }
                    if (Hunting)
                    {
                        s = S.Sniff; stateClock = 0;
                        Turn(Target(p) - pos);
                        anim.Play("sniff", facing, true);
                        Sfx.Play("snuffer_sniff", 0.7f, 0.08f);
                        break;
                    }
                    // nothing burning: it walks its rounds, the way he does at closing time
                    if ((wander -= dt) <= 0)
                    {
                        wander = Random.Range(1.6f, 3.8f);
                        roam = Vector2.Distance(pos, home) > 4f ? (home - pos).normalized : Random.value < 0.4f ? Vector2.zero : Random.insideUnitCircle.normalized;
                    }
                    if (roam != Vector2.zero) { Turn(roam); anim.Play("walk", facing); Move(roam * speed * 0.6f, dt); }
                    break;

                case S.Sniff:
                    Turn(Target(p) - pos);
                    if (stateClock > 0.7f) { s = S.Walk; stateClock = 0; }
                    break;

                case S.Walk:
                {
                    if ((scan -= dt) <= 0) { scan = 0.6f; bool was = onAzar; var old = prey; Choose(p); if (!Hunting) { s = S.Stand; break; } if (was != onAzar || old != prey) stateClock = 0; }
                    if (prey && !prey.lit) { prey = null; s = S.Stand; break; }
                    var to = Target(p) - pos;
                    Turn(to);
                    anim.Play("walk", facing);
                    float pace = speed + Mathf.Min(3, Hot) * 0.3f;
                    Move(to.normalized * pace, dt);
                    if (to.magnitude < (onAzar ? 1.15f : 1.5f))
                    {
                        s = S.Rear; stateClock = 0;
                        from = pos; mark = Target(p);
                        anim.Play("rear", facing, true);
                        Sfx.Play("snuffer_rear", 0.8f, 0.05f);
                    }
                    break;
                }

                case S.Rear:
                    // up on its legs and over: a bowl stays where it is; a man does not, and for the first of it the bell follows
                    if (onAzar && stateClock < 0.38f) mark = Vector2.MoveTowards(mark, p.pos, 4.2f * dt);
                    pos = Vector2.MoveTowards(pos, mark + (prey ? new Vector2(0, -0.06f) : Vector2.zero), 4.5f * dt);
                    if (stateClock > 0.72f) { s = S.Drop; stateClock = 0; anim.Play("drop", facing, true); }
                    break;

                case S.Drop:
                    if (stateClock > 0.13f) Land(p);
                    break;

                case S.Cover:
                    if (holding) { Held(dt, p); break; }
                    if ((smoke -= dt) <= 0 && prey == null && Hot > 0) { smoke = 0.12f; Wisp(); }
                    if (stateClock > (Hot > 0 ? 1.0f : 0.6f)) { s = S.Rise; stateClock = 0; anim.Play("rise", facing, true); Sfx.Play("snuffer_rear", 0.5f, 0.05f); }
                    break;

                case S.Rise:
                    pos = Vector2.MoveTowards(pos, from, 2.4f * dt);
                    if (stateClock > 0.6f && Vector2.Distance(pos, from) < 0.05f) { s = S.Stand; stateClock = 0; scan = 0.4f; }
                    break;

                case S.Tipped:
                    if ((smoke -= dt) <= 0 && Hot > 0) { smoke = 0.2f; Wisp(); }
                    if (stateClock > 3.4f) { s = S.Up; stateClock = 0; anim.Play("up", facing, true); Sfx.Play("snuffer_rear", 0.6f, 0.05f); }
                    break;

                case S.Up:
                    if (stateClock > 0.7f) { s = S.Stand; stateClock = 0; cool = 1.2f; }
                    break;
            }
            glow.transform.position = pos;
            glow.intensity = Mathf.MoveTowards(glow.intensity, Hot > 0 && s != S.Cover ? Mathf.Min(0.7f, 0.25f + 0.15f * Hot) : holding ? 0.35f + heat * 0.5f : 0f, dt * 2f);
        }

        Vector2 Target(Player p) => prey ? prey.basePos : onAzar && p ? p.pos : pos + Vector2.down;

        void Turn(Vector2 d)
        {
            if (d.sqrMagnitude < 0.0004f) return;
            facing = FaceOf(d);
            if (anim.model) anim.model.Aim(d);
        }

        void Wisp() =>
            Fx.Spawn(pos + new Vector2(Random.Range(-Mouth, Mouth), 0.05f), new Vector2(Random.Range(-0.3f, 0.3f), 0.2f), 0.1f, Random.Range(0.4f, 1.1f),
                Random.Range(0.5f, 0.9f), new Color(0.62f, 0.60f, 0.62f, 0.9f), new Color(0.25f, 0.24f, 0.28f, 0f), -0.6f);

        void Land(Player p)
        {
            s = S.Cover; stateClock = 0; rings = 0; heat = 0;
            anim.Play("cover", facing, true);
            Sfx.Play("snuffer_clang", 1f, 0.03f);
            Noise.Make(pos, 12f);
            PixelView.I.Shake(2, 0.2f);
            for (int i = 0; i < 12; i++)
            {
                float a = i / 12f * Mathf.PI * 2f;
                var d = new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.5f);
                Fx.Spawn(pos + d * Mouth, d * 1.6f, 0.05f, Random.Range(0.3f, 1.0f), Random.Range(0.3f, 0.5f), new Color(0.78f, 0.72f, 0.80f, 0.9f), new Color(0.5f, 0.46f, 0.56f, 0f), 4f);
            }
            if (prey)
            {
                if (prey.lit && prey.Snuff())
                {
                    if (!string.IsNullOrEmpty(prey.data.id)) eaten.Add(prey.data.id); else unnamed++;
                    Sfx.Play("snuffer_hiss", 0.9f, 0.05f);
                    if (Story.I) Story.I.Snuffed(prey);
                }
                prey = null;
                return;
            }
            if (!onAzar || !p || !Present) return;
            onAzar = false;
            float d2 = Vector2.Distance(p.pos, pos);
            if (d2 < 0.5f && p.GoUnder(this)) { holding = true; Dark(true); Sfx.Play("snuffer_hiss", 0.6f, 0.05f); }
            else if (d2 < Mouth + 0.35f)
                p.Hurt(new HitInfo { damage = 1, from = pos, knockback = 7f, kind = HitKind.Crush, source = gameObject });
        }

        /// <summary>He is under it, in the dark, with the one flame in Ashkel it cannot put out. Ringing it from inside
        /// gets him out sooner; either way it ends with the Snuffer on its side.</summary>
        void Held(float dt, Player p)
        {
            heat = Mathf.Clamp01(stateClock / 2.6f);
            if (Controls.Down(Controls.Attack) || Controls.Down(Controls.Interact) || Controls.Down(Controls.Item))
            {
                rings++;
                Jolt = 0.3f;
                Sfx.Play("snuffer_ring", 1f, 0.03f);
                Noise.Make(pos, 10f);
                PixelView.I.Shake(2, 0.14f);
                Fx.Sparks(pos + new Vector2(0, 1.0f), new Color(1f, 0.8f, 0.4f), 5);
            }
            if ((smoke -= dt) <= 0) { smoke = Mathf.Lerp(0.22f, 0.05f, heat); Wisp(); }
            bool rung = rings >= 3, cooked = stateClock > 2.6f;
            if (!rung && !cooked) return;
            holding = false;
            Dark(false);
            int side = Random.value < 0.5f ? -1 : 1;
            p.ComeOut(pos + new Vector2(-side * 0.2f, -0.1f));
            if (cooked)
            {
                p.health.invulnerable = 0;
                p.Hurt(new HitInfo { damage = 1, from = pos + Vector2.up * 0.2f, knockback = 3f, kind = HitKind.Crush, source = gameObject });
            }
            Fx.Embers(pos + new Vector2(0, 0.5f), 12);
            Topple(side);
            if (!Told && Story.I && !Story.I.Running) { Told = true; Story.I.SnufferMetTheWakefire(cooked); }
        }

        void Dark(bool on)
        {
            var v = PixelView.I;
            if (!v || on == darkened) return;
            darkened = on;
            if (on) { nightWas = v.ambient; v.ambient = new Color(0.035f, 0.03f, 0.045f); }
            else v.ambient = nightWas;
        }

        protected override void OnHurt(HitInfo h)
        {
            Fx.Sparks(pos + new Vector2(0, 0.7f), new Color(1f, 0.82f, 0.45f), 9);
            Jolt = 0.3f;
            stateClock = Mathf.Min(stateClock, 2.2f);           // every blow keeps it down a little longer
        }

        protected override void Die()
        {
            Dark(false);
            // what it put out goes home
            var map = Map.Current;
            if (map)
                foreach (var id in eaten)
                    foreach (var pr in map.props)
                        if (pr && pr.Kind == "brazier" && pr.data.id == id) { HomingFlame.Send(pos + new Vector2(0, 0.6f), pr); break; }
            for (int i = 0; i < 16; i++)
                Fx.Spawn(pos + new Vector2(Random.Range(-0.6f, 0.6f), 0), Random.insideUnitCircle * 4.2f, Random.Range(0.3f, 1.4f), Random.Range(2f, 6f),
                    Random.Range(0.5f, 0.9f), new Color(0.95f, 0.72f, 0.32f), new Color(0.35f, 0.22f, 0.10f), 18f, i % 3 == 0 ? 2 : 1);
            Sfx.Play("snuffer_break", 1f, 0.03f);
            PixelView.I.Shake(3, 0.25f);
            if (glow) glow.intensity = 0;
            for (int i = 0; i < 2 + Hot; i++) Pickup.Drop(Pickup.Kind.Shekel, pos + Random.insideUnitCircle * 0.6f);
            base.Die();
        }

        /// <summary>Run in, by a man who is asleep, for being abroad after dark without a light: it goes to the lock-up,
        /// and what it had on it is returned to its owners.</summary>
        public void Nicked()
        {
            Dark(false);
            var map = Map.Current;
            if (map)
                foreach (var id in eaten)
                    foreach (var pr in map.props)
                        if (pr && pr.Kind == "brazier" && pr.data.id == id) { HomingFlame.Send(pos + new Vector2(0, 0.6f), pr); break; }
            Fx.Dust(pos, 12);
            Sfx.Play("snuffer_fall", 0.5f, 0.05f);
            if (glow) glow.intensity = 0;
            Story.Set("nicked_snuffer");
            if (spawnId != null) Story.Set("dead_" + spawnId);
            Rooms.Slain(this);
            Destroy(gameObject);
        }

        protected override void OnDestroy()
        {
            Dark(false);
            if (holding && Player.I) Player.I.ComeOut(pos);
            base.OnDestroy();
        }
    }

    /// <summary>A flame on its way home to the bowl it was taken from.</summary>
    public class HomingFlame : MonoBehaviour
    {
        Prop to;
        Vector2 at, vel;
        float z, clock;
        LightBlob light;

        public static void Send(Vector2 from, Prop home)
        {
            var go = new GameObject("Flame going home");
            go.transform.SetParent(Map.Current ? Map.Current.transform : null, false);
            var f = go.AddComponent<HomingFlame>();
            f.to = home; f.at = from; f.z = 0.6f;
            f.vel = Random.insideUnitCircle.normalized * 5f + Vector2.up * 2f;
            f.light = LightBlob.Create(go.transform, from, 1.6f, new Color(1f, 0.70f, 0.32f), 0.7f, true);
        }

        void Update()
        {
            if (Game.Paused) return;
            float dt = Time.deltaTime;
            clock += dt;
            if (!to) { Destroy(gameObject); return; }
            var want = to.basePos + new Vector2(0, 0.1f) - at;
            // out in a curl, then straight home, faster the longer it has been out
            vel = Vector2.Lerp(vel, want.normalized * (5f + clock * 6f), 1f - Mathf.Exp(-(1.5f + clock * 4f) * dt));
            at += vel * dt;
            z = Mathf.Lerp(z, 1.0f, dt * 3f);
            light.transform.position = at;
            light.height = z;
            for (int i = 0; i < 2; i++)
                Fx.Spawn(at + Random.insideUnitCircle * 0.08f, -vel * 0.1f + Random.insideUnitCircle * 0.3f, z, Random.Range(0.2f, 0.8f), Random.Range(0.18f, 0.4f),
                    new Color(1f, 0.92f, 0.55f), new Color(0.95f, 0.35f, 0.10f), -1.5f, i == 0 ? 2 : 1);
            if (want.magnitude < 0.25f || clock > 6f)
            {
                if (to.Ignite()) { Sfx.Play("ignite", 0.8f, 0.06f); Fx.Embers(to.basePos + new Vector2(0, 1f), 8); if (Player.I) Player.I.Notify(to); }
                Destroy(gameObject);
            }
        }
    }

    // ------------------------------------------------------------------------------- the model
    /// <summary>A bell big enough to put a man out, on three legs that come out of its rim like the legs of a
    /// stand. Metres, in its own frame: x to its right, y up, z the way it is going.</summary>
    public class SnufferProp : IPoser
    {
        Transform bell;
        readonly Transform[] upper = new Transform[3], lower = new Transform[3];
        readonly Vector3[] hip = new Vector3[3], rest = new Vector3[3], outw = new Vector3[3];
        readonly bool[] down = { true, true, true };
        Renderer ember;
        Snuffer who;
        bool looked;
        float time, phase, moving, back, lift = WalkH, over, sway;

        const float R = 0.52f, Tall = 1.50f;              // the mouth's radius, and how tall the bell is
        const float U = 0.50f, L = 1.00f;                 // the bracket out of the rim, and the leg down from it
        const float WalkH = 0.50f, RearH = 1.02f;         // how high it carries its mouth: walking, and up on its legs over its prey
        const float Foot = 1.02f, Stride = 0.62f, Duty = 0.70f;
        static readonly float[] Angle = { 32f, 148f, 270f };   // two legs in front, one behind

        static Transform Bone(string name, Transform parent, Vector3 at)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = at;
            return go.transform;
        }

        static float Hash(float x) => Mathf.Repeat(Mathf.Sin(x * 127.1f) * 43758.5453f, 1f);

        public static SnufferProp Make(ModelActor a)
        {
            var c = new SnufferProp();
            var rig = a.rig;
            var at = new Vector3(0, WalkH, 0);
            c.bell = Bone("bell", rig, at);
            var bones = new List<Transform> { c.bell };
            for (int i = 0; i < 3; i++)
            {
                float an = Angle[i] * Mathf.Deg2Rad;
                c.outw[i] = new Vector3(Mathf.Cos(an), 0, Mathf.Sin(an));
                c.hip[i] = c.outw[i] * (R - 0.01f) + new Vector3(0, 0.10f, 0);
                c.rest[i] = c.outw[i] * Foot;
                var h = at + c.hip[i];
                c.upper[i] = Bone("su" + i, rig, h);
                c.lower[i] = Bone("sl" + i, rig, h + c.outw[i] * U);
                bones.Add(c.upper[i]);
                bones.Add(c.lower[i]);
            }
            foreach (var t in bones) a.bones[t.name] = t;

            // old bronze: brown where it is dull, gold only where the light catches it, green where forty winters ran down it
            Color bronze = new Color(0.60f, 0.39f, 0.15f), old = new Color(0.40f, 0.25f, 0.11f), bright = new Color(0.86f, 0.62f, 0.24f);
            Color green = new Color(0.24f, 0.41f, 0.36f), soot = new Color(0.06f, 0.05f, 0.06f), dark = new Color(0.22f, 0.13f, 0.08f);
            const float M = 1f, Cold = -1f;                 // metal, and "this is only metal: it does not burn"
            var kit = new Kit(a, rig, bones.ToArray());

            // ---- the bell: a flared lip, a long waist, a shoulder, a neck, and the ring the handle hooked into
            (float y, float r)[] shape =
            {
                (0.00f, R + 0.045f), (0.035f, R + 0.03f), (0.08f, R), (0.30f, R - 0.03f), (0.60f, R - 0.075f), (0.88f, R - 0.145f),
                (1.10f, R - 0.235f), (1.26f, R - 0.335f), (1.37f, R - 0.42f), (1.44f, 0.08f), (1.50f, 0.075f),
            };
            float RadiusAt(float y)
            {
                for (int i = 0; i + 1 < shape.Length; i++)
                    if (y <= shape[i + 1].y) return Mathf.Lerp(shape[i].r, shape[i + 1].r, Mathf.InverseLerp(shape[i].y, shape[i + 1].y, y));
                return shape[shape.Length - 1].r;
            }
            float[] hoops = { 0.34f, 0.44f, 1.02f };        // three hoops cast proud of it
            var ys = new List<float>();
            for (float y = 0; y <= Tall + 0.001f; y += 0.05f) ys.Add(y);
            foreach (float hoop in hoops) { ys.Add(hoop - 0.022f); ys.Add(hoop); ys.Add(hoop + 0.022f); }
            ys.Sort();
            var prof = new List<(float r, float y)>();
            foreach (float y in ys)
            {
                float proud = 0f;
                foreach (float hoop in hoops) if (Mathf.Abs(y - hoop) < 0.001f) proud = 0.022f;
                prof.Add((RadiusAt(y) + proud, y));
            }
            const int Seg = 28;
            kit.On("bell").Paint(bronze, M, Cold).Stain(p =>
            {
                float y = p.y - at.y, an = Mathf.Atan2(p.z, p.x);
                if (y < 0.04f) return soot;                                     // the lip, black from every flame it ever met
                if (y < 0.085f) return dark;
                foreach (float hoop in hoops) if (Mathf.Abs(y - hoop) < 0.012f) return bright;
                // green runs down it from the shoulder hoop, further in some places than in others
                float col = Mathf.Floor((an + Mathf.PI) / (Mathf.PI * 2f) * Seg);
                float run = Hash(col * 1.7f), len = 0.12f + (run - 0.60f) * 1.9f;
                // (never two runs side by side: it is streaks, not a coat of paint)
                if (run > 0.60f && Hash((col - 1f) * 1.7f) <= 0.60f && y < 1.0f && y > 1.0f - len) return green;
                if (y > 1.30f) return old;
                // (and the side the weather comes from has gone dull)
                if (Hash(col * 3.3f + Mathf.Floor(y * 9f) * 0.61f) > 0.80f) return old;
                return (Color?)null;
            });
            kit.Turned(at, prof.ToArray(), Seg);
            kit.Stain(null);
            // (inside: black)
            var inner = new List<(float r, float y)>();
            for (float y = 0.012f; y <= 1.30f; y += 0.1f) inner.Add((RadiusAt(y) - 0.035f, y));
            kit.Paint(soot).Turned(at, inner.ToArray(), 16);
            // three lugs where the legs go in, bolted through
            for (int i = 0; i < 3; i++)
            {
                kit.Paint(dark, 0.6f, Cold).Egg(at + c.hip[i], new Vector3(0.115f, 0.10f, 0.115f), 8, 5);
                kit.Paint(bright, M, Cold).Egg(at + c.hip[i] + c.outw[i] * 0.09f + new Vector3(0, 0.02f, 0), Vector3.one * 0.035f, 5, 4);
            }
            // the neck's collar and the ring
            kit.Paint(bright, M, Cold).Turned(at, new[] { (0.075f, Tall - 0.01f), (0.115f, Tall + 0.012f), (0.115f, Tall + 0.04f), (0.055f, Tall + 0.058f) }, 10);
            var path = new Vector3[13];
            var thick = new float[13];
            for (int i = 0; i < 13; i++)
            {
                float th = i / 12f * Mathf.PI * 2f;
                path[i] = at + new Vector3(Mathf.Cos(th) * 0.125f, Tall + 0.17f + Mathf.Sin(th) * 0.125f, 0);
                thick[i] = 0.034f;
            }
            kit.Paint(bronze, M, Cold).Tube(path, thick, 6);

            // ---- three legs, built like the legs of a stand: a bracket out of the rim, a knuckle, a leg down to a point with a pad on it
            for (int i = 0; i < 3; i++)
            {
                var h = at + c.hip[i];
                var knee = h + c.outw[i] * U;
                var foot = knee + c.outw[i] * L;
                var o = c.outw[i];
                kit.On("su" + i).Paint(old, M, Cold);
                kit.Tube(new[] { h, Vector3.Lerp(h, knee, 0.5f), knee }, new[] { 0.082f, 0.070f, 0.074f }, 8);
                kit.Paint(dark, 0.6f, Cold).Egg(knee, Vector3.one * 0.105f, 8, 5);
                kit.Paint(bright, M, Cold).Egg(knee + Vector3.up * 0.07f, Vector3.one * 0.04f, 5, 4);
                kit.On("sl" + i).Paint(bronze, M, Cold).Stain(p => Vector3.Dot(p - knee, o) > L - 0.22f ? old : (Color?)null);
                kit.Tube(new[] { knee, Vector3.Lerp(knee, foot, 0.45f), foot - o * 0.20f, foot - o * 0.02f }, new[] { 0.072f, 0.058f, 0.050f, 0.020f }, 8);
                kit.Stain(null);
                // (the pad: a little bronze shoe)
                kit.Paint(dark, 0.6f, Cold).Egg(foot - o * 0.10f, new Vector3(0.078f, 0.078f, 0.078f), 6, 4);
            }
            kit.Wear("Snuffer");

            // ---- what it has put out, still burning in it: the hoops run red, and so does its throat
            var fk = new Kit(a, rig, bones.ToArray());
            Color coal = new Color(1f, 0.46f, 0.13f);
            fk.On("bell");
            foreach (float hoop in hoops)
                fk.Paint(coal, 0, 2.6f).Turned(at, new[] { (RadiusAt(hoop - 0.016f) + 0.026f, hoop - 0.016f), (RadiusAt(hoop) + 0.030f, hoop), (RadiusAt(hoop + 0.016f) + 0.026f, hoop + 0.016f) }, Seg);
            fk.Paint(coal, 0, 2.2f).Egg(at + new Vector3(0, 0.50f, 0), new Vector3(R - 0.10f, 0.46f, R - 0.10f), 12, 6, -90, 0);
            c.ember = fk.Wear("Ember");
            c.ember.enabled = false;
            return c;
        }

        static float Ease(float x) => x * x * (3f - 2f * x);

        public void Pose(ModelActor a, string anim, float n, float dt)
        {
            if (!looked) { looked = true; who = a.sr ? a.sr.GetComponentInParent<Snuffer>() : null; }
            time += dt;
            float scale = a.def.scale;
            Vector2 v = a.velocity / scale;
            float speed = v.magnitude;
            float yaw = a.yaw * Mathf.Deg2Rad;
            Vector2 ahead = new Vector2(Mathf.Sin(yaw), Mathf.Cos(yaw)), sideways = new Vector2(ahead.y, -ahead.x);
            Vector3 travel = speed > 0.03f ? new Vector3(Vector2.Dot(v, sideways), 0, Vector2.Dot(v, ahead)) / speed : Vector3.forward;
            bool walking = anim == "walk";
            moving = Mathf.MoveTowards(moving, walking && speed > 0.06f ? 1f : 0f, dt * 6f);
            if (walking) phase += speed * dt / Stride;

            bool hot = who ? who.Hot > 0 : anim == "hot";
            if (ember) ember.enabled = hot || (who && who.Holding);
            float jolt = who ? Mathf.Clamp01(who.Jolt / 0.3f) : 0f;

            // ---- what the bell is doing. "back": how far its top leans away from where it is going, which turns
            // its mouth to face that way: it shows its prey the dark it is about to be put in.
            float wantBack = 4f, wantOver = 0f, h = WalkH;
            bool exact = false;
            switch (anim)
            {
                case "idle": wantBack = 4f + Mathf.Sin(time * 0.9f) * 3f; break;
                case "walk": wantBack = who && who.Hunting ? 16f : 6f; break;
                case "sniff": wantBack = 34f; h = WalkH + 0.12f; break;
                case "rear": h = Mathf.Lerp(WalkH, RearH, Ease(Mathf.Clamp01(n * 1.5f))); back = Mathf.Lerp(18f, 58f, Ease(Mathf.Clamp01(n * 1.3f))); exact = true; break;
                case "drop": h = Mathf.Lerp(RearH, 0f, n * n); back = Mathf.Lerp(58f, 0f, Mathf.Clamp01(n * 1.6f)); exact = true; break;
                case "cover": h = 0f; back = 0f; exact = true; break;
                case "rise": h = Mathf.Lerp(0f, WalkH, Ease(n)); back = 0f; exact = true; break;
                case "tipped": wantOver = 1f; break;
                case "up": wantOver = 0f; break;
            }
            over = Mathf.MoveTowards(over, wantOver, dt * (wantOver > 0.5f ? 5.5f : 2.2f));
            if (!exact) back = Mathf.Lerp(back, wantBack, 1f - Mathf.Exp(-(anim == "sniff" ? 9f : 6f) * dt));
            lift = exact ? h : Mathf.Lerp(lift, h, 1f - Mathf.Exp(-8f * dt));
            // on its side the open end stands upright, and the middle of it is its own radius off the ground
            float o = Ease(over);
            float height = Mathf.Lerp(lift, R + 0.04f, o);
            // it lurches: down and over towards whichever foot has just come down
            float bob = Mathf.Sin(phase * Mathf.PI * 6f) * 0.03f * moving;
            sway = Mathf.Sin(phase * Mathf.PI * 2f) * 4.5f * moving;
            float shake = jolt * Mathf.Sin(time * 70f) * 3.5f + (anim == "cover" && who && who.Holding ? Mathf.Sin(time * 31f) * 0.8f : 0f);
            var bp = new Vector3(0, height + bob, 0);
            var br = Quaternion.Euler(-back * (1f - o), 0, 0) * Quaternion.Euler(0, 0, sway + shake + 90f * o);
            bell.localPosition = bp;
            bell.localRotation = br;

            // ---- the legs
            for (int i = 0; i < 3; i++)
            {
                var hp = bp + br * hip[i];
                var foot = rest[i];
                Vector3 bendWant;
                if (o > 0.5f)
                {
                    // on its side: three legs with nothing under them
                    foot = hp + br * (outw[i] * 0.75f + new Vector3(0, -0.85f, 0)) + new Vector3(0, 0.12f * Mathf.Sin(time * 9f + i * 2.1f), 0.18f * Mathf.Sin(time * 7f + i * 1.3f));
                    down[i] = false;
                    bendWant = br * outw[i];
                }
                else
                {
                    float u = Mathf.Repeat(phase + i / 3f, 1f);
                    bool planted = u < Duty;
                    if (planted) foot += travel * ((0.5f - u / Duty) * Duty * Stride * moving);
                    else
                    {
                        float w = (u - Duty) / (1f - Duty), e = w * w * (3f - 2f * w);
                        foot += travel * ((-0.5f + e) * Duty * Stride * moving);
                        foot.y += 0.22f * Mathf.Sin(w * Mathf.PI) * moving;
                    }
                    // a foot coming down is a sound
                    if (planted && !down[i] && moving > 0.5f && who && who.Present) Sfx.Play(i == 2 ? "snuffer_step1" : "snuffer_step0", 0.42f, 0.10f);
                    down[i] = planted;
                    // flat on the ground its legs are pushed out from under it
                    if (lift < WalkH) foot = Vector3.Lerp(new Vector3(foot.x * 1.22f, foot.y, foot.z * 1.22f), foot, lift / WalkH);
                    bendWant = Vector3.up * 0.75f + outw[i] * 1.0f;
                }
                var d = foot - hp;
                float len = Mathf.Clamp(d.magnitude, Mathf.Abs(L - U) + 0.02f, U + L - 0.004f);
                var dir = d.normalized;
                float along = (U * U - L * L + len * len) / (2f * len);
                float off = Mathf.Sqrt(Mathf.Max(0, U * U - along * along));
                var bend = bendWant - dir * Vector3.Dot(bendWant, dir);
                bend = bend.sqrMagnitude > 0.0001f ? bend.normalized : Vector3.up;
                var knee = hp + dir * along + bend * off;
                upper[i].localPosition = hp;
                upper[i].localRotation = Quaternion.FromToRotation(outw[i], knee - hp);
                lower[i].localPosition = knee;
                lower[i].localRotation = Quaternion.FromToRotation(outw[i], hp + dir * len - knee);
            }
        }
    }
}
