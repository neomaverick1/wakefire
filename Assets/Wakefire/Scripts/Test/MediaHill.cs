// Staged moments from chapter two for the store page and the README: -wfScene media2.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class MediaHill
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["media2"] = Run;

        static Npc Find(string id) => Npc.All.Find(n => n && n.id == id);

        static IEnumerator Enter(string map, string spawn = null)
        {
            Game.I.EnterMap(map, spawn);
            Story.Abort();
            Fade.Set(0);
            Player.I.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.5f);
        }

        static void Frame(float x, float y)
        {
            var v = PixelView.I;
            v.target = null;
            v.SnapTo(Map.ToWorld(x, y));
        }

        static IEnumerator Said(AutoTest t, string shot, float after)
        {
            yield return t.Shot(shot, after);
            DialogueBox.AutoAdvance = 0.05f;
            float w = 0;
            while (Story.I.Running && w < 30f) { w += Time.deltaTime; yield return null; }
            DialogueBox.AutoAdvance = 30f;
        }

        static IEnumerator Run(AutoTest t)
        {
            foreach (var f in new[] { "key", "gate_open", "braziers", "item_shield", "item_oil", "item_lamp", "bigkey", "yard_bridge", "bull_seen", "bull_dead", "chapter_done",
                                      "ch2", "item_hillkey", "hill_gate", "met_namtar", "queue_passed" })
                Story.Set(f);
            Story.SetCount("vessels", 1);
            DialogueBox.AutoAdvance = 30f;
            // the queue across the road of the dead
            yield return Enter("necro_road", "south");
            var p = Player.I;
            Story.I.ApplyItems();
            p.health.hp = p.health.max;
            p.coins = 58;
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            var q = Find("queue_2");
            p.pos = Map.ToWorld(424, 318);
            p.Face(Facing.Up);
            Frame(420, 328);
            yield return new WaitForSeconds(0.6f);
            Story.Run(q.talk(), q);
            yield return Said(t, "09-the-queue", 3.2f);
            // the king's door, and his herald
            yield return Enter("necropolis", "south");
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            // (no words over this one: the front of the tomb is the picture)
            p.pos = Map.ToWorld(384, 150);
            p.Face(Facing.Up);
            Frame(372, 120);
            yield return t.Shot("10-kings-door", 1.2f);
            // the generals at their game
            var gen = Find("general_a");
            p.pos = gen.pos + new Vector2(1.2f, -1.6f);
            p.Face(Facing.Up);
            Frame(546, 474);
            yield return new WaitForSeconds(0.5f);
            Story.Run(gen.talk(), gen);
            yield return new WaitForSeconds(1.2f);
            DialogueBox.AutoAdvance = 0.05f;
            yield return new WaitForSeconds(0.25f);
            DialogueBox.AutoAdvance = 30f;
            yield return Said(t, "13-the-generals", 3.2f);
            // the hall of servants
            Story.Set("king_door");
            yield return Enter("tomb_1", "south");
            foreach (var e in Enemy.All.ToArray()) if (e is Scarab) Object.Destroy(e.gameObject);
            var sv = Find("servant_1");
            p.pos = sv.pos + new Vector2(0, -1.4f);
            p.Face(Facing.Up);
            Frame(420, 290);
            yield return new WaitForSeconds(0.6f);
            Story.Run(sv.talk(), sv);
            yield return Said(t, "11-hall-of-servants", 3.4f);
            // the king
            yield return Enter("tomb_3", "south");
            p.pos = Map.ToWorld(240, 140);
            p.Face(Facing.Up);
            Frame(240, 107);
            yield return new WaitForSeconds(0.8f);
            Story.Run(Story.Say("Kurashtar", "I AM KURASHTAR. MOUNTAIN OF FIRE AND JUDGEMENT.| I chose it myself.", "king"));
            yield return Said(t, "12-sleepless-king", 4.2f);
            // and the fight: the mace coming down
            var king = SleeplessKing.I;
            if (king)
            {
                yield return king.Rise();
                king.Begin();
                p.pos = king.pos + new Vector2(1.9f, -1.4f);
                p.Face(Facing.Left);
                PixelView.I.target = null;
                PixelView.I.SnapTo(king.pos + new Vector2(0.6f, -1.2f));
                float w = 0;
                while (king.StateName != "Slam" && w < 8f) { w += Time.deltaTime; yield return null; }
                yield return t.Shot("14-the-mace", 0.62f);
            }
        }
    }
}
