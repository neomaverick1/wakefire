// Loads a map built by the art tools: the baked ground, every prop as a sprite sorted by its
// base (so Azar walks behind trees and in front of houses), solid boxes, torch and window
// lights, and markers for spawns and characters. Map pixels: origin top-left, y down.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    [Serializable] public class MapJson { public string name, music; public int w, h; public string ground; public PropJson[] objects; public BoxJson[] boxes; public LightJson[] lights; public MarkerJson[] markers; public string[] surface; public int cell; }
    [Serializable] public class PropJson { public string s; public int x, y, px, py, w, h, layer; public string[] frames; public bool solid; public int bx0, by0, bx1, by1; public string kind, id, text, who; }
    [Serializable] public class BoxJson { public int x0, y0, x1, y1, layer; public string kind; }
    [Serializable] public class LightJson { public int x, y; public float r; public float[] c; public float i; public bool f; public string tag; }
    [Serializable] public class MarkerJson { public string kind; public int x, y, w, h; public string who, id, text; }

    public class Map : MonoBehaviour
    {
        public static Map Current;
        public MapJson data;
        public readonly List<Prop> props = new List<Prop>();
        public Rect bounds;
        static readonly Dictionary<string, Sprite> sprites = new Dictionary<string, Sprite>();
        static Material spriteMat, lightMat;
        static Mesh quad;

        public static Vector2 ToWorld(float px, float py) => new Vector2(px / 16f, -py / 16f);

        /// <summary>What the ground is made of at a world point: g grass, s sand or earth, w wood,
        /// a water, c stone.</summary>
        public char Surface(Vector2 world)
        {
            if (data.surface == null || data.surface.Length == 0 || data.cell <= 0) return 'c';
            int cx = Mathf.FloorToInt(world.x * 16f / data.cell), cy = Mathf.FloorToInt(-world.y * 16f / data.cell);
            if (cy < 0 || cy >= data.surface.Length) return 'c';
            var row = data.surface[cy];
            return cx < 0 || cx >= row.Length ? 'c' : row[cx];
        }
        public static int Order(float worldY) => Mathf.RoundToInt(-worldY * 16f);

        public static Material SpriteMat
        {
            get
            {
                if (!spriteMat) spriteMat = Resources.Load<Material>("Materials/Sprite");
                return spriteMat;
            }
        }

        static readonly Material[] shadeMats = new Material[3];

        /// <summary>The material moon shadows are drawn with, for things in both worlds, the waking one or the dream.</summary>
        public static Material ShadeMat(int layer)
        {
            layer = Mathf.Clamp(layer, 0, 2);
            if (!shadeMats[layer])
            {
                var src = Resources.Load<Material>("Materials/Shade");
                if (!src) return null;
                shadeMats[layer] = new Material(src);
                shadeMats[layer].SetFloat("_Layer", layer);
            }
            return shadeMats[layer];
        }

        public static Sprite GetSprite(string name, float px, float py)
        {
            string key = $"{name}@{px},{py}";
            if (sprites.TryGetValue(key, out var s)) return s;
            var tex = Resources.Load<Texture2D>(name.Contains("/") ? name : "Objects/" + name);
            if (!tex) { Debug.LogWarning("missing sprite " + name); return null; }
            tex.filterMode = FilterMode.Point;
            s = Sprite.Create(tex, new Rect(0, 0, tex.width, tex.height), new Vector2(px / tex.width, 1 - py / tex.height), 16f, 0, SpriteMeshType.FullRect);
            sprites[key] = s;
            return s;
        }

        public static Map Load(string name)
        {
            if (Current) Destroy(Current.gameObject);
            Solids.Clear();
            var go = new GameObject("Map " + name);
            var m = go.AddComponent<Map>();
            Current = m;
            m.Build(name);
            return m;
        }

        void Build(string name)
        {
            data = JsonUtility.FromJson<MapJson>(Resources.Load<TextAsset>("Maps/" + name).text);
            bounds = new Rect(0, -data.h / 16f, data.w / 16f, data.h / 16f);
            // ground
            var g = new GameObject("Ground");
            g.transform.SetParent(transform, false);
            var gsr = g.AddComponent<SpriteRenderer>();
            gsr.sprite = GetSprite(data.ground, 0, 0);
            gsr.sharedMaterial = SpriteMat;
            gsr.sortingOrder = -32000;
            // props
            foreach (var pj in data.objects)
            {
                if (pj.x < 0) continue;
                var p = Prop.Create(pj, transform);
                props.Add(p);
            }
            foreach (var b in data.boxes)
            {
                var a = ToWorld(b.x0, b.y1);
                var sol = Solids.Add(new Rect(a.x, a.y, (b.x1 - b.x0) / 16f, (b.y1 - b.y0) / 16f), (WorldLayer)b.layer);
                sol.pit = b.kind == "pit";
            }
            foreach (var l in data.lights)
            {
                var c = l.c != null && l.c.Length >= 3 ? new Color(l.c[0], l.c[1], l.c[2]) : new Color(1, 0.6f, 0.3f);
                LightBlob.Create(transform, ToWorld(l.x, l.y), l.r, c, l.i, l.f);
            }
        }

        public event Action<string> PlatePressed;

        /// <summary>A plate is pressed while a block sits on it; tells the story which one.</summary>
        public void CheckPlates()
        {
            foreach (var plate in props)
            {
                if (!plate || plate.Kind != "plate" || plate.lit) continue;
                foreach (var b in props)
                {
                    if (!b || b.Kind != "block") continue;
                    if (Vector2.Distance(b.basePos, plate.basePos) < 0.3f)
                    {
                        plate.lit = true;
                        Sfx.Play("plate");
                        PlatePressed?.Invoke(plate.data.id);
                    }
                }
            }
        }

        public MarkerJson Marker(string kind, string who = null)
        {
            foreach (var m in data.markers) if (m.kind == kind && (who == null || m.who == who)) return m;
            return null;
        }

        public Prop Find(string id)
        {
            foreach (var p in props) if (p.data.id == id) return p;
            return null;
        }

        public static Mesh Quad
        {
            get
            {
                if (quad) return quad;
                quad = new Mesh { name = "WF Quad" };
                quad.vertices = new[] { new Vector3(-0.5f, -0.5f), new Vector3(0.5f, -0.5f), new Vector3(0.5f, 0.5f), new Vector3(-0.5f, 0.5f) };
                quad.uv = new[] { new Vector2(0, 0), new Vector2(1, 0), new Vector2(1, 1), new Vector2(0, 1) };
                quad.triangles = new[] { 0, 2, 1, 0, 3, 2 };
                quad.colors = new[] { Color.white, Color.white, Color.white, Color.white };
                return quad;
            }
        }

        public static Material LightMat
        {
            get
            {
                if (!lightMat) lightMat = Resources.Load<Material>("Materials/Light");
                return lightMat;
            }
        }
    }

    /// <summary>A placed prop: a sorted sprite, an optional solid box, and what it does when touched.</summary>
    public partial class Prop : MonoBehaviour
    {
        public PropJson data;
        public SpriteRenderer sr;
        public Solid solid;
        public Vector2 basePos;
        Sprite[] frames;
        float frameClock;
        public bool lit;
        LightBlob glow;

        public string Kind => data.kind ?? "";

        public static Prop Create(PropJson pj, Transform parent)
        {
            var go = new GameObject(pj.s);
            go.transform.SetParent(parent, false);
            var p = go.AddComponent<Prop>();
            p.data = pj;
            p.basePos = Map.ToWorld(pj.x, pj.y);
            go.transform.position = new Vector3(p.basePos.x, p.basePos.y, 0);
            p.sr = go.AddComponent<SpriteRenderer>();
            p.sr.sprite = Map.GetSprite(pj.s, pj.px, pj.py);
            p.sr.sharedMaterial = Map.SpriteMat;
            p.sr.sortingOrder = Map.Order(p.basePos.y);
            if (pj.layer != 0)
            {
                p.sr.material = new Material(Map.SpriteMat);
                p.sr.material.SetFloat("_Layer", pj.layer);
            }
            if (pj.solid)
            {
                var a = Map.ToWorld(pj.x + pj.bx0, pj.y + pj.by1);
                p.solid = Solids.Add(new Rect(a.x, a.y, (pj.bx1 - pj.bx0) / 16f, (pj.by1 - pj.by0) / 16f), (WorldLayer)pj.layer, p);
            }
            if (pj.frames != null && pj.frames.Length > 1) p.SetFrames(pj.frames);
            p.Stand();
            return p;
        }

        SpriteRenderer shade;
        static MaterialPropertyBlock swayBlock;

        /// <summary>Things that stand up throw a moon shadow; trees and bushes also move in the wind.</summary>
        void Stand()
        {
            string n = data.s ?? "";
            bool leafy = n.StartsWith("olive") || n.StartsWith("cypress") || n.StartsWith("palm") || n.StartsWith("bush");
            string k = Kind;
            bool casts = (data.solid && k != "bars" && k != "bigdoor" && k != "lockdoor" && k != "gate" && k != "bullhead" && data.h >= 10) || n == "wall_temple" || k == "banner";
            float sway = n.StartsWith("bush") ? 0.045f : n.StartsWith("palm") ? 0.035f : leafy ? 0.026f : 0f;
            if (sway > 0)
            {
                if (swayBlock == null) swayBlock = new MaterialPropertyBlock();
                sr.GetPropertyBlock(swayBlock);
                swayBlock.SetFloat("_Sway", sway);
                sr.SetPropertyBlock(swayBlock);
            }
            var mat = Map.ShadeMat(data.layer);
            if (!casts || !mat || !sr.sprite) return;
            var go = new GameObject("Shade");
            go.transform.SetParent(transform, false);
            shade = go.AddComponent<SpriteRenderer>();
            shade.sprite = sr.sprite;
            shade.sharedMaterial = mat;
            shade.sortingOrder = sr.sortingOrder - 1;
            if (sway > 0)
            {
                shade.GetPropertyBlock(swayBlock);
                swayBlock.SetFloat("_Sway", sway);
                shade.SetPropertyBlock(swayBlock);
            }
        }

        public void SetFrames(string[] names)
        {
            frames = new Sprite[names.Length];
            for (int i = 0; i < names.Length; i++) frames[i] = Map.GetSprite(names[i], data.px, data.py);
            sr.sprite = frames[0];
        }

        public void SetSprite(string name, int px, int py)
        {
            frames = null;
            sr.sprite = Map.GetSprite(name, px, py);
        }

        public Rect Bounds => solid != null ? solid.r : new Rect(basePos - new Vector2(0.4f, 0), new Vector2(0.8f, 0.5f));

        /// <summary>Light a brazier with the Wakefire.</summary>
        public bool Ignite()
        {
            if (Kind != "brazier" || lit) return false;
            lit = true;
            var meta = Map.Current;
            PropJson litJson = null;
            foreach (var o in meta.data.objects) if (o.s == "brazier_lit_0" || (o.frames != null && o.frames.Length > 0 && o.frames[0] == "brazier_lit_0")) litJson = o;
            if (litJson != null)
            {
                data.px = litJson.px; data.py = litJson.py;
                SetFrames(litJson.frames);
            }
            glow = LightBlob.Create(transform, basePos + new Vector2(0, 1.1f), 5.5f, new Color(1f, 0.72f, 0.36f), 0.85f, true);
            return true;
        }

        /// <summary>A clay jar bursts into shards.</summary>
        public void Shatter()
        {
            if (solid != null) Solids.Remove(solid);
            for (int i = 0; i < 12; i++)
                Fx.Spawn(basePos + new Vector2(0, 0.3f) + UnityEngine.Random.insideUnitCircle * 0.2f, UnityEngine.Random.insideUnitCircle * 3.4f, 0.4f,
                    UnityEngine.Random.Range(3f, 6f), UnityEngine.Random.Range(0.4f, 0.8f), new Color(0.72f, 0.42f, 0.3f), new Color(0.35f, 0.18f, 0.16f), 18f,
                    i % 3 == 0 ? 2 : 1);
            Destroy(gameObject);
        }

        /// <summary>A stone block shoved one tile along, if nothing is in the way. Plates under it press.</summary>
        public bool Slide(Vector2 dir)
        {
            if (sliding || solid == null) return false;
            var r = solid.r;
            r.position += dir;
            foreach (var other in Solids.All)
                if (other != solid && other.enabled && other.r.Overlaps(r) && other.layer == solid.layer) return false;
            StartCoroutine(SlideRoutine(dir));
            return true;
        }

        bool sliding;

        System.Collections.IEnumerator SlideRoutine(Vector2 dir)
        {
            sliding = true;
            var from = basePos;
            var r0 = solid.r.position;
            for (float t = 0; t < 1; t += Time.deltaTime / 0.28f)
            {
                basePos = from + dir * Mathf.SmoothStep(0, 1, t);
                transform.position = basePos;
                solid.r.position = r0 + dir * Mathf.SmoothStep(0, 1, t);
                sr.sortingOrder = Map.Order(basePos.y);
                yield return null;
            }
            basePos = from + dir;
            transform.position = basePos;
            solid.r.position = r0 + dir;
            sr.sortingOrder = Map.Order(basePos.y);
            sliding = false;
            Fx.Dust(basePos, 3);
            Map.Current.CheckPlates();
        }

        public void Cut()
        {
            if (solid != null) Solids.Remove(solid);
            Fx.Leaves(basePos + new Vector2(0, 0.4f));
            Destroy(gameObject);
        }

        float emberClock;
        float crestPhase = UnityEngine.Random.value * 7f;
        bool mothsMade;

        void Update()
        {
            if (shade)
            {
                shade.enabled = sr.enabled;
                shade.sortingOrder = sr.sortingOrder - 1;
                if (shade.sprite != sr.sprite) shade.sprite = sr.sprite;
            }
            if (frames != null)
            {
                float fps = Kind == "banner" ? 2.2f : Kind == "crest" ? 3.0f : 9f;
                frameClock += Time.deltaTime * fps;
                int f = (int)frameClock % frames.Length;
                if (Kind == "crest") { f = (int)(frameClock + crestPhase) % (frames.Length + 3); sr.enabled = f < frames.Length; f = Mathf.Min(f, frames.Length - 1); }
                sr.sprite = frames[f];
            }
            // live fire throws the odd ember up into the night
            bool fire = (Kind == "brazier" && lit) || Kind == "torch";
            if (fire && !mothsMade) { mothsMade = true; TorchMoths.Add(this); }
            if (fire && !Game.Paused)
            {
                emberClock -= Time.deltaTime;
                if (emberClock <= 0)
                {
                    emberClock = UnityEngine.Random.Range(0.25f, 0.7f);
                    Fx.Embers(basePos + new Vector2(UnityEngine.Random.Range(-0.15f, 0.15f), Kind == "torch" ? 1.65f : 1.1f), 1);
                }
            }
        }
    }

    /// <summary>A pool of warm light in the light layer: stepped rings that flicker like fire.</summary>
    public class LightBlob : MonoBehaviour
    {
        public static readonly List<LightBlob> All = new List<LightBlob>();
        void OnEnable() => All.Add(this);
        void OnDisable() => All.Remove(this);
        public float radius, intensity;
        public bool flicker;
        public Color color;
        MeshRenderer mr;
        MaterialPropertyBlock mpb;
        float seed;

        public static LightBlob Create(Transform parent, Vector2 at, float radius, Color c, float intensity = 1f, bool flicker = true)
        {
            var go = new GameObject("Light");
            go.layer = PixelView.LightLayer;
            go.transform.SetParent(parent, false);
            go.transform.position = new Vector3(at.x, at.y, 0);
            var l = go.AddComponent<LightBlob>();
            l.radius = radius;
            l.color = c;
            l.intensity = intensity;
            l.flicker = flicker;
            go.AddComponent<MeshFilter>().sharedMesh = Map.Quad;
            l.mr = go.AddComponent<MeshRenderer>();
            l.mr.sharedMaterial = Map.LightMat;
            l.mpb = new MaterialPropertyBlock();
            l.seed = UnityEngine.Random.value * 100f;
            l.Apply(1f);
            return l;
        }

        /// <summary>How bright the light is this instant (it flickers).</summary>
        public float Now { get; private set; } = 1f;

        void Apply(float k)
        {
            Now = k;
            transform.localScale = new Vector3(radius * 2 * k, radius * 2 * k, 1);
            mpb.SetColor("_Color", color * intensity * (0.85f + 0.15f * k));
            mr.SetPropertyBlock(mpb);
        }

        void Update()
        {
            if (!flicker) { Apply(1); return; }
            float t = Time.time * 7f + seed;
            float k = 0.94f + Mathf.PerlinNoise(t, seed) * 0.12f;
            k = Mathf.Round(k * 16f) / 16f;
            Apply(k);
        }
    }
}
