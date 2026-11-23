// What the bars and doors of a dungeon answer to. A grille names what lifts it (in the map, as
// its text): a plate pressed, a gong struck, fires lit, a sun disc lit, a room cleared of what
// was guarding it. Things that happen set a flag in the story ("on_" + the thing's id), so what
// has been done stays done when Azar comes back, and anything can answer to anything.
//
//   plate:ID  gong:ID  disc:ID  on:ID     that thing has been pressed, struck, lit
//   off:ID                                 it has not (a gong that turns things over opens one grille and shuts another)
//   lit:A,B,C                              every one of those fires is burning
//   clear:ROOM                             nothing is left alive in that room
//   flag:NAME  noflag:NAME                 anything else the story knows
// Several, joined with ';', must all hold. A grille marked "shut" stands open until Azar walks
// into its room with something still alive in it; then it drops behind him, and stays down until
// what it answers to holds. Its room is the one it waits on ("clear:ROOM"), or the one it is told
// ("shut:ROOM", when it answers to something else).
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Mech : MonoBehaviour
    {
        public static Mech I;

        class Gate
        {
            public string id, say;
            public readonly List<Prop> props = new List<Prop>();
            public string[] conds;
            public bool shutter, armed, open;
            public string room;
        }

        readonly List<Gate> gates = new List<Gate>();
        readonly List<Rect> pools = new List<Rect>();
        Map map;
        float scan;
        float shine;
        Prop shining;
        SpriteRenderer beam;
        LightBlob beamLight;

        public static string ClearFlag(string mapName, string room) => "clear_" + mapName + "_" + room;

        public static void Setup(Map m)
        {
            I = m.gameObject.AddComponent<Mech>();
            I.map = m;
            I.Build();
        }

        void Build()
        {
            if (Story.Has("bars_z1")) Story.Set("on_z1_plate");           // a journey from before there were rooms
            var byId = new Dictionary<string, Gate>();
            var broken = new List<Prop>();
            foreach (var pr in map.props)
            {
                if (!pr) continue;
                switch (pr.Kind)
                {
                    case "bars":
                        if (string.IsNullOrEmpty(pr.data.text) || string.IsNullOrEmpty(pr.data.id)) break;
                        if (!byId.TryGetValue(pr.data.id, out var g))
                        {
                            g = new Gate { id = pr.data.id, conds = pr.data.text.Split(';'), say = pr.data.say };
                            g.shutter = !string.IsNullOrEmpty(pr.data.who) && pr.data.who.Contains("shut");
                            foreach (var c in g.conds) if (c.StartsWith("clear:")) g.room = c.Substring(6);
                            if (g.shutter)
                                foreach (var w in pr.data.who.Split(' ')) if (w.StartsWith("shut:")) g.room = w.Substring(5);
                            byId[g.id] = g;
                            gates.Add(g);
                        }
                        g.props.Add(pr);
                        break;
                    case "brazier":
                        if (!string.IsNullOrEmpty(pr.data.id) && Story.Has("on_" + pr.data.id)) pr.Ignite();
                        break;
                    case "bullhead":
                        if (string.IsNullOrEmpty(pr.data.id)) break;
                        if (Story.Has(pr.data.id)) { broken.Add(pr); break; }
                        var head = pr.gameObject.AddComponent<BullHead>();
                        head.prop = pr; head.flag = pr.data.id;
                        head.straight = !string.IsNullOrEmpty(pr.data.who) && pr.data.who.Contains("straight");
                        head.dormant = !string.IsNullOrEmpty(pr.data.who) && pr.data.who.Contains("herd");
                        if (!string.IsNullOrEmpty(pr.data.text) && float.TryParse(pr.data.text, System.Globalization.NumberStyles.Float, System.Globalization.CultureInfo.InvariantCulture, out float ph)) head.phase = ph;
                        break;
                    case "disc":
                        if (Story.Has("on_" + pr.data.id)) pr.SetSprite(pr.data.s + "_lit", pr.data.px, pr.data.py);
                        break;
                }
            }
            foreach (var pr in broken) { map.props.Remove(pr); Destroy(pr.gameObject); }
            foreach (var mk in map.data.markers)
                if (mk.kind == "pool")
                {
                    var a = Map.ToWorld(mk.x, mk.y + mk.h);
                    pools.Add(new Rect(a.x, a.y, mk.w / 16f, mk.h / 16f));
                }
            foreach (var g in gates) Put(g, Holds(g), true);
            map.PlatePressed += OnPlate;
            if (Player.I) Player.I.Interacted += OnNotify;
            Rooms.Entered += OnRoom;
            Twins();
        }

        void OnDestroy()
        {
            if (Player.I) Player.I.Interacted -= OnNotify;
            Rooms.Entered -= OnRoom;
            if (I == this) I = null;
        }

        void OnPlate(string id)
        {
            Story.Set("on_" + id);
        }

        void OnRoom(Room r)
        {
            if (!Rooms.I) return;
            foreach (var g in gates)
                if (g.shutter && g.room == r.id && !g.armed && !Story.Has(ClearFlag(Game.I.CurrentMap, r.id)) && Rooms.I.Left(r) > 0)
                    StartCoroutine(Arm(g));
        }

        IEnumerator Arm(Gate g)
        {
            yield return new WaitForSeconds(0.3f);
            g.armed = true;
        }

        void OnNotify(Prop pr)
        {
            if (!pr || pr.Kind != "gong") return;
            Sfx.Play("gong", 1f, 0.02f);
            PixelView.I.Shake(1, 0.12f);
            StartCoroutine(Swing(pr));
            string id = pr.data.id;
            if (string.IsNullOrEmpty(id)) return;
            if (!string.IsNullOrEmpty(pr.data.who) && pr.data.who.Contains("toggle"))
            {
                if (Story.Has("on_" + id)) Story.Clear("on_" + id); else Story.Set("on_" + id);
            }
            else Story.Set("on_" + id);
        }

        IEnumerator Swing(Prop pr)
        {
            string s = pr.data.s;
            for (int i = 0; i < 6 && pr; i++)
            {
                pr.SetSprite(s + (i % 2 == 0 ? "_a" : "_b"), pr.data.px, pr.data.py);
                yield return new WaitForSeconds(0.07f + i * 0.012f);
            }
            if (pr) pr.SetSprite(s, pr.data.px, pr.data.py);
        }

        bool Cond(Gate g, string c)
        {
            int k = c.IndexOf(':');
            string key = k < 0 ? c : c.Substring(0, k), arg = k < 0 ? "" : c.Substring(k + 1);
            switch (key)
            {
                case "plate": case "gong": case "disc": case "on": return Story.Has("on_" + arg);
                case "off": return !Story.Has("on_" + arg);
                case "lit":
                    foreach (var id in arg.Split(',')) if (!Story.Has("on_" + id)) return false;
                    return true;
                case "clear": return Story.Has(ClearFlag(Game.I.CurrentMap, arg));
                case "flag": return Story.Has(arg);
                case "noflag": return !Story.Has(arg);
            }
            return false;
        }

        bool Holds(Gate g)
        {
            if (g.shutter && !g.armed) return true;
            foreach (var c in g.conds) if (!Cond(g, c)) return false;
            return true;
        }

        void Put(Gate g, bool open, bool quiet)
        {
            g.open = open;
            Prop near = null;
            foreach (var pr in g.props)
            {
                if (!pr) continue;
                pr.Bar(!open);
                if (!near || (Player.I && Vector2.Distance(pr.basePos, Player.I.pos) < Vector2.Distance(near.basePos, Player.I.pos))) near = pr;
            }
            if (quiet || !near) return;
            Sfx.Play(open ? "bars_up" : "bars_down", 0.9f, 0.03f);
            PixelView.I.Shake(open ? 1 : 2, 0.18f);
            foreach (var pr in g.props) if (pr) Fx.Dust(pr.basePos, 5);
            if (open && !string.IsNullOrEmpty(g.say) && Story.Bump("said_" + g.id) == 0) Story.Run(Story.Narrate(g.say));
        }

        /// <summary>A door unlocked from one side is unlocked from the other.</summary>
        void Twins()
        {
            foreach (var pr in map.props)
                if (pr && (pr.Kind == "lockdoor" || pr.Kind == "bigdoor") && Story.Has("door_" + pr.data.id)) pr.Open();
        }

        void Update()
        {
            if (Game.Paused) return;
            var p = Player.I;
            scan -= Time.deltaTime;
            if (scan <= 0)
            {
                scan = 0.15f;
                Twins();
                // fires that have been lit stay lit, and a dark room with all its fires burning is dark no longer
                foreach (var pr in map.props)
                    if (pr && pr.Kind == "brazier" && pr.lit && !string.IsNullOrEmpty(pr.data.id) && !Story.Has("on_" + pr.data.id)) Story.Set("on_" + pr.data.id);
                if (Rooms.I)
                {
                    var rooms = Rooms.I;
                    foreach (var r in rooms.all)
                    {
                        if (!r.Is("dark") || Story.Has("lit_" + Game.I.CurrentMap + "_" + r.id)) continue;
                        int fires = 0, lit = 0;
                        foreach (var pr in map.props)
                            if (pr && pr.Kind == "brazier" && r.rect.Contains(pr.basePos)) { fires++; if (pr.lit) lit++; }
                        if (fires > 0 && lit == fires)
                        {
                            Story.Set("lit_" + Game.I.CurrentMap + "_" + r.id);
                            Sfx.Play("secret", 0.8f, 0);
                        }
                    }
                    // a room with nothing left alive in it is cleared, for good
                    var cur = rooms.current;
                    if (cur != null && !Rooms.Sliding && !Story.Has(ClearFlag(Game.I.CurrentMap, cur.id)) && rooms.Left(cur) == 0 && HadEnemies(cur))
                        Story.Set(ClearFlag(Game.I.CurrentMap, cur.id));
                }
            }
            foreach (var g in gates)
            {
                bool want = Holds(g);
                if (want != g.open) Put(g, want, false);
            }
            Shine(p);
        }

        bool HadEnemies(Room r)
        {
            foreach (var mk in map.data.markers)
                if (mk.kind == "enemy" && r.rect.Contains(Map.ToWorld(mk.x, mk.y))) return true;
            return false;
        }

        // ---------------------------------------------------------------------------- light off the shield
        static Sprite white;

        /// <summary>Standing in a pool of moonlight with the mirror shield raised, Azar throws the light
        /// where he faces. Held on a sun disc for a moment, it lights it.</summary>
        void Shine(Player p)
        {
            bool on = false;
            if (p && p.Guarding && pools.Count > 0)
                foreach (var r in pools) if (r.Contains(p.pos)) on = true;
            if (!on)
            {
                if (beam) beam.enabled = false;
                if (beamLight) beamLight.gameObject.SetActive(false);
                shine = 0; shining = null;
                return;
            }
            Vector2 dir = p.facing == Facing.Down ? Vector2.down : p.facing == Facing.Up ? Vector2.up : p.facing == Facing.Left ? Vector2.left : Vector2.right;
            Vector2 from = p.pos + dir * 0.5f;
            // how far the light goes before a wall takes it
            float reach = 0;
            for (; reach < 16f; reach += 0.25f)
                if (Solids.Blocks(new Rect(from + dir * reach - new Vector2(0.08f, 0.08f), new Vector2(0.16f, 0.16f)), from + dir * reach, p)) break;
            Prop hit = null;
            foreach (var pr in map.props)
            {
                if (!pr || pr.Kind != "disc") continue;
                var d = pr.basePos - from;
                float along = Vector2.Dot(d, dir), off = Mathf.Abs(d.x * dir.y - d.y * dir.x);
                if (along > 0 && along < reach + 1.2f && off < 0.75f) { hit = pr; reach = Mathf.Min(reach, along); }
            }
            if (!beam)
            {
                if (!white)
                {
                    var t = new Texture2D(1, 1) { filterMode = FilterMode.Point };
                    t.SetPixel(0, 0, Color.white); t.Apply();
                    white = Sprite.Create(t, new Rect(0, 0, 1, 1), new Vector2(0, 0.5f), 1f);
                }
                var go = new GameObject("Beam");
                go.transform.SetParent(transform, false);
                beam = go.AddComponent<SpriteRenderer>();
                beam.sprite = white;
                beam.sharedMaterial = Map.SpriteMat;
                beamLight = LightBlob.Create(transform, from, 2.6f, new Color(0.92f, 0.95f, 1f), 0.9f, false);
                beamLight.height = 0.9f;
            }
            beam.enabled = true;
            beamLight.gameObject.SetActive(true);
            float pulse = 0.82f + 0.18f * Mathf.Sin(Time.time * 22f);
            beam.color = new Color(1f, 0.98f, 0.82f, pulse);
            beam.transform.position = new Vector3(from.x, from.y + 0.9f, 0);
            beam.transform.rotation = Quaternion.Euler(0, 0, Mathf.Atan2(dir.y, dir.x) * Mathf.Rad2Deg);
            beam.transform.localScale = new Vector3(reach, 2f / 16f, 1);
            beam.sortingOrder = Map.Order(Mathf.Min(from.y, from.y + dir.y * reach)) + 3;
            var end = from + dir * reach;
            beamLight.transform.position = new Vector3(end.x, end.y, 0);
            if (Random.value < 0.3f) Fx.Sparks(end + new Vector2(0, 0.9f), new Color(1f, 0.97f, 0.8f), 1);
            if (hit && !Story.Has("on_" + hit.data.id))
            {
                if (shining != hit) { shining = hit; shine = 0; }
                shine += Time.deltaTime;
                if (shine > 0.55f)
                {
                    Story.Set("on_" + hit.data.id);
                    hit.SetSprite(hit.data.s + "_lit", hit.data.px, hit.data.py);
                    var glow = LightBlob.Create(hit.transform, hit.basePos + new Vector2(0, 1.5f), 4.2f, new Color(1f, 0.86f, 0.5f), 0.8f, true);
                    glow.height = 1.5f;
                    Sfx.Play("disc_lit", 1f, 0);
                    PixelView.I.Shake(1, 0.2f);
                    Fx.Sparks(hit.basePos + new Vector2(0, 1.5f), new Color(1f, 0.9f, 0.5f), 12);
                }
            }
            else { shining = null; shine = 0; }
        }
    }
}
