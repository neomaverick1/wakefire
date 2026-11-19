// The HUD in render pixels, laid out like the classic games: the Drowsiness meter where the
// magic meter sits, the item box, coin and key counters, and LIFE as a row of flames.
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.UI;

namespace Wakefire
{
    public class Hud : MonoBehaviour
    {
        public static Hud I;
        RectTransform root;
        Image meterFill;
        readonly List<Image> flames = new List<Image>();
        Image[] coinDigits, keyDigits;
        Sprite[] digits;
        Sprite flameFull, flameEmpty;
        Image item;
        int shownLife = -1, shownMax = -1, shownCoins = -1, shownKeys = -1;

        public static Sprite UISprite(string name)
        {
            var t = Resources.Load<Texture2D>("UI/" + name);
            if (!t) return null;
            t.filterMode = FilterMode.Point;
            return Sprite.Create(t, new Rect(0, 0, t.width, t.height), new Vector2(0, 1), 1f);
        }

        public static Image Pixel(Transform parent, Sprite s, float x, float y, string name = "img")
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.layer = PixelView.PixelUILayer;
            go.transform.SetParent(parent, false);
            var img = go.AddComponent<Image>();
            img.sprite = s;
            img.raycastTarget = false;
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(0, 1);
            rt.pivot = new Vector2(0, 1);
            rt.sizeDelta = s ? new Vector2(s.rect.width, s.rect.height) : Vector2.one;
            rt.anchoredPosition = new Vector2(x, -y);
            return img;
        }

        public static Hud Create()
        {
            var go = new GameObject("Hud", typeof(RectTransform));
            go.layer = PixelView.PixelUILayer;
            go.transform.SetParent(PixelView.I.pixelRoot, false);
            PixelView.Stretch((RectTransform)go.transform);
            I = go.AddComponent<Hud>();
            I.Build();
            return I;
        }

        void Build()
        {
            root = (RectTransform)transform;
            digits = new Sprite[10];
            for (int i = 0; i < 10; i++) digits[i] = UISprite("digit_" + i);
            flameFull = UISprite("life_full");
            flameEmpty = UISprite("life_empty");
            Pixel(root, UISprite("meter"), 7, 5, "meter");
            var fillGo = new GameObject("fill", typeof(RectTransform));
            fillGo.layer = PixelView.PixelUILayer;
            fillGo.transform.SetParent(root, false);
            meterFill = fillGo.AddComponent<Image>();
            meterFill.color = new Color(0.31f, 0.47f, 0.82f);
            var frt = (RectTransform)fillGo.transform;
            frt.anchorMin = frt.anchorMax = new Vector2(0, 1);
            frt.pivot = new Vector2(0, 0);
            frt.anchoredPosition = new Vector2(11, -35);
            frt.sizeDelta = new Vector2(4, 24);
            Pixel(root, UISprite("itembox"), 22, 6, "itembox");
            item = Pixel(root, UISprite("icon_lantern"), 27, 10, "item");
            Pixel(root, UISprite("coin"), 50, 5, "coin");
            coinDigits = new[] { Pixel(root, digits[0], 48, 14), Pixel(root, digits[0], 54, 14), Pixel(root, digits[0], 60, 14) };
            Pixel(root, UISprite("key"), 76, 4, "key");
            keyDigits = new[] { Pixel(root, digits[0], 74, 14), Pixel(root, digits[0], 80, 14) };
        }

        void Layout(int max)
        {
            foreach (var f in flames) if (f) Destroy(f.gameObject);
            flames.Clear();
            var label = transform.Find("life_label");
            if (label) Destroy(label.gameObject);
            int n = max / 2;
            float W = PixelView.I.width;
            float x0 = W - 10 - 12 * n;
            Pixel(root, UISprite("life_label"), x0 - 6, 3, "life_label");
            for (int i = 0; i < n; i++) flames.Add(Pixel(root, flameFull, x0 + i * 12, 13, "flame"));
        }

        void Update()
        {
            var p = Player.I;
            if (!p) return;
            var h = p.health;
            if (h.max != shownMax) { Layout(h.max); shownMax = h.max; shownLife = -1; }
            if (h.hp != shownLife)
            {
                for (int i = 0; i < flames.Count; i++)
                {
                    bool full = h.hp >= (i + 1) * 2 || h.hp == i * 2 + 1;
                    flames[i].sprite = full ? flameFull : flameEmpty;
                    flames[i].color = h.hp == i * 2 + 1 ? new Color(1, 1, 1, 1) : Color.white;
                }
                shownLife = h.hp;
            }
            if (p.coins != shownCoins)
            {
                int c = Mathf.Clamp(p.coins, 0, 999);
                coinDigits[0].sprite = digits[c / 100]; coinDigits[1].sprite = digits[(c / 10) % 10]; coinDigits[2].sprite = digits[c % 10];
                shownCoins = p.coins;
            }
            if (p.keys != shownKeys)
            {
                int k = Mathf.Clamp(p.keys, 0, 99);
                keyDigits[0].sprite = digits[k / 10]; keyDigits[1].sprite = digits[k % 10];
                shownKeys = p.keys;
            }
            float lvl = Dream.I ? Dream.I.Drowsiness : 1;
            var frt = meterFill.rectTransform;
            frt.sizeDelta = new Vector2(4, Mathf.Round(24 * lvl));
            meterFill.color = Dream.I && Dream.I.Dreaming ? new Color(0.95f, 0.75f, 0.32f) : new Color(0.31f, 0.47f, 0.82f);
        }
    }
}
