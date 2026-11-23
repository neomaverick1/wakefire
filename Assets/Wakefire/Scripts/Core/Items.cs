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
        }

        /// <summary>The ones that go on the item button, in the order the item page shows them.</summary>
        public static readonly Def[] Usable =
        {
            new Def { id = "wakefire", name = "The Wakefire", art = "wakefire", have = () => true,
                      about = "The watch-flame of Ashkel, the last thing in the city still awake.|Hold it out to light what ought to be lit." },
            new Def { id = "sling", name = "Herdsman's Sling", art = "sling", have = () => Story.Has("item_sling"),
                      about = "A strip of leather and a good eye.|It throws a stone straight ahead: at gongs, at jars, at anything that has it coming." },
            new Def { id = "stick", name = "Huntsman's Throwing Stick", art = "throwing_stick", have = () => Story.Has("item_stick"),
                      about = "Curved cedar with gold at both ends.|It flies out, hits what it meets, and comes back, bringing small things with it." },
        };

        /// <summary>Everything else worth showing.</summary>
        public static readonly Def[] Kept =
        {
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
            new Def { id = "map_zig", name = "Scroll of the Ziggurat", art = "scroll", have = () => Story.Has("item_map_zig"),
                      about = "The builders' own drawing of the ziggurat, floor by floor." },
            new Def { id = "map_tomb", name = "Scroll of the King's Tomb", art = "scroll", have = () => Story.Has("item_map_tomb"),
                      about = "The tomb as its architect drew it, and as he was told to forget it." },
        };

        /// <summary>The id of what is on the item button.</summary>
        public static string Chosen = "wakefire";

        public static Def Find(string id)
        {
            foreach (var d in Usable) if (d.id == id) return d;
            foreach (var d in Kept) if (d.id == id) return d;
            return null;
        }

        /// <summary>What the item button does this moment (the Wakefire, if whatever was chosen is gone).</summary>
        public static Def Current
        {
            get
            {
                var d = Find(Chosen);
                return d != null && d.have() && Array.IndexOf(Usable, d) >= 0 ? d : Usable[0];
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
            if (sprites.TryGetValue(d.art, out var s) && s) return s;
            var t = Resources.Load<Texture2D>("Menu/" + d.art);
            if (!t) return null;
            t.filterMode = FilterMode.Point;
            s = Sprite.Create(t, new Rect(0, 0, t.width, t.height), new Vector2(0, 1), 1f);
            sprites[d.art] = s;
            return s;
        }
    }
}
