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
#if UNITY_WEBGL && !UNITY_EDITOR
            Application.targetFrameRate = -1;      // the browser paces frames to the display
#else
            Application.targetFrameRate = 60;
            QualitySettings.vSyncCount = 0;
#endif
            Screen.sleepTimeout = SleepTimeout.NeverSleep;
            Controls.Init();
            Settings.Load();
            View = PixelView.Create();
            Dream = Dream.Create();
            Pause.Ensure();
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
            exitArmed = false;
            View.target = p.transform;
            View.bounds = m.bounds;
            View.SnapTo(at);
            if (!Hud.I) Hud.Create();
            Populate(m);
            Story.Ensure().Setup(map, m);
            Music.Play(m.data.music);
            return p;
        }

        partial void StartGame()
        {
            Title.Show();
        }

        /// <summary>A fresh game or the saved one, from the title screen.</summary>
        public void Begin(bool resume)
        {
            var d = resume ? Save.Read() : null;
            Story.Abort();
            Story.ResetAll();
            if (d != null)
            {
                foreach (var f in d.flags) Story.Set(f);
                for (int i = 0; i < d.countKeys.Length; i++) Story.SetCount(d.countKeys[i], d.countVals[i]);
                Save.PlayTime = d.playTime;
            }
            var p = EnterMap(d != null ? d.map : "ashkel", d != null ? d.spawn : null);
            if (d != null) { p.coins = d.coins; p.keys = d.keys; p.health.max = Mathf.Max(6, d.maxHp); }
            else { p.coins = 0; p.keys = 0; Save.PlayTime = 0; }          // a new game starts with empty pockets
            Story.I.ApplyItems();
            p.health.hp = p.health.max;
            p.SetState(Player.State.Free, "idle");
            if (Dream.I.Dreaming) Dream.I.SetInstant(false);
            if (d == null) Story.Run(Story.I.Intro());
        }
    }
}
