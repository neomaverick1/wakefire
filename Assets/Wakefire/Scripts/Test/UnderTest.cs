// The Underbed, played through in the crypt: an arm from under a bed, what the light does to it,
// being taken under and put out somewhere else, and the bed in the last room.
//   -wfScene under [-wfUnder reach|bed]
using System.Collections;
using System.Linq;
using UnityEngine;

namespace Wakefire
{
    public static class UnderTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["under"] = Run;

        static AutoTest T;
        static int bad;
        static void Check(string what, bool ok) { T.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }

        static Vector2 InRoom(string id, float x, float y)
        {
            var r = Rooms.I ? Rooms.I.Find(id) : null;
            if (r == null) return Player.I.pos;
            return new Vector2(r.rect.xMin + x / 16f, r.rect.yMax - y / 16f);
        }

        static string Room => Rooms.I && Rooms.I.current != null ? Rooms.I.current.id : "(none)";

        static IEnumerator Quiet(float atLeast = 0.2f, float atMost = 40f)
        {
            float w = 0;
            while ((w < atLeast || (Story.I && Story.I.Running) || Game.Busy || Rooms.Sliding) && w < atMost) { w += Time.deltaTime; yield return null; }
        }

        /// <summary>He is put in a room and the room is allowed to notice.</summary>
        static IEnumerator Put(string room, float x, float y, Facing f)
        {
            var p = Player.I;
            p.SetState(Player.State.Free, "idle");
            p.pos = InRoom(room, x, y); p.Face(f);
            yield return null; yield return null;
            yield return Quiet(0.5f);
            p.pos = InRoom(room, x, y); p.Face(f);
        }

        static IEnumerator Stand(Vector2 at, Facing f, float seconds, System.Func<bool> until = null)
        {
            var p = Player.I;
            for (float w = 0; w < seconds; )
            {
                if (until != null && until()) yield break;
                if (p.state == Player.State.Free && !Game.Busy) { p.pos = at; p.Face(f); }
                if (!(Story.I && Story.I.Running)) w += Time.deltaTime;
                yield return null;
            }
        }

        static IEnumerator Run(AutoTest t)
        {
            T = t; bad = 0;
            DialogueBox.AutoAdvance = 0.1f;
            Save.ClearAll(); Save.Use(0);
            Game.I.Begin(false);
            Story.Abort();
            Story.GiveKit();
            Story.DreamsQuiet = true;
            Game.I.EnterMap("crypt", "south");
            Story.Abort();
            Fade.Set(0);
            yield return new WaitForSeconds(0.5f);
            string only = Boot.Arg("-wfUnder");
            if (only == null || only == "reach") yield return ReachPart(t);
            if (only == null || only == "bed") yield return BedPart(t);
            t.Note(bad == 0 ? "UNDER OK" : $"UNDER FAILED: {bad}");
        }

        // ------------------------------------------------------------------------------ an arm
        static IEnumerator ReachPart(AutoTest t)
        {
            var p = Player.I;
            p.coins = 20;
            yield return Put("beds", 40, 160, Facing.Right);
            var all = Enemy.All.OfType<Reach>().ToArray();
            Check($"the dormitory ({Room}): something under the beds, and up through the floor of the store ({all.Length} arms)", Room == "beds" && all.Length == 7);
            if (all.Length == 0) yield break;
            // the second bed with something under it: nowhere near a torch
            var beds = Rooms.I.Find("beds");
            var r = all.OrderBy(a => Vector2.Distance(a.pos, InRoom("beds", 300, 87))).First();
            Check("nothing shows until somebody is near", all.All(a => !a.Out));
            yield return t.Shot("u0-the-long-sleep", 0.3f);
            // he stands in the dark, two tiles from the foot of the bed
            Vector2 here = r.pos + new Vector2(0.4f, -2.6f);
            yield return Stand(here, Facing.Up, 6f, () => r.Out);
            Check("it comes out from under the bed", r.Out);
            yield return Stand(here, Facing.Up, 1.0f);
            yield return t.Shot("u1-an-arm", 0.1f);
            int hp = p.health.hp, coins = p.coins;
            yield return Stand(here, Facing.Up, 8f, () => r.Has);
            Check("...feels its way across the floor to him, and has him by the ankle", r.Has && p.HeldBy(r));
            yield return t.Shot("u2-by-the-ankle", 0.2f);
            // he does nothing about it: it takes him under, and he is put out somewhere else
            Vector2 was = p.pos;
            for (float w = 0; w < 14f && Story.Count("taken_under") == 0; w += Time.deltaTime) yield return null;
            yield return Quiet(0.6f);
            Check($"left to it, it takes him under ({Story.Count("taken_under")}), and that costs him ({hp} -> {p.health.hp} life, {coins} -> {p.coins} shekels)",
                  Story.Count("taken_under") == 1 && p.health.hp == hp - 1 && p.coins < coins && p.state == Player.State.Free);
            Check($"what it took is kept ({Story.Count("under_hoard")})", Story.Count("under_hoard") == coins - p.coins);
            p.health.hp = p.health.max;
            // again, and this time he cuts
            yield return Quiet(0.3f);
            int arm = r.health.hp;
            for (float w = 0; w < 14f && !r.Has; w += Time.deltaTime) { if (p.state == Player.State.Free) { p.pos = here; p.Face(Facing.Up); } yield return null; }
            Check("it has him again", r.Has);
            for (int i = 0; i < 3 && r.Has; i++) { Controls.FakePress = Controls.Attack; for (float w = 0; w < 0.2f; w += Time.deltaTime) yield return null; }
            yield return null;
            Check($"three cuts and it lets go ({p.state}), and feels it ({arm} -> {r.health.hp})", !r.Has && p.state != Player.State.Held && r.health.hp == arm - 1);
            // the light: it will not put its hand in it
            // (in the torch's light, on the side of it nearest that bed: near enough to be felt for)
            var flame = InRoom("beds", 372, 126);
            var torch = flame + (r.pos - flame).normalized * 1.0f;
            p.pos = torch;
            yield return new WaitForSeconds(0.3f);
            Check($"under a torch the floor counts as lit (lit {StayUp.Lit(p.pos)})", StayUp.Lit(p.pos));
            for (float w = 0; w < 12f && !r.Waiting; w += Time.deltaTime) { if (p.state == Player.State.Free) { p.pos = torch; p.Face(Facing.Left); } yield return null; }
            Check($"it comes as far as the edge of the light and stops there ({r.s}, {Vector2.Distance(r.Hand, p.pos):0.0} tiles off)", r.Waiting && !StayUp.Lit(r.Hand) && Vector2.Distance(r.Hand, p.pos) > 0.6f);
            yield return t.Shot("u3-at-the-edge-of-the-light", 0.6f);
            // ...and a hand that is waiting can be cut, until it has had enough
            for (float w = 0, next = 0; w < 14f && r; )
            {
                if (Story.I && Story.I.Running) { yield return null; continue; }
                if (r.Out && w >= next && (p.state == Player.State.Free || p.state == Player.State.Attack))
                {
                    var to = r.Hand - p.pos;
                    var f = Mathf.Abs(to.x) > Mathf.Abs(to.y) ? (to.x > 0 ? Facing.Right : Facing.Left) : (to.y > 0 ? Facing.Up : Facing.Down);
                    var dir = f == Facing.Right ? Vector2.right : f == Facing.Left ? Vector2.left : f == Facing.Up ? Vector2.up : Vector2.down;
                    p.pos = r.Hand - dir * 0.9f - new Vector2(0, 0.3f); p.Face(f);
                    Controls.FakePress = Controls.Attack; next = w + 0.36f;
                }
                else if (!r.Out && p.state == Player.State.Free) p.pos = here;
                w += Time.deltaTime;
                yield return null;
            }
            Check("cut often enough, it goes back under and stays there", !r && Story.Has("dead_" + "crypt_r1"));
            // the arm under the third bed puts him out in the larder
            var third = all.Where(a => a).OrderBy(a => Vector2.Distance(a.pos, InRoom("beds", 172, 87))).First();
            p.health.hp = p.health.max;
            Vector2 by = third.pos + new Vector2(0.3f, -2.4f);
            int taken = Story.Count("taken_under");
            for (float w = 0; w < 24f && Story.Count("taken_under") == taken; w += Time.deltaTime) { if (p.state == Player.State.Free && Room == "beds") { p.pos = by; p.Face(Facing.Up); } yield return null; }
            yield return Quiet(0.8f);
            Check($"under one bed is under all of them: the third bed's arm puts him out in the larder ({Room})", Room == "larder");
            yield return t.Shot("u4-out-in-the-larder", 0.4f);
            // ...and the heap in the larder has everything it took off him
            foreach (var e in Enemy.All.ToArray()) if (e is Reach) Object.Destroy(e.gameObject);
            var heap = Map.Current.Find("under_hoard");
            int kept = Story.Count("under_hoard"), had = p.coins;
            if (heap) { p.SetState(Player.State.Free, "idle"); p.pos = heap.basePos + new Vector2(0, -0.7f); p.Face(Facing.Up); }
            yield return new WaitForSeconds(0.3f);
            Check($"at the heap the action button says {p.Action}", p.Action == Player.Act.Look);
            Controls.FakePress = Controls.Interact;
            yield return Quiet(0.6f);
            Check($"the heap has what it took off him ({kept} kept, {had} -> {p.coins} shekels)", heap && kept > 0 && p.coins == had + kept && Story.Count("under_hoard") == 0);
        }

        // ------------------------------------------------------------------------------ the bed
        static IEnumerator BedPart(AutoTest t)
        {
            var p = Player.I;
            p.health.max = p.health.hp = 40;
            yield return Put("den", 208, 200, Facing.Up);
            var bed = Enemy.All.OfType<Underbed>().FirstOrDefault();
            Check($"the last room ({Room}): the first bed of the First Watch, and four arms under it ({(bed ? bed.arms.Count : 0)})", Room == "den" && bed && bed.arms.Count == 4);
            if (!bed) yield break;
            var cage = Map.Current.Find("crypt_cage");
            yield return t.Shot("v0-the-first-bed", 0.5f);
            // a man who has come without the blade is no use to it: it puts him out of its room
            p.hasSword = false;
            int outs = Story.Count("taken_under");
            for (float w = 0; w < 40f && Story.Count("taken_under") == outs; w += Time.deltaTime) { if (p.state == Player.State.Free && Room == "den" && bed) { p.pos = bed.pos + new Vector2(0.2f, -2.6f); p.Face(Facing.Up); } yield return null; }
            yield return Quiet(0.8f);
            Check($"with no blade on him the first bed puts him out of its room ({Room}, {p.state})", Room == "run" && p.state == Player.State.Free);
            p.hasSword = true;
            p.health.hp = p.health.max;
            yield return Put("den", 208, 200, Facing.Up);
            bed = Enemy.All.OfType<Underbed>().FirstOrDefault();
            Check($"and is there when he comes back with one ({Room})", Room == "den" && bed);
            if (!bed) yield break;
            // a bot: keeps away from the bed while it jumps, cuts whatever hand is in reach when it is safe to
            float start = Time.time, swing = 0;
            int hp0 = p.health.hp, jumps = 0, winded = 0;
            bool wasJumping = false, wasWinded = false, shotJump = false, shotWinded = false;
            while (bed && Time.time - start < 150f)
            {
                if (Story.I && Story.I.Running) { yield return null; continue; }
                if (bed.Jumping && !wasJumping) jumps++;
                if (bed.Winded && !wasWinded) winded++;
                wasJumping = bed.Jumping; wasWinded = bed.Winded;
                if (bed.Jumping && !shotJump && bed.Air > 0.4f) { shotJump = true; yield return t.Shot("v1-the-bed-gets-up", 0f); }
                if (bed.Winded && !shotWinded && bed.s == Underbed.S.Winded) { shotWinded = true; yield return t.Shot("v2-out-of-breath", 0.3f); }
                var d = bed.pos - p.pos;
                if (p.state == Player.State.Free)
                {
                    if (bed.Jumping)
                    {
                        // away from where it is coming down, and not out of the room
                        var den = Rooms.I.Find("den").rect;
                        Vector2 flee = p.pos - d.normalized * 2f;
                        if (flee.x < den.xMin + 2.5f || flee.x > den.xMax - 2.5f || flee.y < den.yMin + 2.5f || flee.y > den.yMax - 3.5f)
                            flee = den.center + new Vector2(-d.y, d.x).normalized * 3f;
                        Controls.Fake = d.magnitude < 4.6f ? (flee - p.pos).normalized : Vector2.zero;
                    }
                    else
                    {
                        // the nearest hand that is out
                        Reach best = null; float bd = 99;
                        foreach (var a in bed.arms) if (a && a.Out && !a.Has) { float q = Vector2.Distance(a.Hand, p.pos); if (q < bd) { bd = q; best = a; } }
                        if (best)
                        {
                            var to = best.Hand - p.pos;
                            if (to.magnitude > 1.1f) Controls.Fake = to.normalized;
                            else
                            {
                                Controls.Fake = Vector2.zero;
                                p.Face(Mathf.Abs(to.x) > Mathf.Abs(to.y) ? (to.x > 0 ? Facing.Right : Facing.Left) : (to.y > 0 ? Facing.Up : Facing.Down));
                                if (Time.time > swing) { Controls.FakePress = Controls.Attack; swing = Time.time + 0.24f; }
                            }
                        }
                        else Controls.Fake = d.magnitude > 3.2f ? d.normalized : Vector2.zero;
                    }
                }
                else
                {
                    Controls.Fake = Vector2.zero;
                    if (p.state == Player.State.Held && Time.time > swing) { Controls.FakePress = Controls.Attack; swing = Time.time + 0.16f; }
                }
                yield return null;
            }
            Controls.Fake = Vector2.zero;
            yield return Quiet(0.8f);
            Check($"it can be put down ({!bed}, flag {Story.Has("dead_crypt_mother")}, still in {Room}) in {Time.time - start:0}s: it got up {jumps} times, lay winded {winded} times, and cost him {hp0 - p.health.hp} of 40",
                  !bed && Story.Has("dead_crypt_mother") && jumps >= 1 && winded >= 1);
            for (float w = 0; w < 3f && cage && cage.solid != null; w += Time.deltaTime) yield return null;
            Check("the cage lifts", cage && cage.solid == null);
            Check("and the bed stays where it stopped, a bed", Npc.All.Any(n => n && n.id == "first_bed") && !Enemy.All.OfType<Reach>().Any());
            yield return t.Shot("v3-only-a-bed", 0.5f);
        }
    }
}
