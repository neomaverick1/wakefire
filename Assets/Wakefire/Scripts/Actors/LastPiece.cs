// The Board, and the Last Piece. The floor of the barrow's middle hall is the game of twenty
// squares, and on its middle rosette stands the one piece the generals never finished with: a
// champion of clay as tall as a door, who has not moved in three hundred and ninety-one years
// because it has not been anybody's move. Azar walking onto the board is a move.
//
// It does not walk. It is moved, the way a piece is: slid down a row or a file to the end of it
// (Ushur's kind of move), or lifted and set down hard on the square its man is standing on
// (Baltu's). The squares light before it goes. A blade turns on it from the front.
//
// Rule the fourth: a piece that stands on a rosette cannot be taken. If Azar is on a rosette
// when the move would take him, the move is illegal: the Piece stops short and rocks on its base
// while two old men argue about it somewhere overhead, and for that long it is only clay. The
// rosette goes dark afterwards for a while (the rule has been looked up). Past half its life the
// generals stop taking turns.
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Board : MonoBehaviour
    {
        public static Board I;
        public const int Cols = 8, Rows = 3;
        static readonly Vector2Int[] Rosettes = { new Vector2Int(0, 0), new Vector2Int(0, 2), new Vector2Int(3, 1), new Vector2Int(6, 0), new Vector2Int(6, 2) };

        Vector2 origin;                   // the north-west corner, in the world
        public float cell;                // a square's side, in tiles
        readonly SpriteRenderer[,] wash = new SpriteRenderer[Cols, Rows];
        readonly float[,] lit = new float[Cols, Rows];
        readonly Color[,] tint = new Color[Cols, Rows];
        readonly float[,] spent = new float[Cols, Rows];
        readonly LightBlob[] glow = new LightBlob[Rosettes.Length];
        readonly List<LightBlob> tells = new List<LightBlob>();
        // every pixel the game draws is there or not there: a square is marked with a frame and a scatter of
        // dots, never a see-through wash
        Sprite frame, frameDots, dimmed;

        public static bool Valid(int c, int r) => c >= 0 && c < Cols && r >= 0 && r < Rows && (r == 1 || (c != 4 && c != 5));

        public static bool Rosette(int c, int r)
        {
            foreach (var q in Rosettes) if (q.x == c && q.y == r) return true;
            return false;
        }

        public static void Setup(Map m)
        {
            I = null;
            var mk = m.Marker("board");
            if (mk == null) return;
            I = m.gameObject.AddComponent<Board>();
            I.origin = Map.ToWorld(mk.x, mk.y);
            I.cell = mk.w / 16f;
            I.Build();
        }

        void OnDestroy() { if (I == this) I = null; }

        void Build()
        {
            int n = Mathf.Max(8, Mathf.RoundToInt(cell * 16f) - 4);
            frame = Pattern(n, (x, y) => x < 2 || y < 2 || x >= n - 2 || y >= n - 2);
            frameDots = Pattern(n, (x, y) => x < 2 || y < 2 || x >= n - 2 || y >= n - 2 || (x % 3 == 1 && y % 3 == 1));
            dimmed = Pattern(n, (x, y) => (x + y) % 2 == 0);
            for (int c = 0; c < Cols; c++)
                for (int r = 0; r < Rows; r++)
                {
                    if (!Valid(c, r)) continue;
                    var go = new GameObject("Square");
                    go.transform.SetParent(transform, false);
                    var sr = go.AddComponent<SpriteRenderer>();
                    sr.sprite = frame;
                    sr.sharedMaterial = Map.SpriteMat;
                    sr.sortingOrder = -31996;
                    sr.enabled = false;
                    var at = Center(c, r);
                    go.transform.position = new Vector3(at.x, at.y, 0);
                    wash[c, r] = sr;
                }
            for (int i = 0; i < Rosettes.Length; i++)
            {
                glow[i] = LightBlob.Create(transform, Center(Rosettes[i].x, Rosettes[i].y), 1.9f, new Color(1f, 0.82f, 0.42f), 0.5f, false);
                glow[i].height = 0.3f;
            }
        }

        static Sprite Pattern(int n, System.Func<int, int, bool> on)
        {
            var t = new Texture2D(n, n, TextureFormat.RGBA32, false) { filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp };
            var px = new Color32[n * n];
            for (int y = 0; y < n; y++)
                for (int x = 0; x < n; x++)
                    px[y * n + x] = on(x, y) ? new Color32(255, 255, 255, 255) : new Color32(0, 0, 0, 0);
            t.SetPixels32(px); t.Apply();
            return Sprite.Create(t, new Rect(0, 0, n, n), new Vector2(0.5f, 0.5f), 16f, 0, SpriteMeshType.FullRect);
        }

        /// <summary>The light a marked square throws on the floor round it (they are handed out as squares need them).</summary>
        LightBlob Tell(int i, Vector2 at, Color col, float strength)
        {
            while (tells.Count <= i)
            {
                var nl = LightBlob.Create(transform, at, 1.7f, col, 0f, false);
                nl.height = 0.2f;
                tells.Add(nl);
            }
            var l = tells[i];
            if (!l.gameObject.activeSelf) l.gameObject.SetActive(true);
            l.transform.position = new Vector3(at.x, at.y, 0);
            l.color = col; l.intensity = strength;
            return l;
        }

        public Vector2 Center(int c, int r) => origin + new Vector2((c + 0.5f) * cell, -(r + 0.5f) * cell);

        /// <summary>Which square a place is on (false off the board).</summary>
        public bool At(Vector2 p, out int c, out int r)
        {
            c = Mathf.FloorToInt((p.x - origin.x) / cell);
            r = Mathf.FloorToInt((origin.y - p.y) / cell);
            return Valid(c, r);
        }

        /// <summary>The square nearest a place, on the board or off it.</summary>
        public Vector2Int Nearest(Vector2 p)
        {
            var best = new Vector2Int(3, 1);
            float bd = 999f;
            for (int c = 0; c < Cols; c++)
                for (int r = 0; r < Rows; r++)
                {
                    if (!Valid(c, r)) continue;
                    float d = Vector2.Distance(Center(c, r), p);
                    if (d < bd) { bd = d; best = new Vector2Int(c, r); }
                }
            return best;
        }

        /// <summary>Standing on a rosette that still counts.</summary>
        public bool Safe(Vector2 p) => At(p, out int c, out int r) && Rosette(c, r) && spent[c, r] <= 0;

        public bool Spent(int c, int r) => spent[c, r] > 0;

        public void Spend(int c, int r, float seconds) { if (Valid(c, r)) spent[c, r] = seconds; }

        /// <summary>Light a square for a while (where the Piece is about to go).</summary>
        public void Light(int c, int r, Color col, float seconds)
        {
            if (!Valid(c, r)) return;
            lit[c, r] = seconds; tint[c, r] = col;
        }

        public void Unlight()
        {
            for (int c = 0; c < Cols; c++) for (int r = 0; r < Rows; r++) lit[c, r] = 0;
        }

        void Update()
        {
            if (Game.Paused) return;
            float dt = Time.deltaTime;
            bool beat = Mathf.Repeat(Time.time * 7f, 1f) < 0.5f;
            int used = 0;
            for (int c = 0; c < Cols; c++)
                for (int r = 0; r < Rows; r++)
                {
                    var sr = wash[c, r];
                    if (!sr) continue;
                    if (spent[c, r] > 0) spent[c, r] -= dt;
                    if (lit[c, r] > 0)
                    {
                        // where the Piece is about to go: a bright frame that beats, and its own light on the floor
                        lit[c, r] -= dt;
                        var col = tint[c, r]; col.a = 1;
                        sr.sprite = beat ? frameDots : frame;
                        sr.color = col;
                        sr.enabled = true;
                        Tell(used++, Center(c, r), col, beat ? 1.0f : 0.7f);
                    }
                    else if (spent[c, r] > 0)
                    {
                        // a rosette that has been looked up: every other pixel of it gone dark, until the argument is forgotten
                        sr.sprite = dimmed;
                        sr.color = new Color(0.03f, 0.03f, 0.08f, 1f);
                        sr.enabled = spent[c, r] > 1.2f || Mathf.Repeat(Time.time * 6f, 1f) < 0.5f;      // it flickers back
                    }
                    else sr.enabled = false;
                }
            for (int i = used; i < tells.Count; i++)
                if (tells[i].gameObject.activeSelf) tells[i].gameObject.SetActive(false);
            for (int i = 0; i < Rosettes.Length; i++)
            {
                bool on = spent[Rosettes[i].x, Rosettes[i].y] <= 0 && LastPiece.Fighting;
                glow[i].intensity = Mathf.MoveTowards(glow[i].intensity, on ? 0.55f + 0.12f * Mathf.Sin(Time.time * 2.4f + i) : 0.0f, dt * 2f);
            }
        }
    }

    public class LastPiece : Enemy
    {
        enum S { Wait, Rest, Call, Slide, Lift, Carry, Drop, Stall }
        S s;
        Vector2Int sq, target;            // the square it stands on, and the one it is going to
        readonly List<Vector2Int> lane = new List<Vector2Int>();
        Vector2 from, to;
        bool blueMove, twice, illegal;
        int moves;
        float rock;

        public static LastPiece Current;
        /// <summary>The game is on (the rosettes glow while it is).</summary>
        public static bool Fighting => Current && Current.s != S.Wait && !Current.health.Dead;

        public static LastPiece Spawn(Vector2 at) => Make<LastPiece>("sentinel", "idle", at, WorldLayer.Both, 16, "last_piece");

        protected override void Init()
        {
            speed = 0; half = new Vector2(0.45f, 0.2f); touchDamage = 0;
            s = S.Wait;
            Current = this;
            roams = true;                                  // it is carried over walls it could not walk through
        }

        public override Rect HitBox => new Rect(pos.x - 0.6f, pos.y - 0.2f, 1.2f, 2.3f);
        protected override float KnockScale => 0f;
        protected override string HurtSound => "clay_hit";
        protected override Color BurstColor => new Color(0.72f, 0.44f, 0.30f);
        public override bool Sleeps => false;              // it has never been awake enough to fall asleep
        bool Hurt => health.hp <= health.max / 2;
        public bool Stalled => s == S.Stall;
        public bool Resting => s == S.Rest;
        public bool Waiting => s == S.Wait;
        /// <summary>The rule has been explained to somebody who was not listening: start the rocking again.</summary>
        public void StallAgain() { if (s == S.Stall) { stateClock = 0; rock = 0; } }

        static Vector2 Dir(Facing f) => f == Facing.Down ? Vector2.down : f == Facing.Up ? Vector2.up : f == Facing.Left ? Vector2.left : Vector2.right;

        /// <summary>Clay with a shield in front of it; clay all round while it is rocking on an illegal move.</summary>
        protected override bool Accepts(HitInfo h)
        {
            if (s == S.Wait) return false;
            if (s == S.Lift || s == S.Carry) return false;                 // it is in somebody's hand
            if (s == S.Stall || h.kind == HitKind.Reflected || h.kind == HitKind.Fire) return true;
            var d = ((Vector2)h.from - pos).normalized;
            return Vector2.Dot(d, Dir(facing)) < 0.15f;
        }

        /// <summary>Somebody has made a move: the game is on.</summary>
        public void Begin()
        {
            if (s != S.Wait) return;
            s = S.Rest; stateClock = -0.4f;
            var b = Board.I;
            if (b) sq = b.Nearest(pos);
        }

        protected override void Think(float dt, Player p)
        {
            var b = Board.I;
            if (!b) return;
            hover = 0;
            switch (s)
            {
                case S.Wait:
                    anim.Play("idle", facing);
                    break;
                case S.Rest:
                    anim.Play("idle", facing);
                    if (stateClock > (twice ? 0.12f : Hurt ? 0.75f : 1.05f)) Call(p, b);
                    break;
                case S.Call:
                {
                    float tell = twice ? 0.5f : Hurt ? 0.62f : 0.8f;
                    if (blueMove && stateClock < tell * 0.72f) Aim(p, b);          // a lifted piece follows its man until the hand is sure
                    if (stateClock > tell)
                    {
                        b.Unlight();
                        illegal = b.Safe(p.pos) && (blueMove ? Board.I.At(p.pos, out int pc, out int pr) && pc == target.x && pr == target.y : InLane(p, b));
                        if (blueMove) { s = S.Lift; stateClock = 0; from = pos; Sfx.Play("piece_lift", 0.9f, 0.02f); }
                        else { s = S.Slide; stateClock = 0; from = pos; Sfx.Play("piece_slide", 1f, 0.02f); StopShort(p, b); }
                    }
                    break;
                }
                case S.Slide:
                {
                    // down the row or the file to the end of it, and whoever is standing in it
                    float dist = Vector2.Distance(from, to);
                    float time = Mathf.Max(0.12f, dist / 15f);
                    float k = Mathf.Clamp01(stateClock / time);
                    var was = pos;
                    pos = Vector2.Lerp(from, to, k * k * (3 - 2 * k));
                    if (Random.value < 0.6f) Fx.Dust(pos, 1);
                    if (Vector2.Distance(pos, p.pos) < 0.95f && Mathf.Abs(pos.y - p.pos.y) < 0.8f && !illegal)
                        p.Hurt(new HitInfo { damage = 2, from = was, knockback = 9f, kind = HitKind.Crush, source = gameObject });
                    if (k >= 1f) Arrive(b, 1);
                    break;
                }
                case S.Lift:
                    hover = Mathf.SmoothStep(0, 2.4f, stateClock / 0.22f);
                    if (stateClock > 0.22f) { s = S.Carry; stateClock = 0; to = b.Center(target.x, target.y) + new Vector2(0, -0.35f); if (illegal) to = StandOff(p, b); }
                    break;
                case S.Carry:
                {
                    hover = 2.4f;
                    float time = Mathf.Clamp(Vector2.Distance(from, to) / 16f, 0.16f, 0.5f);
                    float k = Mathf.Clamp01(stateClock / time);
                    pos = Vector2.Lerp(from, to, k);
                    if (k >= 1f) { s = S.Drop; stateClock = 0; }
                    break;
                }
                case S.Drop:
                    hover = Mathf.Lerp(2.4f, 0f, Mathf.Clamp01(stateClock / 0.1f) * Mathf.Clamp01(stateClock / 0.1f));
                    if (stateClock > 0.1f)
                    {
                        hover = 0;
                        // set down hard: the square it lands on, and a little over the edges
                        float reach = b.cell * 0.5f + 0.35f;
                        var d = p.pos - (pos + new Vector2(0, 0.35f));
                        if (!illegal && Mathf.Abs(d.x) < reach && Mathf.Abs(d.y) < reach && Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos))
                            p.Hurt(new HitInfo { damage = 2, from = pos, knockback = 9f, kind = HitKind.Crush, source = gameObject });
                        PixelView.I.Shake(illegal ? 1 : 3, 0.22f);
                        Sfx.Play("piece_down", 1f, 0.02f);
                        for (int i = 0; i < 14; i++)
                        {
                            float a = i / 14f * Mathf.PI * 2f;
                            Fx.Dust(pos + new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.6f) * 0.9f, 1);
                        }
                        Arrive(b, 0);
                    }
                    break;
                case S.Stall:
                    // rocking on its base while the rule is looked up
                    rock += dt;
                    anim.sr.transform.localRotation = Quaternion.Euler(0, 0, Mathf.Sin(rock * 9f) * 5.5f * Mathf.Clamp01(1.4f - stateClock * 0.5f));
                    if (stateClock > (Hurt ? 2.1f : 2.5f))
                    {
                        anim.sr.transform.localRotation = Quaternion.identity;
                        s = S.Rest; stateClock = 0;
                    }
                    break;
            }
        }

        /// <summary>Whose move it is, and where it goes.</summary>
        void Call(Player p, Board b)
        {
            s = S.Call; stateClock = 0;
            sq = b.Nearest(pos + new Vector2(0, 0.35f));
            var him = b.Nearest(p.pos);
            // turn and turn about (Ushur's slide, then Baltu's drop), until they stop taking turns
            blueMove = twice ? !blueMove : moves % 2 == 1;
            moves++;
            lane.Clear();
            if (blueMove) { Aim(p, b); Sfx.Play("piece_call_b", 0.9f, 0); }
            else
            {
                // along its own row or file towards him, to the end of the board
                Vector2Int step;
                if (him.y == sq.y && him.x != sq.x) step = new Vector2Int(him.x > sq.x ? 1 : -1, 0);
                else if (him.x == sq.x && him.y != sq.y) step = new Vector2Int(0, him.y > sq.y ? 1 : -1);
                else step = Mathf.Abs(him.x - sq.x) >= Mathf.Abs(him.y - sq.y) ? new Vector2Int(him.x >= sq.x ? 1 : -1, 0) : new Vector2Int(0, him.y > sq.y ? 1 : -1);
                var q = sq + step;
                while (Board.Valid(q.x, q.y)) { lane.Add(q); q += step; }
                if (lane.Count == 0) { blueMove = true; Aim(p, b); Sfx.Play("piece_call_b", 0.9f, 0); return; }
                facing = step.x > 0 ? Facing.Right : step.x < 0 ? Facing.Left : step.y > 0 ? Facing.Down : Facing.Up;
                anim.SetFacing(facing);
                target = lane[lane.Count - 1];
                to = b.Center(target.x, target.y) + new Vector2(0, -0.35f);
                foreach (var l in lane) b.Light(l.x, l.y, new Color(1f, 0.25f, 0.18f), 2f);
                Sfx.Play("piece_call_a", 0.9f, 0);
            }
        }

        /// <summary>The square the lifted piece is coming down on: wherever he is this moment.</summary>
        void Aim(Player p, Board b)
        {
            var t = b.Nearest(p.pos);
            if (t == target && lane.Count > 0) return;
            b.Unlight();
            target = t;
            lane.Clear(); lane.Add(t);
            b.Light(t.x, t.y, new Color(0.3f, 0.5f, 1f), 2f);
            var d = b.Center(t.x, t.y) - pos;
            if (d.sqrMagnitude > 0.2f) { facing = FaceOf(d); anim.SetFacing(facing); }
        }

        bool InLane(Player p, Board b)
        {
            if (!b.At(p.pos, out int c, out int r)) return false;
            foreach (var l in lane) if (l.x == c && l.y == r) return true;
            return false;
        }

        /// <summary>An illegal slide stops on the square before the rosette.</summary>
        void StopShort(Player p, Board b)
        {
            if (!illegal || !b.At(p.pos, out int c, out int r)) return;
            Vector2Int stop = sq;
            foreach (var l in lane)
            {
                if (l.x == c && l.y == r) break;
                stop = l;
            }
            target = stop;
            to = b.Center(stop.x, stop.y) + new Vector2(0, -0.35f);
        }

        /// <summary>An illegal drop comes down on the next square instead (the nearest one that is not his).</summary>
        Vector2 StandOff(Player p, Board b)
        {
            var best = sq; float bd = 999f;
            foreach (var step in new[] { new Vector2Int(1, 0), new Vector2Int(-1, 0), new Vector2Int(0, 1), new Vector2Int(0, -1) })
            {
                var q = target + step;
                if (!Board.Valid(q.x, q.y)) continue;
                float d = Vector2.Distance(b.Center(q.x, q.y), from);
                if (d < bd) { bd = d; best = q; }
            }
            var him = target;
            target = best;
            var c = b.Center(best.x, best.y) + new Vector2(0, -0.35f);
            var look = b.Center(him.x, him.y) - c;
            facing = FaceOf(look); anim.SetFacing(facing);
            return c;
        }

        void Arrive(Board b, int kind)
        {
            sq = target;
            pos = b.Center(sq.x, sq.y) + new Vector2(0, -0.35f);
            if (illegal)
            {
                // rule the fourth
                illegal = false; twice = false;
                if (b.At(Player.I.pos, out int c, out int r)) b.Spend(c, r, Hurt ? 11f : 9f);
                s = S.Stall; stateClock = 0; rock = 0;
                Sfx.Play("piece_illegal", 1f, 0);
                PixelView.I.Shake(1, 0.2f);
                if (Story.I) Story.I.IllegalMove();
                return;
            }
            if (kind == 1) { PixelView.I.Shake(2, 0.18f); Sfx.Play("piece_down", 0.8f, 0.03f); }
            // past half its life they stop taking turns: one move straight after the other
            if (Hurt && !twice) { twice = true; s = S.Rest; stateClock = 0; return; }
            twice = false;
            s = S.Rest; stateClock = 0;
        }

        protected override void OnHurt(HitInfo h)
        {
            if (s == S.Stall) rock += 0.6f;
        }

        void OnDisable() { if (Current == this) Current = null; if (Board.I) Board.I.Unlight(); }

        protected override void Die()
        {
            anim.sr.transform.localRotation = Quaternion.identity;
            PixelView.I.Shake(3, 0.6f);
            Sfx.Play("statue_break", 1f, 0);
            for (int i = 0; i < 10; i++) Pickup.Drop(i % 3 == 0 ? Pickup.Kind.Gold : Pickup.Kind.Shekel, pos + Random.insideUnitCircle * 1.0f);
            Pickup.Drop(Pickup.Kind.Flame, pos + new Vector2(0, 0.4f));
            Pickup.Drop(Pickup.Kind.Flame, pos + new Vector2(0.5f, 0));
            if (Board.I) Board.I.Unlight();
            if (Story.I) Story.I.PieceDown();
            base.Die();
        }
    }
}
