// The Sleeping Watch and the Debt, played through: two watchmen walking their rounds asleep, what
// a noise does to them, what they do to a Snuffer and to Azar; and on the Road of the Dead a debt
// that follows, bills, is broken and is taller, is weighed, and is paid.
//   -wfScene watch [-wfWatch watch|debt]
using System.Collections;
using System.Linq;
using UnityEngine;

namespace Wakefire
{
    public static class WatchTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["watch"] = Run;

        static AutoTest T;
        static int bad;
        static void Check(string what, bool ok) { T.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }

        static IEnumerator Quiet(float atLeast = 0.2f, float atMost = 40f)
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
        }

        /// <summary>He stays where he is put (unless something has him), until the time is up or the thing happens.</summary>
        static IEnumerator Stand(Vector2 at, Facing f, float seconds, System.Func<bool> until = null)
        {
            var p = Player.I;
            for (float w = 0; w < seconds; )
            {
                if (until != null && until()) yield break;
                if (p.state == Player.State.Free && !Game.Busy) { p.pos = at; p.Face(f); }
                if (!(Story.I && Story.I.Running)) w += Time.deltaTime;
                yield return null;
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
            string only = Boot.Arg("-wfWatch");
            if (only == null || only == "watch") yield return WatchPart(t);
            if (only == null || only == "debt") yield return DebtPart(t);
            t.Note(bad == 0 ? "WATCH OK" : $"WATCH FAILED: {bad}");
        }

        // ---------------------------------------------------------------------- the Sleeping Watch
        static IEnumerator WatchPart(AutoTest t)
        {
            yield return Enter("ashkel", "south");
            var p = Player.I;
            var map = Map.Current;
            foreach (var e in Enemy.All.ToArray()) if (e && !(e is SleepWatch)) Object.Destroy(e.gameObject);
            var watch = Enemy.All.OfType<SleepWatch>().ToArray();
            Check($"two of the night watch are out on their rounds ({watch.Length})", watch.Length == 2);
            Check("each has a beat to walk", watch.Length > 0 && watch.All(w => w.beat != null && w.beat.Length >= 2));
            var gong = map.Find("ak_watch_gong");
            Check("the watch has its gong by the drill yard", gong && gong.Kind == "gong");
            if (watch.Length != 2 || !gong) yield break;
            // the one in the square, and the one in the lane
            var w0 = watch.OrderBy(w => Vector2.Distance(w.pos, Map.ToWorld(480, 215))).First();
            Vector2 away = Map.ToWorld(700, 300);
            p.pos = away;
            // left alone, they walk it
            var last = watch.Select(w => w.pos).ToArray();
            var walked = new float[watch.Length];
            for (float w = 0; w < 5f; w += Time.deltaTime)
            {
                if (p.state == Player.State.Free) p.pos = away;
                for (int i = 0; i < watch.Length; i++) { walked[i] += Vector2.Distance(last[i], watch[i].pos); last[i] = watch[i].pos; }
                yield return null;
            }
            Check($"left alone they walk their rounds ({walked[0]:0.0} and {walked[1]:0.0} tiles in five seconds, asleep: {w0.anim.anim})",
                  walked.All(d => d > 2.5f) && (w0.anim.anim == "sleepwalk" || w0.anim.anim == "sleep"));
            p.pos = w0.pos + new Vector2(2.2f, -1.2f); p.Face(Facing.Left);
            yield return t.Shot("f0-the-sleeping-watch", 0.3f);

            // a blade: nobody hits a man who is asleep
            SleepWatch.Bail(4f);
            int hp = w0.health.hp, struck = Story.Count("struck_sleeper");
            p.pos = w0.pos + new Vector2(0, -1.0f); p.Face(Facing.Up);
            yield return null;
            p.pos = w0.pos + new Vector2(0, -1.0f); p.Face(Facing.Up);
            Controls.FakePress = Controls.Attack;
            yield return new WaitForSeconds(0.6f);
            Check($"a blade does nothing to a man who is asleep ({hp} -> {(w0 ? w0.health.hp : -1)}), and the story has a word to say about trying",
                  w0 && w0.health.hp == hp && Story.Count("struck_sleeper") > struck);

            // a noise: they go to it
            p.pos = away;
            var spot = Map.ToWorld(480, 330);
            Noise.Make(spot, 60f);
            yield return null;
            Check("a loud noise, and both of them turn for it", watch.All(w => w.Drawn));
            float d0 = Vector2.Distance(w0.pos, spot);
            yield return Stand(away, Facing.Down, 3f);
            Check($"...and walk to it ({d0:0.0} -> {Vector2.Distance(w0.pos, spot):0.0} tiles)", Vector2.Distance(w0.pos, spot) < d0 - 2.5f || Vector2.Distance(w0.pos, spot) < 1.2f);
            yield return t.Shot("f1-they-heard-something", 0.1f);

            // the gong, rung by hand
            foreach (var w in watch) w.s = SleepWatch.S.Round;
            SleepWatch.Bail(4f);
            Vector2 atGong = gong.basePos + new Vector2(0, -0.8f);
            p.pos = atGong; p.Face(Facing.Up);
            yield return null;
            p.pos = atGong; p.Face(Facing.Up);
            Controls.FakePress = Controls.Interact;
            yield return new WaitForSeconds(0.4f);
            Check($"he rings the watch gong, and they turn for the gong ({watch.Count(w => w.Drawn)} of 2)",
                  watch.All(w => w.Drawn && Vector2.Distance(w.HeardAt, gong.basePos) < 1.5f));

            // one of them walks into a Snuffer
            p.pos = away;
            foreach (var w in watch) w.s = SleepWatch.S.Round;
            w0.pos = Map.ToWorld(462, 340);
            var sn = Snuffer.Spawn(Map.ToWorld(502, 340));
            yield return null;
            Noise.Make(sn.pos, 8f);
            float took = 0;
            while (took < 12f && !SleepWatch.Arresting && sn) { took += Time.deltaTime; if (p.state == Player.State.Free) p.pos = away; yield return null; }
            p.pos = w0.pos + new Vector2(-0.5f, -2.6f);
            yield return t.Shot("f2-a-snuffer-is-nicked", 0.25f);
            for (float w = 0; w < 14f && sn; w += Time.deltaTime) yield return null;
            yield return Quiet(0.4f);
            Check($"a watchman who walks into a Snuffer runs it in: it is gone, and booked (after {took:0.0}s)", !sn && Story.Has("nicked_snuffer"));
            Check("...and he goes back to his round", w0 && w0.s != SleepWatch.S.Arrest && !SleepWatch.Arresting);

            // and one who walks into Azar
            SleepWatch.Bail(0f);
            p.health.invulnerable = 0;
            Vector2 here = Map.ToWorld(470, 384);
            p.pos = here; p.Face(Facing.Up);
            yield return null;
            Noise.Make(here, 60f);
            for (float w = 0; w < 20f && Game.I.CurrentMap != "ashkel_in"; w += Time.deltaTime)
            {
                if (p.state == Player.State.Free && !Game.Busy && Game.I.CurrentMap == "ashkel") { p.pos = here; p.Face(Facing.Up); }
                yield return null;
            }
            yield return Quiet(0.6f);
            p = Player.I;
            string room = Rooms.I && Rooms.I.current != null ? Rooms.I.current.id : "none";
            Check($"a watchman who walks into Azar runs him in: he comes to in the lock-up (map {Game.I.CurrentMap}, room {room})", Game.I.CurrentMap == "ashkel_in" && room == "wt_lock");
            Check("...and is let alone for a little while after", SleepWatch.OnBail);
            Check("the Snuffer is in there already", Npc.All.Any(n => n && n.id == "nicked"));
            Check($"he has not been hurt ({p.health.hp}/{p.health.max}) and can walk ({p.state})", p.health.hp == p.health.max && p.state == Player.State.Free);
            yield return t.Shot("f3-the-lock-up-from-the-inside", 0.4f);
        }

        // ------------------------------------------------------------------------------- the Debt
        static IEnumerator DebtPart(AutoTest t)
        {
            yield return Enter("necro_road", "north");
            var p = Player.I;
            var map = Map.Current;
            foreach (var e in Enemy.All.ToArray()) if (e && !(e is Debt)) Object.Destroy(e.gameObject);
            var debt = Enemy.All.OfType<Debt>().FirstOrDefault();
            var plate = map.Find("nr_weigh");
            var bars = map.Find("nr_vault");
            var chest = map.Find("nr_assessor");
            Check("the road of the dead has its Debt, the assessor's vault, and the plate before the vault", debt && plate && bars && chest && bars.solid != null);
            if (!debt || !plate || !bars || !chest) yield break;
            p.coins = 30;
            // it follows
            Vector2 here = debt.pos + new Vector2(4.0f, 0);
            float d0 = Vector2.Distance(debt.pos, here);
            yield return Stand(here, Facing.Up, 1.6f);
            Check($"it follows him ({d0:0.0} -> {Vector2.Distance(debt.pos, here):0.0} tiles)", Vector2.Distance(debt.pos, here) < d0 - 1f);
            yield return Stand(here, Facing.Up, 8f, () => debt.Billing);
            Check("near enough, it stops and holds out the sum", debt.Billing);
            int price0 = debt.Price;
            yield return t.Shot("g0-the-sum", 0.2f);
            // he does not pay: it adds that on, and brings the tablet down
            int hp0 = p.health.hp;
            yield return Stand(here, Facing.Up, 6f, () => p.health.hp < hp0);
            yield return Quiet(0.6f);
            Check($"not paid, it brings the tablet down on him ({hp0} -> {p.health.hp}) and the sum goes up ({price0} -> {debt.Price})", p.health.hp == hp0 - 1 && debt.Price > price0);
            p.health.hp = p.health.max;
            // broken, it is a heap, and then a taller Debt
            for (float w = 0, next = 0; w < 6f && debt && !debt.InPieces; )
            {
                if (Story.I && Story.I.Running) { yield return null; continue; }
                if (w >= next && (p.state == Player.State.Free || p.state == Player.State.Attack))
                {
                    p.pos = debt.pos + new Vector2(0, -1.0f); p.Face(Facing.Up);
                    Controls.FakePress = Controls.Attack; next = w + 0.34f;
                }
                w += Time.deltaTime;
                yield return null;
            }
            Check("cut down, it is a heap of tablets", debt && debt.InPieces);
            yield return t.Shot("g1-in-pieces", 0.3f);
            p.pos = debt.pos + new Vector2(3f, -1f);
            for (float w = 0; w < 5f && debt && debt.InPieces; w += Time.deltaTime) yield return null;
            Check($"...and then a Debt again, a tablet taller (level {(debt ? debt.level : 0)}), and dearer ({price0} -> {(debt ? debt.Price : 0)})",
                  debt && !debt.InPieces && debt.level == 2 && debt.Price > price0 + 10);
            // weighed: the plate that does not notice a man notices this
            p.pos = plate.basePos;
            yield return new WaitForSeconds(0.4f);
            Check("the plate before the vault does not notice a man", !plate.lit && bars.solid != null);
            p.pos = plate.basePos + new Vector2(0, -3f);
            debt.pos = plate.basePos + new Vector2(0, 0.1f);
            yield return null; yield return null;
            for (float w = 0; w < 3f && bars.solid != null; w += Time.deltaTime) yield return null;
            Check("it notices a Debt: the plate goes down, and the vault's grille lifts", plate.lit && Story.Has("on_nr_weigh") && bars.solid == null);
            yield return Quiet(0.4f);
            // what was set aside against it
            int coins = p.coins;
            debt.pos = Map.ToWorld(434, 196);                          // (out of the way while he is in the vault)
            Vector2 atChest = chest.basePos + new Vector2(0, -0.85f);
            p.pos = atChest; p.Face(Facing.Up);
            yield return null;
            p.pos = atChest; p.Face(Facing.Up);
            Controls.FakePress = Controls.Interact;
            yield return Quiet(1.2f);
            Check($"in the vault, what was set aside against it ({coins} -> {p.coins} shekels)", p.coins == coins + 120);
            // paid
            p.SetState(Player.State.Free, "idle");
            Vector2 pay = plate.basePos + new Vector2(0, -2.5f);
            debt.pos = pay + new Vector2(0, 1.25f);
            int price = debt.Price;
            coins = p.coins;
            DialogueBox.Answers.Enqueue(0);
            p.pos = pay; p.Face(Facing.Up);
            yield return null;
            p.pos = pay; p.Face(Facing.Up);
            Controls.FakePress = Controls.Interact;
            yield return new WaitForSeconds(0.3f);
            yield return Quiet(0.5f);
            Check($"asked, and paid ({coins} - {price} = {p.coins}): the debt is settled", Story.Has("debt_paid") && p.coins == coins - price);
            for (float w = 0; w < 4f && debt; w += Time.deltaTime) yield return null;
            yield return Quiet(0.3f);
            Check("it lies down where it was paid, and stays there", !debt && Npc.All.Any(n => n && n.id == "debt_pile") && Story.Has("dead_nr_debt"));
            p.pos = pay + new Vector2(1.6f, 0.2f); p.Face(Facing.Left);
            yield return t.Shot("g2-paid-in-full", 0.4f);
            // and it is still lying there when he comes back
            yield return Enter("necro_road", "north");
            Check("it is still lying there when he comes back, and nothing follows him", Npc.All.Any(n => n && n.id == "debt_pile") && !Enemy.All.OfType<Debt>().Any());
        }
    }
}
