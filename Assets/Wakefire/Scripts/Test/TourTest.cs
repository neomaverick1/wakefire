// A tour of the whole chapter for the build machine: the title, every place, the people who
// matter, the dream bridges, the dungeon floors, the Brazen Bull and the ending.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class TourTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["tour"] = Run;

        static Npc Find(string id) => Npc.All.Find(n => n && n.id == id);

        static IEnumerator Wait(float s) { yield return new WaitForSeconds(s); }

        static IEnumerator Enter(string map, string spawn = null)
        {
            Game.I.EnterMap(map, spawn);
            Fade.Set(0);
            yield return new WaitForSeconds(0.4f);
        }

        static IEnumerator Run(AutoTest t)
        {
            var g = Game.I;
            Title.Show();
            yield return t.Shot("00-title", 1.0f);
            Object.Destroy(Title.I.gameObject);
            DialogueBox.AutoAdvance = 0.6f;
            yield return Enter("lowtown", "north");
            var p = Player.I;
            p.pos = Map.ToWorld(480, 330);
            g.View.SnapTo(p.pos);
            yield return t.Shot("01-lowtown", 0.6f);
            var ummi = Find("ummi_self");
            p.pos = ummi.pos + new Vector2(0, -1.2f);
            p.Face(Facing.Up);
            g.View.SnapTo(p.pos);
            Dream.I.Flip(p.pos, true);
            yield return Wait(1.0f);
            DialogueBox.AutoAdvance = 30f;
            Story.Run(ummi.talk(), ummi);
            yield return t.Shot("02-ummi", 2.4f);
            DialogueBox.AutoAdvance = 0.05f;
            while (Story.I.Running) yield return null;
            Dream.I.SetInstant(false);
            yield return Enter("cliffs", "west");
            p.pos = Map.ToWorld(300, 470);
            g.View.SnapTo(p.pos);
            yield return t.Shot("03-cliffs", 0.8f);
            p.pos = Map.ToWorld(630, 456);
            g.View.SnapTo(p.pos);
            Dream.I.Drowsiness = 1;
            Dream.I.Flip(p.pos, true);
            yield return t.Shot("04-sea-bridge", 1.3f);
            Dream.I.SetInstant(false);
            yield return Enter("terraces", "east");
            p.pos = Map.ToWorld(560, 330);
            g.View.SnapTo(p.pos);
            yield return t.Shot("05-terraces", 1.6f);
            yield return Enter("temple_yard", "south");
            p.pos = Map.ToWorld(320, 420);
            g.View.SnapTo(Map.ToWorld(320, 300));
            g.View.target = null;
            yield return t.Shot("06-yard", 0.6f);
            Dream.I.Drowsiness = 1;
            Dream.I.Flip(p.pos, true);
            yield return t.Shot("07-yard-dream", 1.6f);
            Dream.I.SetInstant(false);
            g.View.target = p.transform;
            yield return Enter("zig_1", "south");
            yield return t.Shot("08-zig1", 1.0f);
            yield return Enter("zig_2", "south");
            p.pos = Map.ToWorld(256, 240);
            Story.Set("item_shield");
            Story.I.ApplyItems();
            p.Face(Facing.Up);
            yield return t.Shot("09-zig2", 2.2f);
            yield return Enter("zig_3", "south");
            yield return Wait(0.3f);
            p.pos = Map.ToWorld(240, 280);
            yield return Wait(3.5f);
            yield return t.Shot("10-boss", 2.0f);
            var bull = BrazenBull.I;
            t.Note("boss=" + (bull != null));
            if (bull)
            {
                for (int i = 0; i < 20 && !bull.health.Dead; i++)
                {
                    bull.Hit(new HitInfo { damage = 2, from = bull.pos + Vector2.down, kind = HitKind.Reflected });
                    yield return Wait(0.25f);
                }
            }
            yield return Wait(4.0f);
            yield return t.Shot("11-ending", 3.0f);
            yield return Wait(14f);
            yield return t.Shot("12-cards", 2.0f);
            t.Note("flags=" + string.Join(",", Story.Flags));
        }
    }
}
