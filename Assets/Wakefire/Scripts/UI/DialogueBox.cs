// The text box: dark night-blue panel in a bronze frame, the speaker's name on a tab, words
// typed out in the speaker's voice. Markup: {g}gold{/} {r}red {t}dream-teal {w}white,
// '|' holds for a beat, '^' starts a new box, '\n' breaks the line.
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace Wakefire
{
    public class DialogueBox : MonoBehaviour
    {
        public static DialogueBox I;
        public bool Busy { get; private set; }
        /// <summary>Test and attract mode: pages turn by themselves after a beat.</summary>
        public static float AutoAdvance = 0;

        struct Ch { public char c; public Color32 col; public float hold; }

        const int Lines = 3, PadX = 9, PadY = 7;
        static readonly Color32 Ink = PixelCanvas.Hex("#f4ead8"), Shadow = PixelCanvas.Hex("#07040c"), Gold = PixelCanvas.Hex("#f6c85a"),
            Red = PixelCanvas.Hex("#ff6a58"), Teal = PixelCanvas.Hex("#7ee0e0"), Fill = PixelCanvas.Hex("#161228"), Fill2 = PixelCanvas.Hex("#1d1834"),
            Outline = PixelCanvas.Hex("#0a0610"), Bronze = PixelCanvas.Hex("#bc7a34"), BronzeL = PixelCanvas.Hex("#ffd88a"),
            BronzeD = PixelCanvas.Hex("#6a3a18"), Clear = new Color32(0, 0, 0, 0);

        RawImage boxImg, tabImg;
        PixelCanvas box, tab;
        int boxW, boxH;
        List<List<List<Ch>>> pages;
        string voice;
        bool dream;

        public static DialogueBox Ensure()
        {
            if (I) return I;
            var go = new GameObject("Dialogue", typeof(RectTransform));
            go.layer = PixelView.PixelUILayer;
            go.transform.SetParent(PixelView.I.pixelRoot, false);
            PixelView.Stretch((RectTransform)go.transform);
            I = go.AddComponent<DialogueBox>();
            I.boxImg = MakeImage(go.transform, "box");
            I.tabImg = MakeImage(go.transform, "tab");
            I.boxImg.enabled = I.tabImg.enabled = false;
            return I;
        }

        static RawImage MakeImage(Transform parent, string name)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.layer = PixelView.PixelUILayer;
            go.transform.SetParent(parent, false);
            var img = go.AddComponent<RawImage>();
            img.raycastTarget = false;
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(0, 1);
            rt.pivot = new Vector2(0, 1);
            return img;
        }

        /// <summary>Close the box at once, mid-sentence if need be.</summary>
        public static void Reset()
        {
            if (!I) return;
            I.StopAllCoroutines();
            I.options = null;
            I.boxImg.enabled = I.tabImg.enabled = false;
            I.Busy = false;
        }

        /// <summary>Show text and wait until the player has read every box.</summary>
        public static IEnumerator Say(string speaker, string text, string voice = "narrator", bool dreamVoice = false)
        {
            var b = Ensure();
            b.options = null;
            yield return b.Run(speaker, text, voice, dreamVoice);
        }

        /// <summary>Text with a choice on its last box; the answer lands in Choice (0 or 1).</summary>
        public static IEnumerator Ask(string speaker, string text, string a, string b, string voice = "narrator", bool dreamVoice = false)
        {
            var box = Ensure();
            box.options = new[] { a, b };
            yield return box.Run(speaker, text, voice, dreamVoice);
            box.options = null;
        }

        public static int Choice;
        string[] options;
        int optSel;

        IEnumerator Run(string speaker, string text, string v, bool dreamVoice)
        {
            Busy = true;
            voice = v;
            dream = dreamVoice;
            Layout();
            pages = Paginate(text, boxW - PadX * 2);
            DrawTab(speaker);
            boxImg.enabled = true;
            yield return null;   // the press that opened this box must not skip it
            foreach (var page in pages)
            {
                int total = 0;
                foreach (var line in page) total += line.Count;
                float shown = 0;
                int last = -1;
                bool done = false;
                while (!done)
                {
                    float speed = Controls.Held(Controls.Interact) || Controls.Held(Controls.Attack) || Controls.FingerDown ? 90f : 42f;
                    if (Advance()) shown = total;
                    int before = (int)shown;
                    shown += Time.unscaledDeltaTime * speed;
                    // honour holds: stop at a held character until its beat passes
                    int n = Mathf.Min((int)shown, total);
                    for (int i = before; i < n; i++)
                    {
                        var ch = CharAt(page, i);
                        if (ch.hold > 0 && shown < total)
                        {
                            shown = i + 1;
                            n = i + 1;
                            Draw(page, n, false);
                            Blip(ch.c);
                            yield return Wait(ch.hold);
                            break;
                        }
                        if (i % 2 == 0) Blip(ch.c);
                    }
                    if (n != last) { Draw(page, n, false); last = n; }
                    if (n >= total) done = true;
                    yield return null;
                }
                // wait for the reader, with the bronze arrow bobbing (or a choice on the last box)
                float t = 0;
                bool lastPage = page == pages[pages.Count - 1];
                if (lastPage && options != null)
                {
                    optSel = 0;
                    yield return null;
                    while (true)
                    {
                        t += Time.unscaledDeltaTime;
                        var mv = Controls.MoveVector;
                        if (Controls.Move.WasPerformedThisFrame() && Mathf.Abs(mv.x) + Mathf.Abs(mv.y) > 0.5f) { optSel = 1 - optSel; Sfx.Play("menu_move", 0.5f, 0); }
                        DrawOptions(page, total, t);
                        if (Controls.Tapped)
                        {
                            // a finger chooses by touching the answer itself; a tap anywhere else chooses nothing
                            var at = Controls.FingerAt - new Vector2(boxImg.rectTransform.anchoredPosition.x, -boxImg.rectTransform.anchoredPosition.y);
                            int hit = -1;
                            for (int i = 0; i < 2; i++) if (optRect[i].Contains(at)) hit = i;
                            if (hit >= 0) { optSel = hit; DrawOptions(page, total, 0); Choice = optSel; Sfx.Play("menu_ok", 0.7f, 0); break; }
                        }
                        else if (Confirmed() || (AutoAdvance > 0 && t > AutoAdvance)) { Choice = optSel; Sfx.Play("menu_ok", 0.7f, 0); break; }
                        yield return null;
                    }
                    break;
                }
                while (true)
                {
                    t += Time.unscaledDeltaTime;
                    Draw(page, total, ((int)(t * 2.5f)) % 2 == 0);
                    if (Advance() || (AutoAdvance > 0 && t > AutoAdvance)) break;
                    yield return null;
                }
                Sfx.Play("text_next");
                yield return null;
            }
            boxImg.enabled = tabImg.enabled = false;
            Busy = false;
        }

        static IEnumerator Wait(float s)
        {
            float t = 0;
            while (t < s)
            {
                if (Controls.Down(Controls.Interact) || Controls.Down(Controls.Attack) || Controls.Tapped) yield break;
                t += Time.unscaledDeltaTime;
                yield return null;
            }
        }

        static bool Confirmed() => Controls.Down(Controls.Interact) || Controls.Down(Controls.Attack) || Controls.Down(Controls.Confirm);
        static bool Advance() => Confirmed() || Controls.Tapped;
        readonly Rect[] optRect = new Rect[2];

        /// <summary>Where an answer is on the screen, in screen pixels (test runs touch it there).</summary>
        public Vector2 OptionCentre(int i)
        {
            var c = optRect[i].center + new Vector2(boxImg.rectTransform.anchoredPosition.x, -boxImg.rectTransform.anchoredPosition.y);
            float k = PixelView.I.ScreenScale;
            return new Vector2(c.x * k, (PixelView.Height - c.y) * k);
        }

        void Blip(char c)
        {
            if (char.IsLetterOrDigit(c)) Voice.Blip(voice, c, dream);
        }

        static Ch CharAt(List<List<Ch>> page, int i)
        {
            foreach (var line in page)
            {
                if (i < line.Count) return line[i];
                i -= line.Count;
            }
            return default;
        }

        void Layout()
        {
            int W = PixelView.I.width, H = PixelView.Height;
            boxW = Mathf.Min(W - 20, 372);
            boxH = Lines * PixelFont.Main.Line - 2 + PadY * 2;
            if (box == null || box.W != boxW)
            {
                box = new PixelCanvas(boxW, boxH);
                boxImg.texture = box.tex;
                boxImg.rectTransform.sizeDelta = new Vector2(boxW, boxH);
            }
            // keep the box away from Azar: bottom of the screen unless he is down there
            bool low = Player.I && PixelView.I.WorldToPixel(Player.I.pos).y < H * 0.42f;
            float x = Mathf.Round((W - boxW) / 2f);
            float y = low ? 46 : H - boxH - 8;
            boxImg.rectTransform.anchoredPosition = new Vector2(x, -y);
            tabImg.rectTransform.anchoredPosition = new Vector2(x + 8, -(y - 11));
        }

        void DrawTab(string speaker)
        {
            if (string.IsNullOrEmpty(speaker)) { tabImg.enabled = false; return; }
            var f = PixelFont.Main;
            int w = f.Measure(speaker) + 12, h = 13;
            tab = new PixelCanvas(w, h);
            tab.Clear(Clear);
            tab.Rect(0, 0, w, h, Outline);
            tab.Rect(1, 1, w - 2, h - 1, Bronze);
            tab.HLine(1, 1, w - 2, BronzeL);
            tab.Rect(2, 2, w - 4, h - 2, Fill);
            f.DrawString(tab, 6, 3, speaker, Gold, Shadow);
            tab.Apply();
            tabImg.texture = tab.tex;
            tabImg.rectTransform.sizeDelta = new Vector2(w, h);
            tabImg.enabled = true;
            tabImg.transform.SetAsLastSibling();
        }

        void Frame()
        {
            int w = boxW, h = boxH;
            box.Clear(Clear);
            box.Rect(0, 0, w, h, Outline);
            box.Rect(1, 1, w - 2, h - 2, Bronze);
            box.HLine(1, 1, w - 2, BronzeL);
            box.VLine(1, 1, h - 2, BronzeL);
            box.HLine(1, h - 2, w - 2, BronzeD);
            box.VLine(w - 2, 1, h - 2, BronzeD);
            box.Rect(3, 3, w - 6, h - 6, Outline);
            // night-blue fill with a faint dithered lift towards the top
            for (int y = 4; y < h - 4; y++)
                for (int x = 4; x < w - 4; x++)
                {
                    bool lift = y < 4 + (h - 8) / 3 && ((x + y) & 1) == 0 && y < 4 + (h - 8) / 3 - (x & 1);
                    box.Set(x, y, lift ? Fill2 : Fill);
                }
            // bronze rivets in the corners
            foreach (var (cx, cy) in new[] { (5, 5), (w - 7, 5), (5, h - 7), (w - 7, h - 7) })
            {
                box.Set(cx, cy, BronzeL); box.Set(cx + 1, cy, Bronze); box.Set(cx, cy + 1, Bronze); box.Set(cx + 1, cy + 1, BronzeD);
            }
        }

        void Draw(List<List<Ch>> page, int count, bool arrow)
        {
            Frame();
            var f = PixelFont.Main;
            int y = PadY;
            int left = count;
            foreach (var line in page)
            {
                int x = PadX;
                foreach (var ch in line)
                {
                    if (left-- <= 0) break;
                    x += f.Draw(box, x, y, ch.c, ch.col, Shadow);
                }
                y += f.Line;
            }
            if (arrow) f.Draw(box, boxW - PadX - 4, boxH - PadY - 2, '▼', Gold, Shadow);
            box.Apply();
        }

        void DrawOptions(List<List<Ch>> page, int count, float t)
        {
            Draw(page, count, false);
            var f = PixelFont.Main;
            int y = boxH - PadY - f.Line + 2;
            int x = boxW - PadX - f.Measure(options[0]) - f.Measure(options[1]) - 34;
            for (int i = 0; i < 2; i++)
            {
                bool on = i == optSel;
                if (on && ((int)(t * 3f)) % 2 == 0) f.Draw(box, x - 8, y, '>', Gold, Shadow);
                int x0 = x;
                x = f.DrawString(box, x, y, options[i], on ? Gold : Ink, Shadow) + 16;
                optRect[i] = new Rect(x0 - 12, y - 9, x - 16 - x0 + 22, f.Line + 18);      // a thumb's worth of room round each answer
            }
            box.Apply();
        }

        // ---------------------------------------------------------------- text layout
        static List<List<List<Ch>>> Paginate(string text, int width)
        {
            var f = PixelFont.Main;
            var pages = new List<List<List<Ch>>>();
            foreach (var pageText in text.Split('^'))
            {
                var chars = Parse(pageText.Trim());
                var lines = new List<List<Ch>>();
                var line = new List<Ch>();
                int lineW = 0;
                int i = 0;
                while (i < chars.Count)
                {
                    if (chars[i].c == '\n')
                    {
                        lines.Add(line); line = new List<Ch>(); lineW = 0; i++;
                        continue;
                    }
                    // next word (including trailing space)
                    int j = i;
                    int ww = 0;
                    while (j < chars.Count && chars[j].c != ' ' && chars[j].c != '\n') { ww += f.Advance(chars[j].c); j++; }
                    if (lineW > 0 && lineW + ww - f.Space > width)
                    {
                        // drop the trailing space of the previous line
                        if (line.Count > 0 && line[line.Count - 1].c == ' ') line.RemoveAt(line.Count - 1);
                        lines.Add(line); line = new List<Ch>(); lineW = 0;
                    }
                    for (int k = i; k < j; k++) line.Add(chars[k]);
                    lineW += ww;
                    if (j < chars.Count && chars[j].c == ' ')
                    {
                        if (lineW > 0) { line.Add(chars[j]); lineW += f.Advance(' '); }
                        j++;
                    }
                    i = j;
                }
                if (line.Count > 0) lines.Add(line);
                for (int p = 0; p < lines.Count; p += Lines)
                    pages.Add(lines.GetRange(p, Mathf.Min(Lines, lines.Count - p)));
            }
            return pages;
        }

        static List<Ch> Parse(string s)
        {
            var list = new List<Ch>();
            Color32 col = Ink;
            for (int i = 0; i < s.Length; i++)
            {
                char c = s[i];
                if (c == '{')
                {
                    int e = s.IndexOf('}', i);
                    if (e > i)
                    {
                        string tag = s.Substring(i + 1, e - i - 1);
                        col = tag switch { "g" => Gold, "r" => Red, "t" => Teal, _ => Ink };
                        i = e;
                        continue;
                    }
                }
                if (c == '|')
                {
                    if (list.Count > 0) { var last = list[list.Count - 1]; last.hold += 0.32f; list[list.Count - 1] = last; }
                    continue;
                }
                if (c == '…' || (c == '.' && i + 2 < s.Length && s[i + 1] == '.' && s[i + 2] == '.'))
                {
                    // an ellipsis types out slowly: three beats
                    for (int k = 0; k < 3; k++) list.Add(new Ch { c = '.', col = col, hold = 0.16f });
                    if (c == '.') i += 2;
                    continue;
                }
                list.Add(new Ch { c = c, col = col });
            }
            return list;
        }
    }
}
