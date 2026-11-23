// Every lock and every treasure on the chapter's path, used the way a player would: stand in
// front, press the talk/look button, let the scene play. Each line in the log must say "ok".
using System;
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class ProgressTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["progress"] = Run;

        static IEnumerator Use(AutoTest t, string map, string spawn, string id, string label, Func<bool> ok, bool dream = false)
        {
            Game.I.EnterMap(map, spawn);
            Fade.Set(0);
            yield return new WaitForSeconds(0.4f);
            foreach (var e in Enemy.All.ToArray()) if (e) UnityEngine.Object.Destroy(e.gameObject);
            var p = Player.I;
            var pr = Map.Current.Find(id);
            if (pr == null) { t.Note($"{label}: MISSING prop {id}"); yield break; }
            p.pos = pr.basePos + new Vector2(0, -0.85f);
            p.Face(Facing.Up);
            // on a floor of rooms the picture slides to the room he has turned up in: let it, then stand where he meant to
            yield return null; yield return null;
            for (float s = 0; s < 3f && (Rooms.Sliding || Game.Busy); s += Time.deltaTime) yield return null;
            foreach (var e in Enemy.All.ToArray()) if (e) UnityEngine.Object.Destroy(e.gameObject);
            p.pos = pr.basePos + new Vector2(0, -0.85f);
            p.Face(Facing.Up);
            p.SetState(Player.State.Free, "idle");
            if (dream) { Dream.I.Drowsiness = 1; Dream.I.Seconds = 9999; Dream.I.Flip(p.pos, true); yield return new WaitForSeconds(1.2f); }
            yield return new WaitForSeconds(0.2f);
            Controls.FakePress = Controls.Interact;
            float w = 0;
            while ((w < 0.4f || (Story.I && Story.I.Running)) && w < 20f) { w += Time.deltaTime; yield return null; }
            t.Note($"{label}: {(ok() ? "ok" : "FAILED")}");
            if (dream) { Dream.I.SetInstant(false); Dream.I.Seconds = 7; Story.I.ApplyItems(); }
        }

        static IEnumerator Run(AutoTest t)
        {
            DialogueBox.AutoAdvance = 0.05f;
            Game.I.EnterMap("ashkel", "south");
            var p = Player.I;
            int coins0 = p.coins;
            // the gate, once Dur has given up the key
            Story.Set("key");
            yield return Use(t, "ashkel", "gate", "temple_gate", "gate opens with Dur's key", () => Story.Has("gate_open"));
            // the lower town's alley chest
            coins0 = p.coins;
            yield return Use(t, "lowtown", "north", "lt_alley", "alley chest pays out", () => p.coins > coins0);
            // Abu-Nur's oil in the cove
            yield return Use(t, "cliffs", "west", "cove_oil", "Night Oil from the cove", () => Story.Has("item_oil"));
            // the terraces: the vessel, and the lamp only the dream can see
            int max0 = p.health.max;
            yield return Use(t, "terraces", "east", "terrace_vessel", "flame vessel on the terraces", () => Story.Has("chest_terrace_vessel"));
            yield return Use(t, "terraces", "east", "shrine_lamp", "bronze lamp in the dream shrine", () => Story.Has("chest_shrine_lamp"), true);
            t.Note($"life {max0} -> {p.health.max} half-flames");
            // the first floor: the key behind the dream wall, then the locked door
            int keys0 = p.keys;
            yield return Use(t, "zig_1", "south", "z1_key", "small key chest", () => p.keys == keys0 + 1);
            yield return Use(t, "zig_1", "south", "z1_door", "locked door takes the key", () => Story.Has("door_z1_door") && p.keys == keys0);
            yield return Use(t, "zig_1", "south", "z1_coins", "coin chest behind the bars", () => Story.Has("chest_z1_coins"));
            // the second floor: shield, bull key, the great door
            yield return Use(t, "zig_2", "south", "z2_shield", "Bronze Mirror Shield", () => Story.Has("item_shield"));
            yield return Use(t, "zig_2", "top", "z2_bigkey", "bull key", () => Story.Has("bigkey"));
            yield return Use(t, "zig_2", "top", "z2_bigdoor", "great door opens", () => Story.Has("door_z2_bigdoor"));
            // and the saved game carries it all
            Save.Write("zig_2", "top");
            var d = Save.Read();
            bool saved = d != null && Array.IndexOf(d.flags, "door_z2_bigdoor") >= 0 && Array.IndexOf(d.flags, "item_shield") >= 0 && d.maxHp == p.health.max;
            t.Note("save keeps doors, items and life: " + (saved ? "ok" : "FAILED"));
            Save.Clear();
        }
    }
}
