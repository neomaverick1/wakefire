// What the dungeons do not put on their plans, and the floors above the floor:  -wfScene secrets
// walks the crypt (a terrace, its ledge and its steps; the jackals' burrow and the larder), the
// ziggurat (a walled-up doorway and the room behind it, the stair that goes up from that room, the
// stair that waits under the counting room, the oil chute and the store it comes down in), the
// barrow (a doorway only a dreamer has, and the gallery), and the king's tomb (down the well into
// the cistern and up the ladder, the queen's wall and the Sun Wheel, the dead letter room).
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class SecretsTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["secrets"] = Run;

        static Vector2 InRoom(string id, float x, float y)
        {
            var r = Rooms.I.Find(id);
            return new Vector2(r.rect.xMin + x / 16f, r.rect.yMax - y / 16f);
        }

        /// <summary>Where he is in a room, in the map's own pixels from the room's corner.</summary>
        static Vector2 Where(string id)
        {
            var r = Rooms.I.Find(id);
            var p = Player.I.pos;
            return new Vector2((p.x - r.rect.xMin) * 16f, (r.rect.yMax - p.y) * 16f);
        }

        static IEnumerator Scene(float atLeast = 0.4f, float atMost = 60f)
        {
            float w = 0;
            while ((w < atLeast || (Story.I && Story.I.Running) || Game.Busy || Rooms.Sliding) && w < atMost) { w += Time.deltaTime; yield return null; }
        }

        /// <summary>Put him somewhere on the floor (in any room of it) and let the picture catch up with him.</summary>
        static IEnumerator Stand(string room, float x, float y, Facing face)
        {
            var p = Player.I;
            var at = InRoom(room, x, y);
            p.pos = at;
            p.transform.position = new Vector3(at.x, at.y, 0);
            if (Rooms.I) Rooms.I.Jump(at);
            PixelView.I.SnapTo(at);
            p.Face(face);
            p.SetState(Player.State.Free, "idle");
            yield return Scene(0.25f);
            p.pos = at;
            p.Face(face);
            p.health.hp = p.health.max;
            yield return new WaitForSeconds(0.1f);
        }

        /// <summary>The stick held one way while he is free to walk, until `until` holds or the time is up.</summary>
        static IEnumerator Walk(Vector2 dir, float seconds, System.Func<bool> until = null, float settle = 0.3f)
        {
            var p = Player.I;
            for (float w = 0; w < seconds; w += Time.deltaTime)
            {
                Controls.Fake = p.state == Player.State.Free ? dir : Vector2.zero;
                if (until != null && until()) break;
                yield return null;
            }
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(settle);
        }

        static void KillAll()
        {
            var p = Player.I;
            foreach (var e in Enemy.All.ToArray())
                if (e && !e.health.Dead) e.Hit(new HitInfo { damage = 99, from = p.pos, knockback = 0, kind = HitKind.Reflected, source = p.gameObject });
        }

        static void Away()
        {
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
        }

        /// <summary>The three cuts, one after another: the third is the one with his weight behind it.</summary>
        static IEnumerator ThreeCuts()
        {
            for (int i = 0; i < 3; i++)
            {
                Controls.FakePress = Controls.Attack;
                yield return new WaitForSeconds(0.3f);
            }
            yield return new WaitForSeconds(0.7f);
        }

        static IEnumerator Dream(bool on)
        {
            var p = Player.I;
            if (on) { Wakefire.Dream.I.Drowsiness = 1; Wakefire.Dream.I.Seconds = 9999; Wakefire.Dream.I.Flip(p.pos, true); yield return new WaitForSeconds(1.2f); }
            else { Wakefire.Dream.I.Flip(p.pos, false); yield return new WaitForSeconds(1.2f); Wakefire.Dream.I.SetInstant(false); Story.I.ApplyItems(); Wakefire.Dream.I.Drowsiness = 1; }
        }

        static IEnumerator Enter(string map, string spawn)
        {
            Game.I.EnterMap(map, spawn);
            Story.Abort();
            Fade.Set(0);
            Player.I.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.5f);
            yield return Scene(0.2f);
        }

        static bool Shown(string kind, string id)
        {
            foreach (var pr in Map.Current.props) if (pr && pr.Kind == kind && pr.data.id == id) return pr.sr.enabled;
            return false;
        }

        static int Count(string kind, string id)
        {
            int n = 0;
            foreach (var pr in Map.Current.props) if (pr && pr.Kind == kind && pr.data.id == id) n++;
            return n;
        }

        static IEnumerator Run(AutoTest t)
        {
            int bad = 0;
            void Check(string what, bool ok) { t.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
            DialogueBox.AutoAdvance = 0.1f;
            Save.ClearAll(); Save.Use(0);
            Game.I.Begin(false);
            Story.Abort();
            Story.GiveKit();
            Story.Set("item_shield"); Story.Set("item_wheel");
            Story.I.ApplyItems();
            var p = Player.I;
            Vector2 at;

            // ================================================================== the crypt
            yield return Enter("crypt", "south");
            Away();
            // ------------------------------------------------ a floor above the floor
            yield return Stand("stair", 300, 76, Facing.Down);
            yield return Walk(Vector2.down, 0.12f, null, 0.05f);
            at = Where("stair");
            Check($"on the terrace, walking at its edge: the edge holds him for a moment (y {at.y:0})", at.y < 90 && !p.Hopping);
            bool hopped = false;
            yield return Walk(Vector2.down, 1.2f, () => { hopped |= p.Hopping; return hopped && !p.Hopping && p.state == Player.State.Free; });
            at = Where("stair");
            Check($"leaning on it, he hops down to the floor below (y {at.y:0}, life {p.health.hp} of {p.health.max})", hopped && at.y > 104 && at.y < 130 && p.health.hp == p.health.max);
            yield return t.Shot("c0-hopped-down", 0.1f);
            yield return Walk(Vector2.up, 0.8f);
            at = Where("stair");
            Check($"from below, the face of it is a wall (y {at.y:0})", at.y > 104);
            yield return Stand("stair", 208, 132, Facing.Up);
            yield return Walk(Vector2.up, 1.4f, () => Where("stair").y < 80);
            at = Where("stair");
            Check($"the flight of steps takes him up (y {at.y:0})", at.y < 86);
            yield return t.Shot("c1-up-the-steps", 0.1f);
            // ------------------------------------------------ the way the jackals go
            yield return Stand("beds", 410, 70, Facing.Up);
            Away();
            yield return t.Shot("c2-the-burrow", 0.1f);
            yield return Walk(Vector2.up, 1.5f, () => Game.Busy);
            yield return Scene(0.5f);
            Check($"into the hole at the foot of the dormitory wall, and out in a room that is on no plan ({Rooms.I.current.id}: {Rooms.I.current.name})",
                Rooms.I.current.id == "larder" && Story.Has(Rooms.VisitedFlag("crypt", "larder")));
            Check($"the game has said so, once ({Story.Count("secret_room")}), and what the way in was like ({Story.Count("burrowed")})", Story.Count("secret_room") == 1 && Story.Count("burrowed") == 1);
            Away();
            yield return t.Shot("c3-the-larder", 0.2f);
            int coins = p.coins;
            var chest = Map.Current.Find("crypt_larder");
            p.pos = chest.basePos + new Vector2(0, -0.7f); p.Face(Facing.Up);
            yield return new WaitForSeconds(0.2f);
            Controls.FakePress = Controls.Interact;
            yield return Scene(0.5f);
            Check($"what the jackals were keeping ({coins} -> {p.coins})", p.coins > coins);
            yield return Stand("larder", 150, 152, Facing.Up);
            yield return Walk(Vector2.up, 1.5f, () => Game.Busy);
            yield return Scene(0.5f);
            Check($"and back the way he came ({Rooms.I.current.id})", Rooms.I.current.id == "beds");
            // ------------------------------------------------ the larder's own stair, and the stone that stands on it
            yield return Stand("larder", 208, 104, Facing.Up);
            Away();
            yield return Walk(Vector2.up, 2.0f, () => Game.Busy);
            yield return Scene(1.0f);
            var stone = Map.Current.Find("crypt_block2");
            float moved = stone ? Vector2.Distance(stone.basePos, InRoom("lamps", 240, 168)) : -1;
            Check($"the larder's own stair comes up in the hall of lamps ({Rooms.I.current.id}), and the stone that stood on it has gone first (moved {moved:0.0})",
                Rooms.I.current.id == "lamps" && moved > 0.8f);
            Away();
            yield return t.Shot("c4-up-under-the-stone", 0.2f);
            yield return Enter("crypt", "south");
            Away();
            yield return Stand("lamps", 240, 178, Facing.Up);
            Away();
            stone = Map.Current.Find("crypt_block2");
            Check($"come at from above, the stone is standing on it again ({(stone ? Vector2.Distance(stone.basePos, InRoom("lamps", 240, 168)) : -1):0.0})",
                stone && Vector2.Distance(stone.basePos, InRoom("lamps", 240, 168)) < 0.1f);
            yield return Walk(Vector2.up, 4f, () => Game.Busy);
            yield return Scene(1.0f);
            Check($"lean on the stone, it goes, and the stair under it goes down to the larder ({Rooms.I.current.id})", Rooms.I.current.id == "larder");

            // ================================================================== the ziggurat
            yield return Enter("zig_1", "south");
            Away();
            var plan = Dungeons.FloorOf(Dungeons.Of("zig_1"), "zig_1");
            bool onPlan = false;
            foreach (var q in plan.rooms) if (q.id == "twelfth") onPlan = q.secret;
            Check($"the plan knows the twelfth room for what it is ({onPlan})", onPlan);
            // ------------------------------------------------ a doorway somebody walled up
            yield return Stand("west", 30, 128, Facing.Left);
            Away();
            Check($"the weighing room's west wall has a crack in it ({Count("crack", "z1_crack")}), and no doorway to show ({Shown("breach", "z1_crack")})",
                Count("crack", "z1_crack") >= 1 && !Shown("breach", "z1_crack"));
            yield return t.Shot("z0-a-crack", 0.1f);
            yield return Walk(Vector2.left, 0.6f);
            Check($"it is a wall ({Rooms.I.current.id})", Rooms.I.current.id == "west");
            p.Face(Facing.Left);
            Controls.FakePress = Controls.Attack;
            yield return new WaitForSeconds(0.9f);
            yield return Scene(0.3f);
            Check($"a cut rings on it and leaves it standing ({Story.Has("door_z1_crack")}; said {Story.Count("wall_hollow")})", !Story.Has("door_z1_crack") && Story.Count("wall_hollow") == 1);
            yield return Stand("west", 30, 128, Facing.Left);
            yield return ThreeCuts();
            yield return Scene(0.4f);
            Check($"the third blow of three brings it down, both sides, for good ({Story.Has("door_z1_crack")}; cracks left {Count("crack", "z1_crack")}; doorway {Shown("breach", "z1_crack")})",
                Story.Has("door_z1_crack") && Count("crack", "z1_crack") == 0 && Shown("breach", "z1_crack"));
            yield return t.Shot("z1-the-wall-down", 0.1f);
            yield return Walk(Vector2.left, 2.2f, () => Rooms.I.current.id == "twelfth" && !Rooms.Sliding);
            yield return Scene(0.5f);
            Check($"and behind it, the room the plans do not show ({Rooms.I.current.id})", Rooms.I.current.id == "twelfth");
            yield return t.Shot("z2-the-twelfth-room", 0.3f);
            // ------------------------------------------------ its own stair
            yield return Stand("twelfth", 208, 100, Facing.Up);
            yield return Walk(Vector2.up, 2.0f, () => Game.I.CurrentMap == "zig_2");
            yield return Scene(0.6f);
            Away();
            Check($"its stair comes up through the floor of the counting room ({Game.I.CurrentMap}/{Rooms.I.current.id}), which now has a stair in its floor ({Story.Has("open_z2_hatch")}, shown {Shown("hatch", "z2_hatch")})",
                Game.I.CurrentMap == "zig_2" && Rooms.I.current.id == "count" && Story.Has("open_z2_hatch") && Shown("hatch", "z2_hatch"));
            yield return t.Shot("z3-up-through-the-floor", 0.2f);
            // ------------------------------------------------ the stair that waits
            Story.Clear("open_z2_hatch"); Story.Clear(Mech.ClearFlag("zig_2", "count"));
            yield return Enter("zig_2", "south");
            yield return Stand("count", 208, 120, Facing.Down);
            yield return new WaitForSeconds(0.3f);
            Check($"come at from the walk, the counting room shows no stair ({Shown("hatch", "z2_hatch")}) while its sentinels stand ({Rooms.I.Left(Rooms.I.current)})",
                !Shown("hatch", "z2_hatch") && Rooms.I.Left(Rooms.I.current) == 2);
            KillAll();
            yield return new WaitForSeconds(0.8f);
            yield return Scene(0.5f);
            Check($"with nobody left to see who uses it, it shows itself ({Shown("hatch", "z2_hatch")}, {Story.Has("open_z2_hatch")})", Shown("hatch", "z2_hatch") && Story.Has("open_z2_hatch"));
            yield return t.Shot("z4-the-stair-that-waits", 0.2f);
            yield return Stand("count", 208, 196, Facing.Up);
            yield return Walk(Vector2.up, 1.5f, () => Game.I.CurrentMap == "zig_1");
            yield return Scene(0.6f);
            Check($"and it goes down to the twelfth room ({Game.I.CurrentMap}/{Rooms.I.current.id})", Game.I.CurrentMap == "zig_1" && Rooms.I.current.id == "twelfth");
            // ------------------------------------------------ the oil chute
            yield return Enter("zig_hi", "south");
            Away();
            yield return Stand("landing", 306, 100, Facing.Right);
            yield return t.Shot("z5-the-chute", 0.1f);
            int hp = p.health.hp;
            yield return Walk(Vector2.right, 3f, () => Game.I.CurrentMap == "zig_2");
            yield return Scene(1.2f);
            Check($"he leans on the lip of the oil chute, and goes down it ({Game.I.CurrentMap}/{(Rooms.I ? Rooms.I.current.id : "?")}), on his feet ({p.state}), none the worse (life {hp} -> {p.health.hp})",
                Game.I.CurrentMap == "zig_2" && Rooms.I.current.id == "oil" && p.state == Player.State.Free && p.health.hp == hp);
            Check($"the game says what that was ({Story.Count("came_down")})", Story.Count("came_down") == 1);
            yield return t.Shot("z6-the-oil-store", 0.3f);
            // ------------------------------------------------ out through the wall, from the inside
            yield return Stand("oil", 208, 198, Facing.Down);
            yield return ThreeCuts();
            yield return Scene(0.4f);
            Check($"the store's own wall comes down from the inside ({Story.Has("door_z2_crack")})", Story.Has("door_z2_crack"));
            yield return Walk(Vector2.down, 2.4f, () => Rooms.I.current.id == "feed" && !Rooms.Sliding);
            yield return Scene(0.4f);
            Check($"and lets him out into the feed way ({Rooms.I.current.id})", Rooms.I.current.id == "feed");
            yield return t.Shot("z7-out-into-the-feed-way", 0.2f);
            // ------------------------------------------------ the great door's terrace
            yield return Enter("zig_hi", "south");
            Away();
            yield return Stand("door", 208, 160, Facing.Up);
            Away();
            yield return Scene(0.3f);
            yield return Walk(Vector2.up, 1.6f, () => Where("door").y < 100);
            Check($"the great door stands at the head of its own flight (y {Where("door").y:0})", Where("door").y < 104);
            yield return t.Shot("z8-the-great-door", 0.2f);

            // ================================================================== the barrow
            yield return Enter("barrow", "south");
            Away();
            yield return Stand("pass2", 34, 130, Facing.Left);
            yield return Walk(Vector2.left, 0.8f);
            Check($"awake, the passage that goes west stops at a wall ({Rooms.I.current.id})", Rooms.I.current.id == "pass2");
            yield return t.Shot("b0-a-wall", 0.1f);
            yield return Dream(true);
            yield return t.Shot("b1-a-doorway", 0.1f);
            yield return Walk(Vector2.left, 2.4f, () => Rooms.I.current.id == "gallery" && !Rooms.Sliding);
            yield return Scene(0.5f);
            Check($"asleep, it is a doorway, and beyond it the gallery ({Rooms.I.current.id})", Rooms.I.current.id == "gallery");
            yield return Dream(false);
            yield return Scene(0.3f);
            int clay = 0, stirred = 0;
            foreach (var e in Enemy.All) if (e is ClaySoldier && !e.health.Dead) clay++;
            yield return new WaitForSeconds(1.5f);
            foreach (var e in Enemy.All) if (e is ClaySoldier && Vector2.Distance(e.pos, e.home) > 0.3f) stirred++;
            Check($"both armies' off-duty sit in it ({clay}), and none of them gets up for a watchman ({stirred})", clay == 6 && stirred == 0);
            yield return Stand("gallery", 248, 190, Facing.Up);
            yield return t.Shot("b2-the-gallery", 0.2f);
            yield return Walk(Vector2.up, 2.6f, () => Where("gallery").y < 90);
            Check($"two flights take him up its two tiers (y {Where("gallery").y:0})", Where("gallery").y < 96);
            yield return t.Shot("b3-the-top-tier", 0.2f);
            yield return Stand("gallery", 340, 130, Facing.Right);
            hopped = false;
            yield return Walk(Vector2.right, 1.4f, () => { hopped |= p.Hopping; return hopped && !p.Hopping && p.state == Player.State.Free; });
            Check($"and off the side of a tier he hops down (x {Where("gallery").x:0})", hopped && Where("gallery").x > 368);

            // ================================================================== the king's tomb
            yield return Enter("tomb_1", "south");
            Away();
            yield return Stand("well", 136, 128, Facing.Right);
            yield return t.Shot("t0-the-well", 0.1f);
            hp = p.health.hp;
            yield return Walk(Vector2.right, 3f, () => Rooms.I.current.id == "cistern");
            yield return Scene(1.2f);
            Check($"down the well ({Rooms.I.current.id}: {Rooms.I.current.name}), on his feet ({p.state}), none the worse (life {hp} -> {p.health.hp})",
                Rooms.I.current.id == "cistern" && p.state == Player.State.Free && p.health.hp == hp);
            Away();
            yield return t.Shot("t1-the-cistern", 0.3f);
            yield return Stand("cistern", 150, 70, Facing.Up);
            yield return Walk(Vector2.up, 1.5f, () => Game.Busy);
            yield return Scene(0.5f);
            at = Where("well");
            Check($"and up the ladder, out on the side he went in from ({Rooms.I.current.id}, x {at.x:0})", Rooms.I.current.id == "well" && at.x < 152);
            // ------------------------------------------------ the queen's wall, and the wheel
            yield return Enter("tomb_2", "south");
            Away();
            yield return Stand("queen", 340, 128, Facing.Right);
            Away();
            yield return t.Shot("t2-the-queens-wall", 0.1f);
            p.ThrowWheel(Vector2.right);
            yield return new WaitForSeconds(1.6f);
            yield return Scene(0.6f);
            Check($"the Sun Wheel does not care about walls: hers comes down ({Story.Has("door_t2_crack")})", Story.Has("door_t2_crack"));
            yield return Walk(Vector2.right, 2.4f, () => Rooms.I.current.id == "faraway" && !Rooms.Sliding);
            yield return Scene(0.5f);
            Check($"and behind it, as far away as she could get ({Rooms.I.current.id}: {Rooms.I.current.name})", Rooms.I.current.id == "faraway");
            yield return t.Shot("t3-further-away", 0.3f);
            // ------------------------------------------------ the dead letter room
            yield return Enter("tomb_hi", "south");
            Away();
            yield return Stand("stairhead", 388, 128, Facing.Right);
            Away();
            yield return Walk(Vector2.right, 0.8f);
            Check($"awake, the stair head's east wall is a wall ({Rooms.I.current.id})", Rooms.I.current.id == "stairhead");
            yield return Dream(true);
            yield return Walk(Vector2.right, 2.4f, () => Rooms.I.current.id == "letters" && !Rooms.Sliding);
            yield return Scene(0.5f);
            Check($"asleep, the clerk's doorway ({Rooms.I.current.id}: {Rooms.I.current.name})", Rooms.I.current.id == "letters");
            yield return Dream(false);
            yield return Scene(0.3f);
            yield return t.Shot("t4-the-dead-letter-room", 0.3f);
            // ------------------------------------------------ the king's terrace
            yield return Stand("threshold", 208, 150, Facing.Up);
            Away();
            yield return Scene(0.3f);
            yield return Walk(Vector2.up, 1.6f, () => Where("threshold").y < 84);
            Check($"the king's door stands at the head of its own flight (y {Where("threshold").y:0})", Where("threshold").y < 88);
            yield return t.Shot("t5-the-kings-terrace", 0.2f);
            Check($"seven rooms on no plan stood in ({Story.Count("secret_room")}), three walls brought down ({Story.Count("wall_down")})", Story.Count("secret_room") == 7 && Story.Count("wall_down") == 3);
            // ------------------------------------------------ what the map page knows
            Story.Set("item_map_tomb");
            var tomb = Dungeons.Of("tomb_hi");
            int hidden = 0, plain = 0;
            foreach (var fl in tomb.floors) foreach (var q in fl.rooms) { if (q.secret) hidden++; else plain++; }
            Check($"the tomb's plan has {plain} rooms a scroll would show and {hidden} it would not", hidden == 3 && plain > 15);
            t.Note(bad == 0 ? "SECRETS OK" : $"FAILED {bad}");
        }
    }
}
