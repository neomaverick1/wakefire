// The ziggurat's own beats: what its rooms say the first time, and the Bronze Herdsman's hall.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        void SetupZig(Map m)
        {
            Rooms.Entered -= ZigRoom;
            Rooms.Entered += ZigRoom;
            // he is already standing in the first room by the time anything is listening
            if (Rooms.I && Rooms.I.current != null) ZigRoom(Rooms.I.current);
        }

        void ZigRoom(Room r)
        {
            if (!Game.I || !Map.Current) return;
            string map = Game.I.CurrentMap;
            if (map != "zig_2" && map != "zig_hi") return;
            if (map == "zig_2" && r.id == "herd" && !Has("dead_z2_herdsman")) { RunWhenFree(HerdScene(Bump("herd_seen") == 0)); return; }
            // anywhere else on the floor, the floor's own music (he may have backed out of the hall)
            Music.Play(Map.Current.data.music);
            if (map == "zig_2" && r.id == "walk" && Bump("walk_seen") == 0)
                RunWhenFree(One(Narrate("Four bulls' heads in the wall, breathing in turn.^It is the most regular thing left in Ashkel. You could set a water-clock by it, if you could get near the water-clock.")));
            else if (map == "zig_2" && r.id == "gate" && !Has("z2_bull") && Bump("gate_seen") == 0)
                RunWhenFree(One(Narrate(Has("item_shield") ? "The bull over the stair looks at you the way a door looks at a man with no key.^You have a mirror. It has not thought about mirrors."
                                                           : "The bull over the stair looks at you the way a door looks at a man with no key.")));
            else if (map == "zig_hi" && r.id == "mouths" && !(Has("zh_h1") && Has("zh_h2") && Has("zh_h3")) && Bump("mouths_seen") == 0)
                RunWhenFree(One(Narrate("Three bulls' heads turn to look at you.^They do not turn, of course. They are bronze, and set in the wall.| It only feels like it.")));
        }

        IEnumerator HerdScene(bool first)
        {
            yield return Wait(0.25f);
            if (first)
            {
                yield return Narrate("A man of bronze stands in the middle of the hall, leaning on an ox-goad, exactly as he was left.^Nobody told the Herdsman the bulls are metal now. Nobody tells the Herdsman anything.");
                yield return Narrate("He looks up. He counts you.| You are not a bull.^This appears to be a problem.");
            }
            Music.Play("boss");
        }
    }
}
