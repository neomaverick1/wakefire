// What Azar carries. Some of it goes on the item button, one thing at a time, chosen on the item
// page of the pause screen; the rest is simply his, and does what it does without being asked.
using System;
using UnityEngine;

namespace Wakefire
{
    public static class Items
    {
        public class Def
        {
            public string id, name, art, about;
            public Func<bool> have;
            /// <summary>For the few things whose picture depends on where he is (a tuning fork is the colour of its house).</summary>
            public Func<string> artNow;
            public string Art => artNow != null ? artNow() : art;
        }

        /// <summary>The ones that go on the item button, in the order the item page shows them.</summary>
        public static readonly Def[] Usable =
        {
            new Def { id = "wakefire", name = "The Wakefire", art = "wakefire", have = () => Story.Has("item_wakefire"),
                      about = "The watch-flame of Ashkel. It never goes out.|Hold it out to light what ought to be lit. No sleep can keep the man who carries it." },
            // (a fork is in the pack only inside the dungeon it was made for)
            new Def { id = "fork", name = "Tuning Fork", art = "fork_zig", artNow = () => "fork_" + (Fork.Here ?? "zig"), have = () => Fork.Here != null,
                      about = "Strike it and listen. The nearer a chest nobody has opened, the higher it hums, and the room goes on the plan.|It stays in the house it was made for. Outside, it is not in your pack." },
            new Def { id = "wheel", name = "The Sun Wheel", art = "sun_wheel", have = () => Story.Has("item_wheel"),
                      about = "A bronze disc with an edge of gold, made for a king who missed the sun.|Thrown, it banks off walls and comes back to the hand." },
        };

        /// <summary>Everything else worth showing.</summary>
        public static readonly Def[] Kept =
        {
            new Def { id = "sword", name = "Khopesh of the Watch", art = "khopesh", have = () => Story.Has("item_sword"),
                      about = "The first watchman's own blade, hooked like a sickle.|Three cuts, if you keep swinging." },
            new Def { id = "shield", name = "Bronze Mirror Shield", art = "mirror_shield", have = () => Story.Has("item_shield"),
                      about = "Hold the action button with nothing in front of you to raise it.|Blows from the front stop on it, and fire goes back where it came from." },
            new Def { id = "oil", name = "Night Oil", art = "night_oil", have = () => Story.Has("item_oil"),
                      about = "A sip before you nod off and your dreams last twice as long.|It is mostly fish oil." },
            new Def { id = "lamp", name = "Bronze Lamp", art = "bronze_lamp", have = () => Story.Has("item_lamp"),
                      about = "A second little flame to keep the Wakefire company.|One more flame of life." },
            new Def { id = "vessel", name = "Flame Vessels", art = "flame_vessel", have = () => Story.Count("vessels") > 0,
                      about = "Each one holds another flame of life." },
            new Def { id = "bigkey", name = "Bull Key", art = "big_key", have = () => Story.Has("bigkey"),
                      about = "Horned, heavy, and warm to the touch, as if something has been breathing on it." },
            new Def { id = "hillkey", name = "Key to the Hill", art = "hill_key", have = () => Story.Has("item_hillkey"),
                      about = "It opens the gate to the Hill of Sleepers.|Nobody has ever asked for it back." },
            new Def { id = "figs", name = "Old Belu's Figs", art = "figs", have = () => Story.Has("item_figs") && !Story.Has("figs_given"),
                      about = "Four hundred years late, for a widow in the Lower Town.|He would like her to know he is sorry about the wait." },
            new Def { id = "horn", name = "The Dawn Horn", art = "dawn_horn", have = () => Story.Has("item_horn"),
                      about = "The horn that wakes the sun.|It was buried with a king who did not want to get up." },
            new Def { id = "scrolls", name = "Scrolls", art = "scroll", have = () => Scrolls > 0,
                      about = "A plan of every place that had one to find. Inside that place, the map page shows it.|Somebody drew a goat on the crypt's. Nobody admits to the goat." },
        };

        static readonly string[] ScrollFlags = { "item_map_crypt", "item_map_zig", "item_map_barrow", "item_map_tomb" };

        /// <summary>How many places he has the plan of.</summary>
        public static int Scrolls
        {
            get
            {
                int n = 0;
                foreach (var f in ScrollFlags) if (Story.Has(f)) n++;
                return n;
            }
        }

        /// <summary>The id of what is on the item button.</summary>
        public static string Chosen = "wakefire";

        public static Def Find(string id)
        {
            foreach (var d in Usable) if (d.id == id) return d;
            foreach (var d in Kept) if (d.id == id) return d;
            return null;
        }

        /// <summary>What the item button does this moment: what was chosen, or the first thing he has that
        /// can go on it, or nothing at all (before the Wakefire is found).</summary>
        public static Def Current
        {
            get
            {
                var d = Find(Chosen);
                if (d != null && d.have() && Array.IndexOf(Usable, d) >= 0) return d;
                foreach (var u in Usable) if (u.have()) return u;
                return null;
            }
        }

        public static void Choose(string id)
        {
            var d = Find(id);
            if (d == null || !d.have() || Array.IndexOf(Usable, d) < 0) return;
            Chosen = d.id;
        }

        static readonly System.Collections.Generic.Dictionary<string, Sprite> sprites = new System.Collections.Generic.Dictionary<string, Sprite>();
        /// <summary>An item's picture as a sprite for the HUD (the same sixteen pixels the item page shows).</summary>
        public static Sprite Icon(Def d)
        {
            if (d == null) return null;
            string art = d.Art;
            if (sprites.TryGetValue(art, out var s) && s) return s;
            var t = Resources.Load<Texture2D>("Menu/" + art);
            if (!t) return null;
            t.filterMode = FilterMode.Point;
            s = Sprite.Create(t, new Rect(0, 0, t.width, t.height), new Vector2(0, 1), 1f);
            sprites[art] = s;
            return s;
        }
    }
}
