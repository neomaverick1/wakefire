// How one of the three journeys is drawn wherever they are listed (the title, the save page of the
// pause screen, the screen after a fall): its number on a bronze boss, where it has got to, which
// chapter, how long it has been played and how many flames of life Azar has in it.
using UnityEngine;

namespace Wakefire
{
    public static class SlotRow
    {
        public const int Tall = 29, Short = 16;
        static readonly Color32 Frame = new Color32(10, 6, 16, 255), Bronze = new Color32(188, 122, 52, 255), BronzeL = new Color32(255, 216, 138, 255),
            BronzeD = new Color32(106, 58, 24, 255), Fill = new Color32(16, 13, 30, 255), FillOn = new Color32(38, 30, 62, 255), Gold = new Color32(246, 200, 90, 255),
            Ink = new Color32(244, 234, 216, 255), Dim = new Color32(150, 140, 170, 255), Faint = new Color32(98, 90, 118, 255), Sh = new Color32(6, 4, 12, 255),
            Red = new Color32(226, 84, 60, 255);

        /// <summary>One journey as a plate w wide with its top left at (x, y). short rows are one line (the title).</summary>
        public static void Draw(PixelCanvas cv, int x, int y, int w, int slot, bool sel, bool inPlay, float clock, bool compact = false, bool danger = false)
        {
            var f = PixelFont.Main;
            int h = compact ? Short : Tall;
            var d = Save.Read(slot);
            var edge = danger ? Red : sel ? Gold : BronzeD;
            cv.Rect(x, y, w, h, Frame);
            cv.Rect(x + 1, y + 1, w - 2, h - 2, edge);
            cv.Rect(x + 2, y + 2, w - 4, h - 4, sel ? FillOn : Fill);
            if (sel && !danger) { cv.HLine(x + 1, y + 1, w - 2, BronzeL); cv.VLine(x + 1, y + 1, h - 2, BronzeL); }
            // the number, on a boss
            int bx = x + (compact ? 4 : 5), by = y + (compact ? 3 : 8), bs = compact ? 10 : 13;
            cv.Rect(bx + 1, by, bs - 2, bs, Bronze); cv.Rect(bx, by + 1, bs, bs - 2, Bronze);
            cv.HLine(bx + 1, by, bs - 2, BronzeL); cv.VLine(bx, by + 1, bs - 2, BronzeL);
            cv.HLine(bx + 1, by + bs - 1, bs - 2, BronzeD); cv.VLine(bx + bs - 1, by + 1, bs - 2, BronzeD);
            string num = (slot + 1).ToString();
            f.DrawString(cv, bx + (bs - f.Measure(num)) / 2 + 1, by + (bs - 9) / 2, num, Frame);
            int tx = bx + bs + 6;
            if (d == null)
            {
                f.DrawString(cv, tx, y + (h - 9) / 2, compact ? "Begin a new journey" : "Empty", sel ? Ink : Faint, Sh);
                return;
            }
            string place = Places.Name(d.map), time = Save.Clock(d.playTime);
            if (compact)
            {
                f.DrawString(cv, tx, y + 4, place, sel ? Gold : Ink, Sh);
                f.DrawString(cv, x + w - 6 - f.Measure(time), y + 4, time, sel ? Ink : Dim, Sh);
                return;
            }
            f.DrawString(cv, tx, y + 4, place, sel ? Gold : Ink, Sh);
            string sub = Save.Chapter(d, false) + ", " + time;
            f.DrawString(cv, tx, y + 16, sub, Dim, Sh);
            // his flames, right-hand side
            var full = Pic.Get("life_full");
            int n = Mathf.Max(3, d.maxHp / 2);
            int step = n > 6 ? 8 : 10;
            int fx = x + w - 8 - n * step;
            for (int i = 0; i < n; i++) cv.Blit(full, fx + i * step, y + 13);
            if (inPlay)
            {
                string tag = "in play";
                f.DrawString(cv, x + w - 7 - f.Measure(tag), y + 3, tag, Gold, Sh);
            }
        }
    }
}
