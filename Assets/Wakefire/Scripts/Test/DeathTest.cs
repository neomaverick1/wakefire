// Falling, saving and loading, end to end: -wfScene death kills Azar away from the door he came in
// by and checks each way back: wake here, one of the three journeys (from the fallen screen and
// from the save page of the pause screen), and the title with its three journeys and rubbing one
// out. It also checks that a save from before there were three turns up as the first journey.
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

        static IEnumerator Do(string what, float wait = 0.4f)
        {
            Pause.TestDo = what;
            yield return new WaitForSecondsRealtime(wait);
        }

        static IEnumerator Run(AutoTest t)
        {
            var g = Game.I;
            int bad = 0;
            void Check(string what, bool ok) { t.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }

            // 0. a save from before there were three journeys becomes the first of them
            Save.ClearAll();
            PlayerPrefs.SetString("wakefire_save_1", JsonUtility.ToJson(new SaveData { map = "cliffs", spawn = "west", coins = 77, keys = 1, maxHp = 8, flags = new[] { "key", "gate_open" }, countKeys = new string[0], countVals = new int[0], playTime = 600 }));
            PlayerPrefs.SetString("wakefire_save_2", JsonUtility.ToJson(new SaveData { map = "lowtown", spawn = "north", coins = 12, keys = 0, maxHp = 6, flags = new string[0], countKeys = new string[0], countVals = new int[0], playTime = 90 }));
            Save.Reread();
            Check("0. the old save is journey 1, the old own save journey 2, the old keys are gone",
                Save.Has(0) && Save.Read(0).coins == 77 && Save.Has(1) && Save.Read(1).map == "lowtown" && !Save.Has(2) && !PlayerPrefs.HasKey("wakefire_save_1") && !PlayerPrefs.HasKey("wakefire_save_2"));
            Save.ClearAll();
            Save.Reread();

            Fallen.AutoPick = false;
            Save.Use(0);
            g.Begin(false);
            Story.Abort();
            Story.GiveKit();
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

            // 2. the pause screen: it opens on the items, the save page saves into the journey in play and copies into another
            p.coins = 40;
            Story.Set("test_flag_saved");
            Controls.FakePress = Controls.Pause;
            yield return new WaitForSecondsRealtime(0.4f);
            Check("2. the pause screen opens", Game.Paused && Pause.Open);
            yield return t.Shot("d2-pause-items");
            yield return Do("page 0");
            yield return Do("save 0");
            Check("2. Save writes the journey in play", Save.Has(0) && Save.Read(0).coins == 40 && Save.Slot == 0);
            yield return Do("save 1");
            Check("2. Save into journey 2 leaves a copy there and play stays in journey 1", Save.Has(1) && Save.Read(1).coins == 40 && Save.Slot == 0);
            yield return Do("row 1");
            yield return t.Shot("d2-pause-saved");
            yield return Do("ask 1");
            yield return t.Shot("d2-pause-ask");
            yield return Do("page 2");
            yield return t.Shot("d2-pause-map");
            yield return Do("close");
            Check("2. closing it carries on", !Game.Paused && Time.timeScale == 1f);

            // 3. spend, pick up a flag, walk into another place, fall there, and go back to the copy
            p.coins = 3;
            Story.Set("test_flag_after");
            g.Go("ashkel", "south");
            yield return new WaitForSecondsRealtime(1.2f);
            Check("3. walked into the next place (the journey in play saves itself, the copy stays)", g.CurrentMap == "ashkel" && Save.Read(0).map == "ashkel" && Save.Read(1).map == "lowtown");
            yield return t.Shot("d3-place-name-and-saved", 0.5f);
            p.pos += new Vector2(0, 3);
            yield return Fall(p);
            yield return Pick(Fallen.LoadSave, 0.5f);
            yield return t.Shot("d4-fallen-which-journey");
            yield return Pick(1);
            Check($"3. Load from the fallen screen: back in {g.CurrentMap} with {p.coins} coins, journey {Save.Slot + 1} in play",
                g.CurrentMap == "lowtown" && p.coins == 40 && Story.Has("test_flag_saved") && !Story.Has("test_flag_after") && p.health.hp == p.health.max && p.state == Player.State.Free && Save.Slot == 1);

            // 4. Load from the pause screen
            p.coins = 5;
            Controls.FakePress = Controls.Pause;
            yield return new WaitForSecondsRealtime(0.4f);
            yield return Do("load 0", 1.6f);
            Check($"4. Load from the pause screen: {g.CurrentMap}, {p.coins} coins, journey {Save.Slot + 1}, paused={Game.Paused}",
                !Game.Paused && g.CurrentMap == "ashkel" && p.coins == 3 && Save.Slot == 0 && !Game.Busy && Time.timeScale == 1f);

            // 5. fall, back to the title: the three journeys are there; rubbing one out; carrying on with another; beginning in the empty one
            yield return Fall(p);
            yield return Pick(Fallen.ToTitle, 0.8f);
            Check("5. the title is up", Title.I != null);
            var lines = Title.I ? string.Join(" | ", Title.I.Lines) : "";
            Check("5. title offers: " + lines, lines.Contains("1 The Temple Gate") && lines.Contains("2 The Lower Town") && lines.Contains("3 Begin a new journey") && lines.Contains("Rub one out"));
            yield return t.Shot("d6-title");
            Title.TestPick = "erase 1";
            yield return new WaitForSecondsRealtime(0.4f);
            Check("5. journey 1 rubbed out, journey 2 untouched", Title.I != null && !Save.Has(0) && Save.Has(1));
            yield return t.Shot("d7-title-one-gone");
            Title.TestPick = "2";
            yield return new WaitForSecondsRealtime(1.8f);
            Check($"5. journey 2 from the title: {g.CurrentMap}, {p.coins} coins", Title.I == null && g.CurrentMap == "lowtown" && p.coins == 40 && p.state == Player.State.Free && Save.Slot == 1);
            Controls.FakePress = Controls.Pause;
            yield return new WaitForSecondsRealtime(0.4f);
            yield return Do("title", 0.8f);
            Title.TestPick = "3";
            yield return new WaitForSecondsRealtime(1.8f);
            Check($"5. a new journey in the third: {g.CurrentMap}, {p.coins} coins, journey {Save.Slot + 1}", Title.I == null && g.CurrentMap == "ashkel" && p.coins == 0 && Save.Slot == 2 && Save.Has(1));
            Story.Abort();
            Save.ClearAll();
            t.Note(bad == 0 ? "SAVE AND FALL OK" : $"FAILED {bad}");
        }
    }
}
