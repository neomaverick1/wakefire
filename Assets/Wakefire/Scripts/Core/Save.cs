// Three journeys, kept in the device's preferences. Each holds where Azar is, what he carries, and
// every story flag and counter. One of the three is the journey in play: the game writes to it by
// itself whenever Azar walks into a new place or picks up something that matters, and the player
// can write to it (or copy the journey into another of the three) from the save page of the pause
// screen. The title screen is where a journey is picked, begun, or rubbed out.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    [Serializable] public class SaveData
    {
        public string map, spawn;
        public int coins, keys, maxHp;
        public string[] flags;
        public string[] countKeys;
        public int[] countVals;
        public float playTime;
        public string item;                 // what is on the item button

        public bool Has(string flag) => flags != null && Array.IndexOf(flags, flag) >= 0;
    }

    public static class Save
    {
        public const int Slots = 3;
        const string LastKey = "wakefire_file_last", OldAuto = "wakefire_save_1", OldManual = "wakefire_save_2";
        static string Key(int slot) => "wakefire_file_" + (slot + 1);

        public static float PlayTime;
        /// <summary>Raised when the game saves by itself, so the screen can say so.</summary>
        public static event Action Saved;

        static int slot = -1;
        /// <summary>The journey in play (0, 1 or 2).</summary>
        public static int Slot
        {
            get { if (slot < 0) { Migrate(); slot = Mathf.Clamp(PlayerPrefs.GetInt(LastKey, 0), 0, Slots - 1); } return slot; }
        }

        /// <summary>From here on this is the journey in play.</summary>
        public static void Use(int s)
        {
            Migrate();
            slot = Mathf.Clamp(s, 0, Slots - 1);
            PlayerPrefs.SetInt(LastKey, slot);
            PlayerPrefs.Save();
        }

        /// <summary>Forget what has been read from the device, so the next question goes back to it (test runs).</summary>
        public static void Reread() { migrated = false; slot = -1; }

        static bool migrated;
        /// <summary>Saves from before there were three: the game's own save becomes the first journey,
        /// and the player's own, if it was kept at a different moment, the second.</summary>
        static void Migrate()
        {
            if (migrated) return;
            migrated = true;
            bool any = false;
            for (int i = 0; i < Slots; i++) any |= PlayerPrefs.HasKey(Key(i));
            if (!any)
            {
                string a = PlayerPrefs.GetString(OldAuto, ""), m = PlayerPrefs.GetString(OldManual, "");
                if (a == "" && m != "") { a = m; m = ""; }
                if (a != "") PlayerPrefs.SetString(Key(0), a);
                if (m != "" && m != a) PlayerPrefs.SetString(Key(1), m);
            }
            if (PlayerPrefs.HasKey(OldAuto) || PlayerPrefs.HasKey(OldManual))
            {
                PlayerPrefs.DeleteKey(OldAuto); PlayerPrefs.DeleteKey(OldManual);
                PlayerPrefs.Save();
            }
        }

        public static bool Has(int s) { Migrate(); return PlayerPrefs.HasKey(Key(s)); }
        public static bool Any { get { for (int i = 0; i < Slots; i++) if (Has(i)) return true; return false; } }
        /// <summary>The journey in play has been saved at least once.</summary>
        public static bool Exists => Has(Slot);

        static SaveData Snapshot(string map, string spawn)
        {
            var p = Player.I;
            if (!p) return null;
            var d = new SaveData
            {
                map = map, spawn = spawn, coins = p.coins, keys = p.keys, maxHp = p.health.max,
                flags = new List<string>(Story.Flags).ToArray(), playTime = PlayTime, item = Items.Chosen,
            };
            var keys = new List<string>(); var vals = new List<int>();
            foreach (var kv in Story.Counts) { keys.Add(kv.Key); vals.Add(kv.Value); }
            d.countKeys = keys.ToArray(); d.countVals = vals.ToArray();
            return d;
        }

        static bool Put(int s, SaveData d)
        {
            if (d == null) return false;
            Migrate();
            PlayerPrefs.SetString(Key(s), JsonUtility.ToJson(d));
            PlayerPrefs.Save();
            return true;
        }

        /// <summary>The game's own save, into the journey in play.</summary>
        public static void Write(string map, string spawn, bool quiet = false)
        {
            if (Put(Slot, Snapshot(map, spawn)) && !quiet) Saved?.Invoke();
        }

        /// <summary>The player's save, from the pause screen: everything as it is now, waking at the way
        /// into this place. Into the journey in play it is simply "save now"; into one of the other two
        /// it leaves a copy there to come back to, and play goes on in the one it was in.</summary>
        public static bool WriteTo(int s)
        {
            var g = Game.I;
            if (!g || g.CurrentMap == null) return false;
            return Put(s, Snapshot(g.CurrentMap, g.CurrentSpawn));
        }

        public static SaveData Read(int s)
        {
            if (!Has(s)) return null;
            try { return JsonUtility.FromJson<SaveData>(PlayerPrefs.GetString(Key(s))); }
            catch (Exception) { return null; }
        }

        public static SaveData Read() => Read(Slot);

        public static void Erase(int s)
        {
            Migrate();
            PlayerPrefs.DeleteKey(Key(s));
            PlayerPrefs.Save();
        }

        /// <summary>A new journey in the slot in play: whatever was there goes.</summary>
        public static void Clear() => Erase(Slot);

        public static void ClearAll()
        {
            for (int i = 0; i < Slots; i++) Erase(i);
        }

        /// <summary>"The Lower Town, 0:42": where a save is and how long had been played.</summary>
        public static string Describe(SaveData d) => d == null ? "" : Places.Name(d.map) + ", " + Clock(d.playTime);

        /// <summary>Which chapter a journey has got to.</summary>
        public static string Chapter(SaveData d, bool full = true)
        {
            bool two = d != null && d.Has("ch2");
            if (!full) return two ? "Chapter Two" : "Chapter One";
            return two ? "Chapter Two: The Sleepless Dead" : "Chapter One: The Sleeping God";
        }

        public static string Clock(float seconds)
        {
            int m = Mathf.FloorToInt(seconds / 60f);
            return m >= 60 ? $"{m / 60}h {m % 60:00}m" : $"{m}:{Mathf.FloorToInt(seconds) % 60:00}";
        }
    }
}
