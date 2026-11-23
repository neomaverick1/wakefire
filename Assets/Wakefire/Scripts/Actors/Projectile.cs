// Things in flight that somebody else threw: the Brazen Bull's fireballs, and the clay bullets of
// Baltu's slingers. Either one, meeting the Bronze Mirror Shield face-on, turns around and becomes
// Azar's. A slinger's bullet also breaks the other army's men, which is what it was made for.
using UnityEngine;

namespace Wakefire
{
    public class Projectile : MonoBehaviour
    {
        public Vector2 pos, vel;
        public int damage = 2;
        public bool reflected;
        public GameObject owner;
        /// <summary>A clay army's bullet (0 red, 1 blue): it goes for the other army as well as for Azar.</summary>
        public int side = -1;
        bool stone;
        float life, frameClock;
        SpriteRenderer sr;
        Sprite[] frames;
        static Sprite[] fire, stones;
        LightBlob glow;

        public static Projectile Fireball(Vector2 at, Vector2 vel, GameObject owner)
        {
            if (fire == null)
            {
                fire = new Sprite[3];
                for (int i = 0; i < 3; i++) fire[i] = Map.GetSprite("Items/fireball_" + i, 6, 6);
            }
            var p = Make("Fireball", at, vel, owner, fire);
            p.glow = LightBlob.Create(p.transform, at, 2.2f, new Color(1f, 0.6f, 0.25f), 0.8f, true);
            Sfx.Play("fireball", 0.8f);
            return p;
        }

        /// <summary>A sling bullet of baked clay: no fire in it, and a ditch does not stop it.</summary>
        public static Projectile Bullet(Vector2 at, Vector2 vel, GameObject owner)
        {
            if (stones == null)
            {
                stones = new Sprite[2];
                for (int i = 0; i < 2; i++) stones[i] = Map.GetSprite("Items/bullet_" + i, 4, 4);
            }
            var p = Make("Bullet", at, vel, owner, stones);
            p.stone = true;
            p.damage = 1;
            return p;
        }

        static Projectile Make(string name, Vector2 at, Vector2 vel, GameObject owner, Sprite[] frames)
        {
            var go = new GameObject(name);
            go.transform.SetParent(Map.Current ? Map.Current.transform : null, false);
            var p = go.AddComponent<Projectile>();
            p.pos = at; p.vel = vel; p.owner = owner; p.frames = frames;
            p.sr = go.AddComponent<SpriteRenderer>();
            p.sr.sharedMaterial = Map.SpriteMat;
            p.sr.sprite = frames[0];
            return p;
        }

        void Update()
        {
            if (Game.Paused) return;
            float dt = Time.deltaTime;
            life += dt;
            pos += vel * dt;
            transform.position = new Vector3(pos.x, pos.y + 0.55f, 0);
            sr.sortingOrder = Map.Order(pos.y) + 2;
            frameClock += dt * 14f;
            sr.sprite = frames[(int)frameClock % frames.Length];
            if (!stone && ((int)(life * 30)) % 3 == 0) Fx.Embers(pos + new Vector2(0, 0.5f), 1);
            if (life > (stone ? 3f : 6f)) { Burst(); return; }
            var p = Player.I;
            if (!reflected && p && p.state != Player.State.Dead && Vector2.Distance(p.pos + new Vector2(0, 0.2f), pos) < 0.55f
                && (!stone || Dream.I.IsDreamAt(p.pos) == Dream.I.IsDreamAt(pos)))
            {
                if (p.TryReflect(vel))
                {
                    reflected = true;
                    var target = owner ? (Vector2)owner.transform.position : pos - vel;
                    vel = (target - pos).normalized * vel.magnitude * 1.25f;
                    if (stone) { Sfx.Play("clank", 0.8f, 0.04f); Fx.Sparks(pos + new Vector2(0, 0.5f), new Color(1f, 0.9f, 0.6f), 4); }
                    return;
                }
                p.Hurt(new HitInfo { damage = damage, from = pos - vel.normalized, knockback = stone ? 4f : 7f, kind = stone ? HitKind.Thrown : HitKind.Fire, source = gameObject });
                Burst();
                return;
            }
            if (reflected)
            {
                foreach (var e in Enemy.All)
                {
                    if (!e || Vector2.Distance(e.pos + new Vector2(0, 0.5f), pos) > 0.9f) continue;
                    e.Hit(new HitInfo { damage = damage * 2, from = pos - vel.normalized, knockback = 3f, kind = HitKind.Reflected, source = gameObject });
                    Burst();
                    return;
                }
                if (owner && owner.GetComponent<IHittable>() is IHittable h && !(owner.GetComponent<Enemy>()) &&
                    Vector2.Distance((Vector2)owner.transform.position + new Vector2(0, 1f), pos) < 2.0f)
                {
                    h.Hit(new HitInfo { damage = damage * 2, from = pos - vel.normalized, knockback = 0, kind = HitKind.Reflected, source = gameObject });
                    Burst();
                    return;
                }
            }
            else if (side >= 0)
            {
                // clay breaks clay: the other army's man in the way takes it
                foreach (var e in Enemy.All)
                {
                    if (!(e is ClaySoldier c) || c.side == side || c.health.Dead || Vector2.Distance(c.pos + new Vector2(0, 0.5f), pos) > 0.7f) continue;
                    c.Hit(new HitInfo { damage = 3, from = pos - vel.normalized, knockback = 3f, kind = HitKind.Thrown, source = owner ? owner : gameObject });
                    Burst();
                    return;
                }
            }
            var box = new Rect(pos - new Vector2(0.15f, 0.1f), new Vector2(0.3f, 0.2f));
            var mine = owner ? owner.GetComponent<MonoBehaviour>() : null;
            if (stone ? Solids.Blocks(box, pos, mine) : Solids.Overlaps(box, pos, mine)) Burst();
        }

        void Burst()
        {
            if (stone)
            {
                for (int i = 0; i < 7; i++)
                    Fx.Spawn(pos + new Vector2(0, 0.5f), Random.insideUnitCircle * 2.4f, 0.4f, Random.Range(2f, 5f), Random.Range(0.2f, 0.4f),
                        new Color(0.74f, 0.46f, 0.32f), new Color(0.36f, 0.20f, 0.16f), 14f, 1);
                Sfx.Play("clay_hit", 0.5f, 0.06f);
                Destroy(gameObject);
                return;
            }
            for (int i = 0; i < 10; i++)
                Fx.Spawn(pos + new Vector2(0, 0.5f), Random.insideUnitCircle * 3f, 0.3f, Random.Range(1f, 4f), Random.Range(0.25f, 0.5f),
                    new Color(1f, 0.75f, 0.3f), new Color(0.6f, 0.15f, 0.05f), 6f, i % 3 == 0 ? 2 : 1);
            Sfx.Play("fire_burst", 0.7f);
            Destroy(gameObject);
        }
    }
}
