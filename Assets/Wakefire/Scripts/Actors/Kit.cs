// Dressing a rigged body. The Tailor measures the body as it stands at rest; the Kit builds
// what it wears (helmets, kilts, blades, plates) straight onto those measurements and binds
// each piece to the bones that should carry it, so one set of clothes fits whatever body it is
// put on. Everything here is in "tailor space": x to the wearer's right, y up, z the way they
// face, in metres.
using System;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public class Tailor
    {
        public readonly ModelActor actor;
        public readonly Transform rig;
        public readonly SkinnedMeshRenderer body;
        public readonly Transform[] bones;
        public readonly Vector3[] rest;          // every vertex of the body at rest
        public readonly string[] owner;          // the bone each vertex mostly follows
        readonly Quaternion turn;
        readonly Dictionary<string, int> index = new Dictionary<string, int>();

        public Tailor(ModelActor a)
        {
            actor = a;
            rig = a.rig;
            turn = Quaternion.Euler(0, -a.def.forward, 0);
            foreach (var r in a.parts)
                if (r is SkinnedMeshRenderer s && (!body || s.sharedMesh.vertexCount > body.sharedMesh.vertexCount)) body = s;
            bones = body.bones;
            for (int i = 0; i < bones.Length; i++) index[bones[i].name] = i;
            var mesh = body.sharedMesh;
            var v = mesh.vertices;
            var w = mesh.boneWeights;
            var bp = mesh.bindposes;
            var m = new Matrix4x4[bones.Length];
            for (int i = 0; i < bones.Length; i++) m[i] = rig.worldToLocalMatrix * bones[i].localToWorldMatrix * bp[i];
            rest = new Vector3[v.Length];
            owner = new string[v.Length];
            for (int i = 0; i < v.Length; i++)
            {
                var b = w[i];
                var p = m[b.boneIndex0].MultiplyPoint3x4(v[i]) * b.weight0;
                if (b.weight1 > 0) p += m[b.boneIndex1].MultiplyPoint3x4(v[i]) * b.weight1;
                if (b.weight2 > 0) p += m[b.boneIndex2].MultiplyPoint3x4(v[i]) * b.weight2;
                if (b.weight3 > 0) p += m[b.boneIndex3].MultiplyPoint3x4(v[i]) * b.weight3;
                rest[i] = turn * p;
                owner[i] = bones[b.boneIndex0].name;
            }
        }

        public int Index(string bone) => index.TryGetValue(bone, out int i) ? i : 0;
        public bool Has(string bone) => index.ContainsKey(bone);

        /// <summary>Where a joint sits at rest.</summary>
        public Vector3 At(string bone) => turn * rig.InverseTransformPoint(actor.Bone(bone).position);

        public Vector3 FromTailor(Vector3 p) => Quaternion.Inverse(turn) * p;

        /// <summary>How far the skin stands off the line a-b around the fraction t along it, measured
        /// along one direction (so a chest can be wider than it is deep).</summary>
        public float Reach(Vector3 a, Vector3 b, float t, float dt, Vector3 along, Func<string, bool> of = null)
        {
            var axis = b - a;
            float len2 = axis.sqrMagnitude, best = 0;
            for (int i = 0; i < rest.Length; i++)
            {
                if (of != null && !of(owner[i])) continue;
                var d = rest[i] - a;
                float k = Vector3.Dot(d, axis) / len2;
                if (Mathf.Abs(k - t) > dt) continue;
                var off = d - axis * k;
                best = Mathf.Max(best, Vector3.Dot(off, along));
            }
            return best;
        }

        public float Top(Func<string, bool> of)
        {
            float y = -99;
            for (int i = 0; i < rest.Length; i++) if (of(owner[i])) y = Mathf.Max(y, rest[i].y);
            return y;
        }

        /// <summary>Paints the body itself: cloth, plate and skin are colours on its own surface.
        /// The painter is told where each point of the skin is and which bone carries it, and
        /// answers with a colour and how much it shines like metal.</summary>
        public void Paint(Func<Vector3, string, (Color colour, float metal)> painter)
        {
            var mesh = UnityEngine.Object.Instantiate(body.sharedMesh);
            mesh.name = body.sharedMesh.name + " painted";
            var c = new Color[rest.Length];
            var f = new Vector2[rest.Length];
            for (int i = 0; i < rest.Length; i++)
            {
                var k = painter(rest[i], owner[i]);
                f[i] = new Vector2(k.metal, 0);
                c[i] = k.colour.linear;
            }
            mesh.colors = c;
            mesh.uv2 = f;
            body.sharedMesh = mesh;
        }
    }

    public class Kit
    {
        public readonly Tailor tailor;
        // a kit can also be built straight onto a skeleton made by code (the beasts): its bones, by name
        readonly Transform rig;
        readonly Transform[] ownBones;
        readonly ModelActor owner;
        readonly Dictionary<string, int> ownIndex;

        public Kit(ModelActor actor, Transform rigRoot, Transform[] bones)
        {
            owner = actor;
            rig = rigRoot;
            ownBones = bones;
            ownIndex = new Dictionary<string, int>();
            for (int i = 0; i < bones.Length; i++) ownIndex[bones[i].name] = i;
        }

        int Index(string bone) => tailor != null ? tailor.Index(bone) : ownIndex.TryGetValue(bone, out int i) ? i : 0;
        readonly List<Vector3> pos = new List<Vector3>(), nrm = new List<Vector3>();
        readonly List<Color> col = new List<Color>();
        readonly List<Vector2> flag = new List<Vector2>();
        readonly List<BoneWeight> wt = new List<BoneWeight>();
        readonly List<int> tri = new List<int>();
        Color paint = Color.white;
        Vector2 flags;
        Func<Vector3, BoneWeight> bind = _ => default;
        Func<Vector3, Color?> stain;
        Matrix4x4 frame = Matrix4x4.identity;

        public Kit(Tailor t = null) { tailor = t; }

        public Kit Paint(Color c, float metal = 0, float glow = 0)
        {
            paint = c.linear;
            flags = new Vector2(metal, glow);
            return this;
        }

        /// <summary>What follows is carried rigidly by one bone.</summary>
        public Kit On(string bone)
        {
            int i = Index(bone);
            bind = _ => new BoneWeight { boneIndex0 = i, weight0 = 1 };
            return this;
        }

        /// <summary>What follows is shared between two bones.</summary>
        public Kit On(string a, string b, float share)
        {
            int i = Index(a), j = Index(b);
            bind = _ => new BoneWeight { boneIndex0 = i, weight0 = 1 - share, boneIndex1 = j, weight1 = share };
            return this;
        }

        public Kit On(Func<Vector3, BoneWeight> f) { bind = f; return this; }

        /// <summary>Until cleared (null), any point of what follows may be given another colour by where it is: a strap across a breastplate, a stripe.</summary>
        public Kit Stain(Func<Vector3, Color?> f) { stain = f; return this; }

        /// <summary>Carried between two bones, more by the second the further along the line a-b the point is.</summary>
        public Kit Along(string first, string second, Vector3 a, Vector3 b)
        {
            int i = Index(first), j = Index(second);
            var ab = b - a;
            float len2 = ab.sqrMagnitude;
            bind = p =>
            {
                float k = Mathf.Clamp01(Vector3.Dot(p - a, ab) / len2);
                return new BoneWeight { boneIndex0 = i, weight0 = 1 - k, boneIndex1 = j, weight1 = k };
            };
            return this;
        }

        /// <summary>Build what follows in its own frame (an origin and three axes) rather than the wearer's.</summary>
        public Kit Frame(Vector3 origin, Vector3 x, Vector3 y, Vector3 z)
        {
            frame = new Matrix4x4(new Vector4(x.x, x.y, x.z, 0), new Vector4(y.x, y.y, y.z, 0), new Vector4(z.x, z.y, z.z, 0), new Vector4(origin.x, origin.y, origin.z, 1));
            return this;
        }

        public Kit Frame() { frame = Matrix4x4.identity; return this; }

        int V(Vector3 p, Vector3 n)
        {
            var q = frame.MultiplyPoint3x4(p);
            pos.Add(q);
            nrm.Add(frame.MultiplyVector(n).normalized);
            var stained = stain?.Invoke(q);
            col.Add(stained.HasValue ? stained.Value.linear : paint);
            flag.Add(flags);
            wt.Add(bind(q));
            return pos.Count - 1;
        }

        void Quad(int a, int b, int c, int d) { tri.Add(a); tri.Add(b); tri.Add(c); tri.Add(a); tri.Add(c); tri.Add(d); }

        /// <summary>A flat-shaded quad from four corners (given in order round its edge).</summary>
        public Kit Face(Vector3 a, Vector3 b, Vector3 c, Vector3 d, Vector3 outward)
        {
            var n = Vector3.Cross(b - a, c - a).normalized;
            if (n.sqrMagnitude < 0.5f) n = Vector3.Cross(c - a, d - a).normalized;
            if (Vector3.Dot(n, outward) < 0) n = -n;
            Quad(V(a, n), V(b, n), V(c, n), V(d, n));
            return this;
        }

        /// <summary>An egg: centre, radii, and the band of latitude kept (degrees, -90 pole to 90 pole).
        /// "keep" can cut openings; it is asked about each patch by the direction from the centre.</summary>
        public Kit Egg(Vector3 c, Vector3 r, int seg = 14, int rings = 8, float lat0 = -90, float lat1 = 90, Func<Vector3, bool> keep = null, float lon0 = 0, float lon1 = 360)
        {
            var grid = new int[rings + 1, seg + 1];
            var dirs = new Vector3[rings + 1, seg + 1];
            for (int i = 0; i <= rings; i++)
                for (int j = 0; j <= seg; j++)
                {
                    float lat = Mathf.Lerp(lat0, lat1, i / (float)rings) * Mathf.Deg2Rad, lon = Mathf.Lerp(lon0, lon1, j / (float)seg) * Mathf.Deg2Rad;
                    var d = new Vector3(Mathf.Cos(lat) * Mathf.Sin(lon), Mathf.Sin(lat), Mathf.Cos(lat) * Mathf.Cos(lon));
                    dirs[i, j] = d;
                    grid[i, j] = V(c + Vector3.Scale(d, r), new Vector3(d.x / r.x, d.y / r.y, d.z / r.z));
                }
            for (int i = 0; i < rings; i++)
                for (int j = 0; j < seg; j++)
                {
                    if (keep != null && !keep((dirs[i, j] + dirs[i + 1, j + 1] + dirs[i, j + 1] + dirs[i + 1, j]).normalized)) continue;
                    Quad(grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]);
                }
            return this;
        }

        /// <summary>A turned shape: rings of (radius, height) stacked up the y axis from c, optionally
        /// squashed front to back, optionally only part of the way round.</summary>
        public Kit Turned(Vector3 c, (float r, float y)[] profile, int seg = 14, float deep = 1f, float lon0 = 0, float lon1 = 360, Func<int, int, Color?> tint = null)
        {
            int n = profile.Length;
            var grid = new int[n, seg + 1];
            var keepPaint = paint;
            for (int i = 0; i < n; i++)
            {
                var a = profile[Mathf.Max(0, i - 1)];
                var b = profile[Mathf.Min(n - 1, i + 1)];
                var slope = new Vector2(b.y - a.y, -(b.r - a.r)).normalized;     // outward, upward parts of the normal
                for (int j = 0; j <= seg; j++)
                {
                    float lon = Mathf.Lerp(lon0, lon1, j / (float)seg) * Mathf.Deg2Rad;
                    float sx = Mathf.Sin(lon), sz = Mathf.Cos(lon);
                    if (tint != null) { var t = tint(i, j); paint = t.HasValue ? t.Value.linear : keepPaint; }
                    grid[i, j] = V(c + new Vector3(profile[i].r * sx, profile[i].y, profile[i].r * sz * deep), new Vector3(slope.x * sx, slope.y, slope.x * sz / Mathf.Max(0.05f, deep)));
                }
            }
            paint = keepPaint;
            for (int i = 0; i < n - 1; i++)
                for (int j = 0; j < seg; j++)
                    Quad(grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]);
            return this;
        }

        /// <summary>A flat blade or strap cut from a ribbon: centre line points with a width at each,
        /// lying in the frame's x-y plane, with thickness along z.</summary>
        public Kit Ribbon(Vector2[] line, float[] width, float thick)
        {
            int n = line.Length;
            var l = new Vector3[n];
            var r = new Vector3[n];
            for (int i = 0; i < n; i++)
            {
                var d = (line[Mathf.Min(n - 1, i + 1)] - line[Mathf.Max(0, i - 1)]).normalized;
                var side = new Vector2(-d.y, d.x) * width[i] * 0.5f;
                l[i] = line[i] + side;
                r[i] = line[i] - side;
            }
            var up = new Vector3(0, 0, thick * 0.5f);
            for (int i = 0; i < n - 1; i++)
            {
                Face(l[i] + up, l[i + 1] + up, r[i + 1] + up, r[i] + up, Vector3.forward);
                Face(l[i] - up, l[i + 1] - up, r[i + 1] - up, r[i] - up, Vector3.back);
                Face(l[i] - up, l[i + 1] - up, l[i + 1] + up, l[i] + up, l[i] - (Vector3)line[i]);
                Face(r[i] - up, r[i + 1] - up, r[i + 1] + up, r[i] + up, r[i] - (Vector3)line[i]);
            }
            Face(l[0] - up, r[0] - up, r[0] + up, l[0] + up, (Vector3)(line[0] - line[1]));
            Face(l[n - 1] - up, r[n - 1] - up, r[n - 1] + up, l[n - 1] + up, (Vector3)(line[n - 1] - line[n - 2]));
            return this;
        }

        /// <summary>A standing fin (a helmet crest): points along its foot, the matching points along its
        /// top edge, and how thick it is from side to side (along x).</summary>
        public Kit Fin(Vector3[] foot, Vector3[] top, float thick)
        {
            var s = new Vector3(thick * 0.5f, 0, 0);
            int n = foot.Length;
            for (int i = 0; i < n - 1; i++)
            {
                Face(foot[i] + s, foot[i + 1] + s, top[i + 1] + s, top[i] + s, Vector3.right);
                Face(foot[i] - s, foot[i + 1] - s, top[i + 1] - s, top[i] - s, Vector3.left);
                var outward = (top[i] - foot[i]).normalized;
                Face(top[i] - s, top[i + 1] - s, top[i + 1] + s, top[i] + s, outward);
            }
            Face(foot[0] - s, foot[0] + s, top[0] + s, top[0] - s, foot[0] - foot[1]);
            Face(foot[n - 1] - s, foot[n - 1] + s, top[n - 1] + s, top[n - 1] - s, foot[n - 1] - foot[n - 2]);
            return this;
        }

        /// <summary>A round limb or horn following a path, as thick as the radius given at each point.</summary>
        public Kit Tube(Vector3[] path, float[] radius, int seg = 6)
        {
            int n = path.Length;
            var grid = new int[n, seg + 1];
            var side = Vector3.zero;
            for (int i = 0; i < n; i++)
            {
                var tan = (path[Mathf.Min(n - 1, i + 1)] - path[Mathf.Max(0, i - 1)]).normalized;
                if (i == 0)
                {
                    side = Vector3.Cross(tan, Mathf.Abs(tan.y) < 0.9f ? Vector3.up : Vector3.right).normalized;
                }
                else side = (side - tan * Vector3.Dot(side, tan)).normalized;      // carried along the path so the tube doesn't twist
                var other = Vector3.Cross(tan, side);
                for (int j = 0; j <= seg; j++)
                {
                    float a = j / (float)seg * Mathf.PI * 2f;
                    var d = side * Mathf.Cos(a) + other * Mathf.Sin(a);
                    grid[i, j] = V(path[i] + d * radius[i], d);
                }
            }
            for (int i = 0; i < n - 1; i++)
                for (int j = 0; j < seg; j++)
                    Quad(grid[i, j], grid[i + 1, j], grid[i + 1, j + 1], grid[i, j + 1]);
            return this;
        }

        public Kit Box(Vector3 c, Vector3 size)
        {
            var h = size * 0.5f;
            Vector3 P(float x, float y, float z) => c + new Vector3(x * h.x, y * h.y, z * h.z);
            Face(P(-1, -1, 1), P(1, -1, 1), P(1, 1, 1), P(-1, 1, 1), Vector3.forward);
            Face(P(-1, -1, -1), P(1, -1, -1), P(1, 1, -1), P(-1, 1, -1), Vector3.back);
            Face(P(1, -1, -1), P(1, -1, 1), P(1, 1, 1), P(1, 1, -1), Vector3.right);
            Face(P(-1, -1, -1), P(-1, -1, 1), P(-1, 1, 1), P(-1, 1, -1), Vector3.left);
            Face(P(-1, 1, -1), P(1, 1, -1), P(1, 1, 1), P(-1, 1, 1), Vector3.up);
            Face(P(-1, -1, -1), P(1, -1, -1), P(1, -1, 1), P(-1, -1, 1), Vector3.down);
            return this;
        }

        /// <summary>The finished kit as a skinned mesh on the wearer's own skeleton.</summary>
        public SkinnedMeshRenderer Wear(string name)
        {
            var t = tailor;
            var root = t != null ? t.rig : rig;
            var bones = t != null ? t.bones : ownBones;
            var mesh = new Mesh { name = name };
            var p = new Vector3[pos.Count];
            var n = new Vector3[pos.Count];
            for (int i = 0; i < p.Length; i++) { p[i] = t != null ? t.FromTailor(pos[i]) : pos[i]; n[i] = t != null ? t.FromTailor(nrm[i]) : nrm[i]; }
            mesh.vertices = p;
            mesh.normals = n;
            mesh.colors = col.ToArray();
            mesh.uv2 = flag.ToArray();
            mesh.boneWeights = wt.ToArray();
            var bp = new Matrix4x4[bones.Length];
            for (int i = 0; i < bp.Length; i++) bp[i] = bones[i].worldToLocalMatrix * root.localToWorldMatrix;
            mesh.bindposes = bp;
            mesh.triangles = tri.ToArray();
            mesh.RecalculateBounds();

            var go = new GameObject(name);
            go.layer = ModelStage.Layer;
            go.transform.SetParent(root, false);
            var smr = go.AddComponent<SkinnedMeshRenderer>();
            smr.sharedMesh = mesh;
            smr.bones = bones;
            smr.rootBone = t != null ? t.body.rootBone : bones[0];
            smr.updateWhenOffscreen = true;
            smr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            smr.receiveShadows = false;
            var mat = new Material(ModelLibrary.I.material);
            mat.SetFloat("_Cull", 0);
            mat.SetFloat("_Both", 1);
            smr.sharedMaterial = mat;
            (t != null ? t.actor : owner).parts.Add(smr);
            return smr;
        }

        /// <summary>The finished piece as a loose mesh of its own (something carried or hung, moved by hand).</summary>
        public MeshRenderer Loose(string name, Transform parent)
        {
            var mesh = new Mesh { name = name };
            mesh.vertices = pos.ToArray();
            mesh.normals = nrm.ToArray();
            mesh.colors = col.ToArray();
            mesh.uv2 = flag.ToArray();
            mesh.triangles = tri.ToArray();
            mesh.RecalculateBounds();
            var go = new GameObject(name);
            go.layer = ModelStage.Layer;
            go.transform.SetParent(parent, false);
            go.AddComponent<MeshFilter>().sharedMesh = mesh;
            var mr = go.AddComponent<MeshRenderer>();
            var mat = new Material(ModelLibrary.I.material);
            mat.SetFloat("_Cull", 0);
            mat.SetFloat("_Both", 1);
            mr.sharedMaterial = mat;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            return mr;
        }
    }
}
