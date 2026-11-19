// On-screen controls for phones: a thumbstick on the left, five bronze-ringed buttons on the
// right (khopesh, roll, talk, nod off, Wakefire) and a pause button. They drive a virtual
// gamepad, so every other part of the game just sees a controller.
using UnityEngine;
using UnityEngine.EventSystems;
using UnityEngine.InputSystem.OnScreen;
using UnityEngine.InputSystem.UI;
using UnityEngine.UI;

namespace Wakefire
{
    public class TouchControls : MonoBehaviour
    {
        public static TouchControls I;
        RectTransform root;
        float lastH;

        public static bool Wanted => Application.isMobilePlatform || Boot.Flag("-touch") || UnityEngine.InputSystem.Touchscreen.current != null;

        public static void Create()
        {
            if (I || !Wanted) return;
            if (!EventSystem.current)
            {
                var es = new GameObject("EventSystem");
                DontDestroyOnLoad(es);
                es.AddComponent<EventSystem>();
                es.AddComponent<InputSystemUIInputModule>();
            }
            var go = new GameObject("TouchControls", typeof(RectTransform));
            go.transform.SetParent(PixelView.I.touchRoot, false);
            PixelView.Stretch((RectTransform)go.transform);
            I = go.AddComponent<TouchControls>();
            I.root = (RectTransform)go.transform;
            I.Build();
        }

        static Sprite Spr(string name)
        {
            var t = Resources.Load<Texture2D>("UI/Touch/" + name);
            t.filterMode = FilterMode.Point;
            return Sprite.Create(t, new Rect(0, 0, t.width, t.height), new Vector2(0.5f, 0.5f), 1f);
        }

        RectTransform Place(string name, Sprite s, Vector2 anchor, Vector2 posUnits, float scale)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(root, false);
            var img = go.AddComponent<Image>();
            img.sprite = s;
            img.color = new Color(1, 1, 1, 0.78f);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = anchor;
            rt.pivot = new Vector2(0.5f, 0.5f);
            float u = Screen.height / 216f;
            rt.sizeDelta = new Vector2(s.rect.width, s.rect.height) * u * scale;
            rt.anchoredPosition = posUnits * u;
            return rt;
        }

        void Build()
        {
            foreach (Transform c in root) Destroy(c.gameObject);
            lastH = Screen.height;
            float u = Screen.height / 216f;
            // the stick
            var bse = Place("StickBase", Spr("stick_base"), new Vector2(0, 0), new Vector2(46, 44), 1f);
            bse.GetComponent<Image>().raycastTarget = false;
            var knob = Place("Stick", Spr("stick_knob"), new Vector2(0, 0), new Vector2(46, 44), 1f);
            var st = knob.gameObject.AddComponent<OnScreenStick>();
            st.controlPath = "<Gamepad>/leftStick";
            st.movementRange = 20 * u;
            // the buttons, around the right thumb
            Button("Attack", "attack", "<Gamepad>/buttonWest", new Vector2(-44, 40), 1.15f);
            Button("Roll", "roll", "<Gamepad>/buttonEast", new Vector2(-22, 24), 1f);
            Button("Talk", "talk", "<Gamepad>/buttonSouth", new Vector2(-72, 22), 1f);
            Button("Nod", "nod", "<Gamepad>/buttonNorth", new Vector2(-28, 70), 1f);
            Button("Item", "item", "<Gamepad>/rightShoulder", new Vector2(-70, 66), 1f);
            var pause = Place("Pause", Spr("pause"), new Vector2(0.5f, 1), new Vector2(0, -16), 1f);
            pause.gameObject.AddComponent<OnScreenButton>().controlPath = "<Gamepad>/start";
        }

        void Button(string name, string icon, string path, Vector2 pos, float scale)
        {
            var rt = Place(name, Spr(icon), new Vector2(1, 0), pos, scale * 1.15f);
            rt.gameObject.AddComponent<OnScreenButton>().controlPath = path;
        }

        void Update()
        {
            if (Screen.height != lastH) Build();
            // keep out of the way of the title and of cutscenes
            bool show = !Title.I && !(Story.I && Story.I.Running && !(DialogueBox.I && DialogueBox.I.Busy));
            foreach (Transform c in root) c.gameObject.SetActive(show || c.name == "Talk" || c.name == "Attack");
        }
    }
}
