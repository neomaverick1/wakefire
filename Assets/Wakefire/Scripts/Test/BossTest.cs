// The Brazen Bull, fought for real: a simple bot walks Azar into the summit (the intro plays),
// then dodges charges, keeps a pillar between itself and the bull, faces the fire so the mirror
// shield sends it back, and runs in to swing the khopesh whenever the bull reels. It must win and
// the ending must play. Azar gets a deep pool of life so the run measures how much he'd lose.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class BossTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["boss"] = Run;

        static IEnumerator Run(AutoTest t)
        {
            DialogueBox.AutoAdvance = 0.4f;
            Story.Set("item_shield");
            Story.Set("item_oil");
            Game.I.EnterMap("zig_3", "south");
            Story.I.ApplyItems();
            Fade.Set(0);
            var p = Player.I;
            yield return new WaitForSeconds(0.6f);
            PixelView.I.target = null;
            PixelView.I.SnapTo(Map.ToWorld(240, 150));
            yield return t.Shot("b0-summit", 0.8f);
            PixelView.I.target = p.transform;
            p.health.max = p.health.hp = 400;
            // walk in until the bull wakes
            float t0 = Time.time;
            while (!BrazenBull.I && Time.time - t0 < 30f)
            {
                Controls.Fake = p.state == Player.State.Free ? Vector2.up : Vector2.zero;
                yield return null;
            }
            Controls.Fake = Vector2.zero;
            var bull = BrazenBull.I;
            t.Note("bull spawned: " + (bull != null) + $" after {Time.time - t0:0.0}s");
            if (!bull) yield break;
            while (!bull.Fighting) yield return null;
            t.Note("fight begins");
            yield return t.Shot("b1-fight", 0.5f);
            float start = Time.time, swing = 0;
            int hpStart = p.health.hp, shots = 0, stuns = 0;
            bool wasStunned = false;
            var pillars = new System.Collections.Generic.List<Vector2>();
            foreach (var pr in Map.Current.props) if (pr && pr.Kind == "pillar") pillars.Add(pr.basePos);
            while (bull && !bull.health.Dead && Time.time - start < 180f)
            {
                var d = bull.pos - p.pos;
                if (bull.Stunned && !wasStunned) stuns++;
                wasStunned = bull.Stunned;
                bool fire = Object.FindObjectsByType<Projectile>(FindObjectsSortMode.None).Length > 0;
                Vector2 want;
                if (bull.Stunned)
                {
                    // in front of the bull, a blade's length off its flank
                    var spot = bull.pos + new Vector2(Mathf.Sign(-d.x == 0 ? 1 : -d.x) * 2.2f, 0);
                    want = spot - p.pos;
                    if (want.magnitude < 0.35f)
                    {
                        want = Vector2.zero;
                        p.Face(d.x > 0 ? Facing.Right : Facing.Left);
                        if (Time.time > swing && p.state == Player.State.Free) { Controls.FakePress = Controls.Attack; swing = Time.time + 0.18f; }
                    }
                }
                else if (fire)
                {
                    // face the fire and raise the mirror shield
                    want = Vector2.zero;
                    if (p.state == Player.State.Free || p.state == Player.State.Guard)
                        p.Face(Mathf.Abs(d.x) > Mathf.Abs(d.y) ? (d.x > 0 ? Facing.Right : Facing.Left) : (d.y > 0 ? Facing.Up : Facing.Down));
                    Controls.FakeHold = Controls.Interact;
                    if (p.state == Player.State.Free) Controls.FakePress = Controls.Interact;
                }
                else
                {
                    // hide behind the pillar on the far side from the bull
                    Vector2 best = p.pos; float bestScore = float.MaxValue;
                    foreach (var pl in pillars)
                    {
                        var hide = pl + (pl - bull.pos).normalized * 1.6f;
                        float score = Vector2.Distance(hide, p.pos) - Vector2.Distance(hide, bull.pos) * 0.5f;
                        if (score < bestScore) { bestScore = score; best = hide; }
                    }
                    want = best - p.pos;
                    if (bull.Charging && d.magnitude < 7f) want = new Vector2(-d.y, d.x).normalized;   // sidestep
                    if (want.magnitude < 0.3f) want = Vector2.zero;
                }
                if (!fire || bull.Stunned) Controls.FakeHold = null;
                Controls.Fake = p.state == Player.State.Free ? (want.sqrMagnitude > 0 ? want.normalized : Vector2.zero) : Vector2.zero;
                if (Time.time - start > shots * 20f)
                {
                    t.Note($"t={Time.time - start:0} bull={bull.StateName} hp={bull.health.hp} story={Story.I.Running} azar={p.state} at {p.pos} bull at {bull.pos} fake={Controls.Fake}");
                    yield return t.Shot("b2-fight-" + shots, 0f); shots++;
                }
                yield return null;
            }
            Controls.Fake = Vector2.zero;
            Controls.FakeHold = null;
            t.Note($"bull dead: {bull == null || bull.health.Dead} in {Time.time - start:0.0}s, stuns {stuns}, Azar lost {hpStart - p.health.hp} half-flames");
            float e0 = Time.time;
            while (!Story.Has("chapter_done") && Time.time - e0 < 60f) yield return null;
            t.Note("ending reached: " + Story.Has("chapter_done") + $" after {Time.time - e0:0.0}s");
            yield return t.Shot("b3-after", 1.0f);
        }
    }
}
