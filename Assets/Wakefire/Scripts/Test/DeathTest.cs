// Falling, saving and loading, end to end: -wfScene death kills Azar away from the door he came in
// by and checks each way back: wake here, the player's own save (from the fallen screen and from
// the pause menu), and the title with its Continue, Load game and New Game.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class DeathTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["death"] = Run;

        static bool MenuUp => GameObject.Find("Fallen") != null;

        static IEnumerator Fall(Player p)
        {
            p.health.invulnerable = 0;
            p.Hurt(new HitInfo { damage = 99, from = p.pos + Vector2.up, knockback = 2 });
            for (float w = 0; w < 6f && !MenuUp; w += Time.unscaledDeltaTime) yield return null;
            yield return new WaitForSecondsRealtime(0.5f);
        }

        static IEnumerator Pick(int line, float wait = 1.4f)
        {
            PanelMenu.FakePick = line;
            yield return new WaitForSecondsRealtime(wait);
        }

        static IEnumerator Run(AutoTest t)
        {
            var g = Game.I;
            int bad = 0;
            void Check(string what, bool ok) { t.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
            Save.ClearAll();
            Fallen.AutoPick = false;
            g.Begin(false);
            Story.Abort();
            var p = g.EnterMap("lowtown", "north");
            Fade.Set(0);
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.5f);
            var door = p.pos;

            // 1. fall with nothing saved: the choice comes up, Load can't be chosen, "Wake at" puts him back at the door
            p.pos += new Vector2(3, -4);
            p.coins = 17;
            yield return new WaitForSeconds(0.3f);
            yield return Fall(p);
            Check("1. the fallen screen comes up", MenuUp);
            yield return t.Shot("d1-fallen-nothing-saved");
            yield return Pick(Fallen.LoadSave, 0.5f);
            Check("1. Load does nothing with no save", MenuUp);
            yield return Pick(Fallen.WakeHere);
            Check($"1. woke at the way in, full life, coins kept (hp {p.health.hp}/{p.health.max}, coins {p.coins})",
                !MenuUp && p.state == Player.State.Free && p.health.hp == p.health.max && p.coins == 17 && Vector2.Distance(p.pos, door) < 0.1f && !Game.Busy);

            // 2. the player's own save from the pause menu
            p.coins = 40;
            Story.Set("test_flag_saved");
            Controls.FakePress = Controls.Pause;
            yield return new WaitForSecondsRealtime(0.4f);
            Check("2. pause menu opens", Game.Paused);
            yield return Pick(1, 0.4f);
            Check("2. Save writes the player's save", Save.HasManual && Save.ReadManual().coins == 40);
            yield return t.Shot("d2-pause-saved");
            yield return Pick(0, 0.4f);
            Check("2. Carry on closes it", !Game.Paused);

            // 3. spend, pick up a flag, walk into another place, fall there, and load the save back
            p.coins = 3;
            Story.Set("test_flag_after");
            g.Go("ashkel", "south");
            yield return new WaitForSecondsRealtime(1.2f);
            Check("3. walked into the next place (the game's own save follows)", g.CurrentMap == "ashkel" && Save.Read().map == "ashkel" && Save.ReadManual().map == "lowtown");
            yield return t.Shot("d3-place-name-and-saved", 0.5f);
            p.pos += new Vector2(0, 3);
            yield return Fall(p);
            yield return t.Shot("d4-fallen-with-save");
            yield return Pick(Fallen.LoadSave);
            Check($"3. Load from the fallen screen: back in {g.CurrentMap} with {p.coins} coins",
                g.CurrentMap == "lowtown" && p.coins == 40 && Story.Has("test_flag_saved") && !Story.Has("test_flag_after") && p.health.hp == p.health.max && p.state == Player.State.Free);

            // 4. Load from the pause menu asks once, then does it
            p.coins = 5;
            Controls.FakePress = Controls.Pause;
            yield return new WaitForSecondsRealtime(0.4f);
            yield return Pick(2, 0.4f);
            Check("4. Load asks first", Game.Paused && p.coins == 5);
            yield return t.Shot("d5-pause-load-sure");
            yield return Pick(2, 1.6f);
            Check($"4. second press loads: {p.coins} coins, paused={Game.Paused}", !Game.Paused && p.coins == 40 && !Game.Busy && Time.timeScale == 1f);

            // 5. fall, back to the title: Continue, Load game and New Game are all there; New Game asks first
            yield return Fall(p);
            yield return Pick(Fallen.ToTitle, 0.8f);
            Check("5. the title is up", Title.I != null);
            var lines = Title.I ? string.Join(" | ", Title.I.Lines) : "";
            Check("5. title offers: " + lines, lines.Contains("Continue") && lines.Contains("Load game") && lines.Contains("New Game"));
            yield return t.Shot("d6-title");
            Title.TestPick = "New Game";
            yield return new WaitForSecondsRealtime(0.4f);
            Check("5. New Game asks before wiping", Title.I != null && string.Join("|", Title.I.Lines).Contains("sure") && Save.Exists);
            yield return t.Shot("d7-title-sure");
            Title.TestPick = "Load game";
            yield return new WaitForSecondsRealtime(1.8f);
            Check($"5. Load game from the title: {g.CurrentMap}, {p.coins} coins", Title.I == null && g.CurrentMap == "lowtown" && p.coins == 40 && p.state == Player.State.Free);
            Save.ClearAll();
            t.Note(bad == 0 ? "SAVE AND FALL OK" : $"FAILED {bad}");
        }
    }
}
