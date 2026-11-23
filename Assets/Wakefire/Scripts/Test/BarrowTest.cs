// The Generals' Barrow, played through: -wfScene barrow takes Azar in at the mound on the hill,
// through both camps and their standards, onto the Board, into Nod's Pocket, and through each of
// the things the Pocket has carried so far (a key, a plank of moonlight, a blue flame, a snore,
// the last word of an argument). -wfScene piece is the Last Piece against somebody who has read
// rule the fourth: four rounds, standing on rosettes.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class BarrowTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register()
        {
            AutoTest.Scenes["barrow"] = Run;
            AutoTest.Scenes["piece"] = Piece;
        }

        static Vector2 InRoom(string id, float x, float y)
        {
            var r = Rooms.I.Find(id);
            return new Vector2(r.rect.xMin + x / 16f, r.rect.yMax - y / 16f);
        }

        static IEnumerator Walk(Vector2 dir, float seconds, float settle = 0.7f)
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

        static IEnumerator Sleep(bool on)
        {
            var p = Player.I;
            if (on) { Dream.I.Drowsiness = 1; Dream.I.Seconds = 9999; Dream.I.Flip(p.pos, true); yield return new WaitForSeconds(1.2f); }
            else { Dream.I.Flip(p.pos, false); yield return new WaitForSeconds(1.2f); Dream.I.SetInstant(false); Story.I.ApplyItems(); Dream.I.Drowsiness = 1; }
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

        static bool Shut(string id)
        {
            foreach (var pr in Map.Current.props) if (pr && pr.data.id == id && pr.Kind == "bars") return pr.sr.enabled;
            return false;
        }

        static IEnumerator Open(string id, float below = 0.7f)
        {
            var p = Player.I;
            var pr = Map.Current.Find(id);
            if (!pr) yield break;
            p.pos = pr.basePos + new Vector2(0, -below); p.Face(Facing.Up);
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.2f);
            yield return Press(Controls.Interact);
            yield return Scene();
        }

        static void Kit()
        {
            Save.ClearAll(); Save.Use(0);
            Game.I.Begin(false);
            Story.Abort();
            Story.GiveKit();
            // as he comes up the hill in chapter two: the shield, and the gate behind him
            foreach (var f in new[] { "item_shield", "ch2", "chapter_done", "item_hillkey", "hill_gate", "met_namtar", "queue_passed" }) Story.Set(f);
            Story.I.ApplyItems();
        }

        static IEnumerator Run(AutoTest t)
        {
            int bad = 0;
            void Check(string what, bool ok) { t.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
            DialogueBox.AutoAdvance = 0.1f;
            Kit();
            var p = Player.I;
            // ------------------------------------------------ the mound on the hill
            Game.I.EnterMap("necropolis", "barrow");
            Fade.Set(0);
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.5f);
            KillAll();
            yield return t.Shot("b00-the-mound", 0.3f);
            Controls.Fake = Vector2.up;
            for (float w = 0; w < 4f && Game.I.CurrentMap == "necropolis"; w += Time.deltaTime) yield return null;
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(0.9f);
            yield return Scene(0.3f);
            Check("the mound's door goes down into the barrow", Game.I.CurrentMap == "barrow" && Game.I.CurrentSpawn == "south");
            if (Game.I.CurrentMap != "barrow") { Game.I.EnterMap("barrow", "south"); Fade.Set(0); yield return new WaitForSeconds(0.5f); yield return Scene(0.3f); }
            KillAll();
            yield return t.Shot("b01-the-one-door", 0.3f);
            Check("the way north is barred while a standard flies", Shut("bw_board"));
            // a dream thing, before he has anywhere to put it
            var word = Map.Current.Find("bw_word");
            Check("the last word is lying in the hall", word);
            if (word)
            {
                p.pos = word.basePos + new Vector2(0, -0.6f); p.Face(Facing.Up);
                yield return new WaitForSeconds(0.2f);
                Check("awake, there is nothing there to take", p.Action != Player.Act.Take);
                yield return Sleep(true);
                p.pos = word.basePos + new Vector2(0, -0.6f); p.Face(Facing.Up); p.SetState(Player.State.Free, "idle");
                yield return new WaitForSeconds(0.2f);
                Check("in the dream the button says Take", p.Action == Player.Act.Take);
                yield return t.Shot("b02-a-dream-thing", 0.1f);
                yield return Press(Controls.Interact);
                yield return Scene();
                Check("with no pocket, his hand comes away empty", Pocket.Holding == null);
                yield return Sleep(false);
            }
            // ------------------------------------------------ the red camp
            yield return Stand("red", 60, 128, Facing.Right);
            yield return new WaitForSeconds(0.6f);
            Check("three of Ushur's spearmen hold the red camp", Count<Spearman>() == 3);
            Check("the camp's door has dropped behind him", Shut("bw_reddoor"));
            Check("the standard is caged while they stand", Shut("bw_redcage"));
            yield return t.Shot("b03-red-camp", 0.2f);
            // one of them, the honest way: he comes on, and the blade takes him from the side
            KillAll();
            yield return new WaitForSeconds(0.6f);
            yield return Scene(0.3f);
            Check("the camp is cleared", Story.Has(Mech.ClearFlag("barrow", "red")));
            Check("the cage and the door lift", !Shut("bw_redcage") && !Shut("bw_reddoor"));
            var std = Map.Current.Find("bw_red");
            if (std) { p.pos = std.basePos + new Vector2(0, -0.8f); p.Face(Facing.Up); p.SetState(Player.State.Free, "idle"); yield return new WaitForSeconds(0.2f); }
            Check("in front of the standard the button says Lower", p.Action == Player.Act.Lower);
            yield return Press(Controls.Interact);
            yield return Scene();
            Check("Ushur's standard is down", Story.Has("bw_red"));
            yield return t.Shot("b04-red-standard-down", 0.2f);
            // ------------------------------------------------ the blue camp
            yield return Stand("blue", 320, 160, Facing.Up);
            Check("three of Baltu's slingers hold the blue camp", Count<Slinger>() == 3);
            Check("the ditch is gated while they stand", Shut("bw_bluegate"));
            yield return t.Shot("b05-blue-camp", 0.6f);
            // a bullet off the mirror goes back to the man who slung it. One slinger at a time: the one straight
            // across the ditch from him (three at once, from three sides, is a test of his feet, not of the shield)
            Slinger across = null;
            foreach (var e in Enemy.All)
                if (e is Slinger s && !s.health.Dead && (across == null || Mathf.Abs(s.pos.x - p.pos.x) < Mathf.Abs(across.pos.x - p.pos.x))) across = s;
            foreach (var e in Enemy.All.ToArray())
                if (e is Slinger s && s != across && !s.health.Dead) s.Hit(new HitInfo { damage = 99, from = p.pos, knockback = 0, kind = HitKind.Reflected, source = p.gameObject });
            yield return new WaitForSeconds(0.4f);
            Check("one slinger left, straight across the ditch", across && Count<Slinger>() == 1);
            int turned = 0;
            Controls.FakeHold = Controls.Interact; Controls.FakePress = Controls.Interact;
            for (float held = 0; held < 22f && across && !across.health.Dead; held += Time.deltaTime)
            {
                // square to him whenever the shield is down
                if (p.state == Player.State.Free)
                {
                    p.pos = new Vector2(across.pos.x, InRoom("blue", 320, 160).y);
                    p.Face(Facing.Up);
                    Controls.FakePress = Controls.Interact;
                }
                foreach (var pr in Object.FindObjectsByType<Projectile>(FindObjectsSortMode.None)) if (pr.reflected) turned++;
                p.health.hp = p.health.max;
                yield return null;
            }
            Controls.FakeHold = null;
            yield return new WaitForSeconds(0.3f);
            Check($"a bullet off the shield breaks the slinger who threw it (turned for {turned} frames)", !across || across.health.Dead);
            yield return t.Shot("b06-returned", 0.1f);
            KillAll();
            yield return new WaitForSeconds(0.6f);
            yield return Scene(0.3f);
            Check("the gate across the ditch lifts", !Shut("bw_bluegate"));
            // over the causeway on his own feet
            yield return Stand("blue", 208, 150, Facing.Up);
            yield return Walk(Vector2.up, 1.1f);
            Check("he walks the causeway to the far side", p.pos.y > InRoom("blue", 208, 108).y);
            std = Map.Current.Find("bw_blue");
            if (std) { p.pos = std.basePos + new Vector2(0, -0.8f); p.Face(Facing.Up); p.SetState(Player.State.Free, "idle"); yield return new WaitForSeconds(0.2f); }
            yield return Press(Controls.Interact);
            yield return Scene();
            Check("Baltu's standard is down", Story.Has("bw_blue"));
            // ------------------------------------------------ the board
            yield return Stand("pass1", 208, 150, Facing.Up);
            yield return Scene(0.4f);
            yield return Stand("pass2", 208, 150, Facing.Up);
            yield return Scene(0.8f);
            Check("both standards down: the bars at the head of the passage lift", !Shut("bw_board"));
            // into the hall through its door, on his own feet
            yield return Stand("pass2", 208, 84, Facing.Up);
            Controls.Fake = Vector2.up;
            for (float w = 0; w < 4f && Rooms.I.current.id != "board"; w += Time.deltaTime) yield return null;
            Controls.Fake = Vector2.zero;
            for (float w = 0; w < 3f && (Rooms.Sliding || Game.Busy); w += Time.deltaTime) yield return null;
            yield return new WaitForSeconds(0.3f);
            var piece = LastPiece.Current;
            Check("through the door: he is in the hall, and not yet on the board", Rooms.I.current.id == "board" && Board.I && !Board.I.At(p.pos, out _, out _));
            Check("the Last Piece is on its rosette, waiting", piece && piece.Waiting);
            yield return t.Shot("b07-the-board", 0.3f);
            p.health.hp = p.health.max;
            yield return Walk(Vector2.up, 0.6f, 0.2f);
            yield return Scene(0.5f);
            Check("a foot on the board is a move", piece && !piece.Waiting);
            yield return new WaitForSeconds(0.5f);
            Check("the hall shuts behind him", Shut("bw_shut"));
            // rule the fourth
            bool stalled = false;
            int hpB = p.health.hp;
            var b = Board.I;
            for (float w = 0; w < 30f && piece && !stalled; w += Time.deltaTime)
            {
                // stand on a rosette that still counts (the corner ones, away from where it starts)
                Vector2 best = b.Center(0, 2); float bd = 999f;
                foreach (var q in new[] { new Vector2Int(0, 0), new Vector2Int(0, 2), new Vector2Int(6, 0), new Vector2Int(6, 2), new Vector2Int(3, 1) })
                {
                    if (b.Spent(q.x, q.y) || Vector2.Distance(b.Center(q.x, q.y), piece.pos) < b.cell * 1.2f) continue;
                    float d = Vector2.Distance(b.Center(q.x, q.y), p.pos);
                    if (d < bd) { bd = d; best = b.Center(q.x, q.y); }
                }
                if (p.state == Player.State.Free) p.pos = best;
                stalled = piece.Stalled;
                yield return null;
            }
            Check("on a rosette the move is illegal: the Piece rocks on its base", stalled);
            Check("and he is not taken", p.health.hp == hpB);
            yield return t.Shot("b08-rule-the-fourth", 0.3f);
            yield return Scene(0.3f);
            if (piece) piece.Hit(new HitInfo { damage = 99, from = p.pos, knockback = 0, kind = HitKind.Reflected, source = p.gameObject });
            yield return new WaitForSeconds(1.4f);
            yield return Scene(0.5f);
            Check("the Last Piece is down for good", Story.Has("dead_bw_piece"));
            yield return new WaitForSeconds(0.6f);
            Check("its cage lifts, and the doors east and west", !Shut("bw_cage") && !Shut("bw_west") && !Shut("bw_east") && !Shut("bw_shut"));
            p.health.hp = p.health.max;
            yield return Open("bw_pocket");
            Check("Nod's Pocket", Pocket.Have && Items.Current != null && Items.Current.id == "pocket");
            yield return t.Shot("b09-the-pocket", 0.2f);
            // ------------------------------------------------ Nod's post: a dream key for a waking lock
            var key = Map.Current.Find("bw_key");
            yield return Stand("nod", 196, 66, Facing.Up);
            yield return Press(Controls.Item, 0.5f);
            yield return Scene();
            Check("empty, the Pocket has nothing to hold out", Pocket.Holding == null);
            yield return Sleep(true);
            yield return Stand("nod", 196, 66, Facing.Up);
            Check("the key hangs on its hook in the dream", key && key.sr.enabled && p.Action == Player.Act.Take);
            yield return t.Shot("b10-the-dream-key", 0.1f);
            yield return Press(Controls.Interact);
            yield return Scene();
            Check("the key goes in the Pocket", Pocket.Holding != null && Pocket.Holding.id == "key" && key && !key.sr.enabled);
            Check("the item box shows it", Items.Current != null && Items.Current.Art == "pocket_key");
            yield return Press(Controls.Item, 0.5f);
            yield return Scene();
            Check("in the dream the item button does nothing with it", Pocket.Holding != null && Pocket.Holding.id == "key");
            // take a second thing: the first goes back
            var snore = Map.Current.Find("bw_snore");
            if (snore) { p.pos = snore.basePos + new Vector2(0, -0.5f); p.Face(Facing.Up); p.SetState(Player.State.Free, "idle"); yield return new WaitForSeconds(0.2f); }
            yield return Press(Controls.Interact);
            yield return Scene();
            Check("taking the snore puts the key back on its hook", Pocket.Holding != null && Pocket.Holding.id == "snore" && key && key.sr.enabled);
            yield return Stand("nod", 196, 66, Facing.Up);
            yield return Press(Controls.Interact);
            yield return Scene();
            Check("and the key comes off it again", Pocket.Holding != null && Pocket.Holding.id == "key");
            yield return Sleep(false);
            Check("awake, it is still in the Pocket", Pocket.Holding != null && Pocket.Holding.id == "key");
            int coins0 = p.coins;
            yield return Stand("nod", 354, 122, Facing.Up);
            yield return t.Shot("b11-the-strongroom", 0.1f);
            yield return Press(Controls.Item, 0.9f);
            yield return Scene();
            Check("the dream key opens the strongroom", Story.Has("door_bw_strong") && Pocket.Holding == null && Story.Has("spent_bw_key"));
            yield return Open("bw_pay");
            Check("Nod's back pay", p.coins == coins0 + 100);
            // ------------------------------------------------ a plank of moonlight
            yield return Stand("red", 340, 204, Facing.Up);
            yield return Sleep(true);
            yield return Stand("red", 340, 204, Facing.Up);
            yield return t.Shot("b12-planks", 0.1f);
            yield return Press(Controls.Interact);
            yield return Scene();
            Check("a plank of moonlight off the stack", Pocket.Holding != null && Pocket.Holding.id == "plank");
            yield return Sleep(false);
            Save.Write("barrow", "south");
            var sd = Save.Read();
            Check("a saved journey keeps what is in the Pocket", sd != null && System.Array.IndexOf(sd.flags, "pocket_plank") >= 0 && sd.item == "pocket");
            yield return Stand("truce", 84, 148, Facing.Down);
            yield return new WaitForSeconds(0.4f);
            Check("two of each army stand either side of the truce wall", Count<Spearman>() == 2 && Count<Slinger>() == 2);
            float yFar = InRoom("truce", 84, 192).y;
            int hpP = p.health.hp;
            yield return Walk(Vector2.down, 0.5f, 0.3f);
            Check("the drop stops him without a plank", p.pos.y > InRoom("truce", 84, 158).y);
            yield return Stand("truce", 84, 150, Facing.Down);
            yield return Press(Controls.Item, 0.9f);
            yield return Scene();
            Check("the plank is laid across the drop", Story.Has("on_bw_plank") && Pocket.Holding == null);
            yield return t.Shot("b13-the-plank", 0.2f);
            yield return Stand("truce", 84, 150, Facing.Down);
            yield return Walk(Vector2.down, 0.75f, 0.4f);
            Check("and holds him", p.pos.y < yFar && p.health.hp == hpP && p.state == Player.State.Free);
            // ------------------------------------------------ the blue flame
            yield return Stand("blue", 60, 198, Facing.Up);
            yield return Sleep(true);
            yield return Stand("blue", 60, 198, Facing.Up);
            yield return t.Shot("b14-the-blue-fire", 0.1f);
            yield return Press(Controls.Interact);
            yield return Scene();
            var fire = Map.Current.Find("bw_fire");
            Check("a tongue of the blue fire, and the fire still burning", Pocket.Holding != null && Pocket.Holding.id == "flame" && fire && fire.sr.enabled);
            yield return Sleep(false);
            yield return Stand("truce", 84, 196, Facing.Down);
            Check("the truce holds while the lamp is cold", Shut("bw_truce") && Count<Spearman>() == 2 && Count<Slinger>() == 2);
            yield return Press(Controls.Item, 0.9f);
            yield return Scene();
            Check("the cold lamp takes the blue flame", Story.Has("on_bw_lamp") && Pocket.Holding == null);
            yield return new WaitForSeconds(0.5f);
            yield return Scene(0.3f);
            Check("the grille in the truce wall lifts", !Shut("bw_truce"));
            yield return t.Shot("b15-the-truce-is-over", 1.6f);
            float waited = 0;
            while (!Story.Has("bw_truce_over") && waited < 40f) { waited += Time.deltaTime; yield return null; }
            Check($"the war ends (after {waited:0.0} s)", Story.Has("bw_truce_over"));
            yield return new WaitForSeconds(1.0f);
            yield return Scene(0.5f);
            Check("nobody is left, and the prize is uncaged", Count<ClaySoldier>() == 0 && !Shut("bw_prize"));
            t.Note("the truce went to: " + (Story.Has("bw_red_won") ? "red" : Story.Has("bw_blue_won") ? "blue" : "nobody"));
            int v0 = Story.Count("vessels");
            yield return Open("bw_vessel");
            Check("a flame vessel", Story.Count("vessels") == v0 + 1);
            // ------------------------------------------------ the snore, and the last word
            Game.I.EnterMap("barrow", "south");               // (what was dead in the hall is standing again)
            Fade.Set(0);
            yield return new WaitForSeconds(0.6f);
            yield return Scene(0.3f);
            yield return Stand("nod", 146, 108, Facing.Up);
            yield return Sleep(true);
            snore = Map.Current.Find("bw_snore");
            if (snore) { p.pos = snore.basePos + new Vector2(0, -0.5f); p.Face(Facing.Up); p.SetState(Player.State.Free, "idle"); yield return new WaitForSeconds(0.2f); }
            yield return Press(Controls.Interact);
            yield return Scene();
            yield return Sleep(false);
            Check("Nod's snore, folded up small", Pocket.Holding != null && Pocket.Holding.id == "snore");
            yield return Stand("door", 208, 196, Facing.Up);
            yield return new WaitForSeconds(0.3f);
            int scarabs = Count<Scarab>();
            p.health.hp = p.health.max;
            Enemy near = null;
            foreach (var e in Enemy.All) if (e && !e.health.Dead && (near == null || Vector2.Distance(e.pos, p.pos) < Vector2.Distance(near.pos, p.pos))) near = e;
            // (a snore carries about four tiles: he lets it out from two and a half)
            if (near) { p.pos = near.pos + new Vector2(0, -2.5f); p.Face(Facing.Up); p.SetState(Player.State.Free, "idle"); }
            yield return null;
            yield return Press(Controls.Item, 0.2f);
            bool slept = false;
            for (float w = 0; w < 2.5f && !slept; w += Time.deltaTime)
            {
                foreach (var e in Enemy.All) if (e && e.asleep > 0) slept = true;
                p.health.hp = p.health.max;
                yield return null;
            }
            Check($"let out at something awake ({scarabs} scarabs), it is not awake for long", slept);
            Check("and the snore is spent", Pocket.Holding == null);
            yield return Scene(0.3f);
            yield return t.Shot("b16-the-snore", 0.3f);
            KillAll();
            yield return new WaitForSeconds(0.5f);
            yield return Scene(0.3f);
            word = Map.Current.Find("bw_word");
            yield return Sleep(true);
            if (word) { p.pos = word.basePos + new Vector2(0, -0.6f); p.Face(Facing.Up); p.SetState(Player.State.Free, "idle"); yield return new WaitForSeconds(0.2f); }
            yield return Press(Controls.Interact);
            yield return Scene();
            yield return Sleep(false);
            Check("the last word of the argument", Pocket.Holding != null && Pocket.Holding.id == "word");
            p.SetState(Player.State.Free, "idle");
            yield return Press(Controls.Item, 0.9f);
            yield return Scene();
            Check("he has the last word", Pocket.Holding == null && Story.Count("lastword_used") == 1);
            // ------------------------------------------------ the plan, and the way out
            Story.Set("item_map_barrow");
            // (the pack stops the clock: these waits are by the wall clock)
            Pause.TestDo = "open";
            yield return new WaitForSecondsRealtime(0.4f);
            Pause.TestDo = "page " + Pause.MapPage;
            yield return new WaitForSecondsRealtime(0.4f);
            yield return t.Shot("b17-the-plan", 0.2f);
            Pause.TestDo = "page " + Pause.ItemPage;
            yield return new WaitForSecondsRealtime(0.4f);
            yield return t.Shot("b18-the-pack", 0.2f);
            Pause.TestDo = "close";
            yield return new WaitForSecondsRealtime(0.4f);
            yield return Stand("door", 208, 190, Facing.Down);
            Controls.Fake = Vector2.down;
            for (float w = 0; w < 4f && Game.I.CurrentMap == "barrow"; w += Time.deltaTime) yield return null;
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(0.9f);
            Check("out by the one door, onto the hill", Game.I.CurrentMap == "necropolis" && Game.I.CurrentSpawn == "barrow");
            yield return t.Shot("b19-back-on-the-hill", 0.3f);
            // the generals have heard
            Npc gen = null;
            foreach (var n in Npc.All) if (n && n.id == "general_a") gen = n;
            if (gen && gen.talk != null)
            {
                Story.Run(gen.talk(), gen);
                yield return Scene(0.5f);
                Check("the generals have something to say about their piece", Story.Count("generals_piece") == 1);
            }
            else Check("the generals are at their game", false);
            Save.ClearAll();
            t.Note(bad == 0 ? "BARROW OK" : $"BARROW: {bad} FAILED");
        }

        // ---------------------------------------------------------------------------- the Last Piece, played
        static IEnumerator Piece(AutoTest t)
        {
            DialogueBox.AutoAdvance = 0.1f;
            int wins = 0;
            for (int round = 0; round < 4; round++)
            {
                Kit();
                foreach (var f in new[] { "bw_red", "bw_blue" }) Story.Set(f);
                Random.InitState(3100 + round * 77);
                Game.I.EnterMap("barrow", "south");
                Fade.Set(0);
                var p = Player.I;
                p.SetState(Player.State.Free, "idle");
                yield return new WaitForSeconds(0.3f);
                yield return Stand("board", 180, 198, Facing.Up);
                var piece = LastPiece.Current;
                var b = Board.I;
                if (!piece || !b) { t.Note("FAIL no piece on the board"); yield break; }
                yield return Walk(Vector2.up, 0.45f, 0.2f);
                yield return Scene(0.5f);
                float time = 0, swingCd = 0;
                int hp0 = p.health.hp, stalls = 0, swings = 0;
                int pieceMax = piece ? piece.health.max : 0;
                bool was = false;
                while (piece && !piece.health.Dead && p.state != Player.State.Dead && time < 200f)
                {
                    float dt = Time.deltaTime;
                    time += dt; swingCd -= dt;
                    if (piece.Stalled && !was) stalls++;
                    was = piece.Stalled;
                    Vector2 go = Vector2.zero;
                    bool swing = false;
                    var d = piece.pos + new Vector2(0, 0.3f) - p.pos;
                    if (piece.Stalled)
                    {
                        // it is only clay: go in and cut
                        if (d.magnitude > 1.25f) go = d.normalized;
                        else { p.Face(Mathf.Abs(d.x) > Mathf.Abs(d.y) ? (d.x < 0 ? Facing.Left : Facing.Right) : (d.y < 0 ? Facing.Down : Facing.Up)); swing = swingCd <= 0; }
                    }
                    else
                    {
                        // the nearest rosette that still counts and that it is not standing next to
                        Vector2 best = p.pos; float bd = 999f;
                        foreach (var q in new[] { new Vector2Int(0, 0), new Vector2Int(0, 2), new Vector2Int(6, 0), new Vector2Int(6, 2), new Vector2Int(3, 1) })
                        {
                            if (b.Spent(q.x, q.y) || Vector2.Distance(b.Center(q.x, q.y), piece.pos) < b.cell * 1.1f) continue;
                            float dd = Vector2.Distance(b.Center(q.x, q.y), p.pos);
                            if (dd < bd) { bd = dd; best = b.Center(q.x, q.y); }
                        }
                        var to = best - p.pos;
                        if (to.magnitude > 0.25f) go = to.normalized;
                    }
                    Controls.Fake = p.state == Player.State.Free ? go : Vector2.zero;
                    if (swing && p.state == Player.State.Free) { Controls.FakePress = Controls.Attack; swingCd = 0.3f; swings++; }
                    else if (swing && p.state == Player.State.Attack && swingCd <= 0) { Controls.FakePress = Controls.Attack; swingCd = 0.25f; swings++; }
                    yield return null;
                }
                Controls.Fake = Vector2.zero;
                bool won = Story.Has("dead_bw_piece") || (piece == null) || piece.health.Dead;
                if (won && p.state != Player.State.Dead) wins++;
                t.Note($"round {round + 1}: {(won && p.state != Player.State.Dead ? "WON" : p.state == Player.State.Dead ? "fell" : "ran out of time")} in {time:0} s, {stalls} illegal moves, {swings} cuts, "
                     + $"life {p.health.hp}/{hp0}, piece {(piece ? piece.health.hp : 0)}/{pieceMax}");
                if (round == 0) yield return t.Shot("p-round1-end", 0.1f);
                yield return new WaitForSeconds(1.5f);
                yield return Scene(0.5f);
            }
            Save.ClearAll();
            t.Note($"PIECE: the bot won {wins} of 4");
        }
    }
}
