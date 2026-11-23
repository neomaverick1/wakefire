// Things in the high halls that are bronze and glass rather than flesh, built the way the animals
// are (a few bones, a skin drawn over them) so that they are lit and outlined like everything else:
// a thurifer's censer, and a burning glass on its three legs.
using UnityEngine;

namespace Wakefire
{
    /// <summary>A censer: a bronze pot with a lid, a line of fire where the two meet, hung by three chains
    /// from a ring. It hangs from the ring, and trails behind the way it is going.</summary>
    public class CenserProp : IPoser
    {
        Transform pot;
        Vector2 lean;

        public static CenserProp Make(ModelActor a)
        {
            var c = new CenserProp();
            c.pot = new GameObject("pot").transform;
            c.pot.SetParent(a.rig, false);
            c.pot.localPosition = new Vector3(0, 0.62f, 0);
            a.bones["pot"] = c.pot;
            Color bronze = new Color(0.82f, 0.56f, 0.20f), dark = new Color(0.30f, 0.18f, 0.10f), coal = new Color(1f, 0.52f, 0.14f);
            var kit = new Kit(a, a.rig, new[] { c.pot });
            kit.On("pot");
            kit.Paint(bronze, 1).Turned(Vector3.zero, new[] { (0.03f, 0.02f), (0.10f, 0.04f), (0.17f, 0.11f), (0.19f, 0.20f) }, 10);
            kit.Paint(coal, 0, 2.4f).Turned(Vector3.zero, new[] { (0.195f, 0.20f), (0.195f, 0.25f) }, 10);
            kit.Paint(bronze, 1).Turned(Vector3.zero, new[] { (0.19f, 0.25f), (0.155f, 0.33f), (0.075f, 0.40f), (0.03f, 0.43f) }, 10);
            kit.Paint(dark).Egg(new Vector3(0, 0.45f, 0), Vector3.one * 0.038f, 5, 4);
            for (int k = 0; k < 3; k++)
            {
                float an = (90f + k * 120f) * Mathf.Deg2Rad;
                kit.Paint(dark).Tube(new[] { new Vector3(Mathf.Cos(an) * 0.17f, 0.27f, Mathf.Sin(an) * 0.17f), new Vector3(0, 0.62f, 0) }, new[] { 0.013f, 0.013f }, 4);
            }
            kit.Paint(bronze, 1).Egg(new Vector3(0, 0.63f, 0), Vector3.one * 0.03f, 5, 4);
            kit.Wear("Censer");
            return c;
        }

        public void Pose(ModelActor a, string anim, float n, float dt)
        {
            var want = new Vector2(Mathf.Clamp(a.velocity.x * 3.2f, -48f, 48f), Mathf.Clamp(a.velocity.y * 3.2f, -48f, 48f));
            lean = Vector2.Lerp(lean, want, 1f - Mathf.Exp(-dt * 10f));
            pot.localRotation = Quaternion.Euler(lean.y, 0, -lean.x);
        }
    }

    /// <summary>A burning glass: three bronze legs, a yoke, a ring as wide as a shield, and the lens in it.
    /// The whole of it turns to look. The lens takes fire while it gathers, and keeps a crack for every time
    /// it has had its own light back.</summary>
    public class GlassProp : IPoser
    {
        Renderer fire, crack1, crack2;
        BurningGlass who;
        bool looked;

        public static GlassProp Make(ModelActor a)
        {
            var g = new GlassProp();
            var stand = new GameObject("stand").transform;
            stand.SetParent(a.rig, false);
            a.bones["stand"] = stand;
            var bones = new[] { stand };
            Color bronze = new Color(0.80f, 0.54f, 0.20f), dark = new Color(0.28f, 0.17f, 0.10f), glass = new Color(0.56f, 0.84f, 0.92f), lit = new Color(1f, 0.96f, 0.72f);
            const float top = 0.90f, cy = 1.36f, R = 0.36f;
            var kit = new Kit(a, a.rig, bones);
            kit.On("stand");
            for (int k = 0; k < 3; k++)
            {
                float an = (90f + k * 120f) * Mathf.Deg2Rad;
                var foot = new Vector3(Mathf.Cos(an) * 0.44f, 0, Mathf.Sin(an) * 0.44f);
                kit.Paint(bronze, 1).Tube(new[] { foot, Vector3.Lerp(foot, new Vector3(0, top, 0), 0.6f) + new Vector3(0, 0.03f, 0), new Vector3(0, top, 0) }, new[] { 0.032f, 0.036f, 0.046f }, 6);
                kit.Paint(dark).Egg(foot + new Vector3(0, 0.02f, 0), new Vector3(0.055f, 0.03f, 0.055f), 6, 3);
            }
            kit.Paint(bronze, 1).Egg(new Vector3(0, top, 0), new Vector3(0.10f, 0.085f, 0.10f), 8, 5);
            foreach (int side in new[] { -1, 1 })
            {
                kit.Paint(bronze, 1).Tube(new[] { new Vector3(0, top, 0), new Vector3(side * (R + 0.06f), top + 0.08f, 0), new Vector3(side * (R + 0.07f), cy, 0) }, new[] { 0.042f, 0.036f, 0.030f }, 6);
                kit.Paint(dark).Egg(new Vector3(side * (R + 0.07f), cy, 0), Vector3.one * 0.05f, 6, 4);          // the pin the ring hangs on
            }
            // the ring: it faces the way the whole thing looks
            var path = new Vector3[17];
            var thick = new float[17];
            for (int i = 0; i < 17; i++)
            {
                float th = i / 16f * Mathf.PI * 2f;
                path[i] = new Vector3(Mathf.Cos(th) * R, cy + Mathf.Sin(th) * R, 0);
                thick[i] = 0.052f;
            }
            kit.Paint(bronze, 1).Tube(path, thick, 6);
            for (int i = 0; i < 4; i++)
            {
                float th = (45f + i * 90f) * Mathf.Deg2Rad;
                kit.Paint(new Color(0.96f, 0.78f, 0.30f), 1).Egg(new Vector3(Mathf.Cos(th) * R, cy + Mathf.Sin(th) * R, 0), Vector3.one * 0.07f, 6, 4);
            }
            kit.Paint(glass, 0.6f, 0.3f).Egg(new Vector3(0, cy, 0), new Vector3(R - 0.03f, R - 0.03f, 0.08f), 14, 8);
            kit.Wear("Glass");
            // the lens with the light in it
            var fk = new Kit(a, a.rig, bones);
            fk.On("stand").Paint(lit, 0, 3f).Egg(new Vector3(0, cy, 0), new Vector3(R - 0.06f, R - 0.06f, 0.095f), 14, 8);
            g.fire = fk.Wear("Fire");
            g.fire.enabled = false;
            // a crack for each time
            Color black = new Color(0.06f, 0.09f, 0.13f);
            Renderer Crack(string name, params (Vector2 a, Vector2 b)[] lines)
            {
                var ck = new Kit(a, a.rig, bones);
                ck.On("stand").Paint(black);
                foreach (var (p, q) in lines)
                    foreach (int face in new[] { -1, 1 })
                    {
                        var d = (q - p).normalized;
                        ck.Frame(new Vector3((p.x + q.x) * 0.5f, cy + (p.y + q.y) * 0.5f, face * 0.088f), new Vector3(d.x, d.y, 0), new Vector3(-d.y, d.x, 0), Vector3.forward);
                        ck.Box(Vector3.zero, new Vector3((q - p).magnitude, 0.022f, 0.012f));
                    }
                ck.Frame();
                var r = ck.Wear(name);
                r.enabled = false;
                return r;
            }
            g.crack1 = Crack("Crack1", (new Vector2(-0.24f, 0.16f), new Vector2(-0.02f, 0.02f)), (new Vector2(-0.02f, 0.02f), new Vector2(0.10f, -0.20f)), (new Vector2(-0.02f, 0.02f), new Vector2(0.16f, 0.10f)));
            g.crack2 = Crack("Crack2", (new Vector2(0.26f, 0.08f), new Vector2(0.06f, -0.04f)), (new Vector2(-0.20f, -0.18f), new Vector2(-0.04f, -0.06f)), (new Vector2(-0.10f, 0.26f), new Vector2(-0.06f, 0.10f)));
            return g;
        }

        public void Pose(ModelActor a, string anim, float n, float dt)
        {
            if (!looked) { looked = true; who = a.sr ? a.sr.GetComponentInParent<BurningGlass>() : null; }
            // gathering, the light comes and goes faster and faster; let go, it is simply there
            bool on = anim == "fire" || (anim == "gather" && Mathf.Repeat(a.life * (5f + a.life % 1f * 9f), 1f) < 0.6f);
            if (fire) fire.enabled = on;
            int c = who ? who.Cracks : anim == "cracked" ? 2 : 0;
            if (crack1) crack1.enabled = c >= 1;
            if (crack2) crack2.enabled = c >= 2;
        }
    }
}
