// Mashing every button in every place for a while, to shake out errors before players do.
using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

namespace Wakefire
{
    public static class MonkeyTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["monkey"] = Run;

        static IEnumerator Run(AutoTest t)
        {
            var pad = InputSystem.AddDevice<Gamepad>();
            DialogueBox.AutoAdvance = 0.4f;
            var rng = new System.Random(3);
            string[] maps = { "ashkel", "lowtown", "lowtown_in", "cliffs", "terraces", "crypt", "temple_yard", "zig_1", "zig_2", "zig_hi", "zig_3", "barrow", "tomb_1", "tomb_2", "tomb_hi" };
            foreach (var m in maps)
            {
                Game.I.EnterMap(m);
                Fade.Set(0);
                Story.Set("item_shield");
                Story.Set("item_oil");
                // in the barrow he has Nod's Pocket, with something in it to let out at whatever is about
                if (m == "barrow") { Story.Set("item_pocket"); Story.Set("pocket_snore"); }
                // in the king's tomb he has the Pocket (with a thief's goat in it) and the Sun Wheel, and throws it at whatever is about
                if (m.StartsWith("tomb")) { foreach (var f in new[] { "ch2", "chapter_done", "king_door", "item_pocket", "item_wheel" }) Story.Set(f); Story.Clear("pocket_snore"); Story.Set("pocket_goat"); Items.Chosen = "wheel"; }
                Story.I.ApplyItems();
                Player.I.health.hp = Player.I.health.max;
                float until = Time.time + 22f;
                Vector2 dir = Vector2.zero;
                while (Time.time < until)
                {
                    if (rng.NextDouble() < 0.08) dir = new Vector2((float)rng.NextDouble() * 2 - 1, (float)rng.NextDouble() * 2 - 1);
                    Controls.Fake = dir;
                    var st = new GamepadState();
                    double r = rng.NextDouble();
                    if (r < 0.06) st = st.WithButton(GamepadButton.West);
                    else if (r < 0.08) st = st.WithButton(GamepadButton.East);
                    else if (r < 0.095) st = st.WithButton(GamepadButton.North);
                    else if (r < 0.12) st = st.WithButton(GamepadButton.South);
                    else if (r < 0.13) st = st.WithButton(GamepadButton.RightShoulder);
                    InputSystem.QueueStateEvent(pad, st);
                    if (Player.I.health.hp <= 2) Player.I.health.hp = Player.I.health.max;
                    yield return null;
                }
                Controls.Fake = Vector2.zero;
                InputSystem.QueueStateEvent(pad, new GamepadState());
                t.Note($"{m}: ok, pos={Player.I.pos} state={Player.I.state} enemies={Enemy.All.Count} story={Story.I.Running}");
                yield return t.Shot("monkey-" + m, 0.1f);
                float w = 0;
                while ((Story.I.Running || Game.Busy) && w < 20f) { w += Time.deltaTime; yield return null; }
                if (Dream.I.Dreaming) Dream.I.SetInstant(false);
            }
        }
    }
}
