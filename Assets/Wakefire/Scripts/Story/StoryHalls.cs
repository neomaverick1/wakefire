// What the game says about the staff of the high halls (the Medusas, the thurifers, the burning
// glasses), once each.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        /// <summary>Set by the build machine's play-throughs, which have a floor to get across and no time to be told things.</summary>
        public static bool HallsQuiet;

        public void MedusaSeen()
        {
            if (HallsQuiet) return;
            // (the one in the king's tomb is the same trade under another employer, and gets her own introduction)
            if (Game.I && Game.I.CurrentMap != null && Game.I.CurrentMap.StartsWith("tomb"))
            {
                if (Bump("medusa_tomb") != 0 || Running) return;
                Run(Narrate("The king had a doorkeeper sent up from the temple.^Nobody argues with a doorkeeper they cannot look at, and the king knew a great many people who wanted to argue.| "
                          + "She has been on this door four hundred years. She is still not through the hair."));
                return;
            }
            if (Bump("medusa_seen") != 0 || Running) return;
            Run(Narrate("A woman with her back to you, at her hair with a comb.^The comb is having a hard time of it. The hair is combing back.| "
                      + "The temple took her on to keep this door. Nobody argues with a doorkeeper they cannot look at."));
        }

        /// <summary>He met her eyes. (Said once he can move again: it would be unkind to explain it to a statue.)</summary>
        public void MedusaLooked()
        {
            if (HallsQuiet) return;
            if (Bump("medusa_looked") != 0) return;
            RunWhenFree(One(Narrate("You looked.^Everybody looks. For most of them it is the last thing they do.| "
                                  + "The Wakefire burned it off you before it set. Do not meet her eyes: turn your back on her, or put bronze in the way.")));
        }

        public void MedusaMeetsHerself()
        {
            if (HallsQuiet) return;
            if (Bump("medusa_mirror") != 0 || Running) return;
            Run(Narrate("She meets her own eyes in the bronze, and stops.^It is the first time she has ever seen them. Nobody has been in a position to tell her what colour they are.| "
                      + "She is stone. Stone can be cut."));
        }

        public void MedusaEyesShut()
        {
            if (HallsQuiet) return;
            if (Bump("medusa_asleep") != 0) return;
            RunWhenFree(One(Narrate("She looks straight at you, and nothing happens.^You are asleep. Your eyes are shut.| "
                                  + "It is the first advantage of sleeping on duty that the watch has ever recorded. She can still bite.")));
        }

        public void MedusaBroken()
        {
            if (HallsQuiet) return;
            if (Bump("medusa_broken") != 0) return;
            RunWhenFree(One(Narrate("The snakes go off in eleven directions.^They are the only part of her that ever wanted to leave.")));
        }

        // ---- thurifers
        public void ThuriferSeen()
        {
            if (HallsQuiet) return;
            if (Bump("thurifer_seen") != 0 || Running) return;
            Run(Narrate("A man in a saffron robe gone grey to the knee, with a censer going round over his head.^The service stopped forty nights ago. Nobody has told the thurifer.| "
                      + "Nothing gets inside the circle of that chain. Wait until he lets it out to its length, and have the bronze up when he does."));
        }

        public void CenserReturned()
        {
            if (HallsQuiet) return;
            if (Bump("censer_returned") != 0 || Running) return;
            Run(Narrate("The censer goes home the way it came, and round his neck twice.^He stands in his own incense. It is the first time he has had the full benefit of it."));
        }

        public void ThuriferDown()
        {
            if (HallsQuiet) return;
            if (Bump("thurifer_down") != 0) return;
            RunWhenFree(One(Narrate("The censer stops going round.^The air in the hall begins, slowly, to be air again.")));
        }

        // ---- burning glasses
        public void GlassSeen()
        {
            if (HallsQuiet) return;
            if (Game.I && Game.I.CurrentMap != null && Game.I.CurrentMap.StartsWith("tomb"))
            {
                if (Bump("glass_tomb") != 0 || Running) return;
                Run(Narrate("The thieves carried a burning glass up from the temple, to open the king's door with.^It opened two thieves and a donkey first, and they left it where it stood.| "
                          + "It still follows whatever moves. It does not turn as fast as a wheel of gold flies."));
                return;
            }
            if (Bump("glass_seen") != 0 || Running) return;
            Run(Narrate("A lens as wide as a shield, in a bronze ring on three legs.^The priests lit the high lamps with it from the floor. Nobody has turned it off.| "
                      + "It gathers the light, and then lets it go in a line. You can hear it gather.^Stand out of the line. Or stand in it, with the bronze up."));
        }

        public void GlassStruck()
        {
            if (HallsQuiet) return;
            if (Bump("glass_struck") != 0) return;
            RunWhenFree(One(Narrate("It is glass.^It is also three fingers thick, and has not blinked in two hundred years. A blade is not the way to begin.")));
        }

        public void GlassAnswered()
        {
            if (HallsQuiet) return;
            if (Bump("glass_answered") != 0) return;
            RunWhenFree(One(Narrate("The bronze hands it its own light back.^Glass does not care for its own light. That is one crack.")));
        }

        public void GlassBroken()
        {
            if (HallsQuiet) return;
            if (Bump("glass_broken") != 0) return;
            RunWhenFree(One(Narrate("It stops being a glass.^It goes on being extremely sharp. Mind your feet.")));
        }
    }
}
