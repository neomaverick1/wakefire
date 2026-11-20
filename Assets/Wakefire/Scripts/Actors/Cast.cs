// Who wears what. Each character is a rigged body painted and dressed by code: the body's own
// skin is painted where cloth lies close, and whatever shapes the outline (helmet and crest,
// breastplate, kilt, shoulder plates, greaves, blade, lantern, cape) is built onto it by the Kit.
// Measurements are taken from the body itself, so the same kit fits another build.
using UnityEngine;

namespace Wakefire
{
    public static class Cast
    {
        public class Look
        {
            public Color skin = new Color(0.78f, 0.52f, 0.36f);
            public Color tunic = new Color(0.91f, 0.87f, 0.76f);
            public Color tunicFold = new Color(0.78f, 0.72f, 0.62f);
            public Color trim = new Color(0.93f, 0.72f, 0.26f);
            public Color leather = new Color(0.36f, 0.20f, 0.12f);
            public Color bronze = new Color(0.80f, 0.54f, 0.20f);
            public Color blade = new Color(0.97f, 0.82f, 0.40f);
            public Color crest = new Color(0.86f, 0.13f, 0.12f);
            public Color cape = new Color(0.70f, 0.10f, 0.12f);
            public Color dark = new Color(0.07f, 0.05f, 0.07f);
            public Color eyes = new Color(1.0f, 0.93f, 0.78f);
            public Color flame = new Color(1.0f, 0.76f, 0.28f);
            public float crestHeight = 0.12f;
            public bool hasCape = true, hasBlade = true, hasLantern = true, plateSkin;
        }

        static float Table(float k, params float[] pairs)
        {
            for (int i = 0; i + 3 < pairs.Length; i += 2)
                if (k <= pairs[i + 2]) return Mathf.Lerp(pairs[i + 1], pairs[i + 3], Mathf.InverseLerp(pairs[i], pairs[i + 2], k));
            return pairs[pairs.Length - 1];
        }

        public static void Azar(ModelActor m) => Soldier(m, new Look());

        /// <summary>A man of the watch: crested bronze helm, linen breastplate and kilt, plates at shoulder, forearm and shin.</summary>
        public static void Soldier(ModelActor m, Look look)
        {
            var t = new Tailor(m);
            var kit = new Kit(t);
            Vector3 head = t.At("Head"), neck = t.At("neck_01"), pelvis = t.At("pelvis"), chest = t.At("spine_03");
            bool IsHead(string b) => b == "Head";
            bool IsTrunk(string b) => b == "pelvis" || b.StartsWith("spine") || b.StartsWith("thigh");
            bool IsSpine(string b) => b.StartsWith("spine");

            // ---- measurements: a plumb line through the body, so "along it" is simply height
            Vector3 plumb0 = new Vector3(0, 0, head.z), plumb1 = plumb0 + Vector3.up;
            float crown = t.Top(IsHead);
            float hh = (crown - head.y) * 0.5f, headMid = head.y + hh;
            float hw = t.Reach(plumb0, plumb1, headMid, hh, Vector3.right, IsHead);
            float hf = t.Reach(plumb0, plumb1, headMid, hh, Vector3.forward, IsHead);
            float hb = t.Reach(plumb0, plumb1, headMid, hh, Vector3.back, IsHead);
            var hc = new Vector3(0, headMid + 0.022f, head.z + (hf - hb) * 0.5f);
            var hr = new Vector3(hw + 0.042f, hh + 0.040f, (hf + hb) * 0.5f + 0.042f);

            Vector3 kneeAny = t.At("calf_l"), ankleAny = t.At("foot_l");
            float waistY = pelvis.y + 0.11f, hemY = kneeAny.y + 0.12f;
            Vector3 mid0 = new Vector3(0, 0, pelvis.z), mid1 = mid0 + Vector3.up;
            float wx = t.Reach(mid0, mid1, waistY, 0.04f, Vector3.right, IsTrunk);
            float wf = t.Reach(mid0, mid1, waistY, 0.04f, Vector3.forward, IsTrunk);
            float wb = t.Reach(mid0, mid1, waistY, 0.04f, Vector3.back, IsTrunk);
            float hipX = t.Reach(mid0, mid1, pelvis.y - 0.02f, 0.06f, Vector3.right, IsTrunk);
            var waist = new Vector3(0, 0, pelvis.z + (wf - wb) * 0.5f);
            float deep = ((wf + wb) * 0.5f + 0.02f) / (wx + 0.02f);
            float chestX = t.Reach(mid0, mid1, chest.y - 0.05f, 0.07f, Vector3.right, IsSpine);
            float chestFront = t.Reach(mid0, mid1, chest.y - 0.05f, 0.07f, Vector3.forward, IsSpine);
            float chestBack = t.Reach(mid0, mid1, chest.y - 0.02f, 0.09f, Vector3.back, IsSpine);
            var trunk = new Vector3(0, 0, pelvis.z + (chestFront - chestBack) * 0.5f);
            float deepChest = ((chestFront + chestBack) * 0.5f + 0.035f) / (chestX + 0.05f);
            float shoulderX = t.At("upperarm_r").x;

            // ---- the body's own paint (what shows between the pieces)
            var skin = look.plateSkin ? look.bronze : look.skin;
            float skinMetal = look.plateSkin ? 1f : 0f;
            t.Paint((p, bone) =>
            {
                if (bone.StartsWith("spine") || bone.StartsWith("clavicle") || bone == "pelvis") return (look.tunic, 0f);
                if (bone.StartsWith("thigh")) return p.y > hemY - 0.03f ? (look.tunic, 0f) : (skin, skinMetal);
                if (bone.StartsWith("foot") || bone.StartsWith("ball")) return (look.leather, 0f);
                return (skin, skinMetal);
            });

            // ---- helmet: a bronze bowl with a T cut for the eyes and mouth, darkness behind it, two eyes in the dark
            kit.Paint(look.bronze, 1).On("Head");
            kit.Egg(hc, hr, 16, 9, -44, 90, d => !(d.z > 0.2f && ((Mathf.Abs(d.x) < 0.2f && d.y < 0.25f) || (Mathf.Abs(d.x) < 0.7f && d.y > -0.12f && d.y < 0.22f))));
            var inner = hr - Vector3.one * 0.016f;
            kit.Paint(look.dark).Egg(hc, inner, 10, 6, -44, 50, null, -80, 80);
            kit.Paint(look.eyes, 0, 1);
            foreach (int s in new[] { -1, 1 })
            {
                var d = new Vector3(0.38f * s, 0.07f, 0.92f).normalized;
                var c = hc + Vector3.Scale(d, inner) + new Vector3(0, 0, 0.004f);
                kit.Face(c + new Vector3(-0.024f, -0.017f, 0), c + new Vector3(0.024f, -0.017f, 0), c + new Vector3(0.024f, 0.017f, 0), c + new Vector3(-0.024f, 0.017f, 0), Vector3.forward);
            }

            // ---- the crest: a fin from above the brow, over the crown, down to the nape
            if (look.crestHeight > 0)
            {
                const int n = 12;
                var foot = new Vector3[n + 1];
                var top = new Vector3[n + 1];
                for (int i = 0; i <= n; i++)
                {
                    float k = i / (float)n, phi = Mathf.Lerp(56f, 216f, k) * Mathf.Deg2Rad;
                    var d = new Vector3(0, Mathf.Sin(phi), Mathf.Cos(phi));
                    foot[i] = hc + Vector3.Scale(d, hr) * 0.96f;
                    var outward = new Vector3(0, d.y / hr.y, d.z / hr.z).normalized;
                    float h = look.crestHeight * Table(k, 0f, 0.45f, 0.10f, 0.95f, 0.35f, 1.0f, 0.70f, 0.80f, 1f, 0.55f);
                    top[i] = foot[i] + outward * h;
                }
                kit.Paint(look.crest).Fin(foot, top, 0.052f);
            }

            // ---- breastplate of stiffened linen: broad at the chest, drawn in at the waist, a strap across it
            int s1 = t.Index("spine_01"), s2 = t.Index("spine_02"), s3 = t.Index("spine_03");
            kit.On(p =>
            {
                float k = Mathf.InverseLerp(waistY, neck.y, p.y);
                return k < 0.4f
                    ? new BoneWeight { boneIndex0 = s1, weight0 = 1 - k / 0.4f, boneIndex1 = s2, weight1 = k / 0.4f }
                    : new BoneWeight { boneIndex0 = s2, weight0 = 1 - (k - 0.4f) / 0.6f, boneIndex1 = s3, weight1 = (k - 0.4f) / 0.6f };
            });
            Vector2 strapA = new Vector2(shoulderX * 0.8f, neck.y - 0.04f), strapB = new Vector2(-wx - 0.02f, waistY);
            Vector2 strapDir = (strapB - strapA).normalized;
            kit.Stain(p =>
            {
                var q = new Vector2(p.x, p.y) - strapA;
                return Mathf.Abs(q.x * strapDir.y - q.y * strapDir.x) < 0.034f ? look.leather : (Color?)null;
            });
            kit.Paint(look.tunic).Turned(trunk, new[]
            {
                (wx + 0.030f, waistY + 0.02f), (wx + 0.050f, waistY + 0.12f), (chestX + 0.050f, chest.y - 0.10f),
                (chestX + 0.062f, chest.y - 0.01f), (chestX + 0.036f, neck.y - 0.055f), (0.085f, neck.y - 0.012f),
            }, 16, deepChest);
            kit.Stain(null);
            kit.Paint(look.bronze, 1).On("spine_03").Egg(new Vector3(0.025f, chest.y - 0.045f, trunk.z + (chestX + 0.062f) * deepChest), new Vector3(0.078f, 0.078f, 0.03f), 10, 5);

            // ---- arms and legs: a fighter's build, plated at shoulder, forearm, knee and shin
            foreach (string side in new[] { "_l", "_r" })
            {
                Vector3 sh = t.At("upperarm" + side), el = t.At("lowerarm" + side), wr = t.At("hand" + side), fi = t.At("middle_01" + side);
                float s = Mathf.Sign(sh.x), upper = Mathf.Abs(el.x - sh.x), fore = Mathf.Abs(wr.x - el.x);
                kit.Paint(skin, skinMetal).On("upperarm" + side).Egg(Vector3.Lerp(sh, el, 0.48f), new Vector3(upper * 0.56f, 0.068f, 0.072f), 10, 6);
                kit.Paint(look.bronze, 1).On("clavicle" + side, "upperarm" + side, 0.5f).Egg(sh + new Vector3(s * 0.012f, 0.032f, 0), new Vector3(0.105f, 0.086f, 0.11f), 10, 5, -8, 90);
                kit.Paint(look.bronze, 1).On("lowerarm" + side).Egg(Vector3.Lerp(el, wr, 0.52f), new Vector3(fore * 0.45f, 0.064f, 0.066f), 10, 6);
                kit.Paint(skin, skinMetal).On("hand" + side).Egg(wr + (fi - wr).normalized * 0.075f, Vector3.one * 0.056f, 8, 5);

                Vector3 hip = t.At("thigh" + side), kn = t.At("calf" + side), an = t.At("foot" + side), ba = t.At("ball" + side);
                float thigh = hip.y - kn.y, shin = kn.y - an.y;
                kit.Paint(skin, skinMetal).On("thigh" + side).Egg(Vector3.Lerp(hip, kn, 0.5f), new Vector3(0.088f, thigh * 0.56f, 0.096f), 10, 6);
                kit.Paint(look.bronze, 1).On("calf" + side).Egg(Vector3.Lerp(kn, an, 0.45f) + new Vector3(0, 0, 0.006f), new Vector3(0.073f, shin * 0.53f, 0.084f), 10, 6);
                kit.Egg(kn + new Vector3(0, 0.005f, 0.045f), new Vector3(0.058f, 0.064f, 0.05f), 8, 5);
                kit.Paint(look.leather).On("foot" + side).Egg(Vector3.Lerp(an, ba, 0.6f) + new Vector3(0, -0.012f, 0.012f), new Vector3(0.06f, 0.05f, 0.135f), 8, 5);
            }

            // ---- kilt of linen strips: swings with the thighs, hemmed in gold
            int iPelvis = t.Index("pelvis"), iThighL = t.Index("thigh_l"), iThighR = t.Index("thigh_r");
            kit.On(p =>
            {
                float down = Mathf.InverseLerp(waistY, hemY, p.y);
                float side = Mathf.Clamp01((Mathf.Abs(p.x) - 0.015f) / 0.07f);
                float thigh = 0.8f * down * side;
                return new BoneWeight { boneIndex0 = iPelvis, weight0 = 1 - thigh, boneIndex1 = p.x > 0 ? iThighR : iThighL, weight1 = thigh };
            });
            float r0 = wx + 0.02f, r1 = Mathf.Max(hipX, wx) + 0.05f, r2 = r1 * 1.22f + 0.025f, r3 = r1 * 1.42f + 0.04f;
            float y1 = Mathf.Lerp(waistY, hemY, 0.3f), y2 = Mathf.Lerp(waistY, hemY, 0.68f);
            kit.Stain(p => Mathf.FloorToInt((Mathf.Atan2(p.x, p.z - waist.z) + Mathf.PI) / (Mathf.PI * 2f) * 16f + 0.5f) % 2 == 0 ? look.tunicFold : (Color?)null);
            kit.Paint(look.tunic).Turned(waist, new[] { (r0, waistY + 0.03f), (r1, y1), (r2, y2), (r3, hemY + 0.04f) }, 16, deep);
            kit.Stain(null);
            kit.Paint(look.trim).Turned(waist, new[] { (r3, hemY + 0.04f), (r3 + 0.014f, hemY) }, 16, deep);

            // ---- belt and buckle
            kit.Paint(look.leather).On("pelvis", "spine_01", 0.5f);
            kit.Turned(waist, new[] { (r0 + 0.02f, waistY - 0.035f), (r0 + 0.036f, waistY + 0.005f), (r0 + 0.02f, waistY + 0.045f) }, 16, deep);
            kit.Paint(look.bronze, 1).Egg(waist + new Vector3(0, waistY + 0.005f, (r0 + 0.036f) * deep), new Vector3(0.046f, 0.046f, 0.022f), 8, 4);

            // ---- the khopesh, in the right fist: blade out past the thumb, edge towards the knuckles
            if (look.hasBlade)
            {
                Grip(t, "_r", out var grip, out var fingers, out var across, out var palm);
                // carried the way a tired man carries a blade: tipped forward and down out of the fist, not held square
                const float tip = 28f * Mathf.Deg2Rad;
                Vector3 along = across * Mathf.Cos(tip) + fingers * Mathf.Sin(tip), edge = fingers * Mathf.Cos(tip) - across * Mathf.Sin(tip);
                across = along;
                fingers = edge;
                kit.On("hand_r").Frame(grip, across, fingers, palm);
                kit.Paint(look.leather).Ribbon(new[] { new Vector2(-0.12f, 0), new Vector2(0.03f, 0) }, new[] { 0.042f, 0.042f }, 0.042f);
                kit.Paint(look.bronze, 1).Box(new Vector3(-0.145f, 0, 0), new Vector3(0.055f, 0.066f, 0.06f));
                kit.Paint(look.blade, 1).Ribbon(
                    new[] { new Vector2(0.03f, 0), new Vector2(0.21f, 0), new Vector2(0.32f, 0.03f), new Vector2(0.43f, 0.09f), new Vector2(0.54f, 0.15f), new Vector2(0.65f, 0.178f), new Vector2(0.75f, 0.162f), new Vector2(0.82f, 0.118f) },
                    new[] { 0.07f, 0.07f, 0.085f, 0.105f, 0.11f, 0.10f, 0.078f, 0.04f }, 0.05f);
                kit.Frame();
                var handBone = m.Bone("hand_r");
                Vector3 Mark(Vector3 p) => handBone.InverseTransformPoint(t.rig.TransformPoint(t.FromTailor(p)));
                m.marks["blade0"] = (handBone, Mark(grip + across * 0.10f));
                m.marks["blade1"] = (handBone, Mark(grip + across * 0.84f + fingers * 0.13f));
                Trail.Make(m);
            }
            kit.Wear("Kit");

            // ---- the Wakefire, swinging from the left fist
            if (look.hasLantern)
            {
                Grip(t, "_l", out var grip, out _, out _, out _);
                var lk = new Kit();
                float s = m.def.scale;
                lk.Paint(look.bronze, 1).Box(new Vector3(0, -0.05f, 0) * s, new Vector3(0.024f, 0.10f, 0.024f) * s);
                lk.Turned(Vector3.zero, new[] { (0.0f, -0.085f * s), (0.085f * s, -0.13f * s) }, 8);
                lk.Paint(look.flame, 0, 1).Turned(Vector3.zero, new[] { (0.062f * s, -0.13f * s), (0.072f * s, -0.20f * s), (0.062f * s, -0.27f * s) }, 8);
                lk.Paint(look.bronze, 1).Turned(Vector3.zero, new[] { (0.085f * s, -0.27f * s), (0.065f * s, -0.305f * s), (0.0f, -0.305f * s) }, 8);
                var lantern = lk.Loose("Lantern", m.anchor);
                var dangle = lantern.gameObject.AddComponent<Dangle>();
                dangle.actor = m;
                dangle.hand = m.Bone("hand_l");
                dangle.grip = dangle.hand.InverseTransformPoint(t.rig.TransformPoint(t.FromTailor(grip)));
                dangle.length = 0.2f * s;
                m.props["lantern"] = lantern.transform;
            }

            // ---- the cape, pinned across the back of the shoulders
            if (look.hasCape)
            {
                float y = neck.y - 0.02f, z = trunk.z - (chestX + 0.05f) * deepChest - 0.02f;
                Cape.Make(m, t, look.cape, new Vector3(-shoulderX * 0.95f, y, z), new Vector3(shoulderX * 0.95f, y, z), 1.0f, 0.80f);
            }
        }

        /// <summary>Where a closed fist holds a handle: the middle of the grip, the direction the fingers
        /// reach, the direction across the knuckles (little finger to forefinger), and the palm's facing.</summary>
        static void Grip(Tailor t, string side, out Vector3 grip, out Vector3 fingers, out Vector3 across, out Vector3 palm)
        {
            Vector3 hand = t.At("hand" + side), mid = t.At("middle_01" + side), fore = t.At("index_01" + side), little = t.At("pinky_01" + side);
            fingers = (mid - hand).normalized;
            across = fore - little;
            across = (across - fingers * Vector3.Dot(across, fingers)).normalized;
            palm = Vector3.Cross(fingers, across).normalized;
            if (palm.y > 0) palm = -palm;                       // at rest the arms are out level, palms down
            grip = hand + fingers * 0.085f + palm * 0.035f;
        }
    }
}
