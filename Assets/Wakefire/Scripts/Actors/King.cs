// Kurashtar, the Sleepless King. He is dead, so a blade goes through him like a hand through
// smoke; he is awake, so he can still bring his mace down hard enough to shake the hall. But
// the dead do not dream. When Azar nods off, the king is simply not there, and his crown,
// which is real gold and has no opinion either way, is left hanging where his head was. Knock
// it off in the dream; awake again, a king without his crown is only a tired old man, until he
// has walked over and picked it up.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public class SleeplessKing : MonoBehaviour, IHittable, IHitBox
    {
        public static SleeplessKing I;
        enum S { Seated, Rising, Stalk, Slam, Cast, Flinch, Reel, Bare, Crowning, Spent }
        S s = S.Seated;
        public Vector2 pos;
        public Health health;
        SpriteAnim anim;
        Material mat;
        Facing facing = Facing.Down;
        float clock, flash, cool, thin = 0.33f, crownBob;
        bool crowned = true, struck, wasDream;
        int crownHits, round, roundDamage;
        Vector2 crownAt, seat;
        SpriteRenderer crownSr;
        Material crownDream, crownBoth;
        LightBlob crownGlow, glow;
        readonly Vector2 half = new Vector2(0.42f, 0.18f);
        public System.Action Defeated;
        /// <summary>Moments the story has something to say about: "pass" (a blade went through him),
        /// "crown_off", "bare" (awake without it), "crowned" (he has it back), "round".</summary>
        public System.Action<string> Moment;
        public bool Crowned => crowned;
        public bool Fighting => s != S.Seated && s != S.Rising && s != S.Spent;
        public int Round => round;
        public string StateName => s.ToString();
        public Vector2 CrownSpot => crownAt;
        public Rect HitBox => new Rect(pos.x - 0.55f, pos.y - 0.25f, 1.1f, 3.0f);
        const float SeatLift = 0.62f, HeadHeight = 2.72f;
        static readonly Color Cold = new Color(0.72f, 0.97f, 0.94f, 1f);

        public static SleeplessKing Spawn(Vector2 seat)
        {
            var go = new GameObject("SleeplessKing");
            go.transform.SetParent(Map.Current.transform, false);
            var k = go.AddComponent<SleeplessKing>();
            I = k;
            k.pos = k.seat = seat;
            var body = new GameObject("Sprite");
            body.transform.SetParent(go.transform, false);
            var sr = body.AddComponent<SpriteRenderer>();
            k.mat = new Material(Map.SpriteMat);
            k.mat.SetFloat("_Layer", 1);                 // the waking world only: the dead do not dream
            k.mat.SetFloat("_Ghost", 0.55f);
            k.mat.SetVector("_GhostFade", new Vector4(0.285f, k.thin, 0, 0));
            k.mat.SetFloat("_GhostGain", 1.85f);
            k.mat.SetFloat("_GhostGold", 1f);
            k.mat.SetFloat("_GhostRim", 0.9f);
            sr.sharedMaterial = k.mat;
            k.anim = body.AddComponent<SpriteAnim>();
            k.anim.sr = sr;
            k.anim.modelAs = "king";
            k.anim.sheet = SpriteSheet.Load("priest");
            k.anim.Play("sit", Facing.Down, true);
            k.health = go.AddComponent<Health>();
            k.health.max = k.health.hp = 18;
            k.glow = LightBlob.Create(go.transform, seat + new Vector2(0, 1.6f), 4.5f, new Color(0.45f, 1f, 0.85f), 0.5f, false);
            // the crown as a thing of its own: hanging in the dream where his head would be, or lying where it fell
            var cg = new GameObject("Crown");
            cg.transform.SetParent(go.transform, false);
            k.crownSr = cg.AddComponent<SpriteRenderer>();
            k.crownSr.sprite = Map.GetSprite("Items/crown", 8, 16);
            k.crownDream = new Material(Map.SpriteMat); k.crownDream.SetFloat("_Layer", 2); k.crownDream.SetFloat("_DreamKeep", 1);
            k.crownBoth = new Material(Map.SpriteMat); k.crownBoth.SetFloat("_DreamKeep", 1);
            k.crownSr.sharedMaterial = k.crownDream;
            k.crownGlow = LightBlob.Create(cg.transform, seat, 2.2f, new Color(1f, 0.82f, 0.4f), 0.0f, false);
            k.Place();
            return k;
        }

        void OnDestroy() { if (I == this) I = null; }

        /// <summary>He gets up off the throne (the story calls this when the talking is done).</summary>
        public IEnumerator Rise()
        {
            s = S.Rising;
            anim.Play("rise", Facing.Down, true);
            Sfx.Play("king_tired", 0.7f);
            float t = 0;
            var from = pos; var to = seat + new Vector2(0, -1.5f);
            while (t < 1.05f)
            {
                t += Time.deltaTime;
                pos = Vector2.Lerp(from, to, Mathf.SmoothStep(0, 1, Mathf.Clamp01((t - 0.55f) / 0.5f)));
                yield return null;
            }
            pos = to;
            anim.Play("idle", Facing.Down, true);
        }

        public void Begin() { s = S.Stalk; clock = 0; cool = 1.0f; }

        /// <summary>Hold a pose without thinking (for staged pictures and the end of the fight).</summary>
        public void Pose(string a, Facing f) { facing = f; anim.Play(a, f, true); }

        bool DreamHere => Dream.I && Dream.I.IsDreamAt(pos);

        public bool Hit(HitInfo h)
        {
            if (!Fighting) return false;
            if (h.kind == HitKind.Reflected)
            {
                // his own cold, sent back: it can't hurt him, but nobody likes it
                if (DreamHere || s == S.Reel || s == S.Bare || s == S.Crowning) return false;
                s = S.Flinch; clock = 0; flash = 0.15f;
                anim.Play("hurt", facing, true);
                Sfx.Play("shade_hit");
                return true;
            }
            if (DreamHere)
            {
                if (!crowned) return false;                         // nobody here, and nothing of his either
                crownHits += h.kind == HitKind.Heavy ? 2 : 1;
                crownBob = 0.25f;
                Sfx.Play("crown_hit");
                Fx.Sparks(pos + new Vector2(0, HeadHeight), new Color(1f, 0.85f, 0.4f), 6);
                if (crownHits >= 4 + round) KnockOff(h.from);
                return true;
            }
            if (crowned || s == S.Crowning)
            {
                Sfx.Play("ghost_pass", 0.7f);
                for (int i = 0; i < 6; i++)
                    Fx.Spawn(pos + new Vector2(Random.Range(-0.4f, 0.4f), 0), Random.insideUnitCircle * 1.5f, Random.Range(0.6f, 2.2f), Random.Range(0.2f, 1f),
                        Random.Range(0.3f, 0.6f), new Color(0.8f, 1f, 0.95f), new Color(0.15f, 0.4f, 0.5f), -0.5f);
                Moment?.Invoke("pass");
                return false;
            }
            if (!health.Take(h)) return false;
            flash = 0.2f;
            health.invulnerable = 0.2f;
            roundDamage += h.damage;
            Sfx.Play("boss_hit");
            PixelView.I.Shake(1, 0.15f);
            pos = Solids.Move(pos, (pos - (Vector2)h.from).normalized * 0.25f, half, this);
            if (health.Dead) { StartCoroutine(Yield()); return true; }
            if (Random.value < 0.3f) Pickup.Drop(Pickup.Kind.Flame, pos + new Vector2(Random.value < 0.5f ? -1.6f : 1.6f, -0.4f));
            // each time he loses it he lets himself be hit only so long, then goes for the crown at a run
            if (round < 2 && roundDamage >= 5 && s == S.Bare) hurry = true;
            return true;
        }

        bool hurry;

        void KnockOff(Vector3 from)
        {
            crowned = false;
            crownHits = 0;
            roundDamage = 0;
            hurry = false;
            if (anim.model && anim.model.props.TryGetValue("crown", out var worn)) worn.gameObject.SetActive(false);
            // it lands well away from both of them, somewhere a man can walk to
            var m = Map.Current;
            var c = (Vector2)m.bounds.center + new Vector2(0, -0.8f);
            Vector2 best = c; float bestScore = -1;
            foreach (var off in new[] { new Vector2(-5.2f, 2.2f), new Vector2(5.2f, 2.2f), new Vector2(-5.2f, -3.4f), new Vector2(5.2f, -3.4f), new Vector2(0, -4.2f), new Vector2(0, 2.6f) })
            {
                var q = c + off;
                if (Solids.Overlaps(new Rect(q - half, half * 2), q, this)) continue;
                float score = Vector2.Distance(q, pos) + 0.5f * Vector2.Distance(q, (Vector2)from);
                if (score > bestScore) { bestScore = score; best = q; }
            }
            StartCoroutine(CrownFlies(pos + new Vector2(0, HeadHeight), best));
            Moment?.Invoke("crown_off");
        }

        bool crownFlying;

        IEnumerator CrownFlies(Vector2 from, Vector2 to)
        {
            crownFlying = true;
            crownSr.sharedMaterial = crownBoth;
            crownAt = to;
            for (float t = 0; t < 1f; t += Time.deltaTime / 0.7f)
            {
                var p = Vector2.Lerp(from, to, t) + new Vector2(0, Mathf.Sin(t * Mathf.PI) * 2.4f);
                crownSr.transform.position = new Vector3(Mathf.Round(p.x * 16f) / 16f, Mathf.Round(p.y * 16f) / 16f, 0);
                crownSr.transform.Rotate(0, 0, 900f * Time.deltaTime);
                crownSr.sortingOrder = 30000;
                yield return null;
            }
            crownSr.transform.rotation = Quaternion.identity;
            crownFlying = false;
            Sfx.Play("crown");
            PixelView.I.Shake(1, 0.2f);
            Fx.Sparks(to + new Vector2(0, 0.3f), new Color(1f, 0.85f, 0.4f), 8);
        }

        void Update()
        {
            if (Game.Paused) return;
            float dt = Time.deltaTime;
            var p = Player.I;
            if (flash > 0) flash -= dt;
            if (crownBob > 0) crownBob -= dt;
            mat.SetFloat("_Flash", flash > 0 ? 0.9f : 0);
            bool dream = DreamHere;
            bool talking = Story.I && Story.I.Running;
            if (Fighting && p && !talking && p.state != Player.State.Dead)
            {
                // while Azar dreams, the king is not there, and no time passes for him
                if (!dream)
                {
                    if (wasDream && !crowned && s != S.Reel && s != S.Bare && s != S.Crowning)
                    {
                        s = S.Reel; clock = 0;
                        anim.Play("reel", facing, true);
                        Sfx.Play("king_tired", 0.8f);
                        Moment?.Invoke("bare");
                    }
                    clock += dt;
                    Think(dt, p);
                }
                wasDream = dream;
            }
            // a king without his crown has less of himself to stand on: he thins away from the feet up to the belt
            bool whole = crowned || s == S.Spent;
            // (seated or on his knees there is less of him standing up, so less of him is let go)
            thin = Mathf.MoveTowards(thin, s == S.Seated || s == S.Rising || s == S.Spent ? 0.33f : whole ? 0.42f : 0.47f, dt * 0.25f);
            mat.SetVector("_GhostFade", new Vector4(0.285f, thin, 0, 0));
            // crowned, he is the brightest thing in the room, lit along every edge, his gold still warm;
            // without it he is one more of the dead, greyer and dimmer, but there to be seen (and hit)
            mat.SetFloat("_Ghost", Mathf.MoveTowards(mat.GetFloat("_Ghost"), crowned ? 0.55f : s == S.Spent ? 0.6f : 0.7f, dt * 0.5f));
            mat.SetFloat("_GhostGain", Mathf.MoveTowards(mat.GetFloat("_GhostGain"), crowned ? 1.85f : s == S.Spent ? 1.7f : 1.5f, dt * 1.6f));
            mat.SetFloat("_GhostRim", Mathf.MoveTowards(mat.GetFloat("_GhostRim"), crowned ? 0.9f : s == S.Spent ? 0.7f : 0.45f, dt * 1.6f));
            anim.Tick(dt);
            Place();
        }

        static Vector2 Vec(Facing f) => f == Facing.Down ? Vector2.down : f == Facing.Up ? Vector2.up : f == Facing.Left ? Vector2.left : Vector2.right;

        static Facing FaceOf(Vector2 d)
        {
            if (d.sqrMagnitude < 0.0001f) return Facing.Down;
            return Mathf.Abs(d.x) > Mathf.Abs(d.y) ? (d.x < 0 ? Facing.Left : Facing.Right) : (d.y < 0 ? Facing.Down : Facing.Up);
        }

        void Think(float dt, Player p)
        {
            var d = p.pos - pos;
            float pace = 1.08f + 0.18f * round;
            switch (s)
            {
                case S.Stalk:
                    cool -= dt;
                    facing = FaceOf(d);
                    if (d.magnitude > 1.7f)
                    {
                        anim.Play("walk", facing); anim.SetFacing(facing);
                        pos = Solids.Move(pos, d.normalized * 1.7f * pace * dt, half, this);
                    }
                    else { anim.Play("idle", facing); anim.SetFacing(facing); }
                    if (cool <= 0)
                    {
                        clock = 0; struck = false;
                        if (d.magnitude < 3.0f) { s = S.Slam; anim.Play("slam", facing, true); Sfx.Play("bull_snort", 0.5f); }
                        else { s = S.Cast; anim.Play("cast", facing, true); }
                    }
                    break;
                case S.Slam:
                    // the mace is all the way up for most of it; it lands on the tenth frame of twelve
                    if (!struck && anim.Frame >= 9)
                    {
                        struck = true;
                        StartCoroutine(Wave(pos + Vec(facing) * 1.0f));
                        // hurt, he hits the floor hard enough that it answers twice
                        if (health.hp <= health.max / 2) StartCoroutine(Aftershock(pos + Vec(facing) * 1.0f));
                    }
                    if (anim.Done || clock > 1.4f) { s = S.Stalk; cool = Mathf.Max(0.6f, 1.3f - 0.3f * round); }
                    break;
                case S.Cast:
                    if (!struck && anim.Frame >= 4)
                    {
                        struck = true;
                        int n = 1 + round;
                        var hand = pos + new Vector2(0, 0.2f);
                        var aim = (p.pos - hand).normalized;
                        for (int i = 0; i < n; i++)
                        {
                            float a = (i - (n - 1) / 2f) * 20f;
                            KingBolt.Throw(hand, (Vector2)(Quaternion.Euler(0, 0, a) * aim) * (5.0f + 0.5f * round), gameObject);
                        }
                    }
                    if (anim.Done || clock > 1.2f) { s = S.Stalk; cool = Mathf.Max(0.7f, 1.4f - 0.3f * round); }
                    break;
                case S.Flinch:
                    if (clock > 0.7f) { s = S.Stalk; cool = 0.8f; }
                    break;
                case S.Reel:
                    if (clock > 0.95f) { s = S.Bare; clock = 0; }
                    break;
                case S.Bare:
                {
                    if (crownFlying) break;
                    var w = crownAt - pos;
                    facing = FaceOf(w);
                    anim.Play("walk", facing); anim.SetFacing(facing);
                    float speed = hurry ? 5.0f : 1.25f + 0.25f * round;
                    pos = Solids.Move(pos, w.normalized * Mathf.Min(speed, w.magnitude / Mathf.Max(dt, 0.0001f)) * dt, half, this);
                    if (w.magnitude < 0.45f || clock > 14f)
                    {
                        s = S.Crowning; clock = 0;
                        pos = crownAt + new Vector2(0, 0.05f);
                        anim.Play("idle", Facing.Down, true);
                        facing = Facing.Down;
                    }
                    break;
                }
                case S.Crowning:
                    if (clock > 0.8f)
                    {
                        crowned = true;
                        crownSr.sharedMaterial = crownDream;
                        if (anim.model && anim.model.props.TryGetValue("crown", out var worn)) worn.gameObject.SetActive(true);
                        Sfx.Play("crown_hit", 0.7f);
                        round = Mathf.Min(2, round + 1);
                        s = S.Stalk; cool = 0.9f;
                        Moment?.Invoke("crowned");
                    }
                    break;
            }
        }

        /// <summary>Where the mace lands: a blow at the spot, then the floor carries it outward.</summary>
        IEnumerator Aftershock(Vector2 at)
        {
            yield return new WaitForSeconds(0.62f);
            if (!Fighting || s == S.Bare || s == S.Reel) yield break;
            yield return Wave(at);
        }

        IEnumerator Wave(Vector2 at)
        {
            Sfx.Play("king_slam");
            PixelView.I.Shake(3, 0.35f);
            Fx.Dust(at, 10);
            float[] reach = { 0f, 1.5f, 2.9f, 4.2f };
            for (int ring = 0; ring < 3; ring++)
            {
                float r0 = reach[ring], r1 = reach[ring + 1];
                int n = 14 + ring * 8;
                for (int i = 0; i < n; i++)
                {
                    float a = i / (float)n * Mathf.PI * 2f;
                    var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.8f);
                    Fx.Spawn(at + dir * (r0 + 0.3f), dir * 5f, 0.1f, 1.2f, 0.32f, new Color(0.85f, 1f, 0.95f), new Color(0.15f, 0.45f, 0.5f), 6f, ring == 0 ? 2 : 1);
                }
                var p = Player.I;
                if (p && p.state != Player.State.Dead && p.state != Player.State.Roll && !(Dream.I && Dream.I.IsDreamAt(p.pos)))
                {
                    var q = p.pos - at; q.y /= 0.8f;
                    float dist = q.magnitude;
                    if (dist >= r0 - 0.2f && dist < r1)
                        p.Hurt(new HitInfo { damage = ring == 0 ? 2 : 1, from = at, knockback = ring == 0 ? 9f : 6f, kind = HitKind.Crush, source = gameObject });
                }
                if (ring == 0) Sfx.Play("king_wave", 0.7f);
                yield return new WaitForSeconds(0.16f);
            }
        }

        IEnumerator Yield()
        {
            s = S.Spent;
            facing = Facing.Down;
            anim.Play("kneel", facing, true);
            Sfx.Play("king_tired");
            foreach (var e in Enemy.All.ToArray()) if (e is Ushabti u) u.Hit(new HitInfo { damage = 99, from = u.pos + Vector2.up, kind = HitKind.Fire });
            foreach (var b in FindObjectsByType<KingBolt>(FindObjectsSortMode.None)) Destroy(b.gameObject);
            PixelView.I.Shake(2, 0.5f);
            yield return new WaitForSeconds(1.4f);
            Defeated?.Invoke();
        }

        void Place()
        {
            transform.position = new Vector3(pos.x, pos.y, 0);
            bool seated = s == S.Seated || s == S.Rising;
            float lift = s == S.Seated ? SeatLift : s == S.Rising ? Mathf.Lerp(SeatLift, 0, Mathf.Clamp01(Vector2.Distance(pos, seat) / 1.5f)) : 0;
            anim.sr.transform.localPosition = new Vector3(0, Mathf.Round((lift + 1f / 16f) * 16f) / 16f, 0);
            // on the throne he is drawn over it, whatever the rows say
            anim.sr.sortingOrder = Map.Order(pos.y) + (seated ? 48 : 0);
            if (glow)
            {
                glow.transform.position = (Vector3)(pos + new Vector2(0, 1.5f));
                // his light goes where he goes: out of the dream altogether, and low without the crown
                glow.intensity = Mathf.MoveTowards(glow.intensity, DreamHere ? 0f : crowned ? 0.5f : 0.16f, Time.deltaTime * 1.5f);
            }
            if (crownFlying) return;
            if (crowned)
            {
                // seen only in the dream: the crown, on nobody
                var c = pos + new Vector2(Mathf.Sin(Time.time * 37f) * (crownBob > 0 ? 0.08f : 0), HeadHeight - 0.5f + Mathf.Sin(Time.time * 1.7f) * 0.06f + lift);
                crownSr.transform.position = new Vector3(Mathf.Round(c.x * 16f) / 16f, Mathf.Round(c.y * 16f) / 16f, 0);
                crownSr.sortingOrder = Map.Order(pos.y) + (seated ? 50 : 2);
                crownSr.enabled = s != S.Crowning;
                crownGlow.intensity = 0;
            }
            else
            {
                crownSr.transform.position = new Vector3(crownAt.x, crownAt.y, 0);
                crownSr.sortingOrder = Map.Order(crownAt.y);
                crownSr.enabled = true;
                crownGlow.transform.position = (Vector3)(crownAt + new Vector2(0, 0.3f));
                crownGlow.intensity = 0.5f;
            }
        }
    }

    /// <summary>A handful of the dead's cold fire, thrown. It belongs to the waking world like the
    /// hand that threw it; the Bronze Mirror sends it back.</summary>
    public class KingBolt : MonoBehaviour
    {
        Vector2 pos, vel;
        bool reflected;
        GameObject owner;
        float life, frameClock;
        SpriteRenderer sr;
        static Sprite[] frames;
        static Material wakeMat;

        public static KingBolt Throw(Vector2 at, Vector2 vel, GameObject owner)
        {
            if (frames == null)
            {
                frames = new Sprite[3];
                for (int i = 0; i < 3; i++) frames[i] = Map.GetSprite("Items/bolt_" + i, 6, 6);
            }
            if (!wakeMat) { wakeMat = new Material(Map.SpriteMat); wakeMat.SetFloat("_Layer", 1); }
            var go = new GameObject("KingBolt");
            go.transform.SetParent(Map.Current ? Map.Current.transform : null, false);
            var b = go.AddComponent<KingBolt>();
            b.pos = at; b.vel = vel; b.owner = owner;
            b.sr = go.AddComponent<SpriteRenderer>();
            b.sr.sharedMaterial = wakeMat;
            b.sr.sprite = frames[0];
            LightBlob.Create(go.transform, at, 2.0f, new Color(0.45f, 1f, 0.85f), 0.7f, true);
            Sfx.Play("bolt", 0.8f);
            return b;
        }

        void Update()
        {
            if (Game.Paused) return;
            float dt = Time.deltaTime;
            life += dt;
            pos += vel * dt;
            transform.position = new Vector3(pos.x, pos.y + 0.6f, 0);
            sr.sortingOrder = Map.Order(pos.y) + 2;
            frameClock += dt * 12f;
            sr.sprite = frames[(int)frameClock % frames.Length];
            if (((int)(life * 30)) % 4 == 0)
                Fx.Spawn(pos + new Vector2(0, 0.6f), -vel * 0.1f, 0, 0, 0.3f, new Color(0.8f, 1f, 0.95f), new Color(0.1f, 0.4f, 0.5f), 0f);
            if (life > 5f) { Burst(); return; }
            var p = Player.I;
            bool dreamHere = Dream.I && Dream.I.IsDreamAt(pos);
            if (!reflected && !dreamHere && p && p.state != Player.State.Dead && p.state != Player.State.Roll &&
                Vector2.Distance(p.pos + new Vector2(0, 0.2f), pos) < 0.5f && !(Dream.I && Dream.I.IsDreamAt(p.pos)))
            {
                if (p.TryReflect(vel))
                {
                    reflected = true;
                    var target = owner ? (Vector2)owner.transform.position : pos - vel;
                    vel = (target - pos).normalized * vel.magnitude * 1.3f;
                    return;
                }
                p.Hurt(new HitInfo { damage = 1, from = pos - vel.normalized, knockback = 6f, kind = HitKind.Fire, source = gameObject });
                Burst();
                return;
            }
            if (reflected && owner && Vector2.Distance((Vector2)owner.transform.position + new Vector2(0, 0.6f), pos + new Vector2(0, 0.6f)) < 0.9f)
            {
                if (owner.GetComponent<IHittable>() is IHittable h) h.Hit(new HitInfo { damage = 0, from = pos - vel.normalized, kind = HitKind.Reflected, source = gameObject });
                Burst();
                return;
            }
            if (Solids.Overlaps(new Rect(pos - new Vector2(0.15f, 0.1f), new Vector2(0.3f, 0.2f)), pos, owner ? owner.GetComponent<MonoBehaviour>() : null)) Burst();
        }

        void Burst()
        {
            for (int i = 0; i < 8; i++)
                Fx.Spawn(pos + new Vector2(0, 0.6f), Random.insideUnitCircle * 2.6f, 0.3f, Random.Range(1f, 3f), Random.Range(0.25f, 0.45f),
                    new Color(0.85f, 1f, 0.95f), new Color(0.1f, 0.35f, 0.5f), 6f);
            Sfx.Play("bolt_burst", 0.6f);
            Destroy(gameObject);
        }
    }
}
