// The two clay armies of the Generals' Barrow. Ushur's are red and carry spears: they march on
// whoever is nearest, line him up and charge, a shield in front of them. Baltu's are blue and
// carry slings: they keep their distance and throw, and a clay bullet that meets the mirror
// shield goes back to the man who threw it. Each army's first enemy is the other one: put a red
// and a blue in the same room and neither has any time for Azar until one of them is in pieces.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public abstract class ClaySoldier : Enemy
    {
        /// <summary>0: Ushur's red. 1: Baltu's blue.</summary>
        public int side;
        /// <summary>Stands like the statue it is until the story has this flag (the truce).</summary>
        public string holdFlag;

        protected override float KnockScale => 0.3f;
        protected override string HurtSound => "clay_hit";
        protected override Color BurstColor => side == 0 ? new Color(0.74f, 0.36f, 0.28f) : new Color(0.42f, 0.46f, 0.70f);

        protected bool Held => !string.IsNullOrEmpty(holdFlag) && !Story.Has(holdFlag);

        /// <summary>The nearest of the other army that is still standing, if any is in reach.</summary>
        protected ClaySoldier Foe(float range = 14f)
        {
            ClaySoldier best = null;
            float bd = range;
            foreach (var e in All)
            {
                if (!(e is ClaySoldier c) || c.side == side || c.health.Dead) continue;
                float d = Vector2.Distance(c.pos, pos);
                if (d < bd) { bd = d; best = c; }
            }
            return best;
        }

        /// <summary>How many of each army are standing (red, blue).</summary>
        public static void Count(out int red, out int blue)
        {
            red = blue = 0;
            foreach (var e in All)
                if (e is ClaySoldier c && !c.health.Dead) { if (c.side == 0) red++; else blue++; }
        }

        /// <summary>The war is over and there is nobody left to tell: back to clay.</summary>
        public void Crumble() { if (!health.Dead) { health.hp = 0; Rooms.Slain(this); Die(); } }

        protected static Vector2 Dir(Facing f) => f == Facing.Down ? Vector2.down : f == Facing.Up ? Vector2.up : f == Facing.Left ? Vector2.left : Vector2.right;

        protected override void Die()
        {
            Sfx.Play("pot_break");
            var c = BurstColor;
            for (int i = 0; i < 16; i++)
                Fx.Spawn(pos + new Vector2(0, 0.6f) + Random.insideUnitCircle * 0.3f, Random.insideUnitCircle * 3.6f, 0.5f, Random.Range(3f, 6f), Random.Range(0.4f, 0.8f),
                    i % 4 == 0 ? c : new Color(0.74f, 0.46f, 0.32f), new Color(0.36f, 0.20f, 0.16f), 18f, i % 3 == 0 ? 2 : 1);
            base.Die();
        }
    }

    // ---------------------------------------------------------------------------- Ushur's spearmen
    public class Spearman : ClaySoldier
    {
        enum S { Stand, Stir, March, Aim, Charge, Stuck }
        S s;
        Vector2 chargeDir;
        bool struck;

        public static Spearman Spawn(Vector2 at)
        {
            var e = Make<Spearman>("sentinel", "idle", at, WorldLayer.Both, 6, "clay_red");
            e.side = 0;
            return e;
        }

        protected override void Init() { speed = 1.9f; half = new Vector2(0.32f, 0.16f); touchDamage = 0; }

        public override void Blocked(Player p)
        {
            base.Blocked(p);
            if (s == S.Charge) { s = S.Stuck; stateClock = 0; anim.Play("hurt", facing, true); PixelView.I.Shake(1, 0.15f); }
        }

        void Stir()
        {
            s = S.Stir; stateClock = 0; touchDamage = 2;
            Sfx.Play("clay_wake", 0.8f);
            Fx.Dust(pos, 8);
        }

        protected override bool Accepts(HitInfo h)
        {
            if (s == S.Stand || s == S.Stir || s == S.Stuck || h.kind == HitKind.Reflected || h.kind == HitKind.Fire || h.kind == HitKind.Thrown) return true;
            if (h.source && h.source.GetComponent<ClaySoldier>()) return true;          // clay breaks clay
            var from = ((Vector2)h.from - pos).normalized;
            return Vector2.Dot(from, Dir(facing)) < 0.5f;
        }

        protected override void OnHurt(HitInfo h) { if (s == S.Stand) Stir(); }

        protected override void Think(float dt, Player p)
        {
            var foe = Foe();
            Vector2 target = foe ? foe.pos : p.pos;
            var d = target - pos;
            switch (s)
            {
                case S.Stand:
                    anim.Play("idle", facing);
                    if (Held) break;
                    if (foe || CanSee(p, 3.6f)) Stir();
                    break;
                case S.Stir:
                    facing = FaceOf(d);
                    anim.SetFacing(facing);
                    if (stateClock > 0.6f) { s = S.March; stateClock = 0; }
                    break;
                case S.March:
                {
                    if (d.magnitude > 0.9f)
                    {
                        facing = FaceOf(d); anim.Play("walk", facing); anim.SetFacing(facing);
                        // come at him along whichever line is nearer to being a straight one
                        var step = Mathf.Abs(d.x) < Mathf.Abs(d.y) ? new Vector2(Mathf.Sign(d.x) * Mathf.Min(1f, Mathf.Abs(d.x) * 2f), Mathf.Sign(d.y) * 0.45f)
                                                                 : new Vector2(Mathf.Sign(d.x) * 0.45f, Mathf.Sign(d.y) * Mathf.Min(1f, Mathf.Abs(d.y) * 2f));
                        Move(step.normalized * speed, dt);
                    }
                    else anim.Play("idle", facing);
                    bool lined = (Mathf.Abs(d.x) < 0.5f || Mathf.Abs(d.y) < 0.5f) && d.magnitude < 7f;
                    if (lined && stateClock > 0.7f && (foe || CanSee(p, 7.5f)))
                    {
                        s = S.Aim; stateClock = 0; facing = FaceOf(d); anim.Play("idle", facing, true); Sfx.Play("sentinel_alert", 0.6f, 0.02f);
                    }
                    break;
                }
                case S.Aim:
                    if (stateClock > 0.4f)
                    {
                        s = S.Charge; stateClock = 0; struck = false;
                        chargeDir = Dir(facing);
                        anim.Play(anim.model ? "run" : "walk", facing, true);
                    }
                    break;
                case S.Charge:
                {
                    var before = pos;
                    Move(chargeDir * 6.6f, dt);
                    if (!struck)
                        foreach (var e in All)
                        {
                            if (!(e is ClaySoldier c) || c.side == side || c.health.Dead || Vector2.Distance(c.pos, pos) > 0.8f) continue;
                            c.Hit(new HitInfo { damage = 3, from = pos, knockback = 6f, kind = HitKind.Heavy, source = gameObject });
                            struck = true;
                            HitStop.Do(0.04f);
                            break;
                        }
                    if (struck || (pos - before).magnitude < 6.6f * dt * 0.3f || stateClock > 1.5f)
                    {
                        s = S.Stuck; stateClock = 0; PixelView.I.Shake(1, 0.15f); Sfx.Play("clay_hit"); anim.Play("hurt", facing, true);
                    }
                    break;
                }
                case S.Stuck:
                    if (stateClock > 1.0f) { s = S.March; stateClock = 0; }
                    break;
            }
        }
    }

    // ---------------------------------------------------------------------------- Baltu's slingers
    public class Slinger : ClaySoldier
    {
        enum S { Stand, Stir, Ready, Wind, Loosed }
        S s;
        float wait;
        Vector2 aim;

        public static Slinger Spawn(Vector2 at)
        {
            var e = Make<Slinger>("sentinel", "idle", at, WorldLayer.Both, 2, "clay_blue");
            e.side = 1;
            return e;
        }

        protected override void Init() { speed = 1.6f; half = new Vector2(0.3f, 0.16f); touchDamage = 0; wait = Random.Range(0.6f, 2.0f); }

        public bool Winding => s == S.Wind;

        void Stir()
        {
            s = S.Stir; stateClock = 0; touchDamage = 1;
            Sfx.Play("clay_wake", 0.7f);
            Fx.Dust(pos, 6);
        }

        protected override void OnHurt(HitInfo h) { if (s == S.Stand) Stir(); }

        protected override void Think(float dt, Player p)
        {
            var foe = Foe();
            Vector2 target = foe ? foe.pos : p.pos;
            var d = target - pos;
            switch (s)
            {
                case S.Stand:
                    anim.Play("idle", facing);
                    if (Held) break;
                    if (foe || CanSee(p, 9f)) Stir();
                    break;
                case S.Stir:
                    facing = FaceOf(d); anim.SetFacing(facing);
                    if (stateClock > 0.6f) { s = S.Ready; stateClock = 0; }
                    break;
                case S.Ready:
                {
                    facing = FaceOf(d); anim.SetFacing(facing);
                    // a slinger wants room: too close and he gives ground, sideways if he must
                    if (d.magnitude < 3.2f)
                    {
                        anim.Play("walk", facing);
                        var before = pos;
                        Move(-d.normalized * speed, dt);
                        if ((pos - before).magnitude < speed * dt * 0.3f) Move(new Vector2(-d.y, d.x).normalized * speed * (markerId != null && markerId.GetHashCode() % 2 == 0 ? 1 : -1), dt);
                    }
                    else anim.Play("idle", facing);
                    wait -= dt;
                    bool sees = foe || CanSee(p, 11f);
                    if (wait <= 0 && sees && d.magnitude < 11f)
                    {
                        s = S.Wind; stateClock = 0;
                        anim.Play("throw", facing, true);
                        Sfx.Play("sling_wind", 0.7f, 0.04f);
                    }
                    break;
                }
                case S.Wind:
                    facing = FaceOf(d); anim.SetFacing(facing);
                    aim = (target + new Vector2(0, 0.2f) - pos).normalized;
                    if (stateClock > 0.62f)
                    {
                        var b = Projectile.Bullet(pos + aim * 0.5f + new Vector2(0, 0.1f), aim * 8.2f, gameObject);
                        b.side = side;
                        Sfx.Play("stick_throw", 0.8f, 0.05f);
                        s = S.Loosed; stateClock = 0;
                    }
                    break;
                case S.Loosed:
                    if (stateClock > 0.35f) { s = S.Ready; stateClock = 0; wait = Random.Range(1.5f, 2.3f); }
                    break;
            }
        }
    }
}
