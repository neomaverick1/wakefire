// The pause screen: the world stops and three pages open over it, side by side. It opens on the
// middle one, the items: what goes on the item button is chosen here, and everything else Azar
// carries is laid out beside it. One page to the left is saving and loading, with the three
// journeys, and the switches for music and sounds. One page to the right is the map: the world,
// each place drawn where it lies and Azar marked on it. Stick or arrows move; walking off the
// side of a page turns it (so do the shoulder buttons, a swipe, or a tap on the page's name).
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Wakefire
{
    public class Pause : MonoBehaviour
    {
        static Pause I;
        public static bool Open => Game.Paused && I && I.img.enabled;
        /// <summary>The page in front (0 save and load, 1 items, 2 the map), and where the panel sits in game pixels.</summary>
        public static int Page => I ? I.page : -1;
        public static RectInt Panel => I ? new RectInt(I.px, I.py, I.PW, I.PH) : default;
        RawImage img;
        PixelCanvas cv;
        public const int SavePage = 0, ItemPage = 1, MapPage = 2;
        int page = ItemPage;
        float shown = ItemPage, clock;
        string said;

        // where things are (worked out for the canvas in hand)
        int W, H, px, py, PW, PH, ix, iy, IW, IH;

        int cell;                               // items page: which box the cursor is on
        int row;                                // save page: 0..2 the journeys, 3 music, 4 sounds, 5 the title
        int ask = -1, askSel, askStage;         // save page: the little box that opens on a journey
        float pan;                              // map page: how far down the sheet the view has moved
        World world;

        [System.Serializable] class WorldPlace { public string map; public int x, y, w, h; }
        [System.Serializable] class WorldInside { public string map, at; public int x, y; }
        [System.Serializable] class World { public int w, h, scale; public WorldPlace[] places; public WorldInside[] inside; }

        static readonly Color32 Veil = new Color32(6, 4, 12, 170), Frame = new Color32(10, 6, 16, 255), Bronze = new Color32(188, 122, 52, 255),
            BronzeL = new Color32(255, 216, 138, 255), BronzeD = new Color32(106, 58, 24, 255), Fill = new Color32(22, 18, 40, 255), Fill2 = new Color32(29, 24, 52, 255),
            Well = new Color32(14, 11, 26, 255), WellOn = new Color32(40, 32, 66, 255), Gold = new Color32(246, 200, 90, 255), Ink = new Color32(244, 234, 216, 255),
            Dim = new Color32(150, 140, 170, 255), Faint = new Color32(92, 84, 110, 255), Sh = new Color32(6, 4, 12, 255);

        static readonly string[] PageName = { "Save", "Items", "Map" };

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

        // ------------------------------------------------------------------------------ opening and closing
        void OpenUp()
        {
            Game.Paused = true;
            Time.timeScale = 0;
            if (cv == null || cv.W != PixelView.I.width || cv.H != PixelView.Height)
            {
                cv = new PixelCanvas(PixelView.I.width, PixelView.Height);
                img.texture = cv.tex;
            }
            if (world == null)
            {
                var j = Resources.Load<TextAsset>("Menu/world");
                world = j ? JsonUtility.FromJson<World>(j.text) : new World { places = new WorldPlace[0], inside = new WorldInside[0], scale = 10 };
            }
            page = ItemPage; shown = ItemPage; said = null; ask = -1;
            row = Save.Slot;
            cell = System.Array.IndexOf(Items.Usable, Items.Current);
            Layout();
            CentreMap();
            Draw();
            img.enabled = true;
            if (Hud.I) Hud.I.gameObject.SetActive(false);
            Sfx.Play("menu_ok", 0.6f, 0);
            AudioListener.volume = 0.5f;
        }

        void Close()
        {
            Game.Paused = false;
            Time.timeScale = 1;
            img.enabled = false;
            if (Hud.I) Hud.I.gameObject.SetActive(true);
            AudioListener.volume = 1f;
        }

        void Layout()
        {
            W = cv.W; H = cv.H;
            PW = Mathf.Min(304, W - 8); PH = Mathf.Min(168, H - 8);
            px = (W - PW) / 2; py = (H - PH) / 2;
            ix = px + 6; iy = py + 22; IW = PW - 12; IH = PH - 42;
        }

        /// <summary>Test runs work the screen through here: "open", "close", "page 0", "save 1", "load 1", "item sling", "title".</summary>
        public static string TestDo;

        void Update()
        {
            if (Title.I) return;
            if (TestDo != null) { string t = TestDo; TestDo = null; Test(t); return; }
            if (!Game.Paused)
            {
                if (Controls.Down(Controls.Pause) && Player.I && !Game.Busy && !(Story.I && Story.I.Running)) OpenUp();
                return;
            }
            if (!img.enabled) return;            // paused by something else
            clock += Time.unscaledDeltaTime;
            Layout();
            bool done = Poll();
            if (done || !Game.Paused) return;
            // the pages follow a finger that is dragging them, and slide home when it lets go
            if (pressed && dragged && sideways && ask < 0)
                shown = Mathf.Clamp(page + pull, -0.12f, 2.12f);
            else
                shown = Mathf.MoveTowards(shown, page, Time.unscaledDeltaTime * 7f);
            Draw();
        }

        void Test(string t)
        {
            var a = t.Split(' ');
            if (a[0] == "open") { if (!Game.Paused) OpenUp(); return; }
            if (!Game.Paused || !img.enabled) return;
            switch (a[0])
            {
                case "close": Close(); break;
                case "page": page = int.Parse(a[1]); shown = page; if (page == MapPage) CentreMap(); Draw(); break;
                case "cell": cell = int.Parse(a[1]); Draw(); break;
                case "row": row = int.Parse(a[1]); Draw(); break;
                case "ask": ask = int.Parse(a[1]); askStage = 0; askSel = 0; Draw(); break;
                case "save": DoSave(int.Parse(a[1])); Draw(); break;
                case "load": DoLoad(int.Parse(a[1])); break;
                case "item": Items.Choose(a[1]); Draw(); break;
                case "title": ToTitle(); break;
            }
        }

        // ------------------------------------------------------------------------------ the controls
        Vector2 downAt;
        bool pressed, dragged, sideways;
        float lastY, pull;

        Vector2 PointerAt()
        {
            var tp = Pointer.current;
            if (tp == null) return new Vector2(-1, -1);
            var pos = tp.position.ReadValue();
            float k = PixelView.I.ScreenScale;
            return new Vector2(pos.x / k, PixelView.Height - pos.y / k);
        }

        void PageTo(int p)
        {
            p = Mathf.Clamp(p, 0, 2);
            if (p == page) return;
            page = p; said = null; ask = -1;
            if (page == MapPage) CentreMap();
            Sfx.Play("menu_move", 0.6f, 0);
        }

        /// <summary>Reads the controls. True if the screen closed.</summary>
        bool Poll()
        {
            if (Controls.Down(Controls.Pause)) { Close(); return true; }
            if (Controls.Down(Controls.Back))
            {
                if (ask >= 0) { if (askStage > 0) { askStage = 0; askSel = 0; } else ask = -1; return false; }
                Close(); return true;
            }
            if (ask < 0)
            {
                if (Controls.Down(Controls.PageLeft)) PageTo(page - 1);
                if (Controls.Down(Controls.PageRight)) PageTo(page + 1);
            }
            // a finger or the mouse: drags pan the map and turn the pages, taps choose
            var tp = Pointer.current;
            bool tapped = false;
            Vector2 at = PointerAt();
            if (tp != null)
            {
                if (tp.press.wasPressedThisFrame) { pressed = true; dragged = false; sideways = false; pull = 0; downAt = at; }
                else if (pressed && tp.press.isPressed)
                {
                    var d = at - downAt;
                    if (!dragged && d.magnitude > 7f) { dragged = true; sideways = Mathf.Abs(d.x) > Mathf.Abs(d.y); }
                    if (dragged && !sideways && page == MapPage && ask < 0)
                        pan = Mathf.Clamp(pan - (at.y - lastY), 0, Mathf.Max(0, world.h - IH));
                    if (dragged && sideways) pull = -d.x / (IW + 16f);
                }
                if (pressed && tp.press.wasReleasedThisFrame)
                {
                    pressed = false;
                    var d = at - downAt;
                    if (!dragged) tapped = true;
                    else if (ask < 0 && sideways && Mathf.Abs(d.x) > 34f) PageTo(page + (d.x < 0 ? 1 : -1));
                }
                lastY = at.y;
            }
            var step = Controls.Step();
            // a click or a tap chooses what it lands on, not whatever the cursor happens to be on
            bool pointer = tp != null && (tp.press.wasPressedThisFrame || tp.press.wasReleasedThisFrame || tp.press.isPressed);
            bool act = !pointer && (Controls.Down(Controls.Confirm) || Controls.Down(Controls.Interact));
            if (tapped) { Tap(at); return !Game.Paused; }
            switch (page)
            {
                case ItemPage: return ItemControls(step, act);
                case SavePage: return SaveControls(step, act);
                default: return MapControls(step, act);
            }
        }

        /// <summary>A tap on the screen: the page names turn pages, "Carry on" closes, boxes and rows are chosen.</summary>
        void Tap(Vector2 at)
        {
            var pt = new Vector2Int((int)at.x, (int)at.y);
            if (ask >= 0 && page == SavePage)
            {
                var b = AskBox(out var lines);
                for (int i = 0; i < lines.Length; i++)
                    if (at.x >= b.x && at.x < b.xMax && at.y >= b.y + 19 + i * 13 && at.y < b.y + 32 + i * 13) { askSel = i; AskChoose(); return; }
                if (!b.Contains(pt)) ask = -1;
                return;
            }
            if (at.y >= py + 2 && at.y < py + 21)
            {
                if (at.x < px + PW * 0.3f) PageTo(page - 1);
                else if (at.x > px + PW * 0.7f) PageTo(page + 1);
                return;
            }
            if (at.y >= py + PH - 19 && at.x > px + PW - 70) { Sfx.Play("menu_ok", 0.6f, 0); Close(); return; }
            if (page == ItemPage)
            {
                var cs = Cells(0);
                for (int i = 0; i < cs.Count; i++)
                    if (cs[i].r.Contains(pt))
                    {
                        cell = i; said = null;
                        if (cs[i].use) PutOn(cs[i].def); else Sfx.Play("menu_move", 0.5f, 0);
                        return;
                    }
            }
            else if (page == SavePage)
            {
                for (int i = 0; i < 6; i++)
                    if (RowRect(i, 0).Contains(pt)) { row = i; said = null; SaveChoose(); return; }
            }
        }

        // ------------------------------------------------------------------------------ the frame
        void Draw()
        {
            var f = PixelFont.Main;
            cv.NoClip();
            cv.Clear(Veil);
            cv.Rect(px, py, PW, PH, Frame);
            cv.Rect(px + 1, py + 1, PW - 2, PH - 2, Bronze);
            cv.HLine(px + 1, py + 1, PW - 2, BronzeL); cv.VLine(px + 1, py + 1, PH - 2, BronzeL);
            cv.HLine(px + 1, py + PH - 2, PW - 2, BronzeD); cv.VLine(px + PW - 2, py + 1, PH - 2, BronzeD);
            cv.Rect(px + 3, py + 3, PW - 6, PH - 6, Frame);
            cv.Rect(px + 4, py + 4, PW - 8, PH - 8, Fill);
            for (int y = py + 4; y < py + 20; y++)
                for (int x = px + 4; x < px + PW - 4; x++)
                    if (((x + y) & 1) == 0 && y < py + 19 - ((x >> 1) & 1)) cv.Set(x, y, Fill2);
            foreach (var (cx, cy) in new[] { (px + 5, py + 5), (px + PW - 7, py + 5), (px + 5, py + PH - 7), (px + PW - 7, py + PH - 7) })
            {
                cv.Set(cx, cy, BronzeL); cv.Set(cx + 1, cy, Bronze); cv.Set(cx, cy + 1, Bronze); cv.Set(cx + 1, cy + 1, BronzeD);
            }
            // the page's name, and the pages to either side of it
            string title = page == SavePage ? "SAVE AND LOAD" : page == ItemPage ? "ITEMS" : "THE WORLD";
            f.DrawString(cv, (W - f.Measure(title)) / 2, py + 6, title, Gold, Sh);
            bool blink = ((int)(clock * 2.5f)) % 2 == 0;
            if (page > 0)
            {
                f.Draw(cv, px + 10, py + 7, '<', blink ? Gold : Dim, Sh);
                f.DrawString(cv, px + 19, py + 7, PageName[page - 1], Dim, Sh);
            }
            if (page < 2)
            {
                string r = PageName[page + 1];
                f.DrawString(cv, px + PW - 19 - f.Measure(r), py + 7, r, Dim, Sh);
                f.Draw(cv, px + PW - 15, py + 7, '>', blink ? Gold : Dim, Sh);
            }
            for (int i = 0; i < 3; i++) cv.Rect(W / 2 - 8 + i * 6, py + 17, 4, 2, i == page ? Gold : BronzeD);
            cv.HLine(px + 10, py + 20, PW - 20, BronzeD);
            cv.HLine(px + 10, py + PH - 20, PW - 20, BronzeD);
            // the pages themselves, sliding past the window
            cv.Clip(ix, iy, IW, IH);
            for (int p = 0; p < 3; p++)
            {
                float off = (p - shown) * (IW + 16);
                if (Mathf.Abs(off) >= IW + 16) continue;
                int ox = Mathf.RoundToInt(off);
                if (p == SavePage) DrawSave(ox); else if (p == ItemPage) DrawItems(ox); else DrawMap(ox);
            }
            cv.NoClip();
            if (ask >= 0 && page == SavePage) DrawAsk();
            string foot = said ?? Foot();
            f.DrawString(cv, px + 12, py + PH - 15, Fit(foot, PW - 84), said != null ? Gold : Dim, Sh);
            string go = "Carry on";
            f.DrawString(cv, px + PW - 12 - f.Measure(go), py + PH - 15, go, Ink, Sh);
            cv.Apply();
        }

        static string Fit(string s, int width)
        {
            var f = PixelFont.Main;
            if (f.Measure(s) <= width) return s;
            while (s.Length > 1 && f.Measure(s + "…") > width) s = s.Substring(0, s.Length - 1);
            return s + "…";
        }

        string Foot()
        {
            switch (page)
            {
                case ItemPage:
                {
                    var cs = Cells(0);
                    if (cell < 0 || cell >= cs.Count) return "";
                    var c = cs[cell];
                    if (c.def == null || !c.def.have() || !c.use) return "";
                    return Items.Current == c.def ? "It is on the item button." : "Choose it to put it on the item button.";
                }
                case SavePage:
                    if (ask >= 0) return "";
                    if (row < 3) return "Choose a journey to save or load.";
                    if (row == 5) return "The game saves as you go.";
                    return Places.Name(Game.I.CurrentMap) + ", " + Save.Clock(Save.PlayTime);
                default:
                    return "You are in " + Places.Name(Game.I.CurrentMap) + ".";
            }
        }

        // ------------------------------------------------------------------------------ the item page
        struct Cell { public RectInt r; public Items.Def def; public bool use; }

        /// <summary>The boxes of the item page: the four that can go on the button, then what is simply carried.</summary>
        List<Cell> Cells(int ox)
        {
            var l = new List<Cell>();
            for (int i = 0; i < 4; i++)
                l.Add(new Cell { r = new RectInt(ix + ox + 6 + i * 40, iy + 15, 36, 36), def = i < Items.Usable.Length ? Items.Usable[i] : null, use = true });
            int kx = ix + ox + IW - 6 - 5 * 23 + 2;
            for (int j = 0; j < 10; j++)
                l.Add(new Cell { r = new RectInt(kx + (j % 5) * 23, iy + 15 + (j / 5) * 23, 21, 21), def = j < Items.Kept.Length ? Items.Kept[j] : null });
            return l;
        }

        static int Next(List<Cell> cs, int from, Vector2Int dir)
        {
            if (from < 0 || from >= cs.Count) return 0;
            var a = cs[from].r.center;
            int best = -1; float bs = float.MaxValue;
            for (int i = 0; i < cs.Count; i++)
            {
                if (i == from) continue;
                var d = cs[i].r.center - a;
                // (the canvas counts down the screen, the stick counts up it)
                float along = d.x * dir.x - d.y * dir.y, across = Mathf.Abs(d.x * dir.y) + Mathf.Abs(d.y * dir.x);
                if (along < 4f || across > along * 1.6f + 10f) continue;
                float s = along + across * 2.2f;
                if (s < bs) { bs = s; best = i; }
            }
            return best;
        }

        bool ItemControls(Vector2Int step, bool act)
        {
            var cs = Cells(0);
            if (step != Vector2Int.zero)
            {
                int n = Next(cs, cell, step);
                if (n >= 0) { cell = n; said = null; Sfx.Play("menu_move", 0.5f, 0); }
                else if (step.x != 0) PageTo(page + step.x);
            }
            if (act && cell >= 0 && cell < cs.Count) PutOn(cs[cell].def);
            return false;
        }

        void PutOn(Items.Def d)
        {
            if (d == null || !d.have()) { Sfx.Play("deny", 0.5f, 0); return; }
            if (System.Array.IndexOf(Items.Usable, d) < 0) { Sfx.Play("menu_move", 0.5f, 0); return; }
            Items.Choose(d.id);
            said = d.name + " is on the item button.";
            Sfx.Play("menu_ok", 0.7f, 0);
        }

        void DrawItems(int ox)
        {
            var f = PixelFont.Main;
            f.DrawString(cv, ix + ox + 6, iy + 3, "ON THE ITEM BUTTON", Dim, Sh);
            var cs = Cells(ox);
            f.DrawString(cv, cs[4].r.x, iy + 3, "CARRIED", Dim, Sh);
            bool blink = ((int)(clock * 3f)) % 2 == 0;
            for (int i = 0; i < cs.Count; i++)
            {
                var c = cs[i];
                bool on = i == cell && page == ItemPage, have = c.def != null && c.def.have();
                bool chosen = have && c.use && Items.Current == c.def;
                cv.Rect(c.r.x, c.r.y, c.r.width, c.r.height, Frame);
                cv.Rect(c.r.x + 1, c.r.y + 1, c.r.width - 2, c.r.height - 2, on ? (blink ? Gold : BronzeL) : chosen ? Bronze : BronzeD);
                cv.Rect(c.r.x + 2, c.r.y + 2, c.r.width - 4, c.r.height - 4, on ? WellOn : Well);
                if (have)
                {
                    var pic = Pic.Get(c.def.art);
                    int sc = c.use ? 2 : 1;
                    if (pic != null) cv.Blit(pic, c.r.x + (c.r.width - pic.w * sc) / 2, c.r.y + (c.r.height - pic.h * sc) / 2, sc);
                    if (c.def.id == "vessel")
                    {
                        string n = Story.Count("vessels").ToString();
                        f.DrawString(cv, c.r.xMax - 3 - f.Measure(n), c.r.yMax - 11, n, Ink, Sh);
                    }
                }
                else
                {
                    int mx = c.r.x + c.r.width / 2, my = c.r.y + c.r.height / 2;
                    cv.Rect(mx - 1, my - 1, 2, 2, Faint);
                }
                if (chosen)
                {
                    // gold corners: this is the one on the button
                    int x0 = c.r.x + 3, y0 = c.r.y + 3, x1 = c.r.xMax - 4, y1 = c.r.yMax - 4;
                    for (int k = 0; k < 5; k++)
                    {
                        cv.Set(x0 + k, y0, Gold); cv.Set(x0, y0 + k, Gold); cv.Set(x1 - k, y0, Gold); cv.Set(x1, y0 + k, Gold);
                        cv.Set(x0 + k, y1, Gold); cv.Set(x0, y1 - k, Gold); cv.Set(x1 - k, y1, Gold); cv.Set(x1, y1 - k, Gold);
                    }
                }
            }
            // what the cursor is on, in words
            int bx = ix + ox + 4, by = iy + 66, bw = IW - 8, bh = IH - 68;
            cv.Rect(bx, by, bw, bh, Frame);
            cv.Rect(bx + 1, by + 1, bw - 2, bh - 2, BronzeD);
            cv.Rect(bx + 2, by + 2, bw - 4, bh - 4, Well);
            var cur = cell >= 0 && cell < cs.Count ? cs[cell] : default;
            if (cur.def != null && cur.def.have())
            {
                f.DrawString(cv, bx + 8, by + 6, cur.def.name, Gold, Sh);
                int ly = by + 19;
                foreach (var part in cur.def.about.Split('|'))
                    foreach (var line in Wrap(part, bw - 16))
                    {
                        if (ly > by + bh - 12) break;
                        f.DrawString(cv, bx + 8, ly, line, Ink, Sh);
                        ly += 11;
                    }
            }
            else f.DrawString(cv, bx + 8, by + 6, cur.use ? "Nothing here yet." : "Not found yet.", Faint, Sh);
        }

        static List<string> Wrap(string s, int width)
        {
            var f = PixelFont.Main;
            var lines = new List<string>();
            string line = "";
            foreach (var word in s.Split(' '))
            {
                string t = line.Length == 0 ? word : line + " " + word;
                if (f.Measure(t) > width && line.Length > 0) { lines.Add(line); line = word; }
                else line = t;
            }
            if (line.Length > 0) lines.Add(line);
            return lines;
        }

        // ------------------------------------------------------------------------------ the save page
        RectInt RowRect(int i, int ox)
        {
            if (i < 3) return new RectInt(ix + ox + 4, iy + 2 + i * 31, IW - 8, SlotRow.Tall);
            int w = (IW - 8 - 8) / 3;
            return new RectInt(ix + ox + 4 + (i - 3) * (w + 4), iy + 99, w, 17);
        }

        bool SaveControls(Vector2Int step, bool act)
        {
            if (ask >= 0)
            {
                AskBox(out var lines);
                if (step.y != 0)
                {
                    for (int k = 0; k < lines.Length; k++)
                    {
                        askSel = (askSel + (step.y < 0 ? 1 : lines.Length - 1)) % lines.Length;
                        if (AskCan(askSel)) break;
                    }
                    Sfx.Play("menu_move", 0.5f, 0);
                }
                if (act) AskChoose();
                return !Game.Paused;
            }
            if (step != Vector2Int.zero)
            {
                int before = row;
                if (row < 3)
                {
                    if (step.y > 0) row = Mathf.Max(0, row - 1);
                    else if (step.y < 0) row = row == 2 ? 3 : row + 1;
                    else if (step.x > 0) PageTo(page + 1);
                }
                else
                {
                    if (step.y > 0) row = 2;
                    else if (step.x < 0) row = Mathf.Max(3, row - 1);
                    else if (step.x > 0) { if (row == 5) PageTo(page + 1); else row++; }
                }
                if (row != before) { said = null; Sfx.Play("menu_move", 0.5f, 0); }
            }
            if (act) SaveChoose();
            return !Game.Paused;
        }

        void SaveChoose()
        {
            Sfx.Play("menu_ok", 0.7f, 0);
            switch (row)
            {
                case 3: Settings.Toggle(true); break;
                case 4: Settings.Toggle(false); break;
                case 5: ToTitle(); break;
                default: ask = row; askStage = 0; askSel = 0; said = null; break;
            }
        }

        void ToTitle()
        {
            Close();
            if (Game.I.CurrentMap != null) Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn, quiet: true);
            Title.Show();
        }

        string[] AskLines() => askStage == 0 ? new[] { "Save here", "Load", "Never mind" }
            : askStage == 1 ? new[] { "No", "Yes, write over it" } : new[] { "No", "Yes, go back to it" };

        bool AskCan(int i) => !(askStage == 0 && i == 1 && !Save.Has(ask));

        RectInt AskBox(out string[] lines)
        {
            lines = AskLines();
            int bw = 168, bh = 24 + lines.Length * 13;
            return new RectInt(ix + (IW - bw) / 2, iy + (IH - bh) / 2 - 4, bw, bh);
        }

        void AskChoose()
        {
            if (!AskCan(askSel)) { Sfx.Play("deny", 0.5f, 0); return; }
            Sfx.Play("menu_ok", 0.7f, 0);
            if (askStage == 0)
            {
                if (askSel == 0)
                {
                    // into another journey that already holds something: ask before it is gone
                    if (ask != Save.Slot && Save.Has(ask)) { askStage = 1; askSel = 0; }
                    else DoSave(ask);
                }
                else if (askSel == 1) { askStage = 2; askSel = 0; }
                else ask = -1;
            }
            else if (askSel == 0) { askStage = 0; askSel = 0; }
            else if (askStage == 1) DoSave(ask);
            else DoLoad(ask);
        }

        void DoSave(int slot)
        {
            bool ok = Save.WriteTo(slot);
            said = ok ? "Saved: journey " + (slot + 1) + ", " + Save.Describe(Save.Read(slot)) + "." : "Can't save here.";
            ask = -1;
        }

        void DoLoad(int slot)
        {
            if (!Save.Has(slot)) return;
            ask = -1;
            Close();
            Game.I.LoadGame(slot);
        }

        void DrawSave(int ox)
        {
            var f = PixelFont.Main;
            for (int i = 0; i < 3; i++)
            {
                var r = RowRect(i, ox);
                SlotRow.Draw(cv, r.x, r.y, r.width, i, row == i && page == SavePage, i == Save.Slot, clock);
            }
            string[] opt = { "Music: " + (Settings.MusicOn ? "on" : "off"), "Sounds: " + (Settings.SoundOn ? "on" : "off"), "Back to the title" };
            for (int i = 0; i < 3; i++)
            {
                var r = RowRect(3 + i, ox);
                bool on = row == 3 + i && page == SavePage;
                cv.Rect(r.x, r.y, r.width, r.height, Frame);
                cv.Rect(r.x + 1, r.y + 1, r.width - 2, r.height - 2, on ? Gold : BronzeD);
                cv.Rect(r.x + 2, r.y + 2, r.width - 4, r.height - 4, on ? WellOn : Well);
                f.DrawString(cv, r.x + (r.width - f.Measure(opt[i])) / 2, r.y + 4, opt[i], on ? Gold : Ink, Sh);
            }
        }

        void DrawAsk()
        {
            var f = PixelFont.Main;
            var b = AskBox(out var lines);
            cv.Rect(b.x - 1, b.y - 1, b.width + 2, b.height + 2, Frame);
            cv.Rect(b.x, b.y, b.width, b.height, Bronze);
            cv.HLine(b.x, b.y, b.width, BronzeL); cv.VLine(b.x, b.y, b.height, BronzeL);
            cv.Rect(b.x + 2, b.y + 2, b.width - 4, b.height - 4, Frame);
            cv.Rect(b.x + 3, b.y + 3, b.width - 6, b.height - 6, Fill);
            string head = askStage == 0 ? "Journey " + (ask + 1) : askStage == 1 ? "Write over journey " + (ask + 1) + "?" : "Leave this moment?";
            f.DrawString(cv, b.x + (b.width - f.Measure(head)) / 2, b.y + 6, head, Dim, Sh);
            for (int i = 0; i < lines.Length; i++)
            {
                int x = b.x + (b.width - f.Measure(lines[i])) / 2, y = b.y + 21 + i * 13;
                bool on = i == askSel;
                f.DrawString(cv, x, y, lines[i], !AskCan(i) ? Faint : on ? Gold : Ink, Sh);
                if (on && AskCan(i) && ((int)(clock * 3f)) % 2 == 0)
                {
                    f.Draw(cv, x - 10, y, '>', Gold, Sh);
                    f.Draw(cv, x + f.Measure(lines[i]) + 5, y, '<', Gold, Sh);
                }
            }
        }

        // ------------------------------------------------------------------------------ the map page
        /// <summary>Where Azar is on the sheet: the place he is in, or the door of the place he is inside.</summary>
        bool Where(out WorldPlace place, out Vector2 at)
        {
            place = null; at = Vector2.zero;
            string map = Game.I.CurrentMap;
            var p = Player.I;
            foreach (var pl in world.places)
                if (pl.map == map) { place = pl; at = p ? new Vector2(p.pos.x * 16f, -p.pos.y * 16f) : Vector2.zero; return true; }
            foreach (var ins in world.inside)
                if (ins.map == map)
                    foreach (var pl in world.places)
                        if (pl.map == ins.at) { place = pl; at = new Vector2(ins.x, ins.y); return true; }
            return false;
        }

        void CentreMap()
        {
            if (world == null) return;
            float y = world.h / 2f;
            if (Where(out var pl, out var at)) y = pl.y + at.y / world.scale;
            pan = Mathf.Clamp(y - IH / 2f, 0, Mathf.Max(0, world.h - IH));
        }

        bool MapControls(Vector2Int step, bool act)
        {
            if (step.x != 0) PageTo(page + step.x);
            float v = Controls.MoveVector.y;
            if (Mathf.Abs(v) > 0.3f) pan = Mathf.Clamp(pan - v * 90f * Time.unscaledDeltaTime, 0, Mathf.Max(0, world.h - IH));
            return false;
        }

        public static bool Seen(string map) => Story.Has("seen_" + map);

        void DrawMap(int ox)
        {
            var f = PixelFont.Main;
            int mx = ix + ox + (IW - world.w) / 2, my = iy - Mathf.RoundToInt(pan);
            cv.Blit(Pic.Get("world_dark"), mx, my);
            var lit = Pic.Get("world");
            foreach (var pl in world.places)
                if (Seen(pl.map)) cv.Blit(lit, mx + pl.x - 1, my + pl.y - 1, 1, 1f, pl.x - 1, pl.y - 1, pl.w + 2, pl.h + 2);
            bool marked = Where(out var here, out var at);
            int hx = 0, hy = 0;
            if (marked) { hx = mx + here.x + Mathf.RoundToInt(at.x / world.scale); hy = my + here.y + Mathf.RoundToInt(at.y / world.scale); }
            // names, on a dark strip along the foot of each place that has been walked (along its
            // head instead, if the foot is where Azar is standing)
            foreach (var pl in world.places)
            {
                if (!Seen(pl.map)) continue;
                string name = Places.Short(pl.map);
                int tw = f.Measure(name);
                int tx = mx + pl.x + (pl.w - tw) / 2, ty = my + pl.y + pl.h - 11;
                if (marked && here.map == pl.map && hy > ty - 13 && hx > tx - 14 && hx < tx + tw + 14) ty = my + pl.y + 2;
                cv.Rect(tx - 3, ty - 1, tw + 5, 11, Frame);
                f.DrawString(cv, tx, ty, name, pl.map == Game.I.CurrentMap ? Gold : Ink);
            }
            if (marked)
            {
                // a flame where he stands, and a ring that opens round it so the eye finds it
                float beat = (clock * 1.1f) % 1f;
                int rr = 4 + Mathf.RoundToInt(beat * 7f);
                if (beat < 0.8f)
                    for (int k = 0; k < 40; k++)
                    {
                        float a = k / 40f * Mathf.PI * 2f;
                        cv.Set(hx + Mathf.RoundToInt(Mathf.Cos(a) * rr), hy - 1 + Mathf.RoundToInt(Mathf.Sin(a) * rr), beat < 0.45f ? Gold : BronzeD);
                    }
                int lift = ((int)(clock * 4f)) % 2 == 0 ? 1 : 0;
                for (int dy = -6; dy <= 3; dy++)
                    for (int dx = -4; dx <= 4; dx++)
                    {
                        float r = Mathf.Abs(dx) + Mathf.Abs(dy + 1) * (dy < -1 ? 0.62f : 1.1f);
                        if (r <= 3.4f) cv.Set(hx + dx, hy + dy - lift, Frame);
                    }
                for (int dy = -5; dy <= 2; dy++)
                    for (int dx = -3; dx <= 3; dx++)
                    {
                        float r = Mathf.Abs(dx) + Mathf.Abs(dy + 1) * (dy < -1 ? 0.62f : 1.1f);
                        if (r <= 2.4f) cv.Set(hx + dx, hy + dy - lift, r < 1.2f ? new Color32(255, 244, 190, 255) : Gold);
                    }
            }
            // more of the sheet above or below
            if (pan > 1) Arrow(ix + ox + IW - 11, iy + 4, true);
            if (pan < world.h - IH - 1) Arrow(ix + ox + IW - 11, iy + IH - 9, false);
        }

        void Arrow(int x, int y, bool up)
        {
            for (int r = 0; r < 4; r++)
            {
                int w = up ? r : 3 - r;
                cv.Rect(x - w - 1, y + r + 1, w * 2 + 3, 1, Sh);
                cv.Rect(x - w, y + r, w * 2 + 1, 1, Gold);
            }
        }
    }
}
