// The tuning forks. Each of the big dungeons has one, enamelled in its house's colour, and each
// belongs to its house: it is in his pack while he is inside that dungeon and nowhere else (the
// temple lends it, and takes it back at the door). Struck, it gives one of three answers: a plain note (nothing near);
// a higher one, shivering (a chest nobody has opened, in a room next door); the highest, shaking
// in his hand (a chest in this very room). Whatever room it has found goes on the dungeon's plan
// in the fork's colour, and stays there, shown open once the chest has been.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class Fork
    {
        public static string FoundFlag(string map, string room) => "fork_" + map + "_" + room;
        public static bool Owns(string dungeon) => Story.Has("item_fork_" + dungeon);
        /// <summary>The fork in his pack this moment: the one made for the dungeon he is standing in, if he has
        /// found it. Outside its dungeon a fork is not in the pack at all.</summary>
        public static string Here
        {
            get
            {
                var d = Game.I ? Dungeons.Of(Game.I.CurrentMap) : null;
                return d != null && Dungeons.HasFork(d.name) && Owns(d.name) ? d.name : null;
            }
        }

        /// <summary>What the last strike found: 0 nothing near, 1 next door, 2 here.</summary>
        public static int Last { get; private set; }

        public static int Strike(Player p)
        {
            string map = Game.I.CurrentMap;
            var plan = Dungeons.Of(map);
            string which = Here;
            if (which == null) return 0;
            int level = 0;
            if (Rooms.I && Rooms.I.current != null)
            {
                var fl = Dungeons.FloorOf(plan, map);
                string cur = Rooms.I.current.id;
                if (Dungeons.Shut(fl, cur) > 0) { level = 2; Story.Set(FoundFlag(map, cur)); }
                foreach (var n in Dungeons.Next(fl, cur))
                    if (Dungeons.Shut(fl, n) > 0) { if (level == 0) level = 1; Story.Set(FoundFlag(map, n)); }
            }
            Last = level;
            Sfx.Play("fork_" + level, 1f, 0f);
            p.StartCoroutine(Ring(p, which, level));
            if (level == 2) { PixelView.I.Shake(1, 0.55f); Buzz(); }
            return level;
        }

        /// <summary>The fork held up over his head, shivering if it has found something, and its note going out across the floor in rings.</summary>
        static IEnumerator Ring(Player p, string which, int level)
        {
            Color c = Dungeons.ForkColor(which);
            var go = new GameObject("Fork");
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sharedMaterial = Map.SpriteMat;
            sr.sprite = Map.GetSprite("Items/fork_" + which, 8, 16);
            sr.sortingOrder = Map.Order(p.pos.y) + 2;
            var at = p.pos + new Vector2(0, 2.5f);
            float life = 0.95f, next = 0;
            int rings = 0;
            for (float t = 0; t < life; t += Time.deltaTime)
            {
                if (!p) break;
                float shiver = level == 0 ? 0 : (level == 2 ? 1.6f : 0.8f) / 16f * Mathf.Sin(t * (level == 2 ? 95f : 70f));
                go.transform.position = (Vector3)(at + new Vector2(shiver, 0));
                if (t >= next && rings < 1 + level * 2)
                {
                    rings++; next += level == 2 ? 0.13f : 0.2f;
                    int n = 36;
                    float speed = 3.4f + level * 1.4f;
                    for (int i = 0; i < n; i++)
                    {
                        float a = i / (float)n * Mathf.PI * 2f;
                        var dir = new Vector2(Mathf.Cos(a), Mathf.Sin(a) * 0.62f);
                        Fx.Spawn(p.pos + dir * 0.3f, dir * speed, 1.5f, 0f, 0.42f + level * 0.08f, Color.Lerp(c, Color.white, 0.35f), c * 0.55f, 0f, i % 2 == 0 && level > 0 ? 2 : 1);
                    }
                }
                yield return null;
            }
            Object.Destroy(go);
        }

        static void Buzz()
        {
#if UNITY_ANDROID || UNITY_IOS
            if (Application.isMobilePlatform) Handheld.Vibrate();
#endif
        }
    }
}
