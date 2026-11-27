// A look round for the build machine: -wfScene look -wfLook "lowtown:480,330;lowtown:600,250;ashkel:480,200:dream"
// stands Azar at each spot in turn (map pixels) and photographs it, awake or in the dream.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class LookTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["look"] = Run;

        static IEnumerator Run(AutoTest t)
        {
            var g = Game.I;
            string spec = Boot.Arg("-wfLook") ?? "lowtown:480,330";
            string last = null;
            int n = 0;
            foreach (var item in spec.Split(';'))
            {
                var parts = item.Split(':');
                if (parts.Length < 2) continue;
                var xy = parts[1].Split(',');
                float x = float.Parse(xy[0], System.Globalization.CultureInfo.InvariantCulture), y = float.Parse(xy[1], System.Globalization.CultureInfo.InvariantCulture);
                if (parts[0] != last)
                {
                    g.EnterMap(parts[0], null);
                    Fade.Set(0);
                    last = parts[0];
                    yield return new WaitForSeconds(0.4f);
                }
                var p = Player.I;
                Dream.I.SetInstant(false);
                // -wfGhost: he is not there at all, so nothing pushes him out of a wall the picture is centred on
                if (Boot.Flag("-wfGhost")) p.enabled = false;
                p.pos = Map.ToWorld(x, y);
                p.transform.position = new Vector3(p.pos.x, p.pos.y, 0);
                p.Face(Facing.Down);
                g.View.SnapTo(p.pos);
                yield return new WaitForSeconds(0.5f);
                g.View.SnapTo(p.pos);
                if (parts.Length > 2 && parts[2] == "dream")
                {
                    Dream.I.Drowsiness = 1;
                    Dream.I.Flip(p.pos, true);
                    yield return new WaitForSeconds(1.6f);
                }
                // standing somewhere can set a scene going; this is a look, not a playthrough
                if (Story.I && Story.I.Running) { Story.Abort(); p.SetState(Player.State.Free, "idle"); yield return new WaitForSeconds(0.2f); }
                if (Boot.Flag("-wfBare") && Hud.I) Hud.I.gameObject.SetActive(false);
                // -wfGhost: the place without him in it (for a picture of a whole town, taken a screen at a time)
                if (Boot.Flag("-wfGhost"))
                {
                    foreach (var sr in p.GetComponentsInChildren<SpriteRenderer>()) sr.enabled = false;
                    if (p.anim.model) p.anim.model.gameObject.SetActive(false);
                    if (p.lantern) p.lantern.gameObject.SetActive(false);
                    foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
                    yield return null;
                }
                yield return t.Shot($"{n:00}-{parts[0]}-{(int)x}-{(int)y}", 0.4f);
                n++;
            }
        }
    }
}
