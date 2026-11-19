// On-screen controls for phones: a floating thumbstick on the left (it appears wherever the thumb
// lands), the khopesh button under the right thumb with roll, talk, the Wakefire and nod off in an
// arc around it, and a pause button. They drive a virtual gamepad, so every other part of the game
// just sees a controller.
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
        Rect lastSafe;

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

        RectTransform Place(string name, Sprite s, Vector2 anchor, Vector2 posUnits, float scale, Transform parent = null)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent ? parent : root, false);
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
            // keep thumbs clear of notches, rounded corners and the home bar
            var sa = lastSafe = Screen.safeArea;
            root.offsetMin = new Vector2(sa.xMin, sa.yMin);
            root.offsetMax = new Vector2(sa.xMax - Screen.width, sa.yMax - Screen.height);
            float u = Screen.height / 216f;
            // the stick floats: press anywhere on the left of the screen and it appears under the thumb
            var zgo = new GameObject("StickZone", typeof(RectTransform));
            zgo.transform.SetParent(root, false);
            var zone = (RectTransform)zgo.transform;
            zone.anchorMin = Vector2.zero; zone.anchorMax = new Vector2(0.46f, 0.74f);
            zone.pivot = Vector2.zero; zone.offsetMin = zone.offsetMax = Vector2.zero;
            zgo.AddComponent<Image>().color = new Color(0, 0, 0, 0);
            var ring = Place("StickBase", Spr("stick_base"), Vector2.zero, new Vector2(48, 46), 1f, zone);
            var knob = Place("Stick", Spr("stick_knob"), Vector2.zero, new Vector2(48, 46), 1f, zone);
            ring.GetComponent<Image>().raycastTarget = knob.GetComponent<Image>().raycastTarget = false;
            zgo.AddComponent<FloatStick>().Init(zone, ring, knob, 20 * u);
            // the buttons: the khopesh under the thumb, the rest in an arc around it
            var a = new Vector2(-38, 38);
            Button("Attack", "attack", "<Gamepad>/buttonWest", a, 1.15f);
            Button("Nod", "nod", "<Gamepad>/buttonNorth", a + Arc(90), 1f);
            Button("Item", "item", "<Gamepad>/rightShoulder", a + Arc(127), 1f);
            Button("Talk", "talk", "<Gamepad>/buttonSouth", a + Arc(164), 1f);
            Button("Roll", "roll", "<Gamepad>/buttonEast", a + Arc(201), 1f);
            var pause = Place("Pause", Spr("pause"), new Vector2(0.5f, 1), new Vector2(0, -16), 1f);
            pause.gameObject.AddComponent<OnScreenButton>().controlPath = "<Gamepad>/start";
        }

        static Vector2 Arc(float deg) => new Vector2(Mathf.Cos(deg * Mathf.Deg2Rad), Mathf.Sin(deg * Mathf.Deg2Rad)) * 52f;

        void Button(string name, string icon, string path, Vector2 pos, float scale)
        {
            var rt = Place(name, Spr(icon), new Vector2(1, 0), pos, scale * 1.15f);
            rt.gameObject.AddComponent<OnScreenButton>().controlPath = path;
        }

        void Update()
        {
            if (Screen.height != lastH || Screen.safeArea != lastSafe) Build();
            // the virtual gamepad is made at startup, sometimes before the app has focus, and the input
            // system parks devices made out of focus; wake it whenever we're in front
            if (Application.isFocused)
                foreach (var d in UnityEngine.InputSystem.InputSystem.devices)
                    if (!d.enabled && !d.native) UnityEngine.InputSystem.InputSystem.EnableDevice(d);
            // keep out of the way of the title and of cutscenes
            bool show = !Title.I && !(Story.I && Story.I.Running && !(DialogueBox.I && DialogueBox.I.Busy));
            foreach (Transform c in root) c.gameObject.SetActive(show || c.name == "Talk" || c.name == "Attack");
        }
    }

    /// <summary>A thumbstick with no fixed home: it sits faintly in the corner until a thumb lands in
    /// its zone, then centres under that thumb and follows it.</summary>
    public class FloatStick : OnScreenControl, IPointerDownHandler, IDragHandler, IPointerUpHandler
    {
        [UnityEngine.InputSystem.Layouts.InputControl(layout = "Vector2")]
        [SerializeField] string path = "<Gamepad>/leftStick";
        protected override string controlPathInternal { get => path; set => path = value; }

        RectTransform zone, ring, knob;
        Image ringImg, knobImg;
        float range;
        Vector2 home, origin;
        int pointer = int.MinValue;

        public void Init(RectTransform zone, RectTransform ring, RectTransform knob, float range)
        {
            this.zone = zone; this.ring = ring; this.knob = knob; this.range = range;
            ringImg = ring.GetComponent<Image>(); knobImg = knob.GetComponent<Image>();
            home = ring.anchoredPosition;
            Show(false);
        }

        void Show(bool held)
        {
            ringImg.color = new Color(1, 1, 1, held ? 0.85f : 0.42f);
            knobImg.color = new Color(1, 1, 1, held ? 0.95f : 0.5f);
        }

        Vector2 Local(PointerEventData e)
        {
            RectTransformUtility.ScreenPointToLocalPointInRectangle(zone, e.position, e.pressEventCamera, out var p);
            return p;
        }

        public void OnPointerDown(PointerEventData e)
        {
            if (pointer != int.MinValue) return;
            pointer = e.pointerId;
            origin = Local(e);
            var half = ring.sizeDelta * 0.5f;
            origin = Vector2.Max(origin, half + new Vector2(4, 4));
            ring.anchoredPosition = knob.anchoredPosition = origin;
            Show(true);
            Move(e);
        }

        public void OnDrag(PointerEventData e)
        {
            if (e.pointerId == pointer) Move(e);
        }

        public void OnPointerUp(PointerEventData e)
        {
            if (e.pointerId == pointer) Release();
        }

        void Move(PointerEventData e)
        {
            var d = Vector2.ClampMagnitude(Local(e) - origin, range);
            knob.anchoredPosition = origin + d;
            SendValueToControl(d / range);
        }

        void Release()
        {
            pointer = int.MinValue;
            SendValueToControl(Vector2.zero);
            if (ring) { ring.anchoredPosition = knob.anchoredPosition = home; Show(false); }
        }

        protected override void OnDisable()
        {
            if (pointer != int.MinValue) Release();
            base.OnDisable();
        }
    }
}
