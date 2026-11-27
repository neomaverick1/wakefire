// Stay-Ups. A shadow cannot lie down while there is a moon. The people of the Lower Town have
// been asleep for forty nights and their shadows have been up for all of them, with nobody to
// be the shadow of. A Stay-Up is a man's shadow with no man: it lies long across the ground,
// goes under walls and out the other side, and it has no interest in Azar at all. It wants
// his shadow, which is still attached to somebody.
//
// It does not take hold of him. It takes hold of his shadow, and his feet stop answering him.
// A blade goes through it: there is nothing there. Firelight is another matter. In the light of
// a lit bowl, of the Wakefire held out, of the mirror shield with the flame in it, a Stay-Up
// thins, lets go, and runs for the dark.
using UnityEngine;

namespace Wakefire
{
    public class StayUp : Enemy
    {
        enum S { Lie, Creep, Grip, Slink, Burn }
        S s;
        float burn, cool, thin, rest, sear;
        bool tugged;
        static readonly Material[] deep = new Material[3];
        MaterialPropertyBlock block;
        SpriteRenderer shade;

        /// <summary>How far a shadow runs along the ground for each unit of height, as the moon has it: his does.</summary>
        public static readonly Vector2 Cast = new Vector2(0.66f, -0.40f);
        /// <summary>A Stay-Up lies the other way: up the street, towards the moon. It is the first thing wrong with it.</summary>
        public static readonly Vector2 Own = new Vector2(0.22f, 0.90f);
        const float Hands = 2.0f;                 // how high its hands are, in tiles

        public static StayUp Spawn(Vector2 at) => Make<StayUp>("sleeper_a", "idle", at, WorldLayer.Waking, 3, "stayup");

        protected override void Init()
        {
            speed = 3.1f; half = new Vector2(0.3f, 0.15f); touchDamage = 0; flying = true; roams = true;
            mat.SetFloat("_Dissolve", 1.05f);                   // the man is not there. Only what he would throw on the ground is.
            if (anim.model) anim.model.shadeOverride = Deep((int)layer);
            rest = Random.Range(0f, 2f);
        }

        /// <summary>The shadow material for something that is only a shadow: darker than any real one, longer, and
        /// drawn over the top of whatever shade is already there.</summary>
        static Material Deep(int layer)
        {
            layer = Mathf.Clamp(layer, 0, 2);
            if (!deep[layer])
            {
                var src = Map.ShadeMat(layer);
                if (!src) return null;
                deep[layer] = new Material(src);
                deep[layer].SetFloat("_Layer", layer);
                deep[layer].SetFloat("_Deep", 1f);
                deep[layer].SetVector("_Own", new Vector4(Own.x, Own.y, 0, 0));
                deep[layer].SetFloat("_Ref", 2f);
            }
            return deep[layer];
        }

        public override bool Sleeps => false;

        protected override bool WaitsOutStories => true;
        /// <summary>It has his shadow.</summary>
        public bool Gripping => s == S.Grip;
        /// <summary>For the test log: what it is doing.</summary>
        public string Doing => s.ToString();
        /// <summary>It is in firelight, and going.</summary>
        public bool Burning => s == S.Burn;
        protected override Color BurstColor => new Color(0.10f, 0.10f, 0.22f);
        protected override string HurtSound => "stayup_burn";
        /// <summary>The place on the ground where its hands are.</summary>
        public Vector2 Grasp => pos + Own * Hands;
        public override Rect HitBox { get { var g = pos + Own * 1.2f; return new Rect(g.x - 0.6f, g.y - 1.1f, 1.2f, 2.2f); } }

        /// <summary>Only light. A blade finds the ground.</summary>
        protected override bool Untouchable(HitInfo h) => !(h.kind == HitKind.Fire || h.kind == HitKind.Reflected);

        /// <summary>Is there firelight on this piece of ground? Azar's own flame does not count: he carries it above
        /// his shadow, not on it. (A light's place on the map is where the flame shows; the ground under it is lower.)</summary>
        public static bool Lit(Vector2 q)
        {
            var p = Player.I;
            foreach (var l in LightBlob.All)
            {
                if (!l || !l.isActiveAndEnabled || l.intensity < 0.3f || l.radius < 1.4f) continue;
                if (p && l == p.lantern && p.flare <= 0) continue;
                Vector2 c = (Vector2)l.transform.position - new Vector2(0, l.height);
                float reach = p && l == p.lantern ? 2.4f : l.radius * 0.5f;
                if (Vector2.Distance(c, q) < reach) return true;
            }
            return false;
        }

        /// <summary>Is fire being brought to this piece of ground: the Wakefire held out, the mirror shield throwing it
        /// ahead of him, a bowl somebody has lit? Lamps on walls are only light: it keeps out of them. These burn it.</summary>
        public static bool Seared(Vector2 q, bool mirror = true)
        {
            var p = Player.I;
            if (p && !p.Hidden)
            {
                if (p.flare > 0 && Vector2.Distance(p.pos, q) < 2.6f) return true;
                if (mirror && p.Guarding && p.hasShield && p.hasLantern && Vector2.Distance(p.pos + p.Dir * 1.15f, q) < 1.6f) return true;
            }
            var map = Map.Current;
            if (map)
                foreach (var pr in map.props)
                    if (pr && pr.Kind == "brazier" && pr.lit && Vector2.Distance(pr.basePos, q) < 2.6f) return true;
            return false;
        }

        /// <summary>Where Azar's shadow lies: the middle of it, and whether he has one at all just now.</summary>
        static bool HisShadow(Player p, out Vector2 at)
        {
            at = p.pos + Cast * 1.5f;
            if (p.Hidden) return false;
            return !Lit(p.pos + Cast * 0.9f);
        }

        protected override void Think(float dt, Player p)
        {
            cool -= dt;
            // fire brought to any of it, and it is burning
            bool lit = Seared(pos + Own * 0.6f) || Seared(Grasp) || Seared(pos + Own * 1.3f);
            if (lit && s != S.Burn) { s = S.Burn; stateClock = 0; sear = 0; Sfx.Play("stayup_burn", 0.7f, 0.08f); }

            bool has = HisShadow(p, out var his);
            var want = his - Own * Hands;                        // where it has to lie for its hands to be on his shadow
            switch (s)
            {
                case S.Lie:
                    anim.Play("idle", facing);
                    vel = Vector2.zero;
                    if ((rest -= dt) <= 0 && has && CanSee(p, 7.5f)) { s = S.Creep; stateClock = 0; Sfx.Play("stayup_stir", 0.5f, 0.1f); }
                    break;

                case S.Creep:
                {
                    if (!CanSee(p, 11f)) { s = S.Slink; stateClock = 0; break; }
                    var d = want - pos;
                    Turn(his - pos);
                    anim.Play("walk", facing);
                    // without a shadow to go for (he is standing in the light) it waits at the edge of it
                    if (!has) { if (d.magnitude < 3.2f) Glide(-d.normalized * speed * 0.6f, dt); else vel = Vector2.zero; break; }
                    Glide(d.normalized * Mathf.Min(speed, d.magnitude * 6f), dt);
                    if (d.magnitude < 0.3f && cool <= 0 && Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos))
                    {
                        s = S.Grip; stateClock = 0; tugged = false;
                        anim.Play("grip", facing, true);
                        Sfx.Play("stayup_grip", 0.9f, 0.05f);
                        PixelView.I.Shake(1, 0.12f);
                        if (Story.I) Story.I.StayUpGripped();
                    }
                    break;
                }

                case S.Grip:
                    // it has his shadow. He can do anything he likes except go anywhere.
                    if (!has || p.state == Player.State.Dead || Vector2.Distance(want, pos) > 1.2f) { Leave(0.6f); break; }
                    pos = Vector2.MoveTowards(pos, want, 6f * dt);
                    p.rooted = 0.12f;
                    if (!tugged && stateClock > 1.15f)
                    {
                        tugged = true;
                        // one pull, on the shadow; he feels it everywhere else
                        p.Hurt(new HitInfo { damage = 1, from = p.pos - Cast.normalized, knockback = 2.5f, kind = HitKind.Crush, source = gameObject });
                        Sfx.Play("stayup_tug", 0.9f, 0.05f);
                    }
                    if (stateClock > 1.6f) Leave(1.8f);
                    break;

                case S.Slink:
                {
                    var h = home - pos;
                    if (h.magnitude < 0.2f) { s = S.Lie; rest = Random.Range(1.5f, 3.5f); break; }
                    Turn(h);
                    anim.Play("walk", facing);
                    Glide(h.normalized * speed * 0.9f, dt);
                    if (stateClock > 1.2f && cool <= 0 && has && CanSee(p, 6f)) { s = S.Creep; stateClock = 0; }
                    break;
                }

                case S.Burn:
                {
                    // out of the light, any way that is out of it; home if there is no telling
                    sear += dt;
                    if (sear > 0.4f)
                    {
                        sear = 0;
                        if (health.Take(new HitInfo { damage = 1, from = p.pos, kind = HitKind.Fire }))
                        {
                            flash = 0.12f;
                            for (int i = 0; i < 6; i++)
                                Fx.Spawn(pos + Own * Random.Range(0.2f, 2.3f) + Random.insideUnitCircle * 0.2f, Random.insideUnitCircle * 0.8f, 0.05f, Random.Range(0.6f, 1.6f),
                                    Random.Range(0.4f, 0.8f), new Color(0.16f, 0.16f, 0.30f, 0.9f), new Color(0.05f, 0.05f, 0.12f, 0f), -0.6f, i % 2 + 1);
                            if (health.Dead) { Rooms.Slain(this); Die(); return; }
                        }
                    }
                    var away = home - pos;
                    if (away.magnitude < 0.5f) away = pos - p.pos;
                    Turn(away);
                    anim.Play("walk", facing);
                    Glide(away.normalized * speed * 1.9f, dt);
                    if (!lit && stateClock > 0.5f) { s = S.Slink; stateClock = 0; cool = 2.2f; }
                    break;
                }
            }
            // it is thinner in the light and for a moment after it has let go
            float wantThin = s == S.Burn ? 0.55f : 0f;
            thin = Mathf.MoveTowards(thin, wantThin, dt * 3f);
            Paint();
        }

        void Leave(float wait)
        {
            s = S.Slink; stateClock = 0; cool = wait;
            anim.Play("walk", facing, true);
        }

        void Turn(Vector2 d)
        {
            if (d.sqrMagnitude < 0.0004f) return;
            facing = FaceOf(d);
            anim.SetFacing(facing);
        }

        /// <summary>A shadow is not stopped by anything it falls on. It stays on the map.</summary>
        void Glide(Vector2 v, float dt)
        {
            vel = v;
            var to = pos + v * dt;
            var m = Map.Current;
            if (m && !m.bounds.Contains(to)) return;
            // it will not go into lamplight of its own accord: round the edge of it, or not at all
            // (if it is standing in some already, it may leave by any way there is)
            bool inIt = Lit(pos + Own * 0.6f) || Lit(pos + Own * Hands);
            if (s != S.Burn && !inIt && (Lit(to + Own * 0.6f) || Lit(to + Own * Hands)))
            {
                var side = new Vector2(-v.y, v.x) * dt;
                if (!Lit(pos + side + Own * 0.6f) && !Lit(pos + side + Own * Hands)) to = pos + side;
                else if (!Lit(pos - side + Own * 0.6f) && !Lit(pos - side + Own * Hands)) to = pos - side;
                else { vel = Vector2.zero; return; }
            }
            pos = to;
        }

        void Paint()
        {
            if (!shade && anim.model) shade = anim.model.ShadowRenderer;
            if (!shade) return;
            if (block == null) block = new MaterialPropertyBlock();
            shade.GetPropertyBlock(block);
            block.SetFloat("_Thin", thin);
            shade.SetPropertyBlock(block);
        }

        protected override void Die()
        {
            // burnt off: there is a sleeper somewhere who turns over
            for (int i = 0; i < 14; i++)
                Fx.Spawn(pos + Own * Random.Range(0f, 2.4f) + Random.insideUnitCircle * 0.25f, Random.insideUnitCircle * 1.2f, 0.05f, Random.Range(0.8f, 2.2f),
                    Random.Range(0.5f, 1.0f), new Color(0.18f, 0.18f, 0.34f, 0.9f), new Color(0.05f, 0.05f, 0.12f, 0f), -0.8f, i % 2 + 1);
            Sfx.Play("stayup_gone", 0.9f, 0.05f);
            if (Story.I) Story.I.StayUpGone(this);
            if (spawnId != null) Story.Set("dead_" + spawnId);
            Destroy(gameObject);
        }
    }
}
