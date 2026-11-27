// Every creature fought for real with the khopesh: a bot closes in on its flank, faces it and
// swings. Each must go down, and the run reports how long it took and what it cost Azar.
// (Moths live in the dream, so Azar fights those asleep.)
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class FightTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["fight"] = Run;

        static Vector2 Vec(Facing f) => f == Facing.Down ? Vector2.down : f == Facing.Up ? Vector2.up : f == Facing.Left ? Vector2.left : Vector2.right;

        static IEnumerator Run(AutoTest t)
        {
            DialogueBox.AutoAdvance = 0.2f;
            Game.I.EnterMap("zig_1", "south");
            Fade.Set(0);
            yield return new WaitForSeconds(0.5f);
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            var p = Player.I;
            // open floor in the first hall (wherever the hall is on the floor's plan)
            var hall = Rooms.I.Find("hall");
            var arena = new Vector2(hall.rect.xMin + 256 / 16f, hall.rect.yMax - 76 / 16f);
            foreach (var kind in new[] { "crab", "jackal", "moth", "sentinel", "jackal" })
            {
                p.health.max = p.health.hp = 400;
                p.pos = arena + new Vector2(-2.5f, 0);
                p.SetState(Player.State.Free, "idle");
                yield return null;
                if (kind == "moth") { Dream.I.Drowsiness = 1; Dream.I.Seconds = 9999; Dream.I.Flip(p.pos, true); yield return new WaitForSeconds(1.2f); }
                var at = arena + new Vector2(2.5f, 0.5f);
                Enemy foe = kind switch { "crab" => Crab.Spawn(at), "jackal" => Jackal.Spawn(at), "moth" => Moth.Spawn(at), _ => Sentinel.Spawn(at) };
                float start = Time.time, swing = 0;
                int hp0 = p.health.hp, swings = 0;
                while (foe && !foe.health.Dead && Time.time - start < 40f)
                {
                    var d = foe.pos - p.pos;
                    // stand off its flank (a sentinel's shield faces where it faces)
                    var side = new Vector2(-Vec(foe.facing).y, Vec(foe.facing).x);
                    if (Vector2.Dot(side, -d) < 0) side = -side;
                    var spot = foe.pos + side * 1.05f;
                    var want = spot - p.pos;
                    if (p.state == Player.State.Free)
                    {
                        if (want.magnitude > 0.3f && d.magnitude > 1.1f) Controls.Fake = want.normalized;
                        else
                        {
                            Controls.Fake = Vector2.zero;
                            p.Face(Mathf.Abs(d.x) > Mathf.Abs(d.y) ? (d.x > 0 ? Facing.Right : Facing.Left) : (d.y > 0 ? Facing.Up : Facing.Down));
                            if (Time.time > swing) { Controls.FakePress = Controls.Attack; swing = Time.time + 0.2f; swings++; }
                        }
                    }
                    else Controls.Fake = Vector2.zero;
                    yield return null;
                }
                Controls.Fake = Vector2.zero;
                bool dead = !foe || foe.health.Dead;
                t.Note($"{kind}: {(dead ? "down" : "STILL STANDING")} in {Time.time - start:0.0}s, {swings} swings, Azar lost {hp0 - p.health.hp} half-flames");
                if (foe) Object.Destroy(foe.gameObject);
                if (kind == "moth") { Dream.I.SetInstant(false); Dream.I.Seconds = 7; }
                yield return new WaitForSeconds(0.5f);
            }
            // a stutter: one long tick takes the swing straight past the frame the blade lands on. It lands all the same.
            {
                p.health.max = p.health.hp = 400;
                p.pos = arena;
                p.SetState(Player.State.Free, "idle");
                p.Face(Facing.Right);
                var foe = Crab.Spawn(arena + new Vector2(1.0f, 0));
                foe.Sleep(6f);
                yield return null;
                p.pos = arena; p.Face(Facing.Right);
                int hp = foe.health.hp;
                Controls.FakePress = Controls.Attack;
                for (int i = 0; i < 6 && p.state != Player.State.Attack; i++) yield return null;
                bool began = p.state == Player.State.Attack && p.anim.Frame < 2 && foe && foe.health.hp == hp;
                int was = p.anim.Frame;
                p.anim.Tick(0.2f);
                int now = p.anim.Frame;
                yield return null;
                bool landed = !foe || foe.health.hp < hp;
                t.Note($"a blow lands though the picture skipped its frame (frame {was} -> {now}): {(began && landed ? "ok" : "FAILED")}");
                if (foe) Object.Destroy(foe.gameObject);
                yield return new WaitForSeconds(0.3f);
            }
        }
    }
}
