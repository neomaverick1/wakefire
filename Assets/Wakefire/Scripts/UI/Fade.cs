// Screen fades done the pixel way: an ordered-dither curtain of night that closes over the
// picture in sixteen steps, with an optional line of text in the middle.
using System.Collections;
using UnityEngine;
using UnityEngine.UI;

namespace Wakefire
{
    public class Fade : MonoBehaviour
    {
        static Fade I;
        RawImage img;
        PixelCanvas cv;
        int level = -1;
        string caption;
        static readonly int[] Bayer = { 0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5 };
        static readonly Color32 Night = new Color32(6, 4, 12, 255), Clear = new Color32(0, 0, 0, 0);
        public static float Amount { get; private set; }

        static Fade Ensure()
        {
            if (I && I.cv != null && I.cv.W == PixelView.I.width) return I;
            if (!I)
            {
                var go = new GameObject("Fade", typeof(RectTransform));
                go.layer = PixelView.PixelUILayer;
                go.transform.SetParent(PixelView.I.pixelRoot, false);
                PixelView.Stretch((RectTransform)go.transform);
                I = go.AddComponent<Fade>();
                I.img = go.AddComponent<RawImage>();
                I.img.raycastTarget = false;
            }
            I.cv = new PixelCanvas(PixelView.I.width, PixelView.Height);
            I.img.texture = I.cv.tex;
            I.level = -1;
            return I;
        }

        void LateUpdate() => transform.SetAsLastSibling();

        public static void Set(float a, string text = null)
        {
            var f = Ensure();
            Amount = a;
            int lv = Mathf.Clamp(Mathf.RoundToInt(a * 16), 0, 16);
            if (lv == f.level && text == f.caption) return;
            f.level = lv;
            f.caption = text;
            f.img.enabled = lv > 0;
            if (lv == 0) return;
            var c = f.cv;
            for (int y = 0; y < c.H; y++)
                for (int x = 0; x < c.W; x++)
                    c.Set(x, y, Bayer[(y & 3) * 4 + (x & 3)] < lv ? Night : Clear);
            if (!string.IsNullOrEmpty(text) && lv >= 16)
            {
                var font = PixelFont.Main;
                var lines = text.Split('\n');
                int y = c.H / 2 - lines.Length * font.Line / 2;
                foreach (var l in lines)
                {
                    int w = font.Measure(l);
                    font.DrawString(c, (c.W - w) / 2, y, l, new Color32(244, 234, 216, 255));
                    y += font.Line + 2;
                }
            }
            c.Apply();
        }

        public static IEnumerator Out(float seconds, string text = null)
        {
            for (float t = 0; t < seconds; t += Time.unscaledDeltaTime) { Set(t / seconds); yield return null; }
            Set(1, text);
        }

        public static IEnumerator In(float seconds)
        {
            for (float t = 0; t < seconds; t += Time.unscaledDeltaTime) { Set(1 - t / seconds); yield return null; }
            Set(0);
        }
    }
}
