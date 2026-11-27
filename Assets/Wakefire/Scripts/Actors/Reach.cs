// The Underbed. There is one, and it is under every bed. Nobody in Ashkel has seen more of it
// than an arm: long, grey, with more elbows than an arm needs, feeling its way out across the
// floor from the dark under the frame. There has never been a face on the end of the other end
// of it. There has never been another end.
//
// A Reach is one of its arms. It feels for whoever is standing near the bed, closes on an ankle
// and takes him under. Under one bed is under all of them: he is put out again, a little the
// worse for it, from under whichever bed that arm's fancy runs to. (This is a way through walls.
// It is not a comfortable one.) It keeps what falls out of his purse on the way.
//
// It will not put its hand in the light. At the edge of the lamplight it stops, and waits, and
// drums its fingers; and a hand that is waiting can be cut. Cut enough, it goes back under and
// stays there.
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Reach : Enemy
    {
        public enum S { Under, Feel, Wait, Drag, Recoil, Dazzle, Limp, Brace }
        public S s;
        /// <summary>Where the hand is, from the root of the arm (tiles, on the floor).</summary>
        public Vector2 hand;
        /// <summary>0 open and feeling, 1 shut on something.</summary>
        public float curl;
        /// <summary>How far it has shown itself: 0 all under, 1 out (the model fades in from the dark with it).</summary>
        public float shown;
        /// <summary>Which way out from under the bed is (the bed's open side).</summary>
        public Vector2 mouth = Vector2.down;
        /// <summary>The spawn he is put out at when it has taken him under (same map); none: back out the way he went in.</summary>
        public string to;
        public const float Length = 4.4f;
        float rest, tap, pull;
        int cuts;
        Vector2 edge, limpAt;
        bool leashed;
        public static bool Told;
        static bool Peeked;
        /// <summary>The bed this arm belongs to, when it is one of the arms of the bed in the last room: the bed says when.</summary>
        public Underbed owner;

        /// <summary>(for the bed) Where the shoulder is now: the bed has moved.</summary>
        public void Root(Vector2 at) { pos = home = at; }
        /// <summary>(for the bed) Stay under, or be let out.</summary>
        public void Leash(bool on)
        {
            leashed = on;
            if (on && s != S.Under && s != S.Recoil && s != S.Drag) Back(0.3f);
        }
        /// <summary>(for the bed) Out on the floor with nothing left in it, the hand lying there.</summary>
        public void Flop(Vector2 at)
        {
            if (s == S.Drag && Player.I) Player.I.Release(this);
            s = S.Limp; stateClock = 0; limpAt = Vector2.ClampMagnitude(at, Length); leashed = false;
        }
        /// <summary>(for the bed) Out at a corner of it with the hand flat on the floor: the bed is getting up on it.</summary>
        public void Brace(Vector2 at)
        {
            if (s == S.Drag) return;                 // (the one that has hold of him keeps hold)
            s = S.Brace; stateClock = 0; limpAt = Vector2.ClampMagnitude(at, Length); leashed = false;
        }
        /// <summary>(for the bed) Back under, and not out again for a while.</summary>
        public void Away(float wait) { if (s != S.Under) Back(wait); else rest = Mathf.Max(rest, wait); }

        public static Reach Spawn(Vector2 at) => Make<Reach>("moth", "idle", at, WorldLayer.Waking, 3, "reach");

        protected override void Init()
        {
            speed = 2.5f; half = new Vector2(0.2f, 0.1f); touchDamage = 0; roams = false;
            if (shadow) shadow.enabled = false;
            mat.SetFloat("_Dissolve", 1.05f);
            rest = Random.Range(0.3f, 1.2f);
            hand = mouth * 0.05f;
        }

        /// <summary>"to:SPAWN" and "out:n|s|e|w" from the map's marker.</summary>
        public void Read(string text)
        {
            if (string.IsNullOrEmpty(text)) return;
            foreach (var part in text.Split(' '))
            {
                if (part.StartsWith("to:")) to = part.Substring(3);
                else if (part.StartsWith("out:") && part.Length > 4)
                    mouth = part[4] == 'n' ? Vector2.up : part[4] == 'e' ? Vector2.right : part[4] == 'w' ? Vector2.left : Vector2.down;
            }
            hand = mouth * 0.05f;
        }

        public override bool Sleeps => false;
        protected override bool WaitsOutStories => true;
        protected override float KnockScale => 0f;
        protected override string HurtSound => "reach_hurt";
        protected override Color BurstColor => new Color(0.42f, 0.42f, 0.46f);
        protected override int OrderBias => -30;                 // it is on the floor: whoever stands there is standing over it
        public Vector2 Hand => pos + hand;
        public bool Out => s != S.Under;
        public bool Waiting => s == S.Wait;
        public bool Has => s == S.Drag;
        /// <summary>Only the hand is ever within reach of anything, and only while it is out.</summary>
        public override Rect HitBox => s == S.Under ? new Rect(pos.x, pos.y - 900f, 0.01f, 0.01f) : new Rect(Hand.x - 0.5f, Hand.y - 0.3f, 1.0f, 0.9f);

        protected override bool Untouchable(HitInfo h) => s == S.Under || s == S.Drag || s == S.Recoil || s == S.Brace;

        /// <summary>Is that piece of floor lit? (His own flame, carried, is over his head and not on the floor: see the Stay-Ups.)</summary>
        static bool Lit(Vector2 q) => StayUp.Lit(q);

        protected override void Think(float dt, Player p)
        {
            var want = p.pos - pos;
            bool near = Present && !p.Hidden && Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos) && want.magnitude < Length + 0.6f &&
                        Vector2.Dot(want, mouth) > -0.4f && p.state != Player.State.Dead;
            switch (s)
            {
                case S.Under:
                    // a man with no blade is no trouble to it, and so no business of its: it puts its fingers out at the
                    // edge of the bed, drums them, and lets him by
                    if (!leashed && !owner && near && !p.hasSword && !Lit(pos + mouth * 0.6f))
                    {
                        curl = 0.1f;
                        hand = Vector2.MoveTowards(hand, mouth * 0.62f, 2.2f * dt);
                        shown = Mathf.MoveTowards(shown, 1f, dt * 6f);
                        if ((tap -= dt) <= 0) { tap = 0.62f; Sfx.Play("reach_tap", 0.3f, 0.12f); }
                        if (!Peeked && Story.I && !Story.I.Running && want.magnitude < 3.2f) { Peeked = true; Story.I.ReachPeeks(); }
                        break;
                    }
                    curl = 0.6f;
                    hand = Vector2.MoveTowards(hand, mouth * 0.05f, 9f * dt);
                    shown = Mathf.MoveTowards(shown, 0f, dt * 4f);
                    if (leashed) { rest = Mathf.Max(rest, 0.4f); break; }
                    if ((rest -= dt) <= 0 && near && !Lit(pos + mouth * 0.6f))
                    {
                        s = S.Feel; stateClock = 0;
                        Sfx.Play("reach_out", 0.7f, 0.1f);
                        if (!Told && Story.I && !Story.I.Running) { Told = true; Story.I.ReachSeen(); }
                    }
                    break;

                case S.Feel:
                {
                    shown = Mathf.MoveTowards(shown, 1f, dt * 5f);
                    curl = Mathf.MoveTowards(curl, 0.15f, dt * 3f);
                    if (!near) { Back(1.2f); break; }
                    // along the floor towards his feet, no further than it is long, and never into the light
                    var aim = Vector2.ClampMagnitude(want + new Vector2(0, 0.05f), Length);
                    var step = Vector2.MoveTowards(hand, aim, speed * dt);
                    if (Lit(pos + step))
                    {
                        if (Lit(Hand)) { Flinch(); break; }
                        s = S.Wait; stateClock = 0; tap = 0; edge = hand;
                        if (Story.I) Story.I.ReachWaits();
                        break;
                    }
                    hand = step;
                    if (Vector2.Distance(Hand, p.pos) < 0.34f && p.health.invulnerable <= 0 && p.Hold(this, "push"))
                    {
                        s = S.Drag; stateClock = 0; cuts = 0; pull = 0;
                        Sfx.Play("reach_grab", 0.9f, 0.05f);
                        PixelView.I.Shake(1, 0.14f);
                    }
                    break;
                }

                case S.Wait:
                    // at the edge of the light, with all night, and four hundred others behind it
                    curl = 0.1f;
                    if ((tap -= dt) <= 0) { tap = 0.62f; if (CanSee(p, 8f)) Sfx.Play("reach_tap", 0.45f, 0.12f); }
                    if (Lit(Hand)) { Flinch(); break; }
                    if (!near || stateClock > 7f) { Back(2.0f); break; }
                    // (if he steps out of the light it is after him again at once)
                    if (!Lit(pos + Vector2.MoveTowards(hand, Vector2.ClampMagnitude(want, Length), 0.5f)) && stateClock > 0.5f) { s = S.Feel; stateClock = 0; }
                    break;

                case S.Drag:
                    Dragging(dt, p);
                    break;

                case S.Recoil:
                    curl = 0.8f;
                    hand = Vector2.MoveTowards(hand, mouth * 0.05f, 11f * dt);
                    if (hand.magnitude < 0.2f) { s = S.Under; stateClock = 0; }
                    break;

                case S.Dazzle:
                    // light on it: it has never seen its own hand
                    curl = -0.5f;
                    if (stateClock > 1.1f) Back(2.4f);
                    break;

                case S.Brace:
                    // flat on the floor, taking the weight
                    shown = Mathf.MoveTowards(shown, 1f, dt * 8f);
                    hand = Vector2.MoveTowards(hand, limpAt, 9f * dt);
                    curl = -0.15f;
                    break;

                case S.Limp:
                    // nothing left in it: it lies where it fell, and the fingers twitch
                    shown = Mathf.MoveTowards(shown, 1f, dt * 6f);
                    hand = Vector2.MoveTowards(hand, limpAt, 7f * dt);
                    curl = 0.25f + 0.1f * Mathf.Sin(stateClock * 7f);
                    break;
            }
            mat.SetFloat("_Dissolve", shown > 0.02f ? 0f : 1.05f);
        }

        void Flinch()
        {
            s = S.Dazzle; stateClock = 0;
            Sfx.Play("reach_hurt", 0.5f, 0.2f);
        }

        void Back(float wait)
        {
            s = S.Recoil; stateClock = 0; rest = wait;
        }

        /// <summary>It has him by the ankle and is taking him under. Three cuts and it lets go.</summary>
        void Dragging(float dt, Player p)
        {
            curl = 1f;
            if (!p.HeldBy(this)) { Back(1.5f); return; }
            if (Controls.Down(Controls.Attack) && p.hasSword)
            {
                cuts++;
                Sfx.Play("cut", 0.9f, 0.08f);
                PixelView.I.Shake(1, 0.1f);
                Fx.Sparks(Hand + new Vector2(0, 0.3f), new Color(0.7f, 0.7f, 0.78f), 4);
                flash = 0.1f;
                if (cuts >= 3)
                {
                    p.Release(this);
                    p.health.invulnerable = Mathf.Max(p.health.invulnerable, 0.6f);
                    health.hp = Mathf.Max(1, health.hp - 1);
                    Sfx.Play("reach_hurt", 0.9f, 0.05f);
                    Back(2.5f);
                    if (owner) owner.Cut(this);
                    return;
                }
            }
            // a pull, a pause, a pull: it is in no hurry
            pull += dt;
            float heave = Mathf.Max(0f, Mathf.Sin(pull * 4.2f));
            var home = mouth * 0.3f;
            var before = p.pos;
            p.pos = Solids.Move(p.pos, (pos + home - p.pos).normalized * (0.5f + 2.4f * heave) * dt, p.half, p);
            hand = p.pos - pos + new Vector2(0, 0.02f);
            if (heave > 0.9f && (p.pos - before).sqrMagnitude > 0.00001f && Random.value < 0.25f) { Fx.Dust(p.pos, 1); Sfx.Play("reach_drag", 0.5f, 0.15f); }
            if (Vector2.Distance(p.pos, pos + home) < 0.55f || stateClock > 9f)
            {
                s = S.Recoil; stateClock = 0; rest = 5f;
                if (Story.I) Story.Run(Story.I.TakenUnder(this));
                else p.Release(this);
            }
        }

        protected override void OnHurt(HitInfo h)
        {
            Fx.Sparks(Hand + new Vector2(0, 0.3f), new Color(0.7f, 0.7f, 0.78f), 6);
            Back(2.2f);
            // (an arm of the bed itself does not die of it: the bed does, a cut at a time)
            if (owner) { health.hp = health.max; owner.Cut(this); }
        }

        /// <summary>It goes back under, and stays there. What it was holding stays out here.</summary>
        protected override void Die()
        {
            Sfx.Play("reach_gone", 0.9f, 0.05f);
            for (int i = 0; i < 8; i++)
                Fx.Spawn(Hand + Random.insideUnitCircle * 0.2f, Random.insideUnitCircle * 1.6f, 0.05f, Random.Range(0.4f, 1.4f), Random.Range(0.4f, 0.8f),
                    new Color(0.40f, 0.40f, 0.46f, 0.9f), new Color(0.10f, 0.10f, 0.14f, 0f), -0.4f, i % 2 + 1);
            Pickup.Chance(Hand, 0.7f, 0.12f);
            if (Story.I) Story.I.ReachGone(this);
            if (spawnId != null) Story.Set("dead_" + spawnId);
            Destroy(gameObject);
        }
    }

    /// <summary>The arm itself: a row of joints on the floor between the dark under the bed and wherever the hand
    /// has got to. Folded, it is all elbows; out, it is nearly straight, and still has too many.</summary>
    public class ReachProp : IPoser
    {
        const int N = 8;                         // lengths of arm between the shoulder nobody has seen and the wrist
        const float Y0 = 0.05f;
        float seg, len;
        readonly Transform[] joint = new Transform[N + 1];
        Transform palm;
        readonly Transform[] finger = new Transform[5];
        readonly Vector3[] fingerAt = new Vector3[5];
        readonly float[] fingerYaw = { 52f, 20f, 0f, -18f, -38f };
        Reach who;
        bool looked;
        float time;

        static Transform Bone(string name, Transform parent, Vector3 at)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = at;
            return go.transform;
        }

        public static ReachProp Make(ModelActor a)
        {
            var c = new ReachProp();
            var rig = a.rig;
            float scale = a.def.scale;
            c.len = Reach.Length / scale;                    // (the model's own units)
            c.seg = c.len / N;
            var bones = new List<Transform>();
            for (int i = 0; i <= N; i++) { c.joint[i] = Bone("r" + i, rig, new Vector3(0, Y0, i * c.seg)); bones.Add(c.joint[i]); }
            c.palm = Bone("palm", rig, new Vector3(0, Y0, c.len));
            bones.Add(c.palm);
            float pw = 0.17f, pl = 0.25f;
            for (int k = 0; k < 5; k++)
            {
                // the thumb leaves the side of the palm; the four fingers leave the far edge of it
                c.fingerAt[k] = k == 0 ? new Vector3(pw * 0.9f, Y0, c.len + pl * 0.35f) : new Vector3(Mathf.Lerp(pw * 0.8f, -pw * 0.8f, (k - 1) / 3f), Y0, c.len + pl);
                c.finger[k] = Bone("f" + k, rig, c.fingerAt[k]);
                c.finger[k].localRotation = Quaternion.Euler(0, c.fingerYaw[k], 0);
                bones.Add(c.finger[k]);
            }
            foreach (var t in bones) a.bones[t.name] = t;

            Color skin = new Color(0.70f, 0.71f, 0.78f), knuckle = new Color(0.44f, 0.44f, 0.52f), nail = new Color(0.12f, 0.11f, 0.15f), under = new Color(0.36f, 0.36f, 0.44f);
            var kit = new Kit(a, rig, bones.ToArray());
            // every point of the arm hangs between the two joints it lies between
            float seg = c.seg;
            kit.On(p =>
            {
                float f = Mathf.Clamp(p.z / seg, 0f, N - 0.001f);
                int i = Mathf.FloorToInt(f);
                float t = Mathf.SmoothStep(0f, 1f, f - i);
                return new BoneWeight { boneIndex0 = i, weight0 = 1f - t, boneIndex1 = i + 1, weight1 = t };
            });
            // grey above, darker along the underside, and darker again at every joint
            kit.Stain(p =>
            {
                float f = p.z / seg, d = Mathf.Abs(f - Mathf.Round(f));
                if (d < 0.11f && p.z > seg * 0.5f) return knuckle;
                return p.y < Y0 - 0.01f ? under : (Color?)null;
            });
            kit.Paint(skin);
            // the arm: thick where it comes out of the dark, thinner to the wrist, a knot at every elbow
            var path = new List<Vector3>();
            var rad = new List<float>();
            for (int i = 0; i <= N * 4; i++)
            {
                float f = i / 4f;                              // in lengths of arm
                float thick = Mathf.Lerp(0.115f, 0.080f, f / N);
                float knot = Mathf.Abs(f - Mathf.Round(f)) < 0.01f && i > 0 && i < N * 4 ? 0.040f : 0f;
                float belly = Mathf.Sin((f - Mathf.Floor(f)) * Mathf.PI) * 0.012f;
                path.Add(new Vector3(0, Y0, f * seg));
                rad.Add(thick + knot + belly);
            }
            kit.Tube(path.ToArray(), rad.ToArray(), 7);
            kit.Stain(null);
            // the hand: a long flat palm
            kit.On("palm").Paint(skin).Egg(new Vector3(0, Y0, c.len + pl * 0.5f), new Vector3(pw, 0.05f, pl * 0.62f), 10, 5);
            kit.Paint(knuckle);
            for (int k = 1; k < 5; k++) kit.Egg(c.fingerAt[k] + new Vector3(0, 0.016f, -0.016f), new Vector3(0.042f, 0.034f, 0.042f), 6, 4);
            // ...and five fingers, each with a joint too many, and a nail
            for (int k = 0; k < 5; k++)
            {
                float L = k == 0 ? 0.30f : k == 2 ? 0.54f : k == 4 ? 0.40f : 0.48f;
                var dir = Quaternion.Euler(0, c.fingerYaw[k], 0) * Vector3.forward;
                var b = c.fingerAt[k];
                kit.On("f" + k).Paint(skin);
                kit.Tube(new[] { b, b + dir * L * 0.34f, b + dir * L * 0.67f, b + dir * L }, new[] { 0.040f, 0.035f, 0.030f, 0.018f }, 5);
                kit.Paint(knuckle).Egg(b + dir * L * 0.34f, Vector3.one * 0.040f, 5, 3).Egg(b + dir * L * 0.67f, Vector3.one * 0.035f, 5, 3);
                kit.Paint(nail).Egg(b + dir * (L + 0.02f), new Vector3(0.022f, 0.014f, 0.042f), 5, 3);
            }
            kit.Wear("Reach");
            return c;
        }

        public void Pose(ModelActor a, string anim, float n, float dt)
        {
            if (!looked) { looked = true; who = a.sr ? a.sr.GetComponentInParent<Reach>() : null; }
            time += dt;
            // where the hand is: on the floor, in the model's own space. (The stage is tipped thirty degrees to the
            // lens, so a tile of floor away from it is two of the model's units deep.)
            Vector2 h = who ? who.hand : new Vector2(0.2f, -2.6f) * (0.6f + 0.4f * Mathf.Sin(time * 0.8f));
            float curl = who ? who.curl : 0.2f + 0.2f * Mathf.Sin(time * 2f);
            Vector3 target = a.rig.InverseTransformPoint(a.anchor.TransformPoint(new Vector3(h.x, 0, h.y * 2f)));
            target.y = Y0;
            Vector3 flat = new Vector3(target.x, 0, target.z);
            float D = Mathf.Min(flat.magnitude, len * 0.985f);
            Vector3 u = flat.sqrMagnitude > 0.0001f ? flat.normalized : Vector3.forward;
            Vector3 v = new Vector3(-u.z, 0, u.x);
            float cos = Mathf.Clamp01(D / len), sin = Mathf.Sqrt(1f - cos * cos);
            for (int i = 0; i <= N; i++)
            {
                // folded, the elbows stand out to both sides and up off the floor; out, they lie down into a line
                float w = Mathf.Sin(i / (float)N * Mathf.PI);                         // none at the shoulder, none at the wrist
                float side = (i % 2 == 0 ? -0.5f : 0.5f) * seg * sin * (0.35f + 0.65f * w);
                float up = (i % 2 == 1 ? 1f : 0.25f) * seg * sin * 0.55f * w;
                float writhe = Mathf.Sin(time * 2.1f + i * 1.7f) * 0.012f * w;
                joint[i].localPosition = u * (i * seg * cos) + v * (side + writhe) + Vector3.up * (Y0 + up);
            }
            for (int i = 0; i <= N; i++)
            {
                var ahead = i < N ? joint[i + 1].localPosition - joint[i].localPosition : joint[i].localPosition - joint[i - 1].localPosition;
                if (ahead.sqrMagnitude > 0.000001f) joint[i].localRotation = Quaternion.LookRotation(ahead.normalized, Vector3.up);
            }
            // the hand goes where the wrist goes, flat to the floor, pointing the way the arm is reaching
            var turn = Quaternion.LookRotation(u, Vector3.up);
            var wrist = new Vector3(0, Y0, len);
            palm.localPosition = joint[N].localPosition;
            palm.localRotation = turn;
            for (int k = 0; k < 5; k++)
            {
                // open, it feels: one finger lifts after another. Shut, they come round whatever is in it.
                float drum = curl < 0.3f ? Mathf.Max(0f, Mathf.Sin(time * 9f - k * 1.1f)) * 14f : 0f;
                float bend = curl >= 0 ? Mathf.Lerp(4f, 78f, curl) : Mathf.Lerp(4f, -34f, -curl) + Mathf.Sin(time * 31f + k) * 5f;
                finger[k].localPosition = palm.localPosition + turn * (fingerAt[k] - wrist);
                finger[k].localRotation = turn * Quaternion.Euler(0, fingerYaw[k], 0) * Quaternion.Euler(bend - drum, 0, 0);
            }
        }
    }
}
