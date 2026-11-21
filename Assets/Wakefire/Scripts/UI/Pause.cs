// The pause menu: the world stops, a bronze-framed panel offers to carry on, to save or load the
// player's own save, to switch the music or the sounds off, or to go back to the title (the game
// also saves by itself every time Azar enters a new place, so nothing is lost).
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Wakefire
{
    public class Pause : MonoBehaviour
    {
        static Pause I;
        RawImage img;
        PanelMenu menu;
        string said;                // what the last choice did, shown under the list
        bool sure;                  // Load asked once already
        const int CarryOn = 0, SaveIt = 1, LoadIt = 2, MusicLine = 3, SoundLine = 4, ToTitle = 5;

        string[] Options() => new[]
        {
            "Carry on", "Save", sure ? "Load: sure?" : "Load",
            "Music: " + (Settings.MusicOn ? "on" : "off"), "Sounds: " + (Settings.SoundOn ? "on" : "off"), "Back to the title",
        };

        string Footer()
        {
            if (said != null) return said;
            switch (menu.sel)
            {
                case SaveIt: return "Keeps this moment for Load.";
                case LoadIt: return Save.HasManual ? Save.Describe(Save.ReadManual()) : "Nothing saved yet.";
                case ToTitle: return "The game saves as you go.";
                default: return Places.Name(Game.I.CurrentMap) + ", " + Save.Clock(Save.PlayTime);
            }
        }

        void Update()
        {
            if (Title.I) return;
            if (!Game.Paused)
            {
                if (Controls.Down(Controls.Pause) && Player.I && !Game.Busy && !(Story.I && Story.I.Running)) Open();
                return;
            }
            int before = menu.sel;
            menu.options = Options();
            menu.off = new[] { false, false, !Save.HasManual, false, false, false };
            int pick = menu.Poll();
            if (menu.sel != before) { said = null; sure = false; }
            menu.footer = Footer();
            menu.options = Options();
            menu.Draw(new Color32(6, 4, 12, 150));
            if (pick >= 0) { Choose(pick); return; }
            if (Controls.Down(Controls.Pause) || Controls.Down(Controls.Back)) Close();
        }

        public static void Ensure()
        {
            if (I) return;
            var go = new GameObject("Pause", typeof(RectTransform));
            go.layer = PixelView.PixelUILayer;
            go.transform.SetParent(PixelView.I.pixelRoot, false);
            PixelView.Stretch((RectTransform)go.transform);
            I = go.AddComponent<Pause>();
            I.img = go.AddComponent<RawImage>();
            I.img.raycastTarget = false;
            I.img.enabled = false;
        }

        void Open()
        {
            Game.Paused = true;
            Time.timeScale = 0;
            if (menu == null || menu.cv.W != PixelView.I.width || menu.cv.H != PixelView.Height) menu = new PanelMenu(img) { title = "Rest a moment" };
            menu.sel = 0; said = null; sure = false;
            menu.options = Options();
            menu.footer = Footer();
            menu.Draw(new Color32(6, 4, 12, 150));
            img.enabled = true;
            Sfx.Play("menu_ok", 0.6f, 0);
            AudioListener.volume = 0.5f;
        }

        void Close()
        {
            Game.Paused = false;
            Time.timeScale = 1;
            img.enabled = false;
            AudioListener.volume = 1f;
        }

        void Choose(int pick)
        {
            Sfx.Play("menu_ok", 0.7f, 0);
            switch (pick)
            {
                case CarryOn: Close(); return;
                case SaveIt:
                    said = Save.WriteManual() ? "Saved: " + Save.Describe(Save.ReadManual()) : "Can't save here.";
                    sure = false;
                    return;
                case LoadIt:
                    if (!sure) { sure = true; said = "Go back to " + Save.Describe(Save.ReadManual()) + "?"; return; }
                    Close();
                    Game.I.LoadGame(Save.ReadManual());
                    return;
                case MusicLine: Settings.Toggle(true); return;
                case SoundLine: Settings.Toggle(false); return;
                default:
                    Close();
                    if (Game.I.CurrentMap != null) Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn, quiet: true);
                    Title.Show();
                    return;
            }
        }
    }
}
