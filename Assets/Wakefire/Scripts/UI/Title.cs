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
            if (ht && hj)
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
            logo = Img("logo", lt, Mathf.Round((W - lt.width) / 2f), 18 + off);
            options = Save.Exists ? new[] { "Continue", "New Game" } : new[] { "Begin" };
            menu = new PixelCanvas(W, 80);
            menuImg = Img("menu", menu.tex, 0, 96 + off);
            Redraw();
        }

        void Redraw()
        {
            var f = PixelFont.Main;
            menu.Clear(new Color32(0, 0, 0, 0));
            var gold = new Color32(246, 200, 90, 255);
            var ink = new Color32(244, 234, 216, 255);
            var dim = new Color32(150, 140, 170, 255);
            var sh = new Color32(6, 4, 12, 255);
            string sub = "Chapter One: The Sleeping God";
            f.DrawString(menu, (menu.W - f.Measure(sub)) / 2, 0, sub, dim, sh);
            for (int i = 0; i < options.Length; i++)
            {
                string s = options[i];
                int x = (menu.W - f.Measure(s)) / 2, y = 22 + i * 14;
                f.DrawString(menu, x, y, s, i == sel ? gold : ink, sh);
                if (i == sel && ((int)(clock * 2.5f)) % 2 == 0)
                {
                    f.Draw(menu, x - 12, y, '>', gold, sh);
                    f.Draw(menu, x + f.Measure(s) + 6, y, '<', gold, sh);
                }
            }
            string c = "Randy Kundinger 2026";
            f.DrawString(menu, (menu.W - f.Measure(c)) / 2, 68, c, dim, sh);
            menu.Apply();
        }

        void Update()
        {
            if (leaving) return;
            clock += Time.unscaledDeltaTime;
            if (hero) hero.uvRect = new Rect(((int)(clock * 5f) % heroFrames) / (float)heroFrames, 0, 1f / heroFrames, 1);
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
                    if (Mathf.Abs(py - (96 + off + 22 + i * 14 + 4)) < 7) { sel = i; Choose(); return; }
            }
            if (before != sel) Sfx.Play("menu_move", 0.6f, 0);
            Redraw();
            if (Controls.Down(Controls.Confirm) || Controls.Down(Controls.Interact)) Choose();
        }

        void Choose()
        {
            leaving = true;
            Sfx.Play("menu_ok", 0.8f, 0);
            StartCoroutine(Leave(options[sel] == "Continue"));
        }

        System.Collections.IEnumerator Leave(bool resume)
        {
            yield return Fade.Out(0.5f);
            if (!resume) Save.Clear();
            Destroy(gameObject);
            I = null;
            Game.I.Begin(resume);
            if (resume) yield return Fade.In(0.4f);
        }
    }
}
