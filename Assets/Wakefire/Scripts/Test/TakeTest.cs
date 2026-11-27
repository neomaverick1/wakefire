// The action button, where it used to say the wrong thing or nothing at all:  -wfScene take
//   every dream thing in the game is offered as "Take" from every side a man can stand on, asleep
//   (the blue fire burns in a bowl that can itself be looked at: the fire comes first), and the
//   fire really goes into the Pocket; and at the foot of a ladder or a stair, and back at the head
//   of one, the button says "Climb" and carries him the whole way without the stick being touched.
using System.Collections;
using System.Linq;
using UnityEngine;

namespace Wakefire
{
    public static partial class HousesTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void RegisterTake() => AutoTest.Scenes["take"] = RunTake;

        static IEnumerator RunTake(AutoTest t)
        {
            int bad = 0;
            void Check(string what, bool ok) { t.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
            DialogueBox.AutoAdvance = 0.1f;
            Save.ClearAll(); Save.Use(0);
            Game.I.Begin(false);
            Story.Abort();
            Story.GiveKit();
            Story.Set("item_pocket");
            Story.I.ApplyItems();
            var p = Player.I;

            // ------------------------------------------------------------------ every dream thing, from every side
            (Vector2 off, Facing face, string name)[] sides =
            {
                (new Vector2(0, -0.95f), Facing.Up, "below"), (new Vector2(0, 0.95f), Facing.Down, "above"),
                (new Vector2(-0.95f, 0.1f), Facing.Right, "the west"), (new Vector2(0.95f, 0.1f), Facing.Left, "the east"),
            };
            foreach (var map in new[] { "barrow", "tomb_1" })
            {
                yield return Enter(map, null);
                Away();
                Wakefire.Dream.I.Drowsiness = 1; Wakefire.Dream.I.Seconds = 9999; Wakefire.Dream.I.SetInstant(true);
                yield return new WaitForSeconds(0.3f);
                foreach (var pr in Map.Current.props.Where(q => q && q.Kind == "dreamthing").ToArray())
                {
                    int stood = 0, offered = 0;
                    string missed = "";
                    foreach (var s in sides)
                    {
                        var at = pr.basePos + s.off;
                        p.DropRail();
                        p.pos = at; p.transform.position = new Vector3(at.x, at.y, 0);
                        if (Rooms.I) Rooms.I.Jump(at);
                        PixelView.I.SnapTo(at);
                        p.Face(s.face);
                        p.SetState(Player.State.Free, "idle");
                        Wakefire.Dream.I.SetInstant(true);
                        Away();
                        yield return new WaitForSeconds(0.2f);
                        if (Vector2.Distance(p.pos, at) > 0.25f) continue;         // no standing there: a wall, a drop
                        stood++;
                        p.Face(s.face);
                        yield return null; yield return null;
                        if (p.Action == Player.Act.Take) offered++; else missed += " " + s.name + "(" + p.Action + ")";
                    }
                    Check($"{map}: the {pr.data.text} ({pr.data.id}) is offered from every side he can stand on: {offered} of {stood}{(missed == "" ? "" : ", not from" + missed)}", stood > 0 && offered == stood);
                    if (pr.data.text == "flame")
                    {
                        // and it goes in: from the west, where the bowl used to answer instead
                        var at = pr.basePos + sides[3].off;
                        p.pos = at; p.transform.position = new Vector3(at.x, at.y, 0);
                        p.Face(Facing.Left);
                        p.SetState(Player.State.Free, "idle");
                        yield return new WaitForSeconds(0.2f);
                        Story.Abort();
                        Controls.FakePress = Controls.Interact;
                        yield return new WaitForSeconds(0.3f);
                        yield return Scene(1.0f);
                        Check($"the blue fire comes away into the Pocket: holding {(Pocket.Holding != null ? Pocket.Holding.id : "nothing")}", Pocket.Holding != null && Pocket.Holding.id == "flame");
                        yield return t.Shot("k0-the-blue-fire", 0.2f);
                    }
                }
                Wakefire.Dream.I.SetInstant(false);
            }
            Story.I.ApplyItems(); Wakefire.Dream.I.Drowsiness = 1;

            // ------------------------------------------------------------------ Climb, by the button alone
            yield return Enter("lowtown", "north");
            Away();
            bool rode;
            // the ladder up the house the goat stands on, from a little to one side of its foot
            yield return Put(392, 192, Facing.Up);
            yield return null; yield return null;
            Check($"at the foot of a ladder the button says Climb ({p.Action})", p.Action == Player.Act.Climb);
            yield return t.Shot("k1-climb-at-a-ladder", 0.2f);
            Controls.FakePress = Controls.Interact;
            rode = false;
            yield return Walk(Vector2.zero, 5f, () => { rode |= p.OnRail; return rode && !p.OnRail; }, 0.3f);
            Check($"one press and he climbs it to the roof, the stick untouched: {Px}", rode && Px.y < 150);
            yield return null; yield return null;
            Check($"at the head of it the button says Climb again ({p.Action})", p.Action == Player.Act.Climb);
            Controls.FakePress = Controls.Interact;
            rode = false;
            yield return Walk(Vector2.zero, 5f, () => { rode |= p.OnRail; return rode && !p.OnRail; }, 0.3f);
            Check($"and one press brings him down again: {Px}", rode && Px.y > 176);
            // the stair up the front of the bakery
            yield return Put(184, 618, Facing.Right);
            yield return null; yield return null;
            Check($"at the foot of a stair the button says Climb ({p.Action})", p.Action == Player.Act.Climb);
            Controls.FakePress = Controls.Interact;
            rode = false;
            yield return Walk(Vector2.zero, 5f, () => { rode |= p.OnRail; return rode && !p.OnRail; }, 0.3f);
            Check($"one press and he walks up it on to the roof: {Px}", rode && Px.y < 578 && Px.x > 215);
            // half way up, pushed back the way he came, he turns round
            Controls.FakePress = Controls.Interact;
            yield return Walk(Vector2.zero, 0.5f);
            Check("he is on the stair again, going down", p.OnRail);
            yield return Walk(Vector2.right, 4f, () => !p.OnRail, 0.3f);
            Check($"pushed back up it while on it, he turns and comes out on the roof: {Px}", Px.y < 578);
            t.Note(bad == 0 ? "TAKE OK" : $"FAILED {bad}");
        }
    }
}
