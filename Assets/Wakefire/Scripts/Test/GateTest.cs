// Test run for the Gate Square on a build machine: walks Azar about, lights a brazier, cuts a
// bush and nods off into the dream, saving screenshots along the way.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class GateTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["gate"] = Run;

        static IEnumerator Walk(Player p, Vector2 dir, float seconds)
        {
            float t = 0;
            while (t < seconds)
            {
                p.pos = Solids.Move(p.pos, dir.normalized * p.speed * Time.deltaTime, p.half, p);
                p.Face(dir.x < -0.1f ? Facing.Left : dir.x > 0.1f ? Facing.Right : dir.y > 0 ? Facing.Up : Facing.Down);
                p.anim.Play("run", p.facing);
                t += Time.deltaTime;
                yield return null;
            }
            p.anim.Play("idle", p.facing);
        }

        static IEnumerator Run(AutoTest t)
        {
            var g = Game.I;
            var p = g.EnterMap("ashkel");
            p.coins = 27;
            yield return t.Shot("01-square", 1.2f);
            // walk to the left brazier and light it
            var b = Map.Current.props.Find(x => x.data.id == "square_0");
            p.pos = b.basePos + new Vector2(0.9f, 0.3f);
            p.Face(Facing.Left);
            yield return new WaitForSeconds(0.3f);
            b.Ignite();
            Map.Current.props.Find(x => x.data.id == "square_1").Ignite();
            yield return t.Shot("02-lit", 0.8f);
            p.pos = Map.ToWorld(470, 214);
            yield return Walk(p, Vector2.down, 0.5f);
            yield return t.Shot("03-run", 0.05f);
            p.anim.Play("attack1", Facing.Down, true);
            yield return t.Shot("04-attack", 0.12f);
            yield return new WaitForSeconds(0.6f);
            Dream.I.Flip(p.pos, true);
            yield return t.Shot("05-ring", 0.25f);
            yield return t.Shot("06-dream", 1.4f);
        }
    }
}
