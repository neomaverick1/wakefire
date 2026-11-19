// The Brazen Bull: High Priest Ebrum's guilt, cast in bronze with a furnace in its belly.
// It charges in straight lines (dodge, and let it hit a pillar: it reels, open to the blade),
// and it breathes fire (the Bronze Mirror Shield sends that fire back into its face). At half
// strength it loses its temper: faster charges, wider fire, and it doesn't stop to think.
// Also here: the bull's-head statue in the gallery, which only fire can break.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public class BrazenBull : MonoBehaviour, IHittable
    {
        public static BrazenBull I;
        enum S { Wait, Idle, Aim, Charge, Stun, Shoot, Dying }
        S s = S.Wait;
        public Vector2 pos;
        public Health health;
        SpriteAnim anim;
        Material mat;
        SpriteRenderer shadow;
        Facing facing = Facing.Down;
        float clock, flash;
        Vector2 dir;
        int charges;
        LightBlob glow;
        readonly Vector2 half = new Vector2(1.0f, 0.35f);
        public System.Action Defeated;
        public bool Enraged => health.hp <= health.max / 2;

        public static BrazenBull Spawn(Vector2 at)
        {
            var go = new GameObject("BrazenBull");
            go.transform.SetParent(Map.Current.transform, false);
            var b = go.AddComponent<BrazenBull>();
            I = b;
            b.pos = at;
            var body = new GameObject("Sprite");
            body.transform.SetParent(go.transform, false);
            var sr = body.AddComponent<SpriteRenderer>();
            b.mat = new Material(Map.SpriteMat);
            sr.sharedMaterial = b.mat;
            b.anim = body.AddComponent<SpriteAnim>();
            b.anim.sr = sr;
            b.anim.sheet = SpriteSheet.Load("bull");
            b.anim.Play("idle", Facing.Down, true);
            b.health = go.AddComponent<Health>();
            b.health.max = b.health.hp = 16;
            b.shadow = Npc.MakeShadow(go.transform, WorldLayer.Both, 30);
            b.glow = LightBlob.Create(go.transform, at + new Vector2(0, 1f), 4.5f, new Color(1f, 0.55f, 0.22f), 0.7f, true);
            b.Place();
            return b;
        }

        public void Begin() { s = S.Idle; clock = 0; }

        public bool Hit(HitInfo h)
        {
            if (s == S.Wait || s == S.Dying) return false;
            bool open = s == S.Stun || h.kind == HitKind.Reflected;
            if (!open)
            {
                Sfx.Play("clank");
                Fx.Sparks(pos + new Vector2(0, 1.4f), new Color(1f, 0.85f, 0.5f), 6);
                return true;
            }
            if (!health.Take(h)) return false;
            flash = 0.2f;
            health.invulnerable = 0.2f;
            Sfx.Play(h.kind == HitKind.Reflected ? "boss_burn" : "boss_hit");
            PixelView.I.Shake(h.kind == HitKind.Reflected ? 3 : 1, 0.2f);
            if (h.kind == HitKind.Reflected && s != S.Stun) { s = S.Stun; clock = 0.6f; anim.Play("hurt", facing, true); }
            if (health.Dead) StartCoroutine(Die());
            return true;
        }

        void Update()
        {
            if (Game.Paused) return;
            float dt = Time.deltaTime;
            clock += dt;
            var p = Player.I;
            if (flash > 0) flash -= dt;
            mat.SetFloat("_Flash", flash > 0 ? 0.9f : 0);
            if (p && s != S.Wait && s != S.Dying && !(Story.I && Story.I.Running)) Think(dt, p);
            anim.Tick(dt);
            // touching the bull hurts, a charging bull hurts a lot
            if (p && s != S.Wait && s != S.Dying && s != S.Stun && Mathf.Abs(p.pos.x - pos.x) < half.x + 0.3f && Mathf.Abs(p.pos.y - pos.y) < half.y + 0.35f)
                p.Hurt(new HitInfo { damage = s == S.Charge ? 3 : 2, from = pos, knockback = 9f, kind = HitKind.Crush, source = gameObject });
            Place();
        }

        void Think(float dt, Player p)
        {
            var d = p.pos - pos;
            float speedK = Enraged ? 1.3f : 1f;
            switch (s)
            {
                case S.Idle:
                    facing = FaceOf(d);
                    anim.Play("walk", facing);
                    anim.SetFacing(facing);
                    pos = Solids.Move(pos, d.normalized * 1.6f * speedK * dt, half, this);
                    if (clock > (Enraged ? 0.7f : 1.3f))
                    {
                        clock = 0;
                        if (Random.value < (Enraged ? 0.45f : 0.38f)) { s = S.Shoot; anim.Play("shoot", facing, true); }
                        else { s = S.Aim; anim.Play("idle", facing, true); Sfx.Play("bull_snort"); }
                    }
                    break;
                case S.Aim:
                    facing = FaceOf(d);
                    anim.SetFacing(facing);
                    if (clock > (Enraged ? 0.35f : 0.6f))
                    {
                        dir = d.normalized;
                        s = S.Charge; clock = 0;
                        anim.Play("charge", FaceOf(dir), true);
                        Sfx.Play("bull_roar");
                    }
                    break;
                case S.Charge:
                {
                    var before = pos;
                    float sp = 9.5f * speedK;
                    pos = Solids.Move(pos, dir * sp * dt, half, this);
                    if (((int)(clock * 20)) % 2 == 0) Fx.Dust(pos, 1);
                    if (Enraged && ((int)(clock * 30)) % 3 == 0) Fx.Embers(pos + new Vector2(0, 0.8f), 1);
                    bool blocked = (pos - before).magnitude < sp * dt * 0.35f;
                    if (blocked || clock > 2.2f)
                    {
                        bool pillar = HitPillar();
                        PixelView.I.Shake(pillar ? 4 : 2, 0.35f);
                        Sfx.Play("bull_crash");
                        charges++;
                        if (pillar || charges % 3 == 0) { s = S.Stun; clock = 0; anim.Play("stun", facing, true); Sfx.Play("bull_daze"); }
                        else { s = S.Idle; clock = Enraged ? 0.3f : 0; }
                    }
                    break;
                }
                case S.Stun:
                    if (((int)(clock * 8)) % 4 == 0) Fx.Sparks(pos + new Vector2(0, 2.2f), new Color(1f, 0.9f, 0.5f), 1);
                    if (clock > 2.6f) { s = S.Idle; clock = 0; }
                    break;
                case S.Shoot:
                    if (anim.Frame == 2 && clock < 10f)
                    {
                        int n = Enraged ? 5 : 3;
                        var mouth = pos + FaceVec(facing) * 1.4f + new Vector2(0, 0.2f);
                        var aim = (p.pos - mouth).normalized;
                        for (int i = 0; i < n; i++)
                        {
                            float a = (i - (n - 1) / 2f) * (Enraged ? 16f : 20f);
                            var v = (Vector2)(Quaternion.Euler(0, 0, a) * aim) * 5.2f;
                            Projectile.Fireball(mouth, v, gameObject);
                        }
                        clock = 10f;   // fire once per breath
                    }
                    if (anim.Done) { s = S.Idle; clock = 0; }
                    break;
            }
        }

        bool HitPillar()
        {
            var m = Map.Current;
            foreach (var pr in m.props)
                if (pr && pr.Kind == "pillar" && Vector2.Distance(pr.basePos, pos + dir * 1.2f) < 1.9f)
                {
                    Fx.Dust(pr.basePos, 8);
                    return true;
                }
            return false;
        }

        IEnumerator Die()
        {
            s = S.Dying;
            anim.Play("death", Facing.Down, true);
            Sfx.Play("boss_die");
            for (int i = 0; i < 24; i++)
            {
                Fx.Sparks(pos + new Vector2(Random.Range(-1f, 1f), Random.Range(0.5f, 2.4f)), new Color(1f, 0.75f, 0.35f), 4);
                PixelView.I.Shake(2, 0.1f);
                yield return new WaitForSeconds(0.08f);
            }
            glow.intensity = 0.2f;
            yield return new WaitForSeconds(0.8f);
            Defeated?.Invoke();
        }

        static Vector2 FaceVec(Facing f) => f == Facing.Down ? Vector2.down : f == Facing.Up ? Vector2.up : f == Facing.Left ? Vector2.left : Vector2.right;

        static Facing FaceOf(Vector2 d)
        {
            if (d.sqrMagnitude < 0.0001f) return Facing.Down;
            return Mathf.Abs(d.x) > Mathf.Abs(d.y) ? (d.x < 0 ? Facing.Left : Facing.Right) : (d.y < 0 ? Facing.Down : Facing.Up);
        }

        void Place()
        {
            transform.position = new Vector3(pos.x, pos.y, 0);
            int o = Map.Order(pos.y);
            anim.sr.sortingOrder = o;
            shadow.sortingOrder = o - 1;
            if (glow) glow.transform.position = (Vector3)(pos + new Vector2(0, 1.2f));
        }
    }

    /// <summary>A bronze bull's head set in the wall: it breathes fire down the gallery whenever
    /// Azar stands in front of it, and only its own fire, sent back, can crack it.</summary>
    public class BullHead : MonoBehaviour, IHittable
    {
        public Prop prop;
        public string flag;
        float clock;

        public bool Hit(HitInfo h)
        {
            if (h.kind != HitKind.Reflected) { Sfx.Play("clank"); Fx.Sparks(prop.basePos + new Vector2(0, 1f), new Color(1f, 0.85f, 0.5f), 4); return true; }
            Story.Set(flag);
            Sfx.Play("statue_break");
            PixelView.I.Shake(3, 0.5f);
            for (int i = 0; i < 20; i++)
                Fx.Spawn(prop.basePos + new Vector2(0, 0.8f), Random.insideUnitCircle * 4f, 0.6f, Random.Range(2f, 6f), Random.Range(0.4f, 0.9f),
                    new Color(0.85f, 0.55f, 0.25f), new Color(0.3f, 0.18f, 0.1f), 16f, i % 3 == 0 ? 2 : 1);
            Map.Current.props.Remove(prop);
            prop.Shatter();
            Destroy(this);
            return true;
        }

        void Update()
        {
            if (Game.Paused || !prop) return;
            var p = Player.I;
            if (!p || (Story.I && Story.I.Running)) return;
            clock += Time.deltaTime;
            var d = p.pos - prop.basePos;
            if (d.y < -0.5f && Mathf.Abs(d.x) < 2.2f && d.magnitude < 9f && clock > 2.0f)
            {
                clock = 0;
                var mouth = prop.basePos + new Vector2(0, -0.4f);
                Projectile.Fireball(mouth, (p.pos - mouth).normalized * 4.6f, gameObject);
            }
        }
    }
}
