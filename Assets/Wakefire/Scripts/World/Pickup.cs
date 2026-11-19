// Things that drop and get picked up: silver shekels (1), gold bars (5) and flames of life.
// They pop out with a little arc, bob, blink before they fade, and fly to Azar when touched.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Pickup : MonoBehaviour
    {
        public enum Kind { Shekel, Gold, Flame }
        public static readonly List<Pickup> All = new List<Pickup>();

        public Kind kind;
        public Vector2 pos;
        public bool permanent;
        float z, vz, life, frameClock;
        Vector2 vel;
        SpriteRenderer sr, shadow;
        Sprite[] frames;

        public static Pickup Drop(Kind k, Vector2 at, bool pop = true, bool permanent = false)
        {
            var go = new GameObject("Pickup " + k);
            go.transform.SetParent(Map.Current ? Map.Current.transform : null, false);
            var p = go.AddComponent<Pickup>();
            p.kind = k;
            p.pos = at;
            p.permanent = permanent;
            var body = new GameObject("Sprite");
            body.transform.SetParent(go.transform, false);
            p.sr = body.AddComponent<SpriteRenderer>();
            p.sr.sharedMaterial = Map.SpriteMat;
            p.frames = k switch
            {
                Kind.Shekel => new[] { Item("shekel_0"), Item("shekel_2"), Item("shekel_1"), Item("shekel_2") },
                Kind.Gold => new[] { Item("gold_bar") },
                _ => new[] { Item("flame_0"), Item("flame_1") },
            };
            p.sr.sprite = p.frames[0];
            p.shadow = Npc.MakeShadow(go.transform, WorldLayer.Both, 6);
            if (pop)
            {
                p.vel = Random.insideUnitCircle * 1.6f;
                p.vz = Random.Range(5f, 7f);
                p.z = 0.2f;
            }
            All.Add(p);
            p.Place();
            return p;
        }

        static Sprite Item(string name) => Map.GetSprite("Items/" + name, name.StartsWith("gold") ? 5 : 4, name.StartsWith("flame") ? 11 : 8);

        /// <summary>What a cut bush or broken jar might give up.</summary>
        public static void Chance(Vector2 at, float shekel = 0.3f, float flame = 0.08f)
        {
            var p = Player.I;
            float r = Random.value;
            bool hurt = p && p.health.hp < p.health.max;
            if (hurt && r < flame * 2.2f) Drop(Kind.Flame, at);
            else if (r < shekel) Drop(Random.value < 0.08f ? Kind.Gold : Kind.Shekel, at);
        }

        void OnDestroy() => All.Remove(this);

        void Update()
        {
            if (Game.Paused) return;
            float dt = Time.deltaTime;
            life += dt;
            if (z > 0 || vz > 0)
            {
                vz -= 22f * dt;
                z += vz * dt;
                pos = Solids.Move(pos, vel * dt, new Vector2(0.15f, 0.08f), this);
                if (z <= 0) { z = 0; vz = Mathf.Abs(vz) > 3f ? -vz * 0.35f : 0; vel *= 0.5f; if (vz > 0) Sfx.Play("coin_bounce", 0.4f); }
            }
            frameClock += dt * (kind == Kind.Flame ? 6f : 7f);
            sr.sprite = frames[(int)frameClock % frames.Length];
            if (!permanent && life > 9f) sr.enabled = ((int)(life * 12)) % 2 == 0;
            if (!permanent && life > 11f) { Destroy(gameObject); return; }
            var pl = Player.I;
            if (pl && life > 0.25f && z < 0.3f && Vector2.Distance(pl.pos + new Vector2(0, 0.3f), pos) < 0.62f) Collect(pl);
            Place();
        }

        void Collect(Player p)
        {
            switch (kind)
            {
                case Kind.Shekel: p.coins += 1; Sfx.Play("coin", 0.8f); break;
                case Kind.Gold: p.coins += 5; Sfx.Play("coin_big", 0.9f); break;
                case Kind.Flame: p.health.Heal(2); Sfx.Play("flame_get", 0.9f); break;
            }
            Fx.Sparks(pos + new Vector2(0, 0.3f), kind == Kind.Flame ? new Color(1f, 0.7f, 0.3f) : new Color(0.95f, 0.95f, 1f), 5);
            Destroy(gameObject);
        }

        void Place()
        {
            float bob = z <= 0 ? Mathf.Round(Mathf.Sin(life * 4f) * 1f) / 16f : 0;
            transform.position = new Vector3(pos.x, pos.y, 0);
            sr.transform.localPosition = new Vector3(0, Mathf.Round((z + 0.05f) * 16f) / 16f + bob, 0);
            sr.sortingOrder = Map.Order(pos.y) + 1;
            shadow.sortingOrder = Map.Order(pos.y);
        }
    }
}
