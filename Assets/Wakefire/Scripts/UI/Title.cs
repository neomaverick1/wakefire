// The title screen: Ashkel asleep under the moon, the logo, and the three journeys. Pick one that
// has been begun to carry on with it, or an empty one to begin; "Rub one out" clears a journey for
// good, after asking. Keyboard, pad or a tap on a line all work.
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.UI;

namespace Wakefire
{
    public class Title : MonoBehaviour
    {
        public static Title I;
        RawImage bg, logo, menuImg, hero;
        int heroFrames = 1;
        SpriteAnim heroAnim;                 // Azar himself on the roof, when he has a model
        GameObject heroHost;
        Material heroMat;

        [System.Serializable] class HeroInfo { public int frames, w, h, x, y; }
        PixelCanvas menu;
        int sel;                    // 0..2 the journeys, 3 the line under them
        float clock;
        bool leaving;
        int off;
        enum Mode { Pick, Erase, Sure }
        Mode mode;
        int target, sureSel;        // which journey is about to go, and whether "rub it out" is lit
        const int RowW = 204, Row0 = 13, RowStep = 18, LineY = 70;

        public static void Show()
        {
            if (I) return;
            var go = new GameObject("Title", typeof(RectTransform));
            go.layer = PixelView.PixelUILayer;
            go.transform.SetParent(PixelView.I.pixelRoot, false);
            PixelView.Stretch((RectTransform)go.transform);
            I = go.AddComponent<Title>();
            I.Build();
            Music.Play("title");
            // coming back to the title mid-journey: the world behind it stands still until a game begins again
            if (Player.I)
            {
                Player.I.SetState(Player.State.Cutscene);
                Player.I.health.invulnerable = 1e9f;
                foreach (var e in Enemy.All.ToArray()) if (e) Destroy(e.gameObject);
            }
        }

        RawImage Img(string name, Texture t, float x, float y)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.layer = PixelView.PixelUILayer;
            go.transform.SetParent(transform, false);
            var img = go.AddComponent<RawImage>();
            img.raycastTarget = false;
            img.texture = t;
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(0, 1);
            rt.pivot = new Vector2(0, 1);
            rt.sizeDelta = new Vector2(t.width, t.height);
            rt.anchoredPosition = new Vector2(x, -y);
            return img;
        }

        void Build()
        {
            int W = PixelView.I.width, H = PixelView.Height;
            off = (H - 216) / 2;
            var bgt = Resources.Load<Texture2D>("UI/title_bg");
            bgt.filterMode = FilterMode.Point;
            bg = Img("bg", bgt, Mathf.Round((W - bgt.width) / 2f), H - bgt.height);
            // Azar on a roof in the foreground, cape and crest moving in the night wind
            var ht = Resources.Load<Texture2D>("UI/title_hero");
            var hj = Resources.Load<TextAsset>("UI/title_hero");
            if (hj && ModelDefs.For("azar_title") != null)
            {
                // the real Azar stands there, posed on the model stage, his cape in the night wind
                var hi = JsonUtility.FromJson<HeroInfo>(hj.text);
                heroHost = new GameObject("TitleAzar");
                var body = new GameObject("Sprite");
                body.transform.SetParent(heroHost.transform, false);
                var sr = body.AddComponent<SpriteRenderer>();
                sr.sharedMaterial = Map.SpriteMat;
                sr.enabled = false;
                heroAnim = body.AddComponent<SpriteAnim>();
                heroAnim.sr = sr;
                heroAnim.modelAs = "azar_title";
                heroAnim.sheet = SpriteSheet.Load("azar");
                heroAnim.Play("idle", Facing.Right, true);
                if (heroAnim.model)
                {
                    heroAnim.model.ownVelocity = true;
                    heroAnim.model.velocity = new Vector2(2.6f, 0.4f);
                    heroAnim.model.Aim(new Vector2(1f, 0.45f), true);
                }
                float feetX = Mathf.Max(44f, Mathf.Round((W - bgt.width) / 2f) + hi.x + hi.w * 0.5f), feetY = H - bgt.height + hi.y + hi.h;
                int cell = ModelStage.Cell * 2, feet = ModelStage.FeetPx * 2;
                hero = Img("hero", Texture2D.whiteTexture, feetX - cell * 0.5f, feetY - (cell - feet));
                ((RectTransform)hero.transform).sizeDelta = new Vector2(cell, cell);
                heroMat = new Material(Map.SpriteMat);
                heroMat.SetFloat("_Model", 1f);
                hero.material = heroMat;
            }
            else if (ht && hj)
            {
                var hi = JsonUtility.FromJson<HeroInfo>(hj.text);
                ht.filterMode = FilterMode.Point;
                heroFrames = Mathf.Max(1, hi.frames);
                hero = Img("hero", ht, Mathf.Round((W - bgt.width) / 2f) + hi.x, H - bgt.height + hi.y);
                ((RectTransform)hero.transform).sizeDelta = new Vector2(hi.w, hi.h);
                hero.uvRect = new Rect(0, 0, 1f / heroFrames, 1);
            }
            var lt = Resources.Load<Texture2D>("UI/title_logo");
            lt.filterMode = FilterMode.Point;
            logo = Img("logo", lt, Mathf.Round((W - lt.width) / 2f), Mathf.Max(3, 18 + off));
            sel = Save.Slot;
            menu = new PixelCanvas(W, 96);
            menuImg = Img("menu", menu.tex, 0, 96 + off);
            Redraw();
        }

        /// <summary>Test runs choose through here: "1", "2" or "3" picks that journey (carrying on or
        /// beginning, as it stands), "erase 2" rubs the second one out, "Continue" picks the journey last
        /// played and "New Game" the first empty one.</summary>
        public static string TestPick;
        /// <summary>What the screen is offering, line by line (for test runs).</summary>
        public string[] Lines
        {
            get
            {
                var l = new System.Collections.Generic.List<string>();
                for (int i = 0; i < Save.Slots; i++) l.Add((i + 1) + " " + (Save.Has(i) ? Save.Describe(Save.Read(i)) : "Begin a new journey"));
                l.Add(LastLine());
                return l.ToArray();
            }
        }

        string LastLine() => mode == Mode.Pick ? (Save.Any ? "Rub one out" : "") : mode == Mode.Erase ? "Never mind" : "";

        void Redraw()
        {
            var f = PixelFont.Main;
            menu.Clear(new Color32(0, 0, 0, 0));
            var gold = new Color32(246, 200, 90, 255);
            var ink = new Color32(244, 234, 216, 255);
            var sh = new Color32(6, 4, 12, 255);
            var soft = new Color32(196, 188, 214, 255);
            var red = new Color32(240, 110, 80, 255);
            // every loose line is cut out of the picture behind it with a dark edge all round, so it reads over anything
            void Line(string t, int y, Color32 col, int cx = -1)
            {
                int x = (cx < 0 ? menu.W / 2 : cx) - f.Measure(t) / 2;
                for (int ox = -1; ox <= 1; ox++)
                    for (int oy = -1; oy <= 2; oy++)
                        if (ox != 0 || oy != 0) f.DrawString(menu, x + ox, y + oy, t, sh);
                f.DrawString(menu, x, y, t, col);
            }
            int at = Mathf.Min(sel, Save.Slots - 1);
            string head = mode == Mode.Erase ? "Rub out which journey?" : mode == Mode.Sure ? "Journey " + (target + 1) + " will be gone for good."
                        : Save.Chapter(Save.Read(mode == Mode.Sure ? target : at));
            Line(head, 1, mode == Mode.Pick ? soft : red);
            int x0 = (menu.W - RowW) / 2;
            for (int i = 0; i < Save.Slots; i++)
            {
                bool on = mode == Mode.Sure ? i == target : i == sel;
                SlotRow.Draw(menu, x0, Row0 + i * RowStep, RowW, i, on, false, clock, compact: true, danger: on && mode != Mode.Pick);
            }
            if (mode == Mode.Sure)
            {
                Line("Keep it", LineY + 2, sureSel == 0 ? gold : ink, menu.W / 2 - 44);
                Line("Rub it out", LineY + 2, sureSel == 1 ? red : ink, menu.W / 2 + 44);
                int cx = menu.W / 2 + (sureSel == 0 ? -44 : 44), tw = f.Measure(sureSel == 0 ? "Keep it" : "Rub it out");
                if (((int)(clock * 2.5f)) % 2 == 0)
                {
                    f.Draw(menu, cx - tw / 2 - 10, LineY + 2, '>', gold, sh);
                    f.Draw(menu, cx + tw / 2 + 5, LineY + 2, '<', gold, sh);
                }
            }
            else
            {
                string last = LastLine();
                if (last != "")
                {
                    Line(last, LineY, sel == Save.Slots ? gold : soft);
                    if (sel == Save.Slots && ((int)(clock * 2.5f)) % 2 == 0)
                    {
                        int tw = f.Measure(last);
                        f.Draw(menu, menu.W / 2 - tw / 2 - 12, LineY, '>', gold, sh);
                        f.Draw(menu, menu.W / 2 + tw / 2 + 6, LineY, '<', gold, sh);
                    }
                }
                Line("Randy Kundinger 2026", 84, soft);
            }
            menu.Apply();
        }

        void Update()
        {
            if (leaving) return;
            clock += Time.unscaledDeltaTime;
            if (heroAnim)
            {
                heroHost.transform.position = (Vector2)PixelView.I.world.transform.position;      // "in view", so the stage keeps posing him
                heroAnim.Tick(Time.unscaledDeltaTime);
                if (heroAnim.model) heroMat.SetVector("_Cell", heroAnim.model.Cell);
            }
            else if (hero) hero.uvRect = new Rect(((int)(clock * 5f) % heroFrames) / (float)heroFrames, 0, 1f / heroFrames, 1);
            if (TestPick != null)
            {
                string tp0 = TestPick; TestPick = null;
                if (tp0.StartsWith("erase ")) { Save.Erase(int.Parse(tp0.Substring(6)) - 1); mode = Mode.Pick; Redraw(); return; }
                int pick = tp0 == "Continue" ? (Save.Has(Save.Slot) ? Save.Slot : FirstWith(true)) : tp0 == "New Game" || tp0 == "Begin" ? FirstWith(false)
                         : int.TryParse(tp0, out int n) ? n - 1 : -1;
                if (pick >= 0 && pick < Save.Slots) { sel = pick; mode = Mode.Pick; Choose(); return; }
            }
            int last = LastLine() != "" ? Save.Slots : Save.Slots - 1;
            var step = Controls.Step();
            int before = sel, sureBefore = sureSel;
            if (mode == Mode.Sure) { if (step != Vector2Int.zero) sureSel = 1 - sureSel; }
            else if (step.y != 0) sel = Mathf.Clamp(sel - step.y, 0, last);
            // a tap on a line picks it
            var tp = Pointer.current;
            if (tp != null && tp.press.wasPressedThisFrame)
            {
                var pos = tp.position.ReadValue();
                float k = PixelView.I.ScreenScale;
                float pxl = pos.x / k, py = PixelView.Height - pos.y / k - (96 + off);   // render pixels, from the top of the list
                if (mode == Mode.Sure)
                {
                    if (py >= LineY - 4 && py < LineY + 16) { sureSel = pxl < menu.W / 2 ? 0 : 1; Choose(); return; }
                }
                else
                {
                    for (int i = 0; i < Save.Slots; i++)
                        if (py >= Row0 + i * RowStep && py < Row0 + i * RowStep + SlotRow.Short && Mathf.Abs(pxl - menu.W / 2) < RowW / 2) { sel = i; Choose(); return; }
                    if (last == Save.Slots && py >= LineY - 4 && py < LineY + 13 && Mathf.Abs(pxl - menu.W / 2) < 60) { sel = Save.Slots; Choose(); return; }
                }
                Redraw();
                return;         // a tap that lands on nothing chooses nothing
            }
            if (before != sel || sureBefore != sureSel) Sfx.Play("menu_move", 0.6f, 0);
            Redraw();
            if (Controls.Down(Controls.Back) && mode != Mode.Pick) { mode = Mode.Pick; sel = Mathf.Min(sel, last); Sfx.Play("menu_move", 0.6f, 0); return; }
            if (Controls.Down(Controls.Confirm) || Controls.Down(Controls.Interact)) Choose();
        }

        static int FirstWith(bool saved)
        {
            for (int i = 0; i < Save.Slots; i++) if (Save.Has(i) == saved) return i;
            return saved ? -1 : Save.Slot;
        }

        void Choose()
        {
            Sfx.Play("menu_ok", 0.8f, 0);
            switch (mode)
            {
                case Mode.Pick:
                    if (sel == Save.Slots) { mode = Mode.Erase; sel = Mathf.Max(0, FirstWith(true)); Redraw(); return; }
                    leaving = true;
                    StartCoroutine(Leave(sel));
                    return;
                case Mode.Erase:
                    if (sel == Save.Slots) { mode = Mode.Pick; sel = Save.Slot; Redraw(); return; }
                    if (!Save.Has(sel)) { Sfx.Play("deny", 0.6f, 0); return; }
                    target = sel; sureSel = 0; mode = Mode.Sure; Redraw();
                    return;
                default:
                    if (sureSel == 1) { Save.Erase(target); Sfx.Play("pot_break", 0.5f, 0); }
                    mode = Mode.Pick; sel = target; Redraw();
                    return;
            }
        }

        System.Collections.IEnumerator Leave(int slot)
        {
            yield return Fade.Out(0.5f);
            Save.Use(slot);
            var from = Save.Read(slot);
            if (heroHost) Destroy(heroHost);
            Destroy(gameObject);
            I = null;
            Game.I.Begin(from);
            if (from != null)
            {
                Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn, quiet: true);
                yield return Fade.In(0.4f);
            }
        }
    }
}
