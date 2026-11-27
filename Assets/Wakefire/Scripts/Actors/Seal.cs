// The Seal. The temple seals every door it owns, with a cylinder of lapis the length of a
// finger, rolled once across wet clay: a row of spearmen, and the god's name. This is that
// seal, as the priest who keeps it dreams of it: the size of a barrel, and rolling up and down
// the yard by itself, sealing the ground. Once round, and it has printed a spearman.
//
// A Print gets up out of the clay it was pressed in. It is a spearman as deep as a thumbnail:
// from the side he is a man with a spear, from the front he is a line. A line cannot be hit.
// A line cannot hit anybody either, so he has to turn side-on to use the spear, and side-on
// one blow breaks him. There are never more than four. There are never fewer for long.
//
// The Seal itself does not mind a blade, from behind or from the side. Struck from the front,
// it goes back the way it came, a good deal faster, and takes back every Print it rolls over:
// they go into it the way they came out. It does not stop until the end of its beat stops it,
// and lapis does not like stopping. Three times, and it is in two halves.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Seal : Enemy
    {
        public enum S { Roll, Rest, Back, Dazed }
        public S s;
        Vector2 a, b;                               // the two ends of its beat
        int dir = 1;                                // +1: rolling towards b
        float sincePrint;
        /// <summary>Degrees the drum has turned (the model reads it).</summary>
        public float Turn { get; private set; }
        public int Cracks { get; private set; }
        public float Jolt { get; private set; }
        public readonly List<Print> prints = new List<Print>();
        public const float R = 0.62f;               // its radius, in tiles
        const float Girth = 2f * Mathf.PI * R;      // once round: one spearman
        public const int Most = 4;
        public static bool Told;

        public static Seal Spawn(Vector2 at) => Make<Seal>("moth", "idle", at, WorldLayer.Waking, 3, "seal");

        protected override void Init()
        {
            speed = 1.15f; half = new Vector2(1.0f, 0.45f); touchDamage = 1; roams = false; flying = true;
            a = pos; b = pos + new Vector2(0, -6f);
            sincePrint = Girth * 0.5f;
        }

        /// <summary>"beat:x0,y0;x1,y1": the two ends of its roll, in the map's own pixels.</summary>
        public void SetBeat(string text)
        {
            if (string.IsNullOrEmpty(text)) return;
            int i = text.IndexOf("beat:");
            if (i < 0) return;
            var parts = text.Substring(i + 5).Split(' ')[0].Split(';');
            var inv = System.Globalization.CultureInfo.InvariantCulture;
            var pts = new List<Vector2>();
            foreach (var part in parts)
            {
                var xy = part.Split(',');
                if (xy.Length == 2 && float.TryParse(xy[0], System.Globalization.NumberStyles.Float, inv, out float x) &&
                    float.TryParse(xy[1], System.Globalization.NumberStyles.Float, inv, out float y)) pts.Add(Map.ToWorld(x, y));
            }
            if (pts.Count >= 2) { a = pts[0]; b = pts[1]; pos = home = a; }
        }

        public override bool Sleeps => false;
        protected override bool WaitsOutStories => true;
        protected override float KnockScale => 0f;
        protected override string HurtSound => "seal_knock";
        protected override Color BurstColor => new Color(0.16f, 0.26f, 0.62f);
        public override Rect HitBox => new Rect(pos.x - 1.05f, pos.y - 0.25f, 2.1f, 1.5f);
        /// <summary>The way it is going.</summary>
        public Vector2 Along => ((dir > 0 ? b : a) - (dir > 0 ? a : b)).normalized;
        public bool GoingBack => s == S.Back;
        public Vector2 EndA => a;
        public Vector2 EndB => b;

        /// <summary>From behind or from the side a blade rings off it. From the front, it is sent back.</summary>
        protected override bool Accepts(HitInfo h)
        {
            Jolt = 0.25f;
            // (only while it is rolling: standing still it is a barrel of stone, and a blade is a blade)
            if (s != S.Roll) return false;
            // the front of it: in its way, not off to one side of it
            var from = (Vector2)h.from - pos;
            var along = Along;
            if (Vector2.Dot(from, along) < 0.6f || Mathf.Abs(from.x * along.y - from.y * along.x) > 1.15f) return false;
            dir = -dir;
            s = S.Back; stateClock = 0;
            Sfx.Play("seal_knock", 1f, 0.03f);
            PixelView.I.Shake(2, 0.16f);
            if (Story.I) Story.I.SealStruck();
            return false;
        }

        protected override void Think(float dt, Player p)
        {
            if (Jolt > 0) Jolt -= dt;
            prints.RemoveAll(q => !q);
            if (!Told && Story.I && !Story.I.Running && CanSee(p, 7.5f)) { Told = true; Story.I.SealSeen(); }
            var end = dir > 0 ? b : a;
            switch (s)
            {
                case S.Roll:
                {
                    touchDamage = 1;
                    float step = Advance(end, speed * (1f - 0.12f * Cracks), dt);
                    sincePrint += step;
                    if ((int)(stateClock * 2.2f) != (int)((stateClock - dt) * 2.2f) && CanSee(p, 9f)) Sfx.Play("seal_roll", 0.45f, 0.1f);
                    if (sincePrint >= Girth)
                    {
                        sincePrint = 0;
                        if (prints.Count < Most && Present) Lay();
                    }
                    if (Vector2.Distance(pos, end) < 0.05f) { s = S.Rest; stateClock = 0; }
                    break;
                }
                case S.Rest:
                    touchDamage = 0;
                    if (stateClock > 0.9f) { dir = -dir; s = S.Roll; stateClock = 0; }
                    break;

                case S.Back:
                {
                    // the way it came, over everything it printed, until something stops it
                    touchDamage = 2;
                    Advance(end, 5.2f, dt);
                    if ((int)(stateClock * 7f) != (int)((stateClock - dt) * 7f)) Sfx.Play("seal_roll", 0.7f, 0.2f);
                    foreach (var q in prints)
                    {
                        if (!q) continue;
                        var off = q.pos - pos;
                        var way = Along;
                        if (Mathf.Abs(Vector2.Dot(off, way)) < 0.75f && Mathf.Abs(off.x * way.y - off.y * way.x) < 1.3f) q.TakenBack();
                    }
                    if (Vector2.Distance(pos, end) < 0.05f) Crash();
                    break;
                }
                case S.Dazed:
                    touchDamage = 0;
                    if (stateClock > 1.8f) { dir = -dir; s = S.Roll; stateClock = 0; sincePrint = Girth * 0.6f; }
                    break;
            }
        }

        /// <summary>Towards a place, no further than it; how far it went. The drum turns with the ground it covers.</summary>
        float Advance(Vector2 to, float rate, float dt)
        {
            var before = pos;
            pos = Vector2.MoveTowards(pos, to, rate * dt);
            var d = pos - before;
            // (it shows its south face: rolling towards the lens, the top of it comes forward)
            Turn += Vector2.Dot(d, Vector2.down) / R * Mathf.Rad2Deg;
            return d.magnitude;
        }

        void Lay()
        {
            var q = Print.Spawn(pos - Along * 0.15f);
            q.seal = this;
            q.side = prints.Count % 2 == 0 ? 1 : -1;
            prints.Add(q);
            Sfx.Play("seal_print", 0.8f, 0.05f);
            Fx.Dust(pos - Along * 0.3f, 3);
        }

        void Crash()
        {
            Cracks++;
            Jolt = 0.4f;
            Sfx.Play("seal_crash", 1f, 0.03f);
            Noise.Make(pos, 12f);
            PixelView.I.Shake(3, 0.25f);
            Fx.Dust(pos + new Vector2(-0.8f, 0), 6); Fx.Dust(pos + new Vector2(0.8f, 0), 6);
            for (int i = 0; i < 8; i++)
                Fx.Spawn(pos + new Vector2(Random.Range(-0.9f, 0.9f), 0.2f), Random.insideUnitCircle * 3f, 0.4f, Random.Range(1f, 4f), Random.Range(0.4f, 0.8f),
                    new Color(0.20f, 0.32f, 0.70f), new Color(0.08f, 0.10f, 0.24f), 18f, i % 3 == 0 ? 2 : 1);
            flash = 0.15f;
            if (Cracks >= 3) { health.hp = 0; Rooms.Slain(this); Die(); return; }
            if (Story.I) Story.I.SealCracked(Cracks);
            s = S.Dazed; stateClock = 0;
        }

        /// <summary>In two halves, and every spearman it ever pressed has stopped being one.</summary>
        protected override void Die()
        {
            foreach (var q in prints) if (q) q.Crumble();
            prints.Clear();
            Sfx.Play("seal_split", 1f, 0.02f);
            PixelView.I.Shake(3, 0.35f);
            for (int i = 0; i < 24; i++)
                Fx.Spawn(pos + new Vector2(Random.Range(-1f, 1f), Random.Range(0f, 0.8f)), Random.insideUnitCircle * 4f, 0.5f, Random.Range(2f, 6f), Random.Range(0.6f, 1.2f),
                    i % 4 == 0 ? new Color(0.88f, 0.66f, 0.22f) : new Color(0.20f, 0.32f, 0.70f), new Color(0.08f, 0.10f, 0.24f), 18f, i % 3 == 0 ? 2 : 1);
            for (int i = 0; i < 8; i++) Pickup.Drop(Pickup.Kind.Shekel, pos + Random.insideUnitCircle * 1.1f);
            Pickup.Chance(pos, 0f, 1f);
            if (Story.I) Story.I.SealSplit();
            if (spawnId != null) Story.Set("dead_" + spawnId);
            Destroy(gameObject);
        }
    }

    /// <summary>What the Seal leaves behind it: a spearman, as deep as a thumbnail.</summary>
    public class Print : Enemy
    {
        public enum S { Flat, Peel, March, Edge, Thrust, Taken }
        public S s;
        public Seal seal;
        public int side = 1;                         // which way it steps off the Seal's way
        bool struck;
        float row;

        public static Print Spawn(Vector2 at) => Make<Print>("sentinel", "lie", at, WorldLayer.Waking, 1, "print");

        protected override void Init()
        {
            speed = 1.9f; half = new Vector2(0.28f, 0.14f); touchDamage = 0; roams = false;
            Thin();
            mat.SetFloat("_Dissolve", 0.35f);
        }

        /// <summary>As deep as a thumbnail: all of him is in the height and the length.</summary>
        void Thin()
        {
            if (anim.model) anim.model.rig.localScale = Vector3.Scale(new Vector3(0.13f, 1f, 1f), Vector3.one * anim.model.def.scale);
        }

        public override bool Sleeps => false;
        protected override bool WaitsOutStories => true;
        protected override float KnockScale => 0.4f;
        protected override string HurtSound => "print_crumble";
        protected override Color BurstColor => new Color(0.72f, 0.60f, 0.44f);
        /// <summary>Edge-on he is a line.</summary>
        public bool EdgeOn => facing == Facing.Up || facing == Facing.Down;
        public override Rect HitBox => EdgeOn ? new Rect(pos.x - 0.08f, pos.y - 0.1f, 0.16f, 1.9f) : new Rect(pos.x - 0.45f, pos.y - 0.2f, 0.9f, 1.9f);

        /// <summary>Lying in the clay he is clay; edge-on there is nothing there to hit.</summary>
        protected override bool Untouchable(HitInfo h) => s == S.Flat || s == S.Taken || (EdgeOn && s != S.Peel);

        protected override void Think(float dt, Player p)
        {
            var d = p.pos - pos;
            switch (s)
            {
                case S.Flat:
                    // pressed into the ground, still wet
                    anim.Play("lie", Facing.Down);
                    mat.SetFloat("_Dissolve", Mathf.Lerp(0.35f, 0f, stateClock / 0.9f));
                    if (stateClock > 1.1f)
                    {
                        s = S.Peel; stateClock = 0;
                        facing = side > 0 ? Facing.Right : Facing.Left;
                        anim.Play("idle", facing, true); anim.SetFacing(facing);
                        mat.SetFloat("_Dissolve", 0f);
                        Sfx.Play("print_peel", 0.7f, 0.08f);
                        Fx.Dust(pos, 4);
                        if (Story.I) Story.I.PrintPeels();
                    }
                    break;

                case S.Peel:
                    // off the Seal's way, sideways, before anything else
                    anim.Play("walk", facing);
                    Move(new Vector2(side, 0) * speed, dt);
                    if (stateClock > 0.5f) { s = S.March; stateClock = 0; }
                    break;

                case S.March:
                {
                    if (!CanSee(p, 10f)) { anim.Play("idle", facing); vel = Vector2.zero; break; }
                    // not in his row: he has to turn to get there, and turned he is a line
                    if (Mathf.Abs(d.y) > 0.4f) { s = S.Edge; stateClock = 0; row = p.pos.y; break; }
                    facing = d.x > 0 ? Facing.Right : Facing.Left;
                    anim.SetFacing(facing);
                    if (Mathf.Abs(d.x) < 1.25f)
                    {
                        s = S.Thrust; stateClock = 0; struck = false; vel = Vector2.zero;
                        anim.Play("thrust", facing, true);
                        break;
                    }
                    // (in file: he does not walk through the man in front of him)
                    if (Behind(new Vector2(Mathf.Sign(d.x), 0))) { anim.Play("idle", facing); vel = Vector2.zero; break; }
                    anim.Play("walk", facing);
                    Move(new Vector2(Mathf.Sign(d.x), 0) * speed, dt);
                    break;
                }
                case S.Edge:
                {
                    float dy = p.pos.y - pos.y;
                    if (Mathf.Abs(dy) < 0.15f || stateClock > 3.5f) { s = S.March; stateClock = 0; break; }
                    facing = dy > 0 ? Facing.Up : Facing.Down;
                    anim.SetFacing(facing);
                    if (Behind(new Vector2(0, Mathf.Sign(dy)))) { anim.Play("idle", facing); vel = Vector2.zero; break; }
                    anim.Play("walk", facing);
                    Move(new Vector2(0, Mathf.Sign(dy)) * speed * 1.15f, dt);
                    break;
                }
                case S.Thrust:
                    vel = Vector2.zero;
                    if (!struck && stateClock > 0.36f)
                    {
                        struck = true;
                        Sfx.Play("print_thrust", 0.8f, 0.08f);
                        var tip = pos + new Vector2(facing == Facing.Right ? 1.1f : -1.1f, 0);
                        if (Present && Mathf.Abs(p.pos.y - pos.y) < 0.5f && Mathf.Abs(p.pos.x - tip.x) < 0.7f && Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos))
                            p.Hurt(new HitInfo { damage = 1, from = pos, knockback = 5f, kind = HitKind.Slash, source = gameObject });
                    }
                    if (stateClock > 0.95f) { s = S.March; stateClock = 0; }
                    break;

                case S.Taken:
                    vel = Vector2.zero;
                    mat.SetFloat("_Dissolve", Mathf.Clamp01(stateClock / 0.3f));
                    if (stateClock > 0.3f) Destroy(gameObject);
                    break;
            }
        }

        /// <summary>Is another of the same pressing just ahead of him, the way he is going?</summary>
        bool Behind(Vector2 way)
        {
            if (!seal) return false;
            foreach (var q in seal.prints)
            {
                if (!q || q == this || q.s == S.Flat || q.s == S.Taken) continue;
                var off = q.pos - pos;
                float ahead = Vector2.Dot(off, way);
                if (ahead > 0.02f && ahead < 0.75f && Mathf.Abs(off.x * way.y - off.y * way.x) < 0.45f) return true;
            }
            return false;
        }

        /// <summary>The Seal has rolled back over him: he goes into it the way he came out.</summary>
        public void TakenBack()
        {
            if (s == S.Taken) return;
            s = S.Taken; stateClock = 0;
            anim.Play("lie", Facing.Down, true);
            Sfx.Play("seal_print", 0.6f, 0.2f);
        }

        public void Crumble()
        {
            for (int i = 0; i < 8; i++)
                Fx.Spawn(pos + new Vector2(Random.Range(-0.2f, 0.2f), Random.Range(0f, 1.2f)), Random.insideUnitCircle * 1.6f, 0.3f, Random.Range(0.5f, 2.5f), Random.Range(0.4f, 0.8f),
                    new Color(0.74f, 0.62f, 0.46f), new Color(0.40f, 0.32f, 0.24f), 16f, i % 3 == 0 ? 2 : 1);
            Sfx.Play("print_crumble", 0.6f, 0.15f);
            Destroy(gameObject);
        }

        protected override void Die()
        {
            if (Story.I) Story.I.PrintBroken();
            Crumble();
        }
    }

    /// <summary>The cylinder: lapis, a cap of gold at each end, the bore the cord went through, and a row of
    /// spearmen cut round it that nobody has ever seen the right way out.</summary>
    public class SealProp : IPoser
    {
        Transform drum;
        Renderer[] cracks = new Renderer[2];
        Seal who;
        bool looked;
        float time, spin;

        public static SealProp Make(ModelActor a)
        {
            var c = new SealProp();
            float S = a.def.scale;
            float R = Seal.R / S, L = 1.0f / S;                    // radius, and half its length along the axle
            var go = new GameObject("drum");
            go.transform.SetParent(a.rig, false);
            go.transform.localPosition = new Vector3(0, R, 0);
            c.drum = go.transform;
            a.bones["drum"] = c.drum;
            Color lapis = new Color(0.10f, 0.19f, 0.52f), deep = new Color(0.06f, 0.11f, 0.34f), pale = new Color(0.36f, 0.50f, 0.86f), gold = new Color(0.90f, 0.68f, 0.24f), dark = new Color(0.03f, 0.03f, 0.06f);
            var kit = new Kit(a, a.rig, new[] { c.drum });
            // the axle runs east and west: the lathe's own up is the model's right
            kit.On("drum").Frame(new Vector3(0, R, 0), Vector3.forward, Vector3.right, Vector3.up);
            const int Seg = 30;
            var prof = new (float r, float y)[] { (R * 0.94f, -L), (R, -L * 0.90f), (R, -L * 0.62f), (R, -L * 0.30f), (R, 0f), (R, L * 0.30f), (R, L * 0.62f), (R, L * 0.90f), (R * 0.94f, L) };
            kit.Paint(lapis).Turned(Vector3.zero, prof, Seg, 1f, 0, 360, (i, j) =>
            {
                if (i <= 1 || i >= prof.Length - 2) return gold;                                   // a band of gold at each end
                int k = j % 6;                                                                       // five spearmen round it, and a gap for the god's name
                if (j >= Seg - 5) return i == 4 ? pale : deep;
                if (k == 4) return i >= 2 && i <= 6 ? pale : (Color?)null;                           // the spear
                if (k == 1 || k == 2) return i >= 3 && i <= 5 ? pale : (Color?)null;                 // the man
                return k == 0 ? deep : (Color?)null;
            });
            // the ends: gold, and the bore
            foreach (int e in new[] { -1, 1 })
            {
                kit.Paint(gold, 1).Turned(new Vector3(0, e * L, 0), new[] { (0.001f, 0f), (R * 0.94f, 0f) }, Seg);
                kit.Paint(dark).Turned(new Vector3(0, e * (L + 0.004f), 0), new[] { (0.001f, 0f), (R * 0.26f, 0f) }, 10);
            }
            kit.Frame();
            kit.Wear("Seal");
            // what stopping does to it: a crack round it, and then another
            for (int n = 0; n < 2; n++)
            {
                var ck = new Kit(a, a.rig, new[] { c.drum });
                ck.On("drum").Frame(new Vector3(0, R, 0), Vector3.forward, Vector3.right, Vector3.up).Paint(dark);
                float at = n == 0 ? -L * 0.28f : L * 0.36f;
                var path = new List<Vector3>();
                var rad = new List<float>();
                for (int j = 0; j <= Seg; j++)
                {
                    float lon = j / (float)Seg * Mathf.PI * 2f;
                    float jag = (j % 2 == 0 ? 0.035f : -0.03f) + Mathf.Sin(j * 1.7f + n) * 0.02f;
                    path.Add(new Vector3(Mathf.Sin(lon) * (R + 0.004f), at + jag, Mathf.Cos(lon) * (R + 0.004f)));
                    rad.Add(0.012f);
                }
                ck.Tube(path.ToArray(), rad.ToArray(), 4);
                ck.Frame();
                c.cracks[n] = ck.Wear("Crack" + n);
                c.cracks[n].enabled = false;
            }
            return c;
        }

        public void Pose(ModelActor a, string anim, float n, float dt)
        {
            if (!looked) { looked = true; who = a.sr ? a.sr.GetComponentInParent<Seal>() : null; }
            time += dt;
            if (!who) spin += dt * 60f;
            float turn = who ? who.Turn : spin;
            float jolt = who ? Mathf.Clamp01(who.Jolt / 0.3f) : 0f;
            int broke = who ? who.Cracks : (int)(time / 3f) % 3;
            for (int i = 0; i < cracks.Length; i++) if (cracks[i]) cracks[i].enabled = broke > i;
            float R = Seal.R / a.def.scale;
            drum.localPosition = new Vector3(jolt * Mathf.Sin(time * 70f) * 0.02f, R + jolt * 0.03f, 0);
            drum.localRotation = Quaternion.AngleAxis(turn, Vector3.right) * Quaternion.Euler(0, 0, broke * 1.5f * Mathf.Sin(turn * Mathf.Deg2Rad));
        }
    }
}
