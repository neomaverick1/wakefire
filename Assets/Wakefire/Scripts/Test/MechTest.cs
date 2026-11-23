// Mechanics on the build machine, driven through the real controls: crossing the sea on the
// road of moonlight, running out of dream over the chasm (and falling), crossing it with the
// Night Oil, the block and the plate, the dream wall, and the shield against fire.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class MechTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["mech"] = Run;

        static IEnumerator WalkPath(Player p, Vector2[] pts, float timeout = 20f)
        {
            float t = 0;
            foreach (var target in pts)
            {
                while ((target - p.pos).magnitude > 0.18f && t < timeout)
                {
                    if (p.state == Player.State.Free) Controls.Fake = (target - p.pos).normalized;
                    else Controls.Fake = Vector2.zero;
                    t += Time.deltaTime;
                    yield return null;
                }
            }
            Controls.Fake = Vector2.zero;
        }

        static Vector2[] Px(params float[] xy)
        {
            var a = new Vector2[xy.Length / 2];
            for (int i = 0; i < a.Length; i++) a[i] = Map.ToWorld(xy[i * 2], xy[i * 2 + 1]);
            return a;
        }

        static IEnumerator Enter(string map, string spawn)
        {
            Game.I.EnterMap(map, spawn);
            Fade.Set(0);
            yield return new WaitForSeconds(0.3f);
        }

        static IEnumerator NodAndWait(Player p)
        {
            Dream.I.Drowsiness = 1;
            p.NodOff();
            float t = 0;
            while (p.state != Player.State.Free && t < 2f) { t += Time.deltaTime; yield return null; }
        }

        /// <summary>Put him at a place in a room of a floor of rooms (pixels from the room's corner), and let the
        /// picture slide to it before he is asked to do anything.</summary>
        static IEnumerator InRoom(Player p, string id, float x, float y)
        {
            var r = Rooms.I.Find(id);
            var at = new Vector2(r.rect.xMin + x / 16f, r.rect.yMax - y / 16f);
            p.pos = at;
            yield return null; yield return null;
            for (float s = 0; s < 3f && (Rooms.Sliding || Game.Busy || (Story.I && Story.I.Running)); s += Time.deltaTime) yield return null;
            p.pos = at;
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.15f);
        }

        static IEnumerator Run(AutoTest t)
        {
            DialogueBox.AutoAdvance = 0.3f;
            var g = Game.I;
            // 1. the sea bridge with ordinary naps
            yield return Enter("cliffs", "west");
            var p = Player.I;
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            p.pos = Map.ToWorld(620, 456);
            yield return NodAndWait(p);
            float t0 = Time.time;
            yield return WalkPath(p, Px(720, 456, 720, 292, 830, 292, 850, 200));
            t.Note($"sea bridge: reached={Vector2.Distance(p.pos, Map.ToWorld(850, 200)) < 0.5f} hp={p.health.hp} time={Time.time - t0:F1} drowsy={Dream.I.Drowsiness:F2}");
            yield return t.Shot("01-cove", 0.2f);
            // open the chest with the oil
            var chest = Map.Current.Find("cove_oil");
            p.pos = chest.basePos + new Vector2(0, -0.9f);
            p.Face(Facing.Up);
            Game.CommonProp(chest);
            float w = 0;
            while ((Story.I.Running || w < 0.2f) && w < 15f) { w += Time.deltaTime; yield return null; }
            t.Note("oil=" + Story.Has("item_oil") + " seconds=" + Dream.I.Seconds);
            Dream.I.SetInstant(false);
            // 2. the chasm without the oil: run out of dream and fall
            Story.Flags.Remove("item_oil");
            Story.I.ApplyItems();
            yield return Enter("temple_yard", "south");
            p.pos = Map.ToWorld(440, 350);
            int hp0 = p.health.hp;
            yield return NodAndWait(p);
            yield return WalkPath(p, Px(440, 306, 180, 306, 180, 262, 440, 262, 440, 218, 320, 218, 320, 180), 14f);
            float w2 = 0;
            while (p.state != Player.State.Free && w2 < 4f) { w2 += Time.deltaTime; yield return null; }
            t.Note($"chasm without oil: hp {hp0}->{p.health.hp} at {p.pos} safe={p.lastSafe}");
            yield return t.Shot("02-fell", 0.3f);
            // 3. with the oil
            Story.Set("item_oil");
            Story.I.ApplyItems();
            p.pos = Map.ToWorld(440, 350);
            yield return new WaitForSeconds(3f);
            Dream.I.Drowsiness = 1;
            yield return NodAndWait(p);
            t0 = Time.time;
            yield return WalkPath(p, Px(440, 306, 180, 306, 180, 262, 440, 262, 440, 218, 320, 218, 320, 160), 16f);
            t.Note($"chasm with oil: at {p.pos} time={Time.time - t0:F1} drowsy={Dream.I.Drowsiness:F2} bridgeflag={Story.Has("yard_bridge")}");
            yield return t.Shot("03-crossed", 0.5f);
            Dream.I.SetInstant(false);
            w = 0;
            while (Story.I.Running && w < 15f) { w += Time.deltaTime; yield return null; }
            yield return new WaitForSeconds(0.6f);
            t.Note("bridge lowered=" + Story.Has("yard_bridge"));
            // 4. the block and the plate
            yield return Enter("zig_1", "south");
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            // (the weighing room, west of the first hall: he leans on the stone from its east side)
            yield return InRoom(p, "west", 258, 150);
            p.Face(Facing.Left);
            Controls.Fake = Vector2.left;
            yield return new WaitForSeconds(2.6f);
            Controls.Fake = Vector2.zero;
            var blk = Map.Current.Find("z1_block");
            var plate = Map.Current.Find("z1_plate");
            t.Note($"block {(blk.basePos - plate.basePos).magnitude:0.0} tiles from the plate, plate pressed={Story.Has("on_z1_plate")}");
            yield return t.Shot("04-plate", 1.0f);
            // 5. through the dream wall to the key (the room east of the first hall)
            yield return InRoom(p, "east", 220, 128);
            yield return NodAndWait(p);
            Controls.Fake = Vector2.right;
            yield return new WaitForSeconds(0.9f);
            Controls.Fake = Vector2.zero;
            t.Note($"dream wall: at {p.pos * 16}");
            yield return t.Shot("05-dreamwall", 0.3f);
            Dream.I.SetInstant(false);
            // 6. the shield against the bull's head
            yield return Enter("zig_2", "south");
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            Story.Set("item_shield");
            Story.I.ApplyItems();
            // (the bull's gate: north-east room of the floor; its head stands in the gap of the wall across it)
            yield return InRoom(p, "gate", 208, 196);
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            p.Face(Facing.Up);
            // the shield has to be held up now: the action button, with nothing in front of him
            Controls.FakeHold = Controls.Interact;
            for (float held = 0; held < 7f && !Story.Has("z2_bull"); held += Time.deltaTime)
            {
                if (p.state == Player.State.Free) { p.Face(Facing.Up); Controls.FakePress = Controls.Interact; }
                yield return null;
            }
            Controls.FakeHold = null;
            t.Note("bull head broken=" + Story.Has("z2_bull") + " hp=" + p.health.hp + " guarding=" + p.Guarding);
            yield return t.Shot("06-bullhead", 0.2f);
        }
    }
}
