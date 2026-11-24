// Floors above the floor, and floors under it. The edge of a raised floor is a ledge: nothing
// walks off it or on to it, and what is thrown goes over it. Azar, leaning on one from above for
// a moment, hops down; the way back up is a flight of steps, or it is somewhere else. A hole with
// a floor under it he jumps into the same way, and comes down on whatever is below: another floor
// of the dungeon, or a room of this one that has no door.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public partial class Player
    {
        float ledgeClock;
        bool plunged;
        Vector3 plungeScale = Vector3.one;

        /// <summary>In the air between a raised floor and the one below it.</summary>
        public bool Hopping { get; private set; }

        /// <summary>The hole with a floor under it that a point of the map is in, if it is in one.</summary>
        public static MarkerJson HoleAt(Vector2 p)
        {
            var map = Map.Current;
            if (!map) return null;
            foreach (var mk in map.data.markers)
            {
                if (mk.kind != "drop") continue;
                var a = Map.ToWorld(mk.x, mk.y + mk.h);
                if (new Rect(a.x, a.y, mk.w / 16f, mk.h / 16f).Contains(p)) return mk;
            }
            return null;
        }

        /// <summary>Walking into the edge of a raised floor from above, or into the lip of a hole that has a
        /// floor under it: after a moment of leaning on it he goes over. True once he has gone.</summary>
        bool Lean(Vector2 input, float dt)
        {
            var d = Dir;
            if (Vector2.Dot(input.normalized, d) < 0.8f) { ledgeClock = 0; return false; }
            var probe = new Rect(pos - half + d * 0.16f, half * 2);
            bool dream = Dream.I && Dream.I.IsDreamAt(pos);
            Solid edge = null;
            MarkerJson hole = null;
            foreach (var s in Solids.All)
            {
                if (!s.enabled || !s.r.Overlaps(probe)) continue;
                if (s.low)
                {
                    if (s.drop != Vector2.zero && Vector2.Dot(s.drop, d) > 0.9f) edge = s;
                }
                else if (s.pit && !dream && s.layer != WorldLayer.Dream && hole == null)
                {
                    // (a dreamer does not jump: he is asleep on his feet as it is)
                    var c = new Vector2(Mathf.Clamp(pos.x + d.x * 0.6f, s.r.xMin + 0.05f, s.r.xMax - 0.05f), Mathf.Clamp(pos.y + d.y * 0.6f, s.r.yMin + 0.05f, s.r.yMax - 0.05f));
                    hole = HoleAt(c);
                }
            }
            if (edge == null && hole == null) { ledgeClock = 0; return false; }
            ledgeClock += dt;
            if (ledgeClock < (edge != null ? 0.24f : 0.42f)) return false;
            ledgeClock = 0;
            if (edge != null)
            {
                if (!HopTarget(edge, d, out var to)) return false;
                StartCoroutine(Hop(to));
                return true;
            }
            StartCoroutine(Plunge(hole, pos + d * (Mathf.Abs(d.x) > 0.5f ? half.x + 0.55f : half.y + 0.6f)));
            return true;
        }

        /// <summary>Where a hop off this edge comes down: just clear of the foot of it, and a little further if
        /// something is standing there.</summary>
        bool HopTarget(Solid s, Vector2 d, out Vector2 to)
        {
            to = pos;
            Vector2 foot;
            if (d.y < -0.5f) foot = new Vector2(pos.x, s.r.yMin - half.y - 0.14f);
            else if (d.x > 0.5f) foot = new Vector2(s.r.xMax + half.x + 0.14f, pos.y - s.fall);
            else if (d.x < -0.5f) foot = new Vector2(s.r.xMin - half.x - 0.14f, pos.y - s.fall);
            else return false;
            var room = Rooms.Of(pos);
            // (off a roof he comes down clear of the wall under it, however high that is)
            float reach = 1.5f + (d.y < -0.5f ? s.fall : 0f);
            for (float extra = 0; extra <= reach; extra += 0.25f)
            {
                var q = foot + d * extra;
                if (room != null && !room.rect.Contains(q)) break;
                if (Solids.Overlaps(new Rect(q - half, half * 2), q, this)) continue;
                to = q;
                return true;
            }
            return false;
        }

        IEnumerator Hop(Vector2 to)
        {
            Hopping = true;
            state = State.Cutscene;
            stateClock = 0;
            march = Vector2.zero;
            vel = Vector2.zero;
            health.invulnerable = Mathf.Max(health.invulnerable, 0.5f);
            Vector2 from = pos;
            float down = Mathf.Max(0, from.y - to.y);
            float time = 0.26f + (down > 1.5f ? 0.055f : 0.03f) * down;
            var t = anim.sr.transform;
            var rest = t.localPosition;
            anim.Play("run", facing, true);
            Sfx.Play("roll", 0.45f, 0.08f);
            for (float c = 0; c < time; c += Time.deltaTime)
            {
                float k = c / time;
                pos = Vector2.Lerp(from, to, k);
                t.localPosition = rest + new Vector3(0, Mathf.Sin(k * Mathf.PI) * 0.45f, 0);
                yield return null;
            }
            pos = to;
            t.localPosition = rest;
            Place();
            Sfx.Play(StepSound(0), 0.9f, 0.05f);
            Fx.Dust(pos, down > 1.5f ? 9 : 5);
            PixelView.I.Shake(down > 1.5f ? 2 : 1, down > 1.5f ? 0.14f : 0.08f);
            lastSafe = pos;
            state = State.Free;
            stateClock = 0;
            anim.Play("idle", facing, true);
            Hopping = false;
        }

        /// <summary>Over the lip and down a hole that has a floor under it.</summary>
        IEnumerator Plunge(MarkerJson hole, Vector2 into)
        {
            state = State.Cutscene;
            stateClock = 0;
            march = Vector2.zero;
            vel = Vector2.zero;
            health.invulnerable = Mathf.Max(health.invulnerable, 2.5f);
            var t = anim.sr.transform;
            var rest = t.localPosition;
            Vector2 from = pos;
            anim.Play("run", facing, true);
            if ((into - from).sqrMagnitude > 0.001f)
            {
                for (float c = 0; c < 0.2f; c += Time.deltaTime)
                {
                    float k = c / 0.2f;
                    pos = Vector2.Lerp(from, into, k);
                    t.localPosition = rest + new Vector3(0, Mathf.Sin(k * Mathf.PI) * 0.3f, 0);
                    yield return null;
                }
            }
            pos = into;
            t.localPosition = rest;
            Sfx.Play("fall");
            plungeScale = t.localScale;
            plunged = true;
            for (float c = 0; c < 0.4f; c += Time.deltaTime)
            {
                float k = 1 - c / 0.4f;
                t.localScale = new Vector3(plungeScale.x * k, plungeScale.y * k, 1);
                t.Rotate(0, 0, 600 * Time.deltaTime);
                yield return null;
            }
            t.localScale = new Vector3(0.001f, 0.001f, 1);
            if (Game.Busy)
            {
                // (something else has the game by the hand: he is put back on his feet where he stood)
                Unplunge();
                pos = lastSafe;
                state = State.Free;
                yield break;
            }
            Game.I.Drop(hole.id, hole.text);
        }

        void Unplunge()
        {
            var t = anim.sr.transform;
            t.localRotation = Quaternion.identity;
            if (plunged) { t.localScale = plungeScale; plunged = false; }
        }

        /// <summary>He arrives from above: out of the dark over the room, on to the floor, and a moment getting his breath.</summary>
        public IEnumerator Land()
        {
            state = State.Cutscene;
            stateClock = 0;
            march = Vector2.zero;
            vel = Vector2.zero;
            Face(Facing.Down);
            Unplunge();
            var t = anim.sr.transform;
            var rest = t.localPosition;
            anim.Play("hurt", Facing.Down, true);
            const float time = 0.36f;
            for (float c = 0; c < time; c += Time.deltaTime)
            {
                float k = c / time;
                t.localPosition = rest + new Vector3(0, 9f * (1 - k * k), 0);
                yield return null;
            }
            t.localPosition = rest;
            Sfx.Play("piece_down", 0.9f, 0.05f);
            PixelView.I.Shake(2, 0.2f);
            Fx.Dust(pos, 9);
            yield return new WaitForSeconds(0.35f);
            health.invulnerable = Mathf.Max(health.invulnerable, 1f);
            lastSafe = pos;
            state = State.Free;
            stateClock = 0;
            anim.Play("idle", facing, true);
        }
    }
}
