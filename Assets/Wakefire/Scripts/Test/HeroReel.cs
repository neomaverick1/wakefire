// Azar alone in the Gate Square, put through his paces for a screen recording: running every
// way, turning, the three-cut combo, rolls, holding out the Wakefire. Run with -wfScene hero.
using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;

namespace Wakefire
{
    public static class HeroReel
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["hero"] = Run;

        static IEnumerator Go(Vector2 dir, float seconds)
        {
            Controls.Fake = dir.sqrMagnitude > 1 ? dir.normalized : dir;
            yield return new WaitForSeconds(seconds);
        }

        static IEnumerator Press(InputAction a, float after)
        {
            Controls.FakePress = a;
            yield return new WaitForSeconds(after);
        }

        static IEnumerator Run(AutoTest t)
        {
            Fade.Set(1);
            var g = Game.I;
            var p = g.EnterMap(Boot.Arg("-wfMap") ?? "ashkel");
            foreach (var n in Npc.All) if (n) n.gameObject.SetActive(false);
            p.pos = Map.ToWorld(480, 200);
            p.Face(Facing.Down);
            g.View.SnapTo(p.pos);
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(2.2f);                 // the recorder starts
            yield return Fade.In(0.4f);
            yield return new WaitForSeconds(1.0f);

            yield return Go(Vector2.right, 0.9f);
            yield return Go(new Vector2(1, -1), 0.5f);
            yield return Go(Vector2.left, 1.3f);
            yield return Go(new Vector2(-1, 1), 0.5f);
            yield return Go(Vector2.up, 0.4f);
            yield return Go(Vector2.right, 0.75f);
            yield return Go(Vector2.zero, 0.7f);

            for (int i = 0; i < 3; i++) yield return Press(Controls.Attack, 0.27f);
            yield return new WaitForSeconds(0.7f);
            p.Face(Facing.Down);
            yield return new WaitForSeconds(0.25f);
            for (int i = 0; i < 3; i++) yield return Press(Controls.Attack, 0.27f);
            yield return new WaitForSeconds(0.6f);

            Controls.Fake = Vector2.left;
            yield return new WaitForSeconds(0.3f);
            yield return Press(Controls.Roll, 0.5f);
            Controls.Fake = new Vector2(1, 1).normalized;
            yield return new WaitForSeconds(0.25f);
            yield return Press(Controls.Roll, 0.5f);
            Controls.Fake = Vector2.down;
            yield return new WaitForSeconds(0.25f);
            yield return Press(Controls.Roll, 0.55f);

            // a wide loop, to show him lean into the turn and the cape follow
            for (float a = 0; a < 2.6f; a += Time.deltaTime)
            {
                float ang = -Mathf.PI * 0.5f + a * 2.6f;
                Controls.Fake = new Vector2(Mathf.Cos(ang), Mathf.Sin(ang));
                yield return null;
            }
            yield return Go(Vector2.zero, 0.5f);
            p.Face(Facing.Down);
            yield return new WaitForSeconds(0.3f);
            yield return Press(Controls.Item, 1.0f);
            yield return new WaitForSeconds(1.4f);
            yield return Fade.Out(0.4f);
            Controls.Fake = null;
        }
    }
}
