// Chapter two's path, walked the way a player would: the opening on the summit, the gate on
// the terraces, the queue that only a dreamer gets past, the three stones, the king's door, the
// servants and the key behind them, the four fires, and the widow's figs. Each line in the log
// must say "ok". (The king himself is fought in the "king" scene.)
using System;
using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Wakefire
{
    public static class HillTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["hill"] = Run;

        static IEnumerator Idle(float min = 0.4f, float max = 40f)
        {
            float w = 0;
            while ((w < min || (Story.I && Story.I.Running) || Game.Busy) && w < max) { w += Time.deltaTime; yield return null; }
        }

        static void Clear()
        {
            foreach (var e in Enemy.All.ToArray()) if (e) UnityEngine.Object.Destroy(e.gameObject);
        }

        static IEnumerator Enter(string map, string spawn)
        {
            Game.I.EnterMap(map, spawn);
            Fade.Set(0);
            Dream.I.SetInstant(false);
            Player.I.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.3f);
            Clear();
            yield return Idle(0.3f);
        }

        /// <summary>Stand below a thing, face it, press the talk/look button, let the scene play.</summary>
        static IEnumerator Use(AutoTest t, string id, string label, Func<bool> ok, bool dream = false, InputAction with = null)
        {
            var p = Player.I;
            var pr = Map.Current.Find(id);
            if (pr == null) { t.Note($"{label}: MISSING prop {id}"); yield break; }
            p.pos = pr.basePos + new Vector2(0, -0.85f);
            p.Face(Facing.Up);
            p.SetState(Player.State.Free, "idle");
            if (dream) { Dream.I.Drowsiness = 1; Dream.I.Seconds = 9999; Dream.I.Flip(p.pos, true); yield return new WaitForSeconds(1.2f); }
            yield return new WaitForSeconds(0.2f);
            Controls.FakePress = with ?? Controls.Interact;
            yield return Idle(0.9f);
            t.Note($"{label}: {(ok() ? "ok" : "FAILED")}");
            if (dream) { Dream.I.SetInstant(false); Story.I.ApplyItems(); }
        }

        static IEnumerator Talk(AutoTest t, string npc, string label, Func<bool> ok, bool dream = false)
        {
            var p = Player.I;
            Npc who = null;
            foreach (var n in Npc.All) if (n && n.id == npc) who = n;
            if (!who) { t.Note($"{label}: MISSING person {npc}"); yield break; }
            p.pos = who.pos + new Vector2(0, -0.9f);
            p.Face(Facing.Up);
            p.SetState(Player.State.Free, "idle");
            if (dream) { Dream.I.Drowsiness = 1; Dream.I.Seconds = 9999; Dream.I.Flip(p.pos, true); yield return new WaitForSeconds(1.2f); }
            yield return new WaitForSeconds(0.2f);
            Controls.FakePress = Controls.Interact;
            yield return Idle(0.9f);
            t.Note($"{label}: {(ok() ? "ok" : "FAILED")}");
            if (dream) { Dream.I.SetInstant(false); Story.I.ApplyItems(); }
        }

        /// <summary>Walk one way for a while and report where Azar ended up (map pixels).</summary>
        static IEnumerator Walk(Vector2 fromPx, Vector2 dir, float seconds, bool dream, Action<Vector2> done)
        {
            var p = Player.I;
            p.pos = Map.ToWorld(fromPx.x, fromPx.y);
            p.SetState(Player.State.Free, "idle");
            Dream.I.SetInstant(false);
            if (dream) { Dream.I.Drowsiness = 1; Dream.I.Seconds = 9999; Dream.I.Flip(p.pos, true); yield return new WaitForSeconds(1.2f); }
            yield return null;
            for (float w = 0; w < seconds; w += Time.deltaTime)
            {
                Controls.Fake = p.state == Player.State.Free ? dir : Vector2.zero;
                yield return null;
            }
            Controls.Fake = Vector2.zero;
            yield return null;
            done(new Vector2(p.pos.x * 16f, -p.pos.y * 16f));
            if (dream) { Dream.I.SetInstant(false); Story.I.ApplyItems(); }
            yield return Idle(0.3f);
        }

        static IEnumerator Run(AutoTest t)
        {
            DialogueBox.AutoAdvance = 0.05f;
            // chapter one, finished
            foreach (var f in new[] { "key", "gate_open", "braziers", "item_shield", "item_oil", "item_lamp", "bigkey", "yard_bridge", "bull_seen", "bull_dead", "chapter_done" }) Story.Set(f);
            Game.I.EnterMap("zig_3", null);
            Story.I.ApplyItems();
            Fade.Set(0);
            var p = Player.I;
            p.SetState(Player.State.Free, "idle");
            // ---- the summit: chapter two opens by itself
            float w0 = Time.time;
            while (!(Story.Has("item_hillkey") && Game.I.CurrentMap == "terraces") && Time.time - w0 < 90f) yield return null;
            yield return Idle(0.5f);
            t.Note($"chapter two opens on the summit, hands over the Hill Key and takes Azar to the terraces: {(Story.Has("item_hillkey") && Game.I.CurrentMap == "terraces" ? "ok" : "FAILED")} ({Time.time - w0:0}s)");
            yield return t.Shot("h0-terraces-gate", 0.3f);
            // ---- the gate on the terraces
            yield return Use(t, "hill_gate", "hill gate opens with the key", () => Story.Has("hill_gate"));
            p.pos = Map.ToWorld(700, 34);
            Controls.Fake = Vector2.up;
            w0 = Time.time;
            while (Game.I.CurrentMap != "necro_road" && Time.time - w0 < 6f) yield return null;
            Controls.Fake = Vector2.zero;
            t.Note($"through the gate onto the road of the dead: {(Game.I.CurrentMap == "necro_road" ? "ok" : "FAILED")}");
            // ---- the road: Namtar hails him
            w0 = Time.time;
            while (!Story.Has("met_namtar") && Time.time - w0 < 8f) yield return null;
            yield return Idle(0.5f);
            t.Note($"Namtar stops him at the gate: {(Story.Has("met_namtar") ? "ok" : "FAILED")}");
            yield return t.Shot("h1-road", 0.3f);
            Clear();
            Vector2 end = Vector2.zero;
            yield return Walk(new Vector2(420, 322), Vector2.up, 1.4f, false, e => end = e);
            t.Note($"the queue will not let a waking man through: {(end.y > 296 ? "ok" : "FAILED")} (y {end.y:0})");
            yield return Walk(new Vector2(420, 322), Vector2.up, 1.4f, true, e => end = e);
            t.Note($"a dreamer walks straight through it: {(end.y < 280 ? "ok" : "FAILED")} (y {end.y:0})");
            yield return Idle(1.0f);
            t.Note($"and the queue has something to say about that: {(Story.Has("queue_passed") ? "ok" : "FAILED")}");
            yield return Use(t, "stele_kur", "the first stone gives KUR", () => Story.Has("name_kur"));
            yield return Talk(t, "belu", "Old Belu hands over the figs", () => Story.Has("item_figs"));
            yield return Talk(t, "gran_dur", "Great-Grandmother Dur has her say", () => Story.Count("gran") == 1);
            // ---- the hilltop
            yield return Enter("necropolis", "south");
            yield return t.Shot("h2-hilltop", 0.3f);
            yield return Talk(t, "general_a", "the generals explain the three stones", () => Story.Count("generals") == 1);
            yield return Use(t, "stele_tar", "the garden stone is too dark to read", () => !Story.Has("name_tar"));
            yield return Use(t, "garden_0", "first garden altar takes the Wakefire", () => Map.Current.Find("garden_0").lit, false, Controls.Item);
            yield return Use(t, "garden_1", "second altar: the stone gives TAR", () => Story.Has("name_tar"), false, Controls.Item);
            yield return Walk(new Vector2(530, 256), Vector2.right, 1.2f, false, e => end = e);
            t.Note($"the split stops a waking man: {(end.x < 560 ? "ok" : "FAILED")} (x {end.x:0})");
            yield return Walk(new Vector2(530, 256), Vector2.right, 1.6f, true, e => end = e);
            t.Note($"the road of moonlight carries a dreamer to the rock: {(end.x > 636 ? "ok" : "FAILED")} (x {end.x:0})");
            yield return Use(t, "stele_ash", "the stone on the rock gives ASH", () => Story.Has("name_ash"));
            int max0 = p.health.max;
            yield return Use(t, "isle_vessel", "flame vessel on the rock", () => p.health.max == max0 + 2);
            DialogueBox.Answers.Clear();
            yield return Use(t, "king_door", "the wrong name opens nothing", () => !Story.Has("king_door"));
            foreach (int a in new[] { 0, 1, 1 }) DialogueBox.Answers.Enqueue(a);
            yield return Use(t, "king_door", "KUR-ASH-TAR opens the king's door", () => Story.Has("king_door"));
            yield return t.Shot("h3-door-open", 0.3f);
            p.pos = Map.ToWorld(384, 118);
            Controls.Fake = Vector2.up;
            w0 = Time.time;
            while (Game.I.CurrentMap != "tomb_1" && Time.time - w0 < 6f) yield return null;
            Controls.Fake = Vector2.zero;
            t.Note($"through the door into the tomb: {(Game.I.CurrentMap == "tomb_1" ? "ok" : "FAILED")}");
            // ---- the hall of servants
            yield return Idle(0.5f);
            Clear();
            yield return t.Shot("h4-tomb1", 0.3f);
            yield return Walk(new Vector2(448, 340), Vector2.up, 1.2f, false, e => end = e);
            t.Note($"the king's servants will not let a waking man by: {(end.y > 300 ? "ok" : "FAILED")} (y {end.y:0})");
            yield return Walk(new Vector2(448, 340), Vector2.up, 1.2f, true, e => end = e);
            t.Note($"a dreamer walks through them: {(end.y < 288 ? "ok" : "FAILED")} (y {end.y:0})");
            int keys0 = p.keys;
            yield return Use(t, "t1_key", "the key behind the servants", () => p.keys == keys0 + 1, true);
            yield return Use(t, "t1_door", "the locked door takes it", () => Story.Has("door_t1_door"));
            yield return Talk(t, "robber_a_self", "Zimu, asleep and rich", () => Story.Count("zimu") == 1, true);
            // ---- the hall of the lyre
            yield return Enter("tomb_2", "south");
            yield return Use(t, "t2_seal", "the sun door is cold", () => !Story.Has("door_t2_seal"));
            for (int i = 0; i < 4; i++)
            {
                int k = i;
                yield return Use(t, "lyre_" + i, i < 3 ? $"fire {i + 1} of four" : "the fourth fire opens the sun door",
                    () => Map.Current.Find("lyre_" + k).lit && Story.Has("door_t2_seal") == (k == 3), false, Controls.Item);
            }
            yield return Walk(new Vector2(180, 262), Vector2.up, 1.0f, false, e => end = e);
            t.Note($"the trench stops a waking man: {(end.y > 240 ? "ok" : "FAILED")} (y {end.y:0})");
            yield return Walk(new Vector2(180, 262), Vector2.up, 1.3f, true, e => end = e);
            t.Note($"a dreamer crosses it on moonlight: {(end.y < 196 ? "ok" : "FAILED")} (y {end.y:0})");
            yield return t.Shot("h5-tomb2", 0.3f);
            p.pos = Map.ToWorld(256, 70);
            Controls.Fake = Vector2.up;
            w0 = Time.time;
            while (Game.I.CurrentMap != "tomb_3" && Time.time - w0 < 6f) yield return null;
            Controls.Fake = Vector2.zero;
            t.Note($"through the sun door to the king: {(Game.I.CurrentMap == "tomb_3" ? "ok" : "FAILED")}");
            // ---- the widow's figs
            yield return Enter("ashkel", null);
            max0 = p.health.max;
            yield return Talk(t, "walker_self", "the widow gets her figs, and gives a flame vessel for them", () => Story.Has("figs_given") && p.health.max == max0 + 2, true);
            // ---- and a save carries it
            Save.Write("necropolis", "south");
            var d = Save.Read();
            bool saved = d != null && Array.IndexOf(d.flags, "king_door") >= 0 && Array.IndexOf(d.flags, "name_ash") >= 0 && Array.IndexOf(d.flags, "door_t2_seal") >= 0;
            t.Note("save keeps the hill's doors and names: " + (saved ? "ok" : "FAILED"));
            Save.Clear();
        }
    }
}
