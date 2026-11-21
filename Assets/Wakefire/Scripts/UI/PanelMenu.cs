// A bronze-framed panel with a short list to choose from: the pause menu and the screen after a
// fall are both one of these. Stick or arrows move, a button confirms, a tap on a line picks it.
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Wakefire
{
    public class PanelMenu
    {
        public readonly PixelCanvas cv;
        public string title, footer;
        public string[] options;
        public bool[] off;              // lines that can't be chosen right now
        public int sel;
        public float clock;
        public int width = 196;
        public const int Row = 15;
        int bx, by, bw, bh, y0;
        static readonly Color32 Frame = new Color32(10, 6, 16, 255), Bronze = new Color32(188, 122, 52, 255), BronzeL = new Color32(255, 216, 138, 255),
            BronzeD = new Color32(106, 58, 24, 255), Fill = new Color32(22, 18, 40, 255), Fill2 = new Color32(29, 24, 52, 255), Gold = new Color32(246, 200, 90, 255),
            Ink = new Color32(244, 234, 216, 255), Dim = new Color32(150, 140, 170, 255), Faint = new Color32(92, 84, 110, 255), Sh = new Color32(6, 4, 12, 255);

        public PanelMenu(RawImage img)
        {
            cv = new PixelCanvas(PixelView.I.width, PixelView.Height);
            img.texture = cv.tex;
        }

        void Layout()
        {
            int n = options.Length;
            bw = Mathf.Min(width, cv.W - 16);
            bh = 26 + n * Row + (string.IsNullOrEmpty(footer) ? 4 : 20);
            bx = (cv.W - bw) / 2; by = Mathf.Max(4, (cv.H - bh) / 2);
            y0 = by + 24;
        }

        bool Can(int i) => off == null || i >= off.Length || !off[i];

        /// <summary>Test runs choose a line through here.</summary>
        public static int FakePick = -1;

        /// <summary>Reads the controls. Returns the line chosen this frame, or -1.</summary>
        public int Poll()
        {
            Layout();
            clock += Time.unscaledDeltaTime;
            int n = options.Length;
            if (FakePick >= 0) { int fp = FakePick; FakePick = -1; if (fp < n && Can(fp)) { sel = fp; return fp; } return -1; }
            var mv = Controls.MoveVector;
            if (Controls.Move.WasPerformedThisFrame() && Mathf.Abs(mv.y) > 0.5f)
            {
                int step = mv.y < 0 ? 1 : n - 1;
                for (int k = 0; k < n; k++) { sel = (sel + step) % n; if (Can(sel)) break; }
                Sfx.Play("menu_move", 0.5f, 0);
            }
            var tp = Pointer.current;
            if (tp != null && tp.press.wasPressedThisFrame)
            {
                var pos = tp.position.ReadValue();
                float k = PixelView.I.ScreenScale;
                float px = pos.x / k, py = PixelView.Height - pos.y / k;
                if (px >= bx && px < bx + bw)
                    for (int i = 0; i < n; i++)
                        if (py >= y0 + i * Row - 3 && py < y0 + (i + 1) * Row - 3)
                        {
                            if (!Can(i)) { Sfx.Play("deny", 0.6f, 0); return -1; }
                            sel = i;
                            return i;
                        }
                return -1;          // a tap that lands on nothing chooses nothing
            }
            if (Controls.Down(Controls.Confirm) || Controls.Down(Controls.Interact)) return Can(sel) ? sel : -1;
            return -1;
        }

        public void Draw(Color32 veil)
        {
            Layout();
            var f = PixelFont.Main;
            cv.Clear(veil);
            cv.Rect(bx, by, bw, bh, Frame);
            cv.Rect(bx + 1, by + 1, bw - 2, bh - 2, Bronze);
            cv.HLine(bx + 1, by + 1, bw - 2, BronzeL);
            cv.VLine(bx + 1, by + 1, bh - 2, BronzeL);
            cv.HLine(bx + 1, by + bh - 2, bw - 2, BronzeD);
            cv.VLine(bx + bw - 2, by + 1, bh - 2, BronzeD);
            cv.Rect(bx + 3, by + 3, bw - 6, bh - 6, Frame);
            cv.Rect(bx + 4, by + 4, bw - 8, bh - 8, Fill);
            for (int y = by + 4; y < by + 4 + 14; y++)
                for (int x = bx + 4; x < bx + bw - 4; x++)
                    if (((x + y) & 1) == 0 && y < by + 18 - ((x >> 1) & 1)) cv.Set(x, y, Fill2);
            foreach (var (cx, cy) in new[] { (bx + 5, by + 5), (bx + bw - 7, by + 5), (bx + 5, by + bh - 7), (bx + bw - 7, by + bh - 7) })
            {
                cv.Set(cx, cy, BronzeL); cv.Set(cx + 1, cy, Bronze); cv.Set(cx, cy + 1, Bronze); cv.Set(cx + 1, cy + 1, BronzeD);
            }
            f.DrawString(cv, (cv.W - f.Measure(title)) / 2, by + 8, title, Dim, Sh);
            cv.HLine(bx + 14, by + 20, bw - 28, BronzeD);
            for (int i = 0; i < options.Length; i++)
            {
                string s = options[i];
                int x = (cv.W - f.Measure(s)) / 2, y = y0 + i * Row;
                bool on = i == sel;
                f.DrawString(cv, x, y, s, !Can(i) ? Faint : on ? Gold : Ink, Sh);
                if (on && Can(i) && ((int)(clock * 3f)) % 2 == 0)
                {
                    f.Draw(cv, x - 10, y, '>', Gold, Sh);
                    f.Draw(cv, x + f.Measure(s) + 5, y, '<', Gold, Sh);
                }
            }
            if (!string.IsNullOrEmpty(footer))
            {
                int fy = y0 + options.Length * Row + 2;
                cv.HLine(bx + 14, fy - 3, bw - 28, BronzeD);
                f.DrawString(cv, (cv.W - f.Measure(footer)) / 2, fy + 2, footer, Dim, Sh);
            }
            cv.Apply();
        }
    }
}
