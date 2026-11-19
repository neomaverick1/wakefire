// The hand-set WAKEFIRE face (Art/pixel/font.py), drawn straight into pixel buffers so text
// stays exactly on the render grid. Buffers are top-down: (0,0) is the top-left pixel.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    [Serializable] public class FontJson { public int height, baseline, line, space; public GlyphJson[] glyphs; }
    [Serializable] public class GlyphJson { public int c, x, w; }

    public class PixelFont
    {
        static PixelFont main;
        public static PixelFont Main => main ??= new PixelFont("Fonts/ash");

        public readonly int Height, Line, Space;
        readonly Dictionary<char, GlyphJson> glyphs = new Dictionary<char, GlyphJson>();
        readonly bool[] ink;
        readonly int aw;

        PixelFont(string path)
        {
            var tex = Resources.Load<Texture2D>(path);
            var meta = JsonUtility.FromJson<FontJson>(Resources.Load<TextAsset>(path).text);
            Height = meta.height;
            Line = meta.line;
            Space = meta.space;
            foreach (var g in meta.glyphs) glyphs[(char)g.c] = g;
            aw = tex.width;
            var px = tex.GetPixels32();
            ink = new bool[px.Length];
            for (int i = 0; i < px.Length; i++) ink[i] = px[i].a > 127;
        }

        public bool Has(char c) => glyphs.ContainsKey(c);

        public int Advance(char c)
        {
            if (!glyphs.TryGetValue(c, out var g)) g = glyphs['?'];
            return g.w + Space;
        }

        public int Measure(string s)
        {
            int w = 0;
            foreach (char c in s) w += Advance(c);
            return Mathf.Max(0, w - Space);
        }

        /// <summary>Draw one glyph with its top-left at (x, y) in a top-down buffer. Returns the advance.</summary>
        public int Draw(PixelCanvas cv, int x, int y, char c, Color32 col, Color32? shadow = null)
        {
            if (!glyphs.TryGetValue(c, out var g)) g = glyphs['?'];
            for (int gy = 0; gy < Height; gy++)
            {
                int row = (Height - 1 - gy) * aw;   // atlas rows are bottom-up
                for (int gx = 0; gx < g.w; gx++)
                {
                    if (!ink[row + g.x + gx]) continue;
                    if (shadow.HasValue) cv.Set(x + gx + 1, y + gy + 1, shadow.Value, true);
                    cv.Set(x + gx, y + gy, col);
                }
            }
            return g.w + Space;
        }

        public int DrawString(PixelCanvas cv, int x, int y, string s, Color32 col, Color32? shadow = null)
        {
            foreach (char c in s) x += Draw(cv, x, y, c, col, shadow);
            return x;
        }
    }

    /// <summary>A small CPU-side pixel surface shown through a UI RawImage on the pixel canvas.</summary>
    public class PixelCanvas
    {
        public readonly int W, H;
        public readonly Texture2D tex;
        readonly Color32[] px;
        readonly bool[] solid;   // shadows never overwrite ink drawn this frame
        bool dirty;

        public PixelCanvas(int w, int h)
        {
            W = w; H = h;
            tex = new Texture2D(w, h, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp };
            px = new Color32[w * h];
            solid = new bool[w * h];
        }

        public void Clear(Color32 c)
        {
            for (int i = 0; i < px.Length; i++) { px[i] = c; solid[i] = false; }
            dirty = true;
        }

        public void Set(int x, int y, Color32 c, bool isShadow = false)
        {
            if (x < 0 || y < 0 || x >= W || y >= H) return;
            int i = (H - 1 - y) * W + x;
            if (isShadow && solid[i]) return;
            px[i] = c;
            if (!isShadow) solid[i] = true;
            dirty = true;
        }

        public Color32 Get(int x, int y) => (x < 0 || y < 0 || x >= W || y >= H) ? new Color32() : px[(H - 1 - y) * W + x];

        public void Rect(int x, int y, int w, int h, Color32 c)
        {
            for (int yy = y; yy < y + h; yy++)
                for (int xx = x; xx < x + w; xx++)
                {
                    if (xx < 0 || yy < 0 || xx >= W || yy >= H) continue;
                    int i = (H - 1 - yy) * W + xx;
                    px[i] = c;
                    solid[i] = false;
                }
            dirty = true;
        }

        public void HLine(int x, int y, int w, Color32 c) => Rect(x, y, w, 1, c);
        public void VLine(int x, int y, int h, Color32 c) => Rect(x, y, 1, h, c);

        public void Apply()
        {
            if (!dirty) return;
            tex.SetPixels32(px);
            tex.Apply(false);
            dirty = false;
        }

        public static Color32 Hex(string h)
        {
            ColorUtility.TryParseHtmlString(h, out var c);
            return c;
        }
    }
}
