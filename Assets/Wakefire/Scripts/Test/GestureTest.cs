// The small acting: Azar nodding off, waking, yawning, catching himself; the sleepers of Ashkel.
// Run with -wfScene gestures.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class GestureTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["gestures"] = Run;

        static Npc Put(string id, Vector2 at, string sheet, string anim, Facing f = Facing.Down)
        {
            var n = Npc.Create(id, at, sheet, anim, WorldLayer.Both, f, false);
            n.turnsToTalk = false;
            return n;
        }

        static IEnumerator Run(AutoTest t)
        {
            var g = Game.I;
            var p = g.EnterMap("ashkel");
            foreach (var n in Npc.All) if (n) n.gameObject.SetActive(false);
            var c = Map.ToWorld(480, 200);
            p.pos = c + new Vector2(0, -2.2f);
            p.Face(Facing.Down);
            g.View.target = null;
            g.View.bounds = null;
            g.View.SnapTo(c + new Vector2(0, 0.6f));
            Put("a", c + new Vector2(-9.5f, 3.6f), "captain", "lean");
            Put("b", c + new Vector2(-7.4f, 3.6f), "captain", "sleep", Facing.Left);
            Put("c", c + new Vector2(-5.3f, 3.6f), "baker", "knead", Facing.Left);
            Put("d", c + new Vector2(-3.2f, 3.6f), "potter", "sleep");
            Put("e", c + new Vector2(-1.1f, 3.6f), "potter", "shrug");
            Put("f", c + new Vector2(1.0f, 3.6f), "oracle", "point", Facing.Left);
            Put("g", c + new Vector2(3.1f, 3.6f), "priest", "sigh");
            Put("h", c + new Vector2(5.2f, 3.6f), "captain_child", "cower");
            Put("i", c + new Vector2(7.3f, 3.6f), "captain_child", "idle");
            Put("j", c + new Vector2(9.4f, 3.6f), "sleeper_a", "talk");
            Put("k", c + new Vector2(-8.5f, 0.6f), "fisher", "lie");
            var w = Put("l", c + new Vector2(-5f, 0.4f), "sleeper_c", "sleepwalk", Facing.Right);
            w.route = new[] { c + new Vector2(-5f, 0.4f), c + new Vector2(-1.5f, 0.4f) };
            w.walkAnim = "sleepwalk";
            Put("m", c + new Vector2(4f, 0.6f), "sentinel", "idle", Facing.Left);
            Put("n", c + new Vector2(6.5f, 0.6f), "priest", "idle");
            Put("o", c + new Vector2(9f, 0.6f), "sleeper_b", "idle", Facing.Right);
            yield return new WaitForSeconds(1.0f);
            string[] acts = { "nod", "wake", "yawn", "idle_nod", "shrug", "point", "block", "use", "itemget", "doze" };
            float[] at = { 0.2f, 0.12f, 0.55f, 0.42f, 0.4f, 0.4f, 0.3f, 0.2f, 0.4f, 0.9f };
            for (int i = 0; i < acts.Length; i++)
            {
                p.SetState(Player.State.Cutscene, acts[i]);
                yield return new WaitForSeconds(at[i]);
                yield return t.Shot($"{i:00}-{acts[i]}");
                yield return new WaitForSeconds(0.5f);
                p.SetState(Player.State.Cutscene, "idle");
                yield return new WaitForSeconds(0.3f);
            }
        }
    }
}
