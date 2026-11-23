// What leaves Azar's hand. A sling stone flies straight and fast until it meets something. The
// huntsman's throwing stick flies out turning, comes back to the hand that threw it, and brings
// along any small thing it passed over on the way. Both ring gongs, break jars and sting whatever
// they hit; neither cares what is under it, so pits and water are no obstacle.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Thrown : MonoBehaviour
    {
        public static readonly List<Thrown> All = new List<Thrown>();
        public string kind;
        public Vector2 pos, vel;
        Player owner;
        float life, spin, reach;
        bool back;
        SpriteRenderer sr, shadow;
        Sprite[] frames;
        readonly List<Pickup> carried = new List<Pickup>();
        readonly HashSet<Object> struck = new HashSet<Object>();

        /// <summary>How many of these are in the air (there is only one throwing stick).</summary>
        public static int Out(string kind)
        {
            int n = 0;
            foreach (var t in All) if (t && t.kind == kind) n++;
            return n;
        }

        public static Thrown Launch(string kind, Player p, Vector2 dir)
        {
            var go = new GameObject("Thrown " + kind);
            go.transform.SetParent(Map.Current ? Map.Current.transform : null, false);
            var t = go.AddComponent<Thrown>();
            t.kind = kind;
            t.owner = p;
            t.pos = p.pos + dir * 0.55f;
            bool stick = kind == "stick";
            t.vel = dir.normalized * (stick ? 11.5f : 15f);
            t.reach = stick ? 6.2f : 9.5f;
            var body = new GameObject("Sprite");
            body.transform.SetParent(go.transform, false);
            t.sr = body.AddComponent<SpriteRenderer>();
            t.sr.sharedMaterial = Map.SpriteMat;
            t.frames = stick
                ? new[] { Map.GetSprite("Items/stick_0", 6, 6), Map.GetSprite("Items/stick_1", 6, 6), Map.GetSprite("Items/stick_2", 6, 6), Map.GetSprite("Items/stick_3", 6, 6) }
                : new[] { Map.GetSprite("Items/sling_stone", 3, 3) };
            t.sr.sprite = t.frames[0];
            t.shadow = Npc.MakeShadow(go.transform, WorldLayer.Both, 5);
            All.Add(t);
            Sfx.Play(stick ? "stick_fly" : "sling_shot", 0.8f, 0.05f);
            t.Place();
            return t;
        }

        void OnDestroy() => All.Remove(this);

        void Place()
        {
            transform.position = new Vector3(pos.x, pos.y, 0);
            sr.transform.localPosition = new Vector3(0, 0.62f, 0);
            sr.sortingOrder = Map.Order(pos.y) + 2;
            if (shadow) shadow.sortingOrder = Map.Order(pos.y) - 1;
        }

        void Update()
        {
            if (Game.Paused) return;
            float dt = Time.deltaTime;
            life += dt;
            bool stick = kind == "stick";
            if (stick)
            {
                spin += dt * 22f;
                sr.sprite = frames[(int)spin % frames.Length];
                if (!back && (life * 11.5f > reach)) Turn();
                if (back)
                {
                    // home to the hand, faster the longer it has been out
                    var home = (owner ? owner.pos : pos) - pos;
                    if (home.magnitude < 0.5f) { Caught(); return; }
                    vel = home.normalized * Mathf.Min(16f, 11.5f + life * 2f);
                }
            }
            var step = vel * dt;
            pos += step;
            foreach (var c in carried) if (c) c.pos = pos;
            Place();
            if (Strike()) return;
            if (!stick && life * 15f > reach) { Drop(); return; }
            if (life > 6f) { if (stick) Caught(); else Drop(); }
        }

        void Turn() { back = true; struck.Clear(); }

        /// <summary>Everything the thing in the air can meet this frame. True if it is gone.</summary>
        bool Strike()
        {
            bool stick = kind == "stick";
            var r = new Rect(pos - new Vector2(0.32f, 0.3f), new Vector2(0.64f, 0.9f));
            var map = Map.Current;
            if (map)
            {
                for (int i = map.props.Count - 1; i >= 0; i--)
                {
                    var pr = map.props[i];
                    if (!pr || struck.Contains(pr)) continue;
                    if (pr.Kind != "pot" && pr.Kind != "gong" && pr.Kind != "bush") continue;
                    if (pr.data.layer != 0 && Dream.I && (Dream.I.IsDreamAt(pr.basePos) != (pr.data.layer == 2))) continue;
                    if (!pr.Bounds.Overlaps(r)) continue;
                    struck.Add(pr);
                    if (pr.Kind == "gong") { if (owner) owner.Notify(pr); if (stick) { if (!back) Turn(); } else { Drop(); return true; } }
                    else if (pr.Kind == "pot")
                    {
                        map.props.RemoveAt(i); pr.Shatter(); Sfx.Play("pot_break"); Pickup.Chance(pr.basePos, 0.5f, 0.15f);
                        if (!stick) { Drop(); return true; }
                    }
                    else if (stick) { map.props.RemoveAt(i); pr.Cut(); Sfx.Play("cut"); Pickup.Chance(pr.basePos, 0.18f, 0.08f); }
                }
            }
            foreach (var h in FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None))
            {
                if (!(h is IHittable hit) || h == this || (owner && h.gameObject == owner.gameObject) || struck.Contains(h)) continue;
                Vector2 hp = h.transform.position;
                bool inReach = h is IHitBox hb ? hb.HitBox.Overlaps(r) : (r.Contains(hp) || r.Contains(hp + new Vector2(0, 0.4f)));
                if (!inReach) continue;
                struck.Add(h);
                if (hit.Hit(new HitInfo { damage = 1, from = pos - vel.normalized, knockback = stick ? 3.5f : 5f, kind = HitKind.Thrown, source = gameObject }))
                {
                    HitStop.Do(0.03f);
                    if (stick) { if (!back) Turn(); }
                    else { Drop(); return true; }
                }
            }
            if (stick)
            {
                // small things come back with it
                foreach (var pk in Pickup.All)
                    if (pk && !carried.Contains(pk) && Vector2.Distance(pk.pos, pos) < 0.7f) carried.Add(pk);
            }
            // walls stop a stone and turn a stick (pits and water are only floor it does not need)
            if (Solids.Blocks(new Rect(pos - new Vector2(0.12f, 0.1f), new Vector2(0.24f, 0.2f)), pos, this))
            {
                if (stick) { if (!back) { Turn(); Sfx.Play("stick_knock", 0.6f, 0.05f); Fx.Sparks(pos + new Vector2(0, 0.6f), new Color(1f, 0.9f, 0.6f), 3); } }
                else { Drop(); return true; }
            }
            return false;
        }

        /// <summary>A stone's flight ends: a puff, a click, nothing to pick up.</summary>
        void Drop()
        {
            Fx.Dust(pos, 3);
            Fx.Sparks(pos + new Vector2(0, 0.6f), new Color(0.9f, 0.85f, 0.75f), 3);
            Sfx.Play("sling_hit", 0.6f, 0.08f);
            Destroy(gameObject);
        }

        void Caught()
        {
            Sfx.Play("stick_catch", 0.7f, 0.04f);
            Destroy(gameObject);
        }
    }
}
