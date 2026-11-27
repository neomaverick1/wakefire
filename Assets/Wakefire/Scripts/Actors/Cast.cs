// Who wears what. Each character is a rigged body painted and dressed by code: the body's own
// skin is painted where cloth lies close, and whatever shapes the outline (helmets and crests,
// breastplates, kilts and robes, hats, hair and beards, blades, spears, shields, the lantern,
// capes) is built onto it by the Kit. Measurements come from the body itself.
using System;
using UnityEngine;

namespace Wakefire
{
    public static class Cast
    {
        /// <summary>The measure of a body: where its parts are at rest and how wide.</summary>
        public class Fit
        {
            public readonly Tailor t;
            public Vector3 head, neck, pelvis, chest, hc, hr, waist, trunk;
            public float crown, hw, hh, hf, hb, headMid, waistY, kneeY, ankleY, wx, hipX, deep, chestX, chestFront, chestBack, deepChest, shoulderX;

            public Fit(Tailor tailor)
            {
                t = tailor;
                head = t.At("Head"); neck = t.At("neck_01"); pelvis = t.At("pelvis"); chest = t.At("spine_03");
                bool IsHead(string b) => b == "Head";
                bool IsTrunk(string b) => b == "pelvis" || b.StartsWith("spine") || b.StartsWith("thigh");
                bool IsSpine(string b) => b.StartsWith("spine");
                // a plumb line through the body, so "along it" is simply height
                Vector3 plumb0 = new Vector3(0, 0, head.z), plumb1 = plumb0 + Vector3.up;
                crown = t.Top(IsHead);
                hh = (crown - head.y) * 0.5f;
                headMid = head.y + hh;
                hw = t.Reach(plumb0, plumb1, headMid, hh, Vector3.right, IsHead);
                hf = t.Reach(plumb0, plumb1, headMid, hh, Vector3.forward, IsHead);
                hb = t.Reach(plumb0, plumb1, headMid, hh, Vector3.back, IsHead);
                hc = new Vector3(0, headMid, head.z + (hf - hb) * 0.5f);
                hr = new Vector3(hw, hh, (hf + hb) * 0.5f);

                kneeY = t.At("calf_l").y;
                ankleY = t.At("foot_l").y;
                waistY = pelvis.y + 0.11f;
                Vector3 mid0 = new Vector3(0, 0, pelvis.z), mid1 = mid0 + Vector3.up;
                wx = t.Reach(mid0, mid1, waistY, 0.04f, Vector3.right, IsTrunk);
                float wf = t.Reach(mid0, mid1, waistY, 0.04f, Vector3.forward, IsTrunk);
                float wb = t.Reach(mid0, mid1, waistY, 0.04f, Vector3.back, IsTrunk);
                hipX = t.Reach(mid0, mid1, pelvis.y - 0.02f, 0.06f, Vector3.right, IsTrunk);
                waist = new Vector3(0, 0, pelvis.z + (wf - wb) * 0.5f);
                deep = ((wf + wb) * 0.5f + 0.02f) / (wx + 0.02f);
                chestX = t.Reach(mid0, mid1, chest.y - 0.05f, 0.07f, Vector3.right, IsSpine);
                chestFront = t.Reach(mid0, mid1, chest.y - 0.05f, 0.07f, Vector3.forward, IsSpine);
                chestBack = t.Reach(mid0, mid1, chest.y - 0.02f, 0.09f, Vector3.back, IsSpine);
                trunk = new Vector3(0, 0, pelvis.z + (chestFront - chestBack) * 0.5f);
                deepChest = ((chestFront + chestBack) * 0.5f + 0.035f) / (chestX + 0.05f);
                shoulderX = t.At("upperarm_r").x;
            }

            /// <summary>Carried by the spine, by whichever part of it is at that height.</summary>
            public Func<Vector3, BoneWeight> Spine()
            {
                int s1 = t.Index("spine_01"), s2 = t.Index("spine_02"), s3 = t.Index("spine_03");
                float lo = waistY, hi = neck.y;
                return p =>
                {
                    float k = Mathf.InverseLerp(lo, hi, p.y);
                    return k < 0.4f
                        ? new BoneWeight { boneIndex0 = s1, weight0 = 1 - k / 0.4f, boneIndex1 = s2, weight1 = k / 0.4f }
                        : new BoneWeight { boneIndex0 = s2, weight0 = 1 - (k - 0.4f) / 0.6f, boneIndex1 = s3, weight1 = (k - 0.4f) / 0.6f };
                };
            }

            /// <summary>Carried by the hips at the waist and more and more by the legs further down, so a
            /// skirt or robe swings with the stride.</summary>
            public Func<Vector3, BoneWeight> Skirt(float hemY)
            {
                int pel = t.Index("pelvis"), tl = t.Index("thigh_l"), tr = t.Index("thigh_r"), cl = t.Index("calf_l"), cr = t.Index("calf_r");
                float wy = waistY, ky = kneeY;
                return p =>
                {
                    float down = Mathf.Clamp01(Mathf.InverseLerp(wy, Mathf.Max(ky, hemY), p.y));
                    float side = Mathf.Clamp01((Mathf.Abs(p.x) - 0.015f) / 0.07f);
                    float leg = 0.8f * down * side;
                    float below = p.y < ky && hemY < ky ? Mathf.Clamp01(Mathf.InverseLerp(ky, hemY, p.y)) * 0.85f : 0f;
                    bool right = p.x > 0;
                    return new BoneWeight
                    {
                        boneIndex0 = pel, weight0 = 1 - leg,
                        boneIndex1 = right ? tr : tl, weight1 = leg * (1 - below),
                        boneIndex2 = right ? cr : cl, weight2 = leg * below,
                    };
                };
            }
        }

        static float Table(float k, params float[] pairs)
        {
            for (int i = 0; i + 3 < pairs.Length; i += 2)
                if (k <= pairs[i + 2]) return Mathf.Lerp(pairs[i + 1], pairs[i + 3], Mathf.InverseLerp(pairs[i], pairs[i + 2], k));
            return pairs[pairs.Length - 1];
        }

        static readonly Color Dark = new Color(0.07f, 0.05f, 0.07f);

        // ============================================================================ soldiers
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
            public Color eyes = new Color(1.0f, 0.93f, 0.78f);
            public Color flame = new Color(1.0f, 0.76f, 0.28f);
            public Color shield = new Color(0.80f, 0.54f, 0.20f);
            public float crestHeight = 0.12f;
            public bool hasCape = true, hasBlade = true, hasLantern = true, hasSpear, hasShield, plateSkin;
            public bool horns, goad;             // a bull's horns on the helm; a hook under the spear's head
            public float shieldWide = 1f, shieldTall = 1f;   // a warden's is the size of a door
            public float metal = 1f;             // how bright the plate is: 1 polished bronze, 0 fired clay
        }

        public static void Azar(ModelActor m) => Soldier(m, new Look());

        public static void Dur(ModelActor m) => Soldier(m, new Look
        {
            tunic = new Color(0.36f, 0.56f, 0.36f), tunicFold = new Color(0.27f, 0.45f, 0.29f), crest = new Color(0.10f, 0.09f, 0.12f),
            cape = new Color(0.16f, 0.24f, 0.20f), hasBlade = false, hasLantern = false, hasSpear = true, hasShield = true,
            shield = new Color(0.30f, 0.48f, 0.32f),
        });

        public static void Sentinel(ModelActor m) => Soldier(m, new Look
        {
            plateSkin = true, tunic = new Color(0.62f, 0.40f, 0.16f), tunicFold = new Color(0.50f, 0.31f, 0.12f), trim = new Color(0.88f, 0.64f, 0.24f),
            leather = new Color(0.42f, 0.26f, 0.10f), crest = new Color(0.66f, 0.42f, 0.14f), eyes = new Color(1.0f, 0.62f, 0.16f),
            hasCape = false, hasBlade = false, hasLantern = false, hasSpear = true, hasShield = true,
        });

        /// <summary>The Bronze Herdsman: the sentinels' bronze gone dark, a helm horned like the herd he keeps, and the goad.</summary>
        public static void Herdsman(ModelActor m) => Soldier(m, new Look
        {
            plateSkin = true, bronze = new Color(0.62f, 0.40f, 0.17f), tunic = new Color(0.46f, 0.28f, 0.12f), tunicFold = new Color(0.36f, 0.21f, 0.09f),
            trim = new Color(0.93f, 0.72f, 0.26f), leather = new Color(0.30f, 0.18f, 0.08f), crestHeight = 0f, eyes = new Color(1.0f, 0.52f, 0.12f),
            blade = new Color(0.95f, 0.78f, 0.36f), hasCape = false, hasBlade = false, hasLantern = false, hasSpear = true, hasShield = false, horns = true, goad = true,
        });

        /// <summary>A man of the watch: crested bronze helm, linen breastplate and kilt, plates at shoulder, forearm and shin.</summary>
        public static void Soldier(ModelActor m, Look look)
        {
            var t = new Tailor(m);
            var f = new Fit(t);
            var kit = new Kit(t);
            float hemY = f.kneeY + 0.12f;
            var hc = f.hc + new Vector3(0, 0.022f, 0);
            var hr = f.hr + new Vector3(0.042f, 0.040f, 0.042f);

            // ---- the body's own paint (what shows between the pieces)
            var skin = look.plateSkin ? look.bronze : look.skin;
            float skinMetal = look.plateSkin ? look.metal : 0f;
            t.Paint((p, bone) =>
            {
                if (bone.StartsWith("spine") || bone.StartsWith("clavicle") || bone == "pelvis") return (look.tunic, 0f);
                if (bone.StartsWith("thigh")) return p.y > hemY - 0.03f ? (look.tunic, 0f) : (skin, skinMetal);
                if (bone.StartsWith("foot") || bone.StartsWith("ball")) return (look.leather, 0f);
                return (skin, skinMetal);
            });

            // ---- helmet: a bronze bowl with a T cut for the eyes and mouth, darkness behind it, two eyes in the dark
            kit.Paint(look.bronze, look.metal).On("Head");
            kit.Egg(hc, hr, 16, 9, -44, 90, d => !(d.z > 0.2f && ((Mathf.Abs(d.x) < 0.2f && d.y < 0.25f) || (Mathf.Abs(d.x) < 0.7f && d.y > -0.12f && d.y < 0.22f))));
            var inner = hr - Vector3.one * 0.016f;
            kit.Paint(Dark).Egg(hc, inner, 10, 6, -44, 50, null, -80, 80);
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
            // ---- or horns: out from the temples and up, a hand longer than a bull's
            if (look.horns)
                foreach (int s in new[] { -1, 1 })
                    kit.Paint(look.trim, 1).Tube(new[]
                    {
                        new Vector3(s * (hr.x - 0.01f), hc.y + 0.05f, hc.z), new Vector3(s * (hr.x + 0.13f), hc.y + 0.09f, hc.z + 0.01f),
                        new Vector3(s * (hr.x + 0.20f), hc.y + 0.20f, hc.z + 0.02f), new Vector3(s * (hr.x + 0.17f), hc.y + 0.33f, hc.z + 0.03f),
                    }, new[] { 0.044f, 0.038f, 0.026f, 0.006f }, 6);

            // ---- breastplate of stiffened linen: broad at the chest, drawn in at the waist, a strap across it
            kit.On(f.Spine());
            Vector2 strapA = new Vector2(f.shoulderX * 0.8f, f.neck.y - 0.04f), strapB = new Vector2(-f.wx - 0.02f, f.waistY);
            Vector2 strapDir = (strapB - strapA).normalized;
            kit.Stain(p =>
            {
                var q = new Vector2(p.x, p.y) - strapA;
                return Mathf.Abs(q.x * strapDir.y - q.y * strapDir.x) < 0.034f ? look.leather : (Color?)null;
            });
            kit.Paint(look.tunic, look.plateSkin ? look.metal : 0).Turned(f.trunk, new[]
            {
                (f.wx + 0.030f, f.waistY + 0.02f), (f.wx + 0.050f, f.waistY + 0.12f), (f.chestX + 0.050f, f.chest.y - 0.10f),
                (f.chestX + 0.062f, f.chest.y - 0.01f), (f.chestX + 0.036f, f.neck.y - 0.055f), (0.085f, f.neck.y - 0.012f),
            }, 16, f.deepChest);
            kit.Stain(null);
            kit.Paint(look.bronze, look.metal).On("spine_03").Egg(new Vector3(0.025f, f.chest.y - 0.045f, f.trunk.z + (f.chestX + 0.062f) * f.deepChest), new Vector3(0.078f, 0.078f, 0.03f), 10, 5);

            Limbs(kit, t, skin, skinMetal, look.bronze, look.leather, true, null, 1f, look.metal);

            // ---- kilt of linen strips: swings with the thighs, hemmed in gold
            kit.On(f.Skirt(hemY));
            float r0 = f.wx + 0.02f, r1 = Mathf.Max(f.hipX, f.wx) + 0.05f, r2 = r1 * 1.22f + 0.025f, r3 = r1 * 1.42f + 0.04f;
            float y1 = Mathf.Lerp(f.waistY, hemY, 0.3f), y2 = Mathf.Lerp(f.waistY, hemY, 0.68f);
            var waist = f.waist;
            kit.Stain(p => Mathf.FloorToInt((Mathf.Atan2(p.x, p.z - waist.z) + Mathf.PI) / (Mathf.PI * 2f) * 16f + 0.5f) % 2 == 0 ? look.tunicFold : (Color?)null);
            kit.Paint(look.tunic, look.plateSkin ? look.metal : 0).Turned(waist, new[] { (r0, f.waistY + 0.03f), (r1, y1), (r2, y2), (r3, hemY + 0.04f) }, 16, f.deep);
            kit.Stain(null);
            kit.Paint(look.trim, look.plateSkin ? look.metal : 0).Turned(waist, new[] { (r3, hemY + 0.04f), (r3 + 0.014f, hemY) }, 16, f.deep);

            // ---- belt and buckle
            kit.Paint(look.leather).On("pelvis", "spine_01", 0.5f);
            kit.Turned(waist, new[] { (r0 + 0.02f, f.waistY - 0.035f), (r0 + 0.036f, f.waistY + 0.005f), (r0 + 0.02f, f.waistY + 0.045f) }, 16, f.deep);
            kit.Paint(look.bronze, look.metal).Egg(waist + new Vector3(0, f.waistY + 0.005f, (r0 + 0.036f) * f.deep), new Vector3(0.046f, 0.046f, 0.022f), 8, 4);

            // ---- the khopesh, in the right fist: blade out past the thumb, edge towards the knuckles
            Grip(t, "_r", out var grip, out var fingers, out var across, out var palm);
            if (look.hasBlade)
            {
                // carried the way a tired man carries a blade: tipped forward and down out of the fist, not held square
                const float tip = 28f * Mathf.Deg2Rad;
                Vector3 along = across * Mathf.Cos(tip) + fingers * Mathf.Sin(tip), edge = fingers * Mathf.Cos(tip) - across * Mathf.Sin(tip);
                var bk = new Kit(t);
                bk.On("hand_r").Frame(grip, along, edge, palm);
                bk.Paint(look.leather).Ribbon(new[] { new Vector2(-0.12f, 0), new Vector2(0.03f, 0) }, new[] { 0.042f, 0.042f }, 0.042f);
                bk.Paint(look.bronze, look.metal).Box(new Vector3(-0.145f, 0, 0), new Vector3(0.055f, 0.066f, 0.06f));
                bk.Paint(look.blade, 1).Ribbon(
                    new[] { new Vector2(0.03f, 0), new Vector2(0.21f, 0), new Vector2(0.32f, 0.03f), new Vector2(0.43f, 0.09f), new Vector2(0.54f, 0.15f), new Vector2(0.65f, 0.178f), new Vector2(0.75f, 0.162f), new Vector2(0.82f, 0.118f) },
                    new[] { 0.07f, 0.07f, 0.085f, 0.105f, 0.11f, 0.10f, 0.078f, 0.04f }, 0.05f);
                bk.Frame();
                m.props["blade"] = bk.Wear("Blade").transform;
                var handBone = m.Bone("hand_r");
                Vector3 Mark(Vector3 p) => handBone.InverseTransformPoint(t.rig.TransformPoint(t.FromTailor(p)));
                m.marks["blade0"] = (handBone, Mark(grip + along * 0.10f));
                m.marks["blade1"] = (handBone, Mark(grip + along * 0.84f + edge * 0.13f));
                Trail.Make(m);
            }
            // ---- or a spear, held along the arm: upright at a guard's side, levelled when the arm comes up
            if (look.hasSpear)
            {
                kit.On("hand_r").Frame(grip, across, fingers, palm);
                kit.Paint(look.leather).Ribbon(new[] { new Vector2(0, -1.02f), new Vector2(0, 0.78f) }, new[] { 0.04f, 0.04f }, 0.04f);
                kit.Paint(look.blade, 1).Ribbon(new[] { new Vector2(0, -1.02f), new Vector2(0, -1.10f), new Vector2(0, -1.22f), new Vector2(0, -1.34f) }, new[] { 0.05f, 0.11f, 0.08f, 0.012f }, 0.035f);
                // an ox-goad has a hook under the point, for turning a bull's head
                if (look.goad)
                    kit.Paint(look.blade, 1).Ribbon(new[] { new Vector2(0.01f, -1.04f), new Vector2(0.10f, -1.09f), new Vector2(0.15f, -1.00f), new Vector2(0.11f, -0.92f) }, new[] { 0.045f, 0.045f, 0.035f, 0.008f }, 0.03f);
                kit.Frame();
            }
            kit.Wear("Kit");

            // ---- a round shield on the left forearm (Azar carries his once he has won it)
            if (look.hasShield || look.hasLantern)
            {
                Vector3 el = t.At("lowerarm_l"), wr = t.At("hand_l");
                var sk = new Kit(t);
                var c = Vector3.Lerp(el, wr, 0.55f) + new Vector3(0, 0.075f, 0);
                bool mirror = !look.hasShield;                    // Azar's is the Bronze Mirror: bright as a lamp
                var face = mirror ? new Color(0.98f, 0.90f, 0.62f) : look.shield;
                sk.On("lowerarm_l");
                float sw = look.shieldWide, st = look.shieldTall;
                sk.Stain(p => (new Vector2((p.x - c.x) / sw, (p.z - c.z) / st)).magnitude > 0.25f ? look.bronze : (Color?)null);
                sk.Paint(face, mirror ? 1 : look.metal).Egg(c, new Vector3(0.31f * sw, 0.06f, 0.31f * st), 14, 5, 0, 90);
                sk.Stain(null);
                sk.Paint(look.bronze, look.metal).Egg(c + new Vector3(0, 0.05f, 0), new Vector3(0.07f, 0.04f, 0.07f), 8, 4, 0, 90);
                sk.Paint(look.leather).Egg(c, new Vector3(0.30f * sw, 0.02f, 0.30f * st), 12, 3, -90, 0);
                var shield = sk.Wear("Shield");
                m.props["shield"] = shield.transform;
                if (mirror) shield.gameObject.SetActive(false);
            }

            // ---- the Wakefire, swinging from the left fist
            if (look.hasLantern)
            {
                Grip(t, "_l", out var lgrip, out _, out _, out _);
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
                dangle.grip = dangle.hand.InverseTransformPoint(t.rig.TransformPoint(t.FromTailor(lgrip)));
                dangle.length = 0.2f * s;
                m.props["lantern"] = lantern.transform;
            }

            // ---- the cape, pinned across the back of the shoulders
            if (look.hasCape)
            {
                float y = f.neck.y - 0.02f, z = f.trunk.z - (f.chestX + 0.05f) * f.deepChest - 0.02f;
                Cape.Make(m, t, look.cape, new Vector3(-f.shoulderX * 0.95f, y, z), new Vector3(f.shoulderX * 0.95f, y, z), 1.0f, 0.80f);
            }
        }

        /// <summary>Arms and legs with some meat on them: upper arms, fists, thighs; plated (or sleeved) at
        /// shoulder, forearm, knee and shin when armoured.</summary>
        static void Limbs(Kit kit, Tailor t, Color skin, float skinMetal, Color plate, Color shoe, bool armoured, Color? sleeve = null, float build = 1f, float plateMetal = 1f)
        {
            foreach (string side in new[] { "_l", "_r" })
            {
                Vector3 sh = t.At("upperarm" + side), el = t.At("lowerarm" + side), wr = t.At("hand" + side), fi = t.At("middle_01" + side);
                float s = Mathf.Sign(sh.x), upper = Mathf.Abs(el.x - sh.x), fore = Mathf.Abs(wr.x - el.x);
                if (sleeve.HasValue) kit.Paint(sleeve.Value); else kit.Paint(skin, skinMetal);
                kit.On("upperarm" + side).Egg(Vector3.Lerp(sh, el, 0.48f), new Vector3(upper * 0.56f, 0.068f * build, 0.072f * build), 10, 6);
                if (armoured)
                {
                    kit.Paint(plate, plateMetal).On("clavicle" + side, "upperarm" + side, 0.5f).Egg(sh + new Vector3(s * 0.012f, 0.032f, 0), new Vector3(0.105f, 0.086f, 0.11f), 10, 5, -8, 90);
                    kit.Paint(plate, plateMetal).On("lowerarm" + side).Egg(Vector3.Lerp(el, wr, 0.52f), new Vector3(fore * 0.45f, 0.064f, 0.066f), 10, 6);
                }
                else kit.Paint(skin, skinMetal).On("lowerarm" + side).Egg(Vector3.Lerp(el, wr, 0.5f), new Vector3(fore * 0.52f, 0.054f * build, 0.056f * build), 8, 5);
                kit.Paint(skin, skinMetal).On("hand" + side).Egg(wr + (fi - wr).normalized * 0.075f, Vector3.one * 0.056f, 8, 5);

                Vector3 hip = t.At("thigh" + side), kn = t.At("calf" + side), an = t.At("foot" + side), ba = t.At("ball" + side);
                float thigh = hip.y - kn.y, shin = kn.y - an.y;
                kit.Paint(skin, skinMetal).On("thigh" + side).Egg(Vector3.Lerp(hip, kn, 0.5f), new Vector3(0.088f * build, thigh * 0.56f, 0.096f * build), 10, 6);
                if (armoured)
                {
                    kit.Paint(plate, plateMetal).On("calf" + side).Egg(Vector3.Lerp(kn, an, 0.45f) + new Vector3(0, 0, 0.006f), new Vector3(0.073f, shin * 0.53f, 0.084f), 10, 6);
                    kit.Egg(kn + new Vector3(0, 0.005f, 0.045f), new Vector3(0.058f, 0.064f, 0.05f), 8, 5);
                }
                else kit.Paint(skin, skinMetal).On("calf" + side).Egg(Vector3.Lerp(kn, an, 0.42f), new Vector3(0.064f * build, shin * 0.52f, 0.072f * build), 8, 5);
                kit.Paint(shoe).On("foot" + side).Egg(Vector3.Lerp(an, ba, 0.6f) + new Vector3(0, -0.012f, 0.012f), new Vector3(0.06f, 0.05f, 0.135f), 8, 5);
            }
        }

        // ============================================================================ townsfolk
        public class Folk
        {
            public Color skin = new Color(0.80f, 0.56f, 0.40f);
            public Color hair = new Color(0.20f, 0.13f, 0.09f);
            public Color tunic = new Color(0.78f, 0.42f, 0.24f);
            public Color fold = new Color(0.62f, 0.31f, 0.17f);
            public Color sash = new Color(0.36f, 0.20f, 0.12f);
            public Color hat = new Color(0.86f, 0.80f, 0.62f);
            public Color shoe = new Color(0.36f, 0.20f, 0.12f);
            public float hem = 0.45f;            // how far the robe comes down between knee (0) and ankle (1); negative is above the knee
            public string top;                   // scarf, bald, veil, strawhat, tallcap, headband, curls, kidhelm, crown
            public bool beard, longBeard, longHair, apron, sleeves = true, gold;
            public Color beardColour = new Color(0.20f, 0.13f, 0.09f);
            public float headScale = 1.1f, build = 1f;      // heads a touch large, so a face reads at this size
        }

        static readonly Color Warm = new Color(0.82f, 0.58f, 0.42f), Tan = new Color(0.72f, 0.48f, 0.32f), Deep = new Color(0.50f, 0.32f, 0.22f);

        public static readonly System.Collections.Generic.Dictionary<string, Folk> People = new System.Collections.Generic.Dictionary<string, Folk>
        {
            { "baker", new Folk { skin = Warm, hair = new Color(0.78f, 0.72f, 0.56f), tunic = new Color(0.85f, 0.48f, 0.28f), fold = new Color(0.69f, 0.35f, 0.18f), top = "scarf", hat = new Color(0.94f, 0.90f, 0.78f), apron = true, longHair = true, build = 1.18f, hem = 0.7f } },
            { "potter", new Folk { skin = Tan, hair = new Color(0.60f, 0.59f, 0.64f), tunic = new Color(0.50f, 0.58f, 0.44f), fold = new Color(0.39f, 0.47f, 0.34f), top = "bald", beard = true, beardColour = new Color(0.66f, 0.65f, 0.70f), hem = 0.1f } },
            { "oracle", new Folk { skin = Warm, hair = new Color(0.43f, 0.27f, 0.66f), tunic = new Color(0.54f, 0.35f, 0.78f), fold = new Color(0.42f, 0.24f, 0.65f), top = "veil", hat = new Color(0.66f, 0.47f, 0.86f), sash = new Color(0.93f, 0.72f, 0.26f), longHair = true, hem = 0.9f } },
            { "fisher", new Folk { skin = Deep, hair = new Color(0.18f, 0.13f, 0.11f), tunic = new Color(0.42f, 0.54f, 0.69f), fold = new Color(0.29f, 0.42f, 0.56f), top = "strawhat", hat = new Color(0.88f, 0.76f, 0.42f), beard = true, hem = -0.3f, sleeves = false } },
            { "priest", new Folk { skin = Warm, hair = new Color(0.86f, 0.84f, 0.90f), tunic = new Color(0.95f, 0.93f, 0.88f), fold = new Color(0.82f, 0.78f, 0.70f), top = "tallcap", hat = new Color(0.95f, 0.93f, 0.88f), beard = true, longBeard = true, beardColour = new Color(0.90f, 0.88f, 0.94f), sash = new Color(0.93f, 0.72f, 0.26f), gold = true, hem = 0.95f } },
            { "sleeper_a", new Folk { skin = Tan, hair = new Color(0.14f, 0.09f, 0.06f), tunic = new Color(0.85f, 0.35f, 0.23f), fold = new Color(0.69f, 0.24f, 0.15f), top = "headband", hat = new Color(0.93f, 0.72f, 0.26f), hem = 0.0f } },
            { "sleeper_b", new Folk { skin = Warm, hair = new Color(0.29f, 0.20f, 0.12f), tunic = new Color(0.48f, 0.60f, 0.35f), fold = new Color(0.35f, 0.48f, 0.25f), beard = true, beardColour = new Color(0.29f, 0.20f, 0.12f), hem = 0.3f, build = 1.12f } },
            { "sleeper_c", new Folk { skin = Deep, hair = new Color(0.10f, 0.06f, 0.05f), tunic = new Color(0.29f, 0.63f, 0.63f), fold = new Color(0.18f, 0.49f, 0.50f), top = "curls", hem = -0.2f } },
            { "captain_child", new Folk { skin = Warm, hair = new Color(0.23f, 0.14f, 0.09f), tunic = new Color(0.78f, 0.25f, 0.25f), fold = new Color(0.63f, 0.16f, 0.18f), top = "kidhelm", hem = -0.5f, headScale = 1.34f } },
            // ---- the Hill of Sleepers: the dead (drawn pale and thin by their material), and three living thieves
            { "namtar", new Folk { skin = Tan, hair = new Color(0.62f, 0.62f, 0.66f), tunic = new Color(0.84f, 0.84f, 0.78f), fold = new Color(0.68f, 0.68f, 0.62f), top = "bald", beard = true, beardColour = new Color(0.70f, 0.70f, 0.74f), sash = new Color(0.20f, 0.24f, 0.44f), hem = 0.95f } },
            { "gran", new Folk { skin = Warm, hair = new Color(0.92f, 0.92f, 0.94f), tunic = new Color(0.56f, 0.26f, 0.24f), fold = new Color(0.42f, 0.18f, 0.18f), top = "scarf", hat = new Color(0.92f, 0.90f, 0.84f), longHair = true, sash = new Color(0.93f, 0.72f, 0.26f), hem = 0.92f, build = 0.94f, headScale = 1.14f } },
            { "belu", new Folk { skin = Deep, hair = new Color(0.88f, 0.87f, 0.90f), tunic = new Color(0.80f, 0.62f, 0.30f), fold = new Color(0.64f, 0.48f, 0.22f), top = "headband", hat = new Color(0.60f, 0.24f, 0.44f), beard = true, longBeard = true, beardColour = new Color(0.90f, 0.89f, 0.92f), hem = 0.35f } },
            { "poet", new Folk { skin = Warm, hair = new Color(0.16f, 0.12f, 0.14f), tunic = new Color(0.70f, 0.62f, 0.86f), fold = new Color(0.54f, 0.46f, 0.72f), top = "curls", longHair = true, sash = new Color(0.93f, 0.72f, 0.26f), hem = 0.6f, build = 0.92f } },
            { "herald", new Folk { skin = Tan, hair = new Color(0.14f, 0.10f, 0.10f), tunic = new Color(0.22f, 0.30f, 0.66f), fold = new Color(0.16f, 0.22f, 0.52f), top = "tallcap", hat = new Color(0.22f, 0.30f, 0.66f), beard = true, longBeard = true, beardColour = new Color(0.14f, 0.10f, 0.10f), sash = new Color(0.93f, 0.72f, 0.26f), gold = true, hem = 0.95f } },
            { "servant", new Folk { skin = Tan, hair = new Color(0.14f, 0.10f, 0.10f), tunic = new Color(0.90f, 0.87f, 0.78f), fold = new Color(0.74f, 0.70f, 0.60f), top = "bald", sash = new Color(0.62f, 0.14f, 0.14f), hem = -0.15f, sleeves = false } },
            // ---- the dead at home
            { "t_sweeper", new Folk { skin = Warm, hair = new Color(0.34f, 0.24f, 0.20f), tunic = new Color(0.62f, 0.72f, 0.80f), fold = new Color(0.48f, 0.58f, 0.68f), top = "scarf", hat = new Color(0.96f, 0.95f, 0.92f), apron = true, longHair = true, hem = 0.8f } },
            { "t_shepherd", new Folk { skin = Deep, hair = new Color(0.72f, 0.70f, 0.68f), tunic = new Color(0.82f, 0.76f, 0.60f), fold = new Color(0.66f, 0.60f, 0.46f), top = "headband", hat = new Color(0.40f, 0.50f, 0.30f), beard = true, beardColour = new Color(0.76f, 0.74f, 0.72f), hem = 0.1f, sleeves = false } },
            { "t_proud", new Folk { skin = Tan, hair = new Color(0.12f, 0.09f, 0.10f), tunic = new Color(0.62f, 0.16f, 0.18f), fold = new Color(0.46f, 0.10f, 0.14f), top = "tallcap", hat = new Color(0.93f, 0.72f, 0.26f), beard = true, longBeard = true, beardColour = new Color(0.12f, 0.09f, 0.10f), sash = new Color(0.93f, 0.72f, 0.26f), gold = true, hem = 0.95f, build = 1.05f } },
            { "t_wife", new Folk { skin = Warm, hair = new Color(0.80f, 0.78f, 0.80f), tunic = new Color(0.78f, 0.44f, 0.52f), fold = new Color(0.62f, 0.32f, 0.40f), top = "veil", hat = new Color(0.90f, 0.66f, 0.70f), longHair = true, sash = new Color(0.93f, 0.72f, 0.26f), hem = 0.92f, build = 0.96f } },
            { "t_husband", new Folk { skin = Tan, hair = new Color(0.70f, 0.69f, 0.72f), tunic = new Color(0.56f, 0.56f, 0.36f), fold = new Color(0.44f, 0.44f, 0.26f), top = "bald", beard = true, beardColour = new Color(0.74f, 0.73f, 0.76f), hem = 0.5f, build = 1.15f } },
            { "t_rich", new Folk { skin = Warm, hair = new Color(0.14f, 0.10f, 0.12f), tunic = new Color(0.50f, 0.22f, 0.56f), fold = new Color(0.38f, 0.14f, 0.44f), top = "tallcap", hat = new Color(0.93f, 0.72f, 0.26f), beard = true, longBeard = true, beardColour = new Color(0.14f, 0.10f, 0.12f), sash = new Color(0.93f, 0.72f, 0.26f), gold = true, hem = 0.97f, build = 1.3f } },
            { "t_knocker", new Folk { skin = Tan, hair = new Color(0.22f, 0.15f, 0.10f), tunic = new Color(0.82f, 0.62f, 0.26f), fold = new Color(0.66f, 0.48f, 0.18f), top = "curls", hem = 0.2f, build = 0.95f } },
            { "t_scribe", new Folk { skin = Warm, hair = new Color(0.60f, 0.59f, 0.62f), tunic = new Color(0.92f, 0.90f, 0.82f), fold = new Color(0.76f, 0.74f, 0.66f), top = "bald", beard = true, beardColour = new Color(0.64f, 0.63f, 0.66f), sash = new Color(0.22f, 0.30f, 0.66f), hem = 0.9f, build = 0.9f } },
            { "t_listener", new Folk { skin = Warm, hair = new Color(0.92f, 0.92f, 0.94f), tunic = new Color(0.26f, 0.42f, 0.34f), fold = new Color(0.18f, 0.32f, 0.26f), top = "scarf", hat = new Color(0.80f, 0.84f, 0.78f), longHair = true, hem = 0.92f, build = 0.94f, headScale = 1.14f } },
            { "t_watchman", new Folk { skin = Deep, hair = new Color(0.74f, 0.73f, 0.74f), tunic = new Color(0.70f, 0.26f, 0.22f), fold = new Color(0.54f, 0.18f, 0.16f), top = "headband", hat = new Color(0.86f, 0.66f, 0.24f), beard = true, beardColour = new Color(0.78f, 0.77f, 0.78f), hem = 0.0f, sleeves = false, build = 1.12f } },
            { "robber", new Folk { skin = Tan, hair = new Color(0.12f, 0.09f, 0.08f), tunic = new Color(0.30f, 0.27f, 0.30f), fold = new Color(0.21f, 0.19f, 0.22f), top = "scarf", hat = new Color(0.22f, 0.20f, 0.24f), beard = true, beardColour = new Color(0.12f, 0.09f, 0.08f), sash = new Color(0.58f, 0.46f, 0.28f), hem = -0.1f } },
            { "robber_b", new Folk { skin = Deep, hair = new Color(0.10f, 0.07f, 0.06f), tunic = new Color(0.36f, 0.30f, 0.22f), fold = new Color(0.26f, 0.21f, 0.15f), top = "headband", hat = new Color(0.60f, 0.16f, 0.14f), sash = new Color(0.58f, 0.46f, 0.28f), hem = -0.25f, sleeves = false, build = 1.2f } },
            { "shade", new Folk { skin = new Color(0.50f, 0.58f, 0.62f), hair = new Color(0.20f, 0.24f, 0.30f), tunic = new Color(0.26f, 0.32f, 0.40f), fold = new Color(0.18f, 0.22f, 0.30f), top = "veil", hat = new Color(0.22f, 0.27f, 0.36f), sash = new Color(0.14f, 0.17f, 0.24f), longHair = true, hem = 1.0f, build = 0.9f } },
            { "king", new Folk { skin = Tan, hair = new Color(0.10f, 0.08f, 0.10f), tunic = new Color(0.50f, 0.12f, 0.20f), fold = new Color(0.86f, 0.66f, 0.24f), top = "bald", beard = true, longBeard = true, beardColour = new Color(0.10f, 0.08f, 0.10f), sash = new Color(0.93f, 0.72f, 0.26f), gold = true, hem = 0.97f, longHair = true, build = 1.22f, headScale = 1.06f } },
            { "god", new Folk { skin = new Color(0.86f, 0.72f, 0.44f), hair = new Color(0.93f, 0.92f, 0.98f), tunic = new Color(0.93f, 0.91f, 0.98f), fold = new Color(0.74f, 0.74f, 0.90f), top = "crown", hat = new Color(0.98f, 0.82f, 0.34f), beard = true, longBeard = true, beardColour = new Color(0.95f, 0.94f, 1.0f), sash = new Color(0.98f, 0.82f, 0.34f), gold = true, hem = 0.95f, longHair = true, build = 1.15f } },
        };

        public static Action<ModelActor> Person(string who) => m => Citizen(m, People[who]);

        /// <summary>One of the people of Ashkel: a robe or tunic to the knee or the ankle, a sash, and a head
        /// you can tell from across the square (hat, hair, beard).</summary>
        public static void Citizen(ModelActor m, Folk look) => Clothe(m, look);

        /// <summary>Dresses a citizen and hands back the body's measure, for whoever has more to add.</summary>
        static Fit Clothe(ModelActor m, Folk look)
        {
            var t = new Tailor(m);
            var f = new Fit(t);
            var kit = new Kit(t);
            float b = look.build;
            float hemY = look.hem >= 0 ? Mathf.Lerp(f.kneeY, f.ankleY + 0.06f, look.hem) : Mathf.Lerp(f.kneeY, f.pelvis.y, -look.hem * 0.6f);

            t.Paint((p, bone) =>
            {
                if (bone.StartsWith("spine") || bone.StartsWith("clavicle") || bone == "pelvis") return (look.tunic, 0f);
                if (bone.StartsWith("thigh") || bone.StartsWith("calf")) return p.y > hemY - 0.03f ? (look.tunic, 0f) : (look.skin, 0f);
                if (bone.StartsWith("foot") || bone.StartsWith("ball")) return (look.shoe, 0f);
                return (look.skin, 0f);
            });

            // ---- robe: body, then skirt
            kit.On(f.Spine());
            var trunk = f.trunk;
            if (look.apron) kit.Stain(p => p.z > trunk.z + 0.02f && Mathf.Abs(p.x) < 0.13f * b && p.y < f.chest.y - 0.02f ? new Color(0.94f, 0.92f, 0.84f) : (Color?)null);
            kit.Paint(look.tunic).Turned(trunk, new[]
            {
                ((f.wx + 0.035f) * b, f.waistY + 0.02f), ((f.wx + 0.05f) * b, f.waistY + 0.12f), ((f.chestX + 0.04f) * b, f.chest.y - 0.10f),
                ((f.chestX + 0.045f) * b, f.chest.y - 0.01f), ((f.chestX + 0.03f) * b, f.neck.y - 0.055f), (0.08f, f.neck.y - 0.012f),
            }, 16, f.deepChest);
            kit.On(f.Skirt(hemY));
            var waist = f.waist;
            float r0 = (f.wx + 0.03f) * b, r1 = (Mathf.Max(f.hipX, f.wx) + 0.05f) * b;
            float flare = hemY < f.kneeY ? 1.16f : 1.30f, rHem = r1 * flare + 0.03f;
            if (!look.apron) kit.Stain(p => Mathf.FloorToInt((Mathf.Atan2(p.x, p.z - waist.z) + Mathf.PI) / (Mathf.PI * 2f) * 12f + 0.5f) % 3 == 0 ? look.fold : (Color?)null);
            else kit.Stain(p => p.z > waist.z + 0.03f && Mathf.Abs(p.x) < 0.15f * b && p.y > hemY + 0.08f ? new Color(0.94f, 0.92f, 0.84f) : (Color?)null);
            kit.Paint(look.tunic).Turned(waist, new[]
            {
                (r0, f.waistY + 0.03f), (r1, Mathf.Lerp(f.waistY, hemY, 0.25f)), (Mathf.Lerp(r1, rHem, 0.5f), Mathf.Lerp(f.waistY, hemY, 0.6f)), (rHem, hemY + 0.03f), (rHem + 0.006f, hemY),
            }, 16, f.deep);
            kit.Stain(null);
            if (look.gold) kit.Paint(new Color(0.93f, 0.72f, 0.26f)).Turned(waist, new[] { (rHem + 0.006f, hemY + 0.05f), (rHem + 0.016f, hemY) }, 16, f.deep);

            // ---- sash
            kit.Paint(look.sash).On("pelvis", "spine_01", 0.5f);
            kit.Turned(waist, new[] { (r0 + 0.012f, f.waistY - 0.03f), (r0 + 0.026f, f.waistY + 0.005f), (r0 + 0.012f, f.waistY + 0.04f) }, 16, f.deep);

            Limbs(kit, t, look.skin, 0, look.skin, look.shoe, false, look.sleeves ? look.tunic : (Color?)null, b);

            // ---- the head: eyes, hair, beard, and whatever is worn on it
            Head(kit, f, look);
            kit.Wear("Clothes");
            if (look.headScale != 1f)
            {
                var headBone = m.Bone("Head");
                float k = look.headScale;
                headBone.localScale = Vector3.one * k;
                m.Posed += (a, dt) => headBone.localScale = Vector3.one * k;
            }
            return f;
        }

        static void Head(Kit kit, Fit f, Folk look)
        {
            var hc = f.hc;
            var hr = f.hr;
            kit.On("Head");
            // eyes: two dark marks on the face
            kit.Paint(new Color(0.10f, 0.07f, 0.08f));
            foreach (int s in new[] { -1, 1 })
            {
                var d = new Vector3(0.36f * s, 0.10f, 0.93f).normalized;
                var c = hc + Vector3.Scale(d, hr) + new Vector3(0, 0, 0.006f);
                kit.Face(c + new Vector3(-0.02f, -0.017f, 0), c + new Vector3(0.02f, -0.017f, 0), c + new Vector3(0.02f, 0.017f, 0), c + new Vector3(-0.02f, 0.017f, 0), Vector3.forward);
            }
            bool Face(Vector3 d) => d.z > 0.30f && d.y < 0.52f;
            string top = look.top ?? "hair";
            if (top != "bald" && top != "veil" && top != "scarf")
            {
                float puff = top == "curls" ? 0.05f : 0.016f;
                kit.Paint(look.hair).Egg(hc + new Vector3(0, 0.008f, -0.01f), hr + Vector3.one * puff, 14, 8, top == "curls" ? -20 : -8, 90, d => !Face(d));
            }
            if (look.longHair) kit.Paint(look.hair).On("Head", "spine_03", 0.5f).Egg(new Vector3(0, f.neck.y + 0.0f, f.head.z - f.hb * 0.75f), new Vector3(hr.x * 0.95f, 0.17f, 0.075f), 10, 6);
            kit.On("Head");
            if (look.beard)
            {
                float len = look.longBeard ? 0.17f : 0.075f;
                kit.Paint(look.beardColour).Egg(new Vector3(0, f.head.y + f.hh * 0.42f - len * 0.5f, f.head.z + f.hf * 0.72f), new Vector3(hr.x * 0.74f, 0.05f + len * 0.5f, 0.055f), 10, 6);
            }
            float crown = f.crown;
            switch (top)
            {
                case "scarf":
                    kit.Paint(look.hat).Egg(hc + new Vector3(0, 0.012f, -0.012f), hr + Vector3.one * 0.022f, 14, 8, 2, 90, d => !Face(d));
                    kit.Egg(new Vector3(0, hc.y - 0.02f, hc.z - hr.z - 0.03f), new Vector3(0.05f, 0.05f, 0.045f), 8, 5);
                    break;
                case "veil":
                    kit.Paint(look.hat).Egg(hc + new Vector3(0, 0.012f, -0.014f), hr + Vector3.one * 0.026f, 14, 8, -30, 90, d => !Face(d));
                    kit.On("Head", "spine_03", 0.6f).Egg(new Vector3(0, f.neck.y - 0.05f, f.head.z - f.hb * 0.6f), new Vector3(hr.x * 1.25f, 0.24f, 0.09f), 10, 6);
                    kit.On("Head").Paint(new Color(0.93f, 0.72f, 0.26f)).Turned(new Vector3(0, 0, hc.z), new[] { (hr.x + 0.03f, hc.y + 0.035f), (hr.x + 0.034f, hc.y + 0.065f) }, 14, hr.z / hr.x);
                    break;
                case "strawhat":
                    kit.Paint(look.hat).Turned(new Vector3(0, 0, hc.z), new[] { (0.30f, crown - 0.075f), (0.29f, crown - 0.055f), (hr.x + 0.02f, crown - 0.03f), (hr.x * 0.8f, crown + 0.045f), (0f, crown + 0.065f) }, 14);
                    kit.Turned(new Vector3(0, 0, hc.z), new[] { (0.30f, crown - 0.075f), (0f, crown - 0.06f) }, 14);
                    break;
                case "tallcap":
                    kit.Paint(look.hat).Turned(new Vector3(0, 0, hc.z), new[] { (hr.x + 0.022f, hc.y + 0.01f), (hr.x + 0.012f, crown + 0.16f), (hr.x * 0.72f, crown + 0.20f), (0f, crown + 0.20f) }, 12, hr.z / hr.x);
                    kit.Paint(new Color(0.93f, 0.72f, 0.26f)).Turned(new Vector3(0, 0, hc.z), new[] { (hr.x + 0.03f, hc.y + 0.01f), (hr.x + 0.03f, hc.y + 0.055f) }, 12, hr.z / hr.x);
                    break;
                case "headband":
                    kit.Paint(look.hat).Turned(new Vector3(0, 0, hc.z), new[] { (hr.x + 0.022f, hc.y + 0.02f), (hr.x + 0.026f, hc.y + 0.06f) }, 12, hr.z / hr.x);
                    break;
                case "kidhelm":
                    // his father's helmet, three sizes too big, down over his eyes
                    kit.Paint(new Color(0.80f, 0.54f, 0.20f), 1).Egg(hc + new Vector3(0, 0.03f, 0), hr + new Vector3(0.05f, 0.05f, 0.055f), 14, 7, -4, 90);
                    var foot = new Vector3[7];
                    var tip = new Vector3[7];
                    for (int i = 0; i < 7; i++)
                    {
                        float phi = Mathf.Lerp(50f, 170f, i / 6f) * Mathf.Deg2Rad;
                        var d = new Vector3(0, Mathf.Sin(phi), Mathf.Cos(phi));
                        foot[i] = hc + new Vector3(0, 0.03f, 0) + Vector3.Scale(d, hr + new Vector3(0.05f, 0.05f, 0.055f)) * 0.97f;
                        tip[i] = foot[i] + d * 0.075f;
                    }
                    kit.Paint(new Color(0.86f, 0.13f, 0.12f)).Fin(foot, tip, 0.045f);
                    break;
                case "crown":
                    kit.Paint(look.hat, 1).Turned(new Vector3(0, 0, hc.z), new[] { (hr.x + 0.02f, hc.y + 0.05f), (hr.x + 0.035f, crown + 0.02f), (hr.x + 0.06f, crown + 0.09f) }, 12, hr.z / hr.x);
                    break;
            }
        }

        // ============================================================================ the Hill of Sleepers
        /// <summary>One of the king's clay soldiers: fired earth from helm to shin, a real bronze spearhead,
        /// and two points of cold light where a face would be looking out.</summary>
        public static void Clay(ModelActor m) => Soldier(m, new Look
        {
            plateSkin = true, metal = 0f, skin = new Color(0.66f, 0.40f, 0.28f), bronze = new Color(0.70f, 0.44f, 0.30f),
            tunic = new Color(0.60f, 0.36f, 0.25f), tunicFold = new Color(0.48f, 0.28f, 0.20f), trim = new Color(0.80f, 0.58f, 0.40f),
            leather = new Color(0.42f, 0.24f, 0.18f), crest = new Color(0.52f, 0.30f, 0.22f), crestHeight = 0.07f, eyes = new Color(0.45f, 1.0f, 0.86f),
            shield = new Color(0.62f, 0.38f, 0.27f), hasCape = false, hasBlade = false, hasLantern = false, hasSpear = true, hasShield = true,
        });

        /// <summary>A warden of the king's inner doors: the guard's clay, a gold crest, and a shield the size of
        /// the door he was made to stand in.</summary>
        public static void Warden(ModelActor m) => Soldier(m, new Look
        {
            plateSkin = true, metal = 0f, skin = new Color(0.62f, 0.37f, 0.26f), bronze = new Color(0.72f, 0.50f, 0.26f),
            tunic = new Color(0.52f, 0.30f, 0.22f), tunicFold = new Color(0.40f, 0.22f, 0.17f), trim = new Color(0.93f, 0.72f, 0.26f),
            leather = new Color(0.40f, 0.22f, 0.17f), crest = new Color(0.93f, 0.72f, 0.26f), crestHeight = 0.11f, eyes = new Color(0.45f, 1.0f, 0.86f),
            hasCape = false, hasBlade = false, hasLantern = false, hasSpear = false, hasShield = false,       // (his shield is a door: it is its own thing, see WardenDoor)
        });

        /// <summary>The clay armies of the Generals' Barrow: the king's guard's cousins, in their general's
        /// colour. Ushur's (0) carry a spear and a red shield; Baltu's (1) carry nothing you can see, and
        /// throw it.</summary>
        public static Action<ModelActor> ClayOf(int side) => m => Soldier(m, new Look
        {
            plateSkin = true, metal = 0f, skin = new Color(0.66f, 0.40f, 0.28f), bronze = new Color(0.70f, 0.44f, 0.30f),
            tunic = side == 0 ? new Color(0.62f, 0.17f, 0.15f) : new Color(0.20f, 0.30f, 0.62f),
            tunicFold = side == 0 ? new Color(0.46f, 0.11f, 0.12f) : new Color(0.13f, 0.21f, 0.46f),
            trim = side == 0 ? new Color(0.93f, 0.72f, 0.26f) : new Color(0.88f, 0.88f, 0.92f),
            leather = new Color(0.42f, 0.24f, 0.18f), crest = side == 0 ? new Color(0.80f, 0.20f, 0.16f) : new Color(0.26f, 0.38f, 0.78f), crestHeight = 0.10f,
            eyes = new Color(0.45f, 1.0f, 0.86f), shield = side == 0 ? new Color(0.62f, 0.17f, 0.15f) : new Color(0.20f, 0.30f, 0.62f),
            hasCape = false, hasBlade = false, hasLantern = false, hasSpear = side == 0, hasShield = side == 0,
        });

        /// <summary>The Last Piece: the one both generals claim. Ushur's red on its body, Baltu's blue down its
        /// back, a gold crest neither of them paid for, and a shield as wide as a door.</summary>
        public static void Piece(ModelActor m) => Soldier(m, new Look
        {
            plateSkin = true, metal = 0f, skin = new Color(0.62f, 0.37f, 0.26f), bronze = new Color(0.66f, 0.41f, 0.28f),
            tunic = new Color(0.60f, 0.16f, 0.15f), tunicFold = new Color(0.44f, 0.10f, 0.11f), trim = new Color(0.93f, 0.72f, 0.26f),
            leather = new Color(0.40f, 0.22f, 0.17f), crest = new Color(0.93f, 0.72f, 0.26f), crestHeight = 0.2f, eyes = new Color(1.0f, 0.86f, 0.5f),
            cape = new Color(0.18f, 0.28f, 0.62f), shield = new Color(0.70f, 0.46f, 0.26f),
            hasCape = true, hasBlade = false, hasLantern = false, hasSpear = false, hasShield = true,
        });

        /// <summary>The two generals at their game: armour they were buried in, each his own side's colour.</summary>
        public static Action<ModelActor> General(int side) => m => Soldier(m, new Look
        {
            tunic = side == 0 ? new Color(0.60f, 0.16f, 0.16f) : new Color(0.18f, 0.28f, 0.60f),
            tunicFold = side == 0 ? new Color(0.46f, 0.10f, 0.12f) : new Color(0.12f, 0.20f, 0.46f),
            crest = side == 0 ? new Color(0.93f, 0.72f, 0.26f) : new Color(0.92f, 0.92f, 0.96f), crestHeight = 0.16f,
            cape = side == 0 ? new Color(0.46f, 0.10f, 0.12f) : new Color(0.12f, 0.20f, 0.46f),
            hasBlade = false, hasLantern = false, hasSpear = false, hasShield = false,
        });

        /// <summary>Kurashtar: a king's robe with a gold fringe, the squared beard of his line, the tall
        /// horned crown (which comes off), and the mace of his office in his right fist.</summary>
        public static void King(ModelActor m)
        {
            var f = Clothe(m, People["king"]);
            var t = f.t;
            Color gold = new Color(0.96f, 0.78f, 0.30f), lapis = new Color(0.16f, 0.26f, 0.66f), horn = new Color(0.94f, 0.92f, 0.84f);
            // ---- the crown: a tall cap of gold, a blue band, two horns turned in
            var ck = new Kit(t);
            var hc = f.hc; var hr = f.hr * 1.06f; float crown = f.crown + 0.01f;
            ck.On("Head");
            ck.Paint(gold, 1).Turned(new Vector3(0, 0, hc.z), new[]
            {
                (hr.x + 0.026f, hc.y + 0.02f), (hr.x + 0.034f, crown + 0.06f), (hr.x * 0.92f, crown + 0.17f), (hr.x * 0.5f, crown + 0.24f), (0f, crown + 0.26f),
            }, 12, hr.z / hr.x);
            ck.Paint(lapis).Turned(new Vector3(0, 0, hc.z), new[] { (hr.x + 0.042f, hc.y + 0.03f), (hr.x + 0.046f, hc.y + 0.085f) }, 12, hr.z / hr.x);
            foreach (int s in new[] { -1, 1 })
                ck.Paint(horn).Tube(new[]
                {
                    new Vector3(s * (hr.x + 0.02f), hc.y + 0.10f, hc.z + 0.03f), new Vector3(s * (hr.x + 0.10f), crown + 0.04f, hc.z + 0.05f),
                    new Vector3(s * (hr.x + 0.02f), crown + 0.16f, hc.z + 0.06f),
                }, new[] { 0.034f, 0.028f, 0.008f }, 6);
            var worn = ck.Wear("Crown");
            m.props["crown"] = worn.transform;
            // ---- the mace: a shaft of dark wood, a head of gold with a blue ring
            Grip(t, "_r", out var grip, out var fingers, out var across, out var palm);
            var mk = new Kit(t);
            mk.On("hand_r").Frame(grip, across, fingers, palm);
            mk.Paint(new Color(0.24f, 0.14f, 0.10f)).Ribbon(new[] { new Vector2(0, 0.26f), new Vector2(0, -0.66f) }, new[] { 0.045f, 0.045f }, 0.045f);
            mk.Frame();
            Vector3 head = grip + across * -0.74f;
            mk.Paint(gold, 1).Egg(head, Vector3.one * 0.115f, 10, 6);
            mk.Paint(lapis).Egg(head + across * 0.085f, new Vector3(0.07f, 0.07f, 0.07f), 8, 4);
            mk.Paint(gold, 1).Egg(grip + across * 0.27f, Vector3.one * 0.05f, 6, 4);
            mk.Wear("Mace");
            var hand = m.Bone("hand_r");
            m.marks["mace"] = (hand, hand.InverseTransformPoint(t.rig.TransformPoint(t.FromTailor(head))));
        }

        /// <summary>A thurifer: a censer-bearer's saffron robe gone grey to the knee with forty nights of his own
        /// smoke, arms bare for the work, a shaved head, and a cloth over his nose and mouth (he has met incense).</summary>
        public static void Thurifer(ModelActor m)
        {
            var look = new Folk
            {
                skin = Tan, hair = new Color(0.14f, 0.10f, 0.10f), tunic = new Color(0.88f, 0.60f, 0.16f), fold = new Color(0.66f, 0.42f, 0.12f),
                sash = new Color(0.52f, 0.10f, 0.10f), shoe = new Color(0.30f, 0.18f, 0.12f), top = "bald", sleeves = false, hem = 0.82f, build = 1.1f,
            };
            var f = Clothe(m, look);
            var ck = new Kit(f.t);
            ck.On("Head").Paint(new Color(0.26f, 0.22f, 0.22f)).Egg(f.hc + new Vector3(0, -f.hr.y * 0.44f, f.hr.z * 0.30f), new Vector3(f.hr.x * 0.98f, f.hr.y * 0.44f, f.hr.z * 0.84f), 10, 6);
            // a band of red at the brow, and the soot that has settled on his shoulders
            ck.Paint(new Color(0.60f, 0.12f, 0.10f)).Turned(new Vector3(0, 0, f.hc.z), new[] { (f.hr.x + 0.012f, f.hc.y + 0.05f), (f.hr.x + 0.014f, f.hc.y + 0.085f) }, 12, f.hr.z / f.hr.x);
            ck.On("spine_03").Paint(new Color(0.34f, 0.30f, 0.28f)).Turned(new Vector3(0, 0, f.trunk.z), new[] { (0.09f, f.neck.y - 0.015f), (f.chestX + 0.052f, f.neck.y - 0.06f), (f.chestX + 0.056f, f.neck.y - 0.10f) }, 14, f.deepChest);
            ck.Wear("Cloth");
        }

        /// <summary>A Medusa: a doorkeeper's gown the green of deep water with a gold hem, a gold collar and
        /// gold on her bare arms, a face the colour of old bronze, and the hair. The hair is eleven snakes.
        /// They hang about her head while she is at them with the comb, and stand up when she looks.</summary>
        public static void Medusa(ModelActor m)
        {
            Color gold = new Color(0.96f, 0.76f, 0.28f), pallor = new Color(0.58f, 0.68f, 0.54f);
            var look = new Folk
            {
                skin = pallor, hair = new Color(0.10f, 0.20f, 0.14f), tunic = new Color(0.09f, 0.31f, 0.27f), fold = new Color(0.05f, 0.20f, 0.19f),
                sash = gold, shoe = new Color(0.20f, 0.14f, 0.10f), top = "bald", sleeves = false, gold = true, hem = 0.97f, build = 0.96f, headScale = 1.14f,
            };
            var f = Clothe(m, look);
            var t = f.t;
            float k = look.headScale;
            // ---- gold: a broad collar, a band on each arm and each wrist
            var jk = new Kit(t);
            jk.On("spine_03").Paint(gold, 1).Turned(new Vector3(0, 0, f.trunk.z), new[] { (0.085f, f.neck.y - 0.02f), (0.15f, f.neck.y - 0.05f), (0.185f, f.neck.y - 0.085f) }, 14, f.deepChest);
            foreach (string side in new[] { "_l", "_r" })
            {
                Vector3 sh = t.At("upperarm" + side), el = t.At("lowerarm" + side), wr = t.At("hand" + side);
                jk.On("upperarm" + side).Paint(gold, 1).Egg(Vector3.Lerp(sh, el, 0.52f), new Vector3(0.030f, 0.076f, 0.080f), 8, 6);
                jk.On("lowerarm" + side).Paint(gold, 1).Egg(Vector3.Lerp(el, wr, 0.82f), new Vector3(0.026f, 0.062f, 0.064f), 8, 6);
            }
            jk.Wear("Gold");
            // ---- her eyes with the light in them: only there while she looks
            var gk = new Kit(t);
            gk.On("Head").Paint(new Color(0.74f, 1f, 0.62f), 0, 2.4f);
            foreach (int s in new[] { -1, 1 })
            {
                var d = new Vector3(0.36f * s, 0.10f, 0.93f).normalized;
                var c = f.hc + Vector3.Scale(d, f.hr) + new Vector3(0, 0, 0.010f);
                gk.Face(c + new Vector3(-0.027f, -0.022f, 0), c + new Vector3(0.027f, -0.022f, 0), c + new Vector3(0.027f, 0.022f, 0), c + new Vector3(-0.027f, 0.022f, 0), Vector3.forward);
            }
            var glare = gk.Wear("Glare");
            glare.enabled = false;
            // ---- the hair: each snake is two bones of its own on her head, so it can hang, sway and stand
            var headBone = m.Bone("Head");
            Vector3 OnHead(Vector3 p) => f.head + (p - f.head) * k;          // (her head is drawn a little large, and they grow from it as drawn)
            var plan = new (float az, float el, float len)[]
            {
                (0, 84, 0.25f), (-28, 60, 0.26f), (28, 60, 0.26f), (-64, 40, 0.31f), (64, 40, 0.31f), (-102, 32, 0.35f), (102, 32, 0.35f),
                (-140, 36, 0.35f), (140, 36, 0.35f), (-172, 44, 0.32f), (172, 44, 0.32f),
            };
            int n = plan.Length;
            var roots = new Transform[n];
            var tips = new Transform[n];
            var rear = new float[n];
            var bones = new System.Collections.Generic.List<Transform>();
            var origin = new Vector3[n];
            var ax = new Vector3[n]; var ay = new Vector3[n]; var az = new Vector3[n];
            Quaternion World(Vector3 y, Vector3 z) => Quaternion.LookRotation(t.rig.TransformDirection(t.FromTailor(z)), t.rig.TransformDirection(t.FromTailor(y)));
            for (int i = 0; i < n; i++)
            {
                float a = plan[i].az * Mathf.Deg2Rad, e = plan[i].el * Mathf.Deg2Rad;
                var d = new Vector3(Mathf.Sin(a) * Mathf.Cos(e), Mathf.Sin(e), Mathf.Cos(a) * Mathf.Cos(e));
                origin[i] = OnHead(f.hc + Vector3.Scale(d, f.hr) * 0.9f);
                // at rest: the ones on top lie forward and up, the rest hang out and down about her head
                Vector3 dir = i == 0 ? new Vector3(0, 0.75f, -0.5f) : i < 3 ? new Vector3(d.x * 0.9f, 0.45f, 0.65f) : new Vector3(d.x, d.y * 0.2f - 0.42f, d.z);
                ay[i] = dir.normalized;
                ax[i] = Vector3.Cross(Vector3.up, ay[i]);
                ax[i] = ax[i].sqrMagnitude < 0.001f ? Vector3.right : ax[i].normalized;
                az[i] = Vector3.Cross(ax[i], ay[i]);
                float fromUp = Vector3.Angle(ay[i], Vector3.up);
                rear[i] = Mathf.Max(0f, fromUp - (24f + 30f * ((i * 37) % 10) / 10f));
                roots[i] = new GameObject("sn" + i + "a").transform;
                roots[i].SetParent(headBone, false);
                roots[i].position = t.rig.TransformPoint(t.FromTailor(origin[i]));
                roots[i].rotation = World(ay[i], az[i]);
                tips[i] = new GameObject("sn" + i + "b").transform;
                tips[i].SetParent(roots[i], false);
                tips[i].position = t.rig.TransformPoint(t.FromTailor(origin[i] + ay[i] * plan[i].len * 0.5f * k));
                tips[i].rotation = roots[i].rotation;
                bones.Add(roots[i]); bones.Add(tips[i]);
            }
            var sk = new Kit(m, t.rig, bones.ToArray());
            for (int i = 0; i < n; i++)
            {
                float len = plan[i].len * k, half = len * 0.5f;
                Color body = i % 2 == 0 ? new Color(0.22f, 0.58f, 0.22f) : new Color(0.10f, 0.36f, 0.24f), band = new Color(0.05f, 0.17f, 0.10f);
                Color snout = i % 2 == 0 ? new Color(0.62f, 0.86f, 0.36f) : new Color(0.40f, 0.70f, 0.40f);
                Vector3 o = t.FromTailor(origin[i]), x = t.FromTailor(ax[i]), y = t.FromTailor(ay[i]), z = t.FromTailor(az[i]);
                sk.Frame(o, x, y, z);
                sk.Stain(p => Mathf.FloorToInt(Vector3.Dot(p - o, y) / 0.045f + 20f) % 3 == 0 ? band : (Color?)null);
                sk.On("sn" + i + "a").Paint(body).Tube(new[] { new Vector3(0, -0.03f, 0), new Vector3(0, half * 0.5f, 0), new Vector3(0, half + 0.01f, 0) }, new[] { 0.047f, 0.043f, 0.038f }, 6);
                // the far half turns up at the end, and has the head on it
                var up1 = new Vector3(0, half + half * 0.5f, -half * 0.16f);
                var up2 = new Vector3(0, half + half * 0.92f, -half * 0.5f);
                sk.On("sn" + i + "b").Paint(body).Tube(new[] { new Vector3(0, half - 0.01f, 0), up1, up2 }, new[] { 0.038f, 0.034f, 0.030f }, 6);
                sk.Stain(null);
                sk.Paint(snout).Egg(up2 + new Vector3(0, 0.024f, -0.016f), new Vector3(0.046f, 0.052f, 0.046f), 6, 4);
                sk.Paint(new Color(1f, 0.25f, 0.10f), 0, 1.6f).Egg(up2 + new Vector3(0, 0.05f, -0.04f), Vector3.one * 0.016f, 4, 3);       // (a tongue, or an eye: at this distance, a warning)
            }
            sk.Frame();
            sk.Wear("Hair");
            var restA = new Quaternion[n];
            var restB = new Quaternion[n];
            for (int i = 0; i < n; i++) { restA[i] = roots[i].localRotation; restB[i] = tips[i].localRotation; }
            Wakefire.Medusa who = null;
            bool looked = false;
            m.Posed += (a, dt) =>
            {
                if (!looked) { looked = true; who = a.sr ? a.sr.GetComponentInParent<Wakefire.Medusa>() : null; }
                float r = who ? who.Reared : a.anim == "stare" ? 1f : 0f;
                if (glare) glare.enabled = r > 0.35f;
                float time = a.life;
                for (int i = 0; i < n; i++)
                {
                    float ph = i * 1.7f;
                    float lift = -r * rear[i] + Mathf.Sin(time * (1.6f + r * 3.2f) + ph) * (5f + 7f * r);
                    float wig = Mathf.Sin(time * (2.1f + r * 4f) + ph * 1.3f) * (7f + 6f * r);
                    roots[i].localRotation = restA[i] * Quaternion.Euler(lift, 0, wig * 0.6f);
                    tips[i].localRotation = restB[i] * Quaternion.Euler(-r * 16f + Mathf.Sin(time * (2.4f + r * 4f) + ph + 1.1f) * (11f + 9f * r), 0, wig);
                }
            };
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

    /// <summary>Gestures layered on a clip by hand: the things no stock animation has, like a guard
    /// asleep on his feet or a watchman's head dropping and jerking back up.</summary>
    public static class Gesture
    {
        static float Ease(float k) { k = Mathf.Clamp01(k); return k * k * (3 - 2 * k); }

        /// <summary>A head falling forward in sleep.</summary>
        public static void Droop(ModelActor m, float amount)
        {
            m.Bend("spine_03", 7f * amount);
            m.Bend("neck_01", 14f * amount);
            m.Bend("Head", 24f * amount);
        }

        static void Arms(ModelActor m, float pitch, float spread = 0, float elbow = 0)
        {
            m.Bend("upperarm_l", pitch, 0, -spread);
            m.Bend("upperarm_r", pitch, 0, spread);
            if (elbow != 0) { m.Bend("lowerarm_l", elbow); m.Bend("lowerarm_r", elbow); }
        }

        public static Action<ModelActor, float> Asleep(float droop = 0.8f, float sway = 2.5f) => (m, n) =>
        {
            Droop(m, droop + Mathf.Sin(m.life * 1.5f) * 0.07f);
            m.Bend("spine_01", 0, 0, Mathf.Sin(m.life * 0.62f) * sway);
        };

        /// <summary>Asleep leaning on a spear: the weight on one hip, the helmet down on the chest.</summary>
        public static Action<ModelActor, float> Leaning => (m, n) =>
        {
            m.Bend("pelvis", 3f, 0, 7f);
            m.Bend("spine_02", 0, 0, -5f);
            Droop(m, 1.15f + Mathf.Sin(m.life * 1.4f) * 0.08f);
        };

        public static Action<ModelActor, float> Lying => (m, n) =>
        {
            var chest = m.Bone("spine_02");
            if (chest) chest.localScale = Vector3.one * (1f + Mathf.Sin(m.life * 1.5f) * 0.035f);
        };

        public static Action<ModelActor, float> Sleepwalk => (m, n) =>
        {
            Arms(m, -74f, 4f);
            Droop(m, 0.95f);
            m.Bend("spine_01", 0, 0, Mathf.Sin(m.life * 1.1f) * 3f);
        };

        public static Action<ModelActor, float> Kneading => (m, n) => Droop(m, 0.9f + Mathf.Sin(m.life * 1.5f) * 0.06f);

        public static Action<ModelActor, float> Cower => (m, n) =>
        {
            Arms(m, -150f, 14f, -70f);
            Droop(m, 0.8f);
            m.Bend("spine_02", 0, 0, Mathf.Sin(m.life * 31f) * 1.6f);       // shaking
        };

        public static Action<ModelActor, float> Point => (m, n) => { m.Bend("upperarm_r", -82f * Ease(n * 3f), -8f); };

        /// <summary>A censer going round overhead: the right arm up, the wrist doing the work.</summary>
        public static Action<ModelActor, float> Swing => (m, n) =>
        {
            float t = m.life * 4.6f;
            m.Bend("upperarm_r", -152f + Mathf.Sin(t) * 9f, 0, 10f + Mathf.Cos(t) * 9f);
            m.Bend("lowerarm_r", Mathf.Sin(t) * 22f - 10f, 0, Mathf.Cos(t) * 22f);
            m.Bend("spine_02", 0, Mathf.Sin(t) * 4f, 0);
        };

        /// <summary>Bent over with both hands at his throat, coughing.</summary>
        public static Action<ModelActor, float> Cough => (m, n) =>
        {
            float k = Mathf.Abs(Mathf.Sin(m.life * 8.5f));
            m.Bend("spine_02", 16f + k * 12f);
            m.Bend("upperarm_l", -64f, 22f); m.Bend("upperarm_r", -64f, -22f);
            m.Bend("lowerarm_l", -96f); m.Bend("lowerarm_r", -96f);
            Droop(m, 0.5f + k * 0.4f);
        };

        public static Action<ModelActor, float> Shrug => (m, n) =>
        {
            float k = Ease(n * 3f);
            m.Bend("clavicle_l", 0, 0, 14f * k);
            m.Bend("clavicle_r", 0, 0, -14f * k);
            m.Bend("lowerarm_l", -58f * k, 20f * k);
            m.Bend("lowerarm_r", -58f * k, -20f * k);
            m.Bend("Head", 0, 0, 9f * k);
        };

        public static Action<ModelActor, float> Sigh => (m, n) =>
        {
            float k = Mathf.Sin(Mathf.Clamp01(n) * Mathf.PI);
            m.Bend("spine_03", 10f * k);
            Droop(m, 0.55f * k);
        };

        // ---- Azar
        public static Action<ModelActor, float> NodOff => (m, n) =>
        {
            float k = Ease(n);
            Droop(m, 1.35f * k);
            m.Bend("spine_01", 9f * k);
        };

        public static Action<ModelActor, float> WakeUp => (m, n) =>
        {
            float k = 1f - Ease(n * 1.7f);
            Droop(m, 1.35f * k - Mathf.Sin(Mathf.Clamp01(n) * Mathf.PI) * 0.35f);        // snaps past upright and settles
            m.Bend("spine_01", 9f * k);
        };

        public static Action<ModelActor, float> Doze => (m, n) =>
        {
            float k = Ease(n);
            Droop(m, 1.4f * k + Mathf.Sin(m.life * 1.5f) * 0.07f * k);
            m.Bend("spine_01", 8f * k, 0, Mathf.Sin(m.life * 0.7f) * 3f * k);
        };

        public static Action<ModelActor, float> Yawn => (m, n) =>
        {
            float k = Mathf.Sin(Mathf.Clamp01(n) * Mathf.PI);
            Droop(m, -0.9f * k);
            m.Bend("spine_03", -9f * k);
            Arms(m, -12f * k, 26f * k);
        };

        /// <summary>The watchman's head sinks... and jerks back up.</summary>
        public static Action<ModelActor, float> CatchHimself => (m, n) =>
        {
            float k = n < 0.72f ? Ease(n / 0.72f) : 1f - Ease((n - 0.72f) / 0.12f);
            Droop(m, 1.25f * k - (n > 0.84f ? Mathf.Sin((n - 0.84f) / 0.16f * Mathf.PI) * 0.3f : 0f));
        };

        /// <summary>Tips the shoulders so an overhead chop comes down across the body instead.</summary>
        public static Action<ModelActor, float> Across(float degrees) => (m, n) =>
        {
            float k = Mathf.Sin(Mathf.Clamp01(n * 1.15f) * Mathf.PI);
            m.Bend("spine_02", 0, 0, degrees * k);
            m.Bend("spine_03", 0, 0, degrees * 0.45f * k);
            m.Bend("Head", 0, 0, -degrees * 0.6f * k);
        };

        /// <summary>The last cut of the combo leaves the ground: up with the blade, down with all his weight.</summary>
        public static Action<ModelActor, float> Leap => (m, n) =>
        {
            float k = Mathf.Clamp01(n / 0.5f);
            m.height = Mathf.Sin(k * Mathf.PI) * 0.34f;
            m.Bend("spine_01", 10f * Mathf.Clamp01((n - 0.4f) / 0.2f) * (1f - Mathf.Clamp01((n - 0.8f) / 0.2f)));
        };

        public static Action<ModelActor, float> Block => (m, n) =>
        {
            m.Bend("upperarm_l", -62f, 38f);
            m.Bend("lowerarm_l", -64f, 20f);
        };

        /// <summary>A sentinel at the charge: the spear comes down level.</summary>
        /// <summary>Both arms out in front at the height of the chest: a man walking a door along.</summary>
        public static Action<ModelActor, float> Carry => (m, n) =>
        {
            m.Bend("upperarm_r", -70f, -8f);
            m.Bend("upperarm_l", -70f, 8f);
        };

        public static Action<ModelActor, float> Level => (m, n) =>
        {
            m.Bend("upperarm_r", -78f, -6f);
            m.Bend("spine_02", 10f);
        };
    }
}
