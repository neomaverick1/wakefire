// The pause menu: the world stops, a bronze-framed panel offers to carry on or to go back to
// the title (the game saves every time Azar enters a new place, so nothing is lost).
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Wakefire
{
    public class Pause : MonoBehaviour
    {
        static Pause I;
        RawImage img;
        PixelCanvas cv;
        int sel;
        float clock;
        static readonly string[] Options = { "Carry on", "Back to the title" };

        void Update()
        {
            if (Title.I) return;
            if (!Game.Paused)
            {
                if (Controls.Down(Controls.Pause) && Player.I && !Game.Busy && !(Story.I && Story.I.Running)) Open();
                return;
            }
            clock += Time.unscaledDeltaTime;
            var mv = Controls.MoveVector;
            if (Controls.Move.WasPerformedThisFrame() && Mathf.Abs(mv.y) > 0.5f) { sel = 1 - sel; Sfx.Play("menu_move", 0.5f, 0); }
            var tp = Pointer.current;
            if (tp != null && tp.press.wasPressedThisFrame)
            {
                var pos = tp.position.ReadValue();
                float py = PixelView.Height - pos.y / PixelView.I.ScreenScale;
                for (int i = 0; i < 2; i++) if (Mathf.Abs(py - (PixelView.Height / 2 - 4 + i * 14)) < 7) { sel = i; Choose(); return; }
            }
            Draw();
            if (Controls.Down(Controls.Pause) || Controls.Down(Controls.Back)) { Close(); return; }
            if (Controls.Down(Controls.Confirm) || Controls.Down(Controls.Interact)) Choose();
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
            sel = 0;
            cv = new PixelCanvas(PixelView.I.width, PixelView.Height);
            img.texture = cv.tex;
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

        void Choose()
        {
            Sfx.Play("menu_ok", 0.7f, 0);
            if (sel == 0) { Close(); return; }
            Close();
            if (Game.I.CurrentMap != null) Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn);
            Title.Show();
        }

        void Draw()
        {
            var f = PixelFont.Main;
            int W = cv.W, H = cv.H;
            var veil = new Color32(6, 4, 12, 150);
            cv.Clear(veil);
            int bw = 150, bh = 62, bx = (W - bw) / 2, by = H / 2 - 30;
            cv.Rect(bx, by, bw, bh, new Color32(10, 6, 16, 255));
            cv.Rect(bx + 1, by + 1, bw - 2, bh - 2, new Color32(188, 122, 52, 255));
            cv.HLine(bx + 1, by + 1, bw - 2, new Color32(255, 216, 138, 255));
            cv.Rect(bx + 3, by + 3, bw - 6, bh - 6, new Color32(10, 6, 16, 255));
            cv.Rect(bx + 4, by + 4, bw - 8, bh - 8, new Color32(22, 18, 40, 255));
            var gold = new Color32(246, 200, 90, 255);
            var ink = new Color32(244, 234, 216, 255);
            var sh = new Color32(6, 4, 12, 255);
            string t = "Rest a moment";
            f.DrawString(cv, (W - f.Measure(t)) / 2, by + 8, t, new Color32(150, 140, 170, 255), sh);
            for (int i = 0; i < 2; i++)
            {
                string s = Options[i];
                int x = (W - f.Measure(s)) / 2, y = H / 2 - 8 + i * 14;
                f.DrawString(cv, x, y, s, i == sel ? gold : ink, sh);
                if (i == sel && ((int)(clock * 3f)) % 2 == 0) f.Draw(cv, x - 10, y, '>', gold, sh);
            }
            cv.Apply();
        }
    }
}
