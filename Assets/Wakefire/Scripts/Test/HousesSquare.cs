// The houses of the gate square:  -wfScene square  goes in at the watch house, up to its tower room and
// down to its lock-up, takes the cell keys off their peg, crawls the prisoner's tunnel into the cedar
// merchant's cellar, comes up into his hall, lifts the bar off his front door from inside, goes out on
// his roof and hops down; climbs the stair at the end of the watch house; lights the lamp seller's sign
// and goes in at the door it opens, and down to his oil cellar; climbs the tablet house's ladder, goes
// down its roof hatch into the room of confiscated things and out through the grille it unbolts; and
// walks through the door that Widow Ilta's house only has in the dream.
using System.Collections;
using System.Linq;
using UnityEngine;

namespace Wakefire
{
    public static partial class HousesTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void RegisterSquare() => AutoTest.Scenes["square"] = RunSquare;

        /// <summary>Where he stands in the room he is in, in the room's own pixels.</summary>
        static Vector2 Local
        {
            get
            {
                var r = Rooms.I ? Rooms.I.current : null;
                var p = Player.I.pos;
                return r == null ? Vector2.zero : new Vector2((p.x - r.rect.xMin) * 16f, (r.rect.yMax - p.y) * 16f);
            }
        }

        static IEnumerator RunSquare(AutoTest t)
        {
            int bad = 0;
            void Check(string what, bool ok) { t.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
            DialogueBox.AutoAdvance = 0.1f;
            Save.ClearAll(); Save.Use(0);
            Game.I.Begin(false);
            Story.Abort();
            Story.GiveKit();
            var p = Player.I;
            yield return Enter("ashkel", "south");
            Away();
            bool In(string room) => Game.I.CurrentMap == "ashkel_in" && Room == room;
            bool Square() => Game.I.CurrentMap == "ashkel";
            bool rode;

            // ------------------------------------------------------------------ the square from the street
            yield return Put(280, 232, Facing.Up);
            yield return t.Shot("a0-the-watch-house-and-its-yard", 0.4f);
            yield return Put(160, 456, Facing.Up);
            yield return t.Shot("a1-the-merchants", 0.4f);
            yield return Put(300, 420, Facing.Up);
            yield return t.Shot("a2-his-garden", 0.4f);
            yield return Put(700, 230, Facing.Up);
            yield return t.Shot("a3-the-market", 0.4f);
            yield return Put(860, 222, Facing.Up);
            yield return t.Shot("a4-the-lamp-sellers", 0.4f);
            yield return Put(700, 456, Facing.Up);
            yield return t.Shot("a5-the-tablet-house", 0.4f);
            yield return Put(840, 456, Facing.Up);
            yield return t.Shot("a6-widow-iltas", 0.4f);

            // ------------------------------------------------------------------ the watch house: door, tower, lock-up
            yield return Put(119, 206, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Square());
            yield return Scene(0.5f);
            Check($"in at the watch house's door: {Game.I.CurrentMap} / {Room}", In("wt_guard"));
            Check("the day watch is in: one at the board, one at attention, one in his bunk", Has("watch_a") && Has("watch_b") && Has("watch_c"));
            yield return t.Shot("b0-the-watch-house", 0.4f);
            yield return Stand("wt_guard", 208, 110, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => In("wt_tower"));
            yield return Scene(0.5f);
            Check($"up the stair to the tower room: {Room} at {Game.I.CurrentSpawn}", In("wt_tower") && Game.I.CurrentSpawn == "wt_tower_dn");
            yield return t.Shot("b1-the-tower-room", 0.4f);
            yield return Stand("wt_tower", 164, 158, Facing.Up);
            int coins = p.coins;
            yield return Act();
            yield return Scene(1.5f);
            Check($"the lookout kept something by ({coins} -> {p.coins})", p.coins == coins + 30);
            yield return Stand("wt_tower", 250, 156, Facing.Up);
            yield return Walk(Vector2.up, 2f, () => In("wt_guard"));
            yield return Scene(0.5f);
            Check($"and down again: {Room} at {Game.I.CurrentSpawn}", In("wt_guard") && Game.I.CurrentSpawn == "wt_guard_up");
            yield return Stand("wt_guard", 88, 106, Facing.Up);
            yield return Walk(Vector2.up, 2f, () => In("wt_lock"));
            yield return Scene(0.5f);
            Check($"down the stair in the floor to the lock-up: {Room} at {Game.I.CurrentSpawn}", In("wt_lock") && Game.I.CurrentSpawn == "wt_lock_in");
            Check("the prisoner is in", Has("prisoner"));
            yield return t.Shot("b2-the-lock-up", 0.4f);
            yield return Stand("wt_lock", 240, 120, Facing.Down);
            yield return Walk(Vector2.down, 1.0f);
            Check($"the cell is shut: {Local}", Local.y < 134);
            yield return Stand("wt_lock", 140, 57, Facing.Up);
            yield return Act();
            yield return Scene(0.8f);
            Check("the keys come off their peg", Story.Has("on_wt_keys"));
            yield return Stand("wt_lock", 240, 120, Facing.Down);
            yield return Walk(Vector2.down, 1.2f);
            Check($"and the cell door stands open: {Local}", Local.y > 140);
            yield return t.Shot("b3-in-the-cell", 0.3f);

            // ------------------------------------------------------------------ the tunnel, and the merchant's house from underneath
            yield return Stand("wt_lock", 284, 166, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => In("mh_cellar"));
            yield return Scene(1.0f);
            Check($"down the prisoner's hole, and up under Ilu-Bani's: {Room}", In("mh_cellar"));
            yield return t.Shot("c0-under-ilu-banis", 0.4f);
            yield return Stand("mh_cellar", 180, 148, Facing.Up);
            coins = p.coins;
            yield return Act();
            yield return Scene(1.5f);
            Check($"what the Temple paid twice for ({coins} -> {p.coins})", p.coins == coins + 80);
            yield return Stand("mh_cellar", 208, 110, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => In("mh_hall"));
            yield return Scene(0.5f);
            Check($"up the cellar stair into his hall: {Room} at {Game.I.CurrentSpawn}", In("mh_hall") && Game.I.CurrentSpawn == "mh_hall_dn");
            Check("Ilu-Bani, his servant and his hound", Has("ilubani") && Has("servant") && Has("hound"));
            yield return t.Shot("c1-ilu-banis-hall", 0.4f);
            yield return Stand("mh_hall", 208, 196, Facing.Down);
            yield return Act();
            yield return Scene(0.6f);
            Check("the bar comes off his front door, from inside", Story.Has("on_ak_merchant_latch"));
            yield return Stand("mh_hall", 208, 110, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => In("mh_upper"));
            yield return Scene(0.5f);
            Check($"up the stair to the rooms above: {Room} at {Game.I.CurrentSpawn}", In("mh_upper") && Game.I.CurrentSpawn == "mh_upper_dn");
            Check("his wife and two children, asleep", Has("wife") && Has("child_a") && Has("child_b"));
            yield return t.Shot("c2-the-rooms-above", 0.4f);
            yield return Stand("mh_upper", 116, 156, Facing.Up);
            int vessels = Story.Count("vessels");
            yield return Act();
            yield return Scene(2.5f);
            Check($"the good things are up here ({vessels} -> {Story.Count("vessels")} flame vessels)", Story.Count("vessels") == vessels + 1);
            yield return Stand("mh_upper", 208, 196, Facing.Down);
            yield return Walk(Vector2.down, 2.5f, Square);
            yield return Scene(0.5f);
            Check($"out of their door on to the roof: {Game.I.CurrentSpawn}, {Px}", Square() && Game.I.CurrentSpawn == "ak_merchant_roof" && Px.y < 382);
            yield return t.Shot("c3-on-ilu-banis-roof", 0.4f);
            yield return Put(56, 372, Facing.Down);
            yield return Walk(Vector2.down, 3f, () => Px.y > 432 && p.state == Player.State.Free, 0.5f);
            Check($"leaning on the edge of his roof, he comes down in front of the house: {Px}", Px.y > 432 && Px.y < 467);
            yield return Put(120, 452, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Square());
            yield return Scene(0.5f);
            Check($"and now the front door lets him in: {Room}", In("mh_hall"));

            // ------------------------------------------------------------------ the watch house's stair and roof
            yield return Enter("ashkel", "ak_watch");
            Away();
            yield return Put(112, 204, Facing.Right);
            rode = false;
            yield return Walk(Vector2.right, 4f, () => { rode |= p.OnRail; return rode && !p.OnRail; }, 0.4f);
            Check($"up the stair at the end of the watch house, on to its roof: {Px}", rode && Px.y < 160 && Px.x > 150);
            yield return t.Shot("d0-the-watch-house-roof", 0.3f);
            rode = false;
            yield return Walk(Vector2.left, 4f, () => { rode |= p.OnRail; return rode && !p.OnRail; }, 0.4f);
            Check($"and back down it: {Px}", rode && Px.y > 196);

            // ------------------------------------------------------------------ the lamp seller's: the sign, the door, the cellar
            yield return Put(910, 206, Facing.Up);
            yield return Walk(Vector2.up, 1.0f, () => !Square());
            Check("the lamp seller's is shut", Square());
            Story.Abort();
            Controls.FakePress = Controls.Interact;
            yield return new WaitForSeconds(0.15f);
            Check("its door says what opens it", Story.I.Running);
            yield return Scene(0.5f);
            yield return Put(934, 216, Facing.Up);
            Controls.FakePress = Controls.Item;
            yield return new WaitForSeconds(0.9f);
            yield return Scene(0.8f);
            Check("his sign takes the Wakefire, and the door answers", Story.Has("on_ak_lamps_sign"));
            yield return t.Shot("e0-the-sign-is-lit", 0.3f);
            yield return Put(910, 206, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Square());
            yield return Scene(0.5f);
            Check($"in at his door: {Room}", In("lp_shop") && Has("lampseller"));
            yield return t.Shot("e1-the-lamp-sellers", 0.4f);
            Away();
            yield return Stand("lp_shop", 180, 110, Facing.Up);
            yield return Walk(Vector2.up, 2f, () => In("lp_cellar"));
            yield return Scene(0.5f);
            Check($"down to the oil cellar: {Room} at {Game.I.CurrentSpawn}", In("lp_cellar") && Game.I.CurrentSpawn == "lp_cellar_in");
            yield return t.Shot("e2-the-oil-cellar", 0.4f);
            yield return Stand("lp_cellar", 208, 110, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => In("lp_shop"));
            yield return Scene(0.5f);
            Check($"and up again: {Room} at {Game.I.CurrentSpawn}", In("lp_shop") && Game.I.CurrentSpawn == "lp_shop_dn");

            // ------------------------------------------------------------------ the tablet house: door, ladder, roof hatch, the grille
            yield return Enter("ashkel", "ak_tablets");
            Away();
            yield return Put(686, 446, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Square());
            yield return Scene(0.5f);
            Check($"in at the tablet house: {Room}", In("tb_school"));
            Check("the master and three of his boys", Has("master") && Has("boy_a") && Has("boy_b") && Has("boy_c"));
            yield return t.Shot("f0-the-tablet-house", 0.4f);
            yield return Stand("tb_school", 384, 130, Facing.Right);
            yield return Walk(Vector2.right, 1.2f, () => In("tb_kept"));
            Check("the grille in its east wall is bolted from the far side", In("tb_school"));
            yield return Enter("ashkel", "ak_tablets");
            Away();
            yield return Put(717, 452, Facing.Up);
            rode = false;
            yield return Walk(Vector2.up, 4f, () => { rode |= p.OnRail; return rode && !p.OnRail; }, 0.4f);
            Check($"up the ladder on to the roof where the tablets dry: {Px}", rode && Px.y < 404);
            yield return t.Shot("f1-the-tablet-house-roof", 0.3f);
            yield return Put(707, 374, Facing.Up);
            yield return Walk(Vector2.up, 2f, () => !Square());
            yield return Scene(0.5f);
            Check($"down the hatch into the room of things taken away: {Room} at {Game.I.CurrentSpawn}", In("tb_kept") && Game.I.CurrentSpawn == "ak_tablets_up");
            yield return t.Shot("f2-things-taken-away", 0.4f);
            yield return Stand("tb_kept", 40, 89, Facing.Up);
            yield return Act();
            yield return Scene(0.8f);
            Check("the bolt comes back", Story.Has("on_tb_bolt"));
            yield return Stand("tb_kept", 30, 130, Facing.Left);
            yield return Walk(Vector2.left, 4f, () => In("tb_school"));
            yield return Scene(1.0f);
            Check($"and he walks out through the grille into the schoolroom: {Room}", In("tb_school"));

            // ------------------------------------------------------------------ Widow Ilta's: door, ladder, the room her dream has
            yield return Enter("ashkel", "ak_ilta");
            Away();
            yield return Put(906, 452, Facing.Up);
            rode = false;
            yield return Walk(Vector2.up, 4f, () => { rode |= p.OnRail; return rode && !p.OnRail; }, 0.4f);
            Check($"up her ladder to the bed on the roof: {Px}", rode && Px.y < 404);
            Check("the cat has it", Has("cat_roof"));
            yield return t.Shot("g0-iltas-roof", 0.3f);
            yield return Put(852, 446, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Square());
            yield return Scene(0.5f);
            Check($"in at her door: {Room}", In("il_room"));
            yield return t.Shot("g1-widow-iltas", 0.4f);
            yield return Stand("il_room", 380, 130, Facing.Right);
            yield return Walk(Vector2.right, 1.5f, () => In("il_dream"));
            Check("awake, there is only wall", In("il_room"));
            Wakefire.Dream.I.Drowsiness = 1; Wakefire.Dream.I.Seconds = 9999; Wakefire.Dream.I.Flip(p.pos, true);
            yield return new WaitForSeconds(1.2f);
            yield return Stand("il_room", 380, 130, Facing.Right);
            yield return Walk(Vector2.right, 4f, () => In("il_dream"));
            yield return Scene(1.0f);
            Check($"dreaming, there is a door, and a table laid for two: {Room}", In("il_dream"));
            yield return t.Shot("g2-the-table-she-keeps", 0.4f);
            Wakefire.Dream.I.Flip(p.pos, false);
            yield return new WaitForSeconds(1.2f);
            Wakefire.Dream.I.SetInstant(false); Story.I.ApplyItems(); Wakefire.Dream.I.Drowsiness = 1;
            t.Note(bad == 0 ? "SQUARE OK" : $"FAILED {bad}");
        }
    }
}
