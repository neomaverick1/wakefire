// The Brazen Bull on its own floor, from every side and in every mood, for a close look:
// -wfScene bull.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class BullShow
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["bull"] = Run;

        static Npc Put(string id, Vector2 at, string anim, Facing f)
        {
            var n = Npc.Create(id, at, "bull", anim, WorldLayer.Both, f, false);
            n.turnsToTalk = false;
            return n;
        }

        static IEnumerator Run(AutoTest t)
        {
            var g = Game.I;
            var p = g.EnterMap("zig_3");
            Story.Abort();
            Fade.Set(0);
            foreach (var n in Npc.All) if (n) n.gameObject.SetActive(false);
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            if (Hud.I) Hud.I.gameObject.SetActive(false);
            var c = Map.ToWorld(240, 240);
            p.pos = c + new Vector2(0, -5.2f);
            p.Face(Facing.Up);
            g.View.target = null;
            g.View.bounds = null;
            g.View.SnapTo(c + new Vector2(0, -0.3f));
            Put("b1", c + new Vector2(-8.5f, 3.4f), "idle", Facing.Down);
            Put("b2", c + new Vector2(-3.4f, 3.4f), "idle", Facing.Left);
            Put("b3", c + new Vector2(2.6f, 3.4f), "idle", Facing.Right);
            Put("b4", c + new Vector2(8.0f, 3.4f), "idle", Facing.Up);
            Put("b5", c + new Vector2(-8.0f, -1.6f), "walk", Facing.Right);
            Put("b6", c + new Vector2(-2.4f, -1.6f), "charge", Facing.Left);
            Put("b7", c + new Vector2(3.0f, -1.6f), "shoot", Facing.Down);
            Put("b8", c + new Vector2(8.2f, -1.6f), "stun", Facing.Left);
            yield return new WaitForSeconds(1.0f);
            yield return t.Shot("bull-a", 0.2f);
            yield return t.Shot("bull-b", 0.45f);
        }
    }
}
