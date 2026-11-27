// A look at the creatures where they live, with nothing in the way and the hero beside them for size:
// for the build machine's eyes only.   -wfScene zoo -wfZoo jackal|crab|medusa|thurifer
using System.Collections;
using System.Linq;
using UnityEngine;

namespace Wakefire
{
    public static class ZooTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["zoo"] = Run;

        /// <summary>A figure that only stands there in one pose: no mind of its own.</summary>
        static SpriteAnim Figure(string sheet, string anim, Vector2 at, Facing f, string look = null)
        {
            var go = new GameObject("Zoo " + sheet);
            go.transform.position = at;
            var srGo = new GameObject("Sprite");
            srGo.transform.SetParent(go.transform, false);
            var sr = srGo.AddComponent<SpriteRenderer>();
            sr.sharedMaterial = new Material(Map.SpriteMat);
            sr.sortingOrder = 100;
            var a = srGo.AddComponent<SpriteAnim>();
            a.sr = sr;
            a.modelAs = look;
            a.sheet = SpriteSheet.Load(sheet);
            a.Play(anim, f, true);
            go.AddComponent<ZooTick>().anim = a;
            return a;
        }

        class ZooTick : MonoBehaviour
        {
            public SpriteAnim anim;
            public Vector2 walk;
            void Update()
            {
                anim.Tick(Time.deltaTime);
                if (walk != Vector2.zero) transform.position += (Vector3)(walk * Time.deltaTime);
                var p = transform.position;
                anim.sr.sortingOrder = 100 - Mathf.RoundToInt(p.y * 4f);
            }
        }

        static void Clear()
        {
            foreach (var e in Object.FindObjectsByType<Enemy>(FindObjectsSortMode.None)) Object.Destroy(e.gameObject);
            foreach (var e in Object.FindObjectsByType<ZooTick>(FindObjectsSortMode.None)) Object.Destroy(e.gameObject);
        }

        static IEnumerator Hold(float seconds, Vector2 at)
        {
            var p = Player.I;
            for (float w = 0; w < seconds; w += Time.deltaTime) { p.health.hp = p.health.max; if (p.state == Player.State.Free) p.pos = at; yield return null; }
        }

        static IEnumerator Run(AutoTest t)
        {
            DialogueBox.AutoAdvance = 0.1f;
            string what = Boot.Arg("-wfZoo") ?? "jackal";
            if (what == "show")
            {
                // for the README: the animals where they live, round whoever has walked in on them
                foreach (var (map, spawn, a, b, tag) in new[] { ("terraces", "east", "tr_j0", "tr_j1", "jackals"), ("cliffs", "west", "cl_c1", "cl_c2", "crabs") })
                {
                    Game.I.EnterMap(map, spawn);
                    Fade.Set(0);
                    var hero = Player.I;
                    hero.SetState(Player.State.Free, "idle");
                    yield return new WaitForSeconds(0.6f);
                    var every = Object.FindObjectsByType<Enemy>(FindObjectsSortMode.None);
                    var ea = every.FirstOrDefault(e => e.markerId == a);
                    var eb = every.FirstOrDefault(e => e.markerId == b);
                    Vector2 mid = ea && eb ? ((Vector2)ea.transform.position + (Vector2)eb.transform.position) * 0.5f : hero.pos;
                    Clear();
                    bool jackals = tag == "jackals";
                    mid += jackals ? new Vector2(2.7f, -0.3f) : new Vector2(2.4f, 0.6f);
                    hero.pos = mid; hero.Face(jackals ? Facing.Left : Facing.Down);
                    yield return Hold(0.4f, mid);
                    if (jackals)
                    {
                        Figure("jackal", "crouch", mid + new Vector2(-2.4f, -1.0f), Facing.Right);
                        var leap = Figure("jackal", "lunge", mid + new Vector2(2.3f, 1.3f), Facing.Left);
                        leap.model.height = 0.4f;
                        var run = Figure("jackal", "run", mid + new Vector2(-7.4f, 2.5f), Facing.Right);
                        run.GetComponentInParent<ZooTick>().walk = new Vector2(2.2f, -0.5f);
                        Figure("jackal", "idle", mid + new Vector2(4.8f, -2.7f), Facing.Up);
                    }
                    else
                    {
                        Figure("crab", "attack", mid + new Vector2(-2.3f, -0.7f), Facing.Right);
                        var walk = Figure("crab", "walk", mid + new Vector2(3.6f, -1.5f), Facing.Left);
                        walk.GetComponentInParent<ZooTick>().walk = new Vector2(-0.9f, 0);
                        Figure("crab", "idle", mid + new Vector2(0.5f, -2.9f), Facing.Up);
                        Figure("crab", "attack", mid + new Vector2(3.9f, 1.0f), Facing.Left);
                        Figure("crab", "idle", mid + new Vector2(-4.4f, 1.5f), Facing.Right);
                    }
                    for (int i = 0; i < 6; i++)
                    {
                        yield return Hold(0.22f, mid);
                        if (i % 2 == 1) { Controls.FakePress = Controls.Attack; yield return Hold(0.13f, mid); }
                        yield return t.Shot($"s{i}-{tag}", 0f);
                    }
                }
                yield break;
            }
            if (what == "jackal" || what == "crab")
            {
                bool jackal = what == "jackal";
                Game.I.EnterMap(jackal ? "terraces" : "cliffs", jackal ? "east" : "west");
                Fade.Set(0);
                var p = Player.I;
                p.SetState(Player.State.Free, "idle");
                yield return new WaitForSeconds(0.6f);
                var all = Object.FindObjectsByType<Enemy>(FindObjectsSortMode.None);
                string a = jackal ? "tr_j0" : "cl_c1", b = jackal ? "tr_j1" : "cl_c2";
                var ea = all.FirstOrDefault(e => e.markerId == a);
                var eb = all.FirstOrDefault(e => e.markerId == b);
                Vector2 c = ea && eb ? ((Vector2)ea.transform.position + (Vector2)eb.transform.position) * 0.5f : p.pos;
                t.Note($"zoo {what}: centre {c} (found {(ea ? 1 : 0) + (eb ? 1 : 0)} of 2)");
                Clear();
                if (Hud.I) Hud.I.gameObject.SetActive(false);
                p.pos = c; p.Face(Facing.Down);
                yield return Hold(0.5f, c);
                string sheet = jackal ? "jackal" : "crab";
                string[] row1 = jackal ? new[] { "idle", "idle", "idle", "idle" } : new[] { "idle", "idle", "walk", "attack" };
                Facing[] face1 = { Facing.Left, Facing.Down, Facing.Right, Facing.Up };
                for (int i = 0; i < 4; i++) Figure(sheet, row1[i], c + new Vector2(-6.6f + i * 4.4f, 2.7f), face1[i]);
                if (jackal)
                {
                    Figure(sheet, "crouch", c + new Vector2(-6.4f, -2.6f), Facing.Right);
                    var leap = Figure(sheet, "lunge", c + new Vector2(-2.4f, -2.6f), Facing.Right);
                    leap.model.height = 0.45f;
                    var run = Figure(sheet, "run", c + new Vector2(1.2f, -2.9f), Facing.Right);
                    run.GetComponentInParent<ZooTick>().walk = new Vector2(2.6f, 0);
                    Figure(sheet, "hurt", c + new Vector2(3.4f, -0.4f), Facing.Left);
                    Figure("jackal", "idle", c + new Vector2(-5.2f, 0.1f), Facing.Right, "den_mother");
                }
                else
                {
                    var walk = Figure(sheet, "walk", c + new Vector2(-6.4f, -2.6f), Facing.Down);
                    walk.GetComponentInParent<ZooTick>().walk = new Vector2(1.2f, 0);
                    Figure(sheet, "attack", c + new Vector2(-1.6f, -2.7f), Facing.Left);
                    Figure(sheet, "attack", c + new Vector2(2.6f, -2.7f), Facing.Right);
                    Figure(sheet, "hurt", c + new Vector2(5.8f, -2.4f), Facing.Down);
                }
                for (int i = 0; i < 4; i++)
                {
                    yield return Hold(i == 0 ? 0.6f : 0.21f, c);
                    yield return t.Shot($"z{i}-{what}", 0f);
                }
                yield break;
            }
            if (what.StartsWith("dream")) { yield return ZooDreams(t, what); yield break; }
            yield return ZooIndoors(t, what);
        }

        /// <summary>The bad dreams, in the gate square at night with Azar beside them for size.
        /// dream1: Snuffers. dream2: Wicks, the Dragnet and a net that is only a net. dream3: Stay-Ups.</summary>
        static IEnumerator ZooDreams(AutoTest t, string what)
        {
            Story.DreamsQuiet = true;
            Game.I.EnterMap("ashkel", "south");
            Fade.Set(0);
            var p = Player.I;
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.6f);
            Clear();
            if (Hud.I) Hud.I.gameObject.SetActive(false);
            Vector2 c = Map.ToWorld(480, 212);
            // (an empty square: nothing standing between the lens and what is being looked at)
            foreach (var pr in Map.Current.props) if (pr && Vector2.Distance(pr.basePos, c) < 16f) pr.gameObject.SetActive(false);
            foreach (var n in Npc.All) if (n) n.gameObject.SetActive(false);
            p.pos = c; p.Face(Facing.Down);
            yield return Hold(0.4f, c);
            if (what == "dream1")
            {
                Figure("moth", "idle", c + new Vector2(-7.0f, 2.2f), Facing.Down, "snuffer");
                var w = Figure("moth", "walk", c + new Vector2(-4.8f, 2.4f), Facing.Right, "snuffer");
                w.GetComponentInParent<ZooTick>().walk = new Vector2(1.2f, 0);
                Figure("moth", "sniff", c + new Vector2(3.6f, 2.2f), Facing.Left, "snuffer");
                Figure("moth", "rear", c + new Vector2(7.0f, 2.0f), Facing.Down, "snuffer");
                Figure("moth", "cover", c + new Vector2(-7.0f, -2.6f), Facing.Down, "snuffer");
                Figure("moth", "tipped", c + new Vector2(-3.4f, -2.8f), Facing.Right, "snuffer");
                Figure("moth", "hot", c + new Vector2(3.4f, -2.6f), Facing.Down, "snuffer");
                Figure("moth", "sniff", c + new Vector2(7.2f, -2.8f), Facing.Up, "snuffer");
            }
            else if (what == "dream2")
            {
                Figure("moth", "idle", c + new Vector2(-7.4f, 2.4f), Facing.Down, "wick");
                var w = Figure("moth", "walk", c + new Vector2(-5.6f, 2.4f), Facing.Right, "wick");
                w.GetComponentInParent<ZooTick>().walk = new Vector2(2.0f, 0);
                Figure("moth", "dart", c + new Vector2(-2.6f, 2.4f), Facing.Down, "wick");
                Figure("moth", "flat", c + new Vector2(3.0f, 2.6f), Facing.Down, "dragnet");
                Figure("moth", "flat", c + new Vector2(6.6f, 2.6f), Facing.Down, "net");
                Figure("moth", "rise", c + new Vector2(-6.6f, -2.8f), Facing.Down, "dragnet");
                Figure("moth", "cast", c + new Vector2(-3.0f, -2.4f), Facing.Down, "dragnet");
                Figure("moth", "wrap", c + new Vector2(3.2f, -2.8f), Facing.Down, "dragnet");
                Figure("moth", "spent", c + new Vector2(6.8f, -2.6f), Facing.Down, "dragnet");
            }
            else
            {
                foreach (var (at, anim, f) in new[] { (new Vector2(-6.5f, 2.4f), "idle", Facing.Down), (new Vector2(-2.6f, 2.6f), "walk", Facing.Right),
                                                      (new Vector2(3.0f, 2.4f), "grip", Facing.Right), (new Vector2(-5.0f, -1.6f), "walk", Facing.Down) })
                {
                    var e = StayUp.Spawn(c + at);
                    e.enabled = false;                  // (a look at it, not a fight: it stays where it is put)
                    e.anim.Play(anim, f, true);
                    e.gameObject.AddComponent<ZooTick>().anim = e.anim;
                }
            }
            for (int i = 0; i < 4; i++)
            {
                yield return Hold(i == 0 ? 0.9f : 0.35f, c);
                yield return t.Shot($"d{i}-{what}", 0f);
            }
        }

        /// <summary>The ziggurat's people, in a hall of the ziggurat with the lights on.</summary>
        static IEnumerator ZooIndoors(AutoTest t, string what)
        {
            Game.I.EnterMap("zig_1", "south");
            Fade.Set(0);
            var p = Player.I;
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.8f);
            Clear();
            if (Hud.I) Hud.I.gameObject.SetActive(false);
            var room = Rooms.I.current;
            Vector2 c = room != null ? room.rect.center : p.pos;
            t.Note($"zoo {what}: room {(room != null ? room.id : "?")} centre {c}");
            Vector2 stand = c + new Vector2(0, -0.4f);
            p.pos = stand; p.Face(Facing.Up);
            yield return Hold(0.5f, stand);
            SpriteAnim stone = null;
            if (what == "medusa")
            {
                Figure("priest", "comb", c + new Vector2(-7.5f, 2.6f), Facing.Up, "medusa");
                Figure("priest", "comb", c + new Vector2(-4.5f, 2.6f), Facing.Down, "medusa");
                Figure("priest", "idle", c + new Vector2(-1.5f, 2.6f), Facing.Down, "medusa");
                Figure("priest", "stare", c + new Vector2(1.5f, 2.6f), Facing.Down, "medusa");
                Figure("priest", "stare", c + new Vector2(4.5f, 2.6f), Facing.Left, "medusa");
                Figure("priest", "stare", c + new Vector2(7.5f, 2.6f), Facing.Right, "medusa");
                var walk = Figure("priest", "walk", c + new Vector2(-7.5f, -2.9f), Facing.Right, "medusa");
                walk.GetComponentInParent<ZooTick>().walk = new Vector2(1.0f, 0);
                Figure("priest", "idle", c + new Vector2(-3.2f, -2.9f), Facing.Left, "medusa");
                Figure("priest", "stare", c + new Vector2(3.4f, -2.9f), Facing.Up, "medusa");
                stone = Figure("priest", "stare", c + new Vector2(6.8f, -2.9f), Facing.Down, "medusa");
            }
            if (what == "halls")
            {
                Thurifer.Spawn(c + new Vector2(-3.3f, 1.2f));
                BurningGlass.Spawn(c + new Vector2(3.4f, 2.6f));
                Figure("priest", "swing", c + new Vector2(-7.5f, -2.9f), Facing.Down, "thurifer");
                Figure("priest", "cough", c + new Vector2(-5.0f, -2.9f), Facing.Down, "thurifer");
                Figure("priest", "cast", c + new Vector2(-2.6f, -2.9f), Facing.Right, "thurifer");
                Figure("moth", "idle", c + new Vector2(2.8f, -2.7f), Facing.Down, "glass");
                Figure("moth", "gather", c + new Vector2(5.4f, -2.7f), Facing.Left, "glass");
                Figure("moth", "cracked", c + new Vector2(8.0f, -2.7f), Facing.Right, "glass");
                Figure("moth", "idle", c + new Vector2(0.9f, -3.0f), Facing.Down, "censer");
                for (int i = 0; i < 12; i++)
                {
                    yield return Hold(0.5f, stand);
                    yield return t.Shot($"h{i:00}-halls", 0f);
                }
                yield break;
            }
            for (int i = 0; i < 4; i++)
            {
                yield return Hold(i == 0 ? 0.9f : 0.27f, stand);
                if (i == 0 && stone)
                {
                    stone.sr.sharedMaterial.SetFloat("_Stone", 1f);
                    if (stone.model) stone.model.frozen = true;
                }
                yield return t.Shot($"z{i}-{what}", 0f);
            }
        }
    }
}
