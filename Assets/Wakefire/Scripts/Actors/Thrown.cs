// The Sun Wheel in the air. A bronze disc with an edge of gold, made for a king who missed the
// sun. It goes the way it is thrown, straight or across the corners, and a wall does not stop
// it: it banks off the first two it meets, and the third sends it home to the hand that threw it, through
// anything that is in the way; or sooner, if he holds up his hand for it (the item button
// again). Going out it rings gongs, cuts ropes, breaks jars and bites whatever it meets;
// something that turns a blade (a shield, a shell) turns the wheel too, and that is one of its
// two banks. Coming home it arrives from behind, which is the point of it: it bites on the
// way back as well, but it has stopped doing errands (a gong or a rope it passes through a wall
// on the way home is left alone). It does not care what is under it, so drops and water are
// only floor it does not need.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Thrown : MonoBehaviour
    {
        public static readonly List<Thrown> All = new List<Thrown>();
        /// <summary>How many walls turn it before one sends it home. (Out, back past him, out again: so it comes home
        /// from the far side, through whatever was standing between.)</summary>
        public const int MaxBanks = 2;
        const float Speed = 13f, Reach = 34f, Leash = 12f;

        public string kind;
        public Vector2 pos, vel;
        Player owner;
        float life, spin, flown;
        int banks;
        bool home;
        SpriteRenderer sr, shadow;
        Sprite[] frames;
        LightBlob glow;
        readonly HashSet<Object> struck = new HashSet<Object>();

        public int Banks => banks;
        public bool ComingHome => home;

        /// <summary>How many of these are in the air (there is only one Sun Wheel).</summary>
        public static int Out(string kind)
        {
            int n = 0;
            foreach (var t in All) if (t && t.kind == kind) n++;
            return n;
        }

        /// <summary>He holds up his hand: whatever is out turns for home now. True if anything was out.</summary>
        public static bool CallHome()
        {
            bool any = false;
            foreach (var t in All)
            {
                if (!t || t.home) continue;
                t.Turn();
                Fx.Sparks(t.pos + new Vector2(0, 0.6f), new Color(1f, 0.88f, 0.5f), 3);
                any = true;
            }
            if (any) Sfx.Play("wheel_call", 0.7f, 0.04f);
            return any;
        }

        /// <summary>The eight ways it can be thrown: the way the stick is held, or the way he is facing.</summary>
        public static Vector2 Aim(Vector2 held, Vector2 facing)
        {
            if (held.magnitude < 0.35f) return facing.normalized;
            float a = Mathf.Round(Mathf.Atan2(held.y, held.x) / (Mathf.PI / 4f)) * (Mathf.PI / 4f);
            return new Vector2(Mathf.Cos(a), Mathf.Sin(a)).normalized;
        }

        public static Thrown Launch(string kind, Player p, Vector2 dir)
        {
            var go = new GameObject("Thrown " + kind);
            go.transform.SetParent(Map.Current ? Map.Current.transform : null, false);
            var t = go.AddComponent<Thrown>();
            t.kind = kind;
            t.owner = p;
            dir = dir.normalized;
            t.pos = p.pos + dir * 0.6f;
            if (t.Wall(t.pos)) t.pos = p.pos;                 // thrown with his nose to a wall: it starts where he stands
            t.vel = dir * Speed;
            var body = new GameObject("Sprite");
            body.transform.SetParent(go.transform, false);
            t.sr = body.AddComponent<SpriteRenderer>();
            t.sr.sharedMaterial = Map.SpriteMat;
            t.frames = new[] { Map.GetSprite("Items/wheel_0", 6, 6), Map.GetSprite("Items/wheel_1", 6, 6), Map.GetSprite("Items/wheel_2", 6, 6), Map.GetSprite("Items/wheel_3", 6, 6) };
            t.sr.sprite = t.frames[0];
            t.shadow = Npc.MakeShadow(go.transform, WorldLayer.Both, 5);
            // it is the sun, in a small way: it takes its own light with it
            t.glow = LightBlob.Create(go.transform, t.pos, 2.8f, new Color(1f, 0.82f, 0.42f), 0.8f, false);
            t.glow.height = 0.6f;
            All.Add(t);
            Sfx.Play("wheel_fly", 0.8f, 0.03f);
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

        /// <summary>A wall, or the edge of the room he threw it in (it does not go visiting).</summary>
        bool Wall(Vector2 at)
        {
            if (Solids.Blocks(new Rect(at - new Vector2(0.14f, 0.1f), new Vector2(0.28f, 0.2f)), at, this)) return true;
            if (Rooms.I && Rooms.I.current != null)
            {
                var r = Rooms.I.current.rect;
                if (at.x < r.xMin + 0.3f || at.x > r.xMax - 0.3f || at.y < r.yMin + 0.3f || at.y > r.yMax - 0.3f) return true;
            }
            return false;
        }

        void Update()
        {
            if (Game.Paused) return;
            float dt = Time.deltaTime;
            life += dt;
            spin += dt * 26f;
            sr.sprite = frames[(int)spin % frames.Length];
            if (home)
            {
                var to = (owner ? owner.pos : pos) - pos;
                if (!owner || to.magnitude < 0.6f) { Caught(); return; }
                vel = to.normalized * Mathf.Min(20f, Speed + 2f + life * 1.5f);
                pos += vel * dt;
                Strike(false);                                          // (jars and brush in the way; it has stopped doing errands)
            }
            else
            {
                // in short steps (a slow frame must not carry it through a gong), one axis at a time, so it knows
                // which way the wall turned it
                float left = Speed * dt;
                flown += left;
                while (left > 0.0001f && !home)
                {
                    float part = Mathf.Min(left, 0.12f);
                    left -= part;
                    Vector2 step = vel.normalized * part;
                    bool hx = false, hy = false;
                    if (step.x != 0) { var nx = pos + new Vector2(step.x, 0); if (Wall(nx)) hx = true; else pos = nx; }
                    if (step.y != 0) { var ny = pos + new Vector2(0, step.y); if (Wall(ny)) hy = true; else pos = ny; }
                    Strike(false);                                      // gongs, ropes, jars: wherever it is this instant
                    if (hx || hy) Bank(hx, hy);
                }
                if (!home && (flown > Reach || (owner && Vector2.Distance(owner.pos, pos) > Leash && !Rooms.I))) Turn();
            }
            Place();
            Strike(true);
            if (life > 9f) Caught();
        }

        /// <summary>Off a wall: the third wall it meets sends it home instead.</summary>
        void Bank(bool x, bool y)
        {
            Sfx.Play("wheel_bank", 0.75f, 0.05f);
            Fx.Sparks(pos + new Vector2(0, 0.6f), new Color(1f, 0.88f, 0.5f), 4);
            if (banks >= MaxBanks) { Turn(); return; }
            banks++;
            if (x) vel.x = -vel.x;
            if (y) vel.y = -vel.y;
            struck.Clear();
        }

        /// <summary>Off something that turns a blade: back the way it came.</summary>
        void Turned()
        {
            Sfx.Play("clank", 0.9f, 0.04f);
            Fx.Sparks(pos + new Vector2(0, 0.6f), new Color(1f, 0.88f, 0.5f), 5);
            if (home) return;
            if (banks >= MaxBanks) { Turn(); return; }
            banks++;
            vel = -vel;
        }

        void Turn() { home = true; struck.Clear(); }

        /// <summary>Everything the wheel can meet where it is: the things that stand still (asked at every short step),
        /// and, once a frame, whatever is alive.</summary>
        void Strike(bool living)
        {
            var r = new Rect(pos - new Vector2(0.34f, 0.3f), new Vector2(0.68f, 0.9f));
            var map = Map.Current;
            if (map && !living && !home)
            {
                // a walled-up doorway does not stand up to it either
                Prop wall = null;
                foreach (var pr in map.props) if (pr && pr.Kind == "crack" && pr.sr.enabled && pr.Bounds.Overlaps(new Rect(r.x - 0.2f, r.y - 0.2f, r.width + 0.4f, r.height + 0.4f))) { wall = pr; break; }
                if (wall) Secrets.Break(wall);
            }
            if (map && !living)
            {
                for (int i = map.props.Count - 1; i >= 0; i--)
                {
                    var pr = map.props[i];
                    if (!pr || struck.Contains(pr)) continue;
                    string k = pr.Kind;
                    if (k != "pot" && k != "gong" && k != "bush" && k != "rope") continue;
                    if (home && (k == "gong" || k == "rope")) continue;         // coming home it goes through walls: no errands
                    if (pr.data.layer != 0 && Dream.I && (Dream.I.IsDreamAt(pr.basePos) != (pr.data.layer == 2))) continue;
                    if (!pr.sr.enabled || !(k == "rope" ? Rigging.Span(pr) : pr.Bounds).Overlaps(r)) continue;
                    struck.Add(pr);
                    if (k == "gong") { if (owner) owner.Notify(pr); }
                    else if (k == "rope") { map.props.RemoveAt(i); Rigging.Cut(pr); }
                    else if (k == "pot") { map.props.RemoveAt(i); pr.Shatter(); Sfx.Play("pot_break"); Pickup.Chance(pr.basePos, 0.5f, 0.15f); }
                    else { map.props.RemoveAt(i); pr.Cut(); Sfx.Play("cut"); Pickup.Chance(pr.basePos, 0.18f, 0.08f); }
                }
            }
            if (!living) return;
            foreach (var h in FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None))
            {
                if (!(h is IHittable hit) || h == this || (owner && h.gameObject == owner.gameObject) || struck.Contains(h)) continue;
                Vector2 hp = h.transform.position;
                bool inReach = h is IHitBox hb ? hb.HitBox.Overlaps(r) : (r.Contains(hp) || r.Contains(hp + new Vector2(0, 0.4f)));
                if (!inReach) continue;
                struck.Add(h);
                var info = new HitInfo { damage = 2, from = pos - vel.normalized * 0.7f, knockback = 4f, kind = HitKind.Thrown, source = gameObject };
                if (h is Enemy e && e.Present && !e.health.Dead && !e.Takes(info)) { Turned(); continue; }
                if (hit.Hit(info)) HitStop.Do(0.03f);
            }
        }

        void Caught()
        {
            Sfx.Play("wheel_catch", 0.7f, 0.04f);
            Destroy(gameObject);
        }
    }

    /// <summary>Ropes, and what hangs on them. A rope that is cut (the wheel does it from across a drop;
    /// so does a blade, from close enough) sets its flag, and whatever bridge carries the same name comes
    /// down across its drop and stays down.</summary>
    public static class Rigging
    {
        /// <summary>The run of a rope out over its drop, as something thrown meets it (a blade only reaches
        /// the middle of it, which is the part that is a long way out).</summary>
        public static Rect Span(Prop rope) => new Rect(rope.basePos.x - 0.6f, rope.basePos.y - 1.6f, 1.2f, 3.2f);

        public static void Cut(Prop rope)
        {
            if (!rope) return;
            string id = rope.data.id;
            Sfx.Play("cut", 1f, 0.02f);
            for (int i = 0; i < 10; i++)
                Fx.Spawn(rope.basePos + new Vector2(Random.Range(-0.2f, 0.2f), Random.Range(0.3f, 1.4f)), Random.insideUnitCircle * 1.6f, 0.4f, Random.Range(1f, 3f),
                    Random.Range(0.3f, 0.6f), new Color(0.78f, 0.66f, 0.42f), new Color(0.38f, 0.28f, 0.16f), 14f, 1);
            bool weight = rope.data.who == "weight";
            if (weight)
            {
                // what was hanging on it goes down the dark, and is heard from a moment later
                Sfx.Play("weight_fall", 1f, 0f);
                PixelView.I.Shake(2, 0.35f);
                Fx.Dust(rope.basePos + new Vector2(0, 0.4f), 8);
            }
            Object.Destroy(rope.gameObject);
            if (string.IsNullOrEmpty(id)) return;
            Story.Set("on_" + id);
            if (Map.Current)
                foreach (var pr in Map.Current.props)
                {
                    if (!pr || pr.data.id != id) continue;
                    if (pr.Kind == "plank") Pocket.Lay(pr, false);
                    else if (pr.Kind == "bridgeup") pr.Bar(false);          // it is not standing on end any more
                }
            if (Story.I) Story.I.RopeCut(id, weight);
        }
    }
}
