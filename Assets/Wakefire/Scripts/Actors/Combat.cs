// Shared combat plumbing: what a hit carries, things that can be hit, health, and the brief
// freeze on impact ("hit-stop") that makes every blow land.
using System;
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public enum HitKind { Slash, Heavy, Fire, Reflected, Crush, Fall }

    public struct HitInfo
    {
        public int damage;
        public Vector3 from;          // where the blow came from (for knockback)
        public float knockback;
        public HitKind kind;
        public GameObject source;
    }

    public interface IHittable
    {
        /// <summary>Returns true if the hit connected (for hit-stop and sparks).</summary>
        bool Hit(HitInfo h);
    }

    /// <summary>Something with a body worth aiming at: blades connect anywhere on this box, not
    /// just at its feet (a bull is a lot of bull).</summary>
    public interface IHitBox
    {
        Rect HitBox { get; }
    }

    public class Health : MonoBehaviour
    {
        public int max = 6, hp = 6;
        public float invulnerable;
        public event Action<HitInfo> Damaged;
        public event Action Died;
        public bool Dead => hp <= 0;

        void Update()
        {
            if (invulnerable > 0) invulnerable -= Time.deltaTime;
        }

        public bool Take(HitInfo h)
        {
            if (Dead || invulnerable > 0) return false;
            hp = Mathf.Max(0, hp - h.damage);
            Damaged?.Invoke(h);
            if (hp == 0) Died?.Invoke();
            return true;
        }

        public void Heal(int n) => hp = Mathf.Min(max, hp + n);
    }

    public static class HitStop
    {
        static MonoBehaviour host;
        static float until;

        public static void Do(float seconds)
        {
            if (!Game.I) return;
            until = Mathf.Max(until, Time.unscaledTime + seconds);
            if (host == null)
            {
                host = Game.I;
            }
            Time.timeScale = 0.02f;
            Game.I.StartCoroutine(Release());
        }

        static IEnumerator Release()
        {
            while (Time.unscaledTime < until) yield return null;
            if (!Game.Paused) Time.timeScale = 1f;
        }
    }
}
