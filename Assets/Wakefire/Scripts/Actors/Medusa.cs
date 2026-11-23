// The doorkeepers of the high halls. The temple took them on because nobody argues with a
// doorkeeper they cannot look at. A Medusa is found with her back to the room, at her hair
// (the hair is against it). She turns; the snakes stand up and the light comes into her eyes;
// and then she looks. Whoever is looking back is stone for as long as the Wakefire takes to
// burn it off him, and she comes over while he waits. Raise the Bronze Mirror square to her and
// it is her own eyes she meets: she is stone instead, and stone can be cut. What does not look
// at her (a turned back, a man asleep on his feet) she can do nothing about but bite.
using UnityEngine;

namespace Wakefire
{
    public class Medusa : Enemy
    {
        enum S { Comb, Turn, Stalk, Stare, Gaze, Stone, Close, Recover }
        S s;
        float clock, cooldown, stareFor, flare;
        bool provoked;
        LightBlob eyes;
        const float Range = 6f, StoneFor = 3.2f;

        public static Medusa Spawn(Vector2 at) => Make<Medusa>("priest", "idle", at, WorldLayer.Both, 7, "medusa");

        protected override void Init()
        {
            speed = 1.0f; half = new Vector2(0.3f, 0.16f); touchDamage = 0;
            facing = Facing.Up;                               // her back to the room
            cooldown = 1.0f;
            eyes = LightBlob.Create(transform, pos, 2.6f, new Color(0.62f, 1f, 0.55f), 0f, true);
            eyes.height = 1.3f;
        }

        public bool Stoned => s == S.Stone;
        public bool Staring => s == S.Stare || s == S.Gaze;
        public bool Combing => s == S.Comb;
        /// <summary>0 at rest, 1 with the snakes right up (the model's hair reads this).</summary>
        public float Reared => flare;
        public override bool Sleeps => !Stoned;
        protected override float KnockScale => 0.15f;
        protected override string HurtSound => Stoned ? "statue_break" : "clank";
        protected override Color BurstColor => new Color(0.58f, 0.60f, 0.66f);

        /// <summary>Stone can be cut. So can what she is not looking at. Anything else the hair takes.</summary>
        protected override bool Accepts(HitInfo h)
        {
            if (Stoned || h.kind == HitKind.Reflected) return true;
            var from = ((Vector2)h.from - pos).normalized;
            if (Vector2.Dot(from, Tomb.Dir(facing)) < -0.25f) return true;
            provoked = true;                                  // and she has noticed who tried
            return false;
        }

        protected override void OnHurt(HitInfo h)
        {
            Chips(Stoned ? 7 : 3);
            if (s == S.Comb) { s = S.Turn; clock = 0; }
        }

        void Chips(int n)
        {
            for (int i = 0; i < n; i++)
                Fx.Spawn(pos + new Vector2(Random.Range(-0.25f, 0.25f), Random.Range(0.4f, 1.3f)), Random.insideUnitCircle * 2.6f, 0.5f, Random.Range(2f, 5f),
                    Random.Range(0.3f, 0.6f), new Color(0.70f, 0.72f, 0.78f), new Color(0.30f, 0.32f, 0.38f), 16f, i % 3 == 0 ? 2 : 1);
        }

        protected override void Die()
        {
            Sfx.Play("statue_break", 1f, 0.03f);
            Chips(22);
            if (Story.I) Story.I.MedusaBroken();
            base.Die();
        }

        /// <summary>Nothing solid between her eyes and his.</summary>
        bool Sight(Player p)
        {
            Vector2 a = pos + new Vector2(0, 0.2f), b = p.pos + new Vector2(0, 0.2f);
            int n = Mathf.Max(2, Mathf.CeilToInt(Vector2.Distance(a, b) / 0.35f));
            for (int i = 1; i < n; i++)
            {
                var q = Vector2.Lerp(a, b, i / (float)n);
                if (Solids.Blocks(new Rect(q - new Vector2(0.06f, 0.06f), new Vector2(0.12f, 0.12f)), q, this)) return false;
            }
            return true;
        }

        void Stonify()
        {
            s = S.Stone; clock = 0;
            mat.SetFloat("_Stone", 1f);
            anim.fps = 0;                                     // exactly as she stood
            if (anim.model) anim.model.frozen = true;
            Sfx.Play("piece_down", 0.9f, 0.05f);
            PixelView.I.Shake(1, 0.2f);
            Chips(5);
        }

        /// <summary>The look itself, for as long as it lasts.</summary>
        void Look(Player p, Vector2 d)
        {
            if (d.magnitude > Range || Vector2.Dot(d.normalized, Tomb.Dir(facing)) < 0.5f || !Sight(p)) return;
            if (Dream.I && Dream.I.IsDreamAt(p.pos)) { if (Story.I) Story.I.MedusaEyesShut(); return; }      // asleep: his eyes are shut
            float meets = Vector2.Dot(p.Dir, -d.normalized);
            if (p.Guarding && p.hasShield && meets > 0.45f)
            {
                if (p.TryReflect(d)) { Stonify(); if (Story.I) Story.I.MedusaMeetsHerself(); }
                return;
            }
            if (meets > 0.3f && p.Petrify(2.2f))
            {
                s = S.Close; clock = 0;
                if (Story.I) Story.I.MedusaLooked();
            }
        }

        protected override void Think(float dt, Player p)
        {
            clock += dt;
            var d = p.pos - pos;
            flare = Mathf.MoveTowards(flare, Staring ? 1f : 0f, dt * (Staring ? 2.4f : 4f));
            if (eyes) { eyes.intensity = flare * 0.9f; eyes.transform.position = (Vector3)(pos + Tomb.Dir(facing) * 0.7f); }
            switch (s)
            {
                case S.Comb:
                    anim.Play("comb", facing);
                    if (provoked || CanSee(p, 5.2f)) { s = S.Turn; clock = 0; Sfx.Play("medusa_hiss", 0.7f, 0.08f); if (Story.I) Story.I.MedusaSeen(); }
                    break;
                case S.Turn:
                    // she turns round, and takes her time about it: it is the last time anybody gets
                    anim.Play("idle", facing);
                    if (clock > 0.6f) { facing = FaceOf(d); anim.Play("idle", facing, true); s = S.Stalk; clock = 0; cooldown = 0.6f; touchDamage = 1; }
                    break;
                case S.Stalk:
                    facing = FaceOf(d); anim.SetFacing(facing);
                    if (d.magnitude > 2.4f) { anim.Play("walk", facing); Move(d.normalized * speed, dt); }
                    else anim.Play("idle", facing);
                    cooldown -= dt;
                    if ((cooldown <= 0 || provoked) && d.magnitude < Range && CanSee(p, Range) && Sight(p))
                    {
                        s = S.Stare; clock = 0;
                        stareFor = provoked ? 0.32f : 0.72f; provoked = false;
                        anim.Play("stare", facing, true);
                        Sfx.Play("medusa_stare", 0.85f, 0.04f);
                    }
                    break;
                case S.Stare:
                    // the snakes stand up, and the light comes into her eyes: bronze up, or eyes somewhere else
                    facing = FaceOf(d); anim.SetFacing(facing);
                    if (clock > stareFor)
                    {
                        s = S.Gaze; clock = 0;
                        var fd = Tomb.Dir(facing);
                        for (int i = 0; i < 14; i++)
                            Fx.Spawn(pos + fd * Random.Range(0.6f, Range) + new Vector2(Random.Range(-0.5f, 0.5f), 0.9f + Random.Range(-0.4f, 0.4f)), fd * 3f, 0f, 0f,
                                Random.Range(0.2f, 0.45f), new Color(0.78f, 1f, 0.70f), new Color(0.20f, 0.55f, 0.30f), 0f, 1);
                    }
                    break;
                case S.Gaze:
                    Look(p, d);
                    if (s == S.Gaze && clock > 0.45f) { s = S.Stalk; clock = 0; cooldown = Random.Range(1.7f, 2.5f); }
                    break;
                case S.Stone:
                    vel = Vector2.zero;
                    if (clock > StoneFor)
                    {
                        s = S.Recover; clock = 0;
                        mat.SetFloat("_Stone", 0f);
                        if (anim.model) anim.model.frozen = false;
                        Chips(8);
                        Sfx.Play("pot_break", 0.6f, 0.1f);
                        anim.Play("hurt", facing, true);
                    }
                    break;
                case S.Recover:
                    if (clock > 0.6f) { s = S.Stalk; clock = 0; cooldown = 0.8f; }
                    break;
                case S.Close:
                    // he is stone, and she comes over. The hair does the rest
                    facing = FaceOf(d); anim.SetFacing(facing);
                    if (!p.Stoned) { s = S.Stalk; clock = 0; cooldown = 1.5f; break; }
                    if (d.magnitude > 1.0f) { anim.Play("walk", facing); Move(d.normalized * 3.2f, dt); }
                    else
                    {
                        Sfx.Play("medusa_hiss", 0.9f, 0.04f);
                        p.Hurt(new HitInfo { damage = 2, from = pos, knockback = 6.5f, kind = HitKind.Slash, source = gameObject });
                        s = S.Stalk; clock = 0; cooldown = 2.2f;
                    }
                    break;
            }
        }
    }
}
