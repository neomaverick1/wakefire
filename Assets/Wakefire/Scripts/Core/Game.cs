// The game builds itself from code: the scene is empty, and this boots the pixel camera,
// the dream state and input, then starts play (or a test run on a build machine).
using System;
using UnityEngine;

namespace Wakefire
{
    public static class Boot
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.AfterSceneLoad)]
        static void Start()
        {
            if (Game.I) return;
            new GameObject("Game").AddComponent<Game>();
        }

        public static string Arg(string name)
        {
            var a = Environment.GetCommandLineArgs();
            for (int i = 0; i < a.Length - 1; i++) if (a[i] == name) return a[i + 1];
            return null;
        }

        public static bool Flag(string name) => Array.IndexOf(Environment.GetCommandLineArgs(), name) >= 0;
    }

    public partial class Game : MonoBehaviour
    {
        public static Game I;
        public static bool Paused;
        public PixelView View;
        public Dream Dream;

        void Awake()
        {
            I = this;
            DontDestroyOnLoad(gameObject);
            // the scene is empty, so nothing in it is listening: without this the whole game is silent
            if (!FindFirstObjectByType<AudioListener>()) gameObject.AddComponent<AudioListener>();
            Application.targetFrameRate = 60;
            QualitySettings.vSyncCount = 0;
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
            Controls.Init();
            Settings.Load();
            View = PixelView.Create();
            Dream = Dream.Create();
            Sky.Ensure();
            Pause.Ensure();
            Notices.Boot();
            TouchControls.Create();
            OnBoot();
        }

        partial void OnBoot();

        /// <summary>Load a map and put Azar at its spawn (or a named one).</summary>
        public Player EnterMap(string map, string spawn = null)
        {
            var m = Map.Load(map);
            var mk = (string.IsNullOrEmpty(spawn) ? null : m.Marker("spawn", spawn)) ?? m.Marker("spawn");
            var at = Map.ToWorld(mk.x, mk.y);
            var p = Player.I ? Player.I : Player.Spawn(at);
            p.pos = at;
            if (!string.IsNullOrEmpty(mk.text))
                p.Face(mk.text == "up" ? Facing.Up : mk.text == "left" ? Facing.Left : mk.text == "right" ? Facing.Right : Facing.Down);
            CurrentMap = map;
            CurrentSpawn = mk.who;
            Story.Set("seen_" + map);            // the world map shows where he has walked
            exitArmed = false;
            View.target = p.transform;
            View.bounds = m.bounds;
            View.SnapTo(at);
            if (!Hud.I) Hud.Create();
            Rooms.Setup(m, at);
            Populate(m);
            Mech.Setup(m);
            Smoke.Setup(m);
            Pocket.Setup(m);
            Board.Setup(m);
            Story.Ensure().Setup(map, m);
            Music.Play(m.data.music);
            return p;
        }

        partial void StartGame()
        {
            Title.Show();
        }

        /// <summary>A fresh game or the saved one of the journey in play.</summary>
        public void Begin(bool resume) => Begin(resume ? Save.Read() : null);

        /// <summary>Start from a save, or from the beginning with none.</summary>
        public void Begin(SaveData d)
        {
            Story.Abort();
            Story.ResetAll();
            Items.Chosen = d != null && !string.IsNullOrEmpty(d.item) ? d.item : "wakefire";
            if (d == null) Story.Set("prequel");
            if (d != null)
            {
                foreach (var f in d.flags) Story.Set(f);
                // a journey from before the first night was told: he has plainly been through it
                if (!Story.Has("prequel"))
                    foreach (var f in new[] { "prequel", "prequel_done", "item_sword", "item_wakefire", "chest_crypt_sword", "chest_crypt_fire", "dead_crypt_mother", "door_crypt_door", "chest_crypt_key" }) Story.Set(f);
                // a journey that already carries the mirror shield took it from a plain chest: nobody was keeping it then
                if (Story.Has("item_shield")) Story.Set("dead_z2_herdsman");
                for (int i = 0; i < d.countKeys.Length; i++) Story.SetCount(d.countKeys[i], d.countVals[i]);
                Save.PlayTime = d.playTime;
                // a journey from before the world map was drawn: he has plainly walked the places his story has been through
                bool any = false;
                foreach (var f in d.flags) if (f.StartsWith("seen_")) { any = true; break; }
                if (!any)
                {
                    foreach (var m in new[] { "ashkel", "lowtown" }) Story.Set("seen_" + m);
                    if (d.flags.Length > 6) foreach (var m in new[] { "terraces", "cliffs" }) Story.Set("seen_" + m);
                    if (Story.Has("gate_open")) Story.Set("seen_temple_yard");
                    if (Story.Has("met_namtar")) Story.Set("seen_necro_road");
                    if (Story.Has("king_door") || Story.Has("name_tar") || Story.Has("name_ash")) Story.Set("seen_necropolis");
                }
            }
            var p = EnterMap(d != null ? d.map : "ashkel", d != null ? d.spawn : null);
            if (d != null) { p.coins = d.coins; p.keys = d.keys; p.health.max = Mathf.Max(6, d.maxHp); }
            else { p.coins = 0; p.keys = 0; Save.PlayTime = 0; }          // a new game starts with empty pockets
            Story.I.ApplyItems();
            p.health.hp = p.health.max;
            p.health.invulnerable = 0;
            p.SetState(Player.State.Free, "idle");
            if (Dream.I.Dreaming) Dream.I.SetInstant(false);
            if (d == null) Story.Run(Story.I.Prologue());
            else Notices.Place(CurrentMap);
        }
    }
}
