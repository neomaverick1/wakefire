// Rooms of a dungeon floor: -wfScene rooms walks Azar through the doorways of the ziggurat's first
// floor and checks that the picture slides to the next room, that each room has its own enemies,
// and that bars, locked doors and their twins on the far side open together.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class RoomsTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["rooms"] = Run;

        static Vector2 InRoom(string id, float x, float y)
        {
            var r = Rooms.I.Find(id);
            return new Vector2(r.rect.xMin + x / 16f, r.rect.yMax - y / 16f);
        }

        static IEnumerator Walk(Vector2 dir, float seconds)
        {
            Controls.Fake = dir;
            yield return new WaitForSeconds(seconds);
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(0.9f);
        }

        static int Count(string id)
        {
            int n = 0;
            var r = Rooms.I.Find(id);
            foreach (var e in Enemy.All) if (e && r.rect.Contains(e.home)) n++;
            return n;
        }

        static IEnumerator Run(AutoTest t)
        {
            int bad = 0;
            void Check(string what, bool ok) { t.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
            Save.ClearAll(); Save.Use(0);
            DialogueBox.AutoAdvance = 0.1f;
            Game.I.Begin(false);
            Story.Abort();
            Story.GiveKit();
            Game.I.EnterMap("zig_1", "south");
            Fade.Set(0);
            var p = Player.I;
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.5f);
            Check($"the floor has rooms ({(Rooms.I ? Rooms.I.all.Count : 0)}) and he starts in the hall ({Rooms.I?.current?.id})", Rooms.I && Rooms.I.all.Count == 9 && Rooms.I.current.id == "hall");
            Check($"only the hall's own are out (hall {Count("hall")}, west {Count("west")}, stair {Count("stair")})", Count("hall") == 2 && Count("west") == 0 && Count("stair") == 0);
            yield return t.Shot("r1-hall", 0.2f);
            // west, through the side doorway
            p.pos = InRoom("hall", 44, 130);
            Controls.Fake = Vector2.left;
            yield return new WaitForSeconds(0.42f);
            yield return t.Shot("r2-sliding-west", 0.0f);
            yield return new WaitForSeconds(0.5f);
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(0.8f);
            Check($"walked west: now in '{Rooms.I.current.id}', free again ({p.state}), hall emptied ({Count("hall")}), west filled ({Count("west")})",
                Rooms.I.current.id == "west" && p.state == Player.State.Free && Count("hall") == 0 && Count("west") == 1);
            yield return t.Shot("r3-west", 0.2f);
            var bars = Map.Current.Find("z1_bars");
            Check("the bars are down before the plate is pressed", bars && bars.sr.enabled && bars.solid != null);
            Story.Set("on_z1_plate");
            yield return new WaitForSeconds(0.3f);
            Check("the plate lifts them", bars && !bars.sr.enabled && bars.solid == null);
            Story.Abort();
            p.SetState(Player.State.Free, "idle");
            // back east, then north through the locked door
            p.pos = InRoom("west", 380, 130);
            yield return Walk(Vector2.right, 0.8f);
            Check($"back in the hall ({Rooms.I.current.id})", Rooms.I.current.id == "hall");
            p.pos = InRoom("hall", 208, 64);
            p.Face(Facing.Up);
            yield return Walk(Vector2.up, 0.5f);
            Check($"the locked door stops him (still in {Rooms.I.current.id})", Rooms.I.current.id == "hall");
            yield return t.Shot("r4-locked", 0.1f);
            p.keys = 1;
            p.pos = InRoom("hall", 208, 60);
            p.Face(Facing.Up);
            yield return new WaitForSeconds(0.2f);
            Check($"facing it, the action button says {p.Action}", p.Action == Player.Act.Open);
            Controls.FakePress = Controls.Interact;
            yield return new WaitForSeconds(0.5f);
            int shut = 0;
            foreach (var pr in Map.Current.props) if (pr && (pr.Kind == "lockdoor")) shut++;
            Check($"one key opens the door and its far side (doors still shut: {shut})", shut == 0 && Story.Has("door_z1_door"));
            Controls.Fake = Vector2.up;
            yield return new WaitForSeconds(0.55f);
            yield return t.Shot("r5-under-the-lintel", 0.0f);
            yield return new WaitForSeconds(0.75f);
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(0.8f);
            Check($"through the doorway into '{Rooms.I.current.id}'", Rooms.I.current.id == "proc");
            // up the processional to the stair hall
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            p.pos = InRoom("proc", 208, 64);
            yield return Walk(Vector2.up, 1.3f);
            Check($"and up the processional into '{Rooms.I.current.id}' ({Count("stair")} sentinels)", Rooms.I.current.id == "stair" && Count("stair") == 2);
            yield return t.Shot("r6-stair-hall", 0.2f);
            // the sun disc, lit off the mirror shield from the pool of moonlight, lifts the bars of the vault
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            var disc = Map.Current.Find("z1_disc");
            Check("there is a sun disc, and a pool of moonlight under it", disc && Map.Current.Marker("pool") != null);
            var vaultBars = Map.Current.Find("z1_vault");
            Check("the vault is barred until it is lit", vaultBars && vaultBars.solid != null);
            if (disc)
            {
                Story.Set("item_shield"); Story.I.ApplyItems();
                p.pos = disc.basePos + new Vector2(0, -5.9f);
                p.Face(Facing.Up);
                p.SetState(Player.State.Free, "idle");
                yield return new WaitForSeconds(0.2f);
                Controls.FakeHold = Controls.Interact; Controls.FakePress = Controls.Interact;
                yield return new WaitForSeconds(0.5f);
                yield return t.Shot("r6b-light", 0.0f);
                yield return new WaitForSeconds(1.0f);
                Controls.FakeHold = null;
                yield return new WaitForSeconds(0.3f);
            }
            Check($"the shield throws the moon at it and it lights ({Story.Has("on_z1_disc")})", Story.Has("on_z1_disc"));
            float ww = 0;
            while (Story.I.Running && ww < 8f) { ww += Time.deltaTime; yield return null; }
            p.pos = InRoom("stair", 380, 130);
            yield return Walk(Vector2.right, 0.8f);
            Check($"and the vault is open ({Rooms.I.current.id})", Rooms.I.current.id == "vault");
            yield return t.Shot("r7-vault", 0.2f);
            // down again through the stair hall's south door
            p.pos = InRoom("vault", 40, 130);
            yield return Walk(Vector2.left, 0.8f);
            p.pos = InRoom("stair", 208, 196);
            Controls.Fake = Vector2.down;
            yield return new WaitForSeconds(0.5f);
            yield return t.Shot("r8-sliding-south", 0.0f);
            yield return new WaitForSeconds(0.6f);
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(0.8f);
            Check($"south through the door: '{Rooms.I.current.id}', standing clear of the wall (y {p.pos.y - Rooms.I.current.rect.yMax:0.0} below the room's top)",
                Rooms.I.current.id == "proc" && p.pos.y < Rooms.I.current.rect.yMax - 3f);
            yield return t.Shot("r9-hall-again", 0.2f);
            Check($"rooms walked are remembered for the map ({Story.Has(Rooms.VisitedFlag("zig_1", "vault"))})", Story.Has(Rooms.VisitedFlag("zig_1", "vault")));
            t.Note(bad == 0 ? "ROOMS OK" : $"ROOMS: {bad} FAILED");
        }
    }
}
