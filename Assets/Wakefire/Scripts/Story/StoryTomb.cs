// The king's tomb as a dungeon: what its halls say the first time, the servants and the order
// they were left with, the lamp bearers, the scarab that thinks it is rolling the sun, and the
// Sun Wheel it was keeping.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        Map tombMap;
        bool servantsAside, servantsKnown;

        void SetupTomb(string map, Map m)
        {
            tombMap = m;
            servantsKnown = false;
            Rooms.Entered -= TombRoom;
            Rooms.Entered += TombRoom;
            ServantsNow(true);
            // he is already standing in the first room by the time anything is listening
            if (Rooms.I && Rooms.I.current != null) TombRoom(Rooms.I.current);
        }

        void TombRoom(Room r)
        {
            if (!Game.I || !Map.Current || Map.Current != tombMap) return;
            string map = Game.I.CurrentMap;
            if (map != "tomb_1" && map != "tomb_2" && map != "tomb_hi") return;
            if (r.id == "roller" && !Has("dead_t2_roller")) return;                  // the beetle has the hall, and its own music
            Music.Play(Map.Current.data.music);
            string seen = "tomb_seen_" + map + "_" + r.id;
            string line = null;
            switch (map + "/" + r.id)
            {
                case "tomb_1/door":
                    line = "The air in here is four hundred years old.^It is not pleased to be breathed."; break;
                case "tomb_1/store":
                    line = "Jars for the journey, an offering scale, and a grille.^Nothing in this room was ever given. It was all owed."; break;
                case "tomb_1/hall":
                    line = "The king's guard, in fired clay, a man to a niche all down the hall.^Two of the niches are empty."; break;
                case "tomb_1/treasury":
                    line = "The treasury. What the thieves have not got to, behind a grille they could not get through.^Not for want of trying. There is a bent spoon on the floor."; break;
                case "tomb_1/lampwalk":
                    if (!Has("chapter2_done")) line = "Lamps, coming and going down the walk at the height a man would carry them.^Somebody is carrying them.";
                    break;
                case "tomb_1/well":
                    line = "The tomb's well. The dead filled it with dark, to keep the living on this side of it.^They did not think about dreamers. They don't, much."; break;
                case "tomb_2/lyre":
                    line = "The inner halls.^Nobody alive was ever meant to see these, and nobody dead was meant to leave."; break;
                case "tomb_2/queen":
                    line = "A small room, a long way from the king's.^It is the quietest place in the tomb. Somebody arranged that."; break;
                case "tomb_hi/stairhead":
                    line = "The king's road. Nobody was meant to walk it twice.^The one man who walked it once was carried."; break;
                case "tomb_hi/crossing":
                    line = "A bronze perch, a spear's length high, and on it one of the king's vultures.^He kept them the way other kings keep hawks: to see who they circled.| "
                         + "It is looking at you the way you would look at a fig."; break;
                case "tomb_hi/mews":
                    if (!Has(Mech.ClearFlag("tomb_hi", "mews")))
                        line = "The king's mews. Four perches, and four hundred years of patience.^Nothing in here has eaten since the funeral, and they were not invited to that.";
                    break;
                case "tomb_hi/steward":
                    if (!Has("ghostkey"))
                        line = "The steward's rest. His coffin is on the far side of a drop, and so, by the look of it, is he.^A drawbridge stands on end over there. Somebody did not want to be asked for things.";
                    break;
                case "tomb_hi/threshold":
                    if (!Has("door_t3_kingdoor"))
                        line = "The king's own door. No bull on it, no sun.^Only the place where a keyhole used to be, and the cold coming off it.";
                    break;
                case "tomb_hi/roost":
                    line = "Where the old birds went. There is one left.^It has outlived a king, a queen, four hundred years of stewards, and its own curiosity."; break;
                case "tomb_2/suncourt":
                    line = "A court built to hold the morning. Four hundred mornings a year have not found the way in.^A gong hangs round the corner, where no arm will reach it."; break;
                case "tomb_2/wardens":
                    if (!Has(Mech.ClearFlag("tomb_2", "wardens")))
                        line = "Two of the king's clay, behind shields the size of the doors they were made to stand in.^They have waited four hundred years for something to stand in front of.";
                    break;
                case "tomb_2/brink":
                    if (!Has("on_t2_bridge"))
                        line = "The hall stops. It starts again on the far side of a drop, where a drawbridge stands on end.^One rope is holding it up. It is a good rope. It is a long way off.";
                    break;
            }
            if (line != null && Bump(seen) == 0) RunWhenFree(One(Narrate(line)));
        }

        // ------------------------------------------------------------------ the servants, and their order
        /// <summary>The servants stand in the one doorway because they were told to, four hundred years ago. Take
        /// the order out of the dream and nobody has told them anything: they sit down, and the way is open.
        /// Put it back and they are on their feet again.</summary>
        void ServantsNow(bool quiet)
        {
            var m = tombMap;
            if (!m || Game.I.CurrentMap != "tomb_1") return;
            bool aside = Has("chapter2_done") || Has("took_t1_order") || Has("spent_t1_order");
            bool changed = servantsKnown && aside != servantsAside;
            servantsAside = aside; servantsKnown = true;
            var mk = m.Marker("servants");
            if (mk != null)
            {
                var a = Map.ToWorld(mk.x, mk.y + mk.h);
                var r = new Rect(a.x + 0.05f, a.y + 0.05f, mk.w / 16f - 0.1f, mk.h / 16f - 0.1f);
                foreach (var s in Solids.All) if (s.layer == WorldLayer.Waking && !s.pit && s.r.Overlaps(r)) s.enabled = !aside;
            }
            foreach (var n in Npc.All)
            {
                if (!n || n.id == null || !n.id.StartsWith("servant_")) continue;
                n.SetIdle(aside ? "sit" : "wait");
                n.Play(aside ? "sit" : "wait", true);
            }
            if (quiet || !changed || Has("chapter2_done")) return;
            if (aside)
                RunWhenFree(One(Narrate(Bump("servants_sat") == 0
                    ? "The servants look at each other.^Nobody has told them to stand there. For the first time in four hundred years, nobody has told them anything.| One of them sits down. It takes him a while to remember how."
                    : "The servants are sitting down again.^They are getting better at it.")));
            else
                RunWhenFree(One(Narrate("The servants are back on their feet, shoulder to shoulder.^Somebody has put their order back.| They do not thank you. They were told to stand there, not to thank people.")));
        }

        /// <summary>The parts of the tomb's story that happen because of where Azar is standing.</summary>
        void TombUpdate()
        {
            var m = Map.Current;
            var p = Player.I;
            if (!m || m != tombMap || !p || Game.Paused) return;
            if (Game.I.CurrentMap == "tomb_1")
            {
                bool aside = Has("chapter2_done") || Has("took_t1_order") || Has("spent_t1_order");
                // (what he took in the dream is only missed when he is awake to see it missed)
                if (servantsKnown && aside != servantsAside && !(Dream.I && Dream.I.IsDreamAt(p.pos))) ServantsNow(false);
            }
            if (Running || Game.Busy || p.state != Player.State.Free || Rooms.Sliding) return;
            var roller = SunRoller.Current;
            if (roller && roller.Waiting && Rooms.I && Rooms.I.current != null && Rooms.I.current.id == "roller") Run(RollerWakes(roller));
        }

        // ------------------------------------------------------------------ the lamp bearers
        public void BearerPassed()
        {
            if (Bump("bearer_passed") != 0 || Running) return;
            Run(Narrate("The blade goes through him like a hand through lamp smoke.^He is dead, and he is on duty. A khopesh is not going to change either.| The lamp is bronze, though. The lamp is real."));
        }

        public void BearerLampOut()
        {
            if (Bump("bearer_lamp") != 0 || Running) return;
            Run(Narrate("The lamp was hanging in the air where he held it. Now it is on the floor, and out.^The dead do not dream. What they carry was never given the choice."));
        }

        public void BearerOffDuty()
        {
            if (Bump("bearer_off") != 0 || Running) return;
            Run(Narrate("He looks at his hands.^Four hundred years, and nobody ever told him he could put it down.| He goes off duty the way a lamp goes out."));
        }

        public void BearerStepsAside()
        {
            if (Bump("bearer_aside") != 0 || Running) return;
            Run(Narrate("The bearer sees what is on your belt, and finds something to look at on the floor.^Whoever carries that key is the king's business.| "
                      + "He has been dead four hundred years. He knows better than to be the king's business."));
        }

        // ------------------------------------------------------------------ the steward, and the Ghost Key
        IEnumerator TalkSteward()
        {
            const string who = "The Steward";
            if (Has("ghostkey"))
            {
                if (Bump("steward_after") == 0)
                {
                    yield return Say(who, "You have it. Good.| Four hundred years I could not pick it up, and it is gone in an afternoon.", "clerk");
                    yield return Say(who, "Sign here.| ...You cannot sign. Neither can I. We will say it is signed.", "clerk");
                }
                else yield return Say(who, "He will not be pleased to see you.| He has not been pleased to see anybody since the funeral, and he enjoyed the funeral.", "clerk");
                yield break;
            }
            if (Bump("steward") == 0)
            {
                yield return Say(who, "The key? The key is kept about my person. It says so on the treasury wall. I had it carved.", "clerk");
                yield return AzarSays("Where is your person?");
                yield return Say(who, "In that coffin. I am, as you see, not.| The key died with me. It is, strictly, the ghost of a key.", "clerk");
                yield return Say(who, "And I am the ghost of a steward, and you would think that would help.| I have been trying to pick it up for four hundred years.", "clerk");
            }
            else yield return Say(who, "It is in the chest. I cannot open the chest. I cannot open anything.| Do you know what that is like, for a steward?", "clerk");
        }

        // ------------------------------------------------------------------ the Sun Roller
        IEnumerator RollerWakes(SunRoller roller)
        {
            var p = Player.I;
            p.SetState(Player.State.Cutscene, "idle");
            Music.Stop();
            if (Bump("roller_seen") == 0)
            {
                yield return CamTo(roller.pos + new Vector2(0, 1.0f), 0.9f);
                yield return Wait(0.3f);
                yield return Narrate("A scarab the size of a cart, up on a ball of gold.^Everything the thieves dropped is in that ball. Cups. Rings. A king's ransom in small change.| "
                                   + "It has been rolling it up and down this hall for four hundred years, on the understanding that it is the sun.");
                yield return CamBack(0.6f);
                yield return Narrate("It has just noticed that the sun has a visitor.");
            }
            Sfx.Play("scarab", 1f, 0f);
            PixelView.I.Shake(2, 0.3f);
            Music.Play("boss");
            if (roller) roller.Begin();
            p.SetState(Player.State.Free, "idle");
        }

        public void RollerTumbled()
        {
            if (Bump("roller_tumbled") != 0 || Running) return;
            Run(RollerTumbledScene());
        }

        IEnumerator RollerTumbledScene()
        {
            yield return Narrate("The sun stops at the third wall. The beetle does not.^It is on its back. Everything with six legs has this problem.| That is the moment.");
        }

        public void RollerDown() => StartCoroutine(RollerDownScene());

        IEnumerator RollerDownScene()
        {
            yield return new WaitForSeconds(1.0f);
            while (Running || Game.Busy) yield return null;
            Music.Play(Map.Current ? Map.Current.data.music : "tomb");
            Run(One(Narrate("The Sun Roller folds its legs, and is still.^The sun is all over the floor: cups, rings, and four hundred years of small change.| Morning is cancelled until further notice.")));
            Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn);
        }

        public static string WheelText =>
            "You got the {g}SUN WHEEL{/}!^A bronze disc with an edge of gold. It was carried before the king in the morning and behind him at night.| "
          + "He took it into the dark with him, so that Ashkel could not have it.^It comes back when it is thrown. It is the only thing he ever owned that did.";

        public static string LessonWheel(bool touch) => touch
            ? "Throw it with the {g}item{/} button. It goes the way you are walking: straight, or across the corners.^It banks off the first two walls it meets. The third sends it home. It rings gongs, cuts rope, and does not mind a drop.| "
            + "Press {g}item{/} again while it is out and it comes home at once, through whatever is in the way.^Things with shields have never once looked behind them."
            : "Throw it with {g}F{/}. It goes the way you are walking: straight, or across the corners.^It banks off the first two walls it meets. The third sends it home. It rings gongs, cuts rope, and does not mind a drop.| "
            + "Press {g}F{/} again while it is out and it comes home at once, through whatever is in the way.^Things with shields have never once looked behind them.";

        // ------------------------------------------------------------------ ropes
        public void RopeCut(string id, bool weight = false)
        {
            if (weight)
            {
                if (Bump("weight_cut") != 0 || Running) return;
                Run(Narrate("The rope parts, and a block of stone the size of a calf goes down into the dark.^It is some time before it is heard from.| It was all that was holding the grille shut."));
                return;
            }
            if (Bump("rope_cut") != 0 || Running) return;
            Run(Narrate("The rope parts.^The drawbridge thinks about it, for about as long as it has been standing there, and comes down."));
        }
    }
}
