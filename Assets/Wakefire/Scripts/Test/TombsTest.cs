// The houses of the dead:  -wfScene tombs  goes in at the sweeper's and the shepherd's, climbs the steps of the
// stepped tomb and goes down its roof hatch, finds the door of the two vaults held shut and walks in at it asleep
// (the dead do not dream: there is nobody behind it), wakes among them and draws the bolt; on the hill goes in at
// the rich man's, strikes the gong at the door of the man who knocks, crawls the robbers' hole to the house whose
// owner is out and lifts its bar from inside, lights the fire bowl at the night watchman's door, and goes in at
// the scribe's.
using System.Collections;
using System.Linq;
using UnityEngine;

namespace Wakefire
{
    public static partial class HousesTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void RegisterTombs() => AutoTest.Scenes["tombs"] = RunTombs;

        static IEnumerator RunTombs(AutoTest t)
        {
            int bad = 0;
            void Check(string what, bool ok) { t.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
            DialogueBox.AutoAdvance = 0.1f;
            Save.ClearAll(); Save.Use(0);
            Game.I.Begin(false);
            Story.Abort();
            Story.GiveKit();
            var p = Player.I;
            bool In(string map, string room) => Game.I.CurrentMap == map && Room == room;
            bool Road() => Game.I.CurrentMap == "necro_road";
            bool Hill() => Game.I.CurrentMap == "necropolis";
            const string RI = "necro_road_in", HI = "necropolis_in";
            bool rode;
            int coins;

            // ================================================================== the road of the dead
            yield return Enter("necro_road", "south");
            Away();
            yield return Put(200, 676, Facing.Up);
            yield return t.Shot("a0-the-sweepers", 0.4f);
            yield return Put(430, 680, Facing.Up);
            yield return t.Shot("a1-the-shepherds", 0.4f);
            yield return Put(470, 520, Facing.Up);
            yield return t.Shot("a2-the-stepped-tomb", 0.4f);
            yield return Put(240, 196, Facing.Up);
            yield return t.Shot("a3-the-two-vaults", 0.4f);

            // ---- the sweeper's
            yield return Put(114, 664, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Road());
            yield return Scene(0.5f);
            Check($"in at the sweeper's door: {Game.I.CurrentMap} / {Room}", In(RI, "nr_sweep"));
            Check("she is in, and at it", Has("t_sweeper"));
            yield return t.Shot("b0-swept", 0.4f);
            var amat = Npc.All.FirstOrDefault(n => n && n.id == "t_sweeper");
            if (amat) { yield return Stand("nr_sweep", 222, 136, Facing.Right); yield return Act(); yield return Scene(0.5f); }
            Check("she has something to say about feet", Story.Count("t_sweeper") == 1);
            yield return Stand("nr_sweep", 208, 196, Facing.Down);
            yield return Walk(Vector2.down, 2.5f, Road);
            yield return Scene(0.5f);
            Check($"and out again: {Game.I.CurrentSpawn}", Road() && Game.I.CurrentSpawn == "nr_sweeper");

            // ---- the shepherd's
            yield return Put(484, 668, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Road());
            yield return Scene(0.5f);
            Check($"in at the shepherd's: {Room}", In(RI, "nr_sheep") && Has("t_shepherd"));
            yield return t.Shot("b1-nine-thousand-and-eight", 0.4f);
            yield return Stand("nr_sheep", 300, 160, Facing.Up);
            coins = p.coins;
            yield return Act();
            yield return Scene(1.5f);
            Check($"what he kept under the count ({coins} -> {p.coins})", p.coins == coins + 25);

            // ---- the stepped tomb: the door is brick, the steps go up, the hatch goes down
            yield return Enter("necro_road", "nr_proud");
            Away();
            yield return Put(486, 510, Facing.Up);
            yield return Walk(Vector2.up, 1.0f, () => !Road());
            Check("the stepped tomb's door is bricked up", Road());
            yield return Put(552, 506, Facing.Left);
            rode = false;
            yield return Walk(Vector2.left, 4f, () => { rode |= p.OnRail; return rode && !p.OnRail; }, 0.4f);
            Check($"up the steps on the front of it, on to the first tier: {Px}", rode && Px.y < 488);
            yield return t.Shot("c0-on-the-stepped-tomb", 0.3f);
            yield return Put(527, 452, Facing.Up);
            yield return Walk(Vector2.up, 2f, () => !Road());
            yield return Scene(0.5f);
            Check($"down the hatch: {Room} at {Game.I.CurrentSpawn}", In(RI, "nr_high") && Game.I.CurrentSpawn == "nr_proud_up");
            Check("he is in, and standing on something", Has("t_proud"));
            yield return t.Shot("c1-a-little-higher-up", 0.4f);
            yield return Stand("nr_high", 284, 160, Facing.Up);
            coins = p.coins;
            yield return Act();
            yield return Scene(1.5f);
            Check($"what he had put there to be thanked for ({coins} -> {p.coins})", p.coins == coins + 40);
            yield return Stand("nr_high", 208, 110, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, Road);
            yield return Scene(0.5f);
            Check($"and up on to the roof again: {Game.I.CurrentSpawn}, {Px}", Road() && Game.I.CurrentSpawn == "nr_proud_roof" && Px.y < 480);

            // ---- the two vaults: held shut awake, nobody behind it asleep
            yield return Enter("necro_road", "nr_couple");
            Away();
            yield return Put(180, 180, Facing.Up);
            yield return Walk(Vector2.up, 1.0f, () => !Road());
            Check("the door of the two vaults is held shut", Road());
            Story.Abort();
            Controls.FakePress = Controls.Interact;
            yield return new WaitForSeconds(0.15f);
            Check("it says who is holding it", Story.I.Running);
            yield return Scene(0.5f);
            Wakefire.Dream.I.Drowsiness = 1; Wakefire.Dream.I.Seconds = 9999; Wakefire.Dream.I.Flip(p.pos, true);
            yield return new WaitForSeconds(1.2f);
            yield return Put(180, 180, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Road());
            yield return Scene(0.5f);
            Check($"asleep, there is nobody behind it, and he walks in: {Room}", In(RI, "nr_both"));
            yield return t.Shot("d0-nobody-home-in-the-dream", 0.4f);
            Wakefire.Dream.I.Flip(p.pos, false);
            yield return new WaitForSeconds(1.2f);
            Wakefire.Dream.I.SetInstant(false); Story.I.ApplyItems(); Wakefire.Dream.I.Drowsiness = 1;
            Check("awake, they are both there", Has("t_wife") && Has("t_husband"));
            yield return t.Shot("d1-the-left-hand-side", 0.4f);
            yield return Stand("nr_both", 208, 196, Facing.Down);
            yield return Act();
            yield return Scene(0.6f);
            Check("the bolt is drawn from inside", Story.Has("on_nr_couple_latch"));
            yield return Walk(Vector2.down, 2.5f, Road);
            yield return Scene(0.5f);
            Check($"and he walks out at their door: {Game.I.CurrentSpawn}", Road() && Game.I.CurrentSpawn == "nr_couple");
            yield return Put(180, 180, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Road());
            yield return Scene(0.5f);
            Check($"which now lets him in awake: {Room}", In(RI, "nr_both"));

            // ================================================================== the hill
            yield return Enter("necropolis", "south");
            Away();
            yield return Put(250, 410, Facing.Up);
            yield return t.Shot("e0-the-rich-mans", 0.4f);
            yield return Put(190, 566, Facing.Up);
            yield return t.Shot("e1-the-man-who-knocks-and-next-door", 0.4f);
            yield return Put(470, 400, Facing.Up);
            yield return t.Shot("e2-the-watchmans", 0.4f);
            yield return Put(520, 626, Facing.Up);
            yield return t.Shot("e3-the-scribes", 0.4f);

            // ---- the rich man's
            yield return Put(200, 406, Facing.Up);
            yield return Walk(Vector2.up, 3f, () => !Hill());
            yield return Scene(0.5f);
            Check($"in at the rich man's: {Room}", In(HI, "np_feast") && Has("t_rich"));
            yield return t.Shot("f0-laid-for-twelve", 0.4f);
            yield return Stand("np_feast", 330, 158, Facing.Up);
            coins = p.coins;
            yield return Act();
            yield return Scene(1.5f);
            Check($"the chest is for people who actually come ({coins} -> {p.coins})", p.coins == coins + 60);

            // ---- the man who knocks: the gong, the door, the hole in his floor
            yield return Enter("necropolis", "np_knocker");
            Away();
            yield return Put(123, 532, Facing.Up);
            yield return Walk(Vector2.up, 1.0f, () => !Hill());
            Check("the knocker's door is shut", Hill());
            yield return Put(152, 540, Facing.Up);
            Controls.FakePress = Controls.Attack;
            yield return new WaitForSeconds(0.6f);
            yield return Scene(0.6f);
            Check("his gong, struck, opens it", Story.Has("on_np_knocker_gong"));
            yield return Put(123, 532, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Hill());
            yield return Scene(0.5f);
            Check($"in at his door: {Room}", In(HI, "np_knock") && Has("t_knocker"));
            yield return t.Shot("g0-is-anybody-there", 0.4f);
            yield return Stand("np_knock", 136, 166, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => In(HI, "np_five"));
            yield return Scene(1.0f);
            Check($"down the robbers' hole, and up next door: {Room}", In(HI, "np_five"));
            yield return t.Shot("g1-back-in-five-minutes", 0.4f);
            yield return Stand("np_five", 268, 164, Facing.Up);
            int vessels = Story.Count("vessels");
            yield return Act();
            yield return Scene(2.5f);
            Check($"what she left behind ({vessels} -> {Story.Count("vessels")} flame vessels)", Story.Count("vessels") == vessels + 1);
            yield return Stand("np_five", 208, 196, Facing.Down);
            yield return Act();
            yield return Scene(0.6f);
            Check("the bar comes off her door, from inside", Story.Has("on_np_five_latch"));
            yield return Walk(Vector2.down, 2.5f, Hill);
            yield return Scene(0.5f);
            Check($"and he walks out past BACK IN FIVE MINUTES: {Game.I.CurrentSpawn}", Hill() && Game.I.CurrentSpawn == "np_five");

            // ---- the night watchman's: the fire bowl, the door
            yield return Put(484, 384, Facing.Up);
            yield return Walk(Vector2.up, 1.0f, () => !Hill());
            Check("the watchman's door is shut", Hill());
            yield return Put(516, 395, Facing.Up);
            Controls.FakePress = Controls.Item;
            yield return new WaitForSeconds(0.9f);
            yield return Scene(0.8f);
            Check("the fire bowl takes the Wakefire, and the door answers", Story.Has("on_np_pillow_sign"));
            yield return t.Shot("h0-fire-at-the-door", 0.3f);
            yield return Put(484, 384, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Hill());
            yield return Scene(0.5f);
            Check($"in at his door: {Room}", In(HI, "np_pill") && Has("t_watchman"));
            yield return t.Shot("h1-three-hundred-years-owed", 0.4f);
            yield return Stand("np_pill", 268, 160, Facing.Up);
            coins = p.coins;
            yield return Act();
            yield return Scene(1.5f);
            Check($"a watchman's savings ({coins} -> {p.coins})", p.coins == coins + 30);

            // ---- the scribe's
            yield return Enter("necropolis", "np_reader");
            Away();
            yield return Put(566, 622, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Hill());
            yield return Scene(0.5f);
            Check($"in at the scribe's: {Room}", In(HI, "np_read") && Has("t_scribe") && Has("t_listener"));
            yield return t.Shot("i0-tablet-nine-of-sixty", 0.4f);
            t.Note(bad == 0 ? "TOMBS OK" : $"FAILED {bad}");
        }
    }
}
