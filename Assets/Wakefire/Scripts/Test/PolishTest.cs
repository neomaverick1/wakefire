// Small-details check: the dog by the well in both worlds, banners moving in the wind over the
// gate square, moths round the torches, and wave crests coming and going on the sea.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class PolishTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["polish"] = Run;

        static Npc Find(string id) => Npc.All.Find(n => n && n.id == id);

        static IEnumerator Enter(string map, string spawn = null)
        {
            Game.I.EnterMap(map, spawn);
            Fade.Set(0);
            yield return new WaitForSeconds(0.5f);
        }

        static void Frame(Vector2 mapPx)
        {
            var v = PixelView.I;
            v.target = null;
            v.SnapTo(Map.ToWorld(mapPx.x, mapPx.y));
        }

        static IEnumerator Run(AutoTest t)
        {
            DialogueBox.AutoAdvance = 30f;
            // the dog by the well
            yield return Enter("lowtown", "north");
            var p = Player.I;
            var dog = Find("dog");
            var self = Find("dog_self");
            t.Note("dog " + (dog ? "ok" : "MISSING") + ", self " + (self ? "ok" : "MISSING"));
            p.pos = dog.pos + new Vector2(1.4f, 0);
            p.Face(Facing.Left);
            Frame(new Vector2(600, 262));
            yield return t.Shot("p1-dog-wake", 0.6f);
            Story.Run(dog.talk(), dog);
            yield return t.Shot("p2-dog-wake-talk", 2.2f);
            DialogueBox.AutoAdvance = 0.05f;
            while (Story.I.Running) yield return null;
            DialogueBox.AutoAdvance = 30f;
            Dream.I.Drowsiness = 1;
            Dream.I.Flip(p.pos, true);
            yield return t.Shot("p3-dog-dream", 1.6f);
            Story.Run(self.talk(), self);
            yield return t.Shot("p4-dog-lion", 3.2f);
            DialogueBox.AutoAdvance = 0.05f;
            while (Story.I.Running) yield return null;
            Dream.I.SetInstant(false);
            DialogueBox.AutoAdvance = 30f;
            // banners and torch moths over the gate square
            yield return Enter("ashkel", "south");
            p.pos = Map.ToWorld(480, 130);
            p.Face(Facing.Up);
            Frame(new Vector2(480, 96));
            yield return t.Shot("p5-banners-a", 0.8f);
            yield return t.Shot("p5-banners-b", 0.5f);
            // the sea
            yield return Enter("cliffs", "west");
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            p.pos = Map.ToWorld(560, 456);
            p.Face(Facing.Right);
            Frame(new Vector2(690, 400));
            yield return t.Shot("p6-sea-a", 0.8f);
            yield return t.Shot("p6-sea-b", 0.7f);
            // the pause menu, with the sound switches
            Controls.FakePress = Controls.Pause;
            yield return new WaitForSecondsRealtime(0.4f);
            t.Note("paused: " + Game.Paused);
            Settings.Toggle(true);
            yield return t.Shot("p7-pause", 0.3f);
            t.Note($"music off: volume {Music.Volume}");
            Settings.Toggle(true);
            Controls.FakePress = Controls.Pause;
            yield return new WaitForSecondsRealtime(0.3f);
            t.Note("unpaused: " + !Game.Paused + $", music back to {Music.Volume}");
            int crests = 0, moths = 0;
            foreach (var pr in Object.FindObjectsByType<Prop>(FindObjectsSortMode.None)) if (pr.Kind == "crest") crests++;
            moths = Object.FindObjectsByType<TorchMoths>(FindObjectsSortMode.None).Length;
            t.Note($"crests {crests}, moth swarms {moths}");
        }
    }
}
