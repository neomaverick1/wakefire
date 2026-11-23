// A character played by a rigged 3D model instead of drawn frames. The model stands on the
// model stage; this component picks its clip, blends from the last one, turns it to face where
// the actor is heading, leans it into its own acceleration, and tells the actor's sprite
// renderer which square of the stage sheet to draw. SpriteAnim stays the clock: frame counts
// and frame events (the moment a blade lands, a footfall) work exactly as they did with sprites.
using System;
using System.Collections.Generic;
using UnityEngine;
using UnityEngine.Animations;
using UnityEngine.Playables;

namespace Wakefire
{
    public class ModelActor : MonoBehaviour
    {
        public ModelDef def;
        public SpriteRenderer sr;
        public Transform anchor;            // the square of the stage this model stands in, tipped to the camera
        public Transform turn;              // turns and leans the body inside it
        public Transform rig;               // the model itself
        public Animator animator;
        public float yaw = 180f, yawTarget = 180f, turnRate = 1100f;
        public Vector2 lean;                // degrees the body tips, in world x and y
        public Vector2 velocity;            // world units a second: cloth and loose gear trail behind it, strides keep pace with it
        public bool ownVelocity;            // the owner sets velocity itself (Azar); otherwise it is measured from how the actor moves
        Vector2 lastSpot;
        bool spotted;
        /// <summary>This actor's square of the stage sheet (uv origin and size), or zero while it has none.</summary>
        public Vector4 Cell => square >= 0 ? ModelStage.I.Rect(square, def.span) : Vector4.zero;
        /// <summary>The clip stretch showing now.</summary>
        public ClipMap Current => maps[cur];
        public float height;                // lifted off the ground (a jump, a hop), world units
        public string anim;
        public float norm;                  // how far through the sprite frames the actor is, 0..1
        public float clipTime;              // seconds into the clip being shown
        public readonly Dictionary<string, Transform> bones = new Dictionary<string, Transform>();
        public readonly List<Renderer> parts = new List<Renderer>();
        public readonly Dictionary<string, Transform> props = new Dictionary<string, Transform>();   // things carried: "lantern"...
        public readonly Dictionary<string, (Transform bone, Vector3 at)> marks = new Dictionary<string, (Transform, Vector3)>();   // points on the body: "blade0", "blade1"
        readonly List<Material> lit = new List<Material>();     // every material of every part, gathered once
        int litParts = -1;
        Vector3 fireDir = Vector3.up;
        float fireAmount;
        Color fireColour = new Color(1f, 0.62f, 0.26f);
        SpriteRenderer shadow;
        bool lookedForShadow;
        MaterialPropertyBlock shadowBlock;
        /// <summary>After the clip has posed the skeleton: gestures, cloth and carried things go on top.</summary>
        public event Action<ModelActor, float> Posed;

        PlayableGraph graph;
        AnimationMixerPlayable mixer;
        readonly AnimationClipPlayable[] play = new AnimationClipPlayable[2];
        readonly bool[] has = new bool[2];
        readonly ClipMap[] maps = new ClipMap[2];
        readonly float[] clock = new float[2];
        readonly float[] shown = new float[2];
        int cur;
        float blend = 1f;
        int square = -1;
        MaterialPropertyBlock mpb;
        bool dirty = true;
        float lastYaw = 999f;
        Vector2 lastLean;

        IPoser poser;
        int worldLayer = -1;
        static readonly int FireId = Shader.PropertyToID("_Fire"), FireColorId = Shader.PropertyToID("_FireColor");
        static readonly int ModelId = Shader.PropertyToID("_Model"), CellId = Shader.PropertyToID("_Cell");

        public static ModelActor Attach(SpriteAnim a, ModelDef def)
        {
            var lib = ModelLibrary.I;
            var prefab = lib && def.build == null ? lib.Prefab(def.model) : null;
            if (!prefab && def.build == null) return null;
            var stage = ModelStage.Ensure();
            var m = a.gameObject.AddComponent<ModelActor>();
            m.def = def;
            m.sr = a.sr;
            m.sr.sprite = ModelStage.Blank(def.span);
            m.sr.flipX = false;
            m.mpb = new MaterialPropertyBlock();

            var anchorGo = new GameObject("Model " + a.transform.parent?.name);
            anchorGo.transform.SetParent(stage.transform, false);
            m.anchor = anchorGo.transform;
            m.anchor.localRotation = Quaternion.Euler(-ModelStage.Pitch, 0, 0);
            var turnGo = new GameObject("Turn");
            turnGo.transform.SetParent(m.anchor, false);
            m.turn = turnGo.transform;
            if (def.build != null)
            {
                var made = new GameObject("Rig");
                made.layer = ModelStage.Layer;
                made.transform.SetParent(m.turn, false);
                m.rig = made.transform;
                m.rig.localScale = Vector3.one * def.scale;
                m.poser = def.build(m);
                foreach (var t in made.GetComponentsInChildren<Transform>(true)) t.gameObject.layer = ModelStage.Layer;
                m.anchor.gameObject.SetActive(false);
                return m;
            }
            var inst = Instantiate(prefab, m.turn, false);
            inst.name = def.model;
            m.rig = inst.transform;
            m.rig.localPosition = Vector3.zero;
            m.rig.localRotation = Quaternion.identity;
            m.rig.localScale = Vector3.one * def.scale;
            anchorGo.layer = turnGo.layer = ModelStage.Layer;
            foreach (var t in inst.GetComponentsInChildren<Transform>(true))
            {
                t.gameObject.layer = ModelStage.Layer;
                if (!m.bones.ContainsKey(t.name)) m.bones[t.name] = t;
            }
            foreach (var r in inst.GetComponentsInChildren<Renderer>(true))
            {
                m.parts.Add(r);
                r.shadowCastingMode = UnityEngine.Rendering.ShadowCastingMode.Off;
                r.receiveShadows = false;
                r.lightProbeUsage = UnityEngine.Rendering.LightProbeUsage.Off;
                r.reflectionProbeUsage = UnityEngine.Rendering.ReflectionProbeUsage.Off;
                if (r is SkinnedMeshRenderer s) { s.updateWhenOffscreen = true; s.quality = SkinQuality.Bone4; }
                var mats = new Material[r.sharedMaterials.Length];
                for (int i = 0; i < mats.Length; i++) mats[i] = new Material(lib.material);
                r.sharedMaterials = mats;
            }
            m.animator = inst.GetComponent<Animator>();
            if (!m.animator) m.animator = inst.AddComponent<Animator>();
            m.animator.applyRootMotion = false;
            m.animator.cullingMode = AnimatorCullingMode.AlwaysAnimate;
            m.animator.runtimeAnimatorController = null;

            m.graph = PlayableGraph.Create("Model");
            m.graph.SetTimeUpdateMode(DirectorUpdateMode.Manual);
            m.mixer = AnimationMixerPlayable.Create(m.graph, 2);
            var output = AnimationPlayableOutput.Create(m.graph, "pose", m.animator);
            output.SetSourcePlayable(m.mixer);
            m.graph.Play();
            def.dress?.Invoke(m);
            m.anchor.gameObject.SetActive(false);
            return m;
        }

        public Transform Bone(string name) => bones.TryGetValue(name, out var t) ? t : null;

        /// <summary>The character's own frame on the stage: x to their right, y up, z the way they face.</summary>
        public Quaternion Frame => rig.rotation * Quaternion.Euler(0, def.forward, 0);

        /// <summary>Turns one bone on top of whatever the clip gave it, in the character's own terms:
        /// pitch tips it forward (a nodding head, a bowing back; negative lifts an arm to the front),
        /// yaw turns it left or right, roll tips it to the side.</summary>
        public void Bend(string bone, float pitch, float yaw = 0, float roll = 0)
        {
            if (!bones.TryGetValue(bone, out var b)) return;
            var f = Frame;
            b.rotation = Quaternion.AngleAxis(pitch, f * Vector3.right) * Quaternion.AngleAxis(yaw, f * Vector3.up) * Quaternion.AngleAxis(roll, f * Vector3.forward) * b.rotation;
        }

        /// <summary>Seconds this actor has been alive: gestures that breathe or sway keep time by it.</summary>
        public float life;

        /// <summary>How far something on the stage is from the model's feet as the screen shows it (world units).</summary>
        public Vector2 Offset(Vector3 stagePoint) => stagePoint - anchor.position;

        public Material Part(int renderer, int part = 0) => parts[renderer].sharedMaterials[part];

        /// <summary>Which way the body points: a world direction (x right, y up the screen).</summary>
        public void Aim(Vector2 dir, bool snap = false)
        {
            if (dir.sqrMagnitude < 0.0001f) return;
            yawTarget = Mathf.Atan2(dir.x, dir.y) * Mathf.Rad2Deg;
            if (snap) yaw = yawTarget;
        }

        public void Face(Facing f, bool snap = false) =>
            Aim(f == Facing.Down ? Vector2.down : f == Facing.Up ? Vector2.up : f == Facing.Left ? Vector2.left : Vector2.right, snap);

        public void Play(string name, bool restart)
        {
            if (poser != null) { anim = name; return; }
            height = 0;
            var m = def.Map(name);
            if (m == null || !m.asset) return;
            if (!restart && maps[cur] == m && anim == name) return;
            anim = name;
            if (maps[cur] == m && has[cur])
            {
                clock[cur] = 0;          // the same clip again from the top: no blend with itself
                dirty = true;
                return;
            }
            bool first = !has[cur];
            cur = 1 - cur;
            if (has[cur]) { graph.Disconnect(mixer, cur); play[cur].Destroy(); }
            play[cur] = AnimationClipPlayable.Create(graph, m.asset);
            play[cur].SetApplyFootIK(false);
            graph.Connect(play[cur], 0, mixer, cur);
            has[cur] = true;
            maps[cur] = m;
            clock[cur] = 0;
            blend = first || m.fade <= 0 ? 1f : 0f;
            dirty = true;
        }

        /// <summary>Stone does not move: the pose it had stays exactly as it was until this is let go.</summary>
        public bool frozen;

        /// <summary>One game frame: n is how far through the sprite's frames the actor is (0..1).</summary>
        public void Advance(float dt, float n)
        {
            if (frozen) return;
            norm = n;
            life += dt;
            if (!ownVelocity && sr)
            {
                Vector2 spot = sr.transform.parent ? sr.transform.parent.position : sr.transform.position;
                if (spotted && dt > 0.0001f)
                {
                    var v = (spot - lastSpot) / dt;
                    velocity = v.sqrMagnitude > 900f ? Vector2.zero : v;        // a jump across the map isn't a sprint
                }
                lastSpot = spot;
                spotted = true;
            }
            if (poser != null)
            {
                if (square >= 0) poser.Pose(this, anim, n, dt);          // may turn the creature towards where it's going
                yaw = Mathf.MoveTowardsAngle(yaw, yawTarget, turnRate * dt);
                if (square >= 0) turn.localRotation = Quaternion.Euler(0, Mathf.Round(yaw / 7.5f) * 7.5f + def.forward, 0);
                return;
            }
            if (!has[cur]) return;
            var m = maps[cur];
            clock[cur] += dt * m.speed;
            if (blend < 1f) { blend = Mathf.Min(1f, blend + dt / Mathf.Max(0.001f, m.fade)); dirty = true; }
            yaw = Mathf.MoveTowardsAngle(yaw, yawTarget, turnRate * dt);
            if (square < 0) return;

            float t = m.At(n, clock[cur]);
            if (m.step > 0) t = Mathf.Floor(t * m.step + 0.001f) / m.step;
            if (!Mathf.Approximately(t, shown[cur])) { shown[cur] = t; dirty = true; }
            clipTime = t;
            float y = Mathf.Round(yaw / 7.5f) * 7.5f;
            var l = new Vector2(Mathf.Round(lean.x / 2f) * 2f, Mathf.Round(lean.y / 2f) * 2f);
            if (y != lastYaw || l != lastLean) { lastYaw = y; lastLean = l; dirty = true; }
            if (!dirty && Posed == null && m.pose == null) return;

            play[cur].SetTime(t);
            float w = Mathf.Round(blend * 4f) / 4f;
            mixer.SetInputWeight(cur, has[1 - cur] ? w : 1f);
            if (has[1 - cur]) mixer.SetInputWeight(1 - cur, 1f - w);
            graph.Evaluate(0f);
            Stand(y, l);
            m.pose?.Invoke(this, n);
            Posed?.Invoke(this, dt);
            dirty = false;
        }

        void Stand(float y, Vector2 l)
        {
            var tip = Quaternion.identity;
            if (l.sqrMagnitude > 0.01f)
            {
                var dir = new Vector3(l.x, 0, l.y).normalized;
                var axis = Vector3.Cross(Vector3.up, dir);
                tip = Quaternion.AngleAxis(l.magnitude, axis);
                if (Vector3.Dot(tip * Vector3.up, dir) < 0) tip = Quaternion.AngleAxis(-l.magnitude, axis);
            }
            var map = maps[cur];
            turn.localRotation = tip * Quaternion.Euler(0, y + def.forward + (map != null ? map.yaw : 0), 0);
            rig.localPosition = map != null ? map.nudge * def.scale : Vector3.zero;
        }

        void LateUpdate()
        {
            var view = PixelView.I;
            bool want = sr && view;
            if (want)
            {
                Vector2 c = view.world.transform.position, p = sr.transform.position;
                float hw = view.width / (2f * PixelView.PPU) + 5f * def.span, hh = PixelView.Height / (2f * PixelView.PPU) + 6f * def.span;
                want = Mathf.Abs(p.x - c.x) < hw && Mathf.Abs(p.y - c.y) < hh;
                // someone who only exists in the other world isn't posed at all, unless the ring is passing
                if (want && Dream.I && !Dream.I.Sweeping)
                {
                    if (worldLayer < 0) worldLayer = sr.sharedMaterial && sr.sharedMaterial.HasProperty("_Layer") ? Mathf.RoundToInt(sr.sharedMaterial.GetFloat("_Layer")) : 0;
                    if (worldLayer != 0 && Dream.I.IsDreamAt(p) != (worldLayer == 2)) want = false;
                }
            }
            if (want && square < 0)
            {
                square = ModelStage.I.Take(this, def.span);
                if (square >= 0)
                {
                    anchor.gameObject.SetActive(true);
                    dirty = true;
                    Advance(0, norm);
                }
            }
            else if (!want && square >= 0)
            {
                ModelStage.I.Give(this);
                square = -1;
                anchor.gameObject.SetActive(false);
            }
            if (square >= 0)
                anchor.localPosition = ModelStage.I.Feet(square, def.span) + new Vector3(0, Mathf.Round(height * PixelView.PPU) / PixelView.PPU, 0);
            if (!sr) return;
            if (square >= 0) Firelight();
            var cell = square >= 0 ? ModelStage.I.Rect(square, def.span) : Vector4.zero;
            sr.GetPropertyBlock(mpb);
            mpb.SetFloat(ModelId, 1f);
            mpb.SetVector(CellId, cell);
            sr.SetPropertyBlock(mpb);

            // the round blob under the actor becomes a real shadow of the figure
            if (!lookedForShadow && sr.transform.parent)
            {
                var found = sr.transform.parent.Find("Shadow");
                if (found)
                {
                    lookedForShadow = true;
                    shadow = found.GetComponent<SpriteRenderer>();
                    shadow.sprite = ModelStage.Blank(def.span);
                    var shadeMat = Map.ShadeMat(Mathf.RoundToInt(shadow.sharedMaterial ? shadow.sharedMaterial.GetFloat("_Layer") : 0));
                    if (shadeMat) shadow.sharedMaterial = shadeMat;
                    shadowBlock = new MaterialPropertyBlock();
                }
            }
            if (shadow)
            {
                shadow.GetPropertyBlock(shadowBlock);
                shadowBlock.SetFloat(ModelId, 1f);
                shadowBlock.SetVector(CellId, cell);
                shadow.SetPropertyBlock(shadowBlock);
            }
        }

        /// <summary>A light this figure carries itself (Azar's lantern): it lights the ground, not the hand that holds it.</summary>
        public LightBlob ownLight;

        /// <summary>The strongest fire near the actor lights the side of the model that faces it.</summary>
        void Firelight()
        {
            Vector2 here = (Vector2)(sr.transform.parent ? sr.transform.parent.position : sr.transform.position) + new Vector2(0, 0.8f);
            float best = 0;
            Vector2 towards = Vector2.up;
            Color colour = fireColour;
            foreach (var l in LightBlob.All)
            {
                if (!l || l.radius <= 0.1f || l == ownLight) continue;
                Vector2 d = (Vector2)l.transform.position - here;
                float k = l.intensity * Mathf.Clamp01(1f - d.magnitude / (l.radius * 0.95f));
                if (k > best) { best = k; towards = d; colour = l.color; }
            }
            float dt = Time.deltaTime;
            var want = anchor.TransformDirection(new Vector3(towards.x, 0.5f, towards.y).normalized);
            fireDir = Vector3.Slerp(fireDir, want, 1f - Mathf.Exp(-8f * dt));
            fireAmount = Mathf.Lerp(fireAmount, Mathf.Clamp01(best * 1.25f), 1f - Mathf.Exp(-6f * dt));
            fireColour = Color.Lerp(fireColour, colour, 1f - Mathf.Exp(-6f * dt));
            var v = new Vector4(fireDir.x, fireDir.y, -fireDir.z, Mathf.Round(fireAmount * 5f) / 5f);     // view space looks down -z
            if (litParts != parts.Count)
            {
                litParts = parts.Count;
                lit.Clear();
                foreach (var r in parts)
                    if (r) foreach (var m in r.sharedMaterials) if (m && !lit.Contains(m)) lit.Add(m);
            }
            for (int i = 0; i < lit.Count; i++)
            {
                lit[i].SetVector(FireId, v);
                lit[i].SetColor(FireColorId, fireColour);
            }
        }

        void OnDestroy()
        {
            if (poser == null && graph.IsValid()) graph.Destroy();
            if (ModelStage.I) ModelStage.I.Give(this);
            if (anchor) Destroy(anchor.gameObject);
        }
    }
}
