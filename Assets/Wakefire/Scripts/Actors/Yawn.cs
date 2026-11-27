// The Yawn. Somebody in the Lower Town yawned forty nights ago, just before the city went down,
// and the yawn is still going round. It has no body. It is seen only by the air it bends, the
// dust it carries, and what the sleepers do as it goes by: each one it reaches yawns, and passes
// it on to the next.
//
// It is catching. If it passes through Azar he yawns, and for as long as that takes he can do
// nothing else. Three, close together, and he is asleep on his feet: in the dream, whether he
// meant to go or not. A blade does nothing to it. Fire ends it. The mirror shield sends it back
// the way it came, and anything it goes through on the way falls asleep where it stands.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    /// <summary>Places where the air is bent this frame: the last pass of the picture pulls its pixels about them.</summary>
    public static class AirBend
    {
        const int Max = 4;
        static readonly Vector4[] bends = new Vector4[Max];
        static int count, frame = -1;

        /// <summary>A ripple at a place on the map (and how high off the ground it shows), so wide, so strong (pixels).</summary>
        public static void Add(Vector2 at, float height, float radius, float strength)
        {
            if (frame != Time.frameCount) { frame = Time.frameCount; count = 0; }
            if (count >= Max) return;
            bends[count++] = new Vector4(at.x, at.y + height, radius, strength);
        }

        /// <summary>Hands this frame's ripples to the shader (called by the view once the frame's work is done).</summary>
        public static void Push()
        {
            if (frame != Time.frameCount) count = 0;
            for (int i = count; i < Max; i++) bends[i] = Vector4.zero;
            Shader.SetGlobalVectorArray("_WF_Bends", bends);
            Shader.SetGlobalFloat("_WF_BendCount", count);
        }
    }

    public class Yawn : Enemy
    {
        enum S { Round, After, Back, Through }
        S s;
        Npc towards;
        readonly List<Npc> done = new List<Npc>();
        Vector2 dir = Vector2.right, through;
        float grow = 0f, mote, sigh, trying;
        const float Radius = 1.05f;

        /// <summary>How many he has caught lately (it wears off), for the droop of his eyes.</summary>
        public static int Caught;
        public static float CaughtClock;
        public static bool Told;
        /// <summary>How many sleepers it has been passed on by (all of them, all night).</summary>
        public static int Passed;
        /// <summary>Sent back off the mirror.</summary>
        public bool GoingBack => s == S.Back;

        public static Yawn Spawn(Vector2 at) => Make<Yawn>("moth", "fly", at, WorldLayer.Waking, 1, null);

        protected override void Init()
        {
            speed = 2.2f; half = new Vector2(0.3f, 0.2f); touchDamage = 0; flying = true; roams = true;
            mat.SetFloat("_Dissolve", 1.05f);                   // there is nothing to see
            if (shadow) { Destroy(shadow.gameObject); shadow = null; }
        }

        public override bool Sleeps => false;

        protected override bool WaitsOutStories => true;
        protected override bool Untouchable(HitInfo h) => true;      // there is nothing to hit, either
        public override Rect HitBox => new Rect(pos.x - 0.2f, pos.y - 0.2f, 0.4f, 0.4f);

        Npc NextSleeper()
        {
            Npc best = null;
            float bd = 14f;
            foreach (var n in Npc.All)
            {
                if (!n || !n.Present || n.layer != WorldLayer.Waking || done.Contains(n)) continue;
                if (n.anim.anim != "sleep" && n.anim.anim != "lean" && n.anim.anim != "lie" && n.anim.anim != "knead") continue;
                float d = Vector2.Distance(n.pos, pos);
                if (d < bd) { bd = d; best = n; }
            }
            if (!best && done.Count > 0) { done.Clear(); }
            return best;
        }

        protected override void Think(float dt, Player p)
        {
            grow = Mathf.MoveTowards(grow, 1f, dt * 1.5f);
            if (CaughtClock > 0 && (CaughtClock -= dt / Mathf.Max(1, CountAll())) <= 0) Caught = 0;
            var d = p.pos + new Vector2(0, 0.5f) - pos;
            bool sees = CanSee(p, 5.5f) && !p.Hidden;

            switch (s)
            {
                case S.Round:
                    if (sees && d.magnitude < 4.5f) { s = S.After; stateClock = 0; break; }
                    if (!towards) { towards = NextSleeper(); trying = 0; }
                    if (towards)
                    {
                        var to = towards.pos + new Vector2(0, 0.6f) - pos;
                        Steer(to, speed, dt);
                        if (to.magnitude < 0.45f) { PassOn(towards); done.Add(towards); towards = null; }
                        // (somebody it cannot get to: asleep on a roof, behind a wall. It gives them up for now.)
                        else if ((trying += dt) > 7f) { done.Add(towards); towards = null; }
                    }
                    else Steer(home - pos, speed * 0.5f, dt);
                    break;

                case S.After:
                    // a fresh mouth: it would rather have his
                    if (!sees || d.magnitude > 7f) { s = S.Round; break; }
                    Steer(d, speed * 1.25f, dt);
                    // the mirror, raised and facing it: back the way it came
                    if (d.magnitude < 1.3f && p.TryReflect(dir)) { s = S.Back; stateClock = 0; dir = -dir; Sfx.Play("yawn_back", 0.8f, 0.05f); break; }
                    if (d.magnitude < 0.45f && p.state != Player.State.Roll && Catch(p)) { s = S.Through; stateClock = 0; through = dir; }
                    break;

                case S.Through:
                    // it does not stop for him: on through and away
                    Drift(through * speed * 1.4f, dt);
                    if (stateClock > 2.2f) s = S.Round;
                    break;

                case S.Back:
                    // sent back: straight, fast, and anything standing in it goes to sleep
                    Drift(dir * 6.5f, dt);
                    foreach (var e in All)
                    {
                        if (!e || e == this || !e.Present || !e.Sleeps || e.asleep > 0.5f) continue;
                        if (Vector2.Distance(e.pos + new Vector2(0, 0.5f), pos) < 0.8f) { e.Sleep(6f); Sfx.Play("yawn_catch", 0.7f, 0.1f); }
                    }
                    if (stateClock > 1.6f) { Out(false); return; }
                    break;
            }

            // fire ends it: a lit bowl, or the Wakefire held out at it
            if (StayUp.Seared(pos - new Vector2(0, 0.5f), false)) { Out(true); return; }

            // what there is to see of it
            if (Present) AirBend.Add(pos, 0f, Radius * grow, 3.0f);
            if ((mote -= dt) <= 0)
            {
                mote = 0.09f;
                float a = Random.value * Mathf.PI * 2f;
                var off = new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.6f) * Radius * 0.8f;
                var swirl = new Vector2(-off.y, off.x).normalized * 1.3f + dir * 0.6f;
                bool leaf = Random.value < 0.12f;
                Fx.Spawn(pos - new Vector2(0, 0.5f) + off, swirl, 0.5f + Random.Range(-0.3f, 0.3f), Random.Range(-0.2f, 0.5f), Random.Range(0.35f, 0.7f),
                    leaf ? new Color(0.42f, 0.55f, 0.32f, 0.9f) : new Color(0.86f, 0.84f, 0.92f, 0.75f), leaf ? new Color(0.25f, 0.35f, 0.22f, 0f) : new Color(0.6f, 0.6f, 0.75f, 0f), 0.4f, leaf ? 2 : 1);
            }
            if ((sigh -= dt) <= 0 && sees) { sigh = Random.Range(3.5f, 6f); Sfx.Play("yawn_near", Mathf.Lerp(0.6f, 0.2f, d.magnitude / 6f), 0.08f); }
        }

        static int CountAll() { int n = 0; foreach (var e in All) if (e is Yawn) n++; return n; }

        void Steer(Vector2 to, float pace, float dt)
        {
            if (to.sqrMagnitude > 0.0004f) dir = Vector2.Lerp(dir, to.normalized, 1f - Mathf.Exp(-3.5f * dt)).normalized;
            Drift(dir * pace, dt);
        }

        void Drift(Vector2 v, float dt)
        {
            vel = v;
            var to = pos + v * dt;
            var m = Map.Current;
            if (m && !m.bounds.Contains(to)) { dir = -dir; return; }
            // it goes round a house, not through it
            if (Wall(to))
            {
                var slide = new Vector2(-v.y, v.x) * dt;
                if (!Wall(pos + slide)) { pos += slide; dir = Vector2.Lerp(dir, slide.normalized, 0.2f).normalized; }
                else if (!Wall(pos - slide)) { pos -= slide; dir = Vector2.Lerp(dir, -slide.normalized, 0.2f).normalized; }
                else dir = -dir;
                return;
            }
            pos = to;
        }

        /// <summary>Walls and furniture are in its way. People are not: people are what it is for.</summary>
        static bool Wall(Vector2 q)
        {
            var box = new Rect(q - new Vector2(0.2f, 0.7f), new Vector2(0.4f, 0.4f));
            foreach (var sd in Solids.All)
            {
                if (!sd.enabled || sd.pit || sd.low || sd.layer == WorldLayer.Dream) continue;
                if (sd.owner is Npc || sd.owner is Player || sd.owner is Enemy) continue;
                if (sd.r.Overlaps(box)) return true;
            }
            return false;
        }

        /// <summary>A sleeper it has reached: they yawn, and it goes on to the next.</summary>
        void PassOn(Npc n)
        {
            n.YawnNow();
            Passed++;
            Sfx.Play("yawn_pass", 0.5f, 0.12f);
        }

        /// <summary>It has gone through him. False if he is in no state to yawn (already asleep, in a story).</summary>
        bool Catch(Player p)
        {
            if (!p.YawnHelplessly()) return false;
            Caught++;
            CaughtClock = 22f;
            Sfx.Play("yawn_catch", 0.9f, 0.05f);
            if (Caught >= 3)
            {
                Caught = 0; CaughtClock = 0;
                p.AsleepOnHisFeet();
            }
            if (!Told && Story.I) { Told = true; Story.I.CaughtAYawn(); }
            return true;
        }

        void Out(bool burnt)
        {
            for (int i = 0; i < 10; i++)
                Fx.Spawn(pos - new Vector2(0, 0.5f) + Random.insideUnitCircle * 0.5f, Random.insideUnitCircle * 1.5f, 0.6f, Random.Range(0.2f, 1.2f), Random.Range(0.3f, 0.6f),
                    burnt ? new Color(1f, 0.85f, 0.5f, 0.9f) : new Color(0.86f, 0.84f, 0.92f, 0.8f), new Color(0.5f, 0.5f, 0.6f, 0f), -0.4f);
            if (burnt) Sfx.Play("yawn_out", 0.7f, 0.05f);
            if (spawnId != null && burnt) Story.Set("dead_" + spawnId);
            Rooms.Slain(this);
            Destroy(gameObject);
        }
    }
}
