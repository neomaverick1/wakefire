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

    /// <summary>A picture the menus can paint with: its pixels, rows from the top. They live in
    /// Resources/Menu, the one folder of textures the game is allowed to read back.</summary>
    public class Pic
    {
        public Color32[] px;
        public int w, h;
        static readonly System.Collections.Generic.Dictionary<string, Pic> all = new System.Collections.Generic.Dictionary<string, Pic>();

        public static Pic Get(string name)
        {
            if (all.TryGetValue(name, out var p)) return p;
            var t = Resources.Load<Texture2D>("Menu/" + name);
            if (t && t.isReadable)
            {
                var src = t.GetPixels32();
                p = new Pic { w = t.width, h = t.height, px = new Color32[src.Length] };
                for (int y = 0; y < p.h; y++) System.Array.Copy(src, (p.h - 1 - y) * p.w, p.px, y * p.w, p.w);
            }
            all[name] = p;
            return p;
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

        // Nothing is drawn outside this window (a page sliding past its frame, a map wider than its view).
        int cx0, cy0, cx1 = int.MaxValue, cy1 = int.MaxValue;
        public void Clip(int x, int y, int w, int h) { cx0 = x; cy0 = y; cx1 = x + w; cy1 = y + h; }
        public void NoClip() { cx0 = cy0 = 0; cx1 = cy1 = int.MaxValue; }

        public void Set(int x, int y, Color32 c, bool isShadow = false)
        {
            if (x < 0 || y < 0 || x >= W || y >= H || x < cx0 || y < cy0 || x >= cx1 || y >= cy1) return;
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
                    if (xx < 0 || yy < 0 || xx >= W || yy >= H || xx < cx0 || yy < cy0 || xx >= cx1 || yy >= cy1) continue;
                    int i = (H - 1 - yy) * W + xx;
                    px[i] = c;
                    solid[i] = false;
                }
            dirty = true;
        }

        /// <summary>A box with a one-pixel edge.</summary>
        public void Box(int x, int y, int w, int h, Color32 fill, Color32 edge)
        {
            Rect(x, y, w, h, edge);
            Rect(x + 1, y + 1, w - 2, h - 2, fill);
        }

        /// <summary>Lay a picture on the surface with its top left corner at (x, y): see-through where
        /// the picture is clear, each of its pixels drawn scale by scale, darkened by shade, and only
        /// the part of it from (sx, sy), w by h, if that is given.</summary>
        public void Blit(Pic p, int x, int y, int scale = 1, float shade = 1f, int sx = 0, int sy = 0, int w = -1, int h = -1)
        {
            if (p == null) return;
            if (w < 0) w = p.w - sx;
            if (h < 0) h = p.h - sy;
            int sh256 = Mathf.Clamp(Mathf.RoundToInt(shade * 256f), 0, 256);
            for (int j = 0; j < h; j++)
            {
                int py = sy + j;
                if (py < 0 || py >= p.h) continue;
                for (int i = 0; i < w; i++)
                {
                    int qx = sx + i;
                    if (qx < 0 || qx >= p.w) continue;
                    var c = p.px[py * p.w + qx];
                    if (c.a < 128) continue;
                    if (sh256 != 256) c = new Color32((byte)(c.r * sh256 >> 8), (byte)(c.g * sh256 >> 8), (byte)(c.b * sh256 >> 8), 255);
                    else c.a = 255;
                    for (int v = 0; v < scale; v++)
                    {
                        int yy = y + j * scale + v;
                        if (yy < 0 || yy >= H || yy < cy0 || yy >= cy1) continue;
                        for (int u = 0; u < scale; u++)
                        {
                            int xx = x + i * scale + u;
                            if (xx < 0 || xx >= W || xx < cx0 || xx >= cx1) continue;
                            int k = (H - 1 - yy) * W + xx;
                            px[k] = c;
                            solid[k] = true;
                        }
                    }
                }
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
