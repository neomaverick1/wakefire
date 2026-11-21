// When Azar falls the night closes over him, and the game asks where to pick up: at the way into
// the place he fell in, at the player's own save, or back at the title. Nothing is taken from him.
using System.Collections;
using UnityEngine;
using UnityEngine.UI;

namespace Wakefire
{
    public class Fallen : MonoBehaviour
    {
        public const int WakeHere = 0, LoadSave = 1, ToTitle = 2;
        public static int Choice;
        /// <summary>Test runs and the attract loop have nobody to choose: they wake where they fell.</summary>
        public static bool AutoPick;

        public static IEnumerator Ask(string map)
        {
            Choice = WakeHere;
            var go = new GameObject("Fallen", typeof(RectTransform));
            go.layer = PixelView.PixelUILayer;
            go.transform.SetParent(PixelView.I.pixelRoot, false);
            PixelView.Stretch((RectTransform)go.transform);
            var img = go.AddComponent<RawImage>();
            img.raycastTarget = false;
            var menu = new PanelMenu(img) { title = "The dark wins this round.", width = 214 };
            var saved = Save.ReadManual();
            menu.options = new[] { "Wake at " + Places.Name(map), "Load the saved game", "Back to the title" };
            menu.off = new[] { false, saved == null, false };
            var night = new Color32(6, 4, 12, 255);
            string Foot() => menu.sel == WakeHere ? "Full life. Everything you carry stays."
                : menu.sel == LoadSave ? (saved != null ? Save.Describe(saved) : "Nothing saved yet.")
                : "The game saves as you go.";
            menu.footer = Foot();
            menu.Draw(night);
            Fade.Set(0);                    // the panel has its own night behind it
            go.transform.SetAsLastSibling();
            yield return null;
            float t = 0;
            while (true)
            {
                t += Time.unscaledDeltaTime;
                int pick = menu.Poll();
                menu.footer = Foot();
                menu.Draw(night);
                if (pick < 0 && (AutoPick || DialogueBox.AutoAdvance > 0) && t > 1.2f) pick = WakeHere;
                if (pick >= 0) { Choice = pick; Sfx.Play("menu_ok", 0.7f, 0); break; }
                yield return null;
            }
            Fade.Set(1);
            Destroy(go);
            yield return null;
        }
    }
}
