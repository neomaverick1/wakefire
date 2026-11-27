// Carrying on a saved journey from the title:  -wfScene titleload  makes a journey, saves it in each
// kind of place (a town, a room of a house, a dungeon), goes back to the title, picks it, and looks at
// what the player would see: the place itself, with the dark lifted off it and Azar free to walk.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class TitleLoadTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["titleload"] = Run;

        static IEnumerator Run(AutoTest t)
        {
            int bad = 0;
            void Check(string what, bool ok) { t.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
            DialogueBox.AutoAdvance = 0.1f;
            var g = Game.I;
            string[][] places =
            {
                new[] { "lowtown", "north" }, new[] { "ashkel", "south" }, new[] { "lowtown_in", "lt_bakery_in" }, new[] { "cliffs", "west" },
                new[] { "terraces", "east" }, new[] { "crypt", null }, new[] { "zig_1", null }, new[] { "necropolis", null }, new[] { "tomb_1", null },
                new[] { "lowtown", "a_spawn_that_is_gone" },
            };
            int n = 0;
            foreach (var pl in places)
            {
                Save.ClearAll(); Save.Use(0);
                g.Begin(false);
                Story.Abort();
                Story.GiveKit();
                Fade.Set(0);
                g.EnterMap(pl[0], pl[1]);
                var p = Player.I;
                p.SetState(Player.State.Free, "idle");
                p.coins = 7 + n;
                Save.Write(pl[0], pl[1], quiet: true);
                yield return new WaitForSecondsRealtime(0.3f);
                Title.Show();
                Fade.Set(0);
                yield return new WaitForSecondsRealtime(0.6f);
                Title.TestPick = "1";
                // the journey opens by itself: the dark lifts without the game's own guard against a dark screen having to
                // step in. (How long that takes is the size of the place: a town's houses are the heaviest. It is timed.)
                int guard = 0;
                void Heard(string msg, string trace, LogType type) { if (msg.Contains("the screen was left dark")) guard++; }
                Application.logMessageReceived += Heard;
                float took = 0;
                while (took < 4f && !(Title.I == null && g.CurrentMap == pl[0] && Fade.Amount <= 0.01f)) { took += Time.unscaledDeltaTime; yield return null; }
                yield return new WaitForSecondsRealtime(0.3f);
                Application.logMessageReceived -= Heard;
                p = Player.I;
                Check($"{pl[0]} / {pl[1] ?? "(the way in)"}: carried on from the title: map {g.CurrentMap}, title gone {Title.I == null}, dark lifted {Fade.Amount:0.00} after {took:0.0}s (the guard stepped in {guard} times), state {p.state}, coins {p.coins}",
                      Title.I == null && g.CurrentMap == pl[0] && Fade.Amount <= 0.01f && guard == 0 && took < 3.5f && (p.state == Player.State.Free || p.state == Player.State.Hurt) && p.coins == 7 + n);
                if (n < 3) yield return t.Shot($"t{n}-{pl[0]}", 0.2f);
                Fade.Set(0);
                n++;
            }
            // and the guard behind it: a screen left dark with nobody holding it so is lifted by the game itself
            Player.I.SetState(Player.State.Free, "idle");
            Fade.Set(1);
            yield return new WaitForSecondsRealtime(2.4f);
            Check($"left dark with nothing holding it, the game lifts it by itself ({Fade.Amount:0.00})", Fade.Amount <= 0.01f);
            t.Note(bad == 0 ? "TITLELOAD OK" : $"FAILED {bad}");
        }
    }
}
