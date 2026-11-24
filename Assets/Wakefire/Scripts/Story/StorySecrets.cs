// What the game says about the things a dungeon does not put on its plan, once each.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        /// <summary>A cut on a walled-up doorway.</summary>
        public void WallHollow()
        {
            if (HallsQuiet || Running || Bump("wall_hollow") != 0) return;
            Run(Narrate("It rings hollow.^There is a doorway under this, and somebody went to some trouble to say there is not.| "
                      + "A cut will not bring it down. The last blow of three might: the one with your whole weight behind it."));
        }

        public void WallDown()
        {
            if (HallsQuiet || Bump("wall_down") != 0) return;
            RunWhenFree(One(Narrate("The wall comes down all at once, the way a story does when one part of it is not true.^"
                                  + "Somebody walled this doorway up. Whoever it was is past objecting.")));
        }

        /// <summary>The first room he has stood in that is on no plan.</summary>
        public void SecretRoom()
        {
            if (HallsQuiet || Bump("secret_room") != 0) return;
            RunWhenFree(One(Narrate("A room that is on no plan.^The scroll will not show you these. Your own feet will, once they have stood in one.| "
                                  + "There are others. Walls that ring hollow. Stairs that wait under a floor until nobody is watching. Doorways that are only there when your eyes are shut.")));
        }

        public void Burrowed()
        {
            if (HallsQuiet || Bump("burrowed") != 0) return;
            RunWhenFree(One(Narrate("Hands and knees, in the dark, the way the jackals go.^It is exactly as wide as a jackal. You are not, and you have the elbows to prove it.")));
        }

        /// <summary>He jumped down a hole and there was a floor under it.</summary>
        public void CameDown()
        {
            if (HallsQuiet || Bump("came_down") != 0) return;
            RunWhenFree(One(Narrate("That was a floor.^You went down a hole and the building caught you. It does not always.| "
                                  + "A hole with light coming up it has something under it. A hole with nothing coming up it has nothing under it, for a long way.")));
        }
    }
}
