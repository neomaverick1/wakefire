// One save slot, kept in the device's preferences: where Azar is, what he carries, and every
// story flag and counter. Written whenever he walks into a new place.
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
        const string Key = "wakefire_save_1";
        public static float PlayTime;

        public static bool Exists => PlayerPrefs.HasKey(Key);

        public static void Write(string map, string spawn)
        {
            var p = Player.I;
            if (!p) return;
            var d = new SaveData
            {
                map = map, spawn = spawn, coins = p.coins, keys = p.keys, maxHp = p.health.max,
                flags = new List<string>(Story.Flags).ToArray(), playTime = PlayTime,
            };
            var keys = new List<string>(); var vals = new List<int>();
            foreach (var kv in Story.Counts) { keys.Add(kv.Key); vals.Add(kv.Value); }
            d.countKeys = keys.ToArray(); d.countVals = vals.ToArray();
            PlayerPrefs.SetString(Key, JsonUtility.ToJson(d));
            PlayerPrefs.Save();
        }

        public static SaveData Read()
        {
            if (!Exists) return null;
            try { return JsonUtility.FromJson<SaveData>(PlayerPrefs.GetString(Key)); }
            catch (Exception) { return null; }
        }

        public static void Clear()
        {
            PlayerPrefs.DeleteKey(Key);
            PlayerPrefs.Save();
        }
    }
}
