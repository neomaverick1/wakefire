// The staff of the high halls: -wfScene halls checks, in the first hall of the ziggurat, that a
// Medusa turns Azar to stone when he looks and herself when he holds the mirror up, that a
// thurifer's censer comes home off the bronze and ties him up, and that a burning glass burns
// what stands in its line, misses what steps out of it, and breaks on the third time it gets its
// own light back.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class HallsTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["halls"] = Run;

        static IEnumerator Quiet(float atLeast = 0.2f, float atMost = 40f)
        {
            float w = 0;
            while ((w < atLeast || (Story.I && Story.I.Running) || Game.Busy) && w < atMost) { w += Time.deltaTime; yield return null; }
        }

        static IEnumerator Run(AutoTest t)
        {
            int bad = 0;
            void Check(string what, bool ok) { t.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
            DialogueBox.AutoAdvance = 0.1f;
            Save.ClearAll(); Save.Use(0);
            Game.I.Begin(false);
            Story.Abort();
            Story.GiveKit();
            Game.I.EnterMap("zig_1", "south");
            Story.Abort();
            Fade.Set(0);
            var p = Player.I;
            p.SetState(Player.State.Free, "idle");
            p.hasShield = true; Story.Set("item_shield");
            yield return new WaitForSeconds(0.5f);
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            yield return null;
            var hall = Rooms.I.Find("hall");
            Vector2 c = hall.rect.center, stand = c + new Vector2(0, -2.0f);
            float w;
            void Back(Facing f) { p.pos = stand; p.Face(f); }
            void Raise() { Controls.FakeHold = Controls.Interact; Controls.FakePress = Controls.Interact; }

            // ------------------------------------------------------------------ a Medusa
            p.pos = stand + new Vector2(0, -1.4f); p.Face(Facing.Up);
            p.health.hp = p.health.max;
            var m = Medusa.Spawn(c + new Vector2(0, 3.0f));
            yield return new WaitForSeconds(0.4f);
            Check($"a Medusa is found with her back to the room, at her hair ({m.facing})", m.Combing && m.facing == Facing.Up);
            yield return t.Shot("m0-at-her-hair", 0.3f);
            Back(Facing.Up);
            for (w = 0; w < 6f && m.Combing; w += Time.deltaTime) yield return null;
            Check("she notices who has come in, and turns", !m.Combing);
            yield return Quiet(0.3f);
            bool stoned = false;
            int hp0 = p.health.hp;
            for (w = 0; w < 10f && !stoned; w += Time.deltaTime)
            {
                if (p.state == Player.State.Free) Back(Facing.Up);
                stoned = p.Stoned;
                yield return null;
            }
            Check("he meets her eyes: he is stone", stoned);
            if (stoned) yield return t.Shot("m1-he-looked", 0.3f);
            for (w = 0; w < 6f && p.health.hp == hp0; w += Time.deltaTime) yield return null;
            Check($"and she comes over while he waits (life {hp0} -> {p.health.hp})", p.health.hp == hp0 - 2);
            yield return Quiet(1.2f);
            // his back to her: there is nothing for her to meet
            p.health.hp = p.health.max;
            bool stared = false, over = false, turned = false;
            for (w = 0; w < 12f && !over; w += Time.deltaTime)
            {
                if (p.state == Player.State.Free) Back(Facing.Down);
                if (m.Staring) stared = true; else if (stared) over = true;
                turned |= p.Stoned;
                yield return null;
            }
            Check("with his back to her, the look finds nothing to meet", stared && over && !turned);
            // the bronze, square to her
            p.health.hp = p.health.max;
            Back(Facing.Up);
            yield return null;
            Raise();
            bool stone = false;
            for (w = 0; w < 12f && !stone; w += Time.deltaTime)
            {
                if (p.state == Player.State.Free) { Back(Facing.Up); Raise(); }
                stone = m.Stoned;
                yield return null;
            }
            Check("the mirror up and square to her: it is her own eyes she meets, and she is stone", stone && !p.Stoned);
            yield return Quiet(0.3f);
            yield return t.Shot("m2-she-met-herself", 0.1f);
            Controls.FakeHold = null;
            yield return new WaitForSeconds(0.25f);
            int mh = m.health.hp;
            p.pos = m.pos + new Vector2(0, -0.95f); p.Face(Facing.Up);
            yield return null;
            for (int i = 0; i < 3 && m && m.Stoned; i++) { Controls.FakePress = Controls.Attack; yield return new WaitForSeconds(0.36f); }
            Check($"stone can be cut ({mh} -> {(m ? m.health.hp : 0)})", !m || m.health.hp < mh);
            for (w = 0; w < 6f && m && m.Stoned; w += Time.deltaTime) { p.health.hp = p.health.max; yield return null; }
            if (m)
            {
                yield return new WaitForSeconds(0.7f);
                int h1 = m.health.hp;
                m.Hit(new HitInfo { damage = 1, from = m.pos + Tomb.Dir(m.facing), knockback = 1f, kind = HitKind.Slash, source = p.gameObject });
                Check($"awake and from the front, the hair takes it ({h1} -> {m.health.hp})", m.health.hp == h1);
                m.Hit(new HitInfo { damage = 1, from = m.pos - Tomb.Dir(m.facing), knockback = 1f, kind = HitKind.Slash, source = p.gameObject });
                Check($"from behind, it does not ({h1} -> {m.health.hp})", m.health.hp == h1 - 1);
                yield return new WaitForSeconds(0.4f);
                m.Hit(new HitInfo { damage = 99, from = p.pos, knockback = 1f, kind = HitKind.Reflected, source = p.gameObject });
            }
            yield return Quiet(0.6f);
            Check("she is broken", !m);

            // ------------------------------------------------------------------ a thurifer
            p.health.hp = p.health.max;
            Back(Facing.Up);
            p.SetState(Player.State.Free, "idle");
            var th = Thurifer.Spawn(c + new Vector2(0, 2.6f));
            yield return null;
            int th0 = th.health.hp;
            th.Hit(new HitInfo { damage = 1, from = p.pos, knockback = 1f, kind = HitKind.Slash, source = p.gameObject });
            Check($"while the censer goes round, a blade is knocked away ({th0} -> {th.health.hp})", th.health.hp == th0);
            yield return t.Shot("t0-going-round", 0.6f);
            Raise();
            bool tangled = false, wound = false;
            for (w = 0; w < 16f && !tangled; w += Time.deltaTime)
            {
                if (p.state == Player.State.Free) { Back(Facing.Up); Raise(); }
                wound |= th.Winding;
                tangled = th.IsTangled;
                yield return null;
            }
            Check($"he winds it up, lets it out, and off the bronze it comes home round his own neck ({th0} -> {th.health.hp})", wound && tangled && th.health.hp == th0 - 1);
            yield return Quiet(0.3f);
            yield return t.Shot("t1-in-his-own-incense", 0.2f);
            Controls.FakeHold = null;
            yield return new WaitForSeconds(0.25f);
            int th1 = th.health.hp;
            p.pos = th.pos + new Vector2(0, -0.95f); p.Face(Facing.Up);
            yield return null;
            for (int i = 0; i < 2 && th && th.IsTangled; i++) { Controls.FakePress = Controls.Attack; yield return new WaitForSeconds(0.36f); }
            Check($"tied up in his own chain, he can be cut ({th1} -> {(th ? th.health.hp : 0)})", !th || th.health.hp < th1);
            if (th)
            {
                for (w = 0; w < 6f && th.IsTangled; w += Time.deltaTime) yield return null;
                p.health.hp = p.health.max;
                int hpT = p.health.hp;
                for (w = 0; w < 16f && p.health.hp == hpT; w += Time.deltaTime)
                {
                    if (p.state == Player.State.Free) Back(Facing.Up);
                    yield return null;
                }
                Check($"with the bronze down, it lands (life {hpT} -> {p.health.hp})", p.health.hp < hpT);
                th.Hit(new HitInfo { damage = 99, from = p.pos, knockback = 1f, kind = HitKind.Reflected, source = p.gameObject });
            }
            yield return Quiet(0.6f);
            yield return null;
            Check($"he is down, and nothing is left going round ({Object.FindObjectsByType<Censer>(FindObjectsSortMode.None).Length})",
                !th && Object.FindObjectsByType<Censer>(FindObjectsSortMode.None).Length == 0);

            // ------------------------------------------------------------------ a burning glass
            p.health.hp = p.health.max;
            p.SetState(Player.State.Free, "idle");
            Back(Facing.Up);
            yield return new WaitForSeconds(1.1f);          // (he was hit a moment ago: let that pass)
            var g = BurningGlass.Spawn(c + new Vector2(0, 3.2f));
            yield return null;
            int g0 = g.health.hp;
            g.Hit(new HitInfo { damage = 1, from = p.pos, knockback = 1f, kind = HitKind.Slash, source = p.gameObject });
            Check($"a blade makes no impression on it ({g0} -> {g.health.hp})", g.health.hp == g0);
            yield return Quiet(0.3f);
            int hpB = p.health.hp;
            bool shot = false;
            for (w = 0; w < 12f && p.health.hp == hpB; w += Time.deltaTime)
            {
                if (p.state == Player.State.Free) Back(Facing.Up);
                if (g.Gathering && !shot) { shot = true; yield return t.Shot("g0-gathering", 0.5f); }
                yield return null;
            }
            Check($"standing in its line with the bronze down, he is burned (life {hpB} -> {p.health.hp})", p.health.hp == hpB - 2);
            yield return t.Shot("g1-the-line", 0f);
            yield return Quiet(1.2f);
            // out of the line once it has stopped following
            p.health.hp = p.health.max;
            int hpS = p.health.hp;
            bool fired = false, done = false, begun = false;
            for (w = 0; w < 16f && !done; w += Time.deltaTime)
            {
                // (wait for it to begin gathering afresh, with him standing in front of it)
                if (!begun) { begun = g.GatherClock >= 0 && g.GatherClock < 0.2f; if (p.state == Player.State.Free) Back(Facing.Up); yield return null; continue; }
                if (p.state == Player.State.Free) { p.pos = g.GatherClock > 0.62f || g.Firing ? stand + new Vector2(2.2f, 0) : stand; p.Face(Facing.Up); }
                if (g.Firing) fired = true; else if (fired) done = true;
                yield return null;
            }
            Check($"stepping out of the line once it has stopped following, it misses (life {hpS} -> {p.health.hp})", fired && done && p.health.hp == hpS);
            // the bronze up: three times
            for (int n = 1; n <= 3; n++)
            {
                Back(Facing.Up);
                yield return null;
                Raise();
                for (w = 0; w < 14f && g && g.Cracks < n; w += Time.deltaTime)
                {
                    if (p.state == Player.State.Free) { Back(Facing.Up); Raise(); }
                    yield return null;
                }
                Check($"its own light handed back: crack {n} (life {p.health.hp})", !g || g.Cracks >= n);
                yield return Quiet(0.3f);
                if (n == 2) yield return t.Shot("g2-two-cracks", 0.2f);
            }
            Controls.FakeHold = null;
            yield return Quiet(0.6f);
            Check("three times, and it stops being a glass", !g);
            Check($"and none of that cost him anything (life {p.health.hp} of {p.health.max})", p.health.hp == p.health.max);
            t.Note(bad == 0 ? "HALLS OK" : $"FAILED {bad}");
        }
    }
}
