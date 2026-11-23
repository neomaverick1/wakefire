// The Bronze Herdsman against somebody who plays it straight: -wfScene herdsman, four rounds with
// the life and the blade Azar has when he reaches him (no shield yet: it is what he is fighting for).
// He stays out of the goad's reach while it is raised, goes in when the Herdsman leans on it, and
// steps across the line when the heads in the wall are told to breathe.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class HerdTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["herdsman"] = Run;

        static Vector2 InRoom(string id, float x, float y)
        {
            var r = Rooms.I.Find(id);
            return new Vector2(r.rect.xMin + x / 16f, r.rect.yMax - y / 16f);
        }

        static IEnumerator Run(AutoTest t)
        {
            DialogueBox.AutoAdvance = 0.1f;
            int wins = 0;
            for (int round = 0; round < 4; round++)
            {
                Save.ClearAll(); Save.Use(0);
                Game.I.Begin(false);
                Story.Abort();
                Story.GiveKit();
                foreach (var f in new[] { "door_z2_door", "chest_z2_key" }) Story.Set(f);
                Story.I.ApplyItems();
                Random.InitState(2000 + round * 91);
                Game.I.EnterMap("zig_2", "south");
                Fade.Set(0);
                var p = Player.I;
                p.SetState(Player.State.Free, "idle");
                yield return new WaitForSeconds(0.3f);
                p.pos = InRoom("herd", 208, 196);
                yield return new WaitForSeconds(1.2f);
                for (float w = 0; w < 20f && (Story.I.Running || Game.Busy); w += Time.deltaTime) yield return null;
                Herdsman h = null;
                foreach (var e in Enemy.All) if (e is Herdsman hh) h = hh;
                if (!h) { t.Note("FAIL no herdsman in his hall"); yield break; }
                var floor = Rooms.I.Find("herd").Floor;
                var door = new Vector2(floor.center.x, floor.yMin - 0.6f);
                float time = 0, swingCd = 0;
                int swings = 0, hp0 = p.health.hp, opens = 0, calls = 0;
                bool wasOpen = false, wasCalling = false, shot = false;
                Vector2 dodge = Vector2.zero;
                while (h && !h.health.Dead && p.state != Player.State.Dead && time < 180f && Rooms.I.current != null && Rooms.I.current.id == "herd")
                {
                    float dt = Time.deltaTime;
                    time += dt; swingCd -= dt;
                    var d = h.pos - p.pos;
                    if (h.Open && !wasOpen) opens++;
                    if (h.Calling && !wasCalling) calls++;
                    wasOpen = h.Open; wasCalling = h.Calling;
                    Vector2 go = Vector2.zero;
                    bool swing = false;
                    // fire in the air: get off its line
                    Projectile near = null;
                    foreach (var pr in Object.FindObjectsByType<Projectile>(FindObjectsSortMode.None))
                        if (!near || Vector2.Distance(pr.transform.position, p.pos) < Vector2.Distance(near.transform.position, p.pos)) near = pr;
                    if (near && Vector2.Distance(near.transform.position, p.pos) < 4f)
                    {
                        var line = ((Vector2)near.transform.position - p.pos).normalized;
                        if (dodge == Vector2.zero)
                        {
                            var perp = new Vector2(-line.y, line.x);
                            dodge = Vector2.Distance(p.pos + perp * 2f, floor.center) < Vector2.Distance(p.pos - perp * 2f, floor.center) ? perp : -perp;
                        }
                        go = dodge;
                    }
                    else if (h.Open)
                    {
                        dodge = Vector2.zero;
                        go = d.magnitude > 1.3f ? d.normalized : Vector2.zero;
                        swing = d.magnitude <= 1.65f;
                    }
                    else if (h.Winding || h.Sweeping)
                    {
                        // the goad is up: straight back out of its reach, whichever way that is
                        dodge = Vector2.zero;
                        go = d.magnitude < 3.3f ? -d.normalized : Vector2.zero;
                    }
                    else
                    {
                        dodge = Vector2.zero;
                        // wait for him just outside the goad's reach, and no nearer the walls than he has to be
                        var toMid = floor.center - p.pos;
                        go = d.magnitude < 2.9f ? (-d.normalized + toMid.normalized * 0.5f).normalized : d.magnitude > 3.6f ? d.normalized : Vector2.zero;
                    }
                    // the door he came in by stands open behind him: backing out through it would end the fight without winning it
                    var fromDoor = p.pos - door;
                    if (fromDoor.magnitude < 3.2f) go = (go + fromDoor.normalized * 1.6f + Vector2.right * (p.pos.x < door.x ? -0.8f : 0.8f)).normalized;
                    Controls.Fake = go;
                    if (swing && swingCd <= 0 && p.state == Player.State.Free)
                    {
                        p.Face(Mathf.Abs(d.x) > Mathf.Abs(d.y) ? (d.x < 0 ? Facing.Left : Facing.Right) : (d.y < 0 ? Facing.Down : Facing.Up));
                        Controls.FakePress = Controls.Attack;
                        swings++; swingCd = 0.28f;
                    }
                    if (!shot && round == 0 && h.Winding && d.magnitude < 3.4f) { shot = true; yield return t.Shot("h1-raise", 0); }
                    yield return null;
                }
                Controls.Fake = Vector2.zero;
                bool won = Story.Has("dead_z2_herdsman");
                bool left = !won && Rooms.I.current != null && Rooms.I.current.id != "herd";
                if (won) wins++;
                t.Note($"round {round}: {(won ? "won" : left ? "WALKED OUT (no result)" : p.state == Player.State.Dead ? "FELL" : "ran out of time")} in {time:0}s, {swings} swings, he leaned {opens} times and called his herd {calls}, " +
                       $"life {hp0} -> {p.health.hp}{(won || !h ? "" : $", he had {h.health.hp}/{h.health.max} left")}");
                yield return new WaitForSeconds(1.0f);
                if (round == 0) yield return t.Shot("h2-after", 0);
                for (float w = 0; w < 10f && (p.state == Player.State.Dead || Game.Busy); w += Time.deltaTime) yield return null;
                yield return new WaitForSeconds(0.5f);
                Story.Abort();
            }
            t.Note($"HERDSMAN: {wins}/4 rounds won by a plain fighter");
        }
    }
}
