// Waking and dreaming. Nodding off sends a ring out from Azar: everything the ring has passed
// is in the dream (repainted, dream-only things solid, waking-only things gone); waking up sends
// the ring out the other way. Drowsiness limits how long he can stay under.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public enum WorldLayer { Both = 0, Waking = 1, Dream = 2 }

    public class Dream : MonoBehaviour
    {
        public static Dream I;
        public bool Dreaming { get; private set; }
        public float Amount { get; private set; }
        public float Drowsiness = 1f;          // 1 = rested enough to nod off
        public float Seconds = 7f;             // a full meter lasts this long under
        public bool Locked;
        public event Action<bool> Flipped;
        public event Action ForcedWake;

        Vector2 center;
        float radius = 9999f, glow;
        bool insideIsDream;
        float clock = 99f, regen;
        const float Speed = 30f;               // tiles per second

        public static Dream Create()
        {
            var go = new GameObject("Dream");
            DontDestroyOnLoad(go);
            I = go.AddComponent<Dream>();
            return I;
        }

        /// <summary>The ring is on its way out across the map: both worlds are on screen at once.</summary>
        public bool Sweeping => radius < 9999f;

        public bool IsDreamAt(Vector2 p)
        {
            bool inside = Vector2.Distance(p, center) <= radius;
            return insideIsDream ? inside : !inside;
        }

        public bool Flip(Vector2 from, bool toDream)
        {
            if (toDream == Dreaming) return false;
            if (toDream && (Locked || Drowsiness < 0.15f)) return false;
            Dreaming = toDream;
            center = from;
            insideIsDream = toDream;
            radius = 0;
            clock = 0;
            glow = 1;
            Flipped?.Invoke(toDream);
            return true;
        }

        public void SetInstant(bool toDream)
        {
            Dreaming = toDream;
            insideIsDream = toDream;
            radius = 9999;
            glow = 0;
            Amount = toDream ? 1 : 0;
        }

        void Update()
        {
            float dt = Time.deltaTime;
            clock += dt;
            if (radius < 9999)
            {
                radius += Speed * dt * Mathf.Lerp(0.4f, 1.6f, Mathf.Clamp01(clock * 2f));
                glow = Mathf.Clamp01(1.2f - clock * 0.6f);
                if (radius > 120f) { radius = 9999; glow = 0; }
            }
            Amount = Mathf.MoveTowards(Amount, Dreaming ? 1 : 0, dt * 2.2f);
            bool scene = Story.I && Story.I.Running;
            if (Dreaming && !scene)
            {
                Drowsiness -= dt / Mathf.Max(1f, Seconds);
                regen = 0.8f;
                if (Drowsiness <= 0)
                {
                    Drowsiness = 0;
                    ForcedWake?.Invoke();
                }
            }
            else if (!Dreaming)
            {
                regen -= dt;
                if (regen <= 0) Drowsiness = Mathf.MoveTowards(Drowsiness, 1f, dt / 2.6f);
            }
            Shader.SetGlobalVector("_WF_Flip", new Vector4(center.x, center.y, 0, radius));
            Shader.SetGlobalVector("_WF_FlipState", new Vector4(insideIsDream ? 1 : 0, glow, Amount, Time.time));
        }
    }
}
