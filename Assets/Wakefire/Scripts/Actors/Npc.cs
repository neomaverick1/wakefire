// The people of Ashkel. Each NPC belongs to one world: a sleeper's body in the waking world,
// their dream-self in the dream (often standing in the very same spot, so the ring sweeping
// past turns one into the other pixel by pixel). The goat belongs to both. It does not dream.
using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Npc : MonoBehaviour
    {
        public static readonly List<Npc> All = new List<Npc>();
        static Material matWake, matDream;

        public string id;
        public Vector2 pos;
        public Facing facing = Facing.Down;
        public WorldLayer layer;
        public SpriteAnim anim;
        public string idleAnim = "idle";
        public bool turnsToTalk = true;
        public Solid solid;
        public Func<IEnumerator> talk;
        public string voice = "man";
        public int orderBias;
        public float lift;                         // drawn this far above where they stand (someone sitting on a seat)
        public System.Func<IEnumerator> notice;   // said once, when Azar first comes near
        public string snore;                       // sleepers breathe loud enough to hear when Azar is close
        float snoreClock = UnityEngine.Random.Range(1.5f, 8f);

        // optional route (sleepwalkers): walk between points, pausing at each
        public Vector2[] route;
        public string walkAnim = "walk", pauseAnim = "idle";
        public float walkSpeed = 1.1f, pauseTime = 1.6f;
        int leg;
        float pauseClock;
        SpriteRenderer shadow;
        Facing restFacing;
        string talkAnimBefore;

        /// <summary>look: the figure that plays this character, when it is not the one the sheet is named for.</summary>
        public static Npc Create(string id, Vector2 at, string sheet, string anim, WorldLayer layer, Facing facing = Facing.Down, bool solid = true, string look = null)
        {
            var go = new GameObject("Npc " + id);
            go.transform.SetParent(Map.Current ? Map.Current.transform : null, false);
            var n = go.AddComponent<Npc>();
            n.id = id;
            n.pos = at;
            n.layer = layer;
            n.facing = n.restFacing = facing;
            n.idleAnim = anim;
            var body = new GameObject("Sprite");
            body.transform.SetParent(go.transform, false);
            var sr = body.AddComponent<SpriteRenderer>();
            sr.sharedMaterial = Mat(layer);
            n.anim = body.AddComponent<SpriteAnim>();
            n.anim.sr = sr;
            n.anim.modelAs = look;
            n.anim.sheet = SpriteSheet.Load(sheet);
            n.anim.Play(anim, facing, true);
            n.anim.time = UnityEngine.Random.value * 3f;   // sleepers breathe out of step
            n.shadow = MakeShadow(go.transform, layer);
            if (layer == WorldLayer.Waking) n.snore = sheet == "dog" ? "snore_small" : "snore";
            if (solid) n.solid = Solids.Add(new Rect(at.x - 0.3f, at.y - 0.12f, 0.6f, 0.36f), layer, n);
            All.Add(n);
            n.Place();
            return n;
        }

        static Material matGhost;
        public bool ghost;

        /// <summary>The material of the dead: pale, cold, and not all there. They belong to the waking
        /// world only. The dead do not dream.</summary>
        public static Material GhostMat
        {
            get
            {
                if (!matGhost)
                {
                    matGhost = new Material(Map.SpriteMat);
                    matGhost.SetFloat("_Layer", 1);
                    matGhost.SetFloat("_Ghost", 0.56f);
                    matGhost.SetVector("_GhostFade", new Vector4(0.285f, 0.40f, 0, 0));
                }
                return matGhost;
            }
        }

        /// <summary>Makes this character one of the dead: seen through, shadowless, awake.</summary>
        public Npc Ghost()
        {
            ghost = true;
            snore = null;
            anim.sr.sharedMaterial = GhostMat;
            if (shadow) { Destroy(shadow.gameObject); shadow = null; }
            return this;
        }

        public static Material Mat(WorldLayer layer)
        {
            if (layer == WorldLayer.Both) return Map.SpriteMat;
            if (!matWake) { matWake = new Material(Map.SpriteMat); matWake.SetFloat("_Layer", 1); }
            if (!matDream) { matDream = new Material(Map.SpriteMat); matDream.SetFloat("_Layer", 2); }
            return layer == WorldLayer.Waking ? matWake : matDream;
        }

        public static SpriteRenderer MakeShadow(Transform parent, WorldLayer layer, int w = 12)
        {
            var t = new Texture2D(w, 5) { filterMode = FilterMode.Point };
            for (int y = 0; y < 5; y++)
                for (int x = 0; x < w; x++)
                {
                    float dx = (x + 0.5f - w / 2f) / (w / 2f), dy = (y + 0.5f - 2.5f) / 2.5f;
                    float d = dx * dx + dy * dy;
                    t.SetPixel(x, y, d <= 1f && ((x + y) % 2 == 0 || d < 0.4f) ? new Color(0.05f, 0.06f, 0.12f, 1) : Color.clear);
                }
            t.Apply();
            var go = new GameObject("Shadow");
            go.transform.SetParent(parent, false);
            go.transform.localPosition = new Vector3(0, 0.02f, 0);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = Sprite.Create(t, new Rect(0, 0, w, 5), new Vector2(0.5f, 0.5f), 16f);
            sr.sharedMaterial = Mat(layer);
            return sr;
        }

        void OnDestroy()
        {
            All.Remove(this);
            if (solid != null) Solids.Remove(solid);
        }

        /// <summary>Is this character there in the world shown at its own feet right now?</summary>
        public bool Present
        {
            get
            {
                if (layer == WorldLayer.Both) return true;
                bool d = Dream.I && Dream.I.IsDreamAt(pos);
                return layer == WorldLayer.Dream ? d : !d;
            }
        }

        public void Play(string a, bool restart = false) => anim.Play(a, facing, restart);

        public void SetIdle(string a)
        {
            idleAnim = a;
            anim.Play(a, facing, true);
        }

        public void FaceTowards(Vector2 p)
        {
            var d = p - pos;
            facing = Mathf.Abs(d.x) > Mathf.Abs(d.y) ? (d.x < 0 ? Facing.Left : Facing.Right) : (d.y < 0 ? Facing.Down : Facing.Up);
            anim.SetFacing(facing);
        }

        public void BeginTalk(Vector2 from)
        {
            talkAnimBefore = anim.anim;
            if (turnsToTalk)
            {
                FaceTowards(from);
                if (anim.sheet.anims.ContainsKey("talk:down")) anim.Play("talk", facing, true);
            }
        }

        public void EndTalk()
        {
            if (!turnsToTalk) return;
            facing = restFacing;
            anim.Play(talkAnimBefore ?? idleAnim, facing, true);
        }

        void Update()
        {
            if (Game.Paused) return;
            float dt = Time.deltaTime;
            bool talking = Story.I && Story.I.Speaker == this;
            if (route != null && route.Length > 1 && !talking) Walk(dt);
            anim.Tick(dt);
            Place();
            if (snore != null && !talking) Snore(dt);
            if (snore != null && !talking) Zeds(dt);
        }

        float zedClock = UnityEngine.Random.Range(0.3f, 1.6f);

        /// <summary>Sleepers breathe out little letter Zs. Even the ones sleepwalking.</summary>
        void Zeds(float dt)
        {
            zedClock -= dt;
            if (zedClock > 0) return;
            zedClock = UnityEngine.Random.Range(1.25f, 1.9f);
            string a = anim.anim;
            if (!Present || !(a == "sleep" || a == "lie" || a == "lean" || a == "knead" || a == "sleepwalk" || a == "cower")) return;
            var v = PixelView.I;
            if (!v || Mathf.Abs(pos.x - v.focus.x) > 14f || Mathf.Abs(pos.y - v.focus.y) > 9f) return;
            float tall = anim.model ? anim.model.def.scale * 1.62f : 2.1f;
            var at = a == "lie" ? pos + new Vector2(0.95f, 0.75f) : a == "cower" ? pos + new Vector2(0.25f, tall * 0.55f) : pos + new Vector2(0.3f, tall);
            Zed.Spawn(at, layer);
        }

        void Snore(float dt)
        {
            snoreClock -= dt;
            if (snoreClock > 0) return;
            snoreClock = UnityEngine.Random.Range(6.5f, 12f);
            var p = Player.I;
            if (!p || !Present || (Story.I && Story.I.Running)) return;
            float d = Vector2.Distance(p.pos, pos);
            if (d > 7f) return;
            Sfx.Play(snore, Mathf.Lerp(0.5f, 0.06f, d / 7f), 0.1f);
        }

        void Walk(float dt)
        {
            if (pauseClock > 0)
            {
                pauseClock -= dt;
                anim.Play(pauseAnim, facing);
                return;
            }
            var target = route[leg];
            var d = target - pos;
            if (d.magnitude < 0.05f)
            {
                leg = (leg + 1) % route.Length;
                pauseClock = pauseTime;
                return;
            }
            var step = d.normalized * walkSpeed * dt;
            if (step.magnitude > d.magnitude) step = d;
            // stop rather than walk through Azar
            var p = Player.I;
            if (p && Vector2.Distance(pos + step, p.pos) < 0.7f && Present) { anim.Play(pauseAnim, facing); return; }
            pos += step;
            facing = Mathf.Abs(d.x) > Mathf.Abs(d.y) ? (d.x < 0 ? Facing.Left : Facing.Right) : (d.y < 0 ? Facing.Down : Facing.Up);
            anim.Play(walkAnim, facing);
            anim.SetFacing(facing);
            if (solid != null) solid.r.position = new Vector2(pos.x - 0.3f, pos.y - 0.12f);
        }

        void Place()
        {
            transform.position = new Vector3(pos.x, pos.y, 0);
            int o = Map.Order(pos.y) + orderBias;
            anim.sr.sortingOrder = o;
            // the dead do not quite stand on the ground
            if (ghost) anim.sr.transform.localPosition = new Vector3(0, (1f + Mathf.Round(Mathf.Sin(Time.time * 1.3f + pos.x * 2.1f) * 1.2f)) / 16f + lift, 0);
            else if (lift != 0) anim.sr.transform.localPosition = new Vector3(0, lift, 0);
            if (shadow)
            {
                shadow.sortingOrder = o - 1;
                shadow.enabled = anim.model || anim.anim != "lie";
            }
        }
    }

    /// <summary>A small letter Z drifting up from a sleeper and fading.</summary>
    public class Zed : MonoBehaviour
    {
        static Sprite glyph;
        SpriteRenderer sr;
        float life, sway;
        Vector2 at;

        public static void Spawn(Vector2 at, WorldLayer layer)
        {
            if (!glyph)
            {
                // a five-pixel Z with a one-pixel drop shadow, so it reads over grass, stone and sand alike
                string[] rows = { "####", "..#.", ".#..", "####" };
                var t = new Texture2D(5, 5) { filterMode = FilterMode.Point };
                var clear = new Color[25];
                t.SetPixels(clear);
                for (int y = 0; y < 4; y++)
                    for (int x = 0; x < 4; x++)
                        if (rows[y][x] == '#') t.SetPixel(x + 1, 3 - y, new Color(0.07f, 0.07f, 0.16f, 1));
                for (int y = 0; y < 4; y++)
                    for (int x = 0; x < 4; x++)
                        if (rows[y][x] == '#') t.SetPixel(x, 4 - y, new Color(0.92f, 0.95f, 1f, 1));
                t.Apply();
                glyph = Sprite.Create(t, new Rect(0, 0, 5, 5), new Vector2(0.5f, 0.5f), 16f);
            }
            var go = new GameObject("z");
            go.transform.SetParent(Map.Current ? Map.Current.transform : null, false);
            var z = go.AddComponent<Zed>();
            z.at = at;
            z.sway = UnityEngine.Random.value * 6f;
            z.sr = go.AddComponent<SpriteRenderer>();
            z.sr.sprite = glyph;
            z.sr.sharedMaterial = Npc.Mat(layer);
            z.sr.sortingOrder = 30000;
            go.transform.position = at;
        }

        void Update()
        {
            if (Game.Paused) return;
            life += Time.deltaTime;
            float k = life / 1.5f;
            var p = at + new Vector2(Mathf.Sin(life * 3.2f + sway) * 0.16f + life * 0.18f, life * 0.62f);
            transform.position = new Vector3(Mathf.Round(p.x * 16f) / 16f, Mathf.Round(p.y * 16f) / 16f, 0);
            sr.enabled = k < 0.72f || ((int)(life * 16f) % 2 == 0);
            if (k >= 1f) Destroy(gameObject);
        }
    }
}
