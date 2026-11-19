// Pixel particles: cut leaves, sparks off bronze, dust from footsteps and rolls, embers.
// Each particle is a 1-2 pixel square that flies with a little height, gravity and bounce.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Fx : MonoBehaviour
    {
        static Fx I;
        static Sprite px;
        class P { public SpriteRenderer sr; public Vector2 pos, vel; public float z, vz, life, max, grav; public Color c0, c1; public bool alive; }
        readonly List<P> pool = new List<P>();

        static void Ensure()
        {
            if (I) return;
            var go = new GameObject("Fx");
            DontDestroyOnLoad(go);
            I = go.AddComponent<Fx>();
            var t = new Texture2D(1, 1) { filterMode = FilterMode.Point };
            t.SetPixel(0, 0, Color.white);
            t.Apply();
            px = Sprite.Create(t, new Rect(0, 0, 1, 1), new Vector2(0.5f, 0.5f), 16f);
        }

        static P Get()
        {
            Ensure();
            foreach (var p in I.pool) if (!p.alive) return p;
            var go = new GameObject("p");
            go.transform.SetParent(I.transform, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = px;
            sr.sharedMaterial = Map.SpriteMat;
            var np = new P { sr = sr };
            I.pool.Add(np);
            return np;
        }

        public static void Spawn(Vector2 at, Vector2 vel, float z, float vz, float life, Color c0, Color c1, float grav = 18f, int size = 1)
        {
            var p = Get();
            p.alive = true;
            p.pos = at; p.vel = vel; p.z = z; p.vz = vz; p.life = 0; p.max = life; p.grav = grav; p.c0 = c0; p.c1 = c1;
            p.sr.enabled = true;
            p.sr.transform.localScale = new Vector3(size, size, 1);
            p.sr.color = c0;
        }

        public static void Leaves(Vector2 at)
        {
            for (int i = 0; i < 14; i++)
            {
                var v = Random.insideUnitCircle * 3.2f;
                Spawn(at + Random.insideUnitCircle * 0.3f, v, 0.4f, Random.Range(3f, 7f), Random.Range(0.4f, 0.8f),
                    i % 3 == 0 ? new Color(0.45f, 0.66f, 0.38f) : new Color(0.20f, 0.42f, 0.27f), new Color(0.12f, 0.25f, 0.2f), 16f, i % 4 == 0 ? 2 : 1);
            }
        }

        public static void Sparks(Vector2 at, Color c, int n = 8)
        {
            for (int i = 0; i < n; i++)
            {
                var v = Random.insideUnitCircle.normalized * Random.Range(3f, 7f);
                Spawn(at, v, 0.6f, Random.Range(1f, 5f), Random.Range(0.15f, 0.35f), Color.white, c, 22f);
            }
        }

        public static void Dust(Vector2 at, int n = 4)
        {
            for (int i = 0; i < n; i++)
                Spawn(at + new Vector2(Random.Range(-0.2f, 0.2f), 0), new Vector2(Random.Range(-1f, 1f), Random.Range(0.2f, 0.8f)), 0.05f, Random.Range(0.5f, 1.5f),
                    Random.Range(0.25f, 0.45f), new Color(0.78f, 0.72f, 0.80f, 0.9f), new Color(0.5f, 0.46f, 0.56f, 0.0f), 4f);
        }

        public static void Embers(Vector2 at, int n = 3)
        {
            for (int i = 0; i < n; i++)
                Spawn(at + new Vector2(Random.Range(-0.25f, 0.25f), 0), new Vector2(Random.Range(-0.4f, 0.4f), Random.Range(0.4f, 1.2f)), 0.9f, Random.Range(0.5f, 1.4f),
                    Random.Range(0.4f, 0.9f), new Color(1f, 0.85f, 0.4f), new Color(0.9f, 0.3f, 0.1f), -1f);
        }

        void Update()
        {
            float dt = Time.deltaTime;
            foreach (var p in pool)
            {
                if (!p.alive) continue;
                p.life += dt;
                if (p.life >= p.max) { p.alive = false; p.sr.enabled = false; continue; }
                p.pos += p.vel * dt;
                p.vel *= 1f - 2.5f * dt;
                p.vz -= p.grav * dt;
                p.z += p.vz * dt;
                if (p.z < 0 && p.grav > 0) { p.z = 0; p.vz *= -0.35f; p.vel *= 0.5f; }
                float t = p.life / p.max;
                var c = Color.Lerp(p.c0, p.c1, t);
                p.sr.color = c;
                float sx = Mathf.Round((p.pos.x) * 16f) / 16f, sy = Mathf.Round((p.pos.y + p.z) * 16f) / 16f;
                p.sr.transform.position = new Vector3(sx, sy, 0);
                p.sr.sortingOrder = Map.Order(p.pos.y) + 2;
            }
        }
    }
}
