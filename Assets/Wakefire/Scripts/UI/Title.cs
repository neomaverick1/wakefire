// The title screen: Ashkel asleep under the moon, the logo, and the choice to carry on or begin
// again. Keyboard, pad or a tap on the words all work.
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
        string[] options;
        int sel;
        float clock;
        bool leaving;
        int off;

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
            options = MakeOptions();
            menu = new PixelCanvas(W, 96);
            menuImg = Img("menu", menu.tex, 0, 96 + off);
            Redraw();
        }

        bool sure;          // New Game asked once already
        /// <summary>Test runs choose a line by its first words through here.</summary>
        public static string TestPick;
        public string[] Lines => options;

        string[] MakeOptions()
        {
            var o = new System.Collections.Generic.List<string>();
            if (Save.Exists) o.Add("Continue");
            if (Save.HasManual) o.Add("Load game");
            o.Add(o.Count == 0 ? "Begin" : sure ? "New Game: sure?" : "New Game");
            return o.ToArray();
        }

        /// <summary>Under the list: what the chosen line would bring back.</summary>
        string Hint()
        {
            string s = options[sel];
            if (s == "Continue") return Save.Describe(Save.Read());
            if (s == "Load game") return Save.Describe(Save.ReadManual());
            if (s.StartsWith("New Game: sure")) return "Continue would be lost. Your save stays.";
            return "";
        }

        void Redraw()
        {
            var f = PixelFont.Main;
            menu.Clear(new Color32(0, 0, 0, 0));
            var gold = new Color32(246, 200, 90, 255);
            var ink = new Color32(244, 234, 216, 255);
            var dim = new Color32(150, 140, 170, 255);
            var sh = new Color32(6, 4, 12, 255);
            // every line is cut out of the picture behind it with a dark edge all round, so it reads over anything
            void Line(string t, int y, Color32 col)
            {
                int x = (menu.W - f.Measure(t)) / 2;
                for (int ox = -1; ox <= 1; ox++)
                    for (int oy = -1; oy <= 2; oy++)
                        if (ox != 0 || oy != 0) f.DrawString(menu, x + ox, y + oy, t, sh);
                f.DrawString(menu, x, y, t, col);
            }
            var soft = new Color32(196, 188, 214, 255);
            Line("Chapter One: The Sleeping God", 1, soft);
            for (int i = 0; i < options.Length; i++)
            {
                string s = options[i];
                int x = (menu.W - f.Measure(s)) / 2, y = 22 + i * 14;
                Line(s, y, i == sel ? gold : ink);
                if (i == sel && ((int)(clock * 2.5f)) % 2 == 0)
                {
                    f.Draw(menu, x - 12, y, '>', gold, sh);
                    f.Draw(menu, x + f.Measure(s) + 6, y, '<', gold, sh);
                }
            }
            string hint = Hint();
            if (hint != "") Line(hint, 24 + options.Length * 14, soft);
            Line("Randy Kundinger 2026", 82, soft);
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
                int ti = System.Array.FindIndex(options, o => o.StartsWith(TestPick));
                TestPick = null;
                if (ti >= 0) { if (ti != sel) { sel = ti; sure = false; options = MakeOptions(); } Choose(); return; }
            }
            var mv = Controls.MoveVector;
            int before = sel;
            if (Controls.Move.WasPerformedThisFrame() || Keyboard.current != null && (Keyboard.current.upArrowKey.wasPressedThisFrame || Keyboard.current.downArrowKey.wasPressedThisFrame))
            {
                if (mv.y > 0.5f) sel = Mathf.Max(0, sel - 1);
                if (mv.y < -0.5f) sel = Mathf.Min(options.Length - 1, sel + 1);
            }
            // a tap on a word picks it
            var tp = Pointer.current;
            if (tp != null && tp.press.wasPressedThisFrame)
            {
                var pos = tp.position.ReadValue();
                float py = PixelView.Height - pos.y / PixelView.I.ScreenScale;   // render pixels from the top
                for (int i = 0; i < options.Length; i++)
                    if (Mathf.Abs(py - (96 + off + 22 + i * 14 + 4)) < 7)
                    {
                        if (i != sel) { sel = i; sure = false; options = MakeOptions(); }
                        Choose(); return;
                    }
            }
            if (before != sel) { Sfx.Play("menu_move", 0.6f, 0); if (sure) { sure = false; options = MakeOptions(); } }
            Redraw();
            if (Controls.Down(Controls.Confirm) || Controls.Down(Controls.Interact)) Choose();
        }

        void Choose()
        {
            string s = options[sel];
            Sfx.Play("menu_ok", 0.8f, 0);
            // starting over wipes the journey so far: ask once
            if (s == "New Game" && Save.Exists) { sure = true; options = MakeOptions(); Redraw(); return; }
            leaving = true;
            StartCoroutine(Leave(s == "Continue" ? Save.Read() : s == "Load game" ? Save.ReadManual() : null));
        }

        System.Collections.IEnumerator Leave(SaveData from)
        {
            yield return Fade.Out(0.5f);
            if (from == null) Save.Clear();
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
