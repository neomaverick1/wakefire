// The people and creatures of the Hill of Sleepers lined up for a close look, and the king in
// every mood: -wfScene hillshow.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class HillShow
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["hillshow"] = Run;

        static Npc Put(string id, Vector2 at, string look, string anim, Facing f, bool ghost = true, float lift = 0)
        {
            var n = Npc.Create(id, at, "priest", anim, ghost ? WorldLayer.Waking : WorldLayer.Both, f, false, look);
            n.turnsToTalk = false;
            n.lift = lift;
            if (ghost) n.Ghost();
            if (ghost && look == "king")
            {
                // the king's own, lighter touch of the grave
                var m = new Material(Npc.GhostMat);
                m.SetFloat("_Ghost", 0.36f);
                m.SetVector("_GhostFade", new Vector4(0.285f, 0.42f, 0, 0));
                n.anim.sr.sharedMaterial = m;
            }
            return n;
        }

        static IEnumerator Run(AutoTest t)
        {
            var g = Game.I;
            Story.Set("king_done");                 // an empty throne room to stand people in
            var p = g.EnterMap("tomb_3", "south");
            Story.Abort();
            Fade.Set(0);
            foreach (var n in Npc.All) if (n) n.gameObject.SetActive(false);
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            if (Hud.I) Hud.I.gameObject.SetActive(false);
            var c = Map.ToWorld(240, 250);
            p.pos = c + new Vector2(0, -6.2f);
            p.Face(Facing.Up);
            g.View.target = null;
            g.View.bounds = null;
            g.View.SnapTo(c + new Vector2(0, 0.6f));
            // the king: seated (on his throne), standing, striding, mace up, casting, reeling, kneeling
            var tm = Map.Current.Marker("throne");
            var seated = Put("k0", Map.ToWorld(tm.x, tm.y), "king", "sit", Facing.Down, true, 0.62f);
            seated.orderBias = 48;
            Put("k1", c + new Vector2(-7.5f, 3.2f), "king", "idle", Facing.Down);
            Put("k2", c + new Vector2(-4.6f, 3.2f), "king", "walk", Facing.Right);
            Put("k3", c + new Vector2(4.6f, 3.2f), "king", "slam", Facing.Left);
            Put("k4", c + new Vector2(7.6f, 3.2f), "king", "cast", Facing.Down);
            Put("k5", c + new Vector2(-7.4f, -0.4f), "king", "reel", Facing.Down);
            Put("k6", c + new Vector2(-4.4f, -0.4f), "king", "kneel", Facing.Down);
            // the dead
            Put("d1", c + new Vector2(-1.6f, -0.4f), "namtar", "wait", Facing.Down);
            Put("d2", c + new Vector2(0.4f, -0.4f), "gran", "idle", Facing.Down);
            Put("d3", c + new Vector2(2.4f, -0.4f), "belu", "idle", Facing.Left);
            Put("d4", c + new Vector2(4.4f, -0.4f), "poet", "idle", Facing.Down);
            Put("d5", c + new Vector2(6.4f, -0.4f), "herald", "lamp", Facing.Left);
            Put("d6", c + new Vector2(8.4f, -0.4f), "servant", "wait", Facing.Down);
            Put("d7", c + new Vector2(-8.0f, -3.6f), "general_a", "sit", Facing.Right);
            Put("d8", c + new Vector2(-5.6f, -3.6f), "general_b", "idle", Facing.Down);
            // the living: thieves
            Put("r1", c + new Vector2(-3.2f, -3.6f), "robber", "idle", Facing.Down, false);
            Put("r2", c + new Vector2(-1.2f, -3.6f), "robber_b", "idle", Facing.Right, false);
            // and what bites
            var sh = Shade.Spawn(c + new Vector2(1.6f, -3.6f));
            var us = Ushabti.Spawn(c + new Vector2(4.0f, -3.6f));
            var sc = Scarab.Spawn(c + new Vector2(6.2f, -3.6f));
            var sc2 = Scarab.Spawn(c + new Vector2(7.6f, -3.2f));
            foreach (var e in new Enemy[] { sh, us, sc, sc2 }) e.enabled = false;
            yield return new WaitForSeconds(1.0f);
            yield return t.Shot("show-a", 0.2f);
            yield return t.Shot("show-b", 0.5f);
            g.View.SnapTo(Map.ToWorld(tm.x, tm.y) + new Vector2(0, -1.0f));
            yield return t.Shot("show-throne", 0.5f);
        }
    }
}
