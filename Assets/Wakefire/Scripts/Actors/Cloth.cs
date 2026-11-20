// Things that hang off a moving body and obey their own weight: a cape pinned at the shoulders,
// a lantern swinging from a fist. Both are simulated on the model stage in the body's own
// upright frame, with the air rushing past at the speed the actor is really moving through the
// world, so a cape streams out behind a run and settles when its wearer stops.
using UnityEngine;

namespace Wakefire
{
    public class Cape : MonoBehaviour
    {
        public ModelActor actor;
        public int cols = 5, rows = 8;
        public float drag = 3.2f, gravity = 9.8f, damping = 0.985f;
        Transform pin;
        Vector3[] pinLocal;
        Vector3[] p, prev;
        float[] across;                 // spacing between neighbours along each row
        float seg;                      // spacing between rows
        Mesh mesh;
        (Transform a, Transform b, float r)[] body;
        Vector3[] limbA, limbB;
        bool hung;

        public static Cape Make(ModelActor actor, Tailor t, Color colour, Vector3 left, Vector3 right, float length, float hemWidth, string pinBone = "spine_03")
        {
            var go = new GameObject("Cape");
            go.layer = ModelStage.Layer;
            go.transform.SetParent(actor.anchor, false);
            var c = go.AddComponent<Cape>();
            c.actor = actor;
            float s = actor.def.scale;
            c.pin = actor.Bone(pinBone);
            c.pinLocal = new Vector3[c.cols];
            for (int i = 0; i < c.cols; i++)
            {
                var at = Vector3.Lerp(left, right, i / (float)(c.cols - 1));
                c.pinLocal[i] = c.pin.InverseTransformPoint(t.rig.TransformPoint(t.FromTailor(at)));
            }
            float topWidth = (right - left).magnitude * s;
            c.seg = length * s / (c.rows - 1);
            c.across = new float[c.rows];
            for (int r = 0; r < c.rows; r++) c.across[r] = Mathf.Lerp(topWidth, hemWidth * s, r / (float)(c.rows - 1)) / (c.cols - 1);
            c.p = new Vector3[c.cols * c.rows];
            c.prev = new Vector3[c.cols * c.rows];

            var limbs = new System.Collections.Generic.List<(Transform, Transform, float)>();
            void Limb(string a, string b, float r)
            {
                var ta = actor.Bone(a);
                var tb = actor.Bone(b);
                if (ta && tb) limbs.Add((ta, tb, r * s));
            }
            Limb("pelvis", "spine_03", 0.19f);
            Limb("spine_03", "Head", 0.14f);
            Limb("thigh_l", "calf_l", 0.12f);
            Limb("thigh_r", "calf_r", 0.12f);
            Limb("calf_l", "foot_l", 0.09f);
            Limb("calf_r", "foot_r", 0.09f);
            c.body = limbs.ToArray();

            c.mesh = new Mesh { name = "Cape" };
            c.mesh.MarkDynamic();
            c.mesh.vertices = c.p;
            var cols = new Color[c.p.Length];
            for (int i = 0; i < cols.Length; i++) cols[i] = colour.linear;
            c.mesh.colors = cols;
            var tri = new System.Collections.Generic.List<int>();
            for (int r = 0; r < c.rows - 1; r++)
                for (int k = 0; k < c.cols - 1; k++)
                {
                    int a = r * c.cols + k, b = a + 1, d = a + c.cols, e = d + 1;
                    tri.Add(a); tri.Add(d); tri.Add(b); tri.Add(b); tri.Add(d); tri.Add(e);
                }
            c.mesh.triangles = tri.ToArray();
            go.AddComponent<MeshFilter>().sharedMesh = c.mesh;
            var mr = go.AddComponent<MeshRenderer>();
            var mat = new Material(ModelLibrary.I.material);
            mat.SetFloat("_Cull", 0);
            mat.SetFloat("_Both", 1);
            mr.sharedMaterial = mat;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            actor.parts.Add(mr);
            return c;
        }

        Vector3 Local(Vector3 world) => actor.anchor.InverseTransformPoint(world);

        void OnEnable() => hung = false;

        void Hang()
        {
            for (int k = 0; k < cols; k++)
            {
                var top = Local(pin.TransformPoint(pinLocal[k]));
                float spread = (k - (cols - 1) * 0.5f);
                for (int r = 0; r < rows; r++)
                {
                    int i = r * cols + k;
                    p[i] = prev[i] = top + new Vector3(spread * (across[r] - across[0]), -seg * r, -0.02f * r);
                }
            }
            hung = true;
        }

        void LateUpdate()
        {
            if (!hung) Hang();
            float dt = Mathf.Min(Time.deltaTime, 0.05f);
            if (dt > 0.0001f)
            {
                int steps = Mathf.Clamp(Mathf.CeilToInt(dt * 90f), 1, 4);
                float h = dt / steps;
                var v = Vector2.ClampMagnitude(actor.velocity, 12f);
                var wind = new Vector3(-v.x, 0, -v.y);
                for (int s = 0; s < steps; s++) Step(h, wind);
            }
            mesh.vertices = p;
            mesh.RecalculateNormals();
            mesh.RecalculateBounds();
        }

        void Step(float h, Vector3 wind)
        {
            for (int k = 0; k < cols; k++) p[k] = prev[k] = Local(pin.TransformPoint(pinLocal[k]));
            if (limbA == null) { limbA = new Vector3[body.Length]; limbB = new Vector3[body.Length]; }
            for (int j = 0; j < body.Length; j++) { limbA[j] = Local(body[j].a.position); limbB[j] = Local(body[j].b.position); }
            var fall = new Vector3(0, -gravity * actor.def.scale, 0);
            for (int i = cols; i < p.Length; i++)
            {
                var vel = (p[i] - prev[i]) * damping;
                var acc = fall + (wind - vel / h) * drag;
                prev[i] = p[i];
                p[i] += vel + acc * h * h;
            }
            for (int pass = 0; pass < 3; pass++)
            {
                for (int r = 1; r < rows; r++)
                    for (int k = 0; k < cols; k++)
                        Hold(r * cols + k, (r - 1) * cols + k, seg, r == 1, true);
                for (int r = 1; r < rows; r++)
                    for (int k = 0; k < cols - 1; k++)
                        Hold(r * cols + k, r * cols + k + 1, across[r], false, false);
                for (int i = cols; i < p.Length; i++)
                {
                    for (int j = 0; j < body.Length; j++)
                    {
                        Vector3 pa = limbA[j], ab = limbB[j] - pa;
                        float rad = body[j].r;
                        float k = Mathf.Clamp01(Vector3.Dot(p[i] - pa, ab) / Mathf.Max(0.0001f, ab.sqrMagnitude));
                        var off = p[i] - (pa + ab * k);
                        float d = off.magnitude;
                        if (d < rad && d > 0.0001f) p[i] += off / d * (rad - d);
                    }
                    if (p[i].y < 0.03f) p[i].y = 0.03f;
                }
            }
        }

        /// <summary>Keeps two points of the cloth a set distance apart (cloth doesn't stretch; it may bunch sideways).</summary>
        void Hold(int i, int j, float rest, bool jFixed, bool stiff)
        {
            var d = p[i] - p[j];
            float len = d.magnitude;
            if (len < 0.0001f) return;
            if (!stiff && len < rest) return;
            var fix = d * ((len - rest) / len);
            if (jFixed) p[i] -= fix;
            else { p[i] -= fix * 0.5f; p[j] += fix * 0.5f; }
        }
    }

    /// <summary>Something held by a handle that swings under its own weight: the Wakefire in Azar's fist.</summary>
    public class Dangle : MonoBehaviour
    {
        public ModelActor actor;
        public Transform hand;
        public Vector3 grip;            // in the hand's own space
        public float length = 0.3f, drag = 2.2f, gravity = 9.8f, damping = 0.99f;
        Vector3 bob, prev;
        bool hung;

        void OnEnable() => hung = false;

        void LateUpdate()
        {
            var top = actor.anchor.InverseTransformPoint(hand.TransformPoint(grip));
            if (!hung) { bob = prev = top + Vector3.down * length; hung = true; }
            float dt = Mathf.Min(Time.deltaTime, 0.05f);
            if (dt > 0.0001f)
            {
                int steps = Mathf.Clamp(Mathf.CeilToInt(dt * 90f), 1, 4);
                float h = dt / steps;
                var v = Vector2.ClampMagnitude(actor.velocity, 12f);
                var wind = new Vector3(-v.x, 0, -v.y);
                for (int s = 0; s < steps; s++)
                {
                    var vel = (bob - prev) * damping;
                    var acc = new Vector3(0, -gravity * actor.def.scale, 0) + (wind * 0.35f - vel / h) * drag;
                    prev = bob;
                    bob += vel + acc * h * h;
                    var d = bob - top;
                    if (d.sqrMagnitude > 0.000001f) bob = top + d.normalized * length;
                }
            }
            transform.localPosition = top;
            transform.localRotation = Quaternion.FromToRotation(Vector3.down, (bob - top).normalized);
        }
    }

    /// <summary>The streak a blade leaves in the air: a ribbon swept out by its edge over the last tenth
    /// of a second, white-hot where it is now and cooling to ember behind.</summary>
    public class Trail : MonoBehaviour
    {
        public ModelActor actor;
        public string from = "blade0", to = "blade1";
        public float life = 0.10f;
        public bool on;
        const int Max = 16;
        readonly Vector3[] a = new Vector3[Max], b = new Vector3[Max];
        readonly float[] born = new float[Max];
        int count;
        Mesh mesh;
        readonly System.Collections.Generic.List<Vector3> v = new System.Collections.Generic.List<Vector3>();
        readonly System.Collections.Generic.List<Color> c = new System.Collections.Generic.List<Color>();
        readonly System.Collections.Generic.List<int> t = new System.Collections.Generic.List<int>();
        static readonly Color Hot = new Color(1f, 0.97f, 0.84f), Warm = new Color(1f, 0.78f, 0.34f), Ember = new Color(0.92f, 0.42f, 0.16f);

        public static Trail Make(ModelActor actor)
        {
            var go = new GameObject("Trail");
            go.layer = ModelStage.Layer;
            go.transform.SetParent(actor.anchor, false);
            var tr = go.AddComponent<Trail>();
            tr.actor = actor;
            tr.mesh = new Mesh { name = "Trail" };
            tr.mesh.MarkDynamic();
            go.AddComponent<MeshFilter>().sharedMesh = tr.mesh;
            var mr = go.AddComponent<MeshRenderer>();
            var mat = new Material(ModelLibrary.I.material);
            mat.SetFloat("_Cull", 0);
            mat.SetFloat("_Glow", 1);
            mr.sharedMaterial = mat;
            mr.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
            return tr;
        }

        void OnEnable() => count = 0;

        void LateUpdate()
        {
            float now = Time.time;
            on = actor.anim != null && actor.anim.StartsWith("attack") && actor.norm > 0.10f && actor.norm < 0.74f;
            int drop = 0;
            while (drop < count && now - born[drop] > life) drop++;
            if (drop > 0)
            {
                for (int i = drop; i < count; i++) { a[i - drop] = a[i]; b[i - drop] = b[i]; born[i - drop] = born[i]; }
                count -= drop;
            }
            if (on && actor.marks.TryGetValue(from, out var m0) && actor.marks.TryGetValue(to, out var m1))
            {
                var pa = actor.anchor.InverseTransformPoint(m0.bone.TransformPoint(m0.at));
                var pb = actor.anchor.InverseTransformPoint(m1.bone.TransformPoint(m1.at));
                if (count == 0 || (pb - b[count - 1]).sqrMagnitude > 0.0004f)
                {
                    if (count == Max) { for (int i = 1; i < count; i++) { a[i - 1] = a[i]; b[i - 1] = b[i]; born[i - 1] = born[i]; } count--; }
                    a[count] = pa; b[count] = pb; born[count] = now; count++;
                }
            }
            v.Clear(); c.Clear(); t.Clear();
            for (int i = 0; i + 1 < count; i++)
            {
                float age0 = Mathf.Clamp01((now - born[i]) / life), age1 = Mathf.Clamp01((now - born[i + 1]) / life);
                // the streak thins towards its tail: its inner edge closes on the tip
                var i0 = Vector3.Lerp(a[i], b[i], 0.25f + age0 * 0.7f);
                var i1 = Vector3.Lerp(a[i + 1], b[i + 1], 0.25f + age1 * 0.7f);
                var col = (age1 < 0.3f ? Hot : age1 < 0.65f ? Warm : Ember).linear;
                int k = v.Count;
                v.Add(i0); v.Add(b[i]); v.Add(b[i + 1]); v.Add(i1);
                for (int q = 0; q < 4; q++) c.Add(col);
                t.Add(k); t.Add(k + 1); t.Add(k + 2); t.Add(k); t.Add(k + 2); t.Add(k + 3);
            }
            mesh.Clear();
            if (v.Count > 0)
            {
                mesh.SetVertices(v);
                mesh.SetColors(c);
                mesh.SetTriangles(t, 0);
                mesh.RecalculateNormals();
                mesh.RecalculateBounds();
            }
        }
    }
}
