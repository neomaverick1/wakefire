// Test run for people and words: Captain Dur asleep, his dream-self, the braziers, the key,
// the goat and the gate, with screenshots of the text box mid-sentence and finished.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class TalkTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["talk"] = Run;

        static Npc Find(string id) => Npc.All.Find(n => n && n.id == id);

        static IEnumerator Run(AutoTest t)
        {
            var g = Game.I;
            var p = g.EnterMap("ashkel");
            DialogueBox.AutoAdvance = 0.9f;
            var dur = Find("dur");
            t.Note("npcs: " + Npc.All.Count + " dur=" + (dur != null));
            p.pos = dur.pos + new Vector2(0.2f, -1.3f);
            p.Face(Facing.Up);
            g.View.SnapTo(p.pos);
            yield return t.Shot("01-square-people", 1.0f);
            Story.Run(dur.talk(), dur);
            yield return t.Shot("02-typing", 0.55f);
            yield return t.Shot("03-page", 1.6f);
            while (Story.I.Running) yield return null;
            // into Dur's dream
            Dream.I.Flip(p.pos, true);
            yield return new WaitForSeconds(1.2f);
            var child = Find("dur_child");
            Story.Run(child.talk(), child);
            yield return t.Shot("04-child", 1.4f);
            while (Story.I.Running) yield return null;
            // light the three braziers
            foreach (var id in new[] { "square_0", "square_1", "square_2" })
            {
                var b = Map.Current.Find(id);
                b.Ignite();
                p.Notify(b);
            }
            yield return t.Shot("05-lit", 0.8f);
            while (Story.I.Running) yield return null;
            Story.Run(child.talk(), child);
            float w = 0;
            while (Player.I.state != Player.State.ItemGet && w < 12f) { w += Time.deltaTime; yield return null; }
            yield return t.Shot("06-itemget", 1.0f);
            while (Story.I.Running) yield return null;
            t.Note("keys=" + p.keys + " flags=" + string.Join(",", Story.Flags));
            Dream.I.Flip(p.pos, false);
            yield return new WaitForSeconds(1.0f);
            var goat = Find("goat");
            p.pos = goat.pos + new Vector2(1.2f, 0);
            p.Face(Facing.Left);
            g.View.SnapTo(p.pos);
            Story.Run(goat.talk(), goat);
            yield return t.Shot("07-goat", 1.2f);
            while (Story.I.Running) yield return null;
            var gate = Map.Current.Find("temple_gate");
            p.pos = gate.basePos + new Vector2(0, -1.2f);
            p.Face(Facing.Up);
            g.View.SnapTo(p.pos);
            p.Notify(gate);
            yield return t.Shot("08-gate", 3.5f);
            while (Story.I.Running) yield return null;
            yield return t.Shot("09-gate-open", 0.3f);
        }
    }
}
