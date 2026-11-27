// The Sleeping Watch. The day watch fell asleep at its posts. Two of the night watch were out
// on their rounds when the city went down, and went down with it, and have not stopped: forty
// nights of the same beat, asleep, each with his lamp held out in front of him. The lamps went
// out the first night. It is what every watchman in Ashkel dreams of being found doing.
//
// Azar does not strike a sleeping man, and these two are owed forty nights' pay besides. A
// sleepwalker who walks into somebody out after dark does what the rule says: he arrests him,
// without waking, and the somebody comes to in the lock-up under the watch house. (There is a
// way out of the lock-up. The last prisoner dug it.) The rule does not say "somebody". It says
// "anything abroad after dark without a light", and a Snuffer has put its own light out.
//
// They walk towards any loud noise: a gong, a blade on bronze, a bell coming down. So they can
// be sent wherever a noise can be made, and whatever is making it had better have a lamp.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    /// <summary>Loud things, for whoever is listening: where, and how far it carries (tiles).</summary>
    public static class Noise
    {
        public static event System.Action<Vector2, float> Heard;
        public static void Make(Vector2 at, float carries) => Heard?.Invoke(at, carries);
    }

    public class SleepWatch : Enemy
    {
        public enum S { Round, Towards, Listen, Arrest }
        public S s;
        public Vector2[] beat;
        int leg;
        Vector2 heard, was;
        float pause, mutter, stuck, zed;
        Snuffer chase;                              // what made the noise, if it was one of those: he keeps after it
        /// <summary>Set while one of them is making an arrest: there is only ever one.</summary>
        public static bool Arresting;
        static float bailUntil;
        /// <summary>He has only just been run in (or has just let himself out): nobody runs him in again yet.</summary>
        public static bool OnBail => Time.time < bailUntil;
        public static void Bail(float seconds) => bailUntil = Time.time + seconds;

        public static SleepWatch Spawn(Vector2 at) => Make<SleepWatch>("captain", "sleepwalk", at, WorldLayer.Waking, 9, "watchman");

        protected override void Init()
        {
            speed = 1.25f; half = new Vector2(0.3f, 0.15f); touchDamage = 0; roams = true;
            was = pos;
            Noise.Heard += Hear;
        }

        protected override void OnDestroy()
        {
            Noise.Heard -= Hear;
            if (s == S.Arrest) Arresting = false;
            base.OnDestroy();
        }

        /// <summary>"beat:x0,y0;x1,y1;...": the corners of his round, in the map's own pixels.</summary>
        public void SetBeat(string text)
        {
            if (string.IsNullOrEmpty(text)) return;
            int i = text.IndexOf("beat:");
            if (i < 0) return;
            var parts = text.Substring(i + 5).Split(' ')[0].Split(';');
            var pts = new System.Collections.Generic.List<Vector2>();
            var inv = System.Globalization.CultureInfo.InvariantCulture;
            foreach (var part in parts)
            {
                var xy = part.Split(',');
                if (xy.Length == 2 && float.TryParse(xy[0], System.Globalization.NumberStyles.Float, inv, out float x) &&
                    float.TryParse(xy[1], System.Globalization.NumberStyles.Float, inv, out float y)) pts.Add(Map.ToWorld(x, y));
            }
            if (pts.Count > 1) beat = pts.ToArray();
        }

        public override bool Sleeps => false;                 // (he is asleep already)
        protected override bool WaitsOutStories => true;
        /// <summary>He is on his way to something he heard, or standing where he heard it.</summary>
        public bool Drawn => s == S.Towards || s == S.Listen;
        public Vector2 HeardAt => heard;

        /// <summary>Nobody hits a man who is asleep. It is the first rule of the watch, and very nearly the only one.</summary>
        protected override bool Untouchable(HitInfo h)
        {
            if (h.source && h.source.GetComponent<Player>() && Story.I) Story.I.StruckASleeper();
            return true;
        }

        void Hear(Vector2 at, float carries)
        {
            if (!this || s == S.Arrest || !Present) return;
            if (Vector2.Distance(at, pos) > carries) return;
            // (a noise right under his nose is one he is already standing at)
            if (s == S.Listen && Vector2.Distance(at, heard) < 1.5f) { stateClock = 0; return; }
            heard = at;
            chase = null;
            foreach (var e in All)
                if (e is Snuffer sn && sn.Present && Vector2.Distance(sn.pos, at) < 1.3f) { chase = sn; break; }
            if (s != S.Towards) Fx.Spawn(pos + new Vector2(0, 2.3f), Vector2.zero, 0, 0.8f, 0.5f, new Color(1f, 0.95f, 0.7f), new Color(1f, 0.8f, 0.3f, 0f), 0f, 2);
            s = S.Towards; stateClock = 0; stuck = 0;
        }

        protected override void Think(float dt, Player p)
        {
            // a sleepwalker says the odd thing, and sleeps as loudly on his feet as off them
            if ((mutter -= dt) <= 0 && CanSee(p, 5f)) { mutter = Random.Range(5f, 9f); Sfx.Play("snore", 0.35f, 0.15f); }
            if ((zed -= dt) <= 0) { zed = 1.1f; Zed.Spawn(pos + new Vector2(0.25f, 1.9f), WorldLayer.Waking); }
            float moved = (pos - was).magnitude;
            was = pos;
            switch (s)
            {
                case S.Round:
                {
                    if (pause > 0) { pause -= dt; anim.Play("sleep", facing); vel = Vector2.zero; break; }
                    bool round = beat != null && beat.Length > 0;
                    var to = (round ? beat[leg] : home) - pos;
                    if (to.magnitude < 0.14f) { if (round) leg = (leg + 1) % beat.Length; pause = round ? 1.4f : 4f; stuck = 0; break; }
                    Step(to, dt);
                    // something has been left in the road: he gives that corner up and makes for the next
                    stuck = moved < speed * dt * 0.25f ? stuck + dt : 0;
                    if (stuck > 1.6f) { if (round) leg = (leg + 1) % beat.Length; stuck = 0; pause = 0.8f; }
                    break;
                }
                case S.Towards:
                {
                    if (chase) heard = chase.pos;
                    var to = heard - pos;
                    // (as near as he can get: a gong hangs on a wall)
                    if (to.magnitude < 0.9f) { s = S.Listen; stateClock = 0; break; }
                    Step(to, dt, 1.5f);
                    stuck = moved < speed * dt * 0.25f ? stuck + dt : 0;
                    if (stuck > 1.0f || stateClock > 16f) { s = S.Listen; stateClock = 0; stuck = 0; }
                    break;
                }
                case S.Listen:
                    anim.Play("sleep", facing);
                    vel = Vector2.zero;
                    if (stateClock > 6f) { s = S.Round; stateClock = 0; }
                    break;
                case S.Arrest:
                    // (the scene lets him go when it is over; if it was cut short, he lets himself go)
                    vel = Vector2.zero;
                    if (stateClock > 1.5f && !(Story.I && Story.I.Running)) Done();
                    break;
            }
            if (s == S.Arrest || Arresting || !Present || (Story.I && Story.I.Running) || Game.Busy) return;
            var reach = pos + Dir() * 0.45f;
            // somebody out after dark, within arm's reach of the watch
            if (!OnBail && p.state == Player.State.Free && !p.Hidden && !p.Rooted && p.health.invulnerable <= 0 &&
                Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos) && Vector2.Distance(p.pos, reach) < 0.62f)
            {
                Take(p.pos);
                Story.Run(ArrestScene(p));
                return;
            }
            // ...or something: the rule says "abroad after dark without a light", and does not say what
            foreach (var e in All)
            {
                if (!(e is Snuffer sn) || !sn.Present || sn.Holding || sn.health.Dead) continue;
                if (Vector2.Distance(sn.pos, reach) > 1.0f) continue;
                Take(sn.pos);
                Story.Run(NickScene(sn));
                return;
            }
        }

        void Take(Vector2 whom)
        {
            s = S.Arrest; stateClock = 0; Arresting = true;
            facing = FaceOf(whom - pos); anim.SetFacing(facing);
            anim.Play("arrest", facing, true);
            Sfx.Play("deny", 0.6f);
        }

        void Done()
        {
            Arresting = false;
            if (this) { s = S.Round; stateClock = 0; pause = 2f; }
        }

        Vector2 Dir() => facing == Facing.Down ? Vector2.down : facing == Facing.Up ? Vector2.up : facing == Facing.Left ? Vector2.left : Vector2.right;

        void Step(Vector2 to, float dt, float pace = 1f)
        {
            facing = FaceOf(to);
            anim.Play("sleepwalk", facing);
            anim.SetFacing(facing);
            Move(to.normalized * speed * pace, dt);
        }

        IEnumerator ArrestScene(Player p)
        {
            int n = Story.Bump("arrested");
            p.SetState(Player.State.Talk, "idle");
            p.Face(FaceOf(pos - p.pos));
            yield return DialogueBox.Say("Watchman", n == 0
                ? "...halt...| ...out after dark... no lamp lit...| ...name and street...| ...you're nicked..."
                : n == 1 ? "...halt...| ...you again...| ...nicked..." : "...nicked...", "man");
            if (n == 0)
                yield return Story.Narrate("You have been arrested, by a man who is asleep, for being out after dark.^It is your own rule. You wrote it on the watch house door.");
            Done();
            Bail(30f);
            Game.I.Go("ashkel_in", "wt_cell_in");
            yield return null;
            while (Game.Busy) yield return null;
            if (n == 0 && Player.I)
            {
                Player.I.SetState(Player.State.Talk, "idle");
                yield return Story.Narrate("The lock-up, from the inside.^You have put a good many men in here. It was roomier then.| "
                                           + "The keys are on their peg, where the prisoner can see them and not reach them. That was your idea as well.| "
                                           + "The last man they put in here was a well-digger. Nobody asked him what he did with his evenings.");
            }
        }

        IEnumerator NickScene(Snuffer sn)
        {
            int n = Story.Bump("nicked");
            var p = Player.I;
            yield return DialogueBox.Say("Watchman", "...halt...| ...abroad after dark... no light on it...| ...it's got legs, Hadad...| ...nicked...", "man");
            if (sn) sn.Nicked();
            if (n == 0)
                yield return Story.Narrate("The Sleeping Watch has arrested a Snuffer.^It did not come quietly. It came.| "
                                           + "Whatever it had on it has been returned to its owners. That is in the rules too.");
            Done();
        }
    }
}
