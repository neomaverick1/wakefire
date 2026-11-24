// Smoke: what comes out of a chimney, a kiln, the hole in the top of the oracle's dome. The map
// marks where ("smoke"; who = "fig" for whatever it is she burns), and it rises from there for as
// long as the map is up, forty nights after anybody last fed the fire.
using UnityEngine;

namespace Wakefire
{
    public class Smoke : MonoBehaviour
    {
        public Vector2 at;
        public Color near = new Color(0.62f, 0.60f, 0.68f, 0.55f), far = new Color(0.34f, 0.33f, 0.42f, 0f);
        float clock;

        public static void Setup(Map m)
        {
            foreach (var mk in m.data.markers)
            {
                if (mk.kind != "smoke") continue;
                var s = m.gameObject.AddComponent<Smoke>();
                s.at = Map.ToWorld(mk.x, mk.y);
                if (mk.who == "fig") { s.near = new Color(0.72f, 0.52f, 0.86f, 0.55f); s.far = new Color(0.36f, 0.26f, 0.5f, 0f); }
                s.clock = Random.value * 0.5f;
            }
        }

        void Update()
        {
            if (Game.Paused) return;
            clock -= Time.deltaTime;
            if (clock > 0) return;
            clock = Random.Range(0.16f, 0.34f);
            Fx.Spawn(at + new Vector2(Random.Range(-0.12f, 0.12f), 0), new Vector2(Random.Range(0.10f, 0.42f), Random.Range(-0.05f, 0.1f)), 0.05f, Random.Range(1.1f, 1.7f),
                Random.Range(1.5f, 2.6f), near, far, -0.5f, Random.value < 0.4f ? 2 : 1);
        }
    }
}
