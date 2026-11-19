// Staged frames of the Gate Square for screenshots: the Wakefire catching a brazier, the goat,
// the ring of the dream sweeping across the square, and the dream itself.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class ShowcaseTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["showcase"] = Run;

        static Npc Find(string id) => Npc.All.Find(n => n && n.id == id);

        static IEnumerator Run(AutoTest t)
        {
            var g = Game.I;
            var p = g.EnterMap("ashkel");
            p.coins = 27;
            Map.Current.Find("square_1").Ignite();
            var goat = Find("goat");
            goat.pos = Map.ToWorld(396, 206);
            goat.facing = Facing.Right;
            goat.SetIdle("stare");
            var dreamer = Find("dreamer");
            dreamer.pos = Map.ToWorld(566, 206);
            var dself = Find("dreamer_self");
            dself.pos = Map.ToWorld(572, 206);
            p.pos = Map.ToWorld(425, 186);
            p.Face(Facing.Left);
            g.View.target = null;
            g.View.SnapTo(Map.ToWorld(480, 112));
            yield return new WaitForSeconds(1.0f);
            // Azar holds out the Wakefire and the brazier catches
            p.SetState(Player.State.Use, "use");
            yield return t.Shot("01-wakefire", 0.32f);
            yield return new WaitForSeconds(1.2f);
            yield return t.Shot("02-calm", 0.1f);
            // the goat
            p.pos = Map.ToWorld(420, 212);
            p.Face(Facing.Left);
            DialogueBox.AutoAdvance = 30f;
            Story.Bump("goat");
            Story.Run(goat.talk(), goat);
            yield return t.Shot("03-goat", 2.2f);
            DialogueBox.AutoAdvance = 0.05f;
            while (Story.I.Running) yield return null;
            DialogueBox.AutoAdvance = 0;
            // nodding off: the ring of the dream sweeps out across the square
            p.pos = Map.ToWorld(480, 196);
            p.Face(Facing.Down);
            yield return new WaitForSeconds(0.4f);
            Dream.I.Flip(p.pos, true);
            yield return t.Shot("04-ring", 0.16f);
            yield return t.Shot("05-dream", 1.6f);
        }
    }
}
