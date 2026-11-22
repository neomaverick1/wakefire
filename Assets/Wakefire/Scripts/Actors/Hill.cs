// What Azar meets on the Hill of Sleepers besides conversation: the unremembered (the dead
// whose names have worn off their stones, and who would like somebody else's), the king's clay
// soldiers, which stand in their niches until someone comes close enough to be a trespasser,
// and tomb scarabs, which are alive, awake, and busy.
using UnityEngine;

namespace Wakefire
{
    // ------------------------------------------------------------------------- the unremembered
    /// <summary>One of the dead nobody remembers: drifts towards the living, reaches for them, and
    /// when struck comes apart and gathers itself somewhere else. Like all the dead, it is not
    /// there at all in the dream.</summary>
    public class Shade : Enemy
    {
        enum S { Drift, Reach, Gone, Back }
        S s;
        float cool, thin = 0f;
        bool struck;
        Vector2 roam;
        float roamClock;

        public static Shade Spawn(Vector2 at) => Make<Shade>("priest", "idle", at, WorldLayer.Waking, 3, "shade");

        protected override void Init()
        {
            speed = 1.55f; half = new Vector2(0.3f, 0.15f); touchDamage = 0;
            mat.SetFloat("_Ghost", 0.9f);
            mat.SetVector("_GhostFade", new Vector4(0.285f, 0.46f, 0, 0));
            mat.SetFloat("_Dissolve", thin);
            if (shadow) { Destroy(shadow.gameObject); shadow = null; }
            hover = 1f / 16f;
        }

        protected override Color BurstColor => new Color(0.5f, 0.95f, 0.9f);
        protected override string HurtSound => "shade_hit";
        protected override float KnockScale => 1.3f;

        static Vector2 Vec(Facing f) => f == Facing.Down ? Vector2.down : f == Facing.Up ? Vector2.up : f == Facing.Left ? Vector2.left : Vector2.right;

        protected override void Think(float dt, Player p)
        {
            cool -= dt;
            var d = p.pos - pos;
            float want = 0f;
            switch (s)
            {
                case S.Drift:
                    if (!CanSee(p, 6.5f))
                    {
                        roamClock -= dt;
                        if (roamClock <= 0)
                        {
                            roamClock = Random.Range(1.5f, 3.5f);
                            roam = Vector2.Distance(pos, home) > 2.5f ? (home - pos).normalized : Random.value < 0.45f ? Vector2.zero : Random.insideUnitCircle.normalized;
                        }
                        if (roam == Vector2.zero) anim.Play("idle", facing);
                        else { facing = FaceOf(roam); anim.Play("walk", facing); anim.SetFacing(facing); Move(roam * speed * 0.45f, dt); }
                        break;
                    }
                    facing = FaceOf(d);
                    anim.Play("walk", facing);
                    anim.SetFacing(facing);
                    Move(d.normalized * speed, dt);
                    if (d.magnitude < 1.3f && cool <= 0)
                    {
                        s = S.Reach; stateClock = 0; struck = false;
                        anim.Play("scratch", facing, true);
                        Sfx.Play("shade", 0.55f, 0.12f);
                    }
                    break;
                case S.Reach:
                    // the hand comes round on the fifth frame of eight
                    if (!struck && anim.Frame >= 4)
                    {
                        struck = true;
                        var at = pos + Vec(facing) * 0.75f;
                        if (Present && Vector2.Distance(at, p.pos) < 0.95f && Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos))
                            p.Hurt(new HitInfo { damage = 1, from = pos, knockback = 5f, kind = HitKind.Slash, source = gameObject });
                    }
                    if (anim.Done || stateClock > 0.9f) { s = S.Drift; cool = 1.0f; }
                    break;
                case S.Gone:
                    want = 1.05f;
                    if (stateClock > 0.45f)
                    {
                        // somewhere else near him, where there is room to stand
                        for (int i = 0; i < 12; i++)
                        {
                            var c = p.pos + (Vector2)(Quaternion.Euler(0, 0, Random.Range(0f, 360f)) * Vector2.right) * Random.Range(2.6f, 3.6f);
                            if (Solids.Overlaps(new Rect(c - half, half * 2), c, this)) continue;
                            if (Map.Current && !Map.Current.bounds.Contains(c)) continue;
                            pos = c;
                            break;
                        }
                        s = S.Back; stateClock = 0;
                    }
                    break;
                case S.Back:
                    if (stateClock > 0.5f) { s = S.Drift; cool = 0.5f; }
                    break;
            }
            thin = Mathf.MoveTowards(thin, want, dt * 2.2f);
            mat.SetFloat("_Dissolve", thin);
            hover = (1f + Mathf.Round(Mathf.Sin(stateClock * 2.1f + home.x) * 1.2f)) / 16f;
        }

        protected override void OnHurt(HitInfo h)
        {
            if (health.Dead) return;
            // it comes apart, and is somewhere else when it comes back together
            s = S.Gone; stateClock = 0;
            health.invulnerable = 1.2f;
            for (int i = 0; i < 8; i++)
                Fx.Spawn(pos + new Vector2(Random.Range(-0.3f, 0.3f), 0), Random.insideUnitCircle * 1.2f, Random.Range(0.3f, 1.2f), Random.Range(0.4f, 1.2f),
                    Random.Range(0.4f, 0.8f), new Color(0.75f, 1f, 0.95f), new Color(0.15f, 0.4f, 0.5f), -0.5f);
        }
    }

    // ------------------------------------------------------------------------------- ushabti
    /// <summary>A clay soldier of the king's guard: stands in the hall like a statue until Azar is
    /// close, then marches on him and, when he lines up, charges. Its shield turns a blade from the
    /// front; it shatters like the jar it is.</summary>
    public class Ushabti : Enemy
    {
        enum S { Stand, Stir, March, Aim, Charge, Stuck }
        S s;
        Vector2 chargeDir;
        public bool Awake => s != S.Stand;

        public static Ushabti Spawn(Vector2 at) => Make<Ushabti>("sentinel", "idle", at, WorldLayer.Both, 4, "ushabti");

        protected override void Init() { speed = 1.5f; half = new Vector2(0.32f, 0.16f); touchDamage = 0; }
        protected override float KnockScale => 0.3f;
        protected override string HurtSound => "clay_hit";
        protected override Color BurstColor => new Color(0.72f, 0.44f, 0.30f);

        /// <summary>Step out now, whether or not anyone is near (the king calls them).</summary>
        public void Rouse() { if (s == S.Stand) Stir(); }

        void Stir()
        {
            s = S.Stir; stateClock = 0; touchDamage = 2;
            Sfx.Play("clay_wake", 0.8f);
            Fx.Dust(pos, 8);
        }

        protected override bool Accepts(HitInfo h)
        {
            if (s == S.Stand || s == S.Stir || s == S.Stuck || h.kind == HitKind.Reflected || h.kind == HitKind.Fire) return true;
            var from = ((Vector2)h.from - pos).normalized;
            var f = facing == Facing.Down ? Vector2.down : facing == Facing.Up ? Vector2.up : facing == Facing.Left ? Vector2.left : Vector2.right;
            return Vector2.Dot(from, f) < 0.5f;
        }

        protected override void OnHurt(HitInfo h) { if (s == S.Stand) Stir(); }

        protected override void Die()
        {
            Sfx.Play("pot_break");
            for (int i = 0; i < 16; i++)
                Fx.Spawn(pos + new Vector2(0, 0.6f) + Random.insideUnitCircle * 0.3f, Random.insideUnitCircle * 3.6f, 0.5f, Random.Range(3f, 6f), Random.Range(0.4f, 0.8f),
                    new Color(0.74f, 0.46f, 0.32f), new Color(0.36f, 0.20f, 0.16f), 18f, i % 3 == 0 ? 2 : 1);
            base.Die();
        }

        protected override void Think(float dt, Player p)
        {
            var d = p.pos - pos;
            switch (s)
            {
                case S.Stand:
                    anim.Play("idle", facing);
                    if (CanSee(p, 3.3f)) Stir();
                    break;
                case S.Stir:
                    facing = FaceOf(d);
                    anim.SetFacing(facing);
                    if (stateClock > 0.7f) { s = S.March; stateClock = 0; }
                    break;
                case S.March:
                {
                    if (d.magnitude > 0.9f)
                    {
                        facing = FaceOf(d); anim.Play("walk", facing); anim.SetFacing(facing);
                        Move(d.normalized * speed, dt);
                    }
                    else anim.Play("idle", facing);
                    bool lined = (Mathf.Abs(d.x) < 0.45f || Mathf.Abs(d.y) < 0.45f) && d.magnitude < 6.5f;
                    if (lined && stateClock > 0.8f && CanSee(p, 7f)) { s = S.Aim; stateClock = 0; facing = FaceOf(d); anim.Play("idle", facing, true); Sfx.Play("sentinel_alert", 0.6f, 0.02f); }
                    break;
                }
                case S.Aim:
                    if (stateClock > 0.5f)
                    {
                        s = S.Charge; stateClock = 0;
                        chargeDir = facing == Facing.Down ? Vector2.down : facing == Facing.Up ? Vector2.up : facing == Facing.Left ? Vector2.left : Vector2.right;
                        anim.Play(anim.model ? "run" : "walk", facing, true);
                    }
                    break;
                case S.Charge:
                {
                    var before = pos;
                    Move(chargeDir * 5.6f, dt);
                    if ((pos - before).magnitude < 5.6f * dt * 0.3f || stateClock > 1.5f)
                    {
                        s = S.Stuck; stateClock = 0; PixelView.I.Shake(1, 0.15f); Sfx.Play("clay_hit"); anim.Play("hurt", facing, true);
                    }
                    break;
                }
                case S.Stuck:
                    if (stateClock > 1.3f) { s = S.March; stateClock = 0; }
                    break;
            }
        }
    }

    // -------------------------------------------------------------------------------- scarab
    /// <summary>A tomb scarab: comes in a straight dash, stops, turns, dashes again. One blow each,
    /// but there is never only one.</summary>
    public class Scarab : Enemy
    {
        Vector2 dir;
        float next;
        bool dashing;

        public static Scarab Spawn(Vector2 at) => Make<Scarab>("crab", "idle", at, WorldLayer.Waking, 1, "scarab");

        protected override void Init() { speed = 4.4f; half = new Vector2(0.3f, 0.14f); next = Random.Range(0.2f, 1.2f); }
        protected override Color BurstColor => new Color(0.16f, 0.24f, 0.56f);
        protected override float KnockScale => 1.6f;

        protected override void Think(float dt, Player p)
        {
            next -= dt;
            bool sees = CanSee(p, 5.5f);
            if (next <= 0)
            {
                dashing = !dashing;
                if (dashing)
                {
                    if (sees) { dir = (p.pos - pos).normalized; Sfx.Play("scarab", 0.5f, 0.15f); }
                    else dir = Vector2.Distance(pos, home) > 2.5f ? (home - pos).normalized : Random.insideUnitCircle.normalized;
                    // beetles keep to the four ways a stone floor runs, more or less
                    dir = (dir + (Mathf.Abs(dir.x) > Mathf.Abs(dir.y) ? new Vector2(Mathf.Sign(dir.x), 0) : new Vector2(0, Mathf.Sign(dir.y))) * 0.6f).normalized;
                    next = sees ? Random.Range(0.35f, 0.6f) : Random.Range(0.3f, 0.5f);
                }
                else next = sees ? Random.Range(0.25f, 0.5f) : Random.Range(0.6f, 1.8f);
            }
            if (dashing)
            {
                facing = FaceOf(dir);
                anim.Play("walk", facing);
                anim.SetFacing(facing);
                Move(dir * (sees ? speed : speed * 0.45f), dt);
            }
            else if (sees && Vector2.Distance(p.pos, pos) < 1.0f && (anim.anim != "attack" || anim.Done)) anim.Play("attack", facing, true);
            else if (anim.anim != "attack" || anim.Done) anim.Play("idle", facing);
        }
    }
}
