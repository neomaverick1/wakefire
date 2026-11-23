// Every doorway in both chapters walked through for real: Azar starts just inside each exit, walks
// out, and must arrive in the right place at the named spawn (a misspelt spawn would quietly
// drop him somewhere else).
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class ExitTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["exits"] = Run;

        static IEnumerator Run(AutoTest t)
        {
            DialogueBox.AutoAdvance = 0.05f;
            foreach (var f in new[] { "gate_open", "door_z2_bigdoor", "yard_bridge", "key", "item_oil", "item_shield", "bigkey", "door_z1_door",
                                      "bull_seen", "bull_dead", "chapter_done", "ch2", "item_hillkey", "hill_gate", "met_namtar", "queue_passed", "king_door",
                                      "door_t1_door", "door_t2_seal", "king_seen", "king_done", "item_horn", "chapter2_done" })
                Story.Set(f);
            string[] maps = { "ashkel", "lowtown", "cliffs", "terraces", "crypt", "temple_yard", "zig_1", "zig_2", "zig_3", "necro_road", "necropolis", "tomb_1", "tomb_2", "tomb_3" };
            int bad = 0, n = 0;
            foreach (var map in maps)
            {
                Game.I.EnterMap(map);
                Fade.Set(0);
                yield return new WaitForSeconds(0.3f);
                var exits = System.Array.FindAll(Map.Current.data.markers, m => m.kind == "exit");
                foreach (var ex in exits)
                {
                    Game.I.EnterMap(map);
                    Fade.Set(0);
                    yield return new WaitForSeconds(0.25f);
                    foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
                    var p = Player.I;
                    // which edge of the map is this doorway on? walk out through it
                    float cx = ex.x + ex.w / 2f, cy = ex.y + ex.h / 2f;
                    var md = Map.Current.data;
                    float dl = cx, dr = md.w - cx, du = cy, dd = md.h - cy;
                    float min = Mathf.Min(Mathf.Min(dl, dr), Mathf.Min(du, dd));
                    Vector2 dir = min == dl ? Vector2.left : min == dr ? Vector2.right : min == du ? Vector2.up : Vector2.down;
                    var inside = new Vector2(cx, cy) - new Vector2(dir.x, -dir.y) * 22f;
                    p.pos = Map.ToWorld(inside.x, inside.y);
                    p.SetState(Player.State.Free, "idle");
                    yield return new WaitForSeconds(0.2f);      // let the exit arm
                    float w = 0;
                    while (Game.I.CurrentMap == map && w < 4f)
                    {
                        Controls.Fake = p.state == Player.State.Free ? dir : Vector2.zero;
                        w += Time.deltaTime;
                        yield return null;
                    }
                    Controls.Fake = Vector2.zero;
                    yield return new WaitForSeconds(0.6f);
                    string arrived = Game.I.CurrentMap, spawn = Game.I.CurrentSpawn;
                    var want = Map.Current.Marker("spawn", ex.text);
                    bool ok = arrived == ex.id && want != null && spawn == ex.text;
                    n++;
                    if (!ok) bad++;
                    t.Note($"{map} -> {ex.id} ({ex.text}): {(ok ? "ok" : $"FAILED, arrived in {arrived} at spawn {spawn}, spawn exists={want != null}")}");
                }
            }
            t.Note($"{n - bad}/{n} doorways good");
        }
    }
}
