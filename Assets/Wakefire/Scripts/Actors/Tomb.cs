// What keeps the king's tomb, besides the king.
//
// The lamp bearers are dead and on duty: a blade goes through them like a hand through lamp
// smoke, and the lamps they carry burn cold. But the dead do not dream. When Azar nods off a
// bearer is simply not there, and his lamp, which is bronze and has no opinion either way, is
// left hanging where he held it. Knock it out of the air; awake again, a bearer with nothing to
// carry looks at his hands, and is off duty for the first time in four hundred years.
//
// The wardens are the king's clay again, with a shield the size of a door that is always between
// you and them. Nothing gets in from the front or the side. The Sun Wheel, coming home, arrives
// from behind.
//
// The Sun Roller is a scarab the size of a cart. It found the gold the robbers dropped, made a
// ball of it, and has been rolling it up and down the hall ever since, on the understanding that
// it is the sun. The ball banks off two walls; at the third it stops, and the beetle on top of
// it does not. A beetle on its back is the moment.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public static class Tomb
    {
        /// <summary>A picture the map carries for the game to use (parked off its edge), with the pivot the map gave it.</summary>
        public static Sprite Sprite(string name)
        {
            int px = 8, py = 8;
            if (Map.Current)
                foreach (var o in Map.Current.data.objects)
                    if (o.s == name || (o.frames != null && System.Array.IndexOf(o.frames, name) >= 0)) { px = o.px; py = o.py; break; }
            return Map.GetSprite(name, px, py);
        }

        public static Vector2 Dir(Facing f) => f == Facing.Down ? Vector2.down : f == Facing.Up ? Vector2.up : f == Facing.Left ? Vector2.left : Vector2.right;
    }

    // ------------------------------------------------------------------------------ lamp bearers
    public class LampBearer : Enemy
    {
        enum S { Beat, Come, Lost }
        S s;
        Vector2 end0, end1;
        bool toEnd1 = true, wasHere = true, told;
        float thin, cold, aside;
        public BearerLamp lamp;

        public static LampBearer Spawn(Vector2 at) => Make<LampBearer>("priest", "idle", at, WorldLayer.Waking, 3, "bearer");

        protected override void Init()
        {
            speed = 1.15f; half = new Vector2(0.3f, 0.15f); touchDamage = 0;
            mat.SetFloat("_Ghost", 0.9f);
            mat.SetVector("_GhostFade", new Vector4(0.285f, 0.46f, 0, 0));
            if (shadow) { Destroy(shadow.gameObject); shadow = null; }
            hover = 1f / 16f;
            // his beat: the longer way the floor runs from where he was posted
            float l = Free(Vector2.left), r = Free(Vector2.right), u = Free(Vector2.up), d = Free(Vector2.down);
            if (l + r >= u + d) { end0 = pos + Vector2.left * l; end1 = pos + Vector2.right * r; }
            else { end0 = pos + Vector2.down * d; end1 = pos + Vector2.up * u; }
            lamp = BearerLamp.Make(this);
        }

        float Free(Vector2 dir)
        {
            float d = 0;
            for (; d < 5f; d += 0.25f)
                if (Solids.Overlaps(new Rect(pos + dir * (d + 0.25f) - half, half * 2), pos, this)) break;
            return d;
        }

        public override bool Sleeps => false;                // the dead do not
        public bool Burdened => lamp && lamp.Lit;
        protected override Color BurstColor => new Color(0.5f, 0.95f, 0.9f);
        protected override string HurtSound => "shade_hit";

        /// <summary>Dead: a blade goes through him.</summary>
        protected override bool Untouchable(HitInfo h)
        {
            if (h.kind == HitKind.Reflected) return false;
            Sfx.Play("ghost_pass", 0.6f, 0.08f);
            for (int i = 0; i < 6; i++)
                Fx.Spawn(pos + new Vector2(Random.Range(-0.3f, 0.3f), 0), Random.insideUnitCircle * 1.0f, Random.Range(0.4f, 1.3f), Random.Range(0.3f, 1.0f),
                    Random.Range(0.3f, 0.6f), new Color(0.75f, 1f, 0.95f), new Color(0.15f, 0.4f, 0.5f), -0.5f);
            if (Story.I) Story.I.BearerPassed();
            return true;
        }

        /// <summary>His lamp has been knocked out of the air while he was not there to hold it.</summary>
        public void LampGone()
        {
            s = S.Lost; stateClock = 0;
            if (Story.I) Story.I.BearerLampOut();
        }

        protected override void Think(float dt, Player p)
        {
            if (lamp) lamp.Follow(dt);
            bool here = Present;
            if (here && !wasHere) stateClock = 0;            // he is back: whatever he was doing, he starts it again
            wasHere = here;
            if (!here) { anim.Play("idle", facing); return; }   // somebody is dreaming, and the dead are not in it
            cold -= dt;
            var d = p.pos - pos;
            switch (s)
            {
                case S.Beat:
                {
                    if (CanSee(p, 4.6f))
                    {
                        // whoever carries the Ghost Key is the king's business: a bearer stops, and looks at the floor
                        if (Story.Has("ghostkey"))
                        {
                            aside = 0.6f;
                            facing = FaceOf(-d); anim.Play("wait", facing); anim.SetFacing(facing);
                            if (Story.I && d.magnitude < 3.2f) Story.I.BearerStepsAside();
                            break;
                        }
                        s = S.Come; stateClock = 0; Sfx.Play("ghost_sigh", 0.45f, 0.1f); break;
                    }
                    if ((aside -= dt) > 0) break;
                    var to = (toEnd1 ? end1 : end0) - pos;
                    if (to.magnitude < 0.2f) { toEnd1 = !toEnd1; break; }
                    facing = FaceOf(to); anim.Play("walk", facing); anim.SetFacing(facing);
                    var before = pos;
                    Move(to.normalized * speed, dt);
                    if ((pos - before).magnitude < speed * dt * 0.3f) toEnd1 = !toEnd1;
                    break;
                }
                case S.Come:
                    // he comes over with the lamp held up, to see who it is
                    if (!CanSee(p, 6.5f)) { s = S.Beat; break; }
                    facing = FaceOf(d); anim.SetFacing(facing);
                    if (d.magnitude > 0.95f) { anim.Play("walk", facing); Move(d.normalized * speed * 1.25f, dt); }
                    else anim.Play("lamp", facing);
                    // the lamp burns cold: stand in its light and it takes the warmth out of you
                    if (d.magnitude < 1.35f && cold <= 0)
                    {
                        cold = 1.0f;
                        p.Hurt(new HitInfo { damage = 1, from = pos, knockback = 5f, kind = HitKind.Fire, source = gameObject });
                    }
                    break;
                case S.Lost:
                    // nothing to carry: he looks at his hands, and is off duty
                    anim.Play("idle", facing);
                    if (stateClock > 1.2f)
                    {
                        if (!told) { told = true; if (Story.I) Story.I.BearerOffDuty(); }
                        thin = Mathf.MoveTowards(thin, 1.05f, dt * 1.3f);
                        mat.SetFloat("_Dissolve", thin);
                        if (thin >= 1f) { health.hp = 0; Rooms.Slain(this); Die(); }
                    }
                    break;
            }
            hover = (1f + Mathf.Round(Mathf.Sin(stateClock * 2.1f + home.x) * 1.2f)) / 16f;
        }

        protected override void Die()
        {
            Sfx.Play("ghost_sigh", 0.8f, 0.05f);
            for (int i = 0; i < 12; i++)
                Fx.Spawn(pos + new Vector2(Random.Range(-0.3f, 0.3f), 0), Random.insideUnitCircle * 1.2f, Random.Range(0.3f, 1.4f), Random.Range(0.4f, 1.4f),
                    Random.Range(0.5f, 0.9f), new Color(0.75f, 1f, 0.95f), new Color(0.15f, 0.4f, 0.5f), -0.6f);
            if (spawnId != null) Story.Set("dead_" + spawnId);
            if (lamp && lamp.Lit) Destroy(lamp.gameObject);
            Destroy(gameObject);
        }
    }

    /// <summary>The lamp a bearer carries. It is real, so it is in both worlds, and in the dream there is
    /// nobody holding it.</summary>
    public class BearerLamp : MonoBehaviour, IHittable, IHitBox
    {
        LampBearer owner;
        SpriteRenderer sr;
        LightBlob glow;
        Sprite[] lit;
        Sprite dead;
        Vector2 at, hand;
        float fall, flick, height = 1.15f, gone;
        public bool Lit { get; private set; } = true;

        public static BearerLamp Make(LampBearer b)
        {
            var go = new GameObject("Bearer's lamp");
            go.transform.SetParent(Map.Current ? Map.Current.transform : null, false);
            var l = go.AddComponent<BearerLamp>();
            l.owner = b;
            l.sr = go.AddComponent<SpriteRenderer>();
            l.sr.sharedMaterial = Map.SpriteMat;
            l.lit = new[] { Tomb.Sprite("hand_lamp_0"), Tomb.Sprite("hand_lamp_1"), Tomb.Sprite("hand_lamp_2") };
            l.dead = Tomb.Sprite("hand_lamp_out");
            l.at = b.pos;
            l.glow = LightBlob.Create(go.transform, b.pos, 3.4f, new Color(0.45f, 0.95f, 0.85f), 0.8f, true);
            l.glow.height = 1.0f;
            l.Follow(0);
            return l;
        }

        public Rect HitBox => new Rect(at.x - 0.55f, at.y - 0.25f, 1.1f, 1.8f);

        public void Follow(float dt)
        {
            if (!owner) return;
            if (Lit)
            {
                at = owner.pos;
                hand = owner.facing == Facing.Left ? new Vector2(-0.42f, 0) : new Vector2(0.42f, 0);
                height = 1.15f + Mathf.Sin(Time.time * 2.1f) * 0.03f;
                flick += dt * 9f;
                sr.sprite = lit[(int)flick % lit.Length];
            }
            Put();
        }

        void Put()
        {
            transform.position = new Vector3(at.x + hand.x, at.y + height, 0);
            sr.sortingOrder = Map.Order(at.y) + 1;
            if (glow) glow.transform.position = new Vector3(at.x + hand.x, at.y, 0);
        }

        void Update()
        {
            if (Lit || Game.Paused) return;
            // knocked out of the air: it comes down, goes out, and lies there until the floor forgets it
            float dt = Time.deltaTime;
            fall = Mathf.MoveTowards(fall, 1, dt * 3.4f);
            height = Mathf.Lerp(1.15f, 0.1f, fall * fall);
            sr.sprite = dead;
            if (glow) glow.intensity = Mathf.MoveTowards(glow.intensity, 0, dt * 3f);
            Put();
            gone += dt;
            if (gone > 7f || !owner && gone > 2.5f) Destroy(gameObject);
        }

        public bool Hit(HitInfo h)
        {
            if (!Lit || !owner) return false;
            if (!(Dream.I && Dream.I.IsDreamAt(at))) return false;             // awake, he has hold of it
            Lit = false; fall = 0;
            Sfx.Play("crown_hit", 0.9f, 0.04f);
            Sfx.Play("pot_break", 0.5f, 0.05f);
            Fx.Sparks(transform.position, new Color(0.6f, 1f, 0.9f), 10);
            PixelView.I.Shake(1, 0.12f);
            owner.LampGone();
            return true;
        }
    }

    // ---------------------------------------------------------------------------------- wardens
    public class Warden : Enemy
    {
        enum S { Stand, Stir, Hold, Brace, Bash, Rest }
        S s;
        Vector2 bashDir;
        bool struck;

        public static Warden Spawn(Vector2 at) => Make<Warden>("sentinel", "idle", at, WorldLayer.Both, 4, "warden");

        public WardenDoor door;
        protected override void Init() { speed = 1.2f; half = new Vector2(0.36f, 0.17f); touchDamage = 0; door = WardenDoor.Make(this); }
        public bool Bashing => s == S.Bash;
        public bool Bracing => s == S.Brace;
        public float Lift => hover;
        protected override float KnockScale => 0.2f;
        protected override string HurtSound => "clay_hit";
        protected override Color BurstColor => new Color(0.72f, 0.44f, 0.30f);
        public override Rect HitBox => new Rect(pos.x - 0.5f, pos.y - 0.2f, 1.0f, 1.9f);
        public bool Resting => s == S.Rest;
        public bool Standing => s == S.Stand;

        /// <summary>A shield the size of a door, and it is always between you and him: only what comes from
        /// behind gets in.</summary>
        protected override bool Accepts(HitInfo h)
        {
            if (s == S.Stand || h.kind == HitKind.Reflected) return true;
            var from = ((Vector2)h.from - pos).normalized;
            return Vector2.Dot(from, Tomb.Dir(facing)) < -0.25f;
        }

        protected override void OnHurt(HitInfo h) { if (s == S.Stand) Stir(); }

        void Stir()
        {
            s = S.Stir; stateClock = 0;
            Sfx.Play("clay_wake", 0.8f);
            Fx.Dust(pos, 8);
        }

        public override void Blocked(Player p)
        {
            base.Blocked(p);
            if (s == S.Bash) { s = S.Rest; stateClock = 0; PixelView.I.Shake(1, 0.15f); }
        }

        protected override void Die()
        {
            Sfx.Play("pot_break");
            for (int i = 0; i < 18; i++)
                Fx.Spawn(pos + new Vector2(0, 0.6f) + Random.insideUnitCircle * 0.3f, Random.insideUnitCircle * 3.6f, 0.5f, Random.Range(3f, 6f), Random.Range(0.4f, 0.8f),
                    i % 4 == 0 ? new Color(0.93f, 0.72f, 0.26f) : new Color(0.74f, 0.46f, 0.32f), new Color(0.36f, 0.20f, 0.16f), 18f, i % 3 == 0 ? 2 : 1);
            base.Die();
        }

        protected override void Think(float dt, Player p)
        {
            var d = p.pos - pos;
            switch (s)
            {
                case S.Stand:
                    anim.Play("idle", facing);
                    if (CanSee(p, 5f)) Stir();
                    break;
                case S.Stir:
                    facing = FaceOf(d); anim.Play("guard", facing); anim.SetFacing(facing);
                    if (stateClock > 0.7f) { s = S.Hold; stateClock = 0; touchDamage = 1; }
                    break;
                case S.Hold:
                    // the shield follows him round the room; the feet follow the shield
                    facing = FaceOf(d); anim.SetFacing(facing);
                    if (d.magnitude > 1.5f) { anim.Play("walk", facing); Move(d.normalized * speed, dt); }
                    else anim.Play("guard", facing);
                    if (d.magnitude < 1.9f && stateClock > 1.1f && CanSee(p, 4f))
                    {
                        s = S.Brace; stateClock = 0;
                        Sfx.Play("sentinel_alert", 0.6f, 0.02f);
                        anim.Play("guard", facing, true);
                    }
                    break;
                case S.Brace:
                    if (stateClock > 0.5f)
                    {
                        s = S.Bash; stateClock = 0; struck = false;
                        bashDir = Tomb.Dir(facing);
                        anim.Play(anim.model ? "run" : "walk", facing, true);
                    }
                    break;
                case S.Bash:
                    Move(bashDir * 6.8f, dt);
                    if (!struck && Present && Vector2.Distance(pos + bashDir * 0.5f, p.pos) < 0.85f && Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos))
                    {
                        struck = true;
                        p.Hurt(new HitInfo { damage = 2, from = pos, knockback = 8f, kind = HitKind.Heavy, source = gameObject });
                    }
                    if (stateClock > 0.22f) { s = S.Rest; stateClock = 0; anim.Play("guard", facing, true); }
                    break;
                case S.Rest:
                    // the shield is heavy: after a shove he stands where he ended, facing the way he shoved
                    if (stateClock > 1.0f) { s = S.Hold; stateClock = 0; }
                    break;
            }
        }
    }

    /// <summary>What a warden carries for a shield: the inner door he was made to stand in. It goes in front of
    /// him whichever way he turns, leans back before a shove and goes out with it; and when he breaks, it is
    /// only a door again, and lies down.</summary>
    public class WardenDoor : MonoBehaviour
    {
        Warden owner;
        SpriteRenderer sr;
        Sprite front, back, side, flat;
        float down = -1, out_;
        Vector2 last;

        public static WardenDoor Make(Warden w)
        {
            var go = new GameObject("Warden's door");
            go.transform.SetParent(Map.Current ? Map.Current.transform : null, false);
            var d = go.AddComponent<WardenDoor>();
            d.owner = w;
            d.sr = go.AddComponent<SpriteRenderer>();
            d.sr.sharedMaterial = Map.SpriteMat;
            d.front = Tomb.Sprite("warden_door_f"); d.back = Tomb.Sprite("warden_door_b"); d.side = Tomb.Sprite("warden_door_s"); d.flat = Tomb.Sprite("warden_door_flat");
            Map.Normals(d.sr, "warden_door_f_lin");
            d.last = w.pos;
            d.LateUpdate();
            return d;
        }

        void LateUpdate()
        {
            if (down >= 0)
            {
                down += Time.deltaTime;
                if (down > 5f) Destroy(gameObject);
                return;
            }
            if (!owner || owner.health.Dead)
            {
                // nobody is holding it up
                down = 0;
                sr.sprite = flat; sr.flipX = false;
                Map.Normals(sr, "warden_door_flat_lin");
                transform.position = new Vector3(last.x, last.y, 0);
                sr.sortingOrder = Map.Order(last.y + 0.9f);
                Sfx.Play("bars_down", 0.8f, 0.08f);
                PixelView.I.Shake(1, 0.2f);
                Fx.Dust(last, 8);
                return;
            }
            var f = owner.facing;
            var d = Tomb.Dir(f);
            out_ = Mathf.MoveTowards(out_, owner.Bashing ? 0.3f : owner.Bracing ? -0.1f : 0f, Time.deltaTime * 4f);
            Vector2 at = owner.pos + d * (0.44f + out_);
            last = owner.pos;
            sr.sprite = f == Facing.Down ? front : f == Facing.Up ? back : side;
            sr.flipX = f == Facing.Left;
            transform.position = new Vector3(Mathf.Round(at.x * 16f) / 16f, Mathf.Round((at.y + owner.Lift) * 16f) / 16f, 0);
            sr.sortingOrder = Map.Order(at.y) + (f == Facing.Up ? -1 : 1);
        }
    }

    // ------------------------------------------------------------------------------ the king's vultures
    /// <summary>The king kept vultures the way other kings keep hawks. They sit on bronze perches a spear's
    /// length up, out of any blade's reach, and mark whoever walks under them; then they come down in one long
    /// stoop, through him and on, and go back up to think about it. The Sun Wheel takes one off its perch.
    /// A blade can only meet one on the way through; a stoop that meets the mirror shield ends on the floor.</summary>
    public class Vulture : Enemy
    {
        enum S { Perch, Mark, Stoop, Climb, Down }
        S s;
        Vector2 perch, from, to;
        float wait, len, clock;             // (its own clock: a scene on the screen does not hurry it)
        bool struck, angry;
        const float High = 1.75f, LowFlight = 0.42f;

        public static Vulture Spawn(Vector2 at) => Make<Vulture>("moth", "idle", at, WorldLayer.Both, 2, "vulture");

        protected override void Init()
        {
            flying = true; speed = 8.4f; half = new Vector2(0.3f, 0.2f); touchDamage = 0;
            perch = pos; hover = High; wait = 1.0f + Mathf.Abs(pos.x * 0.37f + pos.y * 0.21f) % 1.6f;
        }

        public bool Perched => s == S.Perch || s == S.Mark;
        public bool Stooping => s == S.Stoop;
        public bool Grounded => s == S.Down;
        /// <summary>Low enough for a blade.</summary>
        public bool Low => hover < 0.95f;
        /// <summary>Where it is on the screen; and, while it sits, the whole of its perch under it (what hits the post shakes the bird).</summary>
        public override Rect HitBox => Perched ? new Rect(pos.x - 0.6f, pos.y - 0.1f, 1.2f, hover + 1.0f) : new Rect(pos.x - 0.7f, pos.y + hover - 0.3f, 1.4f, 1.25f);
        protected override float KnockScale => s == S.Down ? 0.5f : 0f;
        protected override string HurtSound => "vulture_hit";
        protected override Color BurstColor => new Color(0.20f, 0.16f, 0.14f);

        /// <summary>Up there a blade is only waved at it. Something thrown is another matter.</summary>
        protected override bool Untouchable(HitInfo h) => !Low && h.kind != HitKind.Thrown && h.kind != HitKind.Reflected;

        protected override void OnHurt(HitInfo h)
        {
            Feathers(8);
            if (Perched) { angry = true; wait = 0.2f; s = S.Perch; }
        }

        /// <summary>It came down on bronze: it sits on the floor a while, working out what happened.</summary>
        public override void Blocked(Player p)
        {
            base.Blocked(p);
            if (s != S.Stoop) return;
            s = S.Down; clock = 0; hover = 0;
            Feathers(6);
            PixelView.I.Shake(1, 0.15f);
        }

        void Feathers(int n)
        {
            for (int i = 0; i < n; i++)
                Fx.Spawn(pos + new Vector2(Random.Range(-0.3f, 0.3f), hover + Random.Range(0.1f, 0.6f)), Random.insideUnitCircle * 1.6f + new Vector2(0, 0.6f), 0.3f, Random.Range(0.4f, 1.2f),
                    Random.Range(0.5f, 1.0f), i % 3 == 0 ? new Color(0.78f, 0.74f, 0.66f) : new Color(0.24f, 0.19f, 0.16f), new Color(0.10f, 0.08f, 0.07f), 2.2f, 1);
        }

        protected override void Die()
        {
            Sfx.Play("enemy_die");
            Feathers(22);
            Pickup.Chance(pos, 0.5f, 0.2f);
            if (spawnId != null) Story.Set("dead_" + spawnId);
            Destroy(gameObject);
        }

        protected override void Think(float dt, Player p)
        {
            clock += dt;
            switch (s)
            {
                case S.Perch:
                    pos = perch; hover = High; vel = Vector2.zero;
                    facing = FaceOf(p.pos - pos); anim.Play("idle", facing); anim.SetFacing(facing);
                    wait -= dt;
                    if (wait <= 0 && CanSee(p, angry ? 13f : 7.5f))
                    {
                        s = S.Mark; clock = 0;
                        Sfx.Play("vulture_mark", 0.8f, 0.08f);
                    }
                    break;
                case S.Mark:
                    // wings out, neck down: it has picked somebody
                    facing = FaceOf(p.pos - pos); anim.Play("mark", facing); anim.SetFacing(facing);
                    if (clock > (angry ? 0.45f : 0.8f))
                    {
                        s = S.Stoop; clock = 0; struck = false;
                        from = pos;
                        var d = p.pos - pos;
                        if (d.sqrMagnitude < 0.01f) d = Vector2.down;
                        to = p.pos + d.normalized * 2.4f;                 // through him, and on
                        len = Vector2.Distance(from, to);
                        Sfx.Play("vulture_stoop", 0.85f, 0.06f);
                    }
                    break;
                case S.Stoop:
                {
                    float k = Mathf.Clamp01(clock * speed / Mathf.Max(0.1f, len));
                    pos = Vector2.Lerp(from, to, k);
                    // down to the height of a man's shoulder by the time it reaches him, and no lower
                    float reach = Mathf.Clamp01(k * len / Mathf.Max(0.1f, len - 2.4f));
                    hover = Mathf.Lerp(High, LowFlight, Mathf.SmoothStep(0, 1, reach));
                    facing = FaceOf(to - from); anim.Play("stoop", facing); anim.SetFacing(facing);
                    vel = (to - from).normalized * speed;
                    if (!struck && Low && p.state != Player.State.Dead && Vector2.Distance(pos, p.pos) < 0.8f && Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos))
                    {
                        struck = true;
                        p.Hurt(new HitInfo { damage = 1, from = pos - vel.normalized * 0.5f, knockback = 5f, kind = HitKind.Slash, source = gameObject });
                    }
                    if (k >= 1f && s == S.Stoop) { s = S.Climb; clock = 0; }
                    break;
                }
                case S.Climb:
                {
                    var d = perch - pos;
                    float step = 5.2f * dt;
                    hover = Mathf.MoveTowards(hover, High, dt * 1.7f);
                    if (d.magnitude <= step)
                    {
                        pos = perch;
                        if (hover >= High - 0.01f) { s = S.Perch; clock = 0; wait = Random.Range(1.5f, 2.7f); angry = false; }
                        anim.Play("fly", facing);
                        break;
                    }
                    pos += d.normalized * step;
                    facing = FaceOf(d); anim.Play("fly", facing); anim.SetFacing(facing);
                    vel = d.normalized * 5.2f;
                    break;
                }
                case S.Down:
                    hover = 0; vel = Vector2.zero;
                    anim.Play("down", facing);
                    if (clock > 2.2f) { s = S.Climb; clock = 0; }
                    break;
            }
        }
    }

    // ------------------------------------------------------------------------------ the Sun Roller
    public class SunRoller : Enemy
    {
        enum S { Wait, Fetch, Mount, Rev, Roll, Tumble, Right }
        S s;
        public static SunRoller Current;
        GoldBall ball;
        Vector2 dir, from, to;
        int banks;
        bool spent;
        float speedNow, clock;              // (its own clock: it only runs while the beetle is free to think)
        const float Ride = 1.18f;                // how high it stands when it is up on its ball

        public bool Waiting => s == S.Wait;
        public bool Tumbled => s == S.Tumble || s == S.Right;
        public bool Rolling => s == S.Roll || s == S.Rev;
        public Vector2 BallPos => ball ? ball.pos : pos;
        public Vector2 BallVel => s == S.Roll ? dir * speedNow : Vector2.zero;
        public Vector2 BallDir => dir;
        public int Banks => banks;
        bool Hurt => health.hp <= health.max / 2;

        public static SunRoller Spawn(Vector2 at) => Make<SunRoller>("crab", "idle", at, WorldLayer.Both, 26, "sun_roller");

        protected override void Init()
        {
            speed = 3.4f; half = new Vector2(0.8f, 0.3f); touchDamage = 0;
            s = S.Wait;
            Current = this;
            roams = true;
            ball = GoldBall.Make(pos);
            hover = Ride;
        }

        void OnDisable() { if (Current == this) Current = null; }

        public override Rect HitBox => new Rect(pos.x - 1.0f, pos.y - 0.4f, 2.0f, 1.9f + hover);
        protected override float KnockScale => 0f;
        protected override string HurtSound => "boss_hit";
        protected override Color BurstColor => new Color(0.16f, 0.24f, 0.56f);
        public override bool Sleeps => false;

        /// <summary>A shell that turns a blade, all the way round. Its belly does not, and it only shows its belly one way.</summary>
        protected override bool Accepts(HitInfo h) => Tumbled || h.kind == HitKind.Reflected;

        /// <summary>Somebody has come into the hall: the sun has business with him.</summary>
        public void Begin()
        {
            if (s != S.Wait) return;
            s = S.Mount; clock = 0; touchDamage = 1;
            if (Player.I && ball) dir = Thrown.Aim(Player.I.pos - ball.pos, Vector2.down);
        }

        Rect Arena
        {
            get
            {
                var r = Rooms.Of(home);
                return r != null ? r.rect : new Rect(home - Vector2.one * 8f, Vector2.one * 16f);
            }
        }

        bool BallWall(Vector2 at)
        {
            // (a drop turns it like a wall does: the sun does not go down holes)
            if (Solids.Overlaps(new Rect(at - new Vector2(0.55f, 0.4f), new Vector2(1.1f, 0.8f)), at, this)) return true;
            var a = Arena;
            return at.x < a.xMin + 0.5f || at.x > a.xMax - 0.5f || at.y < a.yMin + 0.5f || at.y > a.yMax - 0.5f;
        }

        Vector2 Inside(Vector2 at, float margin)
        {
            var a = Arena;
            return new Vector2(Mathf.Clamp(at.x, a.xMin + margin, a.xMax - margin), Mathf.Clamp(at.y, a.yMin + margin, a.yMax - margin));
        }

        protected override void Think(float dt, Player p)
        {
            if (!ball) return;
            clock += dt;
            switch (s)
            {
                case S.Wait:
                    // on top of the sun, where it has been for four hundred years
                    pos = ball.pos; hover = Ride;
                    anim.Play("idle", facing);
                    break;
                case S.Fetch:
                {
                    // back to its ball, the short way
                    var to2 = ball.pos - pos;
                    if (to2.magnitude < 0.35f || clock > 5f) { s = S.Mount; clock = 0; dir = Thrown.Aim(p.pos - ball.pos, Vector2.down); break; }
                    facing = FaceOf(to2); anim.Play("walk", facing); anim.SetFacing(facing);
                    pos += to2.normalized * Mathf.Min(speed * (Hurt ? 1.35f : 1f) * dt, to2.magnitude);
                    vel = to2.normalized * speed;
                    break;
                }
                case S.Mount:
                    // up onto it, and round to face the way it is going to go
                    pos = Vector2.MoveTowards(pos, ball.pos, dt * 6f);
                    hover = Mathf.MoveTowards(hover, Ride, dt * 3.6f);
                    facing = FaceOf(dir); anim.Play("walk", facing); anim.SetFacing(facing);
                    if (clock > 0.45f && hover >= Ride - 0.01f)
                    {
                        s = S.Rev; clock = 0;
                        dir = Thrown.Aim(p.pos - ball.pos, Vector2.down);
                        Sfx.Play("scarab", 1f, 0.02f);
                        Sfx.Play("roll", 0.8f, 0f);
                    }
                    break;
                case S.Rev:
                    // six legs going, and the sun turning under them on the spot: the sparks say which way it will go
                    pos = ball.pos; hover = Ride;
                    facing = FaceOf(dir); anim.Play("walk", facing); anim.SetFacing(facing);
                    vel = dir * 6f;
                    ball.Spin(14f, dt); ball.Heat(1f);
                    if (Random.value < 0.6f)
                        Fx.Spawn(ball.pos + dir * 0.7f + new Vector2(0, 0.3f), dir * Random.Range(5f, 9f) + Random.insideUnitCircle * 0.6f, 0.2f, Random.Range(0.5f, 1.5f),
                            Random.Range(0.2f, 0.4f), new Color(1f, 0.9f, 0.5f), new Color(0.8f, 0.4f, 0.1f), 6f, 1);
                    if (clock > (Hurt ? 0.5f : 0.75f))
                    {
                        s = S.Roll; clock = 0; banks = 0; spent = false;
                        speedNow = Hurt ? 11.5f : 9.6f;
                        Sfx.Play("piece_slide", 1f, 0f);
                    }
                    break;
                case S.Roll:
                {
                    Vector2 step = dir * speedNow * dt;
                    bool hx = false, hy = false;
                    var b = ball.pos;
                    if (step.x != 0) { var nx = b + new Vector2(step.x, 0); if (BallWall(nx)) hx = true; else b = nx; }
                    if (step.y != 0) { var ny = b + new Vector2(0, step.y); if (BallWall(ny)) hy = true; else b = ny; }
                    ball.pos = b;
                    ball.Spin(speedNow, dt); ball.Heat(0.6f);
                    if (hx || hy)
                    {
                        if (hx) dir.x = -dir.x;
                        if (hy) dir.y = -dir.y;
                        banks++;
                        Sfx.Play("bull_crash", 0.7f, 0.05f);
                        PixelView.I.Shake(2, 0.18f);
                        Fx.Dust(b, 6);
                        Fx.Sparks(b + new Vector2(0, 0.6f), new Color(1f, 0.88f, 0.5f), 6);
                        if (banks > Thrown.MaxBanks) spent = true;          // the third wall: the sun has crossed the sky, and stops
                    }
                    if (spent) speedNow = Mathf.MoveTowards(speedNow, 0, dt * 24f);
                    pos = ball.pos; hover = Ride;
                    facing = FaceOf(dir); anim.Play("walk", facing); anim.SetFacing(facing);
                    vel = dir * speedNow;
                    // what the sun meets
                    if (speedNow > 2f && p.state != Player.State.Dead && Vector2.Distance(ball.pos, p.pos + new Vector2(0, 0.1f)) < 1.0f)
                        p.Hurt(new HitInfo { damage = 2, from = ball.pos - dir, knockback = 9f, kind = HitKind.Crush, source = gameObject });
                    if ((spent && speedNow <= 0.01f) || clock > 9f) Topple();
                    break;
                }
                case S.Tumble:
                    // thrown off the front of its sun, onto its back
                    if (clock < 0.32f) { float k = clock / 0.32f; pos = Vector2.Lerp(from, to, k); hover = Mathf.Lerp(Ride, 0, k) + Mathf.Sin(k * Mathf.PI) * 0.7f; }
                    else { pos = to; hover = 0; }
                    anim.Play("back", facing);
                    vel = Vector2.zero;
                    if (clock > (Hurt ? 2.1f : 2.5f)) { s = S.Right; clock = 0; Sfx.Play("scarab", 0.8f, 0.05f); }
                    break;
                case S.Right:
                    anim.Play("idle", facing);
                    if (clock > 0.6f) { s = S.Fetch; clock = 0; touchDamage = 1; }
                    break;
            }
        }

        void Topple()
        {
            s = S.Tumble; clock = 0; touchDamage = 0;
            // the ball settles clear of the wall; the beetle lands beyond it
            ball.pos = Inside(ball.pos, 2.1f);
            from = pos;
            to = Inside(ball.pos + (dir.sqrMagnitude > 0.01f ? dir.normalized : Vector2.down) * 2.0f, 1.3f);
            if (Vector2.Distance(to, ball.pos) < 1.4f) to = Inside(ball.pos + new Vector2(0, -2.0f), 1.3f);
            anim.Play("back", facing, true);
            Sfx.Play("bull_daze", 0.9f, 0.03f);
            PixelView.I.Shake(2, 0.25f);
            if (Story.I) Story.I.RollerTumbled();
        }

        protected override void Die()
        {
            Sfx.Play("boss_die", 1f, 0f);
            PixelView.I.Shake(3, 0.5f);
            for (int i = 0; i < 26; i++)
                Fx.Spawn(pos + new Vector2(0, 0.6f) + Random.insideUnitCircle * 0.7f, Random.insideUnitCircle * 4.2f, 0.5f, Random.Range(2f, 6f), Random.Range(0.4f, 0.9f),
                    i % 3 == 0 ? new Color(0.93f, 0.74f, 0.28f) : BurstColor, new Color(0.05f, 0.05f, 0.12f), 12f, i % 3 == 0 ? 2 : 1);
            // the sun comes apart: everything the robbers dropped was in there
            if (ball)
            {
                for (int i = 0; i < 14; i++) Pickup.Drop(i % 5 == 0 ? Pickup.Kind.Gold : Pickup.Kind.Shekel, ball.pos + Random.insideUnitCircle * 1.1f);
                ball.Break();
            }
            if (spawnId != null) Story.Set("dead_" + spawnId);
            if (Story.I) Story.I.RollerDown();
            Destroy(gameObject);
        }
    }

    /// <summary>The Sun Roller's sun: cups, rings and a king's ransom in small change, rolled into a ball.</summary>
    public class GoldBall : MonoBehaviour
    {
        public Vector2 pos;
        SpriteRenderer sr, shadow;
        Sprite[] frames;
        LightBlob glow;
        float turn, heat;

        public static GoldBall Make(Vector2 at)
        {
            var go = new GameObject("The sun");
            go.transform.SetParent(Map.Current ? Map.Current.transform : null, false);
            var b = go.AddComponent<GoldBall>();
            b.pos = at;
            var body = new GameObject("Sprite");
            body.transform.SetParent(go.transform, false);
            b.sr = body.AddComponent<SpriteRenderer>();
            b.sr.sharedMaterial = Map.SpriteMat;
            b.frames = new[] { Tomb.Sprite("gold_ball_0"), Tomb.Sprite("gold_ball_1"), Tomb.Sprite("gold_ball_2"), Tomb.Sprite("gold_ball_3") };
            b.sr.sprite = b.frames[0];
            b.shadow = Npc.MakeShadow(go.transform, WorldLayer.Both, 16);
            b.glow = LightBlob.Create(go.transform, at, 3.2f, new Color(1f, 0.8f, 0.4f), 0.5f, false);
            b.glow.height = 0.7f;
            b.LateUpdate();
            return b;
        }

        public void Spin(float speed, float dt) { turn += speed * dt * 0.8f; }
        public void Heat(float h) { heat = Mathf.Max(heat, h); }

        void LateUpdate()
        {
            transform.position = new Vector3(pos.x, pos.y, 0);
            sr.sprite = frames[((int)turn % frames.Length + frames.Length) % frames.Length];
            sr.sortingOrder = Map.Order(pos.y) - 1;
            if (shadow) shadow.sortingOrder = Map.Order(pos.y) - 2;
            if (glow) glow.intensity = 0.5f + heat * 0.45f;
            heat = Mathf.MoveTowards(heat, 0, Time.deltaTime * 1.5f);
        }

        public void Break()
        {
            Fx.Sparks(pos + new Vector2(0, 0.7f), new Color(1f, 0.85f, 0.4f), 18);
            Sfx.Play("coin_big", 1f, 0f);
            Destroy(gameObject);
        }
    }
}
