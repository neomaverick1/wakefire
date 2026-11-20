// Azar. Tight 8-way movement with 4-way facing, a three-hit khopesh combo with a buffered
// next swing, a dodge roll with invulnerable frames, nodding off into the dream and back,
// holding out the Wakefire to light braziers, and talking to whoever is in front of him.
using System;
using UnityEngine;

namespace Wakefire
{
    public class Player : MonoBehaviour
    {
        public static Player I;
        public enum State { Free, Attack, Roll, Nod, Use, Hurt, Dead, Talk, Cutscene, ItemGet }

        public State state = State.Free;
        public Vector2 pos;
        public Facing facing = Facing.Down;
        public SpriteAnim anim;
        public Health health;
        public float speed = 5.4f;
        public Vector2 half = new Vector2(0.32f, 0.16f);
        public int coins, keys;
        public bool hasShield;
        public LightBlob lantern;

        int combo;
        bool queued;
        float stateClock, rollCd, idleClock, hurtFlash, skidClock;
        Vector2 vel, knock, rollDir, lastVel;
        const float RollTime = 0.42f;
        SpriteRenderer shadow;
        public event Action<Prop> Interacted;
        public event Action Fell;
        public void Notify(Prop p) => Interacted?.Invoke(p);

        public static Player Spawn(Vector2 at)
        {
            var go = new GameObject("Azar");
            var p = go.AddComponent<Player>();
            I = p;
            p.pos = at;
            var body = new GameObject("Sprite");
            body.transform.SetParent(go.transform, false);
            var sr = body.AddComponent<SpriteRenderer>();
            sr.sharedMaterial = new Material(Map.SpriteMat);
            sr.sharedMaterial.SetFloat("_DreamKeep", 0.8f);      // the dream changes around him, not him
            p.anim = body.AddComponent<SpriteAnim>();
            p.anim.sr = sr;
            p.anim.sheet = SpriteSheet.Load("azar");
            p.anim.Play("idle", Facing.Down, true);
            p.anim.FrameChanged += p.OnFrame;
            p.health = go.AddComponent<Health>();
            p.health.max = 6;
            p.health.hp = 6;
            p.shadow = MakeShadow(go.transform);
            p.lantern = LightBlob.Create(go.transform, at, 3.6f, new Color(1f, 0.78f, 0.42f), 0.6f, true);
            p.lantern.height = 0.7f;
            Dream.I.ForcedWake += p.OnForcedWake;
            p.Place();
            return p;
        }

        static SpriteRenderer MakeShadow(Transform parent)
        {
            var t = new Texture2D(12, 5) { filterMode = FilterMode.Point };
            for (int y = 0; y < 5; y++)
                for (int x = 0; x < 12; x++)
                {
                    float dx = (x + 0.5f - 6) / 6f, dy = (y + 0.5f - 2.5f) / 2.5f;
                    bool inside = dx * dx + dy * dy <= 1f;
                    t.SetPixel(x, y, inside && ((x + y) % 2 == 0 || dx * dx + dy * dy < 0.4f) ? new Color(0.05f, 0.06f, 0.12f, 1) : Color.clear);
                }
            t.Apply();
            var go = new GameObject("Shadow");
            go.transform.SetParent(parent, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = Sprite.Create(t, new Rect(0, 0, 12, 5), new Vector2(0.5f, 0.5f), 16f);
            sr.sharedMaterial = Map.SpriteMat;
            return sr;
        }

        Vector2 Dir => facing == Facing.Down ? Vector2.down : facing == Facing.Up ? Vector2.up : facing == Facing.Left ? Vector2.left : Vector2.right;

        static Facing FacingOf(Vector2 v, Facing current)
        {
            if (v.sqrMagnitude < 0.01f) return current;
            bool horiz = Mathf.Abs(v.x) > Mathf.Abs(v.y) + 0.05f;
            bool vert = Mathf.Abs(v.y) > Mathf.Abs(v.x) + 0.05f;
            // on diagonals keep the current facing if it's one of the two
            if (!horiz && !vert)
            {
                if ((current == Facing.Left && v.x < 0) || (current == Facing.Right && v.x > 0) ||
                    (current == Facing.Up && v.y > 0) || (current == Facing.Down && v.y < 0)) return current;
                horiz = true;
            }
            if (horiz) return v.x < 0 ? Facing.Left : Facing.Right;
            return v.y < 0 ? Facing.Down : Facing.Up;
        }

        void Update()
        {
            if (Game.Paused) return;
            float dt = Time.deltaTime;
            stateClock += dt;
            rollCd -= dt;
            var input = Controls.MoveVector;

            switch (state)
            {
                case State.Free:
                    FreeUpdate(input, dt);
                    break;
                case State.Attack:
                    vel = Vector2.Lerp(vel, Vector2.zero, dt * 14f);
                    if (Controls.Down(Controls.Attack)) queued = true;
                    if (input.sqrMagnitude > 0.2f && anim.Frame <= 1) facing = FacingOf(input, facing);
                    if (anim.Done)
                    {
                        if (queued && combo < 3) StartAttack();
                        else { combo = 0; ToFree(); }
                    }
                    else if (Controls.Down(Controls.Roll) && anim.Frame >= 3 && rollCd <= 0) StartRoll(input);
                    break;
                case State.Roll:
                {
                    // thrown forward hard, carried over the shoulder, slowing as he comes back to his feet
                    float k = Mathf.Clamp01(stateClock / RollTime);
                    vel = rollDir * Mathf.Lerp(10.4f, 3.4f, k);
                    if (stateClock > 0.08f && stateClock < 0.36f) health.invulnerable = Mathf.Max(health.invulnerable, 0.05f);
                    if (anim.Frame % 3 == 0) Fx.Dust(pos, 1);
                    if (anim.Done) { rollCd = 0.12f; ToFree(); }
                    break;
                }
                case State.Nod:
                case State.Use:
                    vel = Vector2.zero;
                    if (anim.Done) ToFree();
                    break;
                case State.Hurt:
                    vel = knock;
                    knock = Vector2.Lerp(knock, Vector2.zero, dt * 10f);
                    if (stateClock > 0.3f) ToFree();
                    break;
                case State.Talk:
                case State.Cutscene:
                case State.ItemGet:
                case State.Dead:
                    vel = Vector2.zero;
                    break;
            }

            var before = pos;
            pos = Solids.Move(pos, vel * dt, half, this);
            CheckGround();
            if (anim.model)
            {
                var m = anim.model;
                m.ownVelocity = true;
                m.velocity = dt > 0.0001f ? (pos - before) / dt : Vector2.zero;
                if (m.props.TryGetValue("shield", out var mirror) && mirror.gameObject.activeSelf != hasShield) mirror.gameObject.SetActive(hasShield);
                // the body points where it's going, not just four ways, and tips into its own acceleration
                if (state == State.Free && vel.sqrMagnitude > 0.5f) m.Aim(vel);
                else if (state == State.Roll) m.Aim(rollDir);
                var push = state == State.Free && dt > 0.0001f ? Vector2.ClampMagnitude((vel - lastVel) / dt * 0.17f, 10f) : Vector2.zero;
                m.lean = Vector2.Lerp(m.lean, push, 1f - Mathf.Exp(-12f * dt));
            }
            lastVel = vel;
            // the camera looks a little ahead of where he's heading
            var view = PixelView.I;
            if (view && view.target == transform)
                view.lookAhead = Vector2.Lerp(view.lookAhead, state == State.Free || state == State.Roll ? vel * 0.14f : Vector2.zero, 1f - Mathf.Exp(-2.5f * dt));
            anim.Tick(dt);
            Place();

            if (hurtFlash > 0)
            {
                hurtFlash -= dt;
                anim.sr.enabled = hurtFlash <= 0 || ((int)(hurtFlash * 20) % 2 == 0);
            }
            else anim.sr.enabled = true;
        }

        void FreeUpdate(Vector2 input, float dt)
        {
            bool moving = input.sqrMagnitude > 0.01f;
            // weight: a short run-up, a short slide to a stop, a skid when he doubles back
            var want = input * speed;
            var was = vel;
            float grip = !moving ? 44f : Vector2.Dot(vel, want) < 0 ? 78f : 54f;
            vel = Vector2.MoveTowards(vel, want, grip * dt);
            skidClock -= dt;
            if (moving && was.sqrMagnitude > 14f && Vector2.Dot(was.normalized, input.normalized) < -0.5f && skidClock <= 0)
            {
                Fx.Dust(pos, 3);
                skidClock = 0.3f;
            }
            if (moving)
            {
                facing = FacingOf(input, facing);
                var block = PropInFront(0.45f, p => p.Kind == "block");
                bool leaning = block != null && Vector2.Dot(input.normalized, Dir) > 0.8f && Solids.Overlaps(new Rect(pos - half + Dir * 0.12f, half * 2), pos, this);
                if (leaning)
                {
                    vel = want;
                    pushClock += dt;
                    anim.Play("push", facing);
                    anim.SetFacing(facing);
                    if (pushClock > 0.38f && block.Slide(Dir)) { pushClock = 0; Sfx.Play("block_push"); }
                    return;
                }
                pushClock = 0;
                anim.Play("run", facing);
                anim.SetFacing(facing);
                idleClock = 0;
                if (anim.Frame == 2 || anim.Frame == 6) { if (stepPuff) { Fx.Dust(pos, 1); Sfx.Play(StepSound(anim.Frame == 2 ? 0 : 1), 0.32f, 0.08f); stepPuff = false; } }
                else stepPuff = true;
            }
            else if (vel.sqrMagnitude > 1.2f && anim.anim == "run")
            {
                idleClock = 0;                    // still carrying speed: the last strides shorten
            }
            else
            {
                idleClock += dt;
                if (anim.anim == "yawn" || anim.anim == "idle_nod")
                {
                    if (anim.Done) anim.Play("idle", facing, true);
                }
                else
                {
                    anim.Play("idle", facing);
                    if (idleClock > 7f && facing == Facing.Down) { anim.Play(UnityEngine.Random.value < 0.6f ? "idle_nod" : "yawn", facing, true); idleClock = 0; }
                }
            }
            if (Controls.Down(Controls.Attack)) { combo = 0; StartAttack(); return; }
            if (Controls.Down(Controls.Roll) && rollCd <= 0) { StartRoll(input); return; }
            if (Controls.Down(Controls.Nod)) { StartNod(); return; }
            if (Controls.Down(Controls.Item)) { StartUse(); return; }
            if (Controls.Down(Controls.Interact)) TryInteract();
        }

        bool stepPuff;
        float pushClock;
        public Vector2 lastSafe;

        /// <summary>Standing over water or a drop when the dream gives out means going in.</summary>
        void CheckGround()
        {
            if (state == State.Dead || state == State.Cutscene) return;
            var feet = new Rect(pos - new Vector2(0.12f, 0.06f), new Vector2(0.24f, 0.12f));
            bool overPit = false, falling = false;
            bool dream = Dream.I && Dream.I.IsDreamAt(pos);
            foreach (var s in Solids.All)
            {
                if (!s.pit || !s.enabled || !s.r.Overlaps(feet)) continue;
                overPit = true;
                if (s.layer == WorldLayer.Both || (s.layer == WorldLayer.Waking) != dream) falling = true;
            }
            if (!overPit && state == State.Free) lastSafe = pos;
            if (falling) StartCoroutine(Fall());
        }

        System.Collections.IEnumerator Fall()
        {
            state = State.Cutscene;
            vel = Vector2.zero;
            Sfx.Play("fall");
            var t0 = anim.sr.transform.localScale;
            for (float t = 0; t < 0.45f; t += Time.deltaTime)
            {
                float k = 1 - t / 0.45f;
                anim.sr.transform.localScale = new Vector3(k, k, 1);
                anim.sr.transform.Rotate(0, 0, 600 * Time.deltaTime);
                yield return null;
            }
            anim.sr.transform.localScale = t0;
            anim.sr.transform.localRotation = Quaternion.identity;
            Fx.Spawn(pos, Vector2.zero, 0, 0, 0.01f, Color.clear, Color.clear);
            pos = lastSafe;
            Place();
            Fell?.Invoke();
            health.hp = Mathf.Max(0, health.hp - 1);
            hurtFlash = 1f;
            health.invulnerable = 1f;
            state = health.Dead ? State.Dead : State.Free;
            if (health.Dead) anim.Play("death", Facing.Down, true);
            else anim.Play("idle", facing, true);
        }

        /// <summary>With the mirror shield, fire coming at Azar's face goes back where it came from.</summary>
        public bool TryReflect(Vector2 incomingDir)
        {
            if (!hasShield) return false;
            if (state != State.Free && state != State.Use && state != State.Talk) return false;
            if (Vector2.Dot(-incomingDir.normalized, Dir) < 0.6f) return false;
            if (state == State.Free) anim.Play("block", facing, true);
            Sfx.Play("reflect");
            Fx.Sparks(pos + Dir * 0.5f + new Vector2(0, 0.6f), new Color(1f, 0.9f, 0.6f), 8);
            return true;
        }

        void ToFree()
        {
            state = State.Free;
            stateClock = 0;
            anim.Play(Controls.MoveVector.sqrMagnitude > 0.01f ? "run" : "idle", facing, true);
        }

        void StartAttack()
        {
            combo++;
            queued = false;
            state = State.Attack;
            stateClock = 0;
            var input = Controls.MoveVector;
            facing = FacingOf(input, facing);
            vel = Dir * (combo == 3 ? 3.2f : 2.0f);
            anim.Play("attack" + combo, facing, true);
            Sfx.Play("swing" + combo);
        }

        void StartRoll(Vector2 input)
        {
            rollDir = input.sqrMagnitude > 0.04f ? input.normalized : Dir;      // any of the ways the stick points, not just four
            facing = FacingOf(rollDir, facing);
            state = State.Roll;
            stateClock = 0;
            anim.Play("roll", facing, true);
            Fx.Dust(pos, 4);
            Sfx.Play("roll");
        }

        /// <summary>For test runs: nod off (or wake) as if the button were pressed.</summary>
        public void NodOff() { if (state == State.Free) StartNod(); }

        /// <summary>The meter ran dry: Azar's eyes snap open wherever he is.</summary>
        void OnForcedWake()
        {
            if (!Dream.I.Dreaming || state == State.Nod || state == State.Dead || state == State.Cutscene) return;
            state = State.Nod;
            stateClock = 0;
            vel = Vector2.zero;
            anim.Play("wake", facing == Facing.Up ? Facing.Down : facing, true);
            Sfx.Play("wake_forced");
        }

        void StartNod()
        {
            var d = Dream.I;
            if (!d.Dreaming && (d.Locked || d.Drowsiness < 0.15f)) { Sfx.Play("deny"); return; }
            state = State.Nod;
            stateClock = 0;
            anim.Play(d.Dreaming ? "wake" : "nod", facing == Facing.Up ? Facing.Down : facing, true);
        }

        void StartUse()
        {
            state = State.Use;
            stateClock = 0;
            anim.Play("use", facing, true);
        }

        void OnFrame(string a, int f)
        {
            if (a.StartsWith("attack") && f == (a == "attack3" ? 3 : 2)) Strike(a == "attack3");
            if (a == "nod" && f == 2) { Dream.I.Flip(pos, true); Sfx.Play("dream_in"); }
            if (a == "wake" && f == 1) { Dream.I.Flip(pos, false); Sfx.Play("dream_out"); }
            if (a == "use" && f == 1) UseLantern();
        }

        Prop PropInFront(float reach, Func<Prop, bool> filter)
        {
            var map = Map.Current;
            if (!map) return null;
            var p = pos + Dir * reach + new Vector2(0, 0.1f);
            var r = new Rect(p - new Vector2(0.55f, 0.55f), new Vector2(1.1f, 1.1f));
            Prop best = null;
            float bd = 99;
            foreach (var pr in map.props)
            {
                if (!pr || !filter(pr)) continue;
                if (pr.data.layer != 0 && Dream.I && (Dream.I.IsDreamAt(pr.basePos) != (pr.data.layer == 2))) continue;
                if (!pr.Bounds.Overlaps(r)) continue;
                float d = Vector2.Distance(pr.basePos, p);
                if (d < bd) { bd = d; best = pr; }
            }
            return best;
        }

        void Strike(bool heavy)
        {
            var center = pos + Dir * 0.85f + new Vector2(0, 0.35f);
            var r = new Rect(center - new Vector2(0.8f, 0.7f), new Vector2(1.6f, 1.4f));
            bool hitAny = false;
            var map = Map.Current;
            if (map)
            {
                for (int i = map.props.Count - 1; i >= 0; i--)
                {
                    var pr = map.props[i];
                    if (!pr || (pr.Kind != "bush" && pr.Kind != "pot")) continue;
                    if (!pr.Bounds.Overlaps(r)) continue;
                    map.props.RemoveAt(i);
                    if (pr.Kind == "pot") { pr.Shatter(); Sfx.Play("pot_break"); Pickup.Chance(pr.basePos, 0.5f, 0.15f); }
                    else { pr.Cut(); Sfx.Play("cut"); Pickup.Chance(pr.basePos, 0.18f, 0.08f); }
                    hitAny = true;
                }
            }
            foreach (var h in FindObjectsByType<MonoBehaviour>(FindObjectsSortMode.None))
            {
                if (h is IHittable hit && h is Component c && c.gameObject != gameObject)
                {
                    Vector2 hp = c.transform.position;
                    bool inReach = h is IHitBox hb ? hb.HitBox.Overlaps(r) : (r.Contains(hp) || r.Contains(hp + new Vector2(0, 0.4f)));
                    if (inReach)
                    {
                        if (hit.Hit(new HitInfo { damage = heavy ? 2 : 1, from = pos, knockback = heavy ? 7f : 4f, kind = heavy ? HitKind.Heavy : HitKind.Slash, source = gameObject }))
                            hitAny = true;
                    }
                }
            }
            if (hitAny)
            {
                HitStop.Do(heavy ? 0.09f : 0.05f);
                PixelView.I.Shake(heavy ? 2 : 1, 0.12f);
            }
            if (heavy) PixelView.I.Shake(1, 0.1f);
        }

        void UseLantern()
        {
            var b = PropInFront(0.7f, p => p.Kind == "brazier" && !p.lit);
            if (b != null && b.Ignite())
            {
                Sfx.Play("ignite");
                Fx.Embers(b.basePos + new Vector2(0, 1f), 10);
                Interacted?.Invoke(b);
            }
            else Sfx.Play("lantern");
        }

        /// <summary>Sandals on grass, sand, planks, stone; in the dream, over water, on moonlight.</summary>
        string StepSound(int i)
        {
            var m = Map.Current;
            char c = m ? m.Surface(pos) : 'c';
            if (c == 'a') c = Dream.I && Dream.I.IsDreamAt(pos) ? 'm' : 'c';
            return c switch { 'g' => "step_grass" + i, 's' => "step_sand" + i, 'w' => "step_wood" + i, 'm' => "step_moon" + i, _ => "step" + i };
        }

        void TryInteract()
        {
            var n = NpcInFront();
            if (n != null && n.talk != null) { Story.Run(n.talk(), n); return; }
            var pr = PropInFront(0.6f, p => p.Kind == "sign" || p.Kind == "well" || p.Kind == "gate" || p.Kind == "npc" || p.Kind == "pot" ||
                                            p.Kind == "chest" || p.Kind == "lockdoor" || p.Kind == "bigdoor" || p.Kind == "look");
            if (pr != null) Interacted?.Invoke(pr);
        }

        Npc NpcInFront()
        {
            var at = pos + Dir * 0.8f + new Vector2(0, 0.25f);
            Npc best = null;
            float bd = 1.05f;
            foreach (var n in Npc.All)
            {
                if (!n || !n.Present || n.talk == null) continue;
                var c = n.pos + new Vector2(0, 0.35f);
                var d = at - c;
                if (n.anim.anim == "lie") { c = n.pos + new Vector2(0.1f, 0.4f); d = at - c; d.x *= 0.4f; }
                float dist = d.magnitude;
                if (dist < bd) { bd = dist; best = n; }
            }
            return best;
        }

        public void Hurt(HitInfo h)
        {
            if (!health.Take(h)) return;
            knock = ((pos - (Vector2)h.from).normalized + Vector2.zero) * h.knockback;
            state = State.Hurt;
            stateClock = 0;
            hurtFlash = 1.0f;
            health.invulnerable = 1.0f;
            anim.Play("hurt", facing, true);
            PixelView.I.Shake(2, 0.15f);
            HitStop.Do(0.06f);
            Sfx.Play("hurt");
            if (health.Dead) { state = State.Dead; anim.Play("death", Facing.Down, true); }
        }

        void Place()
        {
            transform.position = new Vector3(pos.x, pos.y, 0);
            anim.sr.sortingOrder = Map.Order(pos.y);
            shadow.sortingOrder = Map.Order(pos.y) - 1;
            shadow.transform.localPosition = new Vector3(0, 0.02f, 0);
            Vector2 lo = facing == Facing.Left ? new Vector2(-0.35f, 0.5f) : facing == Facing.Right ? new Vector2(0.35f, 0.5f) : new Vector2(0.45f, 0.55f);
            if (lantern && anim.model) anim.model.ownLight = lantern;
            if (lantern && anim.model && anim.model.props.TryGetValue("lantern", out var carried))
                lantern.transform.position = (Vector3)(pos + anim.model.Offset(carried.TransformPoint(0, -0.19f * anim.model.def.scale, 0)));
            else if (lantern) lantern.transform.position = (Vector3)(pos + lo);
        }

        public void SetState(State s, string animName = null)
        {
            state = s;
            stateClock = 0;
            if (animName != null) anim.Play(animName, facing, true);
        }

        public void Face(Facing f)
        {
            facing = f;
            anim.SetFacing(f);
        }
    }
}
