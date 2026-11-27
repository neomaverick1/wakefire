// The rooms of a dungeon floor. A floor is one map; its rooms are rectangles on it (the art tools
// mark them, Art/pixel/dkit.py). Only the room Azar is in is shown: the picture is held inside its
// walls, everything outside them is dark, and when he walks through a doorway he is carried on
// through it while the picture slides across to the next room, the way the old games did it.
// What lives in a room is put there when he enters it and taken away when he leaves; what he
// has killed stays down until he leaves the floor.
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Room
    {
        public string id, name, opts;
        public Rect rect;                         // in tiles, world space
        public bool Is(string o) => !string.IsNullOrEmpty(opts) && (" " + opts + " ").Contains(" " + o + " ");
        /// <summary>The floor inside the walls.</summary>
        public Rect Floor => new Rect(rect.xMin + 1.25f, rect.yMin + 1.2f, rect.width - 2.5f, rect.height - 4.4f);
    }

    public class Rooms : MonoBehaviour
    {
        public static Rooms I;
        public static bool Sliding { get; private set; }
        /// <summary>Raised when Azar has arrived in a room (the first one too).</summary>
        public static event System.Action<Room> Entered;

        public readonly List<Room> all = new List<Room>();
        public Room current;
        Map map;
        readonly HashSet<string> fallen = new HashSet<string>();
        readonly Transform[] dark = new Transform[4];
        Rect shown;
        static readonly Color Moonlit = new Color(0.80f, 0.82f, 0.97f), Unlit = new Color(0.085f, 0.08f, 0.14f), Dim = new Color(0.36f, 0.33f, 0.46f),
                              Lamplit = new Color(0.70f, 0.60f, 0.52f),          // a room of a house with its lamps burning: warm, and not as bright as the moon makes the street
                              Bright = new Color(0.98f, 0.84f, 0.62f),           // a room with every lamp in it lit: the lamp seller's
                              Ghostlit = new Color(0.40f, 0.52f, 0.54f);         // a room of the dead, by the lamps the dead keep: cold, and clear enough to see the dust by

        public static string VisitedFlag(string mapName, string room) => "room_" + mapName + "_" + room;

        /// <summary>Called when a map has loaded and Azar stands at `at`. Maps without rooms get none of this.</summary>
        public static void Setup(Map m, Vector2 at)
        {
            LetGo();
            I = null;
            var marks = new List<MarkerJson>();
            foreach (var mk in m.data.markers) if (mk.kind == "room") marks.Add(mk);
            if (marks.Count == 0) { if (PixelView.I) PixelView.I.ambient = Moonlit; return; }
            var r = m.gameObject.AddComponent<Rooms>();
            I = r;
            r.map = m;
            foreach (var mk in marks)
            {
                var a = Map.ToWorld(mk.x, mk.y + mk.h);
                r.all.Add(new Room { id = mk.id, name = mk.text, opts = mk.who, rect = new Rect(a.x, a.y, mk.w / 16f, mk.h / 16f) });
            }
            r.MakeDark();
            r.current = r.At(at) ?? r.all[0];
            r.Arrive(r.current, true);
        }

        public Room At(Vector2 p)
        {
            foreach (var r in all) if (r.rect.Contains(p)) return r;
            return null;
        }

        public Room Find(string id)
        {
            foreach (var r in all) if (r.id == id) return r;
            return null;
        }

        /// <summary>The room a point of the current map is in, or null (on a map without rooms too).</summary>
        public static Room Of(Vector2 p) => I ? I.At(p) : null;

        void OnDestroy()
        {
            if (I == this) { I = null; LetGo(); }
        }

        /// <summary>A floor that is taken away in the middle of a slide (he fell, a journey was loaded)
        /// must not leave the game holding its breath: whatever the slide had stopped starts again.</summary>
        static void LetGo()
        {
            if (Sliding)
            {
                Game.Busy = false;
                if (Player.I) Player.I.march = Vector2.zero;
            }
            Sliding = false;
            Enemy.Frozen = false;
        }

        // ---------------------------------------------------------------------------- what lives here
        /// <summary>An enemy has died: it stays dead while Azar is on this floor.</summary>
        public static void Slain(Enemy e)
        {
            if (I && e && !string.IsNullOrEmpty(e.markerId)) I.fallen.Add(e.markerId);
        }

        public int Alive(Room r)
        {
            int n = 0;
            foreach (var e in Enemy.All) if (e && !e.health.Dead && r.rect.Contains(e.home)) n++;
            return n;
        }

        /// <summary>How many of a room's enemies have not been killed yet (whether or not they are out).</summary>
        public int Left(Room r)
        {
            int n = 0;
            foreach (var mk in map.data.markers)
            {
                if (mk.kind != "enemy" || !r.rect.Contains(Map.ToWorld(mk.x, mk.y))) continue;
                if (!string.IsNullOrEmpty(mk.id) && (Story.Has("dead_" + mk.id) || fallen.Contains(mk.id))) continue;
                n++;
            }
            return n;
        }

        void Fill(Room r)
        {
            foreach (var mk in map.data.markers)
            {
                if (mk.kind != "enemy" || !r.rect.Contains(Map.ToWorld(mk.x, mk.y))) continue;
                if (!string.IsNullOrEmpty(mk.id) && (Story.Has("dead_" + mk.id) || fallen.Contains(mk.id))) continue;
                Game.SpawnEnemy(mk);
            }
        }

        void Empty(Room r)
        {
            foreach (var e in Enemy.All.ToArray()) if (e && r.rect.Contains(e.home)) Destroy(e.gameObject);
        }

        static void ClearTheAir()
        {
            foreach (var pr in FindObjectsByType<Projectile>(FindObjectsSortMode.None)) Destroy(pr.gameObject);
            foreach (var th in Thrown.All.ToArray()) if (th) Destroy(th.gameObject);
        }

        void Arrive(Room r, bool first)
        {
            current = r;
            shown = r.rect;
            var v = PixelView.I;
            v.bounds = Held(r);
            if (first) { Fill(r); v.ambient = Light(r); }
            if (r.Is("secret") && !Story.Has(VisitedFlag(Game.I.CurrentMap, r.id))) Secrets.Found(r);
            Story.Set(VisitedFlag(Game.I.CurrentMap, r.id));
            PlaceDark();
            Entered?.Invoke(r);
        }

        /// <summary>What the picture may show of a room: all of it; of a room of a house ("snug"), a screen's width about its
        /// middle, so that a small room sits still in the dark round it instead of sliding about.</summary>
        static Rect Held(Room r) => r.Is("snug") ? new Rect(r.rect.center.x - 10f, r.rect.yMin, 20f, r.rect.height) : r.rect;

        /// <summary>He has come out somewhere else on this floor (a burrow, a ladder, a hole with a floor under it):
        /// there was no doorway, so there is no slide. The room he left is put away and this one laid out.</summary>
        public void Jump(Vector2 at)
        {
            var to = At(at);
            if (to == null || to == current) return;
            ClearTheAir();
            Empty(current);
            Fill(to);
            Arrive(to, false);
            PixelView.I.ambient = Light(to);
        }

        /// <summary>What light a room has before anything in it burns.</summary>
        Color Light(Room r) => Dark(r) ? Unlit : r != null && r.Is("dim") ? Dim : r != null && r.Is("ghost") ? Ghostlit : r != null && r.Is("bright") ? Bright : r != null && r.Is("lamp") ? Lamplit : Moonlit;

        /// <summary>A room with no light of its own until its fires are lit.</summary>
        public bool Dark(Room r) => r != null && r.Is("dark") && !Story.Has("lit_" + Game.I.CurrentMap + "_" + r.id);

        // ---------------------------------------------------------------------------- the dark outside the room
        static Sprite black;

        void MakeDark()
        {
            if (!black)
            {
                var t = new Texture2D(1, 1) { filterMode = FilterMode.Point };
                t.SetPixel(0, 0, new Color(0.02f, 0.015f, 0.04f, 1f));
                t.Apply();
                black = Sprite.Create(t, new Rect(0, 0, 1, 1), new Vector2(0, 0), 1f);
            }
            for (int i = 0; i < 4; i++)
            {
                var go = new GameObject("Dark" + i);
                go.transform.SetParent(transform, false);
                var sr = go.AddComponent<SpriteRenderer>();
                sr.sprite = black;
                sr.sharedMaterial = Map.SpriteMat;
                sr.sortingOrder = 32000;
                dark[i] = go.transform;
            }
        }

        void PlaceDark()
        {
            const float far = 400f;
            Rect s = shown;
            Set(dark[0], new Rect(s.xMin - far, s.yMin - far, far, s.height + 2 * far));           // west
            Set(dark[1], new Rect(s.xMax, s.yMin - far, far, s.height + 2 * far));                  // east
            Set(dark[2], new Rect(s.xMin, s.yMax, s.width, far));                                   // north
            Set(dark[3], new Rect(s.xMin, s.yMin - far, s.width, far));                             // south
        }

        static void Set(Transform t, Rect r)
        {
            t.position = new Vector3(r.xMin, r.yMin, 0);
            t.localScale = new Vector3(r.width, r.height, 1);
        }

        // ---------------------------------------------------------------------------- from room to room
        void Update()
        {
            if (Game.Paused) return;
            var v = PixelView.I;
            var p = Player.I;
            if (!p || !v) return;
            // a dark room is dark, and comes up as its fires are lit
            var want = Light(current);
            if (!(Story.I && Story.I.Running)) v.ambient = Color.Lerp(v.ambient, want, 1f - Mathf.Exp(-5f * Time.deltaTime));
            if (Sliding || Game.Busy) return;
            if (p.state == Player.State.Dead) return;
            if (current.rect.Contains(p.pos)) return;
            var to = At(p.pos);
            if (to == null || to == current) return;
            StartCoroutine(Slide(to));
        }

        void LateUpdate()
        {
            // what belongs to a room stays in it
            if (Sliding || current == null) return;
            var f = current.Floor;
            foreach (var e in Enemy.All)
            {
                if (!e || e.roams) continue;
                if (!f.Contains(e.pos)) e.pos = new Vector2(Mathf.Clamp(e.pos.x, f.xMin, f.xMax), Mathf.Clamp(e.pos.y, f.yMin, f.yMax));
            }
        }

        IEnumerator Slide(Room to)
        {
            Sliding = true;
            Game.Busy = true;
            var p = Player.I;
            var v = PixelView.I;
            var from = current;
            // which wall he went through
            Vector2 dir;
            Facing face;
            float walk;
            if (p.pos.x >= from.rect.xMax) { dir = Vector2.right; face = Facing.Right; walk = 1.9f; }
            else if (p.pos.x < from.rect.xMin) { dir = Vector2.left; face = Facing.Left; walk = 1.9f; }
            else if (p.pos.y >= from.rect.yMax) { dir = Vector2.up; face = Facing.Up; walk = 1.9f; }
            else { dir = Vector2.down; face = Facing.Down; walk = 3.9f; }
            const float time = 0.62f;
            Vector2 dest = p.pos + dir * walk;
            Vector2 f0 = v.focus, f1 = v.Clamp(dest, to.rect);
            Rect r0 = from.rect, r1 = to.rect;
            v.target = null;
            v.bounds = null;
            v.lookAhead = Vector2.zero;
            ClearTheAir();
            Enemy.Frozen = true;
            Fill(to);
            p.SetState(Player.State.Cutscene, "run");
            p.Face(face);
            p.march = dir * (walk / time);
            p.health.invulnerable = Mathf.Max(p.health.invulnerable, time + 0.1f);
            for (float t = 0; t < time; t += Time.deltaTime)
            {
                float k = Mathf.SmoothStep(0, 1, t / time);
                v.focus = Vector2.Lerp(f0, f1, k);
                shown = Union(r0, r1, k);
                PlaceDark();
                yield return null;
            }
            p.march = Vector2.zero;
            Empty(from);
            Enemy.Frozen = false;
            v.focus = f1;
            v.target = p.transform;
            p.SetState(Player.State.Free, "idle");
            Sliding = false;
            Game.Busy = false;
            Arrive(to, false);
        }

        /// <summary>What is lit during a slide: both rooms until the picture has left the old one.</summary>
        static Rect Union(Rect a, Rect b, float k)
        {
            if (k >= 0.98f) return b;
            return Rect.MinMaxRect(Mathf.Min(a.xMin, b.xMin), Mathf.Min(a.yMin, b.yMin), Mathf.Max(a.xMax, b.xMax), Mathf.Max(a.yMax, b.yMax));
        }
    }
}
