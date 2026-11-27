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
            foreach (var f in new[] { "gate_open", "door_z2_bigdoor", "door_z2_door", "dead_z2_herdsman", "z2_bull", "yard_bridge", "key", "item_oil", "item_shield", "bigkey", "door_z1_door",
                                      "bull_seen", "bull_dead", "chapter_done", "ch2", "item_hillkey", "hill_gate", "met_namtar", "queue_passed", "king_door",
                                      "door_t1_door", "door_t2_seal", "door_t3_kingdoor", "door_t3_lock", "ghostkey", "item_wheel", "king_seen", "king_done", "item_horn", "chapter2_done",
                                      "on_lt_tax_gong", "on_lt_goat_latch", "open_beer_hatch",
                                      "on_ak_merchant_latch", "on_ak_lamps_sign", "on_wt_keys", "on_tb_bolt",
                                      "on_nr_couple_latch", "on_np_five_latch", "on_np_knocker_gong", "on_np_pillow_sign" })
                Story.Set(f);
            string[] maps = { "ashkel", "ashkel_in", "lowtown", "lowtown_in", "cliffs", "terraces", "crypt", "temple_yard", "zig_1", "zig_2", "zig_hi", "zig_3", "necro_road", "necro_road_in", "necropolis", "necropolis_in", "barrow", "tomb_1", "tomb_2", "tomb_hi", "tomb_3" };
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
                    if (ex.id == "barrow") dir = Vector2.up;            // a door in a mound in the middle of the hill, not at an edge of the map
                    // the doors of houses are anywhere on a map: walked in at going north (a door, a hatch, a stair), and
                    // out of going south (the street door of a room, at the foot of its cell)
                    bool rooms = Game.Houses(map);
                    if (rooms || map == "lowtown" || map == "ashkel" || map == "necro_road" || map == "necropolis")
                    {
                        bool edge = !rooms && min <= 24f;
                        if (!edge) dir = rooms && (ex.y + ex.h) % 224 == 0 ? Vector2.down : Vector2.up;
                    }
                    var inside = new Vector2(cx, cy) - new Vector2(dir.x, -dir.y) * 22f;
                    p.pos = Map.ToWorld(inside.x, inside.y);
                    p.SetState(Player.State.Free, "idle");
                    // on a floor of rooms the picture slides to the room he has turned up in, and walks him a
                    // few steps the way it thinks he came: let it finish, then stand him where he was meant to be
                    yield return null; yield return null;
                    for (float s = 0; s < 3f && (Rooms.Sliding || Game.Busy); s += Time.deltaTime) yield return null;
                    for (float s = 0; s < 15f && Story.I && Story.I.Running; s += Time.deltaTime) yield return null;
                    p.pos = Map.ToWorld(inside.x, inside.y);
                    p.SetState(Player.State.Free, "idle");
                    yield return new WaitForSeconds(0.2f);      // let the exit arm
                    float w = 0;
                    // (a stair from one room of a floor to another room of the same floor does not leave the map:
                    //  there he has arrived when he stands at its far end, and walking on would only take him back down it)
                    bool within = ex.id == map;
                    while ((within ? Game.I.CurrentSpawn != ex.text : Game.I.CurrentMap == map) && w < 4f)
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
