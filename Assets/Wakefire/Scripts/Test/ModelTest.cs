// Poses the hero through his moves for a contact sheet: standing each way, a stride, a swing,
// a roll, a blow taken. Run with -wfScene models; -wfMap picks the place.
using System.Collections;
using System.IO;
using UnityEngine;

namespace Wakefire
{
    public static class ModelTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["models"] = Run;

        static int shot;

        static IEnumerator Snap(AutoTest t, string name)
        {
            yield return t.Shot($"{shot++:00}-{name}");
        }

        static IEnumerator Hold(float gameSeconds)
        {
            for (float c = 0; c < gameSeconds; c += Time.deltaTime) yield return null;
        }

        static void Sheet(AutoTest t)
        {
            var rt = ModelStage.I ? ModelStage.I.sheet : null;
            if (!rt) return;
            var prev = RenderTexture.active;
            RenderTexture.active = rt;
            var tex = new Texture2D(rt.width, ModelStage.Cell * 2, TextureFormat.RGBA32, false);
            tex.ReadPixels(new Rect(0, 0, rt.width, ModelStage.Cell * 2), 0, 0);
            tex.Apply();
            RenderTexture.active = prev;
            File.WriteAllBytes(Path.Combine(t.dir, "stage.png"), tex.EncodeToPNG());
        }

        static IEnumerator Run(AutoTest t)
        {
            shot = 0;
            var g = Game.I;
            var p = g.EnterMap(Boot.Arg("-wfMap") ?? "ashkel");
            p.pos = Map.ToWorld(480, 196);
            g.View.target = null;
            g.View.bounds = null;
            g.View.SnapTo(p.pos + new Vector2(0, 1f));
            yield return new WaitForSeconds(0.6f);
            foreach (var f in new[] { Facing.Down, Facing.Left, Facing.Up, Facing.Right })
            {
                p.Face(f);
                yield return Hold(0.35f);
                yield return Snap(t, "idle");
            }
            Sheet(t);

            Time.timeScale = 0.2f;
            foreach (var dir in new[] { Vector2.right, Vector2.down, new Vector2(-1, 1).normalized })
            {
                var home = p.pos;
                Controls.Fake = dir;
                yield return Hold(0.25f);
                for (int i = 0; i < 6; i++)
                {
                    g.View.SnapTo(p.pos + new Vector2(0, 1f));
                    yield return Snap(t, "run");
                    yield return Hold(0.09f);
                }
                Controls.Fake = Vector2.zero;
                yield return Hold(0.3f);
                p.pos = home;
                g.View.SnapTo(p.pos + new Vector2(0, 1f));
            }

            foreach (var f in new[] { Facing.Right, Facing.Down })
            {
                p.Face(f);
                yield return Hold(0.3f);
                Controls.FakePress = Controls.Attack;
                yield return null;
                for (int i = 0; i < 6; i++)
                {
                    yield return Snap(t, "attack");
                    yield return Hold(0.035f);
                }
                yield return Hold(0.5f);
            }

            p.Face(Facing.Right);
            yield return Hold(0.2f);
            {
                var home = p.pos;
                Controls.Fake = Vector2.right;
                yield return null;
                Controls.FakePress = Controls.Roll;
                yield return null;
                for (int i = 0; i < 8; i++)
                {
                    g.View.SnapTo(p.pos + new Vector2(0, 1f));
                    yield return Snap(t, "roll");
                    yield return Hold(0.035f);
                }
                Controls.Fake = Vector2.zero;
                yield return Hold(0.5f);
                p.pos = home;
                g.View.SnapTo(p.pos + new Vector2(0, 1f));
            }

            p.Face(Facing.Down);
            yield return Hold(0.2f);
            p.SetState(Player.State.Use, "use");
            yield return Hold(0.12f);
            yield return Snap(t, "use");
            yield return Hold(0.5f);
            p.SetState(Player.State.Cutscene, "death");
            for (int i = 0; i < 4; i++)
            {
                yield return Hold(0.3f);
                yield return Snap(t, "death");
            }
            Time.timeScale = 1f;
            Controls.Fake = null;
        }
    }
}
