// A walk through the city for a screen recording: up the processional way to the Temple Gate,
// across the night market, a nod into the dream; then the lower town's market street and the
// pier under the cliffs. Run with -wfScene world.
using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Wakefire
{
    public static class WorldReel
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["world"] = Run;

        static IEnumerator Go(Vector2 dir, float seconds)
        {
            Controls.Fake = dir.sqrMagnitude > 1 ? dir.normalized : dir;
            yield return new WaitForSeconds(seconds);
        }

        /// <summary>Runs towards a spot on the map (pixels) until he is there, or the time is up.</summary>
        static IEnumerator To(float x, float y, float limit = 6f)
        {
            Vector2 goal = Map.ToWorld(x, y);
            for (float t = 0; t < limit; t += Time.deltaTime)
            {
                Vector2 d = goal - Player.I.pos;
                if (d.magnitude < 0.25f) break;
                Controls.Fake = d.normalized;
                yield return null;
            }
            Controls.Fake = Vector2.zero;
        }

        static IEnumerator Press(InputAction a, float after)
        {
            Controls.FakePress = a;
            yield return new WaitForSeconds(after);
        }

        static IEnumerator Cut(string map, float x, float y, Facing f)
        {
            yield return Fade.Out(0.3f);
            var g = Game.I;
            Dream.I.SetInstant(false);
            var p = g.EnterMap(map, null);
            p.pos = Map.ToWorld(x, y);
            p.Face(f);
            g.View.SnapTo(p.pos);
            Controls.Fake = Vector2.zero;
            // whatever would bite him before the picture comes up stays out of this one
            foreach (var e in Object.FindObjectsByType<Enemy>(FindObjectsSortMode.None))
                if (e && ((Vector2)e.transform.position - p.pos).magnitude < 5f) e.gameObject.SetActive(false);
            yield return new WaitForSeconds(0.5f);
            g.View.SnapTo(p.pos);
            yield return Fade.In(0.3f);
        }

        static IEnumerator Run(AutoTest t)
        {
            Fade.Set(1);
            var g = Game.I;
            var p = g.EnterMap("ashkel");
            p.pos = Map.ToWorld(480, 452);
            p.Face(Facing.Up);
            g.View.SnapTo(p.pos);
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(2.2f);                 // the recorder starts
            yield return Fade.In(0.4f);
            yield return new WaitForSeconds(0.6f);

            // up the processional way to the gate
            yield return To(480, 250);
            yield return To(500, 130);
            yield return Go(Vector2.zero, 0.9f);
            // across the square into the night market
            yield return To(590, 200);
            yield return To(700, 190);
            yield return Go(Vector2.zero, 0.5f);
            p.Face(Facing.Up);
            yield return new WaitForSeconds(0.6f);
            // nod off: the ring of the dream sweeps over the market
            Dream.I.Drowsiness = 1;
            p.NodOff();
            yield return new WaitForSeconds(3.2f);
            yield return To(640, 250);
            yield return Go(Vector2.zero, 0.8f);

            // the lower town: along the market street
            yield return Cut("lowtown", 330, 322, Facing.Right);
            yield return To(470, 322);
            yield return To(480, 250);
            yield return To(560, 200);
            yield return Go(Vector2.zero, 0.7f);
            yield return To(500, 330);
            yield return To(640, 326);
            for (int i = 0; i < 3; i++) yield return Press(Controls.Attack, 0.27f);
            yield return new WaitForSeconds(0.6f);

            // the pier under the cliffs
            yield return Cut("cliffs", 300, 470, Facing.Right);
            yield return To(430, 462);
            yield return To(520, 456);
            yield return To(620, 456);
            yield return Go(Vector2.zero, 1.4f);
            yield return Fade.Out(0.4f);
            Controls.Fake = null;
        }
    }
}
