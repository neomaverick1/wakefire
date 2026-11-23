// Kurashtar, fought for real. A simple bot walks Azar into the king's chamber (the scene plays),
// keeps out from under the mace until he is rested, nods off beside the king and knocks the
// crown off the empty air, wakes, and goes for him while he is bare-headed. It must win, the
// Horn must change hands, and the dawn must come (and go) on the summit.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class KingTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["king"] = Run;

        static IEnumerator Run(AutoTest t)
        {
            DialogueBox.AutoAdvance = 0.35f;
            foreach (var f in new[] { "key", "gate_open", "braziers", "item_shield", "item_oil", "item_lamp", "bigkey", "yard_bridge", "bull_seen", "bull_dead", "chapter_done",
                                      "ch2", "item_hillkey", "hill_gate", "met_namtar", "queue_passed", "name_kur", "name_ash", "name_tar", "king_door", "door_t1_door", "door_t2_seal", "item_wheel", "ghostkey", "door_t3_kingdoor" })
                Story.Set(f);
            Game.I.EnterMap("tomb_3", "south");
            Story.I.ApplyItems();
            Fade.Set(0);
            var p = Player.I;
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.6f);
            p.health.max = p.health.hp = 400;
            float t0 = Time.time;
            bool shotTalk = false;
            while (!(SleeplessKing.I && SleeplessKing.I.Fighting) && Time.time - t0 < 90f)
            {
                Controls.Fake = p.state == Player.State.Free && p.pos.y < Map.ToWorld(0, 300).y ? Vector2.up : Vector2.zero;
                if (!shotTalk && Story.I.Running && Time.time - t0 > 6f) { shotTalk = true; yield return t.Shot("k0-throne", 0f); }
                yield return null;
            }
            Controls.Fake = Vector2.zero;
            var k = SleeplessKing.I;
            t.Note("the king is up and fighting: " + (k && k.Fighting ? "ok" : "FAILED") + $" after {Time.time - t0:0.0}s");
            if (!k) yield break;
            yield return t.Shot("k1-fight", 0.4f);
            float start = Time.time, swing = 0, nextNote = 0;
            int hpStart = p.health.hp, offs = 0, shots = 0;
            bool wasCrowned = true, shotDream = false, shotBare = false, shotSlam = false;
            var centre = (Vector2)Map.Current.bounds.center + new Vector2(0, -0.8f);
            while (k && !Story.Has("king_done") && Time.time - start < 240f)
            {
                bool dreaming = Dream.I.Dreaming;
                var d = k.pos - p.pos;
                Vector2 want = Vector2.zero;
                if (!k.Crowned && wasCrowned) offs++;
                wasCrowned = k.Crowned;
                if (k.Crowned)
                {
                    var under = k.pos + new Vector2(0, -1.0f);
                    if (!dreaming)
                    {
                        if (Dream.I.Drowsiness > 0.9f)
                        {
                            want = under - p.pos;
                            if (want.magnitude < 0.6f) { want = Vector2.zero; if (p.state == Player.State.Free) p.NodOff(); }
                        }
                        else
                        {
                            // keep the width of the room between them, circling
                            var away = (p.pos - k.pos).normalized;
                            var side = new Vector2(-away.y, away.x);
                            var spot = k.pos + away * 5.5f + side * 1.5f;
                            spot = centre + Vector2.ClampMagnitude(spot - centre, 5.2f);
                            want = spot - p.pos;
                            if (want.magnitude < 0.3f) want = Vector2.zero;
                        }
                        if (!shotSlam && k.StateName == "Slam") { shotSlam = true; yield return t.Shot("k2-slam", 0.55f); }
                    }
                    else
                    {
                        want = under - p.pos;
                        if (want.magnitude < 0.5f)
                        {
                            want = Vector2.zero;
                            p.Face(Facing.Up);
                            if (!shotDream) { shotDream = true; yield return t.Shot("k3-dream-crown", 0.1f); }
                            if (Time.time > swing && p.state == Player.State.Free) { Controls.FakePress = Controls.Attack; swing = Time.time + 0.18f; }
                        }
                    }
                }
                else if (dreaming)
                {
                    if (p.state == Player.State.Free) p.NodOff();           // wake up: he is only himself in the waking world
                }
                else
                {
                    var flank = k.pos + new Vector2(d.x > 0 ? -1.0f : 1.0f, 0);
                    want = flank - p.pos;
                    if (want.magnitude < 0.45f)
                    {
                        want = Vector2.zero;
                        p.Face(d.x > 0 ? Facing.Right : Facing.Left);
                        if (!shotBare && k.StateName == "Bare") { shotBare = true; yield return t.Shot("k4-bare", 0.05f); }
                        if (Time.time > swing && p.state == Player.State.Free) { Controls.FakePress = Controls.Attack; swing = Time.time + 0.18f; }
                    }
                }
                Controls.Fake = p.state == Player.State.Free && !Story.I.Running ? (want.sqrMagnitude > 0 ? want.normalized : Vector2.zero) : Vector2.zero;
                if (Time.time - start > nextNote)
                {
                    nextNote += 15f;
                    t.Note($"t={Time.time - start:0} king={k.StateName} crowned={k.Crowned} round={k.Round} hp={k.health.hp} dreaming={dreaming} rest={Dream.I.Drowsiness:0.00} azar={p.state} lost={hpStart - p.health.hp}");
                    shots++;
                }
                yield return null;
            }
            Controls.Fake = Vector2.zero;
            t.Note($"the king yields: {(Story.Has("king_done") ? "ok" : "FAILED")} in {Time.time - start:0.0}s, crown off {offs} times, Azar lost {hpStart - p.health.hp} half-flames");
            float e0 = Time.time;
            bool shotYield = false, shotDawn = false, shotGoat = false;
            while (!Story.Has("chapter2_done") && Time.time - e0 < 150f)
            {
                if (!shotYield && Time.time - e0 > 4f) { shotYield = true; yield return t.Shot("k5-yields", 0f); }
                if (!shotDawn && Game.I.CurrentMap == "zig_3" && PixelView.I.ambient.r > 1.1f) { shotDawn = true; yield return t.Shot("k6-dawn", 0.6f); }
                yield return null;
            }
            t.Note($"the Horn changes hands: {(Story.Has("item_horn") ? "ok" : "FAILED")}");
            t.Note($"one breath of dawn on the summit, and the chapter ends: {(Story.Has("chapter2_done") ? "ok" : "FAILED")} after {Time.time - e0:0.0}s");
            if (!shotGoat) yield return t.Shot("k7-card", 2.5f);
            yield return t.Shot("k8-title", 16f);
        }
    }
}
