// The Den Mother: the jackal that has had the crypt under the old shrine to herself for longer
// than the watch has been forgetting to look. She is the size of a calf, she circles wider and
// leaps further than the ones on the terraces. She gathers herself before she leaps and has
// picked her line a moment before she goes, so a step to the side is enough; a leap that misses
// leaves her getting her breath, and one that ends in a pillar leaves her on her side, which is
// the moment. Her bite is worse than her shoulder. Hurt badly enough she calls the pack.
using UnityEngine;

namespace Wakefire
{
    public class DenMother : Enemy
    {
        enum S { Prowl, Crouch, Lunge, Daze, Howl, Recover }
        S s;
        Vector2 lungeDir;
        float orbit, lungeFor;
        bool howled;
        int side = 1;

        public bool Dazed => s == S.Daze;
        public bool Winding => s == S.Crouch;
        public bool Leaping => s == S.Lunge;
        public bool Winded => s == S.Daze || s == S.Recover;

        public static DenMother Spawn(Vector2 at) => Make<DenMother>("jackal", "idle", at, WorldLayer.Waking, 12, "den_mother");

        protected override void Init()
        {
            speed = 3.3f; half = new Vector2(0.62f, 0.2f); touchDamage = 2;
            orbit = Random.value * 6f;
        }

        public override Rect HitBox => new Rect(pos.x - 0.85f, pos.y - 0.2f, 1.7f, 1.5f);
        protected override float KnockScale => s == S.Daze ? 0.5f : 0.22f;
        protected override string HurtSound => "jackal_bark";
        protected override Color BurstColor => new Color(0.42f, 0.34f, 0.26f);
        bool Hurt => health.hp <= health.max / 2;

        protected override void Think(float dt, Player p)
        {
            var d = p.pos - pos;
            // winded or calling, she is nothing to walk into; in the air she is all teeth
            touchDamage = s == S.Lunge ? 2 : s == S.Daze || s == S.Recover || s == S.Howl ? 0 : 1;
            switch (s)
            {
                case S.Prowl:
                {
                    orbit += dt * 0.8f * side;
                    var want = p.pos + new Vector2(Mathf.Cos(orbit), Mathf.Sin(orbit) * 0.7f) * 3.9f;
                    var w = want - pos;
                    facing = FaceOf(d);
                    anim.Play("run", FaceOf(w));
                    anim.SetFacing(FaceOf(w));
                    Move(w.normalized * Mathf.Min(speed * (Hurt ? 1.25f : 1f), w.magnitude * 3f), dt);
                    if (Hurt && !howled) { s = S.Howl; stateClock = 0; howled = true; anim.Play("crouch", facing, true); Sfx.Play("jackal_growl", 1f, 0); break; }
                    if (stateClock > (Hurt ? 0.85f : 1.35f) && d.magnitude < 6.5f)
                    {
                        s = S.Crouch; stateClock = 0; facing = FaceOf(d);
                        anim.Play("crouch", facing, true);
                        Sfx.Play("jackal_growl", 0.9f, 0);
                    }
                    break;
                }
                case S.Crouch:
                {
                    // she picks her line a moment before she goes, and does not change her mind
                    float gather = Hurt ? 0.55f : 0.7f;
                    if (stateClock < gather - 0.2f)
                    {
                        facing = FaceOf(d);
                        anim.SetFacing(facing);
                        lungeDir = d.normalized;
                    }
                    if (stateClock > gather)
                    {
                        s = S.Lunge; stateClock = 0; lungeFor = 0.6f;
                        anim.Play("lunge", FaceOf(lungeDir), true);
                        Sfx.Play("jackal_bark", 1f, 0);
                    }
                    break;
                }
                case S.Lunge:
                {
                    var before = pos;
                    float v = 12.5f * Mathf.Lerp(1f, 0.35f, stateClock / lungeFor);
                    Move(lungeDir * v, dt);
                    // a leap that ends against stone leaves her winded
                    if ((pos - before).magnitude < v * dt * 0.35f && stateClock > 0.08f)
                    {
                        s = S.Daze; stateClock = 0;
                        anim.Play("hurt", facing, true);
                        PixelView.I.Shake(2, 0.2f);
                        Sfx.Play("clank", 0.7f, 0);
                        Fx.Dust(pos, 8);
                        break;
                    }
                    if (stateClock > lungeFor) { s = S.Recover; stateClock = 0; anim.Play("idle", facing, true); side = -side; }
                    break;
                }
                case S.Daze:
                    if (stateClock > 1.7f) { s = S.Prowl; stateClock = 0; }
                    break;
                case S.Howl:
                    // head back, and the pack answers
                    if (stateClock > 0.9f)
                    {
                        Sfx.Play("jackal_bark", 1f, 0);
                        PixelView.I.Shake(1, 0.3f);
                        var room = Rooms.Of(pos);
                        var f = room != null ? room.Floor : new Rect(pos - new Vector2(6, 3), new Vector2(12, 6));
                        foreach (var at in new[] { new Vector2(f.xMin + 0.8f, f.yMin + 0.8f), new Vector2(f.xMax - 0.8f, f.yMin + 0.8f) })
                        {
                            // this year's litter: quick, and not much to them yet
                            var j = Jackal.Spawn(at);
                            j.health.max = j.health.hp = 2;
                            Fx.Dust(at, 8);
                        }
                        s = S.Prowl; stateClock = 0;
                    }
                    break;
                case S.Recover:
                    if (stateClock > (Hurt ? 0.6f : 0.8f)) { s = S.Prowl; stateClock = 0; }
                    break;
            }
        }

        protected override void OnHurt(HitInfo h)
        {
            if (s == S.Crouch) { s = S.Recover; stateClock = 0; }
        }

        public override void Blocked(Player p)
        {
            base.Blocked(p);
            if (s == S.Lunge) { s = S.Daze; stateClock = 0.5f; anim.Play("hurt", facing, true); }
        }

        protected override void Die()
        {
            // the pack does not stay for what killed her
            foreach (var e in All.ToArray())
                if (e && e != this && e is Jackal) { Fx.Dust(e.pos, 6); Destroy(e.gameObject); }
            PixelView.I.Shake(3, 0.5f);
            for (int i = 0; i < 9; i++) Pickup.Drop(i % 3 == 0 ? Pickup.Kind.Gold : Pickup.Kind.Shekel, pos + Random.insideUnitCircle * 0.9f);
            Pickup.Drop(Pickup.Kind.Flame, pos + new Vector2(0, 0.4f));
            if (Story.I) Story.I.DenCleared();
            base.Die();
        }
    }
}
