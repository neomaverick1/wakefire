// Two or three moths that won't leave a fire alone: dark specks circling the flame, darting
// in and out of the light. Real night, no glitter.
using UnityEngine;

namespace Wakefire
{
    public class TorchMoths : MonoBehaviour
    {
        static Sprite dot;
        Prop fire;
        SpriteRenderer[] moths;
        float[] phase, speed, radius;

        public static void Add(Prop p)
        {
            var go = new GameObject("Moths");
            go.transform.SetParent(p.transform, false);
            var m = go.AddComponent<TorchMoths>();
            m.fire = p;
            int n = Random.Range(2, 4);
            m.moths = new SpriteRenderer[n];
            m.phase = new float[n]; m.speed = new float[n]; m.radius = new float[n];
            if (!dot)
            {
                var t = new Texture2D(2, 1) { filterMode = FilterMode.Point };
                t.SetPixel(0, 0, new Color(0.08f, 0.06f, 0.1f)); t.SetPixel(1, 0, new Color(0.18f, 0.15f, 0.2f));
                t.Apply();
                dot = Sprite.Create(t, new Rect(0, 0, 2, 1), new Vector2(0.5f, 0.5f), 16f);
            }
            for (int i = 0; i < n; i++)
            {
                var g = new GameObject("moth");
                g.transform.SetParent(go.transform, false);
                var sr = g.AddComponent<SpriteRenderer>();
                sr.sprite = dot;
                sr.sharedMaterial = Map.SpriteMat;
                m.moths[i] = sr;
                m.phase[i] = Random.value * 10f;
                m.speed[i] = Random.Range(2.2f, 4.2f) * (Random.value < 0.5f ? -1 : 1);
                m.radius[i] = Random.Range(0.35f, 0.8f);
            }
        }

        void Update()
        {
            if (!fire) return;
            float top = fire.Kind == "torch" ? 1.75f : 1.25f;
            var c = fire.basePos + new Vector2(0, top);
            for (int i = 0; i < moths.Length; i++)
            {
                phase[i] += Time.deltaTime * speed[i];
                float r = radius[i] * (0.7f + 0.3f * Mathf.Sin(phase[i] * 1.7f));
                var p = c + new Vector2(Mathf.Cos(phase[i]) * r, Mathf.Sin(phase[i] * 1.3f) * r * 0.6f);
                p.x = Mathf.Round(p.x * 16f) / 16f; p.y = Mathf.Round(p.y * 16f) / 16f;
                moths[i].transform.position = p;
                moths[i].sortingOrder = Map.Order(fire.basePos.y) + 3;
                moths[i].flipX = Mathf.Sin(phase[i] * 7f) > 0;
            }
        }
    }
}
