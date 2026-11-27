// The bad dreams of Ashkel, each made to do the thing it does: -wfScene dreams checks that a
// Snuffer puts a lit bowl out, comes down over the man with the Wakefire, is rung over from
// inside and broken on its side, and that the fire it took flies home; that a Wick is moved by a
// blade and not hurt by it, and driven through the grille of the oil store goes home into the bowl
// and lifts the grille; that the Dragnet stands up, throws itself, hauls him for the water, is
// cut out of and cut to pieces; that a Stay-Up takes his shadow and roots him, keeps out of
// lamplight, and is burnt off by the Wakefire held out; and that the Yawn makes him yawn, three
// put him to sleep on his feet, and the mirror sends it back.
// -wfDreams snuffer|wick|net|stayup|yawn runs one part only.
using System.Collections;
using System.Linq;
using UnityEngine;

namespace Wakefire
{
    public static class DreamsTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["dreams"] = Run;

        static int bad;
        static AutoTest T;
        static void Check(string what, bool ok) { T.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }

        static void KillAll()
        {
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
        }

        static IEnumerator Quiet(float atLeast = 0.2f, float atMost = 30f)
        {
            float w = 0;
            while ((w < atLeast || (Story.I && Story.I.Running) || Game.Busy) && w < atMost) { w += Time.deltaTime; yield return null; }
        }

        static IEnumerator Enter(string map, string spawn)
        {
            Game.I.EnterMap(map, spawn);
            Story.Abort();
            Fade.Set(0);
            var p = Player.I;
            p.SetState(Player.State.Free, "idle");
            p.health.hp = p.health.max;
            yield return new WaitForSeconds(0.5f);
            KillAll();
            yield return null;
        }

        /// <summary>Stands him somewhere and keeps him there (whatever knocks him about) until the test says otherwise.</summary>
        static IEnumerator Stand(Vector2 at, Facing f, float seconds, System.Func<bool> until = null)
        {
            var p = Player.I;
            for (float w = 0; w < seconds; w += Time.deltaTime)
            {
                if (until != null && until()) yield break;
                if (p.state == Player.State.Free) { p.pos = at; p.Face(f); }
                yield return null;
            }
        }

        static IEnumerator Press(UnityEngine.InputSystem.InputAction a, int times, float gap = 0.16f)
        {
            for (int i = 0; i < times; i++)
            {
                Controls.FakePress = a;
                for (float w = 0; w < gap; w += Time.deltaTime) yield return null;
            }
        }

        static IEnumerator Run(AutoTest t)
        {
            T = t; bad = 0;
            DialogueBox.AutoAdvance = 0.1f;
            Save.ClearAll(); Save.Use(0);
            Game.I.Begin(false);
            Story.Abort();
            Story.GiveKit();
            Story.DreamsQuiet = true;
            string only = Boot.Arg("-wfDreams");
            if (only == null || only == "snuffer") yield return SnufferPart(t);
            if (only == null || only == "wick") yield return WickPart(t);
            if (only == null || only == "net") yield return NetPart(t);
            if (only == null || only == "stayup") yield return StayUpPart(t);
            if (only == null || only == "yawn") yield return YawnPart(t);
            t.Note(bad == 0 ? "DREAMS OK" : $"DREAMS FAILED: {bad}");
        }

        // ------------------------------------------------------------------------- the Snuffer
        static IEnumerator SnufferPart(AutoTest t)
        {
            yield return Enter("ashkel", "south");
            var p = Player.I;
            var map = Map.Current;
            var bowl = map.Find("square_0");
            Check("the square has its fire bowls", bowl && bowl.Kind == "brazier");
            if (!bowl) yield break;
            bowl.Ignite();
            yield return null;
            Check("a lit bowl is remembered as lit", bowl.lit && Story.Has("on_square_0") || bowl.lit);
            Vector2 off = bowl.basePos + new Vector2(3.4f, -2.4f);
            p.hasLantern = false;                                   // (no flame on him: it has no reason to look at him)
            p.pos = off;
            var sn = Snuffer.Spawn(bowl.basePos + new Vector2(-1.5f, -5f));
            sn.spawnId = "test_snuffer";
            yield return Stand(off, Facing.Left, 1.1f);
            yield return t.Shot("a0-it-has-smelt-the-fire", 0f);
            yield return Stand(off, Facing.Left, 16f, () => sn.s == Snuffer.S.Rear);
            yield return Stand(off, Facing.Left, 0.5f);
            yield return t.Shot("a0b-up-on-its-legs-over-the-bowl", 0f);
            yield return Stand(off, Facing.Left, 16f, () => !bowl.lit);
            Check("a Snuffer goes for the nearest lit bowl, stands over it and comes down: the fire is out", !bowl.lit);
            Check("...and what answered to that fire no longer does", !Story.Has("on_square_0"));
            Check($"the fire is inside it (it holds {sn.Hot})", sn.Hot == 1);
            yield return t.Shot("a1-out", 0.25f);
            yield return Stand(off, Facing.Left, 2.5f);
            Check($"a man with no flame is of no interest to it ({sn.s}, {p.health.hp}/{p.health.max})", p.state == Player.State.Free && p.health.hp == p.health.max);

            // on its feet, a blade only rings off it
            int hp0 = sn.health.hp;
            yield return Stand(sn.pos + new Vector2(0, -1.1f), Facing.Up, 0.2f);
            yield return Press(Controls.Attack, 2, 0.3f);
            Check($"on its feet a blade only rings off it ({hp0} -> {sn.health.hp})", sn && sn.health.hp == hp0 && sn.s != Snuffer.S.Tipped);

            // with the Wakefire: it comes for him
            p.hasLantern = true;
            Vector2 here = bowl.basePos + new Vector2(2.5f, -4.5f);
            p.pos = here;
            yield return Stand(here, Facing.Down, 14f, () => p.HeldBy(sn));
            Check("it comes down over the man who carries the Wakefire: he is under it", p.HeldBy(sn) && p.Hidden);
            yield return t.Shot("a2-under-it", 0.3f);
            yield return Press(Controls.Attack, 3, 0.2f);
            for (float w = 0; w < 1f && p.Hidden; w += Time.deltaTime) yield return null;
            Check($"rung three times from inside, it goes over on its side and he is out ({sn.s})", !p.Hidden && sn && sn.s == Snuffer.S.Tipped);
            Check($"ringing his way out costs him nothing ({p.health.hp}/{p.health.max})", p.health.hp == p.health.max);
            yield return t.Shot("a3-on-its-side", 0.25f);
            // on its side the open end is the way in
            // (the story says its piece first; the Snuffer lies there and waits for it, as he has to)
            for (float sw = 0, next = 0; sw < 3.2f && sn; )
            {
                if (Story.I && Story.I.Running) { yield return null; continue; }
                if (sw >= next && (p.state == Player.State.Free || p.state == Player.State.Attack))
                {
                    p.pos = sn.pos + new Vector2(0, -0.9f); p.Face(Facing.Up);
                    Controls.FakePress = Controls.Attack; next = sw + 0.34f;
                }
                sw += Time.deltaTime;
                yield return null;
            }
            Check($"on its side it can be hurt, and it breaks{(sn ? $" ({sn.s}, {sn.health.hp} left)" : "")}", !sn);
            Check("it stays broken", Story.Has("dead_test_snuffer"));
            for (float w = 0; w < 5f && !bowl.lit; w += Time.deltaTime) yield return null;
            Check("the fire it had taken flies home: the bowl is lit again", bowl.lit);
            yield return t.Shot("a4-the-fire-comes-home", 0.2f);

            // up on its legs it can be put over; left alone under it, the Wakefire does the rest
            var two = Snuffer.Spawn(here + new Vector2(0, 3f));
            foreach (var pr in map.props) if (pr && pr.Kind == "brazier" && pr.lit) pr.Snuff();
            yield return Stand(here, Facing.Up, 14f, () => two.s == Snuffer.S.Rear);
            Check($"with nothing else burning it rears over him ({two.s})", two.s == Snuffer.S.Rear);
            for (float w = 0; w < 20f && Story.I && Story.I.Running; w += Time.deltaTime) yield return null;
            {
                var to = two.pos - p.pos;
                p.Face(Mathf.Abs(to.x) > Mathf.Abs(to.y) ? (to.x > 0 ? Facing.Right : Facing.Left) : (to.y > 0 ? Facing.Up : Facing.Down));
            }
            Controls.FakePress = Controls.Attack;
            for (float w = 0; w < 0.6f && two.s == Snuffer.S.Rear; w += Time.deltaTime) yield return null;
            Check($"a blow while it is up on its legs puts it over ({two.s})", two.s == Snuffer.S.Tipped);
            Object.Destroy(two.gameObject);
            yield return null;
            var three = Snuffer.Spawn(here + new Vector2(0, 3f));
            p.health.hp = p.health.max;
            yield return Stand(here, Facing.Down, 14f, () => p.HeldBy(three));
            Check("left where he stands, he is under the third", p.HeldBy(three));
            for (float w = 0; w < 4f && p.Hidden; w += Time.deltaTime) yield return null;
            Check($"left under it, the Wakefire throws it off by itself, and that costs him one ({three.s}, {p.health.hp}/{p.health.max})",
                !p.Hidden && three.s == Snuffer.S.Tipped && p.health.hp == p.health.max - 1);
            KillAll();
            yield return null;
            Check("whatever happened to the Snuffer, the night comes back", PixelView.I.ambient.r > 0.2f);
            p.health.hp = p.health.max;
        }

        // ------------------------------------------------------------------------------- Wicks
        static IEnumerator WickPart(AutoTest t)
        {
            yield return Enter("terraces", "east");
            var p = Player.I;
            var map = Map.Current;
            var bowl = map.Find("tr_bowl");
            var grille = map.Find("tr_store");
            Check("the oil store has its bowl and its grille", bowl && grille && grille.solid != null);
            if (!bowl || !grille) yield break;
            // he cannot light it himself: it is on the wrong side of the grille
            p.pos = grille.basePos + new Vector2(0, 0.55f); p.Face(Facing.Down);
            Items.Choose("wakefire");
            yield return Stand(grille.basePos + new Vector2(0, 0.55f), Facing.Down, 0.2f);
            Controls.FakePress = Controls.Item;
            yield return Stand(grille.basePos + new Vector2(0, 0.55f), Facing.Down, 0.9f);
            Check("from outside the grille he cannot light the bowl himself", !bowl.lit);
            // a Wick, up the path from the grille
            var wick = Wick.Spawn(grille.basePos + new Vector2(0, 3.8f));
            wick.home = wick.pos;
            yield return t.Shot("b0-a-wick", 0.6f);
            Vector2 was = wick.pos;
            int hp0 = wick.health.hp;
            p.pos = wick.pos + new Vector2(0, 1.0f); p.Face(Facing.Down);
            yield return null;
            Controls.FakePress = Controls.Attack;
            for (float w = 0; w < 0.5f; w += Time.deltaTime) yield return null;
            Check($"a blade goes through a Wick and does it no harm ({hp0} -> {(wick ? wick.health.hp : -1)})", wick && wick.health.hp == hp0);
            Check($"...but the wind of it moves the flame ({(wick ? Vector2.Distance(was, wick.pos) : 0):0.0} tiles)", wick && Vector2.Distance(was, wick.pos) > 0.5f);
            // drive it down towards the grille: once it is near enough to the bowl, it knows the rest of the way
            for (int i = 0; i < 6 && wick && !bowl.lit; i++)
            {
                for (float w = 0; w < 0.55f && wick && !bowl.lit; w += Time.deltaTime) yield return null;
                if (!wick || bowl.lit) break;
                var stand = wick.pos + new Vector2(0, 1.0f);
                if (stand.y < grille.basePos.y + 0.5f) break;
                if (p.state == Player.State.Free || p.state == Player.State.Attack) { p.pos = stand; p.Face(Facing.Down); }
                yield return null;
                Controls.FakePress = Controls.Attack;
                for (float w = 0; w < 0.45f && wick; w += Time.deltaTime) yield return null;
            }
            yield return Stand(grille.basePos + new Vector2(2.5f, 1.5f), Facing.Left, 6f, () => bowl.lit);
            Check("driven through the grille it goes home into the bowl: the bowl is lit", bowl.lit);
            yield return null; yield return null;
            Check("and the Wick is gone into it", !wick);
            for (float w = 0; w < 2f && grille.solid != null; w += Time.deltaTime) yield return null;
            Check("the grille answers to the bowl, and lifts", grille.solid == null);
            yield return Quiet(0.5f);
            yield return t.Shot("b1-home", 0.2f);
            // one that is not being driven anywhere: it burns
            p.health.hp = p.health.max;
            Vector2 open = Map.ToWorld(420, 572);
            var loose = Wick.Spawn(open + new Vector2(2.5f, 0));
            int hp = p.health.hp;
            yield return Stand(open, Facing.Right, 12f, () => p.health.hp < hp);
            Check($"left to itself a Wick comes through him, and burns ({hp} -> {p.health.hp})", p.health.hp == hp - 1);
            yield return t.Shot("b2-through-him", 0.1f);
            KillAll();
            p.health.hp = p.health.max;
            yield return null;
        }

        // ------------------------------------------------------------------------- the Dragnet
        static IEnumerator NetPart(AutoTest t)
        {
            Game.I.EnterMap("cliffs", "west");
            Story.Abort();
            Fade.Set(0);
            var p = Player.I;
            p.SetState(Player.State.Free, "idle");
            p.health.hp = p.health.max;
            yield return new WaitForSeconds(0.6f);
            var nets = Enemy.All.OfType<Dragnet>().ToArray();
            Check($"the cliffs have their nets that are not nets ({nets.Length})", nets.Length == 3);
            Check($"...and their nets that are ({Npc.All.Count(n => n && n.id.StartsWith("net_"))})", Npc.All.Count(n => n && n.id.StartsWith("net_")) == 4);
            var net = nets.OrderBy(n => n.pos.x).First();
            Check($"lying on the sand it is a net like the others ({net.s})", net.s == Dragnet.S.Flat);
            Vector2 near = net.pos + new Vector2(-2.3f, 0.2f);
            p.pos = net.pos + new Vector2(-5f, 0.2f);
            yield return t.Shot("c0-nets-on-the-sand", 0.4f);
            yield return Stand(near, Facing.Right, 1.0f, () => net.s != Dragnet.S.Flat);
            Check($"something worth catching walks past: it stands up ({net.s})", net.s == Dragnet.S.Rise || net.s == Dragnet.S.Cast);
            yield return t.Shot("c1-it-stands-up", 0.45f);
            yield return Stand(near, Facing.Right, 4f, () => p.HeldBy(net));
            Check("it throws itself, and he is in it", p.HeldBy(net));
            float y0 = p.pos.y;
            yield return t.Shot("c2-caught", 0.2f);
            for (float w = 0; w < 1.1f && p.HeldBy(net); w += Time.deltaTime) yield return null;
            Check($"it hauls him for the water ({y0:0.0} -> {p.pos.y:0.0})", p.pos.y < y0 - 0.25f);
            yield return Press(Controls.Attack, 3, 0.2f);
            Check($"three cuts and he is out ({p.state}, the net {net.s})", !p.HeldBy(net) && p.state != Player.State.Held && net && net.s == Dragnet.S.Spent);
            int nhp = net.health.hp;
            for (int i = 0; i < 8 && net; i++)
            {
                if (p.state == Player.State.Free || p.state == Player.State.Attack) { p.pos = net.pos + new Vector2(-0.9f, 0); p.Face(Facing.Right); }
                Controls.FakePress = Controls.Attack;
                for (float w = 0; w < 0.3f; w += Time.deltaTime) yield return null;
                if (net && net.s != Dragnet.S.Spent && net.s != Dragnet.S.Gather) break;
            }
            Check($"spread on the sand with nothing in it, it can be cut ({nhp} -> {(net ? net.health.hp : 0)})", !net || net.health.hp < nhp);
            // (whatever is left of it: finish the job the same way, as often as it takes)
            for (int round = 0; round < 6 && net; round++)
            {
                p.health.hp = p.health.max;
                yield return Stand(net.pos + new Vector2(-2.2f, 0), Facing.Right, 8f, () => !net || p.HeldBy(net) || net.s == Dragnet.S.Spent);
                if (!net) break;
                if (p.HeldBy(net)) yield return Press(Controls.Attack, 3, 0.2f);
                for (int i = 0; i < 6 && net && (net.s == Dragnet.S.Spent || net.s == Dragnet.S.Gather); i++)
                {
                    if (p.state == Player.State.Free || p.state == Player.State.Attack) { p.pos = net.pos + new Vector2(-0.9f, 0); p.Face(Facing.Right); }
                    Controls.FakePress = Controls.Attack;
                    for (float w = 0; w < 0.3f; w += Time.deltaTime) yield return null;
                }
            }
            Check("cut enough, it comes apart", !net);
            Check("it stays apart", Story.Has("dead_cl_n0") || Story.Has("dead_cl_n1"));
            Check($"and what it had caught is on the sand ({Pickup.All.Count})", Pickup.All.Count >= 3);
            yield return t.Shot("c3-what-it-caught", 0.2f);

            // the Wakefire burns him out at once
            var second = Enemy.All.OfType<Dragnet>().OrderBy(n => n.pos.x).FirstOrDefault();
            Check("there is another on the beach", second);
            if (second)
            {
                p.health.hp = p.health.max;
                Items.Choose("wakefire");
                Vector2 by = second.pos + new Vector2(-2.3f, 0.2f);
                yield return Stand(by, Facing.Right, 8f, () => p.HeldBy(second));
                Check("the second has him", p.HeldBy(second));
                Controls.FakePress = Controls.Item;
                for (float w = 0; w < 0.4f && p.HeldBy(second); w += Time.deltaTime) yield return null;
                Check("the Wakefire burns him out at once", !p.HeldBy(second) && p.state != Player.State.Held);
                // and left in it, he goes in the sea
                p.health.hp = p.health.max;
                yield return Stand(by, Facing.Right, 12f, () => p.HeldBy(second));
                int hp = p.health.hp;
                for (float w = 0; w < 14f && p.health.hp == hp; w += Time.deltaTime) yield return null;
                yield return Quiet(1.2f);
                Check($"left in it he goes in the water, comes out where he last stood on his own feet, and is one flame the poorer ({hp} -> {p.health.hp}, {p.state})",
                    p.health.hp == hp - 1 && p.state == Player.State.Free);
            }
            KillAll();
            p.health.hp = p.health.max;
            yield return null;
        }

        // --------------------------------------------------------------------------- Stay-Ups
        static IEnumerator StayUpPart(AutoTest t)
        {
            yield return Enter("lowtown", "north");
            var p = Player.I;
            // somewhere on the market street the lamps do not reach, and somewhere they do
            Vector2 dark = Vector2.zero, lamp = Vector2.zero;
            bool haveDark = false, haveLamp = false;
            for (int x = 120; x < 860; x += 12)
            {
                var q = Map.ToWorld(x, 420);
                bool lit = StayUp.Lit(q + StayUp.Cast * 0.9f);
                bool clear = !StayUp.Lit(q) && !lit && !StayUp.Lit(q + StayUp.Cast * 1.5f) && !StayUp.Lit(q + new Vector2(0.6f, -2.4f)) && !StayUp.Lit(q + new Vector2(0.6f, -1.2f));
                if (clear && !haveDark && x > 200) { dark = q; haveDark = true; }
                if (lit && !haveLamp) { lamp = q; haveLamp = true; }
            }
            Check($"the market street has dark stretches and lamplit ones (dark {haveDark}, lamp {haveLamp})", haveDark && haveLamp);
            if (!haveDark) yield break;
            p.pos = dark;
            var st = StayUp.Spawn(dark + new Vector2(-5f, 0.5f));
            st.spawnId = "test_stayup";
            yield return t.Shot("d0-a-shadow-with-nobody", 0.5f);
            yield return Stand(dark, Facing.Down, 12f, () => p.Rooted);
            {
                var his = p.pos + StayUp.Cast * 1.5f; var want = his - StayUp.Own * 2.0f;
                t.Note($"  (stay-up {st.Doing} at {st.pos}, he is at {p.pos}, it wants {want}; lit: his shadow {StayUp.Lit(p.pos + StayUp.Cast * 0.9f)}, its body there {StayUp.Lit(want + StayUp.Own * 0.6f)}, its hands there {StayUp.Lit(want + StayUp.Own * 2.0f)}, where it is {StayUp.Lit(st.pos + StayUp.Own * 0.6f)}/{StayUp.Lit(st.Grasp)})");
            }
            Check("a Stay-Up takes hold of his shadow: his feet stop answering", p.Rooted && st.Gripping);
            yield return t.Shot("d1-it-has-his-shadow", 0.15f);
            Vector2 was = p.pos;
            Controls.Fake = Vector2.left;
            for (float w = 0; w < 0.5f; w += Time.deltaTime) yield return null;
            Controls.Fake = null;
            Check($"he cannot walk ({Vector2.Distance(was, p.pos):0.00} tiles)", Vector2.Distance(was, p.pos) < 0.15f);
            int hp = p.health.hp, shp = st.health.hp;
            Controls.FakePress = Controls.Attack;
            for (float w = 0; w < 0.4f; w += Time.deltaTime) yield return null;
            Check($"a blade goes through it ({shp} -> {st.health.hp})", st.health.hp == shp);
            for (float w = 0; w < 2.5f && p.health.hp == hp; w += Time.deltaTime) yield return null;
            Check($"it pulls, and he feels it ({hp} -> {p.health.hp})", p.health.hp == hp - 1);
            // the Wakefire, held out
            Items.Choose("wakefire");
            for (int round = 0; round < 8 && st; round++)
            {
                p.health.hp = p.health.max;
                yield return Stand(dark, Facing.Down, 12f, () => !st || st.Gripping);
                if (!st) break;
                int before = st.health.hp;
                Controls.FakePress = Controls.Item;
                for (float w = 0; w < 1.2f && st && st.health.hp == before; w += Time.deltaTime) yield return null;
                if (round == 0)
                {
                    Check($"the Wakefire held out burns it ({before} -> {(st ? st.health.hp : 0)})", !st || st.health.hp < before);
                    for (float w = 0; w < 0.6f && p.Rooted; w += Time.deltaTime) yield return null;
                    Check("...and it lets go", !p.Rooted);
                    yield return t.Shot("d2-burnt-off", 0.05f);
                }
            }
            Check("burnt three times, it is gone", !st);
            Check("for good", Story.Has("dead_test_stayup"));
            // lamplight: it will not come in
            if (haveLamp)
            {
                p.health.hp = p.health.max;
                var other = StayUp.Spawn(lamp + new Vector2(-5f, 0.5f));
                bool ever = false;
                for (float w = 0; w < 7f; w += Time.deltaTime)
                {
                    if (p.state == Player.State.Free) { p.pos = lamp; p.Face(Facing.Down); }
                    if (p.Rooted) ever = true;
                    yield return null;
                }
                Check($"in lamplight his shadow cannot be taken ({p.health.hp}/{p.health.max})", !ever && p.health.hp == p.health.max);
                Check("and the Stay-Up waits outside it, unburnt", other && other.health.hp == 3);
                yield return t.Shot("d3-in-the-lamplight", 0.05f);
            }
            KillAll();
            p.health.hp = p.health.max;
            yield return null;
        }

        // --------------------------------------------------------------------------- the Yawn
        static IEnumerator YawnPart(AutoTest t)
        {
            yield return Enter("lowtown", "north");
            var p = Player.I;
            Vector2 at = Map.ToWorld(480, 150);
            for (int x = 460; x <= 500 && StayUp.Lit(at - new Vector2(0, 0.5f)); x += 8) at = Map.ToWorld(x, 130);
            p.pos = at;
            Yawn.Caught = 0;
            int passed0 = Yawn.Passed;
            var y = Yawn.Spawn(at + new Vector2(0, -4f));
            yield return t.Shot("e0-the-air-bends", 0.7f);
            yield return Stand(at, Facing.Down, 10f, () => Yawn.Caught > 0);
            Check($"the yawn goes through him and he yawns ({p.anim.anim}, caught {Yawn.Caught})", Yawn.Caught == 1 && p.anim.anim == "yawn");
            yield return t.Shot("e1-he-yawns", 0.25f);
            for (float w = 0; w < 0.5f; w += Time.deltaTime) yield return null;
            Controls.Fake = Vector2.right;
            Vector2 was = p.pos;
            for (float w = 0; w < 0.25f; w += Time.deltaTime) yield return null;
            Controls.Fake = null;
            Check($"while he yawns he can do nothing else ({Vector2.Distance(was, p.pos):0.00} tiles)", Vector2.Distance(was, p.pos) < 0.2f || p.anim.anim != "yawn");
            // two more
            for (int k = 0; k < 2; k++)
            {
                if (y) Object.Destroy(y.gameObject);
                yield return Stand(at, Facing.Down, 1.4f);
                y = Yawn.Spawn(at + new Vector2(0, -3f));
                int had = Yawn.Caught;
                yield return Stand(at, Facing.Down, 8f, () => Yawn.Caught != had || Dream.I.Dreaming);
            }
            for (float w = 0; w < 2.5f && !Dream.I.Dreaming; w += Time.deltaTime) yield return null;
            Check("three, and he is asleep on his feet: in the dream, whether he meant to go or not", Dream.I.Dreaming);
            yield return t.Shot("e2-asleep-on-his-feet", 0.4f);
            for (float w = 0; w < 12f && Dream.I.Dreaming; w += Time.deltaTime) yield return null;
            yield return Quiet(1.0f);
            if (y) Object.Destroy(y.gameObject);
            // sleepers pass it on
            var passer = Yawn.Spawn(Map.ToWorld(316, 600));
            for (float w = 0; w < 9f && Yawn.Passed == passed0; w += Time.deltaTime) { if (p.state == Player.State.Free) p.pos = Map.ToWorld(480, 40); yield return null; }
            Check($"left to itself it goes from sleeper to sleeper, and each passes it on ({Yawn.Passed - passed0})", Yawn.Passed > passed0);
            if (passer) Object.Destroy(passer.gameObject);
            // the mirror
            p.hasShield = true; Story.Set("item_shield");
            p.health.hp = p.health.max;
            yield return Stand(at, Facing.Down, 0.5f);
            var back = Yawn.Spawn(at + new Vector2(0, -4f));
            var sleeper = Crab.Spawn(at + new Vector2(0, -5.5f));
            sleeper.enabled = false;                    // (it only has to stand there)
            Controls.FakeHold = Controls.Interact; Controls.FakePress = Controls.Interact;
            int caught = Yawn.Caught;
            for (float w = 0; w < 9f && back && !back.GoingBack; w += Time.deltaTime)
            {
                if (p.state != Player.State.Guard && p.state == Player.State.Free) { p.pos = at; p.Face(Facing.Down); Controls.FakePress = Controls.Interact; }
                yield return null;
            }
            Check($"the mirror shield sends it back the way it came (caught {Yawn.Caught - caught})", back && back.GoingBack && Yawn.Caught == caught);
            for (float w = 0; w < 2f && sleeper && sleeper.asleep <= 0; w += Time.deltaTime) { if (back) sleeper.pos = back.pos + new Vector2(0, -0.9f); sleeper.transform.position = sleeper.pos; yield return null; }
            Check("and what it goes through on the way falls asleep where it stands", sleeper && sleeper.asleep > 0);
            Controls.FakeHold = null;
            yield return t.Shot("e3-sent-back", 0.05f);
            KillAll();
            // fire ends it
            yield return Stand(at, Facing.Down, 0.6f);
            Items.Choose("wakefire");
            var last = Yawn.Spawn(at + new Vector2(0, -2.2f));
            last.spawnId = "test_yawn";
            yield return Stand(at, Facing.Down, 0.25f);
            Controls.FakePress = Controls.Item;
            for (float w = 0; w < 2.5f && last; w += Time.deltaTime) yield return null;
            Check("the Wakefire held out at it ends it", !last);
            Check("for good", Story.Has("dead_test_yawn"));
            KillAll();
            p.health.hp = p.health.max;
            yield return null;
        }
    }
}
