// When Azar falls the night closes over him, and the game asks where to pick up: at the way into
// the place he fell in, at what one of the three journeys last saved, or back at the title.
// Nothing is taken from him.
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

        /// <summary>Which journey to go back to, when that was the choice.</summary>
        public static int Slot;

        public static IEnumerator Ask(string map)
        {
            Choice = WakeHere;
            Slot = Save.Slot;
            var go = new GameObject("Fallen", typeof(RectTransform));
            go.layer = PixelView.PixelUILayer;
            go.transform.SetParent(PixelView.I.pixelRoot, false);
            PixelView.Stretch((RectTransform)go.transform);
            var img = go.AddComponent<RawImage>();
            img.raycastTarget = false;
            var menu = new PanelMenu(img) { title = "The dark wins this round.", width = 214 };
            var night = new Color32(6, 4, 12, 255);
            Fade.Set(0);                    // the panel has its own night behind it
            go.transform.SetAsLastSibling();
            bool picking = false;           // the second list: which of the three journeys
            void Top()
            {
                picking = false;
                menu.title = "The dark wins this round.";
                menu.options = new[] { "Wake at " + Places.Name(map), "Load a saved journey", "Back to the title" };
                menu.off = new[] { false, !Save.Any, false };
                menu.sel = 0;
            }
            void Journeys()
            {
                picking = true;
                menu.title = "Go back to which journey?";
                var o = new string[Save.Slots + 1]; var off = new bool[Save.Slots + 1];
                for (int i = 0; i < Save.Slots; i++)
                {
                    var d = Save.Read(i);
                    o[i] = (i + 1) + ":  " + (d != null ? Save.Describe(d) : "empty");
                    off[i] = d == null;
                }
                o[Save.Slots] = "Never mind";
                menu.options = o; menu.off = off;
                menu.sel = Save.Has(Save.Slot) ? Save.Slot : Save.Slots;
            }
            string Foot() => picking ? (menu.sel < Save.Slots && Save.Has(menu.sel) ? Save.Chapter(Save.Read(menu.sel), false) : "")
                : menu.sel == WakeHere ? "Full life. Everything you carry stays."
                : menu.sel == LoadSave ? (Save.Any ? "Pick one of the three." : "Nothing saved yet.")
                : "The game saves as you go.";
            Top();
            menu.footer = Foot();
            menu.Draw(night);
            yield return null;
            float t = 0;
            while (true)
            {
                t += Time.unscaledDeltaTime;
                int pick = menu.Poll();
                menu.footer = Foot();
                menu.Draw(night);
                if (pick < 0 && !picking && (AutoPick || DialogueBox.AutoAdvance > 0) && t > 1.2f) pick = WakeHere;
                if (pick >= 0)
                {
                    Sfx.Play("menu_ok", 0.7f, 0);
                    if (picking)
                    {
                        if (pick < Save.Slots) { Choice = LoadSave; Slot = pick; break; }
                        Top();
                    }
                    else if (pick == LoadSave) Journeys();
                    else { Choice = pick; break; }
                }
                else if (picking && Controls.Down(Controls.Back)) Top();
                yield return null;
            }
            Fade.Set(1);
            Destroy(go);
            yield return null;
        }
    }
}
