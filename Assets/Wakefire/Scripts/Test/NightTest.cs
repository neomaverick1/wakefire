// The first night, played through: -wfScene night starts a new journey and takes Azar from his
// post to the crypt under the shrine and back, the way a player has to. He starts with nothing;
// the stone has to be pushed, the roots cut, the key found, the door unlocked, the plate weighted,
// the first bed of the First Watch put down, and the only way out of its room is to go to sleep.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class NightTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["night"] = Run;

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

        /// <summary>Let whatever scene is playing run out (the boxes turn their own pages here).</summary>
        static IEnumerator Scene(float atLeast = 0.4f, float atMost = 60f)
        {
            float w = 0;
            while ((w < atLeast || (Story.I && Story.I.Running) || Game.Busy) && w < atMost) { w += Time.deltaTime; yield return null; }
        }

        static IEnumerator Pack(AutoTest t, string shot, int page)
        {
            Pause.TestDo = "open";
            yield return new WaitForSecondsRealtime(0.3f);
            Pause.TestDo = "page " + page;
            yield return new WaitForSecondsRealtime(0.2f);
            yield return t.Shot(shot, 0.2f);
            Pause.TestDo = "close";
            yield return new WaitForSecondsRealtime(0.3f);
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
                if (e && !e.health.Dead) e.Hit(new HitInfo { damage = 99, from = p.pos, knockback = 0, kind = HitKind.Heavy, source = p.gameObject });
        }

        static int Count<T>() where T : Enemy
        {
            int n = 0;
            foreach (var e in Enemy.All) if (e is T && !e.health.Dead) n++;
            return n;
        }

        /// <summary>Lean on a block until it has gone as far as `until` says.</summary>
        static IEnumerator Push(Prop block, Vector2 from, Vector2 dir, System.Func<bool> until)
        {
            var p = Player.I;
            p.pos = from;
            p.Face(dir.x < 0 ? Facing.Left : dir.x > 0 ? Facing.Right : dir.y > 0 ? Facing.Up : Facing.Down);
            Controls.Fake = dir;
            for (float w = 0; w < 6f && !until(); w += Time.deltaTime) yield return null;
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(0.45f);
        }

        static IEnumerator Run(AutoTest t)
        {
            int bad = 0;
            void Check(string what, bool ok) { t.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
            Save.ClearAll(); Save.Use(0);
            DialogueBox.AutoAdvance = 0.12f;
            Game.I.Begin(false);
            var p = Player.I;
            yield return t.Shot("n00-card", 1.6f);
            float w = 0;
            while (Story.I.Running && w < 90f) { w += Time.deltaTime; if (w > 24.2f && w < 24.25f) yield return t.Shot("n01-waking", 0); yield return null; }
            Check($"the prologue plays and lets go of him ({w:0.0}s, {p.state})", !Story.I.Running && w < 89f && p.state == Player.State.Free);
            Check($"it is the first night in {Game.I.CurrentMap}: no blade ({p.hasSword}), no flame ({p.hasLantern}), no dreaming ({Dream.I.Locked})",
                Story.FirstNight && Game.I.CurrentMap == "ashkel" && !p.hasSword && !p.hasLantern && Dream.I.Locked);
            yield return t.Shot("n02-post", 0.4f);
            // nothing to swing, and he does not dare shut his eyes
            yield return Press(Controls.Attack, 0.25f);
            Check($"the blade button does nothing ({p.state})", p.state == Player.State.Free);
            yield return Press(Controls.Nod, 0.3f);
            Check($"nodding off is refused, with a word about why ({Story.I.Running}, dreaming {Dream.I.Dreaming})", Story.I.Running && !Dream.I.Dreaming);
            yield return Scene();
            // nobody wakes
            Npc dur = null;
            foreach (var n in Object.FindObjectsByType<Npc>(FindObjectsSortMode.None)) if (n.id == "dur") dur = n;
            Check("Captain Dur is at the gate", dur);
            if (dur)
            {
                p.pos = (Vector2)dur.transform.position + new Vector2(0, -0.9f);
                p.Face(Facing.Up);
                yield return new WaitForSeconds(0.2f);
                yield return Press(Controls.Interact, 0.5f);
                yield return t.Shot("n03-dur", 0.0f);
                yield return Scene();
            }
            // the terraces: what hunts there is asleep with everything else, and the door is behind the altar
            Game.I.EnterMap("terraces", "east");
            Fade.Set(0);
            yield return new WaitForSeconds(0.5f);
            Check($"nothing hunts on the terraces tonight ({Enemy.All.Count})", Enemy.All.Count == 0);
            p.pos = Map.ToWorld(420, 50);
            PixelView.I.SnapTo(p.pos);
            yield return t.Shot("n04-shrine", 0.4f);
            yield return Walk(Vector2.up, 0.8f, 1.2f);
            Check($"through the door behind the altar: {Game.I.CurrentMap}", Game.I.CurrentMap == "crypt");
            Check("and the crypt has something to say about its lamps", Story.I.Running);
            yield return Scene();
            Check($"the crypt has rooms ({(Rooms.I ? Rooms.I.all.Count : 0)}), he is on the stair ({Rooms.I?.current?.id}), and it is dim (light {PixelView.I.ambient.r:0.00})",
                Rooms.I && Rooms.I.all.Count == 8 && Rooms.I.current.id == "stair" && PixelView.I.ambient.r < 0.5f);
            Check($"its music is its own ({Map.Current.data.music})", Map.Current.data.music == "crypt" && Resources.Load<AudioClip>("Music/crypt") && Resources.Load<AudioClip>("Music/crypt_dream"));
            yield return t.Shot("n05-stair", 0.3f);
            yield return Pack(t, "n05a-pack-empty", Pause.ItemPage);
            yield return Pack(t, "n05b-plan-no-scroll", Pause.MapPage);
            Check($"the pack closes again and the game goes on ({Game.Paused})", !Game.Paused);
            // the watch roll
            p.pos = InRoom("stair", 350, 78); p.Face(Facing.Up);          // (it stands on the terrace now, up the steps)
            yield return new WaitForSeconds(0.2f);
            Check($"at a chest the action button says {p.Action}", p.Action == Player.Act.Open);
            yield return Press(Controls.Interact);
            yield return Scene();
            Check("the watch roll is in the first chest", Story.Has("item_map_crypt"));
            yield return Pack(t, "n05c-plan-scroll", Pause.MapPage);
            // the locked door, with no key
            p.pos = InRoom("stair", 208, 60); p.Face(Facing.Up);
            yield return Walk(Vector2.up, 0.5f);
            Check($"the door north is locked ({Rooms.I.current.id})", Rooms.I.current.id == "stair");
            yield return Scene();
            // east: the roots, and what is behind them
            p.pos = InRoom("stair", 390, 130);
            yield return Walk(Vector2.right, 0.8f);
            yield return Scene();
            Check($"east is the dormitory ({Rooms.I.current.id}), with {Count<Reach>()} arms under its beds and its floor", Rooms.I.current.id == "beds" && Count<Reach>() == 7);
            var roots = Map.Current.Find("crypt_roots");
            Check("roots are grown across the way", roots && roots.solid != null);
            var beds = Rooms.I.Find("beds");
            p.pos = InRoom("beds", 264, 132);
            yield return Walk(Vector2.down, 1.2f, 0.2f);
            Check($"he cannot get through them ({(beds.rect.yMax - p.pos.y) * 16:0} px down the room), and nothing has hold of him ({p.state}, {p.health.hp}/{p.health.max})",
                (beds.rect.yMax - p.pos.y) * 16 < 152 && p.health.hp == p.health.max && p.state != Player.State.Held);
            yield return t.Shot("n06-roots", 0.2f);
            // (a bed with an arm under it is two strides off: for a man with no blade it only drums its fingers)
            p.pos = InRoom("beds", 270, 124); p.Face(Facing.Up);
            yield return new WaitForSeconds(1.6f);
            int peeking = 0;
            foreach (var e in Enemy.All) if (e is Reach r && r.shown > 0.5f && r.s == Reach.S.Under) peeking++;
            yield return Scene();
            Check($"with no blade on him, what is under the beds only drums its fingers at him ({peeking} showing, {p.state}, {p.health.hp}/{p.health.max})",
                peeking >= 1 && p.health.hp == p.health.max && p.state != Player.State.Held && Story.Count("reach_peeks") > 0);
            yield return t.Shot("n06a-drumming", 0.1f);
            p.pos = InRoom("beds", 264, 132);
            yield return Walk(Vector2.down, 1.2f, 0.2f);
            p.Face(Facing.Down);
            yield return new WaitForSeconds(0.2f);
            Check($"facing the roots the action button says {p.Action}", p.Action == Player.Act.Look);
            yield return Press(Controls.Interact);
            Check("and looking at them says what he lacks", Story.I.Running);
            yield return Scene();
            // west: the armoury
            p.pos = InRoom("beds", 30, 130);
            yield return Walk(Vector2.left, 0.8f);
            yield return Scene();
            p.pos = InRoom("stair", 30, 130);
            yield return Walk(Vector2.left, 0.8f);
            Check($"west is the watch walk ({Rooms.I.current.id})", Rooms.I.current.id == "walk");
            p.pos = InRoom("walk", 30, 130);
            yield return Walk(Vector2.left, 0.8f);
            Check($"and at the end of it the armoury ({Rooms.I.current.id})", Rooms.I.current.id == "arms");
            var block = Map.Current.Find("crypt_block");
            var chest = Map.Current.Find("crypt_sword");
            Check("a stone stands in the gap, and the great chest behind it", block && chest);
            float by = block.basePos.y;
            p.pos = InRoom("arms", 128, 150); p.Face(Facing.Up);
            yield return Walk(Vector2.up, 0.12f, 0.1f);
            yield return t.Shot("n07-armoury", 0.1f);
            yield return Push(block, InRoom("arms", 128, 126), Vector2.up, () => block.basePos.y > by + 1.9f);
            Check($"leaning on the stone moves it ({block.basePos.y - by:0.0} tiles)", block.basePos.y > by + 1.9f);
            // through the gap behind it, and round the stone to the chest
            yield return Walk(Vector2.up, 0.5f, 0.1f);
            yield return Walk(Vector2.left, 0.6f, 0.2f);
            var arms = Rooms.I.Find("arms");
            Check($"and he can walk in past it ({(arms.rect.yMax - p.pos.y) * 16:0} px below the room's top, {(p.pos.x - arms.rect.xMin) * 16:0} from its west wall)",
                (arms.rect.yMax - p.pos.y) * 16 < 94 && (p.pos.x - arms.rect.xMin) * 16 < 118);
            p.pos = chest.basePos + new Vector2(0, -0.6f); p.Face(Facing.Up);
            yield return new WaitForSeconds(0.2f);
            Check($"at the great chest the action button says {p.Action}", p.Action == Player.Act.Open);
            yield return Press(Controls.Interact, 1.3f);
            yield return t.Shot("n08-great-chest", 0.0f);
            yield return new WaitForSeconds(2.6f);
            yield return t.Shot("n09-khopesh", 0.0f);
            yield return Scene();
            Check($"the khopesh is his ({p.hasSword}), and the chest stays open", Story.Has("item_sword") && p.hasSword && Story.Has("chest_crypt_sword"));
            yield return Press(Controls.Attack, 0.12f);
            Check($"and now the blade button swings it ({p.state})", p.state == Player.State.Attack);
            yield return new WaitForSeconds(0.7f);
            // back east and through the roots
            p.pos = InRoom("arms", 390, 130);
            yield return Walk(Vector2.right, 0.8f);
            p.pos = InRoom("stair", 390, 130);
            yield return Walk(Vector2.right, 0.8f);
            roots = Map.Current.Find("crypt_roots");
            p.pos = InRoom("beds", 264, 146); p.Face(Facing.Down);
            yield return new WaitForSeconds(0.15f);
            yield return Press(Controls.Attack, 0.6f);
            Check($"one cut and the roots are gone for good ({Story.Has("cut_crypt_roots")})", !roots && Story.Has("cut_crypt_roots"));
            yield return t.Shot("n10-cut", 0.0f);
            // (what is under the beds has its own test: here it is only in the way)
            foreach (var e in Enemy.All.ToArray()) if (e is Reach) Object.Destroy(e.gameObject);
            yield return new WaitForSeconds(0.3f);
            // (now that he has a blade they have come out for him, and the game has had something to say about that)
            yield return Scene();
            var keyChest = Map.Current.Find("crypt_key");
            p.pos = keyChest.basePos + new Vector2(0, -0.6f); p.Face(Facing.Up);
            yield return new WaitForSeconds(0.2f);
            yield return Press(Controls.Interact);
            yield return Scene();
            Check($"the chest in the store has the key ({p.keys})", p.keys == 1);
            // the locked door, the hall of lamps
            p.pos = InRoom("beds", 30, 130);
            yield return Walk(Vector2.left, 0.8f);
            p.pos = InRoom("stair", 208, 60); p.Face(Facing.Up);
            yield return new WaitForSeconds(0.2f);
            yield return Press(Controls.Interact, 0.5f);
            Check($"the key opens the door ({Story.Has("door_crypt_door")}, keys {p.keys})", Story.Has("door_crypt_door") && p.keys == 0);
            yield return Walk(Vector2.up, 1.3f);
            int mothsSeen = 0;
            foreach (var e in Enemy.All) if (e is Moth && e.Present) mothsSeen++;
            Check($"north is the hall of lamps ({Rooms.I.current.id}): nothing comes up through a lit floor ({Count<Reach>()}), and its moths are a dreamer's business ({mothsSeen} awake)",
                Rooms.I.current.id == "lamps" && Count<Reach>() == 0 && mothsSeen == 0);
            yield return t.Shot("n11-lamps", 0.2f);
            KillAll();
            yield return new WaitForSeconds(0.6f);
            var grille = Map.Current.Find("crypt_den");
            Check("the way west is barred", grille && grille.solid != null);
            var b2 = Map.Current.Find("crypt_block2");
            var plate = Map.Current.Find("crypt_plate");
            Check("there is a stone and a plate", b2 && plate);
            yield return Push(b2, b2.basePos + new Vector2(1.1f, 0.2f), Vector2.left, () => b2.basePos.x <= plate.basePos.x + 0.05f);
            yield return Push(b2, b2.basePos + new Vector2(0, -0.75f), Vector2.up, () => b2.basePos.y >= plate.basePos.y - 0.05f);
            yield return new WaitForSeconds(0.5f);
            Check($"the stone on the plate ({(b2.basePos - plate.basePos).magnitude:0.00} off) lifts the bars ({Story.Has("on_crypt_plate")})",
                Story.Has("on_crypt_plate") && grille.solid == null);
            yield return Scene();
            yield return t.Shot("n12-plate", 0.2f);
            // the den
            var cage = Map.Current.Find("crypt_cage");
            Check("the Wakefire's cage is shut", cage && cage.solid != null);
            p.pos = InRoom("lamps", 30, 130);
            yield return Walk(Vector2.left, 0.8f, 0.6f);
            Check($"west is the crawl ({Rooms.I.current.id}), with {Count<Reach>()} arms up through its floor", Rooms.I.current.id == "run" && Count<Reach>() == 2);
            foreach (var e in Enemy.All.ToArray()) if (e is Reach) Object.Destroy(e.gameObject);
            p.health.hp = p.health.max;
            p.pos = InRoom("run", 30, 128);
            yield return Walk(Vector2.left, 0.8f, 0.6f);
            Check($"and at the end of it the last room ({Rooms.I.current.id}), and the first bed is in it ({Count<Underbed>()})", Rooms.I.current.id == "den" && Count<Underbed>() == 1);
            yield return Scene();
            yield return t.Shot("n13-den", 0.5f);
            var shut = Map.Current.Find("crypt_shut");
            Check("the bars have dropped behind him", shut && shut.solid != null);
            yield return new WaitForSeconds(1.2f);
            yield return t.Shot("n14-the-first-bed", 0.0f);
            // (the fight has its own test: here the last cut is enough)
            foreach (var e in Enemy.All.ToArray()) if (e is Underbed bed) { bed.health.hp = 1; bed.Cut(null); }
            yield return Scene(1.0f);
            Check($"it can be put down ({Story.Has("dead_crypt_mother")}), and the cage lifts", Story.Has("dead_crypt_mother") && cage.solid == null);
            Check("the bars behind him stay down", shut.solid != null);
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            var fire = Map.Current.Find("crypt_fire");
            p.pos = fire.basePos + new Vector2(0, -0.55f); p.Face(Facing.Up);
            yield return new WaitForSeconds(0.2f);
            Check($"at the Wakefire's chest the action button says {p.Action}", p.Action == Player.Act.Open);
            yield return Press(Controls.Interact, 4.2f);
            yield return t.Shot("n15-wakefire", 0.0f);
            yield return Scene();
            Check($"the Wakefire is his ({p.hasLantern}), on the item button ({Items.Chosen}), and he may dream ({!Dream.I.Locked})",
                Story.Has("item_wakefire") && p.hasLantern && Items.Chosen == "wakefire" && !Dream.I.Locked);
            yield return Pack(t, "n15a-pack-full", Pause.ItemPage);
            yield return Pack(t, "n15b-plan-den", Pause.MapPage);
            // the way out: bricks when awake
            var den = Rooms.I.Find("den");
            p.pos = InRoom("den", 208, 150); p.Face(Facing.Down);
            yield return Walk(Vector2.down, 1.0f, 0.2f);
            Check($"awake, the back door is bricks ({(den.rect.yMax - p.pos.y) * 16:0} px down, still in {Rooms.I.current.id})", Rooms.I.current.id == "den" && (den.rect.yMax - p.pos.y) * 16 < 176);
            yield return t.Shot("n16-bricks", 0.1f);
            // nod off, stand where the bricks are, and be woken there: he comes to beside them, not in them
            p.pos = InRoom("den", 208, 150);
            yield return Press(Controls.Nod, 0.1f);
            w = 0;
            while (!Dream.I.Dreaming && w < 4f) { w += Time.deltaTime; yield return null; }
            yield return new WaitForSeconds(0.6f);
            p.pos = InRoom("den", 208, 176);
            Dream.I.SetInstant(false);
            yield return new WaitForSeconds(0.3f);
            var at0 = p.pos;
            yield return Walk(Vector2.up, 0.3f, 0.1f);
            bool freeA = (p.pos - at0).magnitude > 0.5f;
            p.pos = at0;
            yield return Walk(Vector2.down, 0.3f, 0.1f);
            bool freeB = (p.pos - at0).magnitude > 0.5f;
            Check($"woken in the middle of the bricks he is put beside them and can walk ({freeA || freeB})", freeA || freeB);
            w = 0;
            while (Dream.I.Drowsiness < 0.9f && w < 30f) { w += Time.deltaTime; yield return null; }
            p.pos = InRoom("den", 208, 150);
            yield return Press(Controls.Nod, 0.1f);
            w = 0;
            while (!Dream.I.Dreaming && w < 4f) { w += Time.deltaTime; yield return null; }
            Check($"he nods off ({w:0.0}s)", Dream.I.Dreaming);
            yield return t.Shot("n17-asleep", 0.3f);
            yield return Walk(Vector2.down, 1.6f, 1.0f);
            Check($"asleep, he walks out through where the bricks were: {Rooms.I.current.id}", Rooms.I.current.id == "arms");
            yield return t.Shot("n18-out", 0.1f);
            w = 0;
            while (Dream.I.Dreaming && w < 20f) { w += Time.deltaTime; yield return null; }
            Check($"and the flame wakes him again ({w:0.0}s later)", !Dream.I.Dreaming);
            yield return Scene();
            // up the stair and out: forty nights go by
            p.pos = InRoom("arms", 390, 130);
            yield return Walk(Vector2.right, 0.8f);
            p.pos = InRoom("stair", 208, 196);
            Controls.Fake = Vector2.down;
            w = 0;
            while (Game.I.CurrentMap == "crypt" && w < 3f) { w += Time.deltaTime; yield return null; }
            Controls.Fake = Vector2.zero;
            Check($"the stair goes back up to the {Game.I.CurrentMap}", Game.I.CurrentMap == "terraces");
            yield return t.Shot("n19-forty-nights", 6.0f);
            w = 0;
            while ((Story.I.Running || Story.FirstNight) && w < 90f) { w += Time.deltaTime; yield return null; }
            yield return new WaitForSeconds(0.5f);
            Check($"forty nights later ({w:0.0}s) he is at his post in {Game.I.CurrentMap}, and chapter one can begin ({!Story.FirstNight})",
                Game.I.CurrentMap == "ashkel" && Story.Has("prequel_done") && !Story.FirstNight && p.state == Player.State.Free);
            yield return t.Shot("n20-chapter-one", 0.3f);
            var d = Save.Read();
            Check($"the journey is saved there ({d?.map}) and is called '{(d != null ? Save.Chapter(d) : "?")}'", d != null && d.map == "ashkel" && System.Array.IndexOf(d.flags, "item_wakefire") >= 0);
            // chapter one's world is as it was: things hunt again
            Game.I.EnterMap("terraces", "east");
            Fade.Set(0);
            yield return new WaitForSeconds(0.5f);
            Check($"and the Wicks are out on the terraces ({Enemy.All.Count})", Enemy.All.Count >= 5);
            // the crypt can be walked again, and nothing in it shuts
            Game.I.EnterMap("crypt", "south");
            Fade.Set(0);
            yield return new WaitForSeconds(0.5f);
            shut = Map.Current.Find("crypt_shut");
            Check("afterwards the den's bars stand open", shut && shut.solid == null);
            Check("and the roots stay cut", !Map.Current.Find("crypt_roots"));
            t.Note(bad == 0 ? "NIGHT OK" : $"NIGHT: {bad} FAILED");
        }
    }
}
