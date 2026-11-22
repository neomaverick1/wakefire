// The animals. None of them has a stock rig, so each is a small skeleton built by code and
// walked by code: every foot is planted on the ground and stays where it lands while the body
// passes over it (the stride advances with the ground actually covered, so nothing can slide),
// legs fold at the knee and hock to reach, the body bobs on them, and head, jaw and tail are
// free to do what the creature is doing (staring, chewing, bleating, snarling).
// Everything is in the creature's own frame: x to its right, y up, z ahead, in metres.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    /// <summary>Something that poses a code-built skeleton each frame.</summary>
    public interface IPoser
    {
        void Pose(ModelActor m, string anim, float n, float dt);
    }

    public class Beast : IPoser
    {
        public class Shape
        {
            public float length = 0.78f, height = 0.60f, girth = 0.17f, chest = 0.19f, rump = 0.18f;
            public float legThick = 0.05f, stance = 0.12f;
            public float neckLen = 0.28f, neckRise = 55f, neckThick = 0.085f;
            public float headLen = 0.24f, headThick = 0.085f, headTilt = 22f;
            public float tailLen = 0.14f, tailRise = 50f, tailThick = 0.035f;
            public float earLen = 0.10f;
            public bool earsUp, beard;
            public (Vector3 at, float r)[] horn;          // one horn, in the head's frame (mirrored for the other)
            public float stride = 0.62f, stepHeight = 0.08f;
            public Color coat = Color.white, belly = Color.white, dark = new Color(0.12f, 0.10f, 0.10f), hornColour = new Color(0.55f, 0.50f, 0.42f);
            public Color eye = new Color(0.08f, 0.06f, 0.06f);
            public Color? back, muzzle, sock, collar;
            public float metal, eyeGlow;
            public Action<Kit, Beast> extra;
            /// <summary>A creature that isn't made of the usual rounded parts brings its whole skin: this
            /// replaces the stock body, neck, head, legs and tail (the skeleton and its gaits stay).</summary>
            public Action<Kit, Beast> skin;
        }

        public enum Gait { Walk, Trot, Bound }
        static readonly float[][] Offsets =
        {
            // offsets for: left hind, left fore, right hind, right fore
            new[] { 0.0f, 0.75f, 0.5f, 0.25f },          // walk: each foot in turn, hind before fore on the same side
            new[] { 0.0f, 0.5f, 0.5f, 0.0f },            // trot: diagonal pairs together
            new[] { 0.0f, 0.5f, 0.08f, 0.58f },          // bound: the hind pair, then the fore pair
        };
        static readonly float[] Duty = { 0.64f, 0.5f, 0.36f };

        /// <summary>What the creature is doing with its body, beyond walking.</summary>
        public struct Bearing
        {
            public float drop, lift, surge, pitch, roll, neckPitch, neckYaw, headPitch, headYaw, headRoll, jaw, chew, tailPitch, tailYaw;
            public float splay, reach, tuck, stiff;

            public void Towards(Bearing w, float k)
            {
                drop = Mathf.Lerp(drop, w.drop, k); lift = Mathf.Lerp(lift, w.lift, k); surge = Mathf.Lerp(surge, w.surge, k);
                pitch = Mathf.Lerp(pitch, w.pitch, k); roll = Mathf.Lerp(roll, w.roll, k);
                neckPitch = Mathf.Lerp(neckPitch, w.neckPitch, k); neckYaw = Mathf.Lerp(neckYaw, w.neckYaw, k);
                headPitch = Mathf.Lerp(headPitch, w.headPitch, k); headYaw = Mathf.Lerp(headYaw, w.headYaw, k); headRoll = Mathf.Lerp(headRoll, w.headRoll, k);
                jaw = Mathf.Lerp(jaw, w.jaw, k); chew = Mathf.Lerp(chew, w.chew, k);
                tailPitch = Mathf.Lerp(tailPitch, w.tailPitch, k); tailYaw = Mathf.Lerp(tailYaw, w.tailYaw, k);
                splay = Mathf.Lerp(splay, w.splay, k); reach = Mathf.Lerp(reach, w.reach, k); tuck = Mathf.Lerp(tuck, w.tuck, k); stiff = Mathf.Lerp(stiff, w.stiff, k);
            }
        }

        public Shape s;
        public Transform trunk, neck, head, jaw, tail;
        public readonly Transform[] upper = new Transform[4], lower = new Transform[4];   // 0 left fore, 1 right fore, 2 left hind, 3 right hind
        Vector3 trunkRest;
        public Vector3 headBase, headDir, headUp;       // the head's own frame at rest, for anything a species adds to it
        public Vector3 neckBase, neckDir, tailBase, tailDir, trunkAt;
        public float halfLeg;
        public Vector3 Hip(int i) => trunkRest + hipOff[i];
        readonly Vector3[] hipOff = new Vector3[4], footRest = new Vector3[4];
        float legLen;
        protected Bearing now, want;
        protected Gait gait;
        protected float time, phase, moving, ease = 10f, bobScale = 1f;
        protected bool followTravel = true;

        static Transform Bone(string name, Transform parent, Vector3 at)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = at;
            return go.transform;
        }

        public static T Make<T>(ModelActor a, Shape s) where T : Beast, new()
        {
            var b = new T { s = s };
            var rig = a.rig;
            b.trunkRest = new Vector3(0, s.height + s.girth * 0.5f, 0);
            b.trunk = Bone("trunk", rig, b.trunkRest);
            float neckA = s.neckRise * Mathf.Deg2Rad, tiltA = s.headTilt * Mathf.Deg2Rad, tailA = s.tailRise * Mathf.Deg2Rad;
            Vector3 neckDir = new Vector3(0, Mathf.Sin(neckA), Mathf.Cos(neckA)), headDir = new Vector3(0, -Mathf.Sin(tiltA), Mathf.Cos(tiltA));
            Vector3 tailDir = new Vector3(0, Mathf.Sin(tailA), -Mathf.Cos(tailA));
            Vector3 neckBase = b.trunkRest + new Vector3(0, s.girth * 0.35f, s.length * 0.5f + s.chest * 0.15f);
            Vector3 headBase = neckBase + neckDir * s.neckLen;
            Vector3 jawBase = headBase + headDir * s.headLen * 0.25f + new Vector3(0, -s.headThick * 0.55f, 0);
            Vector3 tailBase = b.trunkRest + new Vector3(0, s.girth * 0.45f, -s.length * 0.5f - s.rump * 0.55f);
            b.neck = Bone("neck", b.trunk, neckBase - b.trunkRest);
            b.head = Bone("head", b.neck, headBase - neckBase);
            b.jaw = Bone("jaw", b.head, jawBase - headBase);
            b.tail = Bone("tail", b.trunk, tailBase - b.trunkRest);
            float half = s.height * 0.53f;
            b.legLen = half * 2f;
            var bones = new List<Transform> { b.trunk, b.neck, b.head, b.jaw, b.tail };
            for (int i = 0; i < 4; i++)
            {
                bool front = i < 2;
                float x = (i % 2 == 0 ? -1 : 1) * s.stance;
                b.hipOff[i] = new Vector3(x, -s.girth * 0.5f, front ? s.length * 0.5f - 0.03f : -s.length * 0.5f + 0.05f);
                var hip = b.trunkRest + b.hipOff[i];
                b.footRest[i] = new Vector3(hip.x, 0, hip.z);
                b.upper[i] = Bone("ul" + i, rig, hip);
                b.lower[i] = Bone("ll" + i, rig, hip + Vector3.down * half);
                bones.Add(b.upper[i]);
                bones.Add(b.lower[i]);
            }
            foreach (var t in bones) a.bones[t.name] = t;

            var kit = new Kit(a, rig, bones.ToArray());
            float m = s.metal;
            b.neckBase = neckBase; b.neckDir = neckDir; b.tailBase = tailBase; b.tailDir = tailDir; b.trunkAt = b.trunkRest; b.halfLeg = half;
            b.headBase = headBase; b.headDir = headDir; b.headUp = Vector3.Cross(headDir, Vector3.right);
            if (s.skin != null)
            {
                s.skin(kit, b);
                kit.Frame();
                kit.Wear("Hide");
                return b;
            }
            // trunk: barrel, chest and rump, paler underneath
            float bellyLine = b.trunkRest.y - s.girth * 0.42f;
            float backLine = b.trunkRest.y + s.girth * 0.45f;
            kit.On("trunk").Stain(p => p.y < bellyLine ? s.belly : s.back.HasValue && p.y > backLine ? s.back : (Color?)null).Paint(s.coat, m);
            kit.Egg(b.trunkRest, new Vector3(s.girth, s.girth, s.length * 0.5f + s.girth * 0.3f), 12, 7);
            kit.Egg(b.trunkRest + new Vector3(0, 0.01f, s.length * 0.5f - s.chest * 0.4f), new Vector3(s.chest, s.chest * 1.06f, s.chest * 1.05f), 12, 7);
            kit.Egg(b.trunkRest + new Vector3(0, 0.005f, -s.length * 0.5f + s.rump * 0.45f), new Vector3(s.rump, s.rump, s.rump * 1.05f), 12, 7);
            kit.Stain(null);
            // neck
            kit.On("neck").Frame(neckBase, Vector3.right, neckDir, Vector3.Cross(Vector3.right, neckDir));
            kit.Egg(new Vector3(0, s.neckLen * 0.45f, 0), new Vector3(s.neckThick, s.neckLen * 0.5f + s.neckThick * 0.7f, s.neckThick * 1.2f), 10, 6);
            // head: skull, muzzle, nose, eyes, ears, horns, beard (z runs along the muzzle)
            var headUp = Vector3.Cross(headDir, Vector3.right);
            b.headBase = headBase;
            b.headDir = headDir;
            b.headUp = headUp;
            kit.On("head").Frame(headBase, Vector3.right, headUp, headDir);
            kit.Paint(s.coat, m).Egg(new Vector3(0, 0, s.headLen * 0.28f), new Vector3(s.headThick, s.headThick, s.headLen * 0.42f), 10, 6);
            if (s.muzzle.HasValue) kit.Paint(s.muzzle.Value, m);
            kit.Egg(new Vector3(0, -s.headThick * 0.18f, s.headLen * 0.66f), new Vector3(s.headThick * 0.64f, s.headThick * 0.6f, s.headLen * 0.38f), 8, 5);
            kit.Paint(s.dark, m).Egg(new Vector3(0, -s.headThick * 0.12f, s.headLen * 0.99f), new Vector3(s.headThick * 0.4f, s.headThick * 0.32f, s.headLen * 0.09f), 6, 4);
            kit.Paint(s.eye, 0, s.eyeGlow);
            foreach (int side in new[] { -1, 1 })
                kit.Egg(new Vector3(side * s.headThick * 0.86f, s.headThick * 0.28f, s.headLen * 0.40f), new Vector3(s.headThick * 0.22f, s.headThick * 0.26f, s.headThick * 0.30f), 6, 4);
            kit.Paint(s.coat, m);
            foreach (int side in new[] { -1, 1 })
            {
                if (s.earsUp) kit.Egg(new Vector3(side * s.headThick * 0.62f, s.headThick * 0.75f + s.earLen * 0.42f, s.headLen * 0.10f), new Vector3(s.headThick * 0.36f, s.earLen * 0.55f, s.headThick * 0.22f), 6, 4);
                else kit.Egg(new Vector3(side * (s.headThick * 0.85f + s.earLen * 0.42f), s.headThick * 0.30f, s.headLen * 0.10f), new Vector3(s.earLen * 0.55f, s.headThick * 0.24f, s.headThick * 0.4f), 6, 4);
            }
            if (s.horn != null)
            {
                kit.Paint(s.hornColour, m);
                foreach (int side in new[] { -1, 1 })
                {
                    var path = new Vector3[s.horn.Length];
                    var thick = new float[s.horn.Length];
                    for (int i = 0; i < path.Length; i++) { path[i] = new Vector3(s.horn[i].at.x * side, s.horn[i].at.y, s.horn[i].at.z); thick[i] = s.horn[i].r; }
                    kit.Tube(path, thick, 6);
                }
            }
            if (s.beard) kit.Paint(s.coat, m).On("jaw").Egg(new Vector3(0, -s.headThick * 1.25f, s.headLen * 0.5f), new Vector3(s.headThick * 0.26f, s.headThick * 0.62f, s.headThick * 0.34f), 6, 4);
            kit.Paint(s.belly, m).On("jaw").Egg(new Vector3(0, -s.headThick * 0.62f, s.headLen * 0.56f), new Vector3(s.headThick * 0.5f, s.headThick * 0.26f, s.headLen * 0.34f), 8, 4);
            if (s.collar.HasValue)
            {
                kit.Paint(s.collar.Value).On("neck").Frame(neckBase, Vector3.right, neckDir, Vector3.Cross(Vector3.right, neckDir));
                kit.Turned(Vector3.zero, new[] { (s.neckThick * 1.12f, s.neckLen * 0.42f), (s.neckThick * 1.16f, s.neckLen * 0.62f) }, 8, 1.2f);
            }
            // tail
            kit.Paint(s.back ?? s.coat, m).On("tail").Frame(tailBase, Vector3.right, tailDir, Vector3.Cross(Vector3.right, tailDir));
            kit.Egg(new Vector3(0, s.tailLen * 0.45f, 0), new Vector3(s.tailThick, s.tailLen * 0.55f, s.tailThick), 6, 5);
            kit.Frame();
            // legs: thigh and shank, a hoof or paw at the bottom
            for (int i = 0; i < 4; i++)
            {
                var hip = b.trunkRest + b.hipOff[i];
                kit.Paint(s.coat, m).On("ul" + i).Egg(hip + Vector3.down * half * 0.5f, new Vector3(s.legThick * 1.3f, half * 0.5f + s.legThick * 0.6f, s.legThick * 1.6f), 8, 5);
                if (s.sock.HasValue) kit.Paint(s.sock.Value, m);
                kit.On("ll" + i).Egg(hip + Vector3.down * half * 1.5f, new Vector3(s.legThick * 0.9f, half * 0.5f + 0.012f, s.legThick), 8, 5);
                kit.Paint(s.dark, m).Egg(hip + Vector3.down * (half * 2f - 0.03f) + new Vector3(0, 0, 0.012f), new Vector3(s.legThick * 1.1f, 0.04f, s.legThick * 1.35f), 6, 4);
            }
            s.extra?.Invoke(kit, b);
            kit.Frame();
            kit.Wear("Hide");
            return b;
        }

        /// <summary>The species says what it wants its body to do for this animation.</summary>
        protected virtual void Style(ModelActor a, string anim, float n, float speed) { }

        /// <summary>How far round (degrees) the creature would have to turn its head to look at Azar.</summary>
        protected float LookAt(ModelActor a)
        {
            var p = Player.I;
            if (!p || !a.sr) return 0;
            Vector2 here = a.sr.transform.parent ? a.sr.transform.parent.position : a.sr.transform.position;
            var d = p.pos - here;
            if (d.sqrMagnitude < 0.01f) return 0;
            return Mathf.DeltaAngle(a.yaw, Mathf.Atan2(d.x, d.y) * Mathf.Rad2Deg);
        }

        public virtual void Pose(ModelActor a, string anim, float n, float dt)
        {
            time += dt;
            float scale = a.def.scale;
            Vector2 v = a.velocity / scale;                         // metres a second, in the world's axes
            float speed = v.magnitude;
            if (followTravel && speed * scale > 0.3f) a.Aim(a.velocity);
            // which way the ground is passing, in the creature's own frame
            float yaw = a.yaw * Mathf.Deg2Rad;
            Vector2 ahead = new Vector2(Mathf.Sin(yaw), Mathf.Cos(yaw)), side = new Vector2(ahead.y, -ahead.x);
            Vector3 travel = speed > 0.03f ? new Vector3(Vector2.Dot(v, side), 0, Vector2.Dot(v, ahead)) / speed : Vector3.forward;

            want = default;
            gait = Gait.Walk;
            bobScale = 1f;
            Style(a, anim ?? "idle", n, speed);
            now.Towards(want, 1f - Mathf.Exp(-ease * dt));
            moving = Mathf.MoveTowards(moving, speed > 0.06f ? 1f : 0f, dt * 6f);
            phase += speed * dt / Mathf.Max(0.05f, s.stride);

            float duty = Duty[(int)gait];
            float bob = gait == Gait.Bound ? Mathf.Sin(phase * Mathf.PI * 2f) : Mathf.Sin(phase * Mathf.PI * 4f);
            float rock = gait == Gait.Bound ? Mathf.Sin(phase * Mathf.PI * 2f + 1.2f) * 9f : 0f;
            var tp = trunkRest + new Vector3(0, bob * s.stepHeight * 0.3f * bobScale * moving - now.drop + now.lift, now.surge);
            var tr = Quaternion.Euler(now.pitch + rock * moving, 0, now.roll);
            trunk.localPosition = tp;
            trunk.localRotation = tr;

            for (int i = 0; i < 4; i++)
            {
                bool front = i < 2;
                var hip = tp + tr * hipOff[i];
                var foot = footRest[i] + new Vector3(Mathf.Sign(footRest[i].x) * now.splay, 0, front ? now.reach : -now.reach);
                float u = Mathf.Repeat(phase + Offsets[(int)gait][front ? (i == 0 ? 1 : 3) : (i == 2 ? 0 : 2)], 1f);
                if (u < duty) foot += travel * ((0.5f - u / duty) * duty * s.stride * moving);
                else
                {
                    float w = (u - duty) / (1f - duty), e = w * w * (3f - 2f * w);
                    foot += travel * ((-0.5f + e) * duty * s.stride * moving);
                    foot.y += s.stepHeight * Mathf.Sin(w * Mathf.PI) * moving;
                }
                // tucked under, held stiff or stretched in a leap, a leg goes with the body instead of the ground
                float carry = Mathf.Max(now.tuck, now.stiff);
                if (carry > 0.001f)
                {
                    var held = tp + tr * (hipOff[i] + new Vector3(0, -legLen * (1f - now.tuck * 0.72f), front ? now.tuck * 0.13f : now.tuck * 0.02f));
                    foot = Vector3.Lerp(foot, held, carry);
                }
                if (now.lift > 0.02f) foot.y += now.lift * 0.6f;
                Reach(i, hip, foot, front);
            }

            neck.localRotation = Quaternion.Euler(now.neckPitch, now.neckYaw, 0);
            head.localRotation = Quaternion.Euler(now.headPitch, now.headYaw, now.headRoll);
            jaw.localRotation = Quaternion.Euler(now.jaw, now.chew, 0);
            tail.localRotation = Quaternion.Euler(-now.tailPitch, now.tailYaw, 0);
        }

        /// <summary>Two bones to reach a foot: the joint folds forward on a foreleg (a knee), back on a hind leg (a hock).</summary>
        void Reach(int i, Vector3 hip, Vector3 foot, bool front)
        {
            float half = legLen * 0.5f;
            var d = foot - hip;
            float len = Mathf.Clamp(d.magnitude, 0.02f, legLen - 0.002f);
            var dir = d.sqrMagnitude > 0.000001f ? d.normalized : Vector3.down;
            float along = len * 0.5f, off = Mathf.Sqrt(Mathf.Max(0, half * half - along * along));
            var bend = front ? Vector3.forward : Vector3.back;
            bend -= dir * Vector3.Dot(bend, dir);
            bend = bend.sqrMagnitude > 0.0001f ? bend.normalized : Vector3.forward;
            var knee = hip + dir * along + bend * off;
            upper[i].localPosition = hip;
            upper[i].localRotation = Quaternion.FromToRotation(Vector3.down, knee - hip);
            lower[i].localPosition = knee;
            lower[i].localRotation = Quaternion.FromToRotation(Vector3.down, hip + dir * len - knee);
        }
    }

    // ----------------------------------------------------------------------------------- goat
    /// <summary>The goat. It is awake. It has always been awake. Its head follows Azar wherever he goes.</summary>
    public class Goat : Beast
    {
        public static Shape Body => new Shape
        {
            coat = new Color(0.97f, 0.94f, 0.87f), belly = new Color(0.84f, 0.79f, 0.70f), dark = new Color(0.22f, 0.17f, 0.15f),
            hornColour = new Color(0.42f, 0.34f, 0.27f), muzzle = new Color(0.93f, 0.74f, 0.70f), eye = new Color(0.10f, 0.07f, 0.06f),
            beard = true, length = 0.70f, height = 0.52f, girth = 0.205f, chest = 0.21f, rump = 0.205f, legThick = 0.042f, stance = 0.12f,
            neckLen = 0.22f, neckRise = 62f, neckThick = 0.095f, headLen = 0.29f, headThick = 0.105f, headTilt = 26f,
            tailLen = 0.11f, tailRise = 70f, tailThick = 0.04f, earLen = 0.12f, stride = 0.56f, stepHeight = 0.075f,
            horn = new[]
            {
                (new Vector3(0.05f, 0.085f, 0.03f), 0.040f), (new Vector3(0.062f, 0.16f, -0.005f), 0.036f), (new Vector3(0.08f, 0.225f, -0.07f), 0.030f),
                (new Vector3(0.10f, 0.255f, -0.15f), 0.022f), (new Vector3(0.118f, 0.245f, -0.215f), 0.010f),
            },
        };

        protected override void Style(ModelActor a, string anim, float n, float speed)
        {
            float look = Mathf.Clamp(LookAt(a), -110f, 110f);
            switch (anim)
            {
                case "stare":
                    want.neckYaw = look * 0.55f; want.headYaw = look * 0.45f; want.headPitch = -4f;
                    want.tailYaw = Mathf.Sin(time * 0.8f) > 0.96f ? 30f : 0f;
                    break;
                case "eat":
                    want.neckPitch = 92f; want.headPitch = 12f; want.jaw = 7f; want.chew = Mathf.Sin(time * 9f) * 14f;
                    want.tailYaw = Mathf.Sin(time * 6f) * 22f;
                    break;
                case "bleat":
                {
                    float k = Mathf.Sin(Mathf.Clamp01(n) * Mathf.PI);
                    want.neckPitch = -20f * k; want.headPitch = -24f * k; want.jaw = 38f * k; want.roll = Mathf.Sin(time * 46f) * 2.2f * k;
                    want.neckYaw = look * 0.4f; want.headYaw = look * 0.3f; ease = 26f;
                    break;
                }
                case "butt":
                {
                    float k = Mathf.Sin(Mathf.Clamp01(n) * Mathf.PI);
                    want.neckPitch = 58f * k; want.headPitch = 26f * k; want.surge = 0.22f * k; want.pitch = 6f * k; ease = 30f;
                    break;
                }
                case "walk":
                    want.neckPitch = 6f + Mathf.Sin(phase * Mathf.PI * 4f) * 5f;
                    want.tailYaw = Mathf.Sin(time * 5f) * 16f;
                    break;
                default:
                    want.neckYaw = Mathf.Sin(time * 0.45f) * 28f; want.headYaw = Mathf.Sin(time * 0.45f + 0.6f) * 14f;
                    want.jaw = 5f; want.chew = Mathf.Sin(time * 7.5f) * 13f;
                    want.tailYaw = Mathf.Sin(time * 1.3f) > 0.8f ? Mathf.Sin(time * 16f) * 26f : 0f;
                    break;
            }
            if (anim != "bleat" && anim != "butt") ease = 10f;
        }
    }

    // ------------------------------------------------------------------------------------ dog
    public class Dog : Beast
    {
        public static Shape Body => new Shape
        {
            coat = new Color(0.72f, 0.50f, 0.30f), belly = new Color(0.90f, 0.78f, 0.58f), dark = new Color(0.18f, 0.13f, 0.11f),
            muzzle = new Color(0.92f, 0.82f, 0.64f), sock = new Color(0.92f, 0.82f, 0.64f), collar = new Color(0.80f, 0.16f, 0.14f),
            length = 0.62f, height = 0.40f, girth = 0.14f, chest = 0.15f, rump = 0.135f, legThick = 0.04f, stance = 0.10f,
            neckLen = 0.17f, neckRise = 48f, neckThick = 0.075f, headLen = 0.21f, headThick = 0.082f, headTilt = 12f,
            tailLen = 0.24f, tailRise = 38f, tailThick = 0.028f, earLen = 0.085f, stride = 0.46f, stepHeight = 0.06f,
        };

        protected override void Style(ModelActor a, string anim, float n, float speed)
        {
            switch (anim)
            {
                case "sleep":
                    // flat out by the well, nose on his paws, paws going: he is chasing something
                    want.tuck = 1f; want.drop = s.height - s.girth * 0.25f; want.neckPitch = 58f; want.headPitch = -4f;
                    want.tailYaw = 70f; want.tailPitch = -30f; want.roll = 4f;
                    want.reach = Mathf.Sin(time * 1.1f) > 0.6f ? Mathf.Sin(time * 19f) * 0.035f : 0f;
                    want.pitch = Mathf.Sin(time * 1.6f) * 1.2f;
                    break;
                case "walk":
                    gait = Gait.Trot;
                    want.neckPitch = 6f; want.tailPitch = 30f; want.tailYaw = Mathf.Sin(time * 11f) * 26f; want.jaw = 9f;
                    break;
                default:
                    // in the dream he is a lion: chest out, tail up
                    want.neckPitch = -14f; want.headPitch = -6f; want.tailPitch = 46f; want.tailYaw = Mathf.Sin(time * 13f) * 34f;
                    want.jaw = 10f + Mathf.Sin(time * 9f) * 6f; want.headRoll = Mathf.Sin(time * 0.7f) * 9f;
                    break;
            }
        }
    }

    // --------------------------------------------------------------------------------- jackal
    public class JackalBeast : Beast
    {
        public static Shape Body => new Shape
        {
            coat = new Color(0.74f, 0.56f, 0.34f), belly = new Color(0.90f, 0.80f, 0.60f), dark = new Color(0.15f, 0.11f, 0.10f),
            back = new Color(0.30f, 0.24f, 0.22f), muzzle = new Color(0.90f, 0.80f, 0.60f),
            length = 0.70f, height = 0.50f, girth = 0.125f, chest = 0.15f, rump = 0.125f, legThick = 0.038f, stance = 0.095f,
            neckLen = 0.20f, neckRise = 38f, neckThick = 0.07f, headLen = 0.27f, headThick = 0.078f, headTilt = 10f,
            tailLen = 0.36f, tailRise = -28f, tailThick = 0.062f, earLen = 0.17f, earsUp = true, stride = 0.70f, stepHeight = 0.08f,
            eye = new Color(1.0f, 0.82f, 0.30f), eyeGlow = 1f,
        };

        protected override void Style(ModelActor a, string anim, float n, float speed)
        {
            ease = 14f;
            switch (anim)
            {
                case "run":
                    gait = speed > 3.2f ? Gait.Bound : Gait.Trot;
                    want.neckPitch = 14f; want.headPitch = -8f; want.tailPitch = 18f;
                    break;
                case "walk":
                    want.neckPitch = 24f; want.headPitch = -12f; want.neckYaw = Mathf.Sin(time * 1.4f) * 12f;
                    break;
                case "crouch":
                    // down on its elbows, haunches up, lips back
                    want.pitch = 13f; want.drop = 0.07f; want.neckPitch = -6f; want.headPitch = -14f; want.jaw = 16f; want.tailPitch = 26f;
                    want.roll = Mathf.Sin(time * 34f) * 1.2f;
                    break;
                case "lunge":
                    want.reach = 0.2f; want.stiff = 0.6f; want.pitch = -9f; want.neckPitch = 10f; want.headPitch = -10f; want.jaw = 32f; want.tailPitch = 24f;
                    a.height = Mathf.Sin(Mathf.Clamp01(n) * Mathf.PI) * 0.38f;
                    ease = 30f;
                    break;
                case "hurt":
                    want.roll = 22f; want.pitch = -8f; want.neckPitch = -20f; want.jaw = 24f; ease = 30f;
                    break;
                default:
                    want.neckPitch = 18f; want.headPitch = -10f; want.neckYaw = Mathf.Sin(time * 0.9f) * 30f; want.jaw = 6f + Mathf.Sin(time * 8f) * 4f;
                    break;
            }
            if (anim != "lunge") a.height = Mathf.MoveTowards(a.height, 0, Time.deltaTime * 3f);
        }
    }

    // ----------------------------------------------------------------------------------- bull
    /// <summary>The Brazen Bull: the high priest's guilt, cast in bronze, with fire in its throat.</summary>
    public class BullBeast : Beast
    {
        static readonly Color Fire = new Color(1.0f, 0.62f, 0.16f), Seam = new Color(0.34f, 0.19f, 0.08f), Gold = new Color(0.96f, 0.80f, 0.40f);

        static readonly Color Bronze = new Color(0.70f, 0.42f, 0.15f), BronzeLight = new Color(0.82f, 0.54f, 0.20f), BronzeDark = new Color(0.36f, 0.20f, 0.09f),
            Lapis = new Color(0.10f, 0.19f, 0.58f), LapisDark = new Color(0.06f, 0.10f, 0.34f), Soot = new Color(0.10f, 0.06f, 0.05f);

        public static Shape Body => new Shape
        {
            coat = Bronze, belly = BronzeDark, dark = BronzeDark, hornColour = Gold, eye = Fire, eyeGlow = 1f, metal = 0.5f,
            length = 1.50f, height = 0.92f, girth = 0.46f, chest = 0.58f, rump = 0.45f, legThick = 0.125f, stance = 0.30f,
            neckLen = 0.40f, neckRise = 14f, neckThick = 0.34f, headLen = 0.64f, headThick = 0.26f, headTilt = 38f,
            tailLen = 0.66f, tailRise = -64f, tailThick = 0.05f, earLen = 0.17f, stride = 1.5f, stepHeight = 0.16f,
            skin = Cast,
        };

        /// <summary>The bull as the founders cast it: one great body drawn through its sections instead of
        /// lumps stuck together, squared off like poured bronze; a hump and a deep chest; belts of gold
        /// round the barrel with the furnace showing through a grille between them; a cloth of blue and
        /// gold laid over its back; lyre horns; a brow like a lintel over eyes of fire; a beard of lapis
        /// the way the old bull-heads wore one; and its tail ends in flame.</summary>
        static void Cast(Kit kit, Beast b)
        {
            var s = b.s;
            float m = 0.6f;
            const float Dull = -1f;         // plain metal: lit by the fire, never taken for fire itself
            (Vector3, float, float) R(float z, float hw, float hh, float cy) => (new Vector3(0, cy, z), hw, hh);
            // ---- the body
            var body = new[]
            {
                R(-0.93f, 0.15f, 0.19f, 1.21f), R(-0.80f, 0.35f, 0.39f, 1.17f), R(-0.52f, 0.44f, 0.46f, 1.15f), R(-0.12f, 0.41f, 0.43f, 1.13f),
                R(0.28f, 0.46f, 0.50f, 1.16f), R(0.60f, 0.52f, 0.61f, 1.25f), R(0.84f, 0.45f, 0.51f, 1.23f), R(1.00f, 0.27f, 0.31f, 1.20f),
            };
            kit.On("trunk").Stain(p => p.y < 0.86f ? BronzeDark : p.y > 1.58f && p.z > 0.3f ? BronzeLight : (Color?)null).Paint(Bronze, m, Dull);
            kit.Loft(body, 3.0f, 18);
            kit.Stain(null);
            (Vector3, float, float)[] Slice(float z0, float z1, float grow, int steps = 3)
            {
                // the body's own section between two stations, let out a little: a belt, a plate, a cloth
                var o = new (Vector3, float, float)[steps];
                for (int i = 0; i < steps; i++)
                {
                    float z = Mathf.Lerp(z0, z1, i / (float)(steps - 1));
                    int k = 0;
                    while (k < body.Length - 2 && body[k + 1].Item1.z < z) k++;
                    float t = Mathf.InverseLerp(body[k].Item1.z, body[k + 1].Item1.z, z);
                    o[i] = (new Vector3(0, Mathf.Lerp(body[k].Item1.y, body[k + 1].Item1.y, t), z), Mathf.Lerp(body[k].Item2, body[k + 1].Item2, t) + grow, Mathf.Lerp(body[k].Item3, body[k + 1].Item3, t) + grow);
                }
                return o;
            }
            // two belts of gold, riveted
            kit.Paint(Gold, 1, Dull);
            kit.Loft(Slice(-0.40f, -0.30f, 0.022f), 3.0f, 18, true, true);
            kit.Loft(Slice(0.40f, 0.50f, 0.022f), 3.0f, 18, true, true);
            // the cloth over its back: blue, bordered and lozenged in gold
            kit.Stain(p =>
            {
                float u = Mathf.Abs(p.x), z = p.z - 0.05f;
                if (Mathf.Abs(z) > 0.29f || u > 0.40f) return Gold;                                   // border and the hanging edge
                float d = Mathf.Abs(Mathf.Repeat(z + 0.6f, 0.2f) - 0.1f) / 0.1f + Mathf.Abs(Mathf.Repeat(u, 0.2f) - 0.1f) / 0.1f;
                return d < 0.55f ? Gold : ((Mathf.FloorToInt((z + 0.6f) / 0.2f) + Mathf.FloorToInt(u / 0.2f)) & 1) == 0 ? Lapis : LapisDark;
            });
            kit.Paint(Lapis, 0.15f, Dull).Loft(Slice(-0.30f, 0.40f, 0.03f, 15), 3.0f, 22, false, false, -74f, 74f);
            kit.Stain(null);
            // the furnace: a soot-black grille let into each flank under the cloth, fire behind its bars
            foreach (int side in new[] { -1, 1 })
            {
                float x = side * 0.445f;
                kit.Paint(Soot, 0, Dull).Box(new Vector3(x, 0.99f, 0.05f), new Vector3(0.05f, 0.30f, 0.56f));
                kit.Paint(Fire, 0, 1);
                for (int i = 0; i < 5; i++) kit.Box(new Vector3(side * 0.462f, 0.99f, -0.17f + i * 0.11f), new Vector3(0.03f, 0.24f, 0.05f));
                kit.Paint(BronzeDark, 1, Dull);
                kit.Box(new Vector3(side * 0.468f, 1.135f, 0.05f), new Vector3(0.035f, 0.035f, 0.60f));
                kit.Box(new Vector3(side * 0.468f, 0.845f, 0.05f), new Vector3(0.035f, 0.035f, 0.60f));
            }
            // ---- neck: thick, short, carried low, a dewlap under it and a gold collar
            var up = Vector3.Cross(b.neckDir, Vector3.right);
            kit.On("neck").Frame(b.neckBase, Vector3.right, up, b.neckDir).Paint(Bronze, m, Dull);
            kit.Stain(p => p.y < 1.02f ? BronzeDark : (Color?)null);
            kit.Loft(new[] { (new Vector3(0, -0.10f, -0.26f), 0.37f, 0.42f), (new Vector3(0, -0.07f, 0.04f), 0.32f, 0.36f), (new Vector3(0, -0.03f, 0.32f), 0.27f, 0.28f), (new Vector3(0, 0, 0.50f), 0.22f, 0.22f) }, 2.8f, 16);
            kit.Stain(null);
            kit.Paint(Gold, 1, Dull).Loft(new[] { (new Vector3(0, -0.045f, 0.20f), 0.305f, 0.325f), (new Vector3(0, -0.035f, 0.29f), 0.290f, 0.305f) }, 2.8f, 16);
            kit.Paint(BronzeDark, m, Dull).Fin(new[] { new Vector3(0, -0.40f, -0.10f), new Vector3(0, -0.34f, 0.16f), new Vector3(0, -0.26f, 0.40f) },
                                          new[] { new Vector3(0, -0.62f, -0.06f), new Vector3(0, -0.56f, 0.14f), new Vector3(0, -0.32f, 0.40f) }, 0.07f);
            // ---- head: a long wedge, broad at the brow, square at the muzzle
            kit.On("head").Frame(b.headBase, Vector3.right, b.headUp, b.headDir).Paint(Bronze, m, Dull);
            kit.Loft(new[]
            {
                (new Vector3(0, 0.02f, -0.12f), 0.23f, 0.21f), (new Vector3(0, 0.03f, 0.06f), 0.285f, 0.25f), (new Vector3(0, 0.02f, 0.26f), 0.25f, 0.22f),
                (new Vector3(0, -0.005f, 0.44f), 0.185f, 0.17f), (new Vector3(0, -0.02f, 0.58f), 0.175f, 0.155f), (new Vector3(0, -0.025f, 0.665f), 0.15f, 0.13f),
            }, 3.4f, 14);
            kit.Paint(BronzeLight, m, Dull).Box(new Vector3(0, 0.185f, 0.25f), new Vector3(0.54f, 0.075f, 0.11f));                 // the brow
            kit.Paint(Soot, 0, Dull).Box(new Vector3(0, -0.03f, 0.675f), new Vector3(0.26f, 0.20f, 0.03f));                         // the nose
            kit.Paint(Fire, 0, 1);
            foreach (int side in new[] { -1, 1 })
            {
                kit.Egg(new Vector3(side * 0.232f, 0.085f, 0.27f), new Vector3(0.035f, 0.055f, 0.075f), 6, 4);                // an eye of fire
                kit.Box(new Vector3(side * 0.065f, -0.02f, 0.692f), new Vector3(0.055f, 0.07f, 0.012f));                      // a nostril
            }
            kit.Paint(Gold, 1).Egg(new Vector3(0, -0.175f, 0.655f), new Vector3(0.085f, 0.085f, 0.022f), 8, 4);              // the ring
            // curls of lapis between the horns
            kit.Paint(Lapis, 0.2f);
            for (int i = 0; i < 3; i++) kit.Egg(new Vector3((i - 1) * 0.105f, 0.235f, 0.045f + (i == 1 ? 0.03f : 0f)), new Vector3(0.062f, 0.055f, 0.075f), 6, 4);
            kit.Paint(Gold, 1, Dull).Box(new Vector3(0, 0.215f, 0.135f), new Vector3(0.36f, 0.045f, 0.03f));
            // ears, low and flat under the horns
            kit.Paint(Bronze, m, Dull);
            foreach (int side in new[] { -1, 1 })
                kit.Egg(new Vector3(side * 0.36f, 0.035f, -0.005f), new Vector3(0.125f, 0.05f, 0.075f), 6, 4);
            // the horns: out, up and forward in a lyre, each from a bronze socket
            var horn = new[]
            {
                (new Vector3(0.20f, 0.20f, 0.06f), 0.105f), (new Vector3(0.40f, 0.27f, 0.10f), 0.094f), (new Vector3(0.57f, 0.38f, 0.20f), 0.080f),
                (new Vector3(0.67f, 0.53f, 0.34f), 0.062f), (new Vector3(0.685f, 0.70f, 0.50f), 0.038f), (new Vector3(0.65f, 0.83f, 0.62f), 0.010f),
            };
            foreach (int side in new[] { -1, 1 })
            {
                var path = new Vector3[horn.Length];
                var thick = new float[horn.Length];
                for (int i = 0; i < path.Length; i++) { path[i] = new Vector3(horn[i].Item1.x * side, horn[i].Item1.y, horn[i].Item1.z); thick[i] = horn[i].Item2; }
                kit.Paint(Gold, 1).Tube(path, thick, 8);
                kit.Paint(BronzeDark, 1, Dull).Egg(new Vector3(side * 0.22f, 0.205f, 0.065f), new Vector3(0.125f, 0.125f, 0.125f), 8, 5);
            }
            // ---- jaw: the lower jaw, the fire behind the teeth, the squared beard of lapis tipped in gold
            kit.On("jaw").Paint(BronzeDark, m, Dull).Box(new Vector3(0, -0.185f, 0.40f), new Vector3(0.27f, 0.085f, 0.44f));
            kit.Paint(Fire, 0, 1).Box(new Vector3(0, -0.135f, 0.44f), new Vector3(0.22f, 0.03f, 0.40f));
            kit.Paint(Lapis, 0.2f);
            kit.Stain(p => (Mathf.FloorToInt(p.y / 0.055f) & 1) == 0 ? Lapis : LapisDark);
            kit.Box(new Vector3(0, -0.37f, 0.30f), new Vector3(0.17f, 0.30f, 0.13f));
            kit.Stain(null);
            kit.Paint(Gold, 1, Dull).Box(new Vector3(0, -0.535f, 0.30f), new Vector3(0.19f, 0.045f, 0.15f));
            kit.Frame();
            // ---- legs: a shoulder plate with a gold boss, a tapering forearm, a knee, a cannon, a gold fetlock, a hoof
            float half = b.halfLeg;
            for (int i = 0; i < 4; i++)
            {
                var hip = b.Hip(i);
                float side = Mathf.Sign(hip.x);
                bool front = i < 2;
                var knee = hip + Vector3.down * half;
                kit.On("ul" + i).Paint(Bronze, m, Dull).Tube(new[] { hip + new Vector3(0, 0.12f, 0), hip + Vector3.down * half * 0.45f, knee }, new[] { front ? 0.235f : 0.25f, 0.17f, 0.125f }, 10);
                kit.Paint(BronzeLight, m, Dull).Egg(hip + new Vector3(side * 0.14f, 0.02f, 0), new Vector3(0.10f, 0.25f, 0.23f), 10, 6);
                kit.Paint(Gold, 1, Dull).Egg(hip + new Vector3(side * 0.225f, 0.04f, 0), new Vector3(0.035f, 0.07f, 0.07f), 6, 4);
                kit.On("ll" + i).Paint(BronzeDark, m, Dull).Egg(knee, new Vector3(0.135f, 0.12f, 0.145f), 8, 5);
                kit.Paint(Bronze, m, Dull).Tube(new[] { knee, knee + Vector3.down * half * 0.55f, knee + Vector3.down * (half - 0.12f) }, new[] { 0.115f, 0.085f, 0.095f }, 8);
                kit.Paint(Gold, 1, Dull).Turned(knee + Vector3.down * (half - 0.17f), new[] { (0.112f, 0f), (0.112f, 0.05f) }, 8);
                kit.Paint(Soot, 0.4f, Dull).Turned(knee + Vector3.down * half + new Vector3(0, 0, 0.012f), new[] { (0.155f, 0f), (0.125f, 0.07f), (0.105f, 0.135f) }, 8);
            }
            // ---- tail: a rope of bronze, and at the end of it a flame
            var tup = Vector3.Cross(Vector3.right, b.tailDir);
            kit.On("tail").Frame(b.tailBase, Vector3.right, b.tailDir, tup).Paint(BronzeDark, m, Dull);
            kit.Tube(new[] { new Vector3(0, -0.04f, 0), new Vector3(0, s.tailLen * 0.5f, 0), new Vector3(0, s.tailLen * 0.92f, 0) }, new[] { 0.055f, 0.04f, 0.035f }, 6);
            kit.Paint(Gold, 1, Dull).Turned(new Vector3(0, s.tailLen * 0.86f, 0), new[] { (0.05f, 0f), (0.05f, 0.05f) }, 6);
            kit.Paint(Fire, 0, 1).Egg(new Vector3(0, s.tailLen * 1.04f, 0), new Vector3(0.075f, 0.15f, 0.075f), 6, 5);
            kit.Frame();
        }

        protected override void Style(ModelActor a, string anim, float n, float speed)
        {
            ease = 9f;
            bobScale = 1.4f;
            a.turnRate = 620f;
            switch (anim)
            {
                case "walk":
                    want.neckPitch = 10f + Mathf.Sin(phase * Mathf.PI * 4f) * 4f; want.tailYaw = Mathf.Sin(time * 3f) * 20f;
                    break;
                case "charge":
                    gait = Gait.Bound;
                    want.neckPitch = 34f; want.headPitch = 16f; want.tailPitch = 70f;
                    break;
                case "shoot":
                {
                    // the head goes back, then the fire comes
                    float k = Mathf.Clamp01(n);
                    float back = Mathf.Sin(Mathf.Clamp01(k / 0.35f) * Mathf.PI * 0.5f) * (1f - Mathf.Clamp01((k - 0.35f) / 0.2f));
                    float thrust = Mathf.Clamp01((k - 0.35f) / 0.15f);
                    want.neckPitch = -26f * back + 8f * thrust; want.headPitch = -22f * back - 10f * thrust; want.jaw = 46f * thrust;
                    want.surge = -0.10f * back + 0.16f * thrust; ease = 22f;
                    break;
                }
                case "stun":
                    want.splay = 0.20f; want.drop = 0.16f; want.neckPitch = 58f; want.neckYaw = Mathf.Sin(time * 3.1f) * 24f;
                    want.roll = Mathf.Sin(time * 2.3f) * 5f; want.jaw = 14f;
                    break;
                case "hurt":
                    want.pitch = -9f; want.roll = 9f; want.neckPitch = -24f; want.jaw = 30f; ease = 28f;
                    break;
                case "death":
                {
                    float k = Mathf.Clamp01(n);
                    k = k * k * (3f - 2f * k);
                    want.roll = 84f * k; want.drop = (s.height - s.girth * 0.05f) * k; want.stiff = k; want.neckPitch = 30f * k; want.jaw = 20f * k;
                    ease = 16f;
                    break;
                }
                default:
                    want.neckPitch = 8f + Mathf.Sin(time * 1.4f) * 5f; want.neckYaw = Mathf.Sin(time * 0.6f) * 14f; want.jaw = 5f;
                    want.tailYaw = Mathf.Sin(time * 2.2f) * 24f; want.drop = Mathf.Sin(time * 1.4f) * 0.012f;
                    break;
            }
        }
    }

    // ----------------------------------------------------------------------------------- crab
    /// <summary>Brine crab: a flat shell on six legs that scuttle sideways, two claws that rise and snap.</summary>
    public class CrabBeast : IPoser
    {
        Transform shell;
        readonly Transform[] upper = new Transform[6], lower = new Transform[6], arm = new Transform[2], claw = new Transform[2];
        readonly Vector3[] hip = new Vector3[6], rest = new Vector3[6];
        Vector3 shellRest;
        float time, phase, moving, up, snap, flinch;
        const float Half = 0.17f;

        static Transform Bone(string name, Transform parent, Vector3 at)
        {
            var go = new GameObject(name);
            go.transform.SetParent(parent, false);
            go.transform.localPosition = at;
            return go.transform;
        }

        /// <summary>scarab: the same six legs under a tomb beetle instead, blue-black with a gold seam, jaws where the claws were.</summary>
        public static CrabBeast Make(ModelActor a, bool scarab = false)
        {
            var c = new CrabBeast();
            var rig = a.rig;
            Color red = new Color(0.82f, 0.30f, 0.20f), pale = new Color(0.94f, 0.62f, 0.44f), dark = new Color(0.34f, 0.10f, 0.10f);
            if (scarab) { red = new Color(0.10f, 0.15f, 0.36f); pale = new Color(0.90f, 0.70f, 0.28f); dark = new Color(0.05f, 0.05f, 0.10f); }
            c.shellRest = new Vector3(0, 0.17f, 0);
            c.shell = Bone("shell", rig, c.shellRest);
            var bones = new List<Transform> { c.shell };
            for (int i = 0; i < 6; i++)
            {
                int side = i % 2 == 0 ? -1 : 1, row = i / 2;
                c.hip[i] = new Vector3(side * 0.20f, -0.03f, 0.10f - row * 0.11f);
                var h = c.shellRest + c.hip[i];
                c.rest[i] = new Vector3(side * 0.44f, 0, 0.16f - row * 0.17f);
                c.upper[i] = Bone("cu" + i, rig, h);
                c.lower[i] = Bone("cl" + i, rig, h + new Vector3(side * Half, 0, 0));
                bones.Add(c.upper[i]);
                bones.Add(c.lower[i]);
            }
            for (int i = 0; i < 2; i++)
            {
                int side = i == 0 ? -1 : 1;
                c.arm[i] = Bone("arm" + i, c.shell, new Vector3(side * 0.17f, 0.0f, 0.15f));
                c.claw[i] = Bone("claw" + i, c.arm[i], new Vector3(side * 0.10f, 0.03f, 0.17f));
                bones.Add(c.arm[i]);
                bones.Add(c.claw[i]);
            }
            foreach (var t in bones) a.bones[t.name] = t;
            var kit = new Kit(a, rig, bones.ToArray());
            float line = c.shellRest.y - 0.02f;
            if (scarab)
            {
                // wing cases with a seam of gold down the middle and round the rim; a small dark head in front
                kit.On("shell").Stain(p => Mathf.Abs(p.x) < 0.014f || p.y < line + 0.012f ? pale : (Color?)null).Paint(red, 0.6f);
                kit.Egg(c.shellRest + new Vector3(0, 0.02f, -0.03f), new Vector3(0.22f, 0.135f, 0.25f), 12, 6);
                kit.Stain(null);
                kit.Paint(dark, 0.4f).Egg(c.shellRest + new Vector3(0, 0.0f, 0.24f), new Vector3(0.12f, 0.075f, 0.09f), 8, 5);
            }
            else
            {
                kit.On("shell").Stain(p => p.y < line ? pale : (Color?)null).Paint(red);
                kit.Egg(c.shellRest, new Vector3(0.27f, 0.105f, 0.19f), 12, 6);
                kit.Stain(null);
            }
            // eyes on stalks
            if (!scarab) foreach (int side in new[] { -1, 1 })
            {
                kit.Paint(red).Egg(c.shellRest + new Vector3(side * 0.085f, 0.11f, 0.15f), new Vector3(0.018f, 0.06f, 0.018f), 5, 4);
                kit.Paint(new Color(0.06f, 0.05f, 0.08f)).Egg(c.shellRest + new Vector3(side * 0.085f, 0.18f, 0.155f), Vector3.one * 0.034f, 6, 4);
            }
            for (int i = 0; i < 6; i++)
            {
                int side = i % 2 == 0 ? -1 : 1;
                var h = c.shellRest + c.hip[i];
                kit.Paint(red).On("cu" + i).Egg(h + new Vector3(side * Half * 0.5f, 0, 0), new Vector3(Half * 0.5f + 0.02f, 0.036f, 0.036f), 6, 4);
                kit.Paint(dark).On("cl" + i).Egg(h + new Vector3(side * Half * 1.5f, 0, 0), new Vector3(Half * 0.5f + 0.01f, 0.026f, 0.026f), 6, 4);
            }
            for (int i = 0; i < 2; i++)
            {
                int side = i == 0 ? -1 : 1;
                var armAt = c.shellRest + new Vector3(side * 0.17f, 0, 0.15f);
                var clawAt = armAt + new Vector3(side * 0.10f, 0.03f, 0.17f);
                if (scarab)
                {
                    kit.Paint(dark).On("arm" + i).Egg(Vector3.Lerp(armAt, clawAt, 0.5f), new Vector3(0.045f, 0.035f, 0.09f), 6, 4);
                    kit.Paint(pale, 1).On("claw" + i).Egg(clawAt + new Vector3(-side * 0.03f, 0, 0.05f), new Vector3(0.03f, 0.03f, 0.09f), 6, 4);
                    continue;
                }
                kit.Paint(red).On("arm" + i).Egg(Vector3.Lerp(armAt, clawAt, 0.5f), new Vector3(0.075f, 0.05f, 0.10f), 6, 4);
                kit.Paint(pale).On("claw" + i).Egg(clawAt + new Vector3(0, 0.01f, 0.09f), new Vector3(0.085f, 0.07f, 0.13f), 8, 5);
                kit.Paint(red).Egg(clawAt + new Vector3(side * 0.02f, 0.075f, 0.11f), new Vector3(0.05f, 0.03f, 0.11f), 6, 4);
            }
            kit.Wear("Shell");
            return c;
        }

        public void Pose(ModelActor a, string anim, float n, float dt)
        {
            time += dt;
            float scale = a.def.scale;
            Vector2 v = a.velocity / scale;
            float speed = v.magnitude;
            float yaw = a.yaw * Mathf.Deg2Rad;
            Vector2 ahead = new Vector2(Mathf.Sin(yaw), Mathf.Cos(yaw)), side = new Vector2(ahead.y, -ahead.x);
            Vector3 travel = speed > 0.03f ? new Vector3(Vector2.Dot(v, side), 0, Vector2.Dot(v, ahead)) / speed : Vector3.right;
            moving = Mathf.MoveTowards(moving, speed > 0.06f ? 1f : 0f, dt * 8f);
            const float stride = 0.30f, duty = 0.55f;
            phase += speed * dt / stride;

            bool attack = anim == "attack";
            float raise = attack ? Mathf.Sin(Mathf.Clamp01(n * 1.6f) * Mathf.PI * 0.5f) : 0.12f + Mathf.Sin(time * 1.7f) * 0.06f;
            float shut = attack ? Mathf.Clamp01((n - 0.55f) / 0.15f) : 0f;
            up = Mathf.Lerp(up, raise, 1f - Mathf.Exp(-22f * dt));
            snap = Mathf.Lerp(snap, shut, 1f - Mathf.Exp(-40f * dt));
            flinch = Mathf.Lerp(flinch, anim == "hurt" ? 1f : 0f, 1f - Mathf.Exp(-24f * dt));

            var sp = shellRest + new Vector3(0, Mathf.Sin(phase * Mathf.PI * 4f) * 0.012f * moving + up * 0.03f - flinch * 0.05f, 0);
            var sr = Quaternion.Euler(-up * 9f + flinch * 10f, 0, Mathf.Sin(phase * Mathf.PI * 2f) * 4f * moving);
            shell.localPosition = sp;
            shell.localRotation = sr;
            for (int i = 0; i < 6; i++)
            {
                var h = sp + sr * hip[i];
                var foot = rest[i];
                // alternate tripods: left fore, right middle, left hind move together
                float u = Mathf.Repeat(phase + ((i % 2 + i / 2) % 2 == 0 ? 0f : 0.5f), 1f);
                if (u < duty) foot += travel * ((0.5f - u / duty) * duty * stride * moving);
                else
                {
                    float w = (u - duty) / (1f - duty), e = w * w * (3f - 2f * w);
                    foot += travel * ((-0.5f + e) * duty * stride * moving);
                    foot.y += 0.07f * Mathf.Sin(w * Mathf.PI) * moving;
                }
                var d = foot - h;
                float len = Mathf.Clamp(d.magnitude, 0.02f, Half * 2f - 0.002f);
                var dir = d.normalized;
                float along = len * 0.5f, off = Mathf.Sqrt(Mathf.Max(0, Half * Half - along * along));
                var bend = Vector3.up - dir * Vector3.Dot(Vector3.up, dir);
                var knee = h + dir * along + bend.normalized * off;
                var outward = new Vector3(i % 2 == 0 ? -1 : 1, 0, 0);
                upper[i].localPosition = h;
                upper[i].localRotation = Quaternion.FromToRotation(outward, knee - h);
                lower[i].localPosition = knee;
                lower[i].localRotation = Quaternion.FromToRotation(outward, h + dir * len - knee);
            }
            for (int i = 0; i < 2; i++)
            {
                int s = i == 0 ? -1 : 1;
                arm[i].localRotation = Quaternion.Euler(-up * 62f, s * (-up * 14f + snap * 20f), 0);
                claw[i].localRotation = Quaternion.Euler(-up * 24f + snap * 34f, 0, 0);
            }
        }
    }

    // ----------------------------------------------------------------------------------- moth
    /// <summary>Moth-shade: a soft body between four pale wings that beat too fast to follow.</summary>
    public class MothBeast : IPoser
    {
        Transform body;
        readonly Transform[] wing = new Transform[4];
        float time;

        public static MothBeast Make(ModelActor a)
        {
            var m = new MothBeast();
            var rig = a.rig;
            var go = new GameObject("body");
            go.transform.SetParent(rig, false);
            go.transform.localPosition = new Vector3(0, 0.25f, 0);
            m.body = go.transform;
            var bones = new List<Transform> { m.body };
            for (int i = 0; i < 4; i++)
            {
                var w = new GameObject("wing" + i);
                w.transform.SetParent(m.body, false);
                w.transform.localPosition = new Vector3((i % 2 == 0 ? -1 : 1) * 0.03f, 0.02f, i < 2 ? 0.03f : -0.05f);
                m.wing[i] = w.transform;
                bones.Add(w.transform);
            }
            foreach (var t in bones) a.bones[t.name] = t;
            var kit = new Kit(a, rig, bones.ToArray());
            var at = new Vector3(0, 0.25f, 0);
            Color fur = new Color(0.36f, 0.30f, 0.62f), pale = new Color(0.72f, 0.70f, 0.98f), spot = new Color(0.98f, 0.92f, 0.62f);
            kit.On("body").Paint(fur).Egg(at, new Vector3(0.055f, 0.055f, 0.13f), 8, 5);
            kit.Paint(spot, 0, 1).Egg(at + new Vector3(0.03f, 0.03f, 0.11f), Vector3.one * 0.022f, 5, 3).Egg(at + new Vector3(-0.03f, 0.03f, 0.11f), Vector3.one * 0.022f, 5, 3);
            for (int i = 0; i < 4; i++)
            {
                int side = i % 2 == 0 ? -1 : 1;
                bool fore = i < 2;
                var root = at + new Vector3(side * 0.03f, 0.02f, fore ? 0.03f : -0.05f);
                float span = fore ? 0.26f : 0.19f;
                kit.On("wing" + i).Paint(pale).Egg(root + new Vector3(side * span * 0.55f, 0, fore ? 0.05f : -0.06f), new Vector3(span * 0.55f, 0.012f, fore ? 0.13f : 0.10f), 8, 3);
                kit.Paint(spot, 0, 1).Egg(root + new Vector3(side * span * 0.72f, 0.012f, fore ? 0.06f : -0.07f), new Vector3(0.04f, 0.008f, 0.04f), 5, 3);
            }
            kit.Wear("Moth");
            return m;
        }

        public void Pose(ModelActor a, string anim, float n, float dt)
        {
            time += dt;
            float beat = Mathf.Sin(time * 34f);
            body.localRotation = Quaternion.Euler(-18f + Mathf.Sin(time * 3f) * 6f, 0, Mathf.Sin(time * 2.2f) * 8f);
            for (int i = 0; i < 4; i++)
            {
                int side = i % 2 == 0 ? -1 : 1;
                wing[i].localRotation = Quaternion.Euler(0, 0, side * (18f + beat * (i < 2 ? 52f : 40f)));
            }
        }
    }
}
