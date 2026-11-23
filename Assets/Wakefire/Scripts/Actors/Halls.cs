// The rest of the high halls' staff.
//
// A thurifer is a censer-bearer. Forty nights ago the service stopped, and nobody has told him.
// He walks his round with the censer going over his head on its chain, and nothing gets inside
// the circle of it: a blade is knocked away, and so is whoever brought it. Every few rounds he
// lets it out to its full length at whoever is nearest. Bronze up and square to it, and it goes
// home the way it came, round his own neck twice, and he stands in his own incense until he has
// got it off.
//
// A burning glass is a lens as wide as a shield in a bronze ring on three legs. The priests lit
// the high lamps with it from the floor. Nobody has turned it off. It turns to follow whatever
// moves, gathers the light (you can hear it gather) and lets it go in a line. Stand out of the
// line, or stand in it with the bronze up: what it sends comes back, and glass does not care for
// its own light. Three times, and it stops being a glass.
using UnityEngine;

namespace Wakefire
{
    /// <summary>One white pixel, for chains and beams of light.</summary>
    static class Dot
    {
        static Sprite px;

        static Sprite One
        {
            get
            {
                if (px) return px;
                var t = new Texture2D(1, 1) { filterMode = FilterMode.Point };
                t.SetPixel(0, 0, Color.white);
                t.Apply();
                px = Sprite.Create(t, new Rect(0, 0, 1, 1), new Vector2(0.5f, 0.5f), 16f);
                return px;
            }
        }

        /// <summary>A pixel of that colour. Lit like everything else, or (shining) its own colour whatever the room is doing.</summary>
        public static SpriteRenderer Make(Transform parent, Color c, bool shining = false)
        {
            var go = new GameObject("dot");
            go.transform.SetParent(parent, false);
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sprite = One;
            if (shining)
            {
                var m = new Material(Map.SpriteMat);
                m.SetFloat("_Flash", 1f);
                m.SetColor("_FlashColor", c);
                sr.sharedMaterial = m;
            }
            else
            {
                sr.sharedMaterial = Map.SpriteMat;
                sr.color = c;
            }
            return sr;
        }

        /// <summary>A line of light from a to b that is there for a moment and then is not.</summary>
        public static void Flash(Vector2 a, Vector2 b, float seconds, int order)
        {
            var go = new GameObject("flash");
            go.transform.SetParent(Map.Current ? Map.Current.transform : null, false);
            var sheath = Make(go.transform, new Color(1f, 0.74f, 0.28f), true);
            var core = Make(go.transform, new Color(1f, 0.98f, 0.86f), true);
            Line(sheath, a, b, 3); Line(core, a, b, 1);
            sheath.sortingOrder = order; core.sortingOrder = order + 1;
            Object.Destroy(go, seconds);
        }

        /// <summary>Stretches a pixel into a line from a to b, so many pixels wide.</summary>
        public static void Line(SpriteRenderer sr, Vector2 a, Vector2 b, float width)
        {
            var d = b - a;
            float len = d.magnitude;
            sr.transform.position = (Vector3)((a + b) * 0.5f);
            sr.transform.rotation = Quaternion.Euler(0, 0, Mathf.Atan2(d.y, d.x) * Mathf.Rad2Deg);
            sr.transform.localScale = new Vector3(Mathf.Max(1f, len * 16f), width, 1);
        }
    }

    // ------------------------------------------------------------------------------ thurifer
    public class Thurifer : Enemy
    {
        enum S { Round, Wind, Cast, Back, Tangled }
        S s;
        float clock, angle, spin = 1f, radius = 1.4f, cool = 1.8f, reach, swipeCool, puff;
        int halfTurns;
        Vector2 castDir, censerAt;
        bool thrownBack;
        Censer censer;
        const float Orbit = 1.4f, Range = 5.4f;

        public static Thurifer Spawn(Vector2 at) => Make<Thurifer>("priest", "idle", at, WorldLayer.Both, 4, "thurifer");

        protected override void Init()
        {
            speed = 0.85f; half = new Vector2(0.3f, 0.16f); touchDamage = 0;
            angle = Random.value * Mathf.PI * 2f;
            spin = Random.value < 0.5f ? 1f : -1f;
            censerAt = pos + new Vector2(Mathf.Cos(angle), Mathf.Sin(angle) * 0.7f) * radius;
            censer = Censer.Make(this);
        }

        public bool IsTangled => s == S.Tangled;
        public bool Casting => s == S.Cast || s == S.Back;
        public bool Winding => s == S.Wind;
        public Vector2 CenserAt => censerAt;
        float CenserHeight => s == S.Tangled ? 1.0f : s == S.Cast || s == S.Back ? 0.8f : 2.4f;
        protected override float KnockScale => 0.25f;
        protected override Color BurstColor => new Color(0.86f, 0.62f, 0.26f);

        /// <summary>Nothing gets inside the circle of it while it is going round. (The Sun Wheel comes in flat, under the chain.)</summary>
        protected override bool Accepts(HitInfo h) => s == S.Tangled || h.kind == HitKind.Reflected || h.kind == HitKind.Thrown;

        protected override void OnHurt(HitInfo h)
        {
            if (h.kind == HitKind.Thrown && s != S.Tangled && !health.Dead) Tangle();
        }

        protected override void Die()
        {
            if (censer) censer.Drop();
            if (Story.I) Story.I.ThuriferDown();
            base.Die();
        }

        /// <summary>It has stopped on the bronze. Going round, it only changes its mind about which way; let
        /// out to its length, it goes home the way it came.</summary>
        public override void Blocked(Player p)
        {
            Sfx.Play("censer_clang", 0.8f, 0.05f);
            if (s == S.Cast) { thrownBack = true; s = S.Back; clock = 0; }
            else if (s == S.Round || s == S.Wind) { spin = -spin; swipeCool = 0.6f; }
        }

        void Tangle()
        {
            s = S.Tangled; clock = 0;
            Sfx.Play("censer_clang", 0.9f, 0.05f);
            Sfx.Play("censer_cough", 0.8f, 0.05f);
            PixelView.I.Shake(1, 0.15f);
            anim.Play("cough", facing, true);
            if (Story.I) Story.I.CenserReturned();
        }

        void Swipe(Player p)
        {
            if (swipeCool > 0 || (p.pos - censerAt).magnitude > 0.62f) return;
            swipeCool = 0.55f;
            p.Hurt(new HitInfo { damage = 1, from = censerAt, knockback = 7f, kind = HitKind.Slash, source = gameObject });
        }

        void Circle(float rate, float want, float dt)
        {
            angle += spin * rate * dt;
            radius = Mathf.MoveTowards(radius, want, dt * 2.2f);
            censerAt = pos + new Vector2(Mathf.Cos(angle), Mathf.Sin(angle) * 0.7f) * radius;
            int h = Mathf.FloorToInt(angle / Mathf.PI);
            if (h != halfTurns)
            {
                halfTurns = h;
                if (Player.I && Vector2.Distance(Player.I.pos, pos) < 8f) Sfx.Play("censer_pass", rate > 8f ? 0.55f : 0.3f, 0.12f);
            }
        }

        protected override void Think(float dt, Player p)
        {
            clock += dt;
            swipeCool -= dt;
            var d = p.pos - pos;
            bool sees = CanSee(p, 7.5f);
            switch (s)
            {
                case S.Round:
                    Circle(4.6f, Orbit, dt);
                    if (sees) facing = FaceOf(d);
                    anim.SetFacing(facing);
                    if (sees && d.magnitude > 2.3f) { anim.Play("walk", facing); Move(d.normalized * speed, dt); }
                    else anim.Play("swing", facing);
                    Swipe(p);
                    if (sees) cool -= dt;
                    if (cool <= 0 && sees && d.magnitude < Range - 0.4f && d.magnitude > 1.3f)
                    {
                        s = S.Wind; clock = 0;
                        if (Story.I) Story.I.ThuriferSeen();
                    }
                    break;
                case S.Wind:
                    // faster, and closer in: everybody in the temple knew what that meant, and stood behind something
                    Circle(12f, 0.95f, dt);
                    facing = FaceOf(d); anim.SetFacing(facing);
                    anim.Play("swing", facing);
                    Swipe(p);
                    if (clock > 0.8f)
                    {
                        s = S.Cast; clock = 0; thrownBack = false;
                        castDir = d.sqrMagnitude > 0.01f ? d.normalized : Tomb.Dir(facing);
                        reach = 0.8f;
                        anim.Play("cast", facing, true);
                        Sfx.Play("censer_pass", 0.9f, 0.05f);
                    }
                    break;
                case S.Cast:
                    reach += 12.5f * dt;
                    censerAt = pos + castDir * reach;
                    if (swipeCool <= 0 && (p.pos - censerAt).magnitude < 0.6f)
                    {
                        swipeCool = 0.4f;
                        if (p.TryReflect(castDir)) { Blocked(p); break; }
                        p.Hurt(new HitInfo { damage = 2, from = censerAt - castDir * 0.5f, knockback = 8f, kind = HitKind.Slash, source = gameObject });
                        if (s != S.Cast) break;                 // (it stopped on the bronze after all)
                    }
                    if (reach >= Range || Solids.Blocks(new Rect(censerAt - new Vector2(0.15f, 0.15f), new Vector2(0.3f, 0.3f)), censerAt, this))
                    {
                        if (reach < Range) { Sfx.Play("clank", 0.6f, 0.1f); Fx.Sparks(censerAt + new Vector2(0, 0.7f), new Color(1f, 0.7f, 0.3f), 6); }
                        s = S.Back; clock = 0;
                    }
                    break;
                case S.Back:
                    reach -= (thrownBack ? 17f : 9.5f) * dt;
                    censerAt = pos + castDir * Mathf.Max(0.3f, reach);
                    if (reach <= 0.45f)
                    {
                        if (thrownBack)
                        {
                            Hit(new HitInfo { damage = 1, from = pos + castDir, knockback = 1.5f, kind = HitKind.Reflected, source = gameObject });
                            if (!health.Dead) Tangle();
                        }
                        else
                        {
                            s = S.Round; clock = 0; cool = Random.Range(2.2f, 3.2f);
                            angle = Mathf.Atan2(castDir.y, castDir.x); radius = 0.5f;
                            halfTurns = Mathf.FloorToInt(angle / Mathf.PI);
                        }
                    }
                    break;
                case S.Tangled:
                    // twice round his own neck, and the smoke has nowhere else to go
                    censerAt = pos + new Vector2(0.12f * Mathf.Sin(clock * 9f), 0.02f);
                    anim.Play("cough", facing);
                    if ((puff -= dt) <= 0)
                    {
                        puff = 0.06f;
                        Fx.Spawn(pos + new Vector2(Random.Range(-0.3f, 0.3f), 0), new Vector2(Random.Range(-0.4f, 0.4f), 0), Random.Range(0.9f, 1.5f), Random.Range(0.4f, 1.1f),
                            Random.Range(0.5f, 0.9f), new Color(0.80f, 0.78f, 0.74f), new Color(0.36f, 0.34f, 0.36f), -0.6f, Random.value < 0.4f ? 2 : 1);
                    }
                    if (clock > 2.9f)
                    {
                        s = S.Round; clock = 0; cool = 1.4f; radius = 0.4f;
                        halfTurns = Mathf.FloorToInt(angle / Mathf.PI);
                    }
                    break;
            }
            if (censer) censer.Place(censerAt, CenserHeight, s == S.Tangled);
        }
    }

    /// <summary>The censer itself: bronze, lit, on nine links of chain from his fist.</summary>
    public class Censer : MonoBehaviour
    {
        Thurifer owner;
        SpriteAnim anim;
        SpriteRenderer sr, shade;
        LightBlob glow;
        readonly SpriteRenderer[] links = new SpriteRenderer[9];
        Vector2 at;
        float height = 2.4f, shown = 2.4f, smoke;
        bool wrapped;

        public static Censer Make(Thurifer t)
        {
            var go = new GameObject("Censer");
            go.transform.SetParent(Map.Current ? Map.Current.transform : null, false);
            var c = go.AddComponent<Censer>();
            c.owner = t;
            var body = new GameObject("Sprite");
            body.transform.SetParent(go.transform, false);
            c.sr = body.AddComponent<SpriteRenderer>();
            c.sr.sharedMaterial = new Material(Map.SpriteMat);
            c.anim = body.AddComponent<SpriteAnim>();
            c.anim.sr = c.sr;
            c.anim.modelAs = "censer";
            c.anim.sheet = SpriteSheet.Load("moth");
            c.anim.Play("idle", Facing.Down, true);
            c.shade = Npc.MakeShadow(go.transform, WorldLayer.Both, 6);
            c.glow = LightBlob.Create(go.transform, t.CenserAt, 2.1f, new Color(1f, 0.55f, 0.2f), 0.7f, true);
            for (int i = 0; i < c.links.Length; i++) c.links[i] = Dot.Make(go.transform, i % 2 == 0 ? new Color(1f, 0.84f, 0.42f) : new Color(0.20f, 0.12f, 0.08f));
            c.Place(t.CenserAt, 2.4f, false);
            return c;
        }

        public void Place(Vector2 ground, float h, bool wrap)
        {
            at = ground; height = h; wrapped = wrap;
        }

        /// <summary>Nobody is holding it any more.</summary>
        public void Drop()
        {
            Sfx.Play("censer_clang", 0.7f, 0.1f);
            Fx.Sparks(at + new Vector2(0, 0.3f), new Color(1f, 0.6f, 0.2f), 10);
            Destroy(gameObject);
        }

        void LateUpdate()
        {
            if (!owner) { Destroy(gameObject); return; }
            float dt = Time.deltaTime;
            transform.position = new Vector3(at.x, at.y, 0);
            shown = Mathf.MoveTowards(shown, height, dt * 6f);          // (it comes down to be thrown, and goes back up, rather than jumping)
            if (anim.model) anim.model.height = shown;
            else sr.transform.localPosition = new Vector3(0, shown, 0);
            anim.Tick(Enemy.Frozen ? 0 : dt);
            int order = Map.Order(at.y);
            sr.sortingOrder = order + 1;
            if (shade) shade.sortingOrder = order - 1;
            if (glow) glow.height = shown + 0.4f;
            // the chain: from his fist, over his head, to the ring on top of it
            Vector2 fist = owner.pos + new Vector2(0, owner.IsTangled ? 1.6f : 2.4f), ring = at + new Vector2(0, shown + 0.96f);
            int chainOrder = Map.Order(Mathf.Min(owner.pos.y, at.y)) + 2;
            for (int i = 0; i < links.Length; i++)
            {
                links[i].enabled = !wrapped;
                if (wrapped) continue;
                float k = (i + 0.5f) / links.Length;
                var q = Vector2.Lerp(fist, ring, k) + new Vector2(0, -Mathf.Sin(k * Mathf.PI) * 0.10f);
                links[i].transform.position = new Vector3(Mathf.Round(q.x * 16f) / 16f, Mathf.Round(q.y * 16f) / 16f, 0);
                links[i].transform.localScale = new Vector3(2, 2, 1);
                links[i].sortingOrder = chainOrder;
            }
            if (Enemy.Frozen) return;
            if ((smoke -= dt) <= 0)
            {
                smoke = 0.07f;
                Fx.Spawn(at + new Vector2(Random.Range(-0.1f, 0.1f), 0), new Vector2(Random.Range(-0.2f, 0.2f), 0), shown + 0.5f, Random.Range(0.3f, 0.8f),
                    Random.Range(0.45f, 0.8f), new Color(0.78f, 0.76f, 0.74f), new Color(0.32f, 0.30f, 0.34f), -0.5f);
            }
        }
    }

    // ------------------------------------------------------------------------------ burning glass
    public class BurningGlass : Enemy
    {
        enum S { Idle, Gather, Fire, Cool }
        S s;
        float clock, cool = 1.2f, sweep = 1f, beamLen;
        Vector2 aim = Vector2.down, beamDir;
        bool struck, told;
        Solid body;
        SpriteRenderer core, sheath, warn;
        LightBlob glow;
        const float Range = 9f, LensHeight = 1.6f;

        public static BurningGlass Spawn(Vector2 at) => Make<BurningGlass>("moth", "idle", at, WorldLayer.Both, 3, "glass");

        protected override void Init()
        {
            speed = 0; half = new Vector2(0.42f, 0.2f); touchDamage = 0;
            body = Solids.Add(new Rect(pos - new Vector2(0.42f, 0.18f), new Vector2(0.84f, 0.42f)), WorldLayer.Both, this);
            var beam = new GameObject("Beam");
            beam.transform.SetParent(transform, false);
            sheath = Dot.Make(beam.transform, new Color(1f, 0.74f, 0.28f), true);
            core = Dot.Make(beam.transform, new Color(1f, 0.98f, 0.86f), true);
            warn = Dot.Make(beam.transform, new Color(1f, 0.52f, 0.20f), true);
            sheath.enabled = core.enabled = warn.enabled = false;
            glow = LightBlob.Create(transform, pos, 2.6f, new Color(1f, 0.86f, 0.55f), 0f, true);
            glow.height = LensHeight;
            if (anim.model) { anim.model.turnRate = 100000f; anim.model.Aim(aim, true); }
        }

        /// <summary>How many times it has had its own light back.</summary>
        public int Cracks => health ? health.max - health.hp : 0;
        public bool Gathering => s == S.Gather;
        /// <summary>Seconds it has been gathering (it follows for the first half of a second, then holds its line); -1 when it is not.</summary>
        public float GatherClock => s == S.Gather ? clock : -1f;
        public bool Firing => s == S.Fire;
        public Vector2 Aim => aim;
        public override bool Sleeps => false;                 // (a lens has nothing to sleep with)
        protected override float KnockScale => 0f;
        protected override string HurtSound => "glass_crack";
        protected override Color BurstColor => new Color(0.75f, 0.92f, 1f);
        public override Rect HitBox => new Rect(pos.x - 0.5f, pos.y - 0.2f, 1.0f, 1.9f);

        /// <summary>It is glass. It is also three fingers thick: only light, or a wheel of gold, makes any impression.</summary>
        protected override bool Accepts(HitInfo h)
        {
            if (h.kind == HitKind.Reflected || h.kind == HitKind.Thrown) return true;
            if (!told && Story.I) { told = true; Story.I.GlassStruck(); }
            return false;
        }

        protected override void OnHurt(HitInfo h)
        {
            Shards(6);
            Quench();
            s = S.Cool; clock = 0;
            anim.Play("idle", Facing.Down);
        }

        protected override void Die()
        {
            Sfx.Play("glass_break", 1f, 0.03f);
            Shards(26);
            Quench();
            if (body != null) { Solids.Remove(body); body = null; }
            if (Story.I) Story.I.GlassBroken();
            base.Die();
        }

        /// <summary>Taken away with its room, or broken: either way it is not in anybody's way any more.</summary>
        protected override void OnDestroy()
        {
            if (body != null) { Solids.Remove(body); body = null; }
            base.OnDestroy();
        }

        void Shards(int n)
        {
            for (int i = 0; i < n; i++)
                Fx.Spawn(pos + new Vector2(Random.Range(-0.3f, 0.3f), 0), Random.insideUnitCircle * 3.2f, LensHeight + Random.Range(-0.3f, 0.3f), Random.Range(1f, 5f),
                    Random.Range(0.35f, 0.7f), new Color(0.90f, 1f, 1f), new Color(0.35f, 0.60f, 0.70f), 18f, i % 4 == 0 ? 2 : 1);
        }

        void Quench()
        {
            sheath.enabled = core.enabled = warn.enabled = false;
            if (glow) glow.intensity = 0;
        }

        bool Sight(Player p)
        {
            Vector2 a = pos + new Vector2(0, 0.2f), b = p.pos + new Vector2(0, 0.2f);
            int n = Mathf.Max(2, Mathf.CeilToInt(Vector2.Distance(a, b) / 0.35f));
            for (int i = 1; i < n; i++)
            {
                var q = Vector2.Lerp(a, b, i / (float)n);
                if (Solids.Blocks(new Rect(q - new Vector2(0.06f, 0.06f), new Vector2(0.12f, 0.12f)), q, this)) return false;
            }
            return true;
        }

        /// <summary>Turns the ring towards a direction, so many degrees a second at most. True once it is on it.</summary>
        bool Turn(Vector2 to, float rate, float dt)
        {
            float off = Vector2.SignedAngle(aim, to);
            float step = Mathf.Clamp(off, -rate * dt, rate * dt);
            float a = (Mathf.Atan2(aim.y, aim.x) * Mathf.Rad2Deg + step) * Mathf.Deg2Rad;
            aim = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
            if (anim.model) anim.model.Aim(aim, true);
            return Mathf.Abs(off) < 10f;
        }

        Vector2 Lens => pos + new Vector2(0, LensHeight);

        /// <summary>How far the light gets before something stops it.</summary>
        float Reach(Vector2 dir)
        {
            float d = 0.7f;
            for (; d < Range + 4f; d += 0.2f)
            {
                var q = pos + dir * d;
                if (Solids.Blocks(new Rect(q - new Vector2(0.08f, 0.08f), new Vector2(0.16f, 0.16f)), q, this)) break;
            }
            return d;
        }

        void Draw(float len, bool full)
        {
            Vector2 a = Lens + beamDir * 0.25f, b = Lens + beamDir * len;
            int order = Map.Order(Mathf.Min(pos.y, pos.y + beamDir.y * len)) + 40;
            if (full)
            {
                Dot.Line(sheath, a, b, 3); Dot.Line(core, a, b, 1);
                sheath.sortingOrder = order; core.sortingOrder = order + 1;
            }
            else
            {
                Dot.Line(warn, a, b, 1);
                warn.sortingOrder = order;
            }
        }

        /// <summary>The light, while it lasts: whoever is standing in the line has it, unless they hand it back.</summary>
        void Burn(Player p)
        {
            if (struck) return;
            var rel = p.pos - pos;
            float along = Vector2.Dot(rel, beamDir);
            if (along < 0.5f || along > beamLen + 0.3f) return;
            if (Mathf.Abs(rel.x * beamDir.y - rel.y * beamDir.x) > 0.45f) return;
            if (Dream.I && Dream.I.IsDreamAt(p.pos) != Dream.I.IsDreamAt(pos)) return;
            struck = true;
            if (p.TryReflect(beamDir)) { Returned(p, along); return; }
            p.Hurt(new HitInfo { damage = 2, from = pos, knockback = 6f, kind = HitKind.Fire, source = gameObject });
        }

        /// <summary>It stopped on the bronze: it has come back.</summary>
        public override void Blocked(Player p)
        {
            Returned(p, Vector2.Dot(p.pos - pos, beamDir));
        }

        void Returned(Player p, float along)
        {
            beamLen = Mathf.Max(0.6f, along - 0.3f);
            Dot.Flash(Lens + beamDir * 0.25f, Lens + beamDir * beamLen, 0.16f, Map.Order(Mathf.Min(pos.y, p.pos.y)) + 40);
            Fx.Sparks(Lens, new Color(1f, 0.95f, 0.7f), 10);
            if (Story.I) Story.I.GlassAnswered();
            Hit(new HitInfo { damage = 1, from = p.pos, knockback = 0, kind = HitKind.Reflected, source = p.gameObject });
        }

        protected override void Think(float dt, Player p)
        {
            clock += dt;
            var d = p.pos - pos;
            bool sees = CanSee(p, Range) && Sight(p);
            switch (s)
            {
                case S.Idle:
                    anim.Play("idle", Facing.Down);
                    if (sees)
                    {
                        bool on = Turn(d.normalized, 85f, dt);
                        cool -= dt;
                        if (cool <= 0 && on)
                        {
                            s = S.Gather; clock = 0;
                            Sfx.Play("glass_gather", 0.75f, 0.03f);
                            anim.Play("gather", Facing.Down, true);
                            if (Story.I) Story.I.GlassSeen();
                        }
                    }
                    else
                    {
                        // nobody about: it looks, slowly, at everything else
                        float a = Mathf.Atan2(aim.y, aim.x) + sweep * 0.35f * dt;
                        aim = new Vector2(Mathf.Cos(a), Mathf.Sin(a));
                        if (anim.model) anim.model.Aim(aim, true);
                        if (Random.value < dt * 0.15f) sweep = -sweep;
                    }
                    break;
                case S.Gather:
                    // it follows for the first part of it, and then it holds its line: step out, or square up
                    if (clock < 0.55f && sees) Turn(d.normalized, 60f, dt);
                    beamDir = aim;
                    if (glow) glow.intensity = Mathf.Clamp01(clock / 0.95f) * 0.9f;
                    warn.enabled = Mathf.Repeat(clock * (7f + clock * 12f), 1f) < 0.55f;
                    if (warn.enabled) Draw(Reach(beamDir), false);
                    if (clock > 0.95f)
                    {
                        s = S.Fire; clock = 0; struck = false;
                        beamLen = Reach(beamDir);
                        warn.enabled = false;
                        sheath.enabled = core.enabled = true;
                        anim.Play("fire", Facing.Down, true);
                        Sfx.Play("glass_beam", 0.9f, 0.03f);
                        PixelView.I.Shake(1, 0.12f);
                        if (glow) glow.intensity = 1.3f;
                    }
                    break;
                case S.Fire:
                    Burn(p);
                    if (s != S.Fire) break;                    // (it had its own light back, and has stopped)
                    Draw(beamLen, true);
                    if (Random.value < dt * 40f)
                    {
                        var q = Lens + beamDir * Random.Range(0.4f, beamLen);
                        Fx.Spawn(q - new Vector2(0, LensHeight), Random.insideUnitCircle * 0.8f, LensHeight, Random.Range(0.2f, 1.2f), Random.Range(0.15f, 0.3f),
                            new Color(1f, 0.95f, 0.75f), new Color(1f, 0.5f, 0.15f), 2f);
                    }
                    if (clock > 0.34f) { Quench(); s = S.Cool; clock = 0; anim.Play("idle", Facing.Down); }
                    break;
                case S.Cool:
                    if (clock > 1.5f) { s = S.Idle; clock = 0; cool = 0.5f; }
                    break;
            }
        }
    }
}
