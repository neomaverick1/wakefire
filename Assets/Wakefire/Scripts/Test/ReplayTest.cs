// After the credits (chapter two's): the title comes back, and both a new game and Continue must leave Azar
// free to walk (not frozen in the last cutscene), with the right pockets.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class ReplayTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["replay"] = Run;

        static IEnumerator Run(AutoTest t)
        {
            DialogueBox.AutoAdvance = 0.05f;
            foreach (var f in new[] { "item_shield", "bull_seen", "bull_dead", "chapter_done", "ch2", "item_hillkey", "king_done", "item_horn" }) Story.Set(f);
            Game.I.EnterMap("zig_3", "south");
            Story.Abort();              // the summit would start the dawn by itself; this run starts it by hand
            Fade.Set(0);
            var p = Player.I;
            p.coins = 77; p.keys = 2;
            yield return new WaitForSeconds(0.5f);
            p.pos = Map.ToWorld(240, 200);
            Story.Run(Story.I.Dawn());
            float w = 0;
            while (!Title.I && w < 150f) { w += Time.deltaTime; yield return null; }
            t.Note($"title after the credits: {(Title.I ? "ok" : "FAILED")} ({w:0}s)");
            yield return t.Shot("r1-title", 0.5f);
            // a new game
            Title.I.gameObject.SetActive(false);
            Object.Destroy(Title.I.gameObject);
            yield return null;
            Game.I.Begin(false);
            w = 0;
            while (Story.I.Running && w < 60f) { w += Time.deltaTime; yield return null; }
            t.Note($"intro took {w:0.0}s, running={Story.I.Running} state={p.state} dialog={(DialogueBox.I ? DialogueBox.I.Busy : false)} busy={Game.Busy}");
            yield return new WaitForSeconds(0.3f);
            var x0 = p.pos;
            Controls.Fake = Vector2.down;
            yield return new WaitForSeconds(0.5f);
            Controls.Fake = Vector2.zero;
            t.Note($"new game: map={Game.I.CurrentMap} coins={p.coins} keys={p.keys} hp={p.health.hp}/{p.health.max} shield={p.hasShield} moved={(p.pos - x0).magnitude:0.0} state={p.state}");
            bool ok = Game.I.CurrentMap == "ashkel" && p.coins == 0 && p.keys == 0 && !p.hasShield && (p.pos - x0).magnitude > 0.5f;
            t.Note("new game clean and playable: " + (ok ? "ok" : "FAILED"));
            // and Continue from the save the ending wrote
            Save.Write("zig_3", null);
            Game.I.Begin(true);
            yield return new WaitForSeconds(0.6f);
            x0 = p.pos;
            Controls.Fake = Vector2.up;
            yield return new WaitForSeconds(0.5f);
            Controls.Fake = Vector2.zero;
            t.Note($"continue: map={Game.I.CurrentMap} moved={(p.pos - x0).magnitude:0.0} state={p.state}");
            Save.Clear();
        }
    }
}
