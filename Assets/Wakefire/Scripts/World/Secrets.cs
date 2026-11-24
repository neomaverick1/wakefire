// What a dungeon does not show on its plan. A doorway somebody walled up: a crack in the wall, a
// cut rings hollow on it, and the heavy blow (or the Sun Wheel) brings it down, both sides of the
// wall at once, for good ("door_" + its id). A room on no plan: its name comes up the first time
// he stands in it. (The stairs that wait under floors are Mech's; the ledges and the holes are
// Player's, in Heights.cs; a doorway only a dreamer has is nothing but a wall of the waking world.)
using UnityEngine;

namespace Wakefire
{
    public static class Secrets
    {
        /// <summary>A walled-up doorway comes down: every piece of it on this floor, and the doorway shows.</summary>
        public static bool Break(Prop hit)
        {
            var map = Map.Current;
            if (!map || !hit || hit.Kind != "crack" || string.IsNullOrEmpty(hit.data.id)) return false;
            string id = hit.data.id;
            for (int i = map.props.Count - 1; i >= 0; i--)
            {
                var pr = map.props[i];
                if (!pr || pr.data.id != id) continue;
                if (pr.Kind == "crack")
                {
                    Rubble(pr.Bounds);
                    map.props.RemoveAt(i);
                    pr.Clear();
                }
                else if (pr.Kind == "breach") pr.sr.enabled = true;
            }
            Story.Set("door_" + id);
            Sfx.Play("statue_break", 1f, 0.03f);
            Sfx.Play("stone_door", 0.7f, 0.05f);
            Sfx.Play("secret", 0.8f, 0);
            PixelView.I.Shake(3, 0.3f);
            HitStop.Do(0.1f);
            if (Story.I) Story.I.WallDown();
            return true;
        }

        /// <summary>A cut that was not enough: it rings, and that is all it does.</summary>
        public static void Ring(Prop wall)
        {
            Sfx.Play("clank", 0.7f, 0.1f);
            var b = wall.Bounds;
            Fx.Sparks(new Vector2(b.center.x, b.yMin + 0.6f), new Color(0.85f, 0.82f, 0.74f), 4);
            if (Story.I) Story.I.WallHollow();
        }

        static void Rubble(Rect b)
        {
            for (int i = 0; i < 26; i++)
            {
                var at = new Vector2(Random.Range(b.xMin, b.xMax), Random.Range(b.yMin, b.yMax));
                Fx.Spawn(at, Random.insideUnitCircle * 3.2f, Random.Range(0.3f, 1.6f), Random.Range(2f, 6f), Random.Range(0.4f, 0.9f),
                    i % 3 == 0 ? new Color(0.74f, 0.70f, 0.62f) : new Color(0.46f, 0.43f, 0.42f), new Color(0.18f, 0.16f, 0.20f), 17f, i % 4 == 0 ? 2 : 1);
            }
            Fx.Dust(new Vector2(b.center.x, b.yMin), 10);
        }

        /// <summary>He is standing, for the first time, in a room that is on no plan.</summary>
        public static void Found(Room r)
        {
            Sfx.Play("secret", 0.9f, 0);
            if (!string.IsNullOrEmpty(r.name)) Notices.Room(r.name);
            if (Story.I) Story.I.SecretRoom();
        }
    }
}
