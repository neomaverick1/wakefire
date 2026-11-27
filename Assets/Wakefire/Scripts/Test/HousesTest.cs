// The houses of the Lower Town:  -wfScene houses  goes in at every door that opens, up every stair
// and ladder, on to the roofs and off them, in by the roof where a street door is shut, rings the
// counting house's gong, lifts the bar off the goat's door, takes the key the goat keeps to the
// strongroom, comes up under the Seven Jars by the cellar door and by the cave on the cliffs,
// brings down the potter's wall, and walks through the oracle's dream door.
using System.Collections;
using System.Linq;
using UnityEngine;

namespace Wakefire
{
    public static partial class HousesTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["houses"] = Run;

        static Vector2 InRoom(string id, float x, float y)
        {
            var r = Rooms.I ? Rooms.I.Find(id) : null;
            if (r == null) return Player.I.pos;                     // (not where the test thought it was: what follows will say so)
            return new Vector2(r.rect.xMin + x / 16f, r.rect.yMax - y / 16f);
        }

        static IEnumerator Scene(float atLeast = 0.4f, float atMost = 60f)
        {
            float w = 0;
            while ((w < atLeast || (Story.I && Story.I.Running) || Game.Busy || Rooms.Sliding) && w < atMost) { w += Time.deltaTime; yield return null; }
        }

        /// <summary>Put him at a point of the map (its own pixels) and let the picture catch up.</summary>
        static IEnumerator Put(float x, float y, Facing face)
        {
            var p = Player.I;
            var at = Map.ToWorld(x, y);
            p.DropRail();
            p.pos = at;
            p.transform.position = new Vector3(at.x, at.y, 0);
            if (Rooms.I) Rooms.I.Jump(at);
            PixelView.I.SnapTo(at);
            p.Face(face);
            p.SetState(Player.State.Free, "idle");
            yield return Scene(0.25f);
            p.pos = at;
            p.Face(face);
            p.health.hp = p.health.max;
            yield return new WaitForSeconds(0.1f);
        }

        static IEnumerator Stand(string room, float x, float y, Facing face)
        {
            var at = InRoom(room, x, y);
            yield return Put(at.x * 16f, -at.y * 16f, face);
        }

        static IEnumerator Walk(Vector2 dir, float seconds, System.Func<bool> until = null, float settle = 0.3f)
        {
            var p = Player.I;
            for (float w = 0; w < seconds; w += Time.deltaTime)
            {
                Controls.Fake = p.state == Player.State.Free || p.state == Player.State.Rail ? dir : Vector2.zero;
                if (until != null && until()) break;
                yield return null;
            }
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(settle);
        }

        static IEnumerator Enter(string map, string spawn)
        {
            Game.I.EnterMap(map, spawn);
            Story.Abort();
            Fade.Set(0);
            Player.I.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.5f);
            yield return Scene(0.2f);
        }

        static IEnumerator Act()
        {
            Controls.FakePress = Controls.Interact;
            yield return new WaitForSeconds(0.2f);
            yield return Scene(0.3f);
        }

        static IEnumerator ThreeCuts()
        {
            for (int i = 0; i < 3; i++)
            {
                Controls.FakePress = Controls.Attack;
                yield return new WaitForSeconds(0.3f);
            }
            yield return new WaitForSeconds(0.7f);
        }

        static void Away()
        {
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
        }

        static string Room => Rooms.I && Rooms.I.current != null ? Rooms.I.current.id : "(none)";
        static Vector2 Px => new Vector2(Player.I.pos.x * 16f, -Player.I.pos.y * 16f);
        static bool Has(string id) => Npc.All.Any(n => n && n.id == id);

        static IEnumerator Run(AutoTest t)
        {
            int bad = 0;
            void Check(string what, bool ok) { t.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
            DialogueBox.AutoAdvance = 0.1f;
            Save.ClearAll(); Save.Use(0);
            Game.I.Begin(false);
            Story.Abort();
            Story.GiveKit();
            var p = Player.I;
            yield return Enter("lowtown", "north");
            Away();
            bool In(string room) => Game.I.CurrentMap == "lowtown_in" && Room == room;
            bool Town() => Game.I.CurrentMap == "lowtown";

            // ------------------------------------------------------------------ the town from the street
            yield return Put(480, 424, Facing.Down);
            yield return t.Shot("a0-the-crossing", 0.4f);
            yield return Put(336, 420, Facing.Up);
            yield return t.Shot("a1-weavers-and-jars", 0.4f);
            yield return Put(632, 196, Facing.Up);
            yield return t.Shot("a2-the-well-court", 0.4f);
            yield return Put(852, 204, Facing.Up);
            yield return t.Shot("a3-the-oracles", 0.4f);
            yield return Put(250, 640, Facing.Up);
            yield return t.Shot("a4-the-bakery-yard", 0.4f);
            yield return Put(660, 640, Facing.Up);
            yield return t.Shot("a5-the-pottery-yard", 0.4f);

            // ------------------------------------------------------------------ the bakery: door, stairs, roof, the way down
            yield return Put(181, 620, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Town());
            yield return Scene(0.5f);
            Check($"in at the bakery's door: {Game.I.CurrentMap} / {Room}", In("bk_shop"));
            Check("Urbau is at his counter", Has("urbau"));
            yield return t.Shot("b0-the-bakery", 0.4f);
            // the flour bin, shoved aside, and what is under it
            yield return Stand("bk_shop", 276, 157, Facing.Left);
            yield return Walk(Vector2.left, 1.6f);
            yield return Stand("bk_shop", 256, 159, Facing.Up);
            yield return Walk(Vector2.up, 1.5f, () => In("bk_cellar"));
            yield return Scene(0.5f);
            Check($"under the flour bin, a stair down to the cellar: {Room}", In("bk_cellar"));
            yield return t.Shot("b0b-the-flour-cellar", 0.4f);
            yield return Stand("bk_cellar", 208, 110, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => In("bk_shop"));
            yield return Scene(0.5f);
            Check($"and back up it: {Room} at {Game.I.CurrentSpawn}", In("bk_shop") && Game.I.CurrentSpawn == "bk_shop_dn");
            yield return Stand("bk_shop", 208, 110, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => In("bk_bed"));
            yield return Scene(0.5f);
            Check($"up the stairs to the room over the shop: {Room} at {Game.I.CurrentSpawn}", In("bk_bed") && Game.I.CurrentSpawn == "bk_bed_dn");
            Check("somebody is in the bed, and something is on the other one", Has("granny") && Has("cat_bed"));
            yield return t.Shot("b1-over-the-shop", 0.4f);
            yield return Stand("bk_bed", 208, 196, Facing.Down);
            yield return Walk(Vector2.down, 2.5f, Town);
            yield return Scene(0.5f);
            Check($"out of its door on to the roof: {Game.I.CurrentMap} at {Game.I.CurrentSpawn}, {Px}", Town() && Game.I.CurrentSpawn == "lt_bakery_roof" && Px.y < 560);
            yield return t.Shot("b2-on-the-bakery-roof", 0.4f);
            // across the roof and off the front of it
            yield return Put(170, 548, Facing.Down);
            yield return Walk(Vector2.down, 3f, () => Px.y > 606 && p.state == Player.State.Free, 0.5f);
            Check($"leaning on the edge of the roof, he comes down in the street: {Px}", Px.y > 606 && Px.y < 640);
            // up the stair along the front
            yield return Put(184, 613, Facing.Right);
            bool rode = false;
            yield return Walk(Vector2.right, 4f, () => { rode |= p.OnRail; return rode && !p.OnRail; }, 0.4f);
            Check($"up the stair along the front of the house, on to the roof: {Px}", rode && Px.y < 566 && Px.x > 215);
            yield return t.Shot("b3-up-the-stair", 0.3f);
            rode = false;
            yield return Walk(Vector2.left, 4f, () => { rode |= p.OnRail; return rode && !p.OnRail; }, 0.4f);
            Check($"and back down it to the street: {Px}", rode && Px.y > 606);

            // ------------------------------------------------------------------ the goat's house: ladder, hatch, key, bar
            yield return Put(386, 191, Facing.Up);
            rode = false;
            yield return Walk(Vector2.up, 4f, () => { rode |= p.OnRail; return rode && !p.OnRail; }, 0.4f);
            Check($"up the ladder on to the goat's roof: {Px}", rode && Px.y < 136);
            Check("the goat is up there", Has("goat_roof"));
            yield return t.Shot("c0-the-goats-roof", 0.3f);
            yield return Put(373, 118, Facing.Up);
            yield return Walk(Vector2.up, 2f, () => !Town());
            yield return Scene(0.5f);
            Check($"down the hatch into the house: {Room}", In("goat_room"));
            yield return t.Shot("c1-the-goats-house", 0.4f);
            yield return Stand("goat_room", 264, 158, Facing.Up);
            int keys = p.keys;
            yield return Act();
            yield return Scene(1.5f);
            Check($"the goat keeps a key ({keys} -> {p.keys})", p.keys == keys + 1);
            yield return Stand("goat_room", 208, 196, Facing.Down);
            yield return Act();
            yield return Scene(0.6f);
            Check("the bar comes off the door", Story.Has("on_lt_goat_latch"));
            yield return Stand("goat_room", 208, 196, Facing.Down);
            yield return Walk(Vector2.down, 2.5f, Town);
            yield return Scene(0.5f);
            Check($"and he walks out of it into the street: {Game.I.CurrentSpawn}", Town() && Game.I.CurrentSpawn == "lt_goat");
            var leaf = Map.Current.props.FirstOrDefault(q => q && q.data.id == "lt_goat_door");
            Check("the door stands open behind him", leaf && !leaf.sr.enabled);

            // ------------------------------------------------------------------ the counting house: gong, door, lock, strongroom
            yield return Put(588, 396, Facing.Up);
            yield return Walk(Vector2.up, 1.0f, () => !Town());
            Check("the counting house is shut", Town());
            yield return Put(552, 402, Facing.Up);
            Controls.FakePress = Controls.Attack;
            yield return new WaitForSeconds(0.6f);
            yield return Scene(0.6f);
            Check("its gong, struck, opens it", Story.Has("on_lt_tax_gong"));
            yield return t.Shot("d0-the-gong", 0.2f);
            yield return Put(588, 398, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Town());
            yield return Scene(0.5f);
            Check($"in at its door: {Room}", In("tax_office"));
            Check("the clerk is in", Has("clerk"));
            yield return t.Shot("d1-the-counting-house", 0.4f);
            yield return Stand("tax_office", 384, 130, Facing.Right);
            keys = p.keys;
            yield return Walk(Vector2.right, 1.2f, () => In("tax_vault"));
            Check("the way into the strongroom is locked", In("tax_office"));
            yield return Act();
            yield return Scene(0.5f);
            Check($"the goat's key opens it ({keys} -> {p.keys})", p.keys == keys - 1);
            yield return Walk(Vector2.right, 4f, () => In("tax_vault"));
            yield return Scene(0.8f);
            Check($"into the strongroom: {Room}", In("tax_vault"));
            yield return t.Shot("d2-the-strongroom", 0.4f);

            // ------------------------------------------------------------------ the Seven Jars, and under it by two ways
            yield return Enter("lowtown", "lt_beer");
            Away();
            yield return Put(138, 398, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Town());
            yield return Scene(0.5f);
            Check($"in at the Seven Jars: {Room}", In("beer_hall"));
            Check("the alewife, two regulars and a dog", Has("alewife") && Has("drinker_a") && Has("drinker_b") && Has("dog_beer"));
            yield return t.Shot("e0-the-seven-jars", 0.4f);
            Check("the board behind the counter is bolted from underneath", !Story.Has("open_beer_hatch"));
            // its stair, at the west end, and who is on the roof
            yield return Enter("lowtown", "lt_beer");
            Away();
            yield return Put(97, 389, Facing.Left);
            rode = false;
            yield return Walk(Vector2.left, 4f, () => { rode |= p.OnRail; return rode && !p.OnRail; }, 0.4f);
            Check($"up the stair at the end of the Seven Jars, on to the roof they drink on: {Px}", rode && Px.y < 344);
            Check("somebody is still up there", Has("roof_drinker"));
            yield return t.Shot("e0b-the-roof-of-the-seven-jars", 0.3f);
            yield return Put(60, 310, Facing.Left);
            yield return Walk(Vector2.left, 3f, () => Px.x < 34 && p.state == Player.State.Free, 0.5f);
            Check($"and off the end of it into the yard: {Px}", Px.x < 34 && Px.y > 330);
            yield return Enter("lowtown", "lt_beer_cellar");
            Away();
            yield return Put(240, 342, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Town());
            yield return Scene(0.5f);
            Check($"down the cellar door in the alley: {Room}", In("beer_cellar"));
            Check($"something got here first ({Enemy.All.Count(e => e)})", Enemy.All.Count(e => e) == 2);
            yield return t.Shot("e1-under-the-seven-jars", 0.4f);
            Away();
            yield return Stand("beer_cellar", 208, 110, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => In("beer_hall"));
            yield return Scene(1.0f);
            Check($"up its stair, and the board lifts: {Room} at {Game.I.CurrentSpawn}", In("beer_hall") && Story.Has("open_beer_hatch"));
            yield return Enter("cliffs", "west");
            Away();
            yield return Put(120, 426, Facing.Up);
            yield return t.Shot("e2-the-cave-on-the-cliffs", 0.3f);
            yield return Walk(Vector2.up, 2.5f, () => Game.I.CurrentMap != "cliffs");
            yield return Scene(0.5f);
            Check($"in at the cave on the cliffs, out under the Seven Jars: {Game.I.CurrentMap} / {Room}", In("beer_cellar") && Game.I.CurrentSpawn == "beer_cave_in");
            Away();
            yield return Stand("beer_cellar", 276, 62, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => Game.I.CurrentMap == "cliffs");
            yield return Scene(0.5f);
            Check($"and back the same way: {Game.I.CurrentMap} at {Game.I.CurrentSpawn}", Game.I.CurrentMap == "cliffs" && Game.I.CurrentSpawn == "beer_cave");

            // ------------------------------------------------------------------ the pottery: the wall, the cash room, the roof
            yield return Enter("lowtown", "lt_pottery");
            Away();
            yield return Put(723, 620, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Town());
            yield return Scene(0.5f);
            Check($"in at the pottery: {Room}", In("pt_shop"));
            yield return t.Shot("f0-the-pottery", 0.4f);
            yield return Stand("pt_shop", 384, 130, Facing.Right);
            yield return new WaitForSeconds(0.3f);
            yield return ThreeCuts();
            yield return Scene(0.6f);
            Check("his wall comes down to the heavy chop", Story.Has("door_pt_crack"));
            yield return Walk(Vector2.right, 4f, () => In("pt_cash"));
            yield return Scene(1.0f);
            Check($"into the cash room: {Room}", In("pt_cash"));
            yield return t.Shot("f1-the-cash-room", 0.4f);
            yield return Stand("pt_cash", 208, 110, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, Town);
            yield return Scene(0.5f);
            Check($"up its stair and out of the hatch in the roof: {Game.I.CurrentSpawn}, {Px}", Town() && Game.I.CurrentSpawn == "lt_pottery_roof" && Px.y < 572);
            yield return t.Shot("f2-on-the-pottery-roof", 0.3f);
            yield return Put(602, 564, Facing.Down);
            rode = false;
            yield return Walk(Vector2.down, 4f, () => { rode |= p.OnRail; return rode && !p.OnRail; }, 0.4f);
            Check($"down the ladder to the yard: {Px}", rode && Px.y > 608);

            // ------------------------------------------------------------------ the weavers': shut door, ladder, the hut on the roof
            yield return Put(290, 394, Facing.Up);
            Story.Abort();
            Controls.FakePress = Controls.Interact;
            yield return new WaitForSeconds(0.15f);
            Check("their street door says why it is shut", Story.I.Running);
            yield return Scene(0.5f);
            yield return Put(402, 399, Facing.Up);
            rode = false;
            yield return Walk(Vector2.up, 4f, () => { rode |= p.OnRail; return rode && !p.OnRail; }, 0.4f);
            Check($"up the ladder at the end of their house: {Px}", rode && Px.y < 340);
            yield return t.Shot("g0-the-weavers-roof", 0.3f);
            yield return Put(393, 314, Facing.Up);
            yield return Walk(Vector2.up, 2f, () => !Town());
            yield return Scene(0.5f);
            Check($"in at the hut on the roof: {Room}", In("wv_upper"));
            yield return t.Shot("g1-the-sisters-room", 0.4f);
            yield return Stand("wv_upper", 160, 167, Facing.Up);
            yield return Walk(Vector2.up, 2f, () => In("wv_work"));
            yield return Scene(0.5f);
            Check($"down to the looms: {Room}", In("wv_work") && Has("sister_a") && Has("sister_b"));
            yield return t.Shot("g2-the-weavers", 0.4f);

            // ------------------------------------------------------------------ the oracle's, and the door only a dreamer has
            yield return Enter("lowtown", "lt_oracle");
            Away();
            yield return Put(852, 190, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Town());
            yield return Scene(0.5f);
            Check($"in at Ummi's: {Room}", In("or_room") && Has("client"));
            yield return t.Shot("h0-ummis", 0.4f);
            yield return Stand("or_room", 380, 130, Facing.Right);
            yield return Walk(Vector2.right, 1.5f, () => In("or_dream"));
            Check("awake, there is only wall", In("or_room"));
            Wakefire.Dream.I.Drowsiness = 1; Wakefire.Dream.I.Seconds = 9999; Wakefire.Dream.I.Flip(p.pos, true);
            yield return new WaitForSeconds(1.2f);
            yield return Stand("or_room", 380, 130, Facing.Right);
            yield return Walk(Vector2.right, 4f, () => In("or_dream"));
            yield return Scene(1.0f);
            Check($"dreaming, there is a door: {Room}", In("or_dream"));
            yield return t.Shot("h1-what-she-sees", 0.4f);
            Wakefire.Dream.I.Flip(p.pos, false);
            yield return new WaitForSeconds(1.2f);
            Wakefire.Dream.I.SetInstant(false); Story.I.ApplyItems(); Wakefire.Dream.I.Drowsiness = 1;

            // ------------------------------------------------------------------ the net loft
            yield return Enter("lowtown", "lt_netloft");
            Away();
            yield return Put(837, 656, Facing.Up);
            yield return Walk(Vector2.up, 2.5f, () => !Town());
            yield return Scene(0.5f);
            Check($"in at the net loft: {Room}", In("net_loft") && Has("oldfisher"));
            yield return t.Shot("i0-the-net-loft", 0.4f);
            t.Note(bad == 0 ? "HOUSES OK" : $"FAILED {bad}");
        }
    }
}
