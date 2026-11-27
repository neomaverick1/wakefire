// Stairs up the front of a house, and ladders. Neither is a place a man walks about on: he is on
// it or he is off it, and while he is on it there is only up and down. The map marks each as a
// "rail": where its foot is, and its head. Walking on to the foot carries him up it to the roof;
// walking back on to its head carries him down to the street. So does the action button, which
// says "Climb" whenever he is standing at either end of one. Once he is on it he goes the whole
// way by himself, unless the stick is pushed back the way he came.
using UnityEngine;

namespace Wakefire
{
    public partial class Player
    {
        MarkerJson rail;
        readonly Vector2[] railPts = new Vector2[4];
        readonly float[] railLen = new float[3];
        Vector2 railUp;
        float railS, railTotal, railStep, railGo;
        bool railLadder;

        /// <summary>How near the foot of one (or the head, up on the roof) he has to be standing for the action button to offer it.</summary>
        const float RailReach = 0.8f;

        /// <summary>Standing at the foot of a stair or a ladder, or at the head of one.</summary>
        bool RailNear(out MarkerJson found, out bool foot)
        {
            found = null; foot = false;
            var map = Map.Current;
            if (!map) return false;
            float best = RailReach;
            foreach (var mk in map.data.markers)
            {
                if (mk.kind != "rail") continue;
                RailPoints(mk, railPts);
                float df = Vector2.Distance(pos, railPts[0]), dh = Vector2.Distance(pos, railPts[3]);
                if (df < best) { best = df; found = mk; foot = true; }
                if (dh < best) { best = dh; found = mk; foot = false; }
            }
            return found != null;
        }

        void StartRail(MarkerJson mk, bool foot)
        {
            RailPoints(mk, railPts);
            // he steps across to it from wherever he was standing
            if (foot) railPts[0] = pos; else railPts[3] = pos;
            rail = mk;
            railUp = (railPts[2] - railPts[1]).normalized;
            railLadder = mk.who == "ladder";
            railTotal = 0;
            for (int i = 0; i < 3; i++) { railLen[i] = Vector2.Distance(railPts[i], railPts[i + 1]); railTotal += railLen[i]; }
            railS = foot ? 0.01f : railTotal - 0.01f;
            railGo = foot ? 1 : -1;
            railStep = 0;
            state = State.Rail;
            stateClock = 0;
            vel = Vector2.zero;
            ledgeClock = 0;
        }

        /// <summary>On a stair or a ladder, between the street and a roof.</summary>
        public bool OnRail => rail != null;

        static void RailPoints(MarkerJson mk, Vector2[] p)
        {
            Vector2 a = Map.ToWorld(mk.x, mk.y), b = Map.ToWorld(mk.x + mk.w, mk.y + mk.h);
            bool ladder = mk.who == "ladder";
            p[1] = a; p[2] = b;
            p[0] = ladder ? a + new Vector2(0, -0.28f) : a + new Vector2(b.x > a.x ? -0.56f : 0.56f, 0);     // on the street, clear of the foot
            p[3] = b + new Vector2(0, 0.72f);                                                               // on the roof, clear of the edge
        }

        /// <summary>Free, and walking at the foot of a stair or back at the head of one: he is on it.</summary>
        bool TakeRail(Vector2 input)
        {
            var map = Map.Current;
            if (!map || input.sqrMagnitude < 0.2f) return false;
            var dir = input.normalized;
            foreach (var mk in map.data.markers)
            {
                if (mk.kind != "rail") continue;
                RailPoints(mk, railPts);
                Vector2 up = (railPts[2] - railPts[1]).normalized;
                bool ladder = mk.who == "ladder";
                // a ladder is climbed by walking up at it; a stair along a wall by walking along the wall at its foot
                // (so that a door beside the foot of a stair is still a door). Either is left by walking back at its head.
                float on = ladder ? dir.y : dir.x * Mathf.Sign(up.x);
                bool foot = on > 0.6f && Vector2.Distance(pos, railPts[0]) < 0.6f;
                bool head = (on < -0.6f || dir.y < -0.6f) && Vector2.Distance(pos, railPts[3]) < 0.6f;
                if (!foot && !head) continue;
                StartRail(mk, foot);
                return true;
            }
            return false;
        }

        Vector2 RailAt(float s)
        {
            for (int i = 0; i < 3; i++)
            {
                if (s <= railLen[i] || i == 2) return Vector2.Lerp(railPts[i], railPts[i + 1], railLen[i] > 0.001f ? Mathf.Clamp01(s / railLen[i]) : 1f);
                s -= railLen[i];
            }
            return railPts[3];
        }

        void RailUpdate(Vector2 input, float dt)
        {
            vel = Vector2.zero;
            health.invulnerable = Mathf.Max(health.invulnerable, 0.12f);
            float along = input.sqrMagnitude > 0.01f ? Vector2.Dot(input, railUp) : 0f;
            // he goes the whole way by himself; pushed back the way he came, he turns round on it
            if (Mathf.Abs(along) > 0.45f) railGo = Mathf.Sign(along);
            float pace = speed * (railLadder ? 0.46f : 0.72f);
            float ds = railGo * pace * dt;
            railS += ds;
            if (Mathf.Abs(ds) > 0)
            {
                bool rising = ds > 0;
                Facing f = railLadder ? Facing.Up : (railUp.x > 0) == rising ? Facing.Right : Facing.Left;
                facing = f;
                anim.Play("run", f);
                anim.SetFacing(f);
                railStep += Mathf.Abs(ds);
                if (railStep > (railLadder ? 0.42f : 0.5f))
                {
                    railStep = 0;
                    Sfx.Play(railLadder ? "step_wood" + ((int)(railS * 3) & 1) : "step" + ((int)(railS * 3) & 1), railLadder ? 0.5f : 0.34f, 0.08f);
                }
            }
            else anim.Play("idle", facing);
            if (railS <= 0 || railS >= railTotal)
            {
                pos = railS <= 0 ? railPts[0] : railPts[3];
                rail = null;
                state = State.Free;
                stateClock = 0;
                lastSafe = pos;
                return;
            }
            pos = RailAt(railS);
        }

        /// <summary>Taken off whatever he was climbing (the map went, a story took him by the hand).</summary>
        public void DropRail() { rail = null; }
    }
}
