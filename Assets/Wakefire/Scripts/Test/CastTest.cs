// Everyone in a place, one after another, awake and dreaming, for a contact sheet.
// Run with -wfScene cast -wfMap <map>.
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public static class CastTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["cast"] = Run;

        static IEnumerator Run(AutoTest t)
        {
            var g = Game.I;
            string map = Boot.Arg("-wfMap") ?? "ashkel";
            var p = g.EnterMap(map);
            g.View.target = null;
            g.View.bounds = null;
            p.pos += new Vector2(0, -40);                    // out of the picture
            yield return new WaitForSeconds(1.2f);
            int i = 0;
            var seen = new List<Npc>(Npc.All);
            foreach (var n in seen)
            {
                if (!n || n.layer == WorldLayer.Dream) continue;
                g.View.SnapTo(n.pos + new Vector2(0, 1f));
                yield return new WaitForSeconds(0.7f);
                yield return t.Shot($"{i++:00}-{n.id}");
            }
            Dream.I.Drowsiness = 1;
            Dream.I.Seconds = 9999;
            Dream.I.SetInstant(true);
            yield return new WaitForSeconds(0.5f);
            foreach (var n in seen)
            {
                if (!n || n.layer != WorldLayer.Dream) continue;
                g.View.SnapTo(n.pos + new Vector2(0, 1f));
                yield return new WaitForSeconds(0.5f);
                if (n.talk != null && n.turnsToTalk) { n.BeginTalk(n.pos + Vector2.down); }
                yield return new WaitForSeconds(0.5f);
                yield return t.Shot($"{i++:00}-{n.id}");
            }
            foreach (var e in Enemy.All)
            {
                if (!e) continue;
                g.View.SnapTo(e.pos + new Vector2(0, 1f));
                yield return new WaitForSeconds(0.4f);
                yield return t.Shot($"{i++:00}-{e.GetType().Name}");
            }
        }
    }
}
