// The game is drawn at 216 lines (a clean 5x on 1080p phones) and blown up with nearest-
// neighbour filtering. The camera snaps to whole pixels and the leftover sub-pixel offset
// slides the final image so scrolling stays smooth. A light layer (moonlit ambient plus
// torch and lantern rings) is rendered alongside and multiplied in on the display.
// The pixel HUD has its own low-res target, drawn on top without the slide.
using UnityEngine;
using UnityEngine.Rendering.Universal;
using UnityEngine.UI;

namespace Wakefire
{
    public class PixelView : MonoBehaviour
    {
        public static PixelView I;
        /// <summary>Render lines: about 216, picked so the screen is a whole multiple of it (crisp pixels on every phone).</summary>
        public static int Height { get; private set; } = 216;
        public const float PPU = 16f;            // pixels per world unit (one tile)
        public const int PixelUILayer = 6;
        public const int LightLayer = 11;

        public Camera world, light, ui;
        public RenderTexture worldRT, lightRT, uiRT;
        public int width;
        /// <summary>Notch and corner insets in render pixels: x = left, y = bottom, width = right, height = top.</summary>
        public RectInt safe;
        Rect lastSafe;
        public Canvas pixelCanvas;               // HUD and dialogue, in render pixels
        public RectTransform pixelRoot;
        public Canvas display;
        public RectTransform touchRoot;
        public Color ambient = new Color(0.68f, 0.74f, 0.96f);
        public float nightStrength = 1f;

        public Transform target;
        public Vector2 focus;
        public float followSharpness = 10f;
        public Vector2 lookAhead;
        public Rect? bounds;
        float shakeTime, shakeAmp;
        Vector2 shakePx;
        RawImage worldImage, uiImage;
        Material composite;
        int lastW, lastH;

        public float ScreenScale => Screen.height / (float)Height;

        public static PixelView Create()
        {
            var go = new GameObject("PixelView");
            DontDestroyOnLoad(go);
            var v = go.AddComponent<PixelView>();
            v.Build();
            return v;
        }

        Camera MakeCamera(string name, int mask, Color clear, int renderer)
        {
            var go = new GameObject(name);
            go.transform.SetParent(transform, false);
            var c = go.AddComponent<Camera>();
            c.orthographic = true;
            c.orthographicSize = Height / (2f * PPU);
            c.nearClipPlane = 0.1f;
            c.farClipPlane = 100f;
            c.clearFlags = CameraClearFlags.SolidColor;
            c.backgroundColor = clear;
            c.cullingMask = mask;
            c.allowMSAA = false;
            c.allowHDR = false;
            c.transparencySortMode = TransparencySortMode.CustomAxis;
            c.transparencySortAxis = new Vector3(0, 1, 0);
            var d = c.GetUniversalAdditionalCameraData();
            d.renderPostProcessing = false;
            d.antialiasing = AntialiasingMode.None;
            d.SetRenderer(renderer);
            return c;
        }

        void Build()
        {
            I = this;
            world = MakeCamera("WorldCamera", ~((1 << PixelUILayer) | (1 << LightLayer)), new Color(0.03f, 0.03f, 0.06f, 1), 0);
            light = MakeCamera("LightCamera", 1 << LightLayer, ambient, 1);
            light.allowHDR = true;
            light.transform.SetParent(world.transform, false);
            ui = MakeCamera("PixelUICamera", 1 << PixelUILayer, new Color(0, 0, 0, 0), 1);
            ui.transform.position = new Vector3(0, -5000, -10);
            ui.depth = -10;

            var pc = new GameObject("PixelCanvas");
            pc.layer = PixelUILayer;
            pc.transform.SetParent(ui.transform, false);
            pixelCanvas = pc.AddComponent<Canvas>();
            pixelCanvas.renderMode = RenderMode.ScreenSpaceCamera;
            pixelCanvas.worldCamera = ui;
            pixelCanvas.planeDistance = 5;
            pixelCanvas.pixelPerfect = true;
            var cs = pc.AddComponent<CanvasScaler>();
            cs.uiScaleMode = CanvasScaler.ScaleMode.ConstantPixelSize;
            cs.scaleFactor = 1;
            pixelRoot = pc.GetComponent<RectTransform>();

            var dgo = new GameObject("Display");
            dgo.transform.SetParent(transform, false);
            display = dgo.AddComponent<Canvas>();
            display.renderMode = RenderMode.ScreenSpaceOverlay;
            display.sortingOrder = 0;
            dgo.AddComponent<CanvasScaler>().uiScaleMode = CanvasScaler.ScaleMode.ConstantPixelSize;
            dgo.AddComponent<GraphicRaycaster>();
            worldImage = MakeImage("World", dgo.transform);
            composite = new Material(Shader.Find("Wakefire/Composite"));
            worldImage.material = composite;
            uiImage = MakeImage("PixelUI", dgo.transform);
            var tgo = new GameObject("Touch", typeof(RectTransform));
            tgo.transform.SetParent(dgo.transform, false);
            touchRoot = (RectTransform)tgo.transform;
            Stretch(touchRoot);
            Resize();
        }

        static RawImage MakeImage(string name, Transform parent)
        {
            var go = new GameObject(name, typeof(RectTransform));
            go.transform.SetParent(parent, false);
            var img = go.AddComponent<RawImage>();
            img.raycastTarget = false;
            Stretch((RectTransform)go.transform);
            return img;
        }

        public static void Stretch(RectTransform rt)
        {
            rt.anchorMin = Vector2.zero;
            rt.anchorMax = Vector2.one;
            rt.offsetMin = Vector2.zero;
            rt.offsetMax = Vector2.zero;
        }

        static RenderTexture RT(string name, int w, int h, bool hdr = false)
        {
            var fmt = hdr && SystemInfo.SupportsRenderTextureFormat(RenderTextureFormat.ARGBHalf) ? RenderTextureFormat.ARGBHalf : RenderTextureFormat.ARGB32;
            var r = new RenderTexture(w, h, 16, fmt) { filterMode = FilterMode.Point, name = name, antiAliasing = 1 };
            r.Create();
            return r;
        }

        void Resize()
        {
            lastW = Screen.width;
            lastH = Screen.height;
            int scale = Mathf.Max(1, Mathf.RoundToInt(Screen.height / 216f));
            Height = Mathf.Clamp(Screen.height / scale, 196, 248);
            // pixels stay square on every shape of screen: on narrow ones (4:3 tablets, a phone
            // held upright in a browser) the view grows taller rather than the picture squashing
            float aspect = Screen.width / (float)Mathf.Max(1, Screen.height);
            if (Height * aspect < 256) Height = Mathf.Min(560, Mathf.CeilToInt(256 / aspect));
            if (Height % 2 == 1) Height++;
            width = Mathf.Max(2, Mathf.RoundToInt(Height * aspect));
            if (width % 2 == 1) width++;
            foreach (var (cam, rt) in new[] { (world, worldRT), (light, lightRT), (ui, uiRT) })
                if (rt) { cam.targetTexture = null; rt.Release(); Destroy(rt); }
            worldRT = RT("WF World", width + 2, Height + 2);
            lightRT = RT("WF Light", width + 2, Height + 2, true);
            uiRT = RT("WF PixelUI", width, Height);
            world.targetTexture = worldRT;
            light.targetTexture = lightRT;
            ui.targetTexture = uiRT;
            float ortho = (Height + 2) / (2f * PPU);
            world.orthographicSize = ortho;
            light.orthographicSize = ortho;
            ui.orthographicSize = Height / 2f;
            worldImage.texture = worldRT;
            composite.SetTexture("_LightTex", lightRT);
            uiImage.texture = uiRT;
            uiImage.uvRect = new Rect(0, 0, 1, 1);
            Insets();
        }

        void Insets()
        {
            var sa = lastSafe = Screen.safeArea;
            float kx = width / (float)Mathf.Max(1, Screen.width), ky = Height / (float)Mathf.Max(1, Screen.height);
            safe = new RectInt(Mathf.CeilToInt(sa.xMin * kx), Mathf.CeilToInt(sa.yMin * ky),
                               Mathf.CeilToInt((Screen.width - sa.xMax) * kx), Mathf.CeilToInt((Screen.height - sa.yMax) * ky));
        }

        public void Shake(float pixels, float seconds)
        {
            if (pixels * seconds < shakeAmp * shakeTime) return;
            shakeAmp = pixels;
            shakeTime = seconds;
        }

        public void SnapTo(Vector2 p) => focus = p;

        void LateUpdate()
        {
            if (Screen.width != lastW || Screen.height != lastH) Resize();
            else if (Screen.safeArea != lastSafe) Insets();
            light.backgroundColor = ambient;
            composite.SetFloat("_Strength", nightStrength);
            if (target)
            {
                var goal = (Vector2)target.position + lookAhead;
                focus = Vector2.Lerp(focus, goal, 1f - Mathf.Exp(-followSharpness * Time.unscaledDeltaTime));
            }
            if (bounds.HasValue)
            {
                var b = bounds.Value;
                float halfW = width / (2f * PPU), halfH = Height / (2f * PPU);
                focus.x = b.width < halfW * 2 ? b.center.x : Mathf.Clamp(focus.x, b.xMin + halfW, b.xMax - halfW);
                focus.y = b.height < halfH * 2 ? b.center.y : Mathf.Clamp(focus.y, b.yMin + halfH, b.yMax - halfH);
            }
            if (shakeTime > 0)
            {
                shakeTime -= Time.unscaledDeltaTime;
                float a = shakeAmp * Mathf.Clamp01(shakeTime * 6f);
                shakePx = new Vector2(Mathf.Round(Random.Range(-a, a)), Mathf.Round(Random.Range(-a, a)));
            }
            else shakePx = Vector2.zero;

            float s = 1f / PPU;
            Vector2 desired = focus + shakePx * s;
            float xs = Mathf.Round(desired.x / s) * s, ys = Mathf.Round(desired.y / s) * s;
            world.transform.position = new Vector3(xs, ys, -20);
            float ox = (desired.x - xs) / s, oy = (desired.y - ys) / s;
            worldImage.uvRect = new Rect((1 + ox) / (width + 2), (1 + oy) / (Height + 2),
                width / (float)(width + 2), Height / (float)(Height + 2));
            Shader.SetGlobalVector("_WF_RTWorld", new Vector4(xs, ys, (width + 2) / (float)PPU, (Height + 2) / (float)PPU));
        }

        /// <summary>World point to the pixel HUD (origin bottom-left, render pixels).</summary>
        public Vector2 WorldToPixel(Vector3 p)
        {
            var c = world.transform.position;
            return new Vector2((p.x - c.x) * PPU + width / 2f, (p.y - c.y) * PPU + Height / 2f);
        }
    }
}
