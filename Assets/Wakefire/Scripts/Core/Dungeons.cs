// The plan of each dungeon, as its builder wrote it (Art/pixel/dkit.py puts one in
// Resources/Menu/dungeon_<name>.json): floors of rooms on a grid of cells, the doorways between
// them, and which chest stands in which room. The map page draws it; the tuning forks listen to it.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public static class Dungeons
    {
        [Serializable] public class Room { public string id, name, mark; public int c, r, cw, ch; }
        [Serializable] public class Link { public int c, r; public string side, kind, to, a, b, id; }
        [Serializable] public class Chest { public string id, room; public bool big; }
        [Serializable] public class Floor { public string map, label; public int order, cols, rows; public Room[] rooms; public Link[] links; public Chest[] chests; }
        [Serializable] public class Plan { public Floor[] floors; public string name; }

        static readonly string[] Names = { "crypt", "zig", "barrow", "tomb" };
        static readonly Dictionary<string, Plan> plans = new Dictionary<string, Plan>();

        /// <summary>The dungeon this map is a floor of, or null (the open world, and any hall with no plan).</summary>
        public static Plan Of(string map)
        {
            if (string.IsNullOrEmpty(map)) return null;
            foreach (var n in Names)
            {
                if (!plans.TryGetValue(n, out var d))
                {
                    var j = Resources.Load<TextAsset>("Menu/dungeon_" + n);
                    d = j ? JsonUtility.FromJson<Plan>(j.text) : null;
                    if (d != null) d.name = n;
                    plans[n] = d;
                }
                if (d == null || d.floors == null) continue;
                foreach (var f in d.floors) if (f.map == map) return d;
            }
            return null;
        }

        public static Floor FloorOf(Plan d, string map)
        {
            if (d != null) foreach (var f in d.floors) if (f.map == map) return f;
            return null;
        }

        public static string Title(string name) => name switch
        {
            "crypt" => "THE CRYPT", "zig" => "THE ZIGGURAT", "barrow" => "THE BARROW", "tomb" => "THE KING'S TOMB", _ => "THE WORLD",
        };

        /// <summary>The full-size dungeons each have a tuning fork that finds their chests. The small ones do
        /// not: their scroll shows what is in them.</summary>
        public static bool HasFork(string name) => name == "zig" || name == "tomb";

        /// <summary>Each fork is enamelled in its house's colour: lapis for the ziggurat, carnelian for the king's tomb.</summary>
        public static Color32 ForkColor(string name) => name == "tomb" ? new Color32(226, 84, 70, 255) : new Color32(86, 140, 246, 255);

        /// <summary>How many chests in a room nobody has opened yet.</summary>
        public static int Shut(Floor f, string room)
        {
            int n = 0;
            if (f != null && f.chests != null)
                foreach (var c in f.chests) if (c.room == room && !Story.Has("chest_" + c.id)) n++;
            return n;
        }

        /// <summary>The rooms a doorway joins this one to (never mind whether the door is open).</summary>
        public static List<string> Next(Floor f, string room)
        {
            var next = new List<string>();
            if (f == null || f.links == null) return next;
            foreach (var l in f.links)
            {
                if (string.IsNullOrEmpty(l.a) || string.IsNullOrEmpty(l.b)) continue;
                if (l.a == room && !next.Contains(l.b)) next.Add(l.b);
                else if (l.b == room && !next.Contains(l.a)) next.Add(l.a);
            }
            return next;
        }
    }
}
