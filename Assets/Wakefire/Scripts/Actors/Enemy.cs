// What hunts Azar: brine crabs on the shore, jackals in the olive terraces, moth-shades that
// only live in the dream, and bronze sentinels in the ziggurat. Shared plumbing here (health,
// knockback, flashing, touching hurts, dying in a burst, dropping shekels); each kind thinks
// for itself below.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public abstract class Enemy : MonoBehaviour, IHittable, IHitBox
    {
        public static readonly List<Enemy> All = new List<Enemy>();
        public virtual Rect HitBox => new Rect(pos.x - half.x - 0.1f, pos.y - half.y, half.x * 2 + 0.2f, half.y * 2 + 0.8f + (flying ? hover : 0));

        public Vector2 pos, home;
        public Facing facing = Facing.Down;
        public WorldLayer layer = WorldLayer.Waking;
        public SpriteAnim anim;
        public Health health;
        public Vector2 half = new Vector2(0.3f, 0.15f);
        public int touchDamage = 1;
        public float speed = 2f;
        public string spawnId;
        protected float stateClock, knockClock, flash;
        protected Vector2 knockVel, vel;
        protected SpriteRenderer shadow;
        protected Material mat;
        protected bool flying;
        protected float hover;

        protected static T Make<T>(string sheet, string anim, Vector2 at, WorldLayer layer, int hp, string look = null) where T : Enemy
        {
            var go = new GameObject(typeof(T).Name);
            go.transform.SetParent(Map.Current ? Map.Current.transform : null, false);
            var e = go.AddComponent<T>();
            e.pos = e.home = at;
            e.layer = layer;
            var body = new GameObject("Sprite");
            body.transform.SetParent(go.transform, false);
            var sr = body.AddComponent<SpriteRenderer>();
            e.mat = new Material(Map.SpriteMat);
            e.mat.SetFloat("_Layer", (float)layer);
            sr.sharedMaterial = e.mat;
            e.anim = body.AddComponent<SpriteAnim>();
            e.anim.sr = sr;
            e.anim.modelAs = look;
            e.anim.sheet = SpriteSheet.Load(sheet);
            e.anim.Play(anim, Facing.Down, true);
            e.health = go.AddComponent<Health>();
            e.health.max = e.health.hp = hp;
            e.shadow = Npc.MakeShadow(go.transform, layer, 10);
            All.Add(e);
            e.Init();
            e.Place();
            return e;
        }

        protected virtual void Init() { }
        protected abstract void Think(float dt, Player p);
        protected virtual void OnHurt(HitInfo h) { }

        void OnDestroy() => All.Remove(this);

        /// <summary>Is this creature in the world shown where it stands?</summary>
        public bool Present
        {
            get
            {
                if (layer == WorldLayer.Both) return true;
                bool d = Dream.I && Dream.I.IsDreamAt(pos);
                return layer == WorldLayer.Dream ? d : !d;
            }
        }

        public bool Hit(HitInfo h)
        {
            if (!Present || health.Dead) return false;
            if (!Accepts(h)) { Sfx.Play("clank"); Fx.Sparks(pos + new Vector2(0, 0.5f), new Color(1f, 0.85f, 0.5f), 4); return true; }
            if (!health.Take(h)) return false;
            flash = 0.18f;
            health.invulnerable = 0.25f;
            var away = (pos - (Vector2)h.from).normalized;
            knockVel = away * h.knockback * KnockScale;
            knockClock = 0.18f;
            OnHurt(h);
            Sfx.Play(HurtSound);
            if (health.Dead) Die();
            return true;
        }

        /// <summary>This one's blow has just stopped on Azar's raised shield: it is thrown back off the bronze.</summary>
        public virtual void Blocked(Player p)
        {
            knockVel = (pos - p.pos).normalized * 6f * Mathf.Max(0.5f, KnockScale);
            knockClock = 0.24f;
        }

        protected virtual bool Accepts(HitInfo h) => true;
        protected virtual float KnockScale => 1f;
        protected virtual string HurtSound => "enemy_hit";
        protected virtual Color BurstColor => new Color(0.25f, 0.18f, 0.32f);

        protected virtual void Die()
        {
            Sfx.Play("enemy_die");
            for (int i = 0; i < 14; i++)
                Fx.Spawn(pos + new Vector2(0, 0.4f) + Random.insideUnitCircle * 0.3f, Random.insideUnitCircle * 3f, 0.5f, Random.Range(1f, 4f),
                    Random.Range(0.35f, 0.7f), BurstColor, new Color(0.08f, 0.06f, 0.12f), 4f, i % 3 == 0 ? 2 : 1);
            Pickup.Chance(pos, 0.55f, 0.18f);
            if (spawnId != null) Story.Set("dead_" + spawnId);
            Destroy(gameObject);
        }

        void Update()
        {
            if (Game.Paused) return;
            float dt = Time.deltaTime;
            stateClock += dt;
            var p = Player.I;
            bool here = Present;
            anim.sr.enabled = true;
            if (knockClock > 0)
            {
                knockClock -= dt;
                pos = Solids.Move(pos, knockVel * dt, half, this);
                knockVel *= Mathf.Exp(-9f * dt);          // the same slide to a stop at any frame rate
            }
            else if (p && p.state != Player.State.Dead && !(Story.I && Story.I.Running)) Think(dt, p);
            // touching hurts (only in the world we share)
            if (here && p && !health.Dead && touchDamage > 0 && Vector2.Distance(pos, p.pos) < half.x + 0.38f &&
                Mathf.Abs(pos.y - p.pos.y) < 0.5f && Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos))
                p.Hurt(new HitInfo { damage = touchDamage, from = pos, knockback = 6f, kind = HitKind.Slash, source = gameObject });
            if (flash > 0) flash -= dt;
            mat.SetFloat("_Flash", flash > 0 ? 0.85f : 0);
            anim.Tick(dt);
            Place();
        }

        protected void Move(Vector2 v, float dt)
        {
            vel = v;
            pos = flying ? pos + v * dt : Solids.Move(pos, v * dt, half, this);
        }

        protected Facing FaceOf(Vector2 d)
        {
            if (d.sqrMagnitude < 0.0001f) return facing;
            return Mathf.Abs(d.x) > Mathf.Abs(d.y) ? (d.x < 0 ? Facing.Left : Facing.Right) : (d.y < 0 ? Facing.Down : Facing.Up);
        }

        protected bool CanSee(Player p, float range) => p && Vector2.Distance(p.pos, pos) < range && Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos) && Present;

        void Place()
        {
            transform.position = new Vector3(pos.x, pos.y, 0);
            anim.sr.transform.localPosition = new Vector3(0, Mathf.Round(hover * 16f) / 16f, 0);
            int o = Map.Order(pos.y);
            anim.sr.sortingOrder = o;
            if (shadow) shadow.sortingOrder = o - 1;
        }
    }

    // ---------------------------------------------------------------------------------- crab
    /// <summary>Brine crab: scuttles sideways in bursts, rushes when Azar is close, snaps.</summary>
    public class Crab : Enemy
    {
        Vector2 dir;
        float next;
        public static Crab Spawn(Vector2 at) => Make<Crab>("crab", "idle", at, WorldLayer.Waking, 3);
        protected override void Init() { speed = 2.9f; half = new Vector2(0.45f, 0.16f); }
        protected override Color BurstColor => new Color(0.75f, 0.3f, 0.22f);

        protected override void Think(float dt, Player p)
        {
            next -= dt;
            if (CanSee(p, 5.2f))
            {
                var d = p.pos - pos;
                if (d.magnitude < 1.1f && next <= 0) { anim.Play("attack", Facing.Down, true); Sfx.Play("crab_snap", 0.7f); next = 0.9f; }
                // crabs come at you sideways
                var side = new Vector2(Mathf.Sign(d.x), Mathf.Clamp(d.y, -0.6f, 0.6f));
                if (anim.anim != "attack" || anim.Done) { anim.Play("walk", Facing.Down); Move(side.normalized * speed * 1.2f, dt); }
                return;
            }
            if (next <= 0)
            {
                dir = Random.value < 0.4f ? Vector2.zero : new Vector2(Random.value < 0.5f ? -1 : 1, Random.Range(-0.3f, 0.3f));
                if (Vector2.Distance(pos, home) > 3f) dir = (home - pos).normalized;
                next = Random.Range(0.5f, 1.4f);
            }
            if (dir == Vector2.zero) anim.Play("idle", Facing.Down);
            else { anim.Play("walk", Facing.Down); Move(dir * speed, dt); }
        }
    }

    // --------------------------------------------------------------------------------- jackal
    /// <summary>Jackal: circles at a distance, crouches, then lunges in a straight line.</summary>
    public class Jackal : Enemy
    {
        enum S { Prowl, Crouch, Lunge, Recover }
        S s;
        Vector2 lungeDir;
        float orbit;
        public static Jackal Spawn(Vector2 at) => Make<Jackal>("jackal", "idle", at, WorldLayer.Waking, 4);
        protected override void Init() { speed = 3.5f; half = new Vector2(0.5f, 0.16f); orbit = Random.value * 6f; }
        protected override Color BurstColor => new Color(0.62f, 0.5f, 0.34f);

        protected override void Think(float dt, Player p)
        {
            var d = p.pos - pos;
            switch (s)
            {
                case S.Prowl:
                    if (!CanSee(p, 7f))
                    {
                        var h = home - pos;
                        if (h.magnitude > 0.5f) { facing = FaceOf(h); anim.Play("walk", facing); Move(h.normalized * speed * 0.5f, dt); }
                        else anim.Play("idle", facing);
                        return;
                    }
                    orbit += dt * 0.9f;
                    var want = p.pos + new Vector2(Mathf.Cos(orbit), Mathf.Sin(orbit) * 0.7f) * 3.2f;
                    var w = want - pos;
                    facing = FaceOf(d);
                    anim.Play("run", FaceOf(w));
                    anim.SetFacing(FaceOf(w));
                    Move(w.normalized * Mathf.Min(speed, w.magnitude * 3f), dt);
                    if (stateClock > 1.25f && d.magnitude < 4.4f) { s = S.Crouch; stateClock = 0; facing = FaceOf(d); anim.Play("crouch", facing, true); Sfx.Play("jackal_growl", 0.7f); }
                    break;
                case S.Crouch:
                    facing = FaceOf(d);
                    anim.SetFacing(facing);
                    if (stateClock > 0.38f) { s = S.Lunge; stateClock = 0; lungeDir = d.normalized; anim.Play("lunge", FaceOf(lungeDir), true); Sfx.Play("jackal_bark", 0.8f); }
                    break;
                case S.Lunge:
                    Move(lungeDir * 10.4f * Mathf.Lerp(1f, 0.3f, stateClock / 0.42f), dt);
                    if (stateClock > 0.42f) { s = S.Recover; stateClock = 0; anim.Play("idle", facing, true); }
                    break;
                case S.Recover:
                    if (stateClock > 0.5f) { s = S.Prowl; stateClock = 0; }
                    break;
            }
        }

        protected override void OnHurt(HitInfo h) { s = S.Recover; stateClock = 0; }
        public override void Blocked(Player p) { base.Blocked(p); s = S.Recover; stateClock = -0.35f; anim.Play("idle", facing, true); }
    }

    // ---------------------------------------------------------------------------------- moth
    /// <summary>Moth-shade: lives only in the dream; flutters, then darts at Azar.</summary>
    public class Moth : Enemy
    {
        Vector2 drift;
        float dart;
        public static Moth Spawn(Vector2 at) => Make<Moth>("moth", "fly", at, WorldLayer.Dream, 1);
        /// <summary>How many moths are about (the king's chamber only ever draws a few).</summary>
        public static int All2() { int n = 0; foreach (var e in All) if (e is Moth) n++; return n; }
        protected override void Init() { flying = true; speed = 2.5f; hover = 0.6f; half = new Vector2(0.3f, 0.2f); }
        protected override Color BurstColor => new Color(0.55f, 0.45f, 0.9f);

        protected override void Think(float dt, Player p)
        {
            hover = 0.6f + Mathf.Sin(stateClock * 5f) * 0.12f;
            anim.Play("fly", Facing.Down);
            dart -= dt;
            if (CanSee(p, 6f))
            {
                var d = p.pos + new Vector2(0, 0.4f) - pos;
                if (dart <= 0 && d.magnitude < 3.6f) { drift = d.normalized * 7.6f; dart = 1.15f; Sfx.Play("moth", 0.6f); }
                drift = Vector2.Lerp(drift, d.normalized * speed + new Vector2(Mathf.Sin(stateClock * 7f), Mathf.Cos(stateClock * 5f)) * 1.5f, dt * 2.5f);
            }
            else drift = Vector2.Lerp(drift, (home - pos) * 0.8f + new Vector2(Mathf.Sin(stateClock * 3f), Mathf.Cos(stateClock * 2f)), dt * 2f);
            Move(drift, dt);
        }
    }

    // ------------------------------------------------------------------------------ sentinel
    /// <summary>Bronze sentinel: walks a beat; when Azar lines up with it, it levels the spear and
    /// charges. Blows bounce off the front of its shield.</summary>
    public class Sentinel : Enemy
    {
        enum S { Patrol, Aim, Charge, Stuck }
        S s;
        Vector2 chargeDir;
        public Vector2[] beat;
        int leg;
        public static Sentinel Spawn(Vector2 at) => Make<Sentinel>("sentinel", "idle", at, WorldLayer.Both, 5);
        protected override void Init() { speed = 1.6f; half = new Vector2(0.32f, 0.16f); touchDamage = 2; }
        protected override float KnockScale => 0.35f;
        protected override string HurtSound => "clank";
        protected override Color BurstColor => new Color(0.85f, 0.55f, 0.25f);

        protected override bool Accepts(HitInfo h)
        {
            if (s == S.Stuck || h.kind == HitKind.Reflected || h.kind == HitKind.Fire) return true;
            // the shield faces where the sentinel faces
            var from = ((Vector2)h.from - pos).normalized;
            var f = facing == Facing.Down ? Vector2.down : facing == Facing.Up ? Vector2.up : facing == Facing.Left ? Vector2.left : Vector2.right;
            return Vector2.Dot(from, f) < 0.5f;
        }

        protected override void Think(float dt, Player p)
        {
            var d = p.pos - pos;
            switch (s)
            {
                case S.Patrol:
                {
                    var target = beat != null && beat.Length > 0 ? beat[leg] : home;
                    var w = target - pos;
                    if (w.magnitude < 0.1f) { if (beat != null && beat.Length > 0) leg = (leg + 1) % beat.Length; anim.Play("idle", facing); }
                    else { facing = FaceOf(w); anim.Play("walk", facing); anim.SetFacing(facing); Move(w.normalized * speed, dt); }
                    bool lined = (Mathf.Abs(d.x) < 0.45f || Mathf.Abs(d.y) < 0.45f) && d.magnitude < 7f;
                    if (lined && CanSee(p, 7f)) { s = S.Aim; stateClock = 0; facing = FaceOf(d); anim.Play("idle", facing, true); Sfx.Play("sentinel_alert", 0.8f); }
                    break;
                }
                case S.Aim:
                    if (stateClock > 0.42f)
                    {
                        s = S.Charge; stateClock = 0;
                        chargeDir = facing == Facing.Down ? Vector2.down : facing == Facing.Up ? Vector2.up : facing == Facing.Left ? Vector2.left : Vector2.right;
                        anim.Play(anim.model ? "run" : "walk", facing, true);
                    }
                    break;
                case S.Charge:
                {
                    var before = pos;
                    Move(chargeDir * 7.2f, dt);
                    if ((pos - before).magnitude < 7.2f * dt * 0.3f || stateClock > 1.6f)
                    {
                        // slammed into something: stuck for a moment, open to a blow
                        s = S.Stuck; stateClock = 0; PixelView.I.Shake(1, 0.15f); Sfx.Play("clank"); anim.Play("hurt", facing, true);
                    }
                    break;
                }
                case S.Stuck:
                    if (stateClock > 1.0f) { s = S.Patrol; stateClock = 0; }
                    break;
            }
        }

        /// <summary>Bronze on bronze: a charge that meets the mirror shield stops dead, and so does the sentinel.</summary>
        public override void Blocked(Player p)
        {
            base.Blocked(p);
            if (s == S.Charge) { s = S.Stuck; stateClock = 0; anim.Play("hurt", facing, true); PixelView.I.Shake(1, 0.15f); }
        }
    }
}
