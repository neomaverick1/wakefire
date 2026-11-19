// The humour reel: the funniest moments of the chapter played back to back in real time, for a
// screen recording. Run with -wfScene reel; it takes no screenshots of its own.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class ReelTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["reel"] = Run;

        static Npc Find(string id) => Npc.All.Find(n => n && n.id == id);

        static IEnumerator Enter(string map, string spawn = null)
        {
            Fade.Set(1);
            Game.I.EnterMap(map, spawn);
            yield return new WaitForSeconds(0.15f);
            yield return Fade.In(0.35f);
        }

        static IEnumerator Cut()
        {
            yield return new WaitForSeconds(0.4f);
            yield return Fade.Out(0.35f);
        }

        static void Stage(Npc n, Vector2 offset, Facing f, Vector2 look = default)
        {
            var p = Player.I;
            p.pos = n.pos + offset;
            p.Face(f);
            p.SetState(Player.State.Free, "idle");
            PixelView.I.target = null;
            PixelView.I.SnapTo(n.pos + offset * 0.5f + new Vector2(0, -0.4f) + look);
        }

        static IEnumerator Talk(Npc n, float after = 0.5f)
        {
            if (!n) yield break;
            Story.Run(n.talk(), n);
            yield return null;
            while (Story.I.Running) yield return null;
            yield return new WaitForSeconds(after);
        }

        static IEnumerator Dreaming()
        {
            Dream.I.Drowsiness = 1;
            Dream.I.Seconds = 9999;
            Dream.I.Flip(Player.I.pos, true);
            yield return new WaitForSeconds(1.4f);
        }

        static IEnumerator Run(AutoTest t)
        {
            DialogueBox.AutoAdvance = 1.6f;
            Fade.Set(1);
            yield return new WaitForSeconds(2.5f);                  // the recorder starts
            var p = Player.I;

            // the goat, who is always awake
            yield return Enter("ashkel", "south");
            p = Player.I;
            var goat = Find("goat");
            Stage(goat, new Vector2(1.4f, 0), Facing.Left);
            yield return new WaitForSeconds(0.6f);
            for (int i = 0; i < 4; i++) yield return Talk(goat, 0.25f);
            yield return Cut();

            // Captain Dur, asleep on his feet with the key
            var dur = Find("dur");
            Stage(dur, new Vector2(0, -1.3f), Facing.Up);
            yield return Fade.In(0.3f);
            yield return new WaitForSeconds(0.3f);
            yield return Talk(dur, 0.2f);
            yield return Talk(dur, 0.4f);
            // ...and in his dream, Dur at six
            yield return Dreaming();
            yield return Talk(Find("dur_child"), 0.4f);
            yield return Cut();

            // the widow and her husband's figs
            var walker = Find("walker_self");
            Dream.I.SetInstant(false);
            if (walker)
            {
                Stage(walker, new Vector2(1.3f, 0), Facing.Left);
                yield return Fade.In(0.3f);
                yield return Dreaming();
                yield return Talk(walker, 0.4f);
            }
            yield return Cut();
            Dream.I.SetInstant(false);

            // the lower town, all of it dreaming out loud
            yield return Enter("lowtown", "north");
            p = Player.I;
            Stage(Find("taxman"), new Vector2(1.3f, 0), Facing.Left);
            yield return Dreaming();
            yield return Talk(Find("taxman_self"), 0.4f);
            foreach (var id in new[] { "lover", "dog", "hesha" })
            {
                var body = Find(id);
                if (!body) continue;
                yield return Fade.Out(0.25f);
                Dream.I.SetInstant(false);
                Stage(body, new Vector2(id == "dog" ? 1.4f : 1.3f, 0), Facing.Left);
                yield return Fade.In(0.25f);
                yield return Dreaming();
                yield return Talk(Find(id + "_self"), 0.4f);
            }
            yield return Cut();
            Dream.I.SetInstant(false);

            // the summit: what the high priest did, and who climbed four hundred steps to see it
            Story.Set("bull_dead");
            yield return Enter("zig_3", "south");
            Story.Flags.Remove("bull_dead");
            p = Player.I;
            p.pos = Map.ToWorld(240, 180);
            p.Face(Facing.Up);
            PixelView.I.target = p.transform;
            DialogueBox.AutoAdvance = 1.7f;
            Story.Run(Story.I.Ending());
            float clock = 0;
            while (Story.I.Running && clock < 80f) { clock += Time.deltaTime; yield return null; }
            yield return new WaitForSeconds(1.0f);
        }
    }
}
