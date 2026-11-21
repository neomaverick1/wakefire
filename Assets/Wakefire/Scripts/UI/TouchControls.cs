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

#if UNITY_WEBGL && !UNITY_EDITOR
        // a browser always reports a touchscreen, so on the web the buttons wait for a phone or a real touch
        public static bool Wanted => Application.isMobilePlatform || Boot.Flag("-touch") || touchedOnce;
#else
        public static bool Wanted => Application.isMobilePlatform || Boot.Flag("-touch") || UnityEngine.InputSystem.Touchscreen.current != null;
#endif
        static bool touchedOnce;

        /// <summary>Called every frame: the first finger on the screen brings the buttons up.</summary>
        public static void Poll()
        {
            if (I || touchedOnce) return;
            var ts = UnityEngine.InputSystem.Touchscreen.current;
            if (ts != null && ts.primaryTouch.press.isPressed) { touchedOnce = true; Create(); }
        }

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
            return Sprite.Create(t, new Rect(0, 0, t.width, t.height), new Vector2(0.5f, 0.5f), 1f);
        }

        /// <summary>The buttons are drawn six texture pixels to the game pixel (Art/ui/touch_art.py).</summary>
        const float Density = 6f;

        RectTransform Place(string name, Sprite s, Vector2 anchor, Vector2 posUnits, float scale, Transform parent = null)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent ? parent : root, false);
            var img = go.AddComponent<Image>();
            img.sprite = s;
            img.color = new Color(1, 1, 1, 0.93f);
            var rt = (RectTransform)go.transform;
            rt.anchorMin = rt.anchorMax = anchor;
            rt.pivot = new Vector2(0.5f, 0.5f);
            float u = Screen.height / 216f;
            rt.sizeDelta = new Vector2(s.rect.width, s.rect.height) / Density * u * scale;
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
            var ring = Place("StickBase", Spr("stick_base"), Vector2.zero, new Vector2(50, 48), 1f, zone);
            var knob = Place("Stick", Spr("stick_knob"), Vector2.zero, new Vector2(50, 48), 1f, zone);
            ring.GetComponent<Image>().raycastTarget = knob.GetComponent<Image>().raycastTarget = false;
            zgo.AddComponent<FloatStick>().Init(zone, ring, knob, 20 * u);
            // the buttons: the khopesh under the thumb, the rest in an arc around it
            var a = new Vector2(-40, 40);
            Button("Attack", "attack", "<Gamepad>/buttonWest", a, 1.14f);
            Button("Nod", "nod", "<Gamepad>/buttonNorth", a + Arc(90), 1.06f);
            Button("Item", "item", "<Gamepad>/rightShoulder", a + Arc(127), 1.06f);
            Button("Talk", "talk", "<Gamepad>/buttonSouth", a + Arc(164), 1.06f);
            Button("Roll", "roll", "<Gamepad>/buttonEast", a + Arc(201), 1.06f);
            var pause = Place("Pause", Spr("pause"), new Vector2(0.5f, 1), new Vector2(0, -15), 1f);
            pause.gameObject.AddComponent<OnScreenButton>().controlPath = "<Gamepad>/start";
            pause.gameObject.AddComponent<PressLook>();
        }

        static Vector2 Arc(float deg) => new Vector2(Mathf.Cos(deg * Mathf.Deg2Rad), Mathf.Sin(deg * Mathf.Deg2Rad)) * 56f;

        void Button(string name, string icon, string path, Vector2 pos, float scale)
        {
            var rt = Place(name, Spr(icon), new Vector2(1, 0), pos, scale);
            rt.gameObject.AddComponent<OnScreenButton>().controlPath = path;
            rt.gameObject.AddComponent<PressLook>();
        }

        /// <summary>True while the buttons are on screen and taking presses.</summary>
        public static bool Showing => I && I.shown > 0.5f;
        float shown = 0;
        CanvasGroup group;

        void Update()
        {
            if (Screen.height != lastH || Screen.safeArea != lastSafe) Build();
            // the virtual gamepad is made at startup, sometimes before the app has focus, and the input
            // system parks devices made out of focus; wake it whenever we're in front
            if (Application.isFocused)
                foreach (var d in UnityEngine.InputSystem.InputSystem.devices)
                    if (!d.enabled && !d.native) UnityEngine.InputSystem.InputSystem.EnableDevice(d);
            // Out of the way of anything there is to read or watch: the title, a scene, a text box, the
            // pause menu. They fade out (still there underneath, so the virtual gamepad stays alive) and a
            // tap anywhere turns the page.
            bool show = !Title.I && !Game.Paused && !(Story.I && Story.I.Running) && !(DialogueBox.I && DialogueBox.I.Busy);
            if (!group) group = root.gameObject.GetComponent<CanvasGroup>() ?? root.gameObject.AddComponent<CanvasGroup>();
            shown = Mathf.MoveTowards(shown, show ? 1 : 0, Time.unscaledDeltaTime / (show ? 0.22f : 0.08f));
            group.alpha = shown;
            group.blocksRaycasts = group.interactable = show;
        }
    }

    /// <summary>A button answers the thumb: it sinks a little and brightens while it is held.</summary>
    public class PressLook : MonoBehaviour, IPointerDownHandler, IPointerUpHandler
    {
        Image img;
        Vector3 rest;
        bool held;
        float t;

        void Awake() { img = GetComponent<Image>(); rest = transform.localScale; }
        public void OnPointerDown(PointerEventData e) { held = true; }
        public void OnPointerUp(PointerEventData e) { held = false; }
        void OnDisable() { held = false; t = 0; transform.localScale = rest; }

        void Update()
        {
            t = Mathf.MoveTowards(t, held ? 1 : 0, Time.unscaledDeltaTime / (held ? 0.04f : 0.12f));
            transform.localScale = rest * (1 - 0.07f * t);
            if (img) img.color = new Color(1, 1 - 0.06f * t, 1 - 0.16f * t, Mathf.Lerp(0.93f, 1f, t));
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
