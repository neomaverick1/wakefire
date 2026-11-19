// Staged moments for the store page and the README: each place at its best, captured on the
// build machine at an exact pixel scale.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class MediaTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["media"] = Run;

        static Npc Find(string id) => Npc.All.Find(n => n && n.id == id);

        static IEnumerator Enter(string map, string spawn = null)
        {
            Game.I.EnterMap(map, spawn);
            Fade.Set(0);
            yield return new WaitForSeconds(0.5f);
        }

        static void Frame(Vector2 mapPx)
        {
            var v = PixelView.I;
            v.target = null;
            v.SnapTo(Map.ToWorld(mapPx.x, mapPx.y));
        }

        static IEnumerator Run(AutoTest t)
        {
            var g = Game.I;
            DialogueBox.AutoAdvance = 30f;
            // the lower town: a sleeper's dream-self has something to say
            yield return Enter("lowtown", "north");
            var p = Player.I;
            p.coins = 34;
            var tax = Find("taxman_self");
            p.pos = tax.pos + new Vector2(1.1f, 0.1f);
            p.Face(Facing.Left);
            Frame(new Vector2(500, 300));
            Dream.I.Drowsiness = 1;
            Dream.I.Flip(p.pos, true);
            yield return new WaitForSeconds(0.25f);
            yield return t.Shot("m4-ring-town", 0.0f);
            yield return new WaitForSeconds(1.4f);
            Story.Run(tax.talk(), tax);
            yield return t.Shot("m5-taxman", 2.6f);
            DialogueBox.AutoAdvance = 0.05f;
            while (Story.I.Running) yield return null;
            Dream.I.SetInstant(false);
            DialogueBox.AutoAdvance = 30f;
            // the sea, and the road of moonlight across it
            yield return Enter("cliffs", "west");
            foreach (var e in Enemy.All.ToArray()) if (e && e.pos.x > 30) Object.Destroy(e.gameObject);
            p.pos = Map.ToWorld(720, 360);
            p.Face(Facing.Up);
            Frame(new Vector2(660, 380));
            Dream.I.Drowsiness = 1;
            Dream.I.Flip(p.pos, true);
            yield return new WaitForSeconds(1.6f);
            p.anim.Play("run", Facing.Up, true);
            yield return t.Shot("m6-sea-bridge", 0.2f);
            Dream.I.SetInstant(false);
            // the beach: crabs
            p.pos = Map.ToWorld(200, 470);
            p.Face(Facing.Right);
            Frame(new Vector2(240, 440));
            yield return new WaitForSeconds(1.2f);
            p.anim.Play("attack2", Facing.Right, true);
            yield return t.Shot("m7-crabs", 0.1f);
            // the terraces: jackals
            yield return Enter("terraces", "east");
            p.pos = Map.ToWorld(452, 300);
            Frame(new Vector2(440, 320));
            yield return new WaitForSeconds(2.4f);
            p.anim.Play("attack3", Facing.Left, true);
            yield return t.Shot("m8-jackals", 0.15f);
            // the temple yard in the dream
            yield return Enter("temple_yard", "south");
            p.pos = Map.ToWorld(300, 306);
            Frame(new Vector2(320, 250));
            Dream.I.Drowsiness = 1;
            Dream.I.Flip(p.pos, true);
            yield return new WaitForSeconds(1.6f);
            p.anim.Play("run", Facing.Left, true);
            yield return t.Shot("m9-yard-dream", 0.1f);
            Dream.I.SetInstant(false);
            // the gallery: the bull's head and the mirror shield
            yield return Enter("zig_2", "south");
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            Story.Set("item_shield");
            Story.I.ApplyItems();
            p.pos = Map.ToWorld(256, 250);
            p.Face(Facing.Up);
            Frame(new Vector2(256, 200));
            for (int i = 0; i < 6; i++) yield return t.Shot("m10-shield-" + i, 0.35f);
            // the Brazen Bull
            Story.Set("bull_dead");
            yield return Enter("zig_3", "south");
            Story.Flags.Remove("bull_dead");
            var bull = BrazenBull.Spawn(Map.ToWorld(240, 196));
            p.pos = Map.ToWorld(240, 268);
            p.Face(Facing.Up);
            p.health.invulnerable = 999;
            Frame(new Vector2(240, 176));
            yield return new WaitForSeconds(0.4f);
            // the bull breathes fire, the mirror shield sends it back
            bull.Pose("shoot", Facing.Down);
            for (int i = 0; i < 8; i++)
            {
                if (i == 1)
                    for (int k = -1; k <= 1; k++)
                        Projectile.Fireball(bull.Mouth, (Vector2)(Quaternion.Euler(0, 0, k * 14f) * Vector2.down) * 5.2f, bull.gameObject);
                yield return t.Shot("m11-bull-" + i, 0.1f);
            }
            // the ending: the god mumbles, the watchman nearly gives in
            Object.Destroy(bull.gameObject);
            p.pos = Map.ToWorld(240, 180);
            PixelView.I.target = p.transform;
            DialogueBox.AutoAdvance = 1.0f;
            Story.Run(Story.I.Ending());
            for (int i = 0; i < 16; i++) yield return t.Shot("m12-end-" + i, 1.6f);
        }
    }
}
