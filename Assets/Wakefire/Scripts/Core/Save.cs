// Two saves, kept in the device's preferences. The first the game writes by itself whenever Azar
// walks into a new place or picks up something that matters ("Continue" on the title). The second
// is the player's own, written from the pause menu and brought back with Load. Each holds where
// Azar is, what he carries, and every story flag and counter.
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
    }

    public static class Save
    {
        const string AutoKey = "wakefire_save_1", ManualKey = "wakefire_save_2";
        public static float PlayTime;
        /// <summary>Raised when the game saves by itself, so the screen can say so.</summary>
        public static event Action Saved;

        public static bool Exists => PlayerPrefs.HasKey(AutoKey);
        public static bool HasManual => PlayerPrefs.HasKey(ManualKey);

        static SaveData Snapshot(string map, string spawn)
        {
            var p = Player.I;
            if (!p) return null;
            var d = new SaveData
            {
                map = map, spawn = spawn, coins = p.coins, keys = p.keys, maxHp = p.health.max,
                flags = new List<string>(Story.Flags).ToArray(), playTime = PlayTime,
            };
            var keys = new List<string>(); var vals = new List<int>();
            foreach (var kv in Story.Counts) { keys.Add(kv.Key); vals.Add(kv.Value); }
            d.countKeys = keys.ToArray(); d.countVals = vals.ToArray();
            return d;
        }

        static bool Put(string key, SaveData d)
        {
            if (d == null) return false;
            PlayerPrefs.SetString(key, JsonUtility.ToJson(d));
            PlayerPrefs.Save();
            return true;
        }

        /// <summary>The game's own save.</summary>
        public static void Write(string map, string spawn, bool quiet = false)
        {
            if (Put(AutoKey, Snapshot(map, spawn)) && !quiet) Saved?.Invoke();
        }

        /// <summary>The player's save, from the pause menu: everything as it is now, waking at the way into this place.</summary>
        public static bool WriteManual()
        {
            var g = Game.I;
            if (!g || g.CurrentMap == null) return false;
            var d = Snapshot(g.CurrentMap, g.CurrentSpawn);
            return Put(ManualKey, d) && Put(AutoKey, d);
        }

        static SaveData Get(string key)
        {
            if (!PlayerPrefs.HasKey(key)) return null;
            try { return JsonUtility.FromJson<SaveData>(PlayerPrefs.GetString(key)); }
            catch (Exception) { return null; }
        }

        public static SaveData Read() => Get(AutoKey);
        public static SaveData ReadManual() => Get(ManualKey);

        /// <summary>A new journey: the game's own save goes. The player's stays until they save over it.</summary>
        public static void Clear()
        {
            PlayerPrefs.DeleteKey(AutoKey);
            PlayerPrefs.Save();
        }

        public static void ClearAll()
        {
            PlayerPrefs.DeleteKey(AutoKey); PlayerPrefs.DeleteKey(ManualKey);
            PlayerPrefs.Save();
        }

        /// <summary>"The Lower Town, 0:42": where a save is and how long had been played.</summary>
        public static string Describe(SaveData d) => d == null ? "" : Places.Name(d.map) + ", " + Clock(d.playTime);

        public static string Clock(float seconds)
        {
            int m = Mathf.FloorToInt(seconds / 60f);
            return m >= 60 ? $"{m / 60}h {m % 60:00}m" : $"{m}:{Mathf.FloorToInt(seconds) % 60:00}";
        }
    }
}
