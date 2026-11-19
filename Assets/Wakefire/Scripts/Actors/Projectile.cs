// Fire in flight: the Brazen Bull's fireballs (and anything else that throws). A fireball that
// meets the Bronze Mirror Shield face-on turns around and becomes Azar's.
using UnityEngine;

namespace Wakefire
{
    public class Projectile : MonoBehaviour
    {
        public Vector2 pos, vel;
        public int damage = 2;
        public bool reflected;
        public GameObject owner;
        float life, frameClock;
        SpriteRenderer sr;
        static Sprite[] frames;
        LightBlob glow;

        public static Projectile Fireball(Vector2 at, Vector2 vel, GameObject owner)
        {
            if (frames == null)
            {
                frames = new Sprite[3];
                for (int i = 0; i < 3; i++) frames[i] = Map.GetSprite("Items/fireball_" + i, 6, 6);
            }
            var go = new GameObject("Fireball");
            go.transform.SetParent(Map.Current ? Map.Current.transform : null, false);
            var p = go.AddComponent<Projectile>();
            p.pos = at; p.vel = vel; p.owner = owner;
            p.sr = go.AddComponent<SpriteRenderer>();
            p.sr.sharedMaterial = Map.SpriteMat;
            p.sr.sprite = frames[0];
            p.glow = LightBlob.Create(go.transform, at, 2.2f, new Color(1f, 0.6f, 0.25f), 0.8f, true);
            Sfx.Play("fireball", 0.8f);
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
            if (((int)(life * 30)) % 3 == 0) Fx.Embers(pos + new Vector2(0, 0.5f), 1);
            if (life > 6f) { Burst(); return; }
            var p = Player.I;
            if (!reflected && p && p.state != Player.State.Dead && Vector2.Distance(p.pos + new Vector2(0, 0.2f), pos) < 0.55f)
            {
                if (p.TryReflect(vel))
                {
                    reflected = true;
                    var target = owner ? (Vector2)owner.transform.position : pos - vel;
                    vel = (target - pos).normalized * vel.magnitude * 1.25f;
                    return;
                }
                p.Hurt(new HitInfo { damage = damage, from = pos - vel.normalized, knockback = 7f, kind = HitKind.Fire, source = gameObject });
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
                    Vector2.Distance((Vector2)owner.transform.position + new Vector2(0, 1f), pos) < 1.6f)
                {
                    h.Hit(new HitInfo { damage = damage * 2, from = pos - vel.normalized, knockback = 0, kind = HitKind.Reflected, source = gameObject });
                    Burst();
                    return;
                }
            }
            if (Solids.Overlaps(new Rect(pos - new Vector2(0.15f, 0.1f), new Vector2(0.3f, 0.2f)), pos, owner ? owner.GetComponent<MonoBehaviour>() : null)) Burst();
        }

        void Burst()
        {
            for (int i = 0; i < 10; i++)
                Fx.Spawn(pos + new Vector2(0, 0.5f), Random.insideUnitCircle * 3f, 0.3f, Random.Range(1f, 4f), Random.Range(0.25f, 0.5f),
                    new Color(1f, 0.75f, 0.3f), new Color(0.6f, 0.15f, 0.05f), 6f, i % 3 == 0 ? 2 : 1);
            Sfx.Play("fire_burst", 0.7f);
            Destroy(gameObject);
        }
    }
}
