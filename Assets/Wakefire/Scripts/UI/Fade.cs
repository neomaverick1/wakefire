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
            if (I && I.cv != null && I.cv.W == PixelView.I.width && I.cv.H == PixelView.Height) return I;
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

        void LateUpdate()
        {
            transform.SetAsLastSibling();
            // a picture behind the curtain covers everything else on the screen, the life flames included
            if (backdrop && backdrop.enabled) backdrop.transform.SetSiblingIndex(Mathf.Max(0, transform.GetSiblingIndex() - 1));
        }

        RawImage backdrop;

        /// <summary>A picture behind the curtain (the intro cards sit over the sleeping city).</summary>
        public static void Backdrop(string uiTexture)
        {
            var f = Ensure();
            if (!f.backdrop)
            {
                var go = new GameObject("Backdrop", typeof(RectTransform));
                go.layer = PixelView.PixelUILayer;
                go.transform.SetParent(f.transform.parent, false);
                f.backdrop = go.AddComponent<RawImage>();
                f.backdrop.raycastTarget = false;
                var rt = (RectTransform)go.transform;
                rt.anchorMin = rt.anchorMax = new Vector2(0, 1);
                rt.pivot = new Vector2(0, 1);
            }
            if (string.IsNullOrEmpty(uiTexture)) { f.backdrop.enabled = false; return; }
            var t = Resources.Load<Texture2D>("UI/" + uiTexture);
            t.filterMode = FilterMode.Point;
            f.backdrop.texture = t;
            f.backdrop.enabled = true;
            var r = (RectTransform)f.backdrop.transform;
            r.sizeDelta = new Vector2(t.width, t.height);
            r.anchoredPosition = new Vector2(Mathf.Round((PixelView.I.width - t.width) / 2f), -(PixelView.Height - t.height));
            f.backdrop.transform.SetSiblingIndex(f.transform.GetSiblingIndex());
        }

        public static void Set(float a, string text = null, bool textAlways = false)
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
            if (textAlways && lv < 16)
                c.Clear(new Color32(6, 4, 12, (byte)(lv * 12)));      // a smooth veil for captions over a picture
            else
                for (int y = 0; y < c.H; y++)
                    for (int x = 0; x < c.W; x++)
                        c.Set(x, y, Bayer[(y & 3) * 4 + (x & 3)] < lv ? Night : Clear);
            if (!string.IsNullOrEmpty(text) && (lv >= 16 || textAlways))
            {
                var font = PixelFont.Main;
                var lines = text.Split('\n');
                int y = c.H / 2 - lines.Length * font.Line / 2;
                foreach (var l in lines)
                {
                    int w = font.Measure(l);
                    for (int ox = -1; ox <= 1; ox++)
                        for (int oy = -1; oy <= 1; oy++)
                            if (ox != 0 || oy != 0) font.DrawString(c, (c.W - w) / 2 + ox, y + oy, l, Night);
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
