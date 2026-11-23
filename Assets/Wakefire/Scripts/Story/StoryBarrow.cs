// The Generals' Barrow: what its rooms say the first time, the two standards, the Last Piece and
// the rule that beats it, Nod's Pocket, and the nine seconds it takes to finish a war that has
// been at a draw for three hundred and ninety-one years.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        Map barrowMap;
        bool truceRunning;
        float truceClock;

        void SetupBarrow(Map m)
        {
            barrowMap = m;
            truceRunning = false;
            truceClock = 0;
            Rooms.Entered -= BarrowRoom;
            Rooms.Entered += BarrowRoom;
            foreach (var pr in m.props)
                if (pr && pr.Kind == "standard" && Has(pr.data.id)) pr.SetSprite(pr.data.s + "_down", pr.data.px, pr.data.py);
            // he is already standing in the first room by the time anything is listening
            if (Rooms.I && Rooms.I.current != null) BarrowRoom(Rooms.I.current);
        }

        void BarrowRoom(Room r)
        {
            if (!Game.I || !Map.Current || Game.I.CurrentMap != "barrow") return;
            if (r.id == "board" && !Has("dead_bw_piece")) return;                       // the Piece has the hall, and its own music when it moves
            Music.Play(Map.Current.data.music);
            switch (r.id)
            {
                case "door":
                    if (Bump("bw_door_seen") == 0)
                        RunWhenFree(One(Narrate("Mud brick, and two of everything: two drums, two colours of shield, two sets of footprints in the dust.^One door. You are standing in it.")));
                    break;
                case "red":
                    if (!Has(Mech.ClearFlag("barrow", "red")) && Bump("bw_red_seen") == 0)
                        RunWhenFree(One(Narrate("Ushur's spearmen, in fired clay, at attention.^They have held this hall against Baltu's slingers since the funeral.| They are fairly sure you are a slinger.")));
                    break;
                case "blue":
                    if (!Has(Mech.ClearFlag("barrow", "blue")) && Bump("bw_blue_seen") == 0)
                        RunWhenFree(One(Narrate("Baltu's slingers, in fired clay, on the far side of a ditch.^It is a good ditch. They dug it to keep Ushur's spearmen out, and it has.| They are fairly sure you are a spearman.")));
                    break;
                case "nod":
                    if (Bump("bw_nod_seen") == 0)
                        RunWhenFree(One(Narrate("The quietest room in the barrow.^Somebody chose it for that.")));
                    break;
                case "truce":
                    if (!Has("on_bw_lamp") && Bump("bw_truce_seen") == 0)
                        RunWhenFree(One(Narrate("A wall down the middle of a parade ground, and a grille in the wall.^Red on one side of it. Blue on the other.| Neither has blinked since the funeral. They are clay. It is easier.")));
                    break;
            }
        }

        /// <summary>The parts of the barrow's story that happen because of where Azar is standing.</summary>
        void BarrowUpdate()
        {
            var m = Map.Current;
            var p = Player.I;
            if (!m || m != barrowMap || !p || Game.Paused) return;
            // the war, once the lamp is lit: whoever wins it has nobody left to tell
            if (Has("on_bw_lamp") && !Has("bw_truce_over") && Rooms.I && Rooms.I.current != null && Rooms.I.current.id == "truce" && !truceRunning)
            {
                if (truceClock == 0) WatchTheField(true);
                truceClock += Time.deltaTime;
                ClaySoldier.Count(out int red, out int blue);
                if (truceClock > 1.5f && (red == 0 || blue == 0 || truceClock > 16f)) StartCoroutine(TruceEnds(red, blue));
            }
            if (Running || Game.Busy || p.state != Player.State.Free) return;
            // a foot on the board is a move
            var piece = LastPiece.Current;
            if (piece && piece.Waiting && Board.I && Board.I.At(p.pos, out _, out _)) Run(PieceWakes(piece));
        }

        Transform fieldWatch;

        /// <summary>While the two armies settle it, the picture stands back far enough to take in the parade
        /// ground and the man who started it; afterwards it is his again.</summary>
        void WatchTheField(bool on)
        {
            var v = PixelView.I;
            if (!v) return;
            if (!on)
            {
                if (fieldWatch) { if (v.target == fieldWatch && Player.I) v.target = Player.I.transform; Destroy(fieldWatch.gameObject); }
                return;
            }
            if (!Rooms.I || Rooms.I.current == null) return;
            var r = Rooms.I.current.rect;
            if (!fieldWatch) fieldWatch = new GameObject("FieldWatch").transform;
            fieldWatch.SetParent(Map.Current ? Map.Current.transform : null, false);
            fieldWatch.position = new Vector3(r.xMin + 236f / 16f, r.yMax - 128f / 16f, 0);
            v.target = fieldWatch;
        }

        IEnumerator TruceEnds(int red, int blue)
        {
            truceRunning = true;
            yield return new WaitForSeconds(1.6f);
            foreach (var e in Enemy.All.ToArray())
            {
                if (!(e is ClaySoldier c) || c.health.Dead) continue;
                c.Crumble();
                yield return new WaitForSeconds(0.35f);
            }
            Set("bw_truce_over");
            yield return new WaitForSeconds(0.8f);
            WatchTheField(false);
            // the war is over for good: none of them is standing the next time he comes down here
            foreach (var id in new[] { "bw_tr0", "bw_tr1", "bw_tb0", "bw_tb1" }) Set("dead_" + id);
            Set(red > 0 && blue == 0 ? "bw_red_won" : blue > 0 && red == 0 ? "bw_blue_won" : "bw_nobody_won");
            truceRunning = false;
        }

        // ------------------------------------------------------------------ the standards
        public IEnumerator LowerStandard(Prop pr)
        {
            var p = Player.I;
            bool red = pr.data.text == "red";
            if (Has(pr.data.id))
            {
                yield return Narrate(red ? "A bare pole, and Ushur's colours in a heap at the foot of it.^You feel the heap is looking at you."
                                         : "A bare pole, and Baltu's colours in a heap at the foot of it.^It is a very dignified heap.");
                yield break;
            }
            p.Face(Facing.Up);
            if (p.anim.model) { p.SetState(Player.State.ItemGet, "open"); yield return Wait(0.5f); }
            Sfx.Play("standard_down", 1f, 0f);
            yield return Wait(0.45f);
            pr.SetSprite(pr.data.s + "_down", pr.data.px, pr.data.py);
            Fx.Dust(pr.basePos + new Vector2(0, -0.2f), 6);
            Set(pr.data.id);
            bool both = Has("bw_red") && Has("bw_blue");
            yield return Narrate(red
                ? "You haul down Ushur's standard.^A long way overhead, an old man says: {g}'Who did that?'{/}| Another old man says he has no idea, in the voice of somebody who is delighted."
                : "You haul down Baltu's standard.^A long way overhead, an old man says: {g}'That is cheating.'{/}| Another old man says: {g}'You only say that when it happens to you.'{/}");
            if (!both) yield return Narrate(red ? "One standard down. Baltu's is still flying, in the west hall." : "One standard down. Ushur's is still flying, in the east hall.");
            p.SetState(Player.State.Free, "idle");
            Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn);
        }

        // ------------------------------------------------------------------ the Last Piece
        IEnumerator PieceWakes(LastPiece piece)
        {
            var p = Player.I;
            p.SetState(Player.State.Cutscene, "idle");
            Music.Stop();
            if (Bump("bw_piece_seen") == 0)
            {
                yield return CamTo(piece.pos + new Vector2(0, 0.6f), 0.9f);
                yield return Wait(0.3f);
                yield return Narrate("On the middle rosette stands a soldier of clay as tall as a door, a shield on its arm.^It has not moved in three hundred and ninety-one years.| It has not been anybody's move.");
                yield return CamBack(0.6f);
                yield return Narrate("Your foot comes down on the board.^That was a move.");
            }
            Sfx.Play("piece_down", 1f, 0f);
            PixelView.I.Shake(2, 0.3f);
            Music.Play("boss");
            if (piece) piece.Begin();
            p.SetState(Player.State.Free, "idle");
        }

        /// <summary>Rule the fourth, the first time it saves him.</summary>
        public void IllegalMove()
        {
            if (Bump("bw_illegal") != 0 || Running) return;
            Run(IllegalScene());
        }

        IEnumerator IllegalScene()
        {
            yield return Narrate("The Piece stops short of your square and rocks on its base.^Overhead, faintly: {g}'He is on a rosette.'{/}| {g}'I can SEE he is on a rosette.'{/}| "
                               + "Rule the fourth. Until they have finished arguing, it is only clay.");
            var piece = LastPiece.Current;
            if (piece) piece.StallAgain();
        }

        public void PieceDown()
        {
            StartCoroutine(PieceDownScene());
        }

        IEnumerator PieceDownScene()
        {
            yield return new WaitForSeconds(0.9f);
            while (Running || Game.Busy) yield return null;
            Music.Play(Map.Current ? Map.Current.data.music : "barrow");
            Run(One(Narrate("The Last Piece comes apart on its own square.^Three hundred and ninety-one years unbeaten, and taken by a night watchman who was not even playing.| "
                          + "A long way overhead, a general says a word that is not in the rules.")));
        }

        // ------------------------------------------------------------------ what the generals have to say about it
        /// <summary>Put in front of the generals' usual talk: true if they had something new to say.</summary>
        IEnumerator GeneralsAboutTheBarrow(System.Action<bool> said)
        {
            const string a = "General Ushur", b = "General Baltu";
            if (Has("dead_bw_piece") && Bump("generals_piece") == 0)
            {
                said(true);
                yield return Say(a, "Something has taken your piece.", "general");
                yield return Say(b, "I was THINKING about that piece.", "general");
                yield return Say(a, "For three hundred and ninety-one years.", "general");
                yield return Say(b, "It was a good piece.| ...Whose move is it now?", "general");
                yield return Say(a, "His, I think.", "general");
                if (Has("item_pocket"))
                {
                    yield return Say(b, "Is that Nod's pocket? We wondered where that went.| We wondered where Nod went.", "general");
                    yield return Say(a, "He will be asleep. Try anywhere flat.", "general");
                }
                yield break;
            }
            if (!Has("item_pocket") && Count("generals") >= 1 && Bump("generals_barrow") == 0)
            {
                said(true);
                yield return Say(a, "If you are going in to see the king, go by way of our barrow first. The big mound, behind him.", "general");
                yield return Say(b, "He means MY barrow.", "general");
                yield return Say(a, "Our quartermaster is in there. Nod. He was the best we ever had.", "general");
                yield return Say(b, "Always finding useful things in his dreams.", "general");
                yield return Say(a, "The only problem was, we always caught him sleeping on the job.", "general");
                yield return Say(b, "Take his pocket. He is not using it.| Mind the piece on the board. It is mine.", "general");
                yield return Say(a, "It is not his.", "general");
                yield break;
            }
            said(false);
        }
    }
}
