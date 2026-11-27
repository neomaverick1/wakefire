// The Debt. Somebody on the Hill of Sleepers died owing money. Nobody knows who: three hundred
// years of interest have long since covered the name. What is left is the paperwork, which in
// Ashkel is clay, and which has piled itself into the shape of a man, because a man is the
// shape that goes and collects. It has stopped minding whose debt it is. Azar is on the hill,
// has a purse, and is awake.
//
// It follows him, at a walk, wherever on the hill he goes. Close enough, it stops and holds out
// its top tablet: the sum. He can pay it (talk to it), and then it is settled for good. If he
// does not, it brings the tablet down on him and adds that to the account. Broken, it lies in
// pieces for a moment and stacks itself back up one tablet taller, and dearer. It cannot do
// that for ever: the fifth time it has run out of clay.
//
// Three hundred years of interest weighs what it weighs. Before the assessor's vault, at the top
// of the road, there is a plate in the ground that does not notice a man. It notices this.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    /// <summary>Something that is not one of the townsfolk but can be spoken to with the action button.</summary>
    public interface IAnswers
    {
        bool Answers(Player p);
        IEnumerator Answer();
    }

    public class Debt : Enemy, IAnswers
    {
        enum S { Follow, Bill, Slam, Apart, Paid }
        S s;
        /// <summary>How many times it has stacked itself up: 1 the first time it is met, 5 the last.</summary>
        public int level = 1;
        public const int Last = 5;
        int interest;
        float wait;
        bool struck, stacking;

        public static Debt Spawn(Vector2 at) => Make<Debt>("priest", "idle", at, WorldLayer.Waking, 3, "debt");

        protected override void Init()
        {
            speed = 1.3f; half = new Vector2(0.34f, 0.16f); touchDamage = 0; roams = true;
            Size();
        }

        /// <summary>What it is asking, this moment.</summary>
        public int Price => 15 * level + 5 * interest;
        public bool Billing => s == S.Bill;
        public bool InPieces => s == S.Apart;
        public override bool Sleeps => false;
        protected override bool WaitsOutStories => true;
        protected override float KnockScale => 0.3f;
        protected override string HurtSound => "clay_hit";
        protected override Color BurstColor => new Color(0.66f, 0.45f, 0.30f);
        public override Rect HitBox => new Rect(pos.x - 0.5f, pos.y - 0.2f, 1.0f, 2.2f + 0.2f * level);

        void Size()
        {
            health.max = health.hp = 2 + level;
            if (anim.model) anim.model.rig.localScale = Vector3.one * anim.model.def.scale * (1f + 0.09f * (level - 1));
        }

        public bool Answers(Player p) =>
            Present && (s == S.Bill || s == S.Follow) && Vector2.Distance(p.pos, pos) < 1.7f && Vector2.Dot(p.Dir, (pos - p.pos).normalized) > 0.3f;

        public IEnumerator Answer()
        {
            var p = Player.I;
            if (Story.Bump("debt_met") == 0)
                yield return Story.Narrate("A debt.^Somebody up here died owing it, three hundred years ago, and it has been earning ever since.| The name wore off long ago. It has stopped minding who pays.");
            int price = Price;
            yield return DialogueBox.Ask(null, $"The top tablet says {{g}}{price} shekels{{/}}.^You have {p.coins}.", "Pay it", "Not now");
            if (DialogueBox.Choice != 0) { wait = 0.8f; yield break; }
            if (p.coins < price)
            {
                yield return Story.Narrate($"You are {price - p.coins} short.^It makes a note of that.");
                interest++;
                wait = 0.4f;
                yield break;
            }
            p.coins -= price;
            Sfx.Play("coin_big", 0.9f, 0.02f);
            yield return Story.Narrate("It counts them. Twice.^Then it turns the top tablet round. {g}PAID IN FULL.{/}| It has no further reason to be standing up.");
            s = S.Paid; stateClock = 0;
            anim.Play("yes", facing, true);
            Story.Set("debt_paid");
            if (Story.I) Story.I.DebtSettled(true);
        }

        /// <summary>A plate that does not notice a man notices this, whole or in pieces.</summary>
        void Weigh()
        {
            var map = Map.Current;
            if (!map) return;
            foreach (var pr in map.props)
                if (pr && pr.Kind == "plate" && !pr.lit && Vector2.Distance(pr.basePos, pos) < 0.5f)
                {
                    map.Press(pr);
                    PixelView.I.Shake(1, 0.12f);
                    if (Story.I) Story.I.DebtWeighed();
                }
        }

        protected override void Think(float dt, Player p)
        {
            wait -= dt;
            Weigh();
            var d = p.pos - pos;
            switch (s)
            {
                case S.Follow:
                    if (!Present || p.Hidden) { anim.Play("idle", facing); vel = Vector2.zero; break; }
                    facing = FaceOf(d);
                    if (d.magnitude < 1.45f && wait <= 0 && Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos))
                    {
                        s = S.Bill; stateClock = 0;
                        anim.Play("bill", facing, true);
                        Sfx.Play("debt_bill", 0.8f, 0.05f);
                        if (Story.I) Story.I.DebtBilled();
                        break;
                    }
                    if (d.magnitude < 1.2f) { anim.Play("idle", facing); vel = Vector2.zero; break; }
                    anim.Play("walk", facing);
                    anim.SetFacing(facing);
                    Move(d.normalized * (speed + 0.12f * (level - 1)), dt);
                    break;

                case S.Bill:
                    // the sum, held out where he can read it, for as long as a collector's patience lasts
                    vel = Vector2.zero;
                    facing = FaceOf(d); anim.SetFacing(facing);
                    if (d.magnitude > 2.6f) { s = S.Follow; wait = 0.6f; break; }
                    if (stateClock > 2.8f) { s = S.Slam; stateClock = 0; struck = false; interest++; anim.Play("slam", facing, true); Sfx.Play("debt_lift", 0.8f, 0.05f); }
                    break;

                case S.Slam:
                    if (!struck && stateClock > 0.5f)
                    {
                        struck = true;
                        var at = pos + (facing == Facing.Down ? Vector2.down : facing == Facing.Up ? Vector2.up : facing == Facing.Left ? Vector2.left : Vector2.right) * 0.9f;
                        Sfx.Play("debt_slam", 0.9f, 0.05f);
                        PixelView.I.Shake(2, 0.14f);
                        Fx.Dust(at, 6);
                        if (Present && Vector2.Distance(at, p.pos) < 1.05f && Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos))
                            p.Hurt(new HitInfo { damage = 1, from = pos, knockback = 6f, kind = HitKind.Heavy, source = gameObject });
                    }
                    if (stateClock > 1.1f) { s = S.Follow; stateClock = 0; wait = 1.2f; }
                    break;

                case S.Apart:
                    // in pieces: a moment's peace, and then the sound of tablets finding each other
                    vel = Vector2.zero;
                    if (!stacking && stateClock > 1.7f) { stacking = true; Sfx.Play("debt_stack", 0.9f, 0.04f); }
                    if (stateClock > 2.6f)
                    {
                        level++;
                        Size();
                        s = S.Follow; stateClock = 0; wait = 1.0f;
                        flash = 0.2f;
                        Fx.Dust(pos, 10);
                        anim.Play("idle", facing, true);
                        if (Story.I) Story.I.DebtRestacked(level);
                    }
                    break;

                case S.Paid:
                    // it nods, and lies down where it stands: a paid debt stays where it was paid
                    vel = Vector2.zero;
                    if (stateClock > 1.2f)
                    {
                        Fx.Dust(pos, 8);
                        Sfx.Play("debt_stack", 0.7f, 0.04f);
                        if (spawnId != null) Story.Set("dead_" + spawnId);
                        Story.SetCount("debt_x", Mathf.RoundToInt(pos.x * 16f));
                        Story.SetCount("debt_y", Mathf.RoundToInt(pos.y * 16f));
                        if (Story.I) Story.I.DebtLiesDown();
                        Rooms.Slain(this);
                        Destroy(gameObject);
                    }
                    break;
            }
        }

        void Tablets(int n)
        {
            for (int i = 0; i < n; i++)
                Fx.Spawn(pos + new Vector2(Random.Range(-0.4f, 0.4f), 0), Random.insideUnitCircle * 3.0f, Random.Range(0.3f, 1.6f), Random.Range(1.5f, 5f), Random.Range(0.5f, 0.9f),
                    i % 3 == 0 ? new Color(0.80f, 0.58f, 0.38f) : new Color(0.60f, 0.40f, 0.26f), new Color(0.32f, 0.20f, 0.14f), 18f, 2);
        }

        public override void Blocked(Player p) { base.Blocked(p); s = S.Follow; wait = 1.4f; }

        protected override void OnHurt(HitInfo h) => Tablets(3);

        /// <summary>Broken, it is a heap of tablets, and then it is a taller Debt. The fifth time there is no clay left.</summary>
        protected override void Die()
        {
            Tablets(16);
            Sfx.Play("statue_break", 0.9f, 0.05f);
            PixelView.I.Shake(2, 0.16f);
            if (level >= Last)
            {
                if (Story.I) { Story.I.DebtOutOfClay(); Story.I.DebtSettled(false); }
                Pickup.Chance(pos, 1f, 0.5f);
                base.Die();
                return;
            }
            s = S.Apart; stateClock = 0; stacking = false;
            anim.Play("lie", facing, true);
        }

        // ---------------------------------------------------------------------------- what it is made of
        static float Hash(float x) => Mathf.Repeat(Mathf.Sin(x * 127.1f) * 43758.5453f, 1f);

        /// <summary>The man the tablets are stacked on is not there: only the tablets are. Each lies along one bone
        /// of the body and goes where the bone goes, so the heap walks like a man.</summary>
        public static void Dress(ModelActor m)
        {
            var t = new Tailor(m);
            foreach (var r in m.parts) r.enabled = false;
            var kit = new Kit(t);
            // fired clay, red where the kiln was hot and nearly black where it was hotter: darker than the ground it walks on
            Color[] clay = { new Color(0.56f, 0.30f, 0.19f), new Color(0.40f, 0.21f, 0.14f), new Color(0.68f, 0.40f, 0.25f) };
            Color ink = new Color(0.20f, 0.10f, 0.07f), seal = new Color(0.80f, 0.16f, 0.10f);
            int n = 0;
            void Stack(string bone, Vector3 a, Vector3 b, float wide, float deep, int count, bool written = true)
            {
                var axis = b - a;
                float len = axis.magnitude;
                if (len < 0.001f) return;
                var y = axis / len;
                var x = Vector3.Cross(y, Mathf.Abs(y.z) < 0.9f ? Vector3.forward : Vector3.right).normalized;
                var z = Vector3.Cross(x, y);
                for (int i = 0; i < count; i++)
                {
                    var c = Vector3.Lerp(a, b, (i + 0.5f) / count);
                    var q = Quaternion.AngleAxis((Hash(n * 1.3f) - 0.5f) * 30f, y);       // no two lie square on each other
                    float w = wide * (0.88f + Hash(n * 2.1f) * 0.24f), h = len / count * 0.90f;
                    kit.On(bone).Paint(clay[n % 3]).Frame(c, q * x, y, q * z);
                    kit.Box(Vector3.zero, new Vector3(w, h, deep));
                    if (written)
                    {
                        // the writing: lines of it, front and back
                        kit.Paint(ink);
                        for (int k = -1; k <= 1; k++)
                            foreach (int face in new[] { -1, 1 })
                                kit.Box(new Vector3(0, k * h * 0.26f, face * (deep * 0.5f + 0.003f)), new Vector3(w * 0.72f, Mathf.Min(0.014f, h * 0.12f), 0.006f));
                    }
                    n++;
                }
                kit.Frame();
            }
            Vector3 up = Vector3.up, fwd = Vector3.forward;
            Vector3 pelvis = t.At("pelvis"), s1 = t.At("spine_01"), s3 = t.At("spine_03"), neck = t.At("neck_01"), head = t.At("Head");
            Stack("pelvis", pelvis - up * 0.10f, s1 + up * 0.02f, 0.36f, 0.22f, 1);
            Stack("spine_02", s1 + up * 0.02f, neck - up * 0.02f, 0.42f, 0.24f, 3);
            // the head: two tablets, and the top one is the bill, with a seal on it
            Stack("Head", neck, head + up * 0.20f, 0.25f, 0.20f, 2);
            kit.On("Head").Paint(seal).Box(head + up * 0.13f + fwd * 0.104f, new Vector3(0.07f, 0.07f, 0.012f));
            foreach (var side in new[] { "_l", "_r" })
            {
                Vector3 sh = t.At("upperarm" + side), el = t.At("lowerarm" + side), wr = t.At("hand" + side), fi = t.At("middle_01" + side);
                Stack("upperarm" + side, sh, el, 0.15f, 0.13f, 2);
                Stack("lowerarm" + side, el, wr, 0.14f, 0.12f, 2);
                Stack("hand" + side, wr, wr + (fi - wr).normalized * 0.16f, 0.15f, 0.06f, 1, false);
                Vector3 hip = t.At("thigh" + side), kn = t.At("calf" + side), an = t.At("foot" + side), ba = t.At("ball" + side);
                Stack("thigh" + side, hip, kn, 0.19f, 0.17f, 2);
                Stack("calf" + side, kn, an, 0.17f, 0.15f, 2);
                Stack("foot" + side, an - up * 0.02f, ba + fwd * 0.05f, 0.14f, 0.09f, 1, false);
            }
            kit.Wear("Debt");
        }
    }
}
