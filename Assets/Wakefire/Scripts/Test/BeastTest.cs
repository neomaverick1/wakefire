// The animals side by side, doing what they do, for a contact sheet. Run with -wfScene beasts.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class BeastTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["beasts"] = Run;

        static Npc Put(string id, Vector2 at, string sheet, string anim, Facing f = Facing.Down)
        {
            var n = Npc.Create(id, at, sheet, anim, WorldLayer.Both, f, false);
            n.turnsToTalk = false;
            return n;
        }

        static Npc Walker(string id, Vector2 a, Vector2 b, string sheet, string anim, float speed)
        {
            var n = Put(id, a, sheet, anim, Facing.Right);
            n.route = new[] { a, b };
            n.walkAnim = anim;
            n.pauseAnim = "idle";
            n.walkSpeed = speed;
            n.pauseTime = 0.3f;
            return n;
        }

        static IEnumerator Run(AutoTest t)
        {
            var g = Game.I;
            var p = g.EnterMap("ashkel");
            foreach (var n in Npc.All) if (n) n.gameObject.SetActive(false);
            var c = Map.ToWorld(480, 200);
            p.pos = c + new Vector2(0, -2.6f);
            p.Face(Facing.Up);
            g.View.target = null;
            g.View.bounds = null;
            g.View.SnapTo(c + new Vector2(0, 0.2f));

            Put("g1", c + new Vector2(-9.5f, 4.2f), "goat", "stare", Facing.Right);
            Put("g2", c + new Vector2(-7.0f, 4.2f), "goat", "eat", Facing.Left);
            var bleater = Put("g3", c + new Vector2(-4.4f, 4.2f), "goat", "idle", Facing.Down);
            Walker("g4", c + new Vector2(-10f, 2.2f), c + new Vector2(-4.5f, 2.2f), "goat", "walk", 1.2f);
            Put("d1", c + new Vector2(-1.5f, 4.2f), "dog", "sleep", Facing.Left);
            Put("d2", c + new Vector2(0.6f, 4.2f), "dog", "idle", Facing.Down);
            Walker("d3", c + new Vector2(-2.5f, 2.2f), c + new Vector2(2.5f, 2.2f), "dog", "walk", 2.2f);
            Put("j1", c + new Vector2(3.4f, 4.2f), "jackal", "idle", Facing.Left);
            Put("j2", c + new Vector2(5.6f, 4.2f), "jackal", "crouch", Facing.Down);
            Walker("j3", c + new Vector2(3.5f, 2.2f), c + new Vector2(10f, 2.2f), "jackal", "run", 4.6f);
            var leaper = Put("j4", c + new Vector2(8.2f, 4.2f), "jackal", "idle", Facing.Left);
            Put("c1", c + new Vector2(-9f, -0.4f), "crab", "idle");
            Walker("c2", c + new Vector2(-7f, -0.4f), c + new Vector2(-3.5f, -0.4f), "crab", "walk", 2.6f);
            var snapper = Put("c3", c + new Vector2(-9f, -2.2f), "crab", "idle");
            Put("m1", c + new Vector2(4f, -0.2f), "moth", "fly");
            Put("m2", c + new Vector2(5.5f, -0.6f), "moth", "fly");
            Walker("s1", c + new Vector2(6.5f, -2.4f), c + new Vector2(10.5f, -2.4f), "sentinel", "walk", 1.4f);
            yield return new WaitForSeconds(1.2f);
            for (int i = 0; i < 6; i++)
            {
                bleater.Play("bleat", true);
                snapper.Play("attack", true);
                leaper.Play("lunge", true);
                yield return new WaitForSeconds(0.22f + i * 0.04f);
                yield return t.Shot($"a{i}");
                yield return new WaitForSeconds(0.5f);
            }

            foreach (var n in Npc.All) if (n) n.gameObject.SetActive(false);
            Put("b1", c + new Vector2(-8f, 3.2f), "bull", "idle", Facing.Down);
            Put("b2", c + new Vector2(-2.5f, 3.2f), "bull", "idle", Facing.Left);
            Put("b3", c + new Vector2(3.5f, 3.2f), "bull", "stun", Facing.Right);
            var shooter = Put("b4", c + new Vector2(8.5f, 3.2f), "bull", "idle", Facing.Down);
            Walker("b5", c + new Vector2(-9f, -1.2f), c + new Vector2(-1f, -1.2f), "bull", "walk", 2.2f);
            Walker("b6", c + new Vector2(1f, -2.6f), c + new Vector2(10f, -2.6f), "bull", "charge", 7.5f);
            var dying = Put("b7", c + new Vector2(4.5f, 0.2f), "bull", "idle", Facing.Left);
            yield return new WaitForSeconds(1.0f);
            for (int i = 0; i < 4; i++)
            {
                shooter.Play("shoot", true);
                if (i == 2) dying.SetIdle("death");
                yield return new WaitForSeconds(0.25f + i * 0.05f);
                yield return t.Shot($"b{i}");
                yield return new WaitForSeconds(0.45f);
            }
        }
    }
}
