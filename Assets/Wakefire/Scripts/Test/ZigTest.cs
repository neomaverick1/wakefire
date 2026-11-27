// The ziggurat above its first floor, played through: -wfScene zig takes Azar from the head of the
// first stair to the summit the way a player has to. The walk of fire and its key, the counting
// room, the Herdsman and the shield he keeps, the bull that shuts the stair, two sun discs (one of
// them across a drop only a dreamer crosses), three mouths, the Bull Key and the great door.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class ZigTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["zig"] = Run;

        static Vector2 InRoom(string id, float x, float y)
        {
            var r = Rooms.I.Find(id);
            return new Vector2(r.rect.xMin + x / 16f, r.rect.yMax - y / 16f);
        }

        static IEnumerator Walk(Vector2 dir, float seconds, float settle = 0.9f)
        {
            Controls.Fake = dir;
            yield return new WaitForSeconds(seconds);
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(settle);
        }

        static IEnumerator Scene(float atLeast = 0.4f, float atMost = 60f)
        {
            float w = 0;
            while ((w < atLeast || (Story.I && Story.I.Running) || Game.Busy) && w < atMost) { w += Time.deltaTime; yield return null; }
        }

        /// <summary>Put him somewhere on the floor and let the picture catch up with him.</summary>
        static IEnumerator Stand(string room, float x, float y, Facing face)
        {
            var p = Player.I;
            p.pos = InRoom(room, x, y);
            p.Face(face);
            yield return null; yield return null;
            for (float s = 0; s < 3f && (Rooms.Sliding || Game.Busy); s += Time.deltaTime) yield return null;
            yield return Scene(0.2f);
            p.pos = InRoom(room, x, y);
            p.Face(face);
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.15f);
        }

        static IEnumerator Press(UnityEngine.InputSystem.InputAction a, float wait = 0.3f)
        {
            Controls.FakePress = a;
            yield return new WaitForSeconds(wait);
        }

        static void KillAll()
        {
            var p = Player.I;
            foreach (var e in Enemy.All.ToArray())
                if (e && !e.health.Dead) e.Hit(new HitInfo { damage = 99, from = p.pos, knockback = 0, kind = HitKind.Reflected, source = p.gameObject });
        }

        static int Count<T>() where T : Enemy
        {
            int n = 0;
            foreach (var e in Enemy.All) if (e is T && !e.health.Dead) n++;
            return n;
        }

        /// <summary>Hold the shield up, facing north, until `until` holds or the time runs out.</summary>
        static IEnumerator Guard(System.Func<bool> until, float atMost)
        {
            var p = Player.I;
            Controls.FakeHold = Controls.Interact; Controls.FakePress = Controls.Interact;
            for (float held = 0; held < atMost && !until(); held += Time.deltaTime)
            {
                if (p.state == Player.State.Free) { p.Face(Facing.Up); Controls.FakePress = Controls.Interact; }
                yield return null;
            }
            Controls.FakeHold = null;
            yield return new WaitForSeconds(0.3f);
        }

        static IEnumerator Open(string id)
        {
            var p = Player.I;
            var pr = Map.Current.Find(id);
            if (!pr) yield break;
            p.pos = pr.basePos + new Vector2(0, -0.7f); p.Face(Facing.Up);
            yield return new WaitForSeconds(0.2f);
            yield return Press(Controls.Interact);
            yield return Scene();
        }

        static IEnumerator Run(AutoTest t)
        {
            int bad = 0;
            void Check(string what, bool ok) { t.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
            Save.ClearAll(); Save.Use(0);
            DialogueBox.AutoAdvance = 0.1f;
            Game.I.Begin(false);
            Story.Abort();
            Story.GiveKit();                              // as he comes up the first stair: the blade and the flame, no shield yet
            // ------------------------------------------------ the tuning fork, in the stair hall on the way up
            Game.I.EnterMap("zig_1", "top");
            Fade.Set(0);
            var p = Player.I;
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.5f);
            KillAll();
            yield return new WaitForSeconds(0.5f);
            Check($"no fork yet ({Fork.Owns("zig")}), and the item button has the {Items.Current?.id}", !Fork.Owns("zig") && Items.Current != null && Items.Current.id == "wakefire");
            yield return Open("z1_fork");
            Check($"the stair hall's chest has the ziggurat's fork ({Fork.Owns("zig")})", Fork.Owns("zig") && Items.Find("fork").have());
            Items.Choose("fork");
            Check($"it goes on the item button ({Items.Current?.id}) in the ziggurat's colour ({Items.Current?.Art})", Items.Current != null && Items.Current.id == "fork" && Items.Current.Art == "fork_zig");
            yield return Stand("stair", 208, 150, Facing.Down);
            yield return Press(Controls.Item, 0.25f);
            Check($"struck here it answers that a chest is shut next door ({Fork.Last}): the broken floor ({Story.Has(Fork.FoundFlag("zig_1", "gap"))}) and the vault ({Story.Has(Fork.FoundFlag("zig_1", "vault"))}) go on the plan, this room does not ({Story.Has(Fork.FoundFlag("zig_1", "stair"))})",
                Fork.Last == 1 && Story.Has(Fork.FoundFlag("zig_1", "gap")) && Story.Has(Fork.FoundFlag("zig_1", "vault")) && !Story.Has(Fork.FoundFlag("zig_1", "stair")) && p.state == Player.State.Use);
            yield return t.Shot("z00-fork-next-door", 0.15f);
            yield return new WaitForSeconds(1.0f);
            Check($"and he is let go again ({p.state})", p.state == Player.State.Free);
            yield return Stand("gap", 340, 130, Facing.Down);
            yield return Press(Controls.Item, 0.25f);
            Check($"in the room with the chest it gives its highest answer ({Fork.Last})", Fork.Last == 2);
            yield return t.Shot("z00-fork-here", 0.15f);
            yield return new WaitForSeconds(1.0f);
            yield return Open("z1_coins");
            yield return Stand("gap", 340, 130, Facing.Down);
            yield return Press(Controls.Item, 0.25f);
            Check($"with that chest opened and nothing shut next door, a plain note ({Fork.Last})", Fork.Last == 0);
            yield return new WaitForSeconds(1.0f);
            Pause.TestDo = "open";
            yield return new WaitForSecondsRealtime(0.3f);
            Pause.TestDo = "page " + Pause.MapPage;
            yield return new WaitForSecondsRealtime(0.2f);
            yield return t.Shot("z00-fork-plan", 0.2f);
            Pause.TestDo = "close";
            yield return new WaitForSecondsRealtime(0.3f);
            // it is the ziggurat's: outside, it is not in the pack at all
            Game.I.EnterMap("temple_yard", "door");
            Fade.Set(0);
            Story.Abort();
            yield return new WaitForSeconds(0.4f);
            Check($"outside the ziggurat the fork is not in the pack ({Items.Find("fork").have()}), and the item button goes back to the {Items.Current?.id}",
                !Items.Find("fork").have() && Items.Current != null && Items.Current.id == "wakefire");
            Game.I.EnterMap("zig_1", "south");
            Fade.Set(0);
            yield return new WaitForSeconds(0.4f);
            Check($"back inside it is in the pack and on the item button again ({Items.Current?.id})", Items.Find("fork").have() && Items.Current != null && Items.Current.id == "fork");
            Items.Choose("wakefire");
            // ------------------------------------------------ the second floor
            Game.I.EnterMap("zig_2", "south");
            Fade.Set(0);
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.5f);
            Check($"the second floor has rooms ({(Rooms.I ? Rooms.I.all.Count : 0)}), and he is on the landing ({Rooms.I?.current?.id}) with no shield ({p.hasShield})",
                Rooms.I && Rooms.I.all.Count == 9 && Rooms.I.current.id == "landing" && !p.hasShield);
            yield return t.Shot("z01-landing", 0.2f);
            yield return Stand("landing", 208, 60, Facing.Up);
            yield return Walk(Vector2.up, 0.5f);
            Check($"the door north is locked ({Rooms.I.current.id})", Rooms.I.current.id == "landing");
            yield return Scene();
            // ------------------------------------------------ the bull walk
            yield return Stand("landing", 30, 130, Facing.Left);
            yield return Walk(Vector2.left, 0.8f);
            Check($"west is the bull walk ({Rooms.I.current.id}), and it has something to say", Rooms.I.current.id == "walk" && Story.I.Running);
            yield return Scene();
            int straight = 0;
            foreach (var h in Object.FindObjectsByType<BullHead>(FindObjectsSortMode.None)) if (h.straight && Rooms.Of(h.prop.basePos + new Vector2(0, -1f)) == Rooms.I.current) straight++;
            Check($"eight heads breathe down it in turn ({straight}), and it is two halls long ({Rooms.I.current.rect.width:0} tiles)", straight == 8 && Rooms.I.current.rect.width > 50f);
            yield return t.Shot("z02-bull-walk", 1.2f);
            yield return Stand("walk", 336, 150, Facing.Up);
            int hp0 = p.health.hp;
            // (the fifth head of eight: it first breathes 4.8 s after the hall wakes, and the fire is 1.2 s coming down)
            for (float w = 0; w < 8f && p.health.hp >= hp0; w += Time.deltaTime) yield return null;
            Check($"standing in a lane gets him burnt ({hp0} -> {p.health.hp})", p.health.hp < hp0);
            p.health.Heal(99);
            // between the lanes nothing reaches him
            yield return Stand("walk", 304, 150, Facing.Up);
            hp0 = p.health.hp;
            yield return new WaitForSeconds(3.4f);
            Check($"standing between two lanes does not ({hp0} -> {p.health.hp})", p.health.hp == hp0);
            int keys0 = p.keys;
            yield return Open("z2_key");
            Check($"the key is at the far end ({p.keys})", p.keys == keys0 + 1);
            // ------------------------------------------------ the counting room
            yield return Stand("walk", 624, 62, Facing.Up);
            yield return Walk(Vector2.up, 1.2f);
            Check($"north of the walk is the counting room ({Rooms.I.current.id}), with {Count<Sentinel>()} sentinels", Rooms.I.current.id == "count" && Count<Sentinel>() == 2);
            KillAll();
            yield return new WaitForSeconds(0.6f);
            yield return Scene(0.6f);
            Check($"with nobody left to see who uses it, the stair under the counting room's floor shows itself ({Story.Has("open_z2_hatch")})", Story.Has("open_z2_hatch"));
            int coins0 = p.coins;
            yield return Open("z2_coins");
            Check($"what the temple was owed ({coins0} -> {p.coins})", p.coins > coins0);
            // ------------------------------------------------ the Herdsman
            yield return Stand("landing", 208, 60, Facing.Up);
            yield return Press(Controls.Interact, 0.5f);
            Check($"the key opens the landing's north door ({Story.Has("door_z2_door")})", Story.Has("door_z2_door") && p.keys == keys0);
            yield return Walk(Vector2.up, 1.3f, 0.5f);
            Check($"north is the Herdsman's own stair ({Rooms.I.current.id})", Rooms.I.current.id == "climb");
            yield return Stand("climb", 208, 62, Facing.Up);
            yield return Walk(Vector2.up, 1.3f, 0.5f);
            Check($"and at the top of it his hall ({Rooms.I.current.id}), and he is in ({Count<Herdsman>()})", Rooms.I.current.id == "herd" && Count<Herdsman>() == 1);
            yield return Scene();
            var cage = Map.Current.Find("z2_cage");
            Check("the shield's cage is shut", cage && cage.solid != null);
            int dormant = 0;
            foreach (var h in Object.FindObjectsByType<BullHead>(FindObjectsSortMode.None)) if (h.dormant) dormant++;
            Check($"two of his herd are in the wall, asleep ({dormant})", dormant == 2);
            yield return t.Shot("z03-herdsman", 0.6f);
            // keep clear of him and see whether the heads answer the goad
            Herdsman herd = null;
            foreach (var e in Enemy.All) if (e is Herdsman hh) herd = hh;
            int fire = 0; bool called = false;
            // two corners well away from the door he came in by: whenever the Herdsman gets near one, go to the other
            var corners = new[] { InRoom("herd", 56, 190), InRoom("herd", 360, 190) };
            int corner = 0;
            for (float w = 0; w < 16f && fire == 0; w += Time.deltaTime)
            {
                foreach (var e in Enemy.All) if (e is Herdsman hh) herd = hh;
                if (!herd) break;
                if (Vector2.Distance(herd.pos, corners[corner]) < 4.2f) corner = 1 - corner;
                var to = corners[corner] - p.pos;
                Controls.Fake = to.magnitude > 0.4f ? to.normalized : Vector2.zero;
                called |= herd.Calling;
                fire = Object.FindObjectsByType<Projectile>(FindObjectsSortMode.None).Length;
                yield return null;
            }
            Controls.Fake = Vector2.zero;
            Check($"he stays in the hall while he keeps his distance ({Rooms.I.current.id})", Rooms.I.current.id == "herd" && herd);
            Check($"when he raises the goad they breathe (called {called}, fire in the air {fire})", called && fire > 0);
            yield return t.Shot("z04-the-herd-answers", 0.0f);
            foreach (var pr in Object.FindObjectsByType<Projectile>(FindObjectsSortMode.None)) Object.Destroy(pr.gameObject);
            p.health.Heal(99);
            // a blade from the front turns on him
            yield return Stand("herd", 208, 196, Facing.Up);
            int bronze = herd.health.hp;
            herd.Hit(new HitInfo { damage = 1, from = (Vector3)(herd.pos + (herd.facing == Facing.Down ? Vector2.down : herd.facing == Facing.Up ? Vector2.up : herd.facing == Facing.Left ? Vector2.left : Vector2.right)), knockback = 0, kind = HitKind.Slash, source = p.gameObject });
            Check($"a blade from the front turns on him ({bronze} -> {herd.health.hp})", herd.health.hp == bronze || herd.Open);
            KillAll();
            yield return Scene(1.0f);
            Check($"he can be put down ({Story.Has("dead_z2_herdsman")}), and the cage lifts", Story.Has("dead_z2_herdsman") && cage.solid == null);
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            var chest = Map.Current.Find("z2_shield");
            p.pos = chest.basePos + new Vector2(0, -0.55f); p.Face(Facing.Up);
            yield return new WaitForSeconds(0.2f);
            Check($"at the great chest the action button says {p.Action}", p.Action == Player.Act.Open);
            yield return Press(Controls.Interact, 4.2f);
            yield return t.Shot("z05-mirror-shield", 0.0f);
            yield return Scene();
            Check($"the Mirror Shield is his ({p.hasShield})", Story.Has("item_shield") && p.hasShield);
            // ------------------------------------------------ the feed store, the gate, the stair
            yield return Stand("landing", 390, 130, Facing.Right);
            yield return Walk(Vector2.right, 0.8f);
            Check($"east is the feed way ({Rooms.I.current.id})", Rooms.I.current.id == "feed");
            KillAll();
            yield return Stand("feed", 390, 128, Facing.Right);
            yield return Walk(Vector2.right, 0.8f);
            Check($"and at the end of it the feed store ({Rooms.I.current.id})", Rooms.I.current.id == "store");
            KillAll();
            yield return new WaitForSeconds(0.5f);
            var gateBars = Map.Current.Find("z2_gate");
            Check("the Herdsman's fall has lifted the bars of the gate", gateBars && gateBars.solid == null);
            yield return Stand("store", 208, 62, Facing.Up);
            yield return Walk(Vector2.up, 1.2f, 0.5f);
            Check($"north is the bull's gate ({Rooms.I.current.id})", Rooms.I.current.id == "gate");
            yield return Scene();
            var gate = Rooms.I.Find("gate");
            yield return Walk(Vector2.up, 1.2f, 0.2f);
            Check($"the bull is in the way ({(gate.rect.yMax - p.pos.y) * 16:0} px down the room)", (gate.rect.yMax - p.pos.y) * 16 > 150);
            yield return Stand("gate", 208, 196, Facing.Up);
            yield return t.Shot("z06-the-question", 1.6f);
            yield return Guard(() => Story.Has("z2_bull"), 9f);
            Check($"its own fire, handed back, breaks it ({Story.Has("z2_bull")}, life {p.health.hp}/{p.health.max})", Story.Has("z2_bull"));
            KillAll();                                    // (the thurifer on his round north of the head has a test of his own)
            Controls.Fake = Vector2.up;
            float ww = 0;
            while (Game.I.CurrentMap == "zig_2" && ww < 4f) { ww += Time.deltaTime; yield return null; }
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(0.8f);
            Check($"and the stair behind it goes up to {Game.I.CurrentMap} ({Rooms.I?.current?.id})", Game.I.CurrentMap == "zig_hi" && Rooms.I && Rooms.I.current.id == "landing");
            // ...and on another visit the gap where the head was is still a gap (it used to leave its block of wall behind)
            Game.I.EnterMap("zig_2", "south");
            Fade.Set(0);
            yield return Scene();
            KillAll();
            yield return Stand("gate", 208, 196, Facing.Up);
            KillAll();
            Controls.Fake = Vector2.up;
            ww = 0;
            while (Game.I.CurrentMap == "zig_2" && ww < 4f) { ww += Time.deltaTime; yield return null; }
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(0.8f);
            Check($"come back later, and he walks through where the head was, up to {Game.I.CurrentMap}", Game.I.CurrentMap == "zig_hi");
            // ------------------------------------------------ the high halls
            Fade.Set(0);
            yield return Scene();
            Check($"the third floor has rooms ({Rooms.I.all.Count})", Rooms.I.all.Count == 8);
            var last = Map.Current.Find("zh_bars");
            Check("the last hall is barred", last && last.solid != null);
            yield return t.Shot("z07-high-landing", 0.2f);
            KillAll();
            yield return Stand("landing", 30, 130, Facing.Left);
            yield return Walk(Vector2.left, 0.8f);
            Check($"west is the lamp way ({Rooms.I.current.id})", Rooms.I.current.id == "lamp");
            KillAll();
            yield return Stand("lamp", 30, 128, Facing.Left);
            yield return Walk(Vector2.left, 0.8f);
            Check($"and beyond it the west light ({Rooms.I.current.id})", Rooms.I.current.id == "west");
            KillAll();
            yield return new WaitForSeconds(0.5f);
            yield return Stand("west", 120, 152, Facing.Up);
            yield return Guard(() => Story.Has("on_zh_d1"), 3f);
            Check($"the shield hands the first disc the moon ({Story.Has("on_zh_d1")})", Story.Has("on_zh_d1"));
            yield return t.Shot("z08-first-disc", 0.2f);
            yield return Stand("west", 208, 62, Facing.Up);
            yield return Walk(Vector2.up, 1.2f);
            Check($"north is the moon room ({Rooms.I.current.id})", Rooms.I.current.id == "moon");
            KillAll();
            var moon = Rooms.I.Find("moon");
            // the pool is across a drop: a dreamer's road crosses it
            yield return Stand("moon", 190, 128, Facing.Left);
            yield return t.Shot("z09-moon-room", 0.2f);
            yield return Press(Controls.Nod, 0.1f);
            ww = 0;
            while (!Dream.I.Dreaming && ww < 4f) { ww += Time.deltaTime; yield return null; }
            // (well clear of the edge: a man who wakes with a heel still over the drop goes down it)
            yield return Walk(Vector2.left, 1.5f, 0.1f);
            Check($"asleep he crosses it ({(p.pos.x - moon.rect.xMin) * 16:0} px from the west wall, dreaming {Dream.I.Dreaming})", (p.pos.x - moon.rect.xMin) * 16 < 96);
            ww = 0;
            while (Dream.I.Dreaming && ww < 20f) { ww += Time.deltaTime; yield return null; }
            yield return new WaitForSeconds(0.4f);
            Check($"and wakes on the far side ({(p.pos.x - moon.rect.xMin) * 16:0} px, life {p.health.hp}/{p.health.max})", (p.pos.x - moon.rect.xMin) * 16 < 96 && Rooms.I.current.id == "moon");
            p.pos = InRoom("moon", 56, 152); p.Face(Facing.Up);
            yield return new WaitForSeconds(0.2f);
            yield return Guard(() => Story.Has("on_zh_d2"), 3f);
            Check($"the second disc lights ({Story.Has("on_zh_d2")})", Story.Has("on_zh_d2"));
            yield return Scene();
            // ------------------------------------------------ three mouths
            yield return Stand("landing", 390, 130, Facing.Right);
            yield return Scene(1.2f);
            last = Map.Current.Find("zh_bars");
            Check("both discs lit: the bars of the last hall are up", last && last.solid == null);
            yield return Walk(Vector2.right, 0.8f);
            Check($"east are the three mouths ({Rooms.I.current.id})", Rooms.I.current.id == "mouths");
            yield return Scene();
            var keyBars = Map.Current.Find("zh_keybars");
            Check("the key room is barred", keyBars && keyBars.solid != null);
            yield return t.Shot("z10-three-mouths", 0.2f);
            foreach (var (id, x, y) in new[] { ("zh_h1", 104f, 140f), ("zh_h2", 208f, 160f), ("zh_h3", 312f, 140f) })
            {
                yield return Stand("mouths", x, y, Facing.Up);
                yield return Guard(() => Story.Has(id), 10f);
                Check($"{id} answered ({Story.Has(id)}, life {p.health.hp}/{p.health.max})", Story.Has(id));
                p.health.Heal(99);
            }
            yield return Scene();
            Check("three broken: the key room's bars are up", keyBars.solid == null);
            yield return Stand("mouths", 208, 64, Facing.Up);
            yield return Walk(Vector2.up, 1.2f);
            Check($"north is the key room ({Rooms.I.current.id})", Rooms.I.current.id == "key");
            yield return Open("z2_bigkey");
            Check($"the Bull Key ({Story.Has("bigkey")})", Story.Has("bigkey"));
            // ------------------------------------------------ the great door
            yield return Stand("landing", 208, 62, Facing.Up);
            yield return Walk(Vector2.up, 1.3f);
            Check($"north of the landing is the last stair ({Rooms.I.current.id})", Rooms.I.current.id == "last");
            yield return Stand("last", 208, 62, Facing.Up);
            yield return Walk(Vector2.up, 1.3f);
            Check($"and at the top of it the great door's hall ({Rooms.I.current.id})", Rooms.I.current.id == "door");
            KillAll();
            yield return new WaitForSeconds(0.5f);
            var great = Map.Current.Find("z2_bigdoor");
            Check("the great door stands shut at the foot of the last stair", great && great.solid != null);
            yield return t.Shot("z11-great-door", 0.2f);
            p.pos = great.basePos + new Vector2(0, -0.85f); p.Face(Facing.Up);
            yield return new WaitForSeconds(0.2f);
            yield return Press(Controls.Interact, 0.6f);
            yield return Scene();
            Check($"the Bull Key opens it ({Story.Has("door_z2_bigdoor")})", Story.Has("door_z2_bigdoor"));
            Controls.Fake = Vector2.up;
            ww = 0;
            while (Game.I.CurrentMap == "zig_hi" && ww < 4f) { ww += Time.deltaTime; yield return null; }
            Controls.Fake = Vector2.zero;
            Story.Abort();
            yield return new WaitForSeconds(0.5f);
            Check($"and the last stair goes up to the summit ({Game.I.CurrentMap})", Game.I.CurrentMap == "zig_3");
            // and back down
            Game.I.EnterMap("zig_3", "south");
            Fade.Set(0);
            Story.Abort();
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.3f);
            Controls.Fake = Vector2.down;
            ww = 0;
            while (Game.I.CurrentMap == "zig_3" && ww < 3f) { ww += Time.deltaTime; yield return null; }
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(0.8f);
            Check($"from the summit the stair comes down to the high halls ({Game.I.CurrentMap}, {Rooms.I?.current?.id})", Game.I.CurrentMap == "zig_hi" && Rooms.I && Rooms.I.current.id == "door");
            // the plan of the place knows all three floors
            Pause.TestDo = "open";
            yield return new WaitForSecondsRealtime(0.3f);
            Pause.TestDo = "page " + Pause.MapPage;
            yield return new WaitForSecondsRealtime(0.2f);
            yield return t.Shot("z12-plan", 0.2f);
            Pause.TestDo = "close";
            yield return new WaitForSecondsRealtime(0.3f);
            // a journey from before the Herdsman: it already carries the shield, so nobody is keeping it
            Save.ClearAll(); Save.Use(0);
            Story.ResetAll();
            foreach (var f in new[] { "prequel", "prequel_done", "item_sword", "item_wakefire", "item_shield", "chest_z2_shield" }) Story.Set(f);
            Save.Write("zig_2", "south");
            Game.I.Begin(true);
            Fade.Set(0);
            yield return new WaitForSeconds(0.6f);
            Check($"an older journey with the shield finds his hall empty ({Story.Has("dead_z2_herdsman")}, in {Game.I.CurrentMap})", Story.Has("dead_z2_herdsman") && Game.I.CurrentMap == "zig_2");
            Save.Clear();
            t.Note(bad == 0 ? "ZIG OK" : $"ZIG: {bad} FAILED");
        }
    }
}
