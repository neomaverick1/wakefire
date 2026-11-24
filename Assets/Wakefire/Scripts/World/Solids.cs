// Top-down collision: every solid thing is an axis-aligned box in tile units, tagged with the
// world it exists in. Movers slide along walls one axis at a time, like the classic games.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Solid
    {
        public Rect r;
        public WorldLayer layer;
        public bool enabled = true;
        public bool pit;          // water or a drop: walls you can't enter, that swallow you if the world changes under you
        public bool low;          // the edge of a raised floor: it stops feet, and nothing that is in the air
        public Vector2 drop;      // ...the way down off it (zero: there is none), and how far down that is, in tiles
        public float fall;
        public Object owner;
    }

    public static class Solids
    {
        static readonly List<Solid> all = new List<Solid>();
        public static IReadOnlyList<Solid> All => all;

        public static void Clear() => all.Clear();

        public static Solid Add(Rect r, WorldLayer layer = WorldLayer.Both, Object owner = null)
        {
            var s = new Solid { r = r, layer = layer, owner = owner };
            all.Add(s);
            return s;
        }

        public static void Remove(Solid s) => all.Remove(s);

        static bool Active(Solid s, Vector2 at)
        {
            if (!s.enabled) return false;
            if (s.layer == WorldLayer.Both || Dream.I == null) return true;
            bool dream = Dream.I.IsDreamAt(at);
            return (s.layer == WorldLayer.Dream) == dream;
        }

        public static bool Overlaps(Rect r, Vector2 at, Object ignore = null)
        {
            foreach (var s in all)
                if (s.owner != ignore && s.r.Overlaps(r) && Active(s, at)) return true;
            return false;
        }

        /// <summary>For things in the air: walls and furniture stop them; water, drops and the edges of raised floors do not.</summary>
        public static bool Blocks(Rect r, Vector2 at, Object ignore = null)
        {
            foreach (var s in all)
                if (!s.pit && !s.low && s.owner != ignore && s.r.Overlaps(r) && Active(s, at)) return true;
            return false;
        }

        /// <summary>Standing in the edge of a raised floor, which nothing should be (the world moved under him).</summary>
        public static bool InEdge(Rect r)
        {
            foreach (var s in all)
                if (s.low && s.enabled && s.r.Overlaps(r)) return true;
            return false;
        }

        public static Solid FirstOverlap(Rect r, Vector2 at)
        {
            foreach (var s in all)
                if (s.r.Overlaps(r) && Active(s, at)) return s;
            return null;
        }

        /// <summary>Move a box (centre p, half size h) by d, sliding along walls. Returns the new centre.</summary>
        public static Vector2 Move(Vector2 p, Vector2 d, Vector2 h, Object ignore = null)
        {
            const int steps = 4;
            Vector2 step = d / steps;
            for (int i = 0; i < steps; i++)
            {
                var nx = new Vector2(p.x + step.x, p.y);
                if (!Overlaps(new Rect(nx - h, h * 2), nx, ignore)) p = nx;
                else
                {
                    // corner help: nudge round small edges so you don't snag on them
                    foreach (float nudge in new[] { 0.06f, -0.06f, 0.12f, -0.12f })
                    {
                        var t = new Vector2(p.x + step.x, p.y + nudge);
                        if (Mathf.Abs(step.y) < 0.0001f && !Overlaps(new Rect(t - h, h * 2), t, ignore)) { p = new Vector2(p.x, p.y + Mathf.Sign(nudge) * 0.02f); break; }
                    }
                }
                var ny = new Vector2(p.x, p.y + step.y);
                if (!Overlaps(new Rect(ny - h, h * 2), ny, ignore)) p = ny;
                else
                {
                    foreach (float nudge in new[] { 0.06f, -0.06f, 0.12f, -0.12f })
                    {
                        var t = new Vector2(p.x + nudge, p.y + step.y);
                        if (Mathf.Abs(step.x) < 0.0001f && !Overlaps(new Rect(t - h, h * 2), t, ignore)) { p = new Vector2(p.x + Mathf.Sign(nudge) * 0.02f, p.y); break; }
                    }
                }
            }
            return p;
        }
    }
}
