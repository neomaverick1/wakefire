// Two quiet things the screen says without stopping the game: the name of a place as Azar walks
// into it (gold, between two bronze rules, top centre), and "Saved" with a small flame when the
// game has saved by itself (under the LIFE flames).
using UnityEngine;
using UnityEngine.UI;

namespace Wakefire
{
    public class Notices : MonoBehaviour
    {
        static Notices I;
        RawImage placeImg, savedImg;
        PixelCanvas place, saved;
        float placeT = 99, savedT = 99;
        const float PlaceHold = 2.6f, SavedHold = 1.9f;
        static readonly Color32 Gold = new Color32(246, 200, 90, 255), Ink = new Color32(244, 234, 216, 255), Night = new Color32(6, 4, 12, 255),
            Bronze = new Color32(188, 122, 52, 255), BronzeL = new Color32(255, 216, 138, 255), Clear = new Color32(0, 0, 0, 0);

        static Notices Ensure()
        {
            if (I) return I;
            var go = new GameObject("Notices", typeof(RectTransform));
            go.layer = PixelView.PixelUILayer;
            go.transform.SetParent(PixelView.I.pixelRoot, false);
            PixelView.Stretch((RectTransform)go.transform);
            I = go.AddComponent<Notices>();
            I.placeImg = Img(go.transform, "place");
            I.savedImg = Img(go.transform, "saved");
            Save.Saved += () => { if (I) I.ShowSaved(); };
            return I;
        }

        static RawImage Img(Transform parent, string name)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.layer = PixelView.PixelUILayer;
            go.transform.SetParent(parent, false);
            var img = go.AddComponent<RawImage>();
            img.raycastTarget = false;
            img.enabled = false;
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = new Vector2(0, 1);
            rt.pivot = new Vector2(0, 1);
            return img;
        }

        public static void Boot() => Ensure();

        /// <summary>Walking into a place: its name comes up for a moment.</summary>
        public static void Place(string map) => Banner(Places.Name(map));

        /// <summary>...and for a room that is on no plan, the first time he stands in it.</summary>
        public static void Room(string name) => Banner(name);

        /// <summary>The same banner for the turn of a chapter: "Chapter One: The Sleeping God".</summary>
        public static void Chapter(string number, string name) => Banner(number + ": " + name);

        static void Banner(string s)
        {
            var n = Ensure();
            var f = PixelFont.Main;
            int tw = f.Measure(s), w = tw + 56, h = f.Line + 6;
            n.place = new PixelCanvas(w, h);
            n.place.Clear(Clear);
            int ty = 2;
            for (int ox = -1; ox <= 1; ox++)
                for (int oy = -1; oy <= 1; oy++)
                    if (ox != 0 || oy != 0) f.DrawString(n.place, 28 + ox, ty + oy, s, Night);
            f.DrawString(n.place, 28, ty, s, Gold);
            // a bronze rule each side, ending in a stud
            int ry = ty + f.Line / 2 - 1;
            foreach (var (x0, x1, stud) in new[] { (2, 22, 2), (w - 23, w - 3, w - 4) })
            {
                n.place.Rect(x0 - 1, ry - 1, x1 - x0 + 2, 3, Night);
                n.place.HLine(x0, ry, x1 - x0, Bronze);
                n.place.Rect(stud - 1, ry - 2, 4, 5, Night);
                n.place.Rect(stud, ry - 1, 2, 3, BronzeL);
            }
            n.place.Apply();
            n.placeImg.texture = n.place.tex;
            n.placeImg.rectTransform.sizeDelta = new Vector2(w, h);
            n.placeT = 0;
        }

        void ShowSaved()
        {
            var f = PixelFont.Main;
            const string s = "Saved";
            int w = f.Measure(s) + 14, h = f.Line + 4;
            saved = new PixelCanvas(w, h);
            saved.Clear(Clear);
            // a small flame: the Wakefire keeps the place
            int fx = 3, fy = 2;
            var flame = new[] { "..1..", ".121.", ".121.", "12321", "12321", ".121." };
            var cols = new[] { Clear, new Color32(214, 96, 40, 255), new Color32(246, 176, 64, 255), new Color32(255, 240, 180, 255) };
            for (int y = 0; y < flame.Length; y++)
                for (int x = 0; x < 5; x++)
                    if (flame[y][x] != '.')
                    {
                        for (int ox = -1; ox <= 1; ox++) for (int oy = -1; oy <= 1; oy++) if (saved.Get(fx + x + ox, fy + y + oy).a == 0) saved.Set(fx + x + ox, fy + y + oy, Night);
                    }
            for (int y = 0; y < flame.Length; y++)
                for (int x = 0; x < 5; x++)
                    if (flame[y][x] != '.') saved.Set(fx + x, fy + y, cols[flame[y][x] - '0']);
            for (int ox = -1; ox <= 1; ox++)
                for (int oy = -1; oy <= 1; oy++)
                    if (ox != 0 || oy != 0) f.DrawString(saved, 12 + ox, 2 + oy, s, Night);
            f.DrawString(saved, 12, 2, s, Ink);
            saved.Apply();
            savedImg.texture = saved.tex;
            savedImg.rectTransform.sizeDelta = new Vector2(w, h);
            savedT = 0;
        }

        static float Curve(float t, float hold) => t < 0.25f ? t / 0.25f : t < hold ? 1 : Mathf.Clamp01(1 - (t - hold) / 0.5f);

        void LateUpdate()
        {
            float dt = Time.unscaledDeltaTime;
            int W = PixelView.I.width;
            var sa = PixelView.I.safe;
            bool quiet = Title.I || Game.Paused || (Story.I && Story.I.Running) || !Player.I;
            if (placeT < PlaceHold + 0.6f)
            {
                // a scene or a text box has the screen: the name waits its turn
                if (!quiet || placeT > 0) placeT += dt;
                float a = quiet ? 0 : Curve(placeT, PlaceHold);
                placeImg.enabled = a > 0;
                placeImg.color = new Color(1, 1, 1, a);
                placeImg.rectTransform.anchoredPosition = new Vector2(Mathf.Round((W - place.W) / 2f), -(30 + sa.height));
            }
            else placeImg.enabled = false;
            if (savedT < SavedHold + 0.6f)
            {
                savedT += dt;
                float a = Title.I || Game.Paused ? 0 : Curve(savedT, SavedHold);
                savedImg.enabled = a > 0;
                savedImg.color = new Color(1, 1, 1, a);
                savedImg.rectTransform.anchoredPosition = new Vector2(W - sa.width - saved.W - 6, -(30 + sa.height));
            }
            else savedImg.enabled = false;
        }
    }
}
