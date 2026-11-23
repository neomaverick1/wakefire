// The Bronze Herdsman: the keeper of the temple's bulls, cast in the same bronze as his herd and
// left on duty. He walks his man down, plants his feet, and brings the goad round in a sweep that
// clears the floor in front of him. A blade turns on him from the front; the sweep leaves him
// leaning on the goad for a moment with his back open, and that is the moment. When he raises the
// goad instead, the two bulls' heads in the wall breathe on whoever he is pointing at. Past half
// his life he sweeps twice before he rests.
using UnityEngine;

namespace Wakefire
{
    public class Herdsman : Enemy
    {
        enum S { Walk, Raise, Sweep, Lean, Call }
        S s;
        Vector2 aim;
        float callClock;
        bool struck, second, spat;
        int calls;
        int sweeps;

        // (the sentinels' old sheet stands in where models are off; his own model is asked for by name)
        public static Herdsman Spawn(Vector2 at) => Make<Herdsman>("sentinel", "idle", at, WorldLayer.Both, 16, "herdsman");

        protected override void Init()
        {
            speed = 1.75f; half = new Vector2(0.42f, 0.18f); touchDamage = 1;
            callClock = 2.5f;
        }

        public override Rect HitBox => new Rect(pos.x - 0.6f, pos.y - 0.2f, 1.2f, 2.2f);
        protected override float KnockScale => s == S.Lean ? 0.3f : 0.08f;
        protected override string HurtSound => "clank";
        protected override Color BurstColor => new Color(0.85f, 0.55f, 0.25f);
        bool Hurt => health.hp <= health.max / 2;
        public bool Open => s == S.Lean;
        public bool Winding => s == S.Raise;
        public bool Sweeping => s == S.Sweep;
        public bool Calling => s == S.Call;

        static Vector2 Dir(Facing f) => f == Facing.Down ? Vector2.down : f == Facing.Up ? Vector2.up : f == Facing.Left ? Vector2.left : Vector2.right;

        /// <summary>Bronze all the way round, until he is leaning on the goad: then it is only bronze in front.</summary>
        protected override bool Accepts(HitInfo h)
        {
            if (h.kind == HitKind.Reflected || h.kind == HitKind.Fire) return true;
            var from = ((Vector2)h.from - pos).normalized;
            float facingHim = Vector2.Dot(from, Dir(facing));
            if (s == S.Lean) return true;
            return facingHim < -0.3f;                     // from behind, any time, if you can get there
        }

        protected override void Think(float dt, Player p)
        {
            var d = p.pos - pos;
            callClock -= dt;
            switch (s)
            {
                case S.Walk:
                {
                    facing = FaceOf(d);
                    anim.SetFacing(facing);
                    if (d.magnitude > 1.9f)
                    {
                        anim.Play("walk", facing);
                        Move(d.normalized * speed * (Hurt ? 1.25f : 1f), dt);
                    }
                    else anim.Play("idle", facing);
                    if (callClock <= 0 && d.magnitude > 3.2f) { s = S.Call; stateClock = 0; spat = false; anim.Play("call", facing, true); Sfx.Play("sentinel_alert", 1f, 0); break; }
                    if (d.magnitude < 2.35f && stateClock > 0.35f) Wind(d, false);
                    break;
                }
                case S.Raise:
                    // he has chosen where the goad is going, and tells you with his whole body
                    if (stateClock > (second ? 0.4f : Hurt ? 0.54f : 0.68f))
                    {
                        s = S.Sweep; stateClock = 0; struck = false;
                        anim.Play("sweep", facing, true);
                        Sfx.Play("swing3", 1f, 0.03f);
                    }
                    break;
                case S.Sweep:
                    if (!struck && stateClock > 0.13f)
                    {
                        struck = true;
                        // everything in front of him and out to the goad's length
                        var to = p.pos - pos;
                        if (to.magnitude < 2.6f && Vector2.Dot(to.normalized, aim) > 0.0f && Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos))
                            p.Hurt(new HitInfo { damage = 2, from = pos, knockback = 9f, kind = HitKind.Slash, source = gameObject });
                        PixelView.I.Shake(2, 0.16f);
                        for (int i = -4; i <= 4; i++)
                        {
                            float a = Mathf.Atan2(aim.y, aim.x) + i * 0.24f;
                            var at = pos + new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.8f) * 2.3f;
                            Fx.Dust(at, 1);
                            if (i % 2 == 0) Fx.Sparks(at + new Vector2(0, 0.3f), new Color(1f, 0.82f, 0.45f), 2);
                        }
                    }
                    if (stateClock > 0.5f)
                    {
                        sweeps++;
                        if (Hurt && !second) { Wind(d, true); break; }
                        s = S.Lean; stateClock = 0; second = false;
                        anim.Play("lean", facing, true);
                        Sfx.Play("clank", 0.5f, 0);
                    }
                    break;
                case S.Lean:
                    if (stateClock > (Hurt ? 1.15f : 1.4f)) { s = S.Walk; stateClock = 0; }
                    break;
                case S.Call:
                    facing = FaceOf(d);
                    anim.SetFacing(facing);
                    if (!spat && stateClock > 0.75f)
                    {
                        spat = true;
                        // one of his herd answers him, turn and turn about; hurt, he calls both
                        int n = 0, k = 0;
                        var room = Rooms.Of(pos);
                        foreach (var head in FindObjectsByType<BullHead>(FindObjectsSortMode.None))
                        {
                            if (!head || !head.dormant || !head.prop) continue;
                            if (room != null && Rooms.Of(head.prop.basePos + new Vector2(0, -1f)) != room) continue;
                            if (Hurt || (k++ + calls) % 2 == 0) head.SpitAt(p, 0.45f * n++);
                        }
                        calls++;
                    }
                    if (stateClock > 1.7f) { s = S.Walk; stateClock = 0; callClock = Hurt ? 5.5f : 8f; }
                    break;
            }
        }

        void Wind(Vector2 d, bool again)
        {
            s = S.Raise; stateClock = 0; second = again;
            facing = FaceOf(d);
            aim = Dir(facing);
            anim.Play("raise", facing, true);
            if (!again) Sfx.Play("sentinel_alert", 0.7f, 0);
        }

        protected override void OnHurt(HitInfo h)
        {
            // hit while he rests, he is slower getting up
            if (s == S.Lean) stateClock = Mathf.Max(0, stateClock - 0.12f);
        }

        protected override void Die()
        {
            PixelView.I.Shake(3, 0.6f);
            Sfx.Play("statue_break", 1f, 0);
            for (int i = 0; i < 10; i++) Pickup.Drop(i % 3 == 0 ? Pickup.Kind.Gold : Pickup.Kind.Shekel, pos + Random.insideUnitCircle * 1.0f);
            Pickup.Drop(Pickup.Kind.Flame, pos + new Vector2(0, 0.4f));
            Pickup.Drop(Pickup.Kind.Flame, pos + new Vector2(0.5f, 0));
            if (Story.I) Story.I.HerdsmanDown();
            base.Die();
        }
    }
}
