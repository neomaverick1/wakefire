// The king's tomb, played through: -wfScene tomb takes Azar in at the king's door on the hill,
// through the outer halls (the thieves and their goat, the servants and their order, the scale,
// the treasury's dream key, the lamp bearers, the well), up into the inner halls (the cut, the
// Sun Roller and the Sun Wheel, the three gongs, the wardens, the rope and the four fires) and
// on through the door with the sun on it. -wfScene roller is the Sun Roller against somebody who
// has watched which way the sparks go: four rounds.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class TombTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register()
        {
            AutoTest.Scenes["tomb"] = Run;
            AutoTest.Scenes["roller"] = Roller;
            AutoTest.Scenes["wheel"] = Wheel;
            AutoTest.Scenes["tombcast"] = Cast;
        }

        static Vector2 InRoom(string id, float x, float y)
        {
            var r = Rooms.I.Find(id);
            return new Vector2(r.rect.xMin + x / 16f, r.rect.yMax - y / 16f);
        }

        /// <summary>Where Azar is in a room, in the pixels its plan was drawn in.</summary>
        static Vector2 Local(string id)
        {
            var r = Rooms.I.Find(id);
            var p = Player.I.pos;
            return new Vector2((p.x - r.rect.xMin) * 16f, (r.rect.yMax - p.y) * 16f);
        }

        static IEnumerator Walk(Vector2 dir, float seconds, float settle = 0.5f)
        {
            Controls.Fake = dir;
            yield return new WaitForSeconds(seconds);
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(settle);
        }

        static IEnumerator WalkUntil(Vector2 dir, System.Func<bool> done, float atMost)
        {
            Controls.Fake = dir;
            for (float w = 0; w < atMost && !done(); w += Time.deltaTime) yield return null;
            Controls.Fake = Vector2.zero;
            yield return new WaitForSeconds(0.2f);
        }

        static IEnumerator Scene(float atLeast = 0.4f, float atMost = 60f)
        {
            float w = 0;
            while ((w < atLeast || (Story.I && Story.I.Running) || Game.Busy) && w < atMost) { w += Time.deltaTime; yield return null; }
        }

        /// <summary>Put him somewhere in a room. (Coming into a room the game marches him a few steps on from its
        /// door, so he is put back until he stays put; nowhere this is used is within four steps north of a way out
        /// of the map.)</summary>
        static IEnumerator Stand(string room, float x, float y, Facing face)
        {
            var p = Player.I;
            for (int i = 0; i < 3; i++)
            {
                p.pos = InRoom(room, x, y);
                p.Face(face);
                yield return null; yield return null;
                for (float s = 0; s < 3f && (Rooms.Sliding || Game.Busy); s += Time.deltaTime) yield return null;
                if (Rooms.I.current != null && Rooms.I.current.id == room && Vector2.Distance(p.pos, InRoom(room, x, y)) < 0.05f) break;
            }
            yield return Scene(0.2f);
            p.pos = InRoom(room, x, y);
            p.Face(face);
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.15f);
        }

        static IEnumerator Press(UnityEngine.InputSystem.InputAction a, float wait = 0.3f)
        {
            Controls.FakePress = a;
            yield return new WaitForSeconds(wait);
        }

        static IEnumerator Sleep(bool on)
        {
            var p = Player.I;
            if (on) { Dream.I.Drowsiness = 1; Dream.I.Seconds = 9999; Dream.I.Flip(p.pos, true); yield return new WaitForSeconds(1.2f); }
            else { Dream.I.Flip(p.pos, false); yield return new WaitForSeconds(1.2f); Dream.I.SetInstant(false); Story.I.ApplyItems(); Dream.I.Drowsiness = 1; }
        }

        static void Kill(Enemy e)
        {
            if (e && !e.health.Dead) e.Hit(new HitInfo { damage = 99, from = Player.I.pos, knockback = 0, kind = HitKind.Reflected, source = Player.I.gameObject });
        }

        static void KillAll()
        {
            foreach (var e in Enemy.All.ToArray()) Kill(e);
        }

        static int Count<T>() where T : Enemy
        {
            int n = 0;
            foreach (var e in Enemy.All) if (e is T && !e.health.Dead) n++;
            return n;
        }

        static T Nearest<T>() where T : Enemy
        {
            T best = null;
            foreach (var e in Enemy.All)
                if (e is T t && !e.health.Dead && (best == null || Vector2.Distance(e.pos, Player.I.pos) < Vector2.Distance(best.pos, Player.I.pos))) best = t;
            return best;
        }

        static bool Shut(string id)
        {
            foreach (var pr in Map.Current.props) if (pr && pr.data.id == id && pr.Kind == "bars") return pr.sr.enabled;
            return false;
        }

        /// <summary>Stand under a thing, face it.</summary>
        static IEnumerator Under(string id, float below = 0.7f)
        {
            var p = Player.I;
            var pr = Map.Current.Find(id);
            if (!pr) yield break;
            p.pos = pr.basePos + new Vector2(0, -below); p.Face(Facing.Up);
            yield return null; yield return null;
            for (float s = 0; s < 3f && (Rooms.Sliding || Game.Busy); s += Time.deltaTime) yield return null;
            yield return Scene(0.2f);
            p.pos = pr.basePos + new Vector2(0, -below); p.Face(Facing.Up);
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.2f);
        }

        static IEnumerator Open(string id, float below = 0.7f)
        {
            yield return Under(id, below);
            yield return Press(Controls.Interact);
            yield return Scene();
        }

        /// <summary>Hold the Wakefire out to a fire altar.</summary>
        static IEnumerator Light(string id)
        {
            Items.Chosen = "wakefire";
            yield return Under(id, 0.85f);
            yield return Press(Controls.Item, 0.9f);
            yield return Scene();
        }

        /// <summary>Throw the Sun Wheel and wait for it to come home.</summary>
        static IEnumerator Throw(Vector2 dir, float atMost = 7f)
        {
            var p = Player.I;
            Items.Chosen = "wheel";
            p.SetState(Player.State.Free, "idle");
            p.ThrowWheel(dir);
            float w = 0;
            for (; w < 0.8f && Thrown.Out("wheel") == 0; w += Time.deltaTime) yield return null;
            for (w = 0; w < atMost && Thrown.Out("wheel") > 0; w += Time.deltaTime) yield return null;
            yield return new WaitForSeconds(0.15f);
        }

        static bool Lit(string id) { var b = Map.Current.Find(id); return b && b.lit; }

        static void Kit(params string[] more)
        {
            Save.ClearAll(); Save.Use(0);
            Game.I.Begin(false);
            Story.Abort();
            Story.GiveKit();
            // as he comes to the king's door: the shield, the Pocket, and the three names said
            foreach (var f in new[] { "item_shield", "ch2", "chapter_done", "item_hillkey", "hill_gate", "met_namtar", "queue_passed", "item_pocket",
                                      "name_kur", "name_ash", "name_tar", "king_door", "bw_red", "bw_blue", "dead_bw_piece" }) Story.Set(f);
            foreach (var f in more) Story.Set(f);
            Items.Chosen = "wakefire";
            Story.I.ApplyItems();
        }

        static IEnumerator Run(AutoTest t)
        {
            int bad = 0;
            void Check(string what, bool ok) { t.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
            DialogueBox.AutoAdvance = 0.1f;
            Kit();
            var p = Player.I;
            // ------------------------------------------------ the king's door, on the hill
            Game.I.EnterMap("necropolis", "door");
            Fade.Set(0);
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.5f);
            KillAll();
            yield return Scene(0.3f);
            yield return WalkUntil(Vector2.up, () => Game.I.CurrentMap != "necropolis", 5f);
            yield return new WaitForSeconds(0.9f);
            yield return Scene(0.5f);
            Check("the king's door lets him into the outer halls", Game.I.CurrentMap == "tomb_1" && Game.I.CurrentSpawn == "south");
            if (Game.I.CurrentMap != "tomb_1") { Game.I.EnterMap("tomb_1", "south"); Fade.Set(0); yield return new WaitForSeconds(0.5f); yield return Scene(0.5f); }
            Check("he is in the antechamber, and it has been said what the air is like", Rooms.I.current != null && Rooms.I.current.id == "door" && Story.Count("tomb_seen_tomb_1_door") == 1);
            KillAll();
            yield return t.Shot("t01-antechamber", 0.3f);

            // ------------------------------------------------ a thief's dream of a goat
            var goat = Map.Current.Find("t1_goat");
            Check("awake there is no goat", goat && p.Action != Player.Act.Take);
            yield return Sleep(true);
            yield return Under("t1_goat", 0.6f);
            Check("in Zimu's dream there is a whole gold goat, and the button says Take", p.Action == Player.Act.Take);
            yield return t.Shot("t02-the-goat", 0.1f);
            yield return Press(Controls.Interact);
            yield return Scene();
            Check("the goat goes in the Pocket", Pocket.Holding != null && Pocket.Holding.id == "goat");
            Check("and there is always another one", goat && goat.sr.enabled);
            yield return Sleep(false);

            // ------------------------------------------------ the servants, and the order they were left with
            yield return Stand("servants", 208, 180, Facing.Up);
            yield return Walk(Vector2.up, 1.4f);
            Check($"the king's servants will not let a waking man by (y {Local("servants").y:0})", Local("servants").y > 90);
            yield return t.Shot("t03-servants", 0.1f);
            yield return Sleep(true);
            yield return Stand("servants", 208, 104, Facing.Up);
            Check("in the dream they are not there, and their order is: the button says Take", p.Action == Player.Act.Take);
            yield return t.Shot("t04-the-order", 0.1f);
            yield return Press(Controls.Interact);
            yield return Scene();
            Check("the order goes in the Pocket (and the goat goes back to the dream it came from)", Pocket.Holding != null && Pocket.Holding.id == "order");
            yield return WalkUntil(Vector2.up, () => Local("servants").y < 70, 3f);
            Check($"a dreamer walks through where they stand (y {Local("servants").y:0})", Local("servants").y < 76);
            yield return Stand("servants", 208, 150, Facing.Up);
            yield return Sleep(false);
            yield return Scene(0.8f);
            Check("awake, with nobody telling them anything, the servants sit down", Story.Count("servants_sat") == 1);
            yield return t.Shot("t05-servants-sit", 0.1f);
            yield return WalkUntil(Vector2.up, () => Local("servants").y < 70, 3f);
            Check($"and a waking man walks through the doorway (y {Local("servants").y:0})", Local("servants").y < 76);

            // ------------------------------------------------ the pillared hall: STAND THERE
            yield return Stand("hall", 208, 196, Facing.Up);
            yield return Scene(0.5f);
            Check("two of the king's clay stand in the pillared hall", Count<Ushabti>() == 2);
            // close enough to wake them, then let the order out at them
            var clay = Nearest<Ushabti>();
            if (clay) { p.pos = clay.pos + new Vector2(0, -2.6f); p.Face(Facing.Up); }
            for (float w = 0; w < 3f && clay && !clay.Awake; w += Time.deltaTime) yield return null;
            Check("they step out of their niches at a visitor", clay && clay.Awake);
            if (clay) { p.pos = clay.pos + new Vector2(0, -2.6f); p.Face(Facing.Up); p.SetState(Player.State.Free, "idle"); }
            Items.Chosen = "pocket";
            yield return Press(Controls.Item, 0.9f);
            yield return Scene();
            Check("the order is given, and is gone", Pocket.Holding == null && Story.Has("spent_t1_order") && Story.Count("order_used") == 1);
            var where = new System.Collections.Generic.Dictionary<Enemy, Vector2>();
            foreach (var e in Enemy.All) if (e is Ushabti && !e.health.Dead) where[e] = e.pos;
            int hpO = p.health.hp;
            yield return new WaitForSeconds(2.5f);
            bool stood = where.Count == 2;
            foreach (var kv in where) if (!kv.Key || Vector2.Distance(kv.Key.pos, kv.Value) > 0.05f) stood = false;
            Check("the clay stands there: nothing moves, nobody is hit", stood && p.health.hp == hpO);
            yield return t.Shot("t06-stand-there", 0.1f);
            KillAll();
            yield return new WaitForSeconds(0.5f);
            yield return Open("t1_fork");
            Check("the carnelian fork", Story.Has("item_fork_tomb"));
            yield return Stand("servants", 208, 150, Facing.Up);
            yield return Scene(0.5f);
            bool sitting = false;
            foreach (var n in Npc.All) if (n && n.id == "servant_1") sitting = true;
            yield return WalkUntil(Vector2.up, () => Local("servants").y < 70, 3f);
            Check("an order that has been given does not go back: the servants stay sat, and the way stays open", sitting && Local("servants").y < 76 && Story.Count("servants_sat") == 1);

            // ------------------------------------------------ the offering store: one goat, in gold
            yield return Stand("door", 110, 120, Facing.Up);
            yield return Sleep(true);
            yield return Under("t1_goat", 0.6f);
            yield return Press(Controls.Interact);
            yield return Scene();
            yield return Sleep(false);
            Check("another goat, out of the same dream", Pocket.Holding != null && Pocket.Holding.id == "goat");
            yield return Stand("store", 150, 112, Facing.Left);
            yield return Scene(0.5f);
            KillAll();
            Check("the grille in the store is down", Shut("t1_storebars"));
            yield return Under("t1_scale", 0.75f);
            Check("in front of the scale the button says Look", p.Action == Player.Act.Look);
            yield return t.Shot("t07-the-scale", 0.1f);
            Items.Chosen = "pocket";
            yield return Press(Controls.Item, 0.9f);
            yield return Scene();
            yield return new WaitForSeconds(0.6f);
            yield return Scene();
            Check("the goat is in the pan, and the Pocket is empty", Story.Has("on_t1_scale") && Pocket.Holding == null);
            Check("the king has been paid: the grille lifts", !Shut("t1_storebars"));
            yield return t.Shot("t08-paid", 0.1f);
            yield return Open("t1_map");
            Check("the scroll of the king's tomb", Story.Has("item_map_tomb"));

            // ------------------------------------------------ the treasury: a key that is only anywhere in a dream
            yield return Stand("treasury", 190, 66, Facing.Up);
            yield return Scene(0.5f);
            Check("awake, the hook is empty", p.Action != Player.Act.Take);
            yield return Sleep(true);
            yield return Stand("treasury", 190, 66, Facing.Up);
            Check("in the dream the steward's key hangs on it", p.Action == Player.Act.Take);
            yield return Press(Controls.Interact);
            yield return Scene();
            yield return Sleep(false);
            Check("the dream key comes back awake", Pocket.Holding != null && Pocket.Holding.id == "key");
            yield return Under("t1_strong", 0.8f);
            yield return t.Shot("t09-treasury", 0.1f);
            Items.Chosen = "pocket";
            yield return Press(Controls.Item, 0.9f);
            yield return Scene();
            Check("it opens the treasury's strongroom", Story.Has("door_t1_strong") && Pocket.Holding == null);
            int keys0 = p.keys;
            yield return Open("t1_key");
            Check("a key that is really there", p.keys == keys0 + 1);

            // ------------------------------------------------ the lamp walk
            yield return Stand("lampwalk", 40, 128, Facing.Right);
            yield return Scene(0.6f);
            Check("two lamp bearers keep the walk", Count<LampBearer>() == 2);
            yield return t.Shot("t10-lamp-walk", 0.2f);
            for (int n = 0; n < 2; n++)
            {
                var b = Nearest<LampBearer>();
                if (!b) break;
                string id = b.spawnId;
                p.health.hp = p.health.max;
                p.pos = b.pos + new Vector2(-0.95f, 0); p.Face(Facing.Right); p.SetState(Player.State.Free, "idle");
                yield return new WaitForSeconds(0.1f);
                if (n == 0)
                {
                    int bh = b.health.hp;
                    yield return Press(Controls.Attack, 0.5f);
                    yield return Scene();
                    Check("a blade goes through a bearer like a hand through lamp smoke", b && b.health.hp == bh && Story.Count("bearer_passed") == 1);
                }
                yield return Sleep(true);
                if (b) { p.pos = b.pos + new Vector2(-0.95f, 0); p.Face(Facing.Right); p.SetState(Player.State.Free, "idle"); }
                yield return new WaitForSeconds(0.2f);
                if (n == 0)
                {
                    Check("in the dream he is not there, and his lamp is", b && !b.Present && b.lamp && b.lamp.Lit);
                    yield return t.Shot("t11-a-lamp-and-nobody", 0.1f);
                }
                yield return Press(Controls.Attack, 0.5f);
                yield return Scene();
                if (n == 0) Check("the lamp is knocked out of the air", b && b.lamp && !b.lamp.Lit);
                yield return Sleep(false);
                p.health.hp = p.health.max;
                for (float w = 0; w < 8f && b && !b.health.Dead; w += Time.deltaTime) yield return null;
                yield return Scene(0.5f);
                Check($"with nothing to carry, bearer {n + 1} goes off duty", !b && Story.Has("dead_" + id));
            }
            Check("the walk is empty, and somebody said so", Count<LampBearer>() == 0 && Story.Count("bearer_off") >= 1);

            // ------------------------------------------------ the well
            yield return Stand("well", 100, 128, Facing.Right);
            yield return Scene(0.5f);
            KillAll();
            int hpW = p.health.hp;
            yield return Walk(Vector2.right, 0.9f);
            Check($"the well stops a waking man (x {Local("well").x:0})", Local("well").x < 152 && p.health.hp == hpW);
            yield return Stand("well", 100, 128, Facing.Right);
            yield return Sleep(true);
            yield return t.Shot("t12-the-well", 0.1f);
            yield return WalkUntil(Vector2.right, () => Local("well").x > 280, 4f);
            Check($"a dreamer crosses it on moonlight (x {Local("well").x:0})", Local("well").x > 270);
            yield return Sleep(false);
            int max0 = p.health.max;
            yield return Open("t1_vessel");
            Check("a flame vessel on the far side", p.health.max == max0 + 2);

            // ------------------------------------------------ the stair
            yield return Stand("hall", 208, 100, Facing.Up);
            KillAll();
            keys0 = p.keys;
            yield return Open("t1_door", 0.85f);
            Check("the stair door takes the key", Story.Has("door_t1_door") && p.keys == keys0 - 1);
            yield return WalkUntil(Vector2.up, () => Game.I.CurrentMap != "tomb_1", 5f);
            yield return new WaitForSeconds(0.9f);
            yield return Scene(0.5f);
            Check("up the stair into the inner halls", Game.I.CurrentMap == "tomb_2" && Game.I.CurrentSpawn == "south");
            if (Game.I.CurrentMap != "tomb_2") { Game.I.EnterMap("tomb_2", "south"); Fade.Set(0); yield return new WaitForSeconds(0.5f); yield return Scene(0.5f); }

            // ================================================ 2F
            KillAll();
            Check("he comes up into the hall of the lyre", Rooms.I.current != null && Rooms.I.current.id == "lyre");
            yield return t.Shot("t13-hall-of-the-lyre", 0.3f);
            yield return Light("lyre_0");
            Check("the first of four fires", Lit("lyre_0") && !Story.Has("door_t2_seal") && Story.Count("lyre_first") == 1);
            yield return Stand("lyre", 120, 296, Facing.Up);
            yield return Walk(Vector2.up, 1.0f);
            Check($"the cut stops a waking man (y {Local("lyre").y:0})", Local("lyre").y > 264);
            yield return Stand("lyre", 120, 296, Facing.Up);
            yield return Sleep(true);
            yield return WalkUntil(Vector2.up, () => Local("lyre").y < 210, 4f);
            Check($"a dreamer crosses it (y {Local("lyre").y:0})", Local("lyre").y < 226);
            yield return Sleep(false);
            KillAll();
            yield return Light("lyre_1");
            Check("the second fire", Lit("lyre_1") && !Story.Has("door_t2_seal"));
            Check("east is barred, and its gong hangs over a drop", Shut("t2_eastbars") && !Story.Has("on_t2_gong0"));
            yield return Stand("lyre", 340, 108, Facing.Up);
            yield return Press(Controls.Attack, 0.5f);
            Check("a blade does not reach it", !Story.Has("on_t2_gong0"));
            yield return t.Shot("t14-a-gong-out-of-reach", 0.1f);

            // ------------------------------------------------ the bearers' way
            yield return Stand("westpass", 370, 128, Facing.Left);
            yield return Scene(0.5f);
            Check("two more bearers keep the way west", Count<LampBearer>() == 2);
            yield return t.Shot("t15-bearers-way", 0.2f);
            KillAll();
            yield return new WaitForSeconds(0.5f);

            // ------------------------------------------------ the hall of the sun
            p.health.hp = p.health.max;
            yield return Stand("westpass", 60, 128, Facing.Left);
            yield return WalkUntil(Vector2.left, () => Rooms.I.current != null && Rooms.I.current.id == "roller", 4f);
            for (float w = 0; w < 3f && (Rooms.Sliding || Game.Busy); w += Time.deltaTime) yield return null;
            var roller = SunRoller.Current;
            Check("the Sun Roller is up on its sun", roller);
            yield return t.Shot("t16-the-sun-roller", 0.1f);
            yield return Scene(1.0f);
            Check("it notices the sun has a visitor", roller && !roller.Waiting && Story.Count("roller_seen") == 1);
            Check("the hall shuts, and the great chest is caged", Shut("t2_rollerdoor") && Shut("t2_cage"));
            if (roller)
            {
                int rh = roller.health.hp;
                roller.Hit(new HitInfo { damage = 1, from = p.pos, knockback = 0, kind = HitKind.Slash, source = p.gameObject });
                Check("its shell turns a blade", roller.health.hp == rh);
                bool rolled = false; int most = 0;
                for (float w = 0; w < 25f && roller && !roller.Tumbled; w += Time.deltaTime)
                {
                    // out of the way, wherever that is this second: opposite the ball
                    if (p.state == Player.State.Free)
                    {
                        var c = Rooms.I.Find("roller").rect.center;
                        var away = c + (c - roller.BallPos).normalized * 2.5f + new Vector2(0, -1.5f);
                        if (Vector2.Distance(p.pos, roller.BallPos) < 3f) p.pos = away;
                    }
                    p.health.hp = p.health.max;
                    if (roller.BallVel.sqrMagnitude > 1f) rolled = true;
                    most = Mathf.Max(most, roller.Banks);
                    yield return null;
                }
                Check($"the sun rolls, banks off two walls and stops at the third (walls {most})", rolled && most >= Thrown.MaxBanks + 1);
                Check("and the beetle on top of it does not stop: it is on its back", roller && roller.Tumbled);
                yield return t.Shot("t17-on-its-back", 0.25f);
                yield return Scene(0.3f);
                if (roller)
                {
                    rh = roller.health.hp;
                    p.pos = roller.pos + new Vector2(0, -1.0f); p.Face(Facing.Up); p.SetState(Player.State.Free, "idle");
                    yield return new WaitForSeconds(0.1f);
                    yield return Press(Controls.Attack, 0.5f);
                    Check("on its back, the blade gets in", roller && roller.health.hp < rh);
                }
                Kill(roller);
                yield return new WaitForSeconds(1.6f);
                yield return Scene(0.5f);
            }
            Check("the Sun Roller is down for good", Story.Has("dead_t2_roller"));
            yield return new WaitForSeconds(0.6f);
            Check("the cage lifts, and the door", !Shut("t2_cage") && !Shut("t2_rollerdoor"));
            p.health.hp = p.health.max;
            foreach (var pk in Object.FindObjectsByType<Pickup>(FindObjectsSortMode.None)) Object.Destroy(pk.gameObject);
            yield return Open("t2_wheel");
            Check("the Sun Wheel", Story.Has("item_wheel") && Items.Current != null && Items.Current.id == "wheel");
            yield return t.Shot("t18-the-sun-wheel", 0.2f);

            // ------------------------------------------------ three gongs
            Check("north is barred", Shut("t2_northbars"));
            yield return Stand("roller", 332, 112, Facing.Up);
            yield return Press(Controls.Attack, 0.5f);
            Check("the gong over the drop is out of a blade's reach", !Story.Has("on_t2_gong1"));
            yield return Stand("roller", 332, 112, Facing.Up);
            yield return Throw(Vector2.up);
            yield return Scene();
            Check("the wheel rings it, and comes home", Story.Has("on_t2_gong1") && Thrown.Out("wheel") == 0);
            yield return new WaitForSeconds(0.5f);
            yield return Scene();
            Check("north lifts", !Shut("t2_northbars"));
            // the sun court
            yield return Stand("suncourt", 320, 184, Facing.Up);
            yield return Scene(0.6f);
            Check("the third fire is caged", Shut("t2_altarbars") && !Story.Has("on_t2_gong2"));
            yield return t.Shot("t19-the-sun-court", 0.2f);
            yield return Stand("suncourt", 344, 184, Facing.Up);
            yield return Throw(Vector2.up);
            Check("thrown straight, the wheel finds a wall and no gong", !Story.Has("on_t2_gong2"));
            yield return Stand("suncourt", 320, 184, Facing.Up);
            Thrown wheel = null;
            int banks = -1;
            p.ThrowWheel(new Vector2(1, 1));
            for (float w = 0; w < 7f; w += Time.deltaTime)
            {
                if (!wheel && Thrown.All.Count > 0) wheel = Thrown.All[0];
                if (wheel && banks < 0 && Story.Has("on_t2_gong2")) banks = wheel.Banks;
                if (w > 0.8f && Thrown.Out("wheel") == 0) break;
                yield return null;
            }
            yield return Scene();
            Check($"standing on the sun, thrown at the sunrise: off the east wall and into the gong (banks {banks})", Story.Has("on_t2_gong2") && banks == 1);
            yield return new WaitForSeconds(0.5f);
            yield return Scene();
            Check("the grille in front of the third fire lifts", !Shut("t2_altarbars"));
            yield return Light("lyre_2");
            Check("the third fire", Lit("lyre_2") && !Story.Has("door_t2_seal"));
            // back in the hall of the lyre
            yield return Stand("lyre", 340, 108, Facing.Up);
            yield return Flight(t, "lyre", Vector2.up, "on_t2_gong0");
            yield return new WaitForSeconds(0.5f);
            yield return Scene();
            Check($"the lyre hall's gong sings, and east lifts (gong {Story.Has("on_t2_gong0")}, bars shut {Shut("t2_eastbars")})", Story.Has("on_t2_gong0") && !Shut("t2_eastbars"));

            // ------------------------------------------------ the wardens
            yield return Stand("wardens", 60, 128, Facing.Right);
            yield return Scene(0.6f);
            Check("two wardens stand in the hall east of it", Count<Warden>() == 2);
            Check("east of them is barred", Shut("t2_brinkbars"));
            yield return t.Shot("t20-the-wardens", 0.2f);
            // one at a time: the far one is put down the quick way
            var wd = Nearest<Warden>();
            foreach (var e in Enemy.All.ToArray()) if (e is Warden && e != wd) Kill(e);
            // into his sight
            if (wd) { p.pos = wd.pos + new Vector2(-3.0f, 0); p.Face(Facing.Right); p.SetState(Player.State.Free, "idle"); }
            for (float w = 0; w < 3f && wd && wd.Standing; w += Time.deltaTime) yield return null;
            yield return new WaitForSeconds(0.9f);
            Check("a warden turns his shield to a visitor", wd && !wd.Standing);
            if (wd)
            {
                var front = Tomb.Dir(wd.facing);
                Check("with his shield up, what comes at the front of him is turned",
                    !wd.Takes(new HitInfo { damage = 1, from = wd.pos + front, kind = HitKind.Slash }) && !wd.Takes(new HitInfo { damage = 2, from = wd.pos + front, kind = HitKind.Thrown }));
                Check("and what comes from behind is not", wd.Takes(new HitInfo { damage = 2, from = wd.pos - front, kind = HitKind.Thrown }));
                int wh = wd.health.hp;
                p.pos = wd.pos + front * 1.1f; p.Face(Opposite(wd.facing)); p.SetState(Player.State.Free, "idle");
                yield return new WaitForSeconds(0.1f);
                yield return Press(Controls.Attack, 0.45f);
                Check("a blade at the front of him rings off the shield", wd && wd.health.hp == wh);
            }
            // past his shoulder and on; then a step into line with him, a hand held up, and it comes home through his back
            int throws = 0;
            var hall = Rooms.I.Find("wardens").rect;
            for (; throws < 8 && wd && !wd.health.Dead; throws++)
            {
                p.health.hp = p.health.max;
                // three steps south of him if there is floor there (north if not), a long stride to the side the hall is on
                bool south = wd.pos.y - hall.yMin > 4.4f;
                float side = wd.pos.x > hall.center.x ? -1.3f : 1.3f;
                p.pos = wd.pos + new Vector2(side, south ? -3.0f : 3.0f);
                p.Face(south ? Facing.Up : Facing.Down); p.SetState(Player.State.Free, "idle");
                yield return new WaitForSeconds(0.2f);
                int wh = wd.health.hp;
                if (throws == 0) yield return t.Shot("t21-past-his-shoulder", 0.05f);
                Items.Chosen = "wheel";
                p.ThrowWheel(south ? Vector2.up : Vector2.down);
                Thrown th = null;
                bool called = false;
                for (float w = 0; w < 5f; w += Time.deltaTime)
                {
                    if (!th && Thrown.All.Count > 0) th = Thrown.All[0];
                    if (th && wd && !called && !th.ComingHome)
                    {
                        bool past = th.Banks > 0 || (south ? th.pos.y > wd.pos.y + 1.2f : th.pos.y < wd.pos.y - 1.2f);
                        if (past && p.state == Player.State.Free)
                        {
                            if (Mathf.Abs(p.pos.x - wd.pos.x) > 0.15f) Controls.Fake = new Vector2(Mathf.Sign(wd.pos.x - p.pos.x), 0);
                            else { Controls.Fake = Vector2.zero; Controls.FakePress = Controls.Item; called = true; }
                        }
                    }
                    if (w > 0.8f && Thrown.Out("wheel") == 0) break;
                    p.health.hp = p.health.max;
                    yield return null;
                }
                Controls.Fake = Vector2.zero;
                yield return new WaitForSeconds(0.2f);
                t.Note($"     throw {throws + 1}: called home {called}, warden {(wd && !wd.health.Dead ? wd.health.hp.ToString() : "broken")} (was {wh})");
            }
            yield return new WaitForSeconds(0.6f);
            Check($"called home, the wheel comes back through him from behind until he breaks ({throws} throws)", !wd || wd.health.Dead);
            yield return Scene(0.5f);
            yield return new WaitForSeconds(0.6f);
            yield return Scene();
            Check("the hall is clear: the grille to the brink lifts", Story.Has(Mech.ClearFlag("tomb_2", "wardens")) && !Shut("t2_brinkbars"));
            // the queen
            yield return Stand("queen", 208, 150, Facing.Up);
            yield return Scene(0.4f);
            max0 = p.health.max;
            yield return Open("t2_vessel");
            Check("the queen's flame vessel", p.health.max == max0 + 2);

            // ------------------------------------------------ the brink
            yield return Stand("brink", 208, 300, Facing.Up);
            yield return Scene(0.6f);
            yield return t.Shot("t22-the-brink", 0.2f);
            int hpB = p.health.hp;
            yield return Walk(Vector2.up, 0.9f);
            Check($"the drop stops him (y {Local("brink").y:0})", Local("brink").y > 264 && p.health.hp == hpB && !Story.Has("on_t2_bridge"));
            yield return Stand("brink", 244, 270, Facing.Up);
            yield return Press(Controls.Attack, 0.5f);
            Check("the rope is a long way out for a blade", !Story.Has("on_t2_bridge"));
            yield return Stand("brink", 244, 280, Facing.Up);
            yield return Throw(Vector2.up);
            yield return Scene();
            Check("not for something thrown: the rope parts, and the bridge comes down", Story.Has("on_t2_bridge") && Story.Count("rope_cut") == 1);
            yield return t.Shot("t23-the-bridge-is-down", 0.2f);
            yield return Stand("brink", 208, 300, Facing.Up);
            yield return WalkUntil(Vector2.up, () => Local("brink").y < 170, 4f);
            Check($"he walks it (y {Local("brink").y:0})", Local("brink").y < 196 && p.state != Player.State.Dead);
            yield return Light("lyre_3");
            yield return Scene(1.0f);
            Check("the fourth fire: far off, the door with the sun on it lets go", Lit("lyre_3") && Story.Has("door_t2_seal"));

            // ------------------------------------------------ the door with the sun on it
            yield return Stand("lyre", 208, 90, Facing.Up);
            yield return t.Shot("t24-the-sun-door", 0.2f);
            yield return WalkUntil(Vector2.up, () => Game.I.CurrentMap != "tomb_2", 5f);
            yield return new WaitForSeconds(0.9f);
            yield return Scene(0.5f);
            Check($"through it, and on ({Game.I.CurrentMap})", Game.I.CurrentMap == Next && Game.I.CurrentSpawn == "south");
            if (Game.I.CurrentMap != Next) { Game.I.EnterMap(Next, "south"); Fade.Set(0); yield return new WaitForSeconds(0.5f); yield return Scene(0.5f); }

            // ================================================ 3F
            Check("he comes up onto the king's road", Rooms.I.current != null && Rooms.I.current.id == "stairhead" && Story.Count("tomb_seen_tomb_hi_stairhead") == 1);
            Check("three scarabs keep the stair head", Count<Scarab>() == 3);
            yield return t.Shot("t25-the-kings-road", 0.3f);
            // the wheel through a line of them
            KillAll();
            yield return new WaitForSeconds(0.4f);

            // ------------------------------------------------ the crossing: a vulture on its perch
            yield return Stand("crossing", 208, 200, Facing.Up);
            yield return Scene(0.6f);
            var vu = Nearest<Vulture>();
            Check("one of the king's vultures keeps the crossing, up on its perch", vu && vu.Perched && Count<Vulture>() == 1);
            yield return t.Shot("t26-a-vulture", 0.1f);
            if (vu)
            {
                int vh = vu.health.hp;
                p.pos = vu.pos + new Vector2(0, -0.9f); p.Face(Facing.Up); p.SetState(Player.State.Free, "idle");
                yield return new WaitForSeconds(0.1f);
                yield return Press(Controls.Attack, 0.45f);
                Check("up there a blade is only waved at it", vu && vu.health.hp == vh);
                // it marks him, and comes down: the mirror shield, square to it
                bool marked = false, stooped = false;
                Controls.FakeHold = Controls.Interact; Controls.FakePress = Controls.Interact;
                for (float w = 0; w < 14f && vu && !vu.Grounded; w += Time.deltaTime)
                {
                    if (p.state == Player.State.Free)
                    {
                        if (vu.Perched) { p.pos = vu.pos + new Vector2(0, -3.4f); p.Face(Facing.Up); }
                        Controls.FakePress = Controls.Interact;
                    }
                    if (!vu.Perched && !vu.Stooping) { }
                    marked |= vu.Perched && vu.anim.anim == "mark";
                    stooped |= vu.Stooping;
                    p.health.hp = p.health.max;
                    yield return null;
                }
                Controls.FakeHold = null;
                Check("it opens its wings at him first, and then it comes", marked && stooped);
                Check("a stoop that meets the mirror shield ends on the floor", vu && vu.Grounded);
                yield return t.Shot("t27-on-the-floor", 0.05f);
                if (vu)
                {
                    p.pos = vu.pos + new Vector2(0, -0.9f); p.Face(Facing.Up); p.SetState(Player.State.Free, "idle");
                    yield return new WaitForSeconds(0.1f);
                    yield return Press(Controls.Attack, 0.45f);
                    Check("and on the floor a blade finds it", !vu || vu.health.hp < vh);
                }
                for (float w = 0; w < 8f && vu && !vu.Perched; w += Time.deltaTime) { p.health.hp = p.health.max; yield return null; }
                if (vu) yield return WheelAt(vu, "crossing");
                yield return new WaitForSeconds(0.3f);
                Check("back on its perch, the Sun Wheel takes it off for good", !vu || vu.health.Dead);
            }

            // ------------------------------------------------ the king's door, with no key
            yield return Stand("threshold", 208, 160, Facing.Up);
            yield return Scene(0.6f);
            KillAll();
            yield return Open("t3_kingdoor", 0.85f);
            Check("the king's own door has no keyhole for a man without the Ghost Key", !Story.Has("door_t3_kingdoor"));
            yield return t.Shot("t28-the-kings-door", 0.2f);

            // ------------------------------------------------ east: the falconers' way and the mews
            yield return Stand("eastpass", 60, 128, Facing.Right);
            yield return Scene(0.5f);
            Check("a warden holds the falconers' way", Count<Warden>() == 1);
            KillAll();
            yield return new WaitForSeconds(0.4f);
            p.health.hp = p.health.max;
            yield return Stand("eastpass", 208, 84, Facing.Up);
            yield return WalkUntil(Vector2.up, () => Rooms.I.current != null && Rooms.I.current.id == "mews", 4f);
            for (float w = 0; w < 3f && (Rooms.Sliding || Game.Busy); w += Time.deltaTime) yield return null;
            yield return Scene(0.8f);
            yield return new WaitForSeconds(0.4f);
            Check("four of the king's vultures in the mews", Count<Vulture>() == 4);
            Check("the door shuts behind him, and the small key is caged", Shut("t3_mewsdoor") && Shut("t3_keycage"));
            yield return t.Shot("t29-the-mews", 0.2f);
            foreach (var e in Enemy.All.ToArray()) if (e is Scarab) Kill(e);
            int tries = 0;
            for (; tries < 16 && Count<Vulture>() > 0; tries++)
            {
                Vulture v = null;
                foreach (var e in Enemy.All) if (e is Vulture q && !q.health.Dead && q.Perched && (v == null || Vector2.Distance(q.pos, p.pos) < Vector2.Distance(v.pos, p.pos))) v = q;
                if (v == null) { p.health.hp = p.health.max; yield return new WaitForSeconds(0.4f); continue; }
                yield return WheelAt(v, "mews");
            }
            yield return new WaitForSeconds(0.6f);
            Check($"the wheel takes all four off their perches ({tries} throws)", Count<Vulture>() == 0);
            yield return Scene(0.5f);
            yield return new WaitForSeconds(0.6f);
            yield return Scene();
            Check("the mews is clear: the door lifts, and the cage", Story.Has(Mech.ClearFlag("tomb_hi", "mews")) && !Shut("t3_mewsdoor") && !Shut("t3_keycage"));
            keys0 = p.keys;
            p.health.hp = p.health.max;
            yield return Open("t3_key");
            Check("the small key", p.keys == keys0 + 1);

            // ------------------------------------------------ the roost
            yield return Stand("roost", 208, 70, Facing.Down);
            yield return Scene(0.6f);
            Check("the oldest of the birds has the roost", Count<Vulture>() == 1);
            yield return t.Shot("t30-the-roost", 0.2f);
            KillAll();
            Check("the flame vessel is caged", Shut("t3_vesselcage") && !Story.Has("on_t3_gong"));
            yield return Stand("roost", 208, 70, Facing.Down);
            yield return Flight(t, "roost", Vector2.down, "on_t3_gong");
            yield return new WaitForSeconds(0.5f);
            yield return Scene();
            Check($"the gong on its island sings to the wheel, and the cage lifts (gong {Story.Has("on_t3_gong")}, cage shut {Shut("t3_vesselcage")})", Story.Has("on_t3_gong") && !Shut("t3_vesselcage"));
            max0 = p.health.max;
            yield return Open("t3_vessel");
            Check("the roost's flame vessel", p.health.max == max0 + 2);

            // ------------------------------------------------ west: the clerks' passage and the steward's rest
            yield return Stand("westpass", 330, 150, Facing.Left);
            yield return Scene(0.5f);
            Check("two bearers keep the clerks' passage", Count<LampBearer>() == 2);
            p.health.hp = p.health.max;
            keys0 = p.keys;
            yield return Open("t3_lock", 0.85f);
            Check("the clerks' door takes the small key", Story.Has("door_t3_lock") && p.keys == keys0 - 1);
            p.health.hp = p.health.max;
            yield return WalkUntil(Vector2.up, () => Rooms.I.current != null && Rooms.I.current.id == "steward", 4f);
            for (float w = 0; w < 3f && (Rooms.Sliding || Game.Busy); w += Time.deltaTime) yield return null;
            yield return Scene(0.8f);
            Check("he is in the steward's rest, and two wardens are", Rooms.I.current != null && Rooms.I.current.id == "steward" && Count<Warden>() == 2);
            KillAll();
            yield return new WaitForSeconds(0.4f);
            p.health.hp = p.health.max;
            yield return t.Shot("t31-the-stewards-rest", 0.2f);
            yield return Stand("steward", 244, 282, Facing.Up);
            yield return Throw(Vector2.up);
            yield return Scene();
            Check("the wheel cuts the drawbridge's rope", Story.Has("on_t3_bridge"));
            yield return Stand("steward", 208, 300, Facing.Up);
            yield return WalkUntil(Vector2.up, () => Local("steward").y < 186, 4f);
            Check($"he crosses to the steward's side (y {Local("steward").y:0})", Local("steward").y < 198 && p.state != Player.State.Dead);
            Npc stw = null;
            foreach (var n in Npc.All) if (n && n.id == "steward") stw = n;
            Check("the steward is in", stw);
            if (stw)
            {
                p.pos = stw.pos + new Vector2(0, -0.9f); p.Face(Facing.Up); p.SetState(Player.State.Free, "idle");
                yield return new WaitForSeconds(0.2f);
                yield return Press(Controls.Interact);
                yield return Scene();
                Check("he explains about the key, and about his person", Story.Count("steward") == 1);
            }
            Check("his chest is behind a grille, and a counterweight holds it down", Shut("t3_ghostcage") && !Story.Has("on_t3_weight"));
            yield return t.Shot("t32-the-steward", 0.2f);
            yield return Stand("steward", 150, 140, Facing.Left);
            yield return Throw(Vector2.left);
            Check("thrown straight along the wall, the wheel finds rock and no rope", !Story.Has("on_t3_weight"));
            yield return Stand("steward", 96, 184, Facing.Up);
            wheel = null; banks = -1;
            p.ThrowWheel(new Vector2(-1, 1));
            for (float w = 0; w < 7f; w += Time.deltaTime)
            {
                if (!wheel && Thrown.All.Count > 0) wheel = Thrown.All[0];
                if (wheel && banks < 0 && Story.Has("on_t3_weight")) banks = wheel.Banks;
                if (w > 0.8f && Thrown.Out("wheel") == 0) break;
                yield return null;
            }
            yield return Scene();
            Check($"from the sun in the floor, off the west wall and round the corner: the rope parts (banks {banks})", Story.Has("on_t3_weight") && banks == 1 && Story.Count("weight_cut") == 1);
            yield return new WaitForSeconds(0.5f);
            yield return Scene();
            Check("with nothing holding it down, the grille goes up", !Shut("t3_ghostcage"));
            yield return t.Shot("t33-the-ghost-chest", 0.2f);
            yield return Open("t3_ghost");
            Check("the Ghost Key", Story.Has("ghostkey"));
            if (stw)
            {
                p.pos = stw.pos + new Vector2(0, -0.9f); p.Face(Facing.Up); p.SetState(Player.State.Free, "idle");
                yield return new WaitForSeconds(0.2f);
                yield return Press(Controls.Interact);
                yield return Scene();
                Check("the steward wants it signed for", Story.Count("steward_after") == 1);
            }
            // the dead of the house, and whoever carries it
            yield return Stand("westpass", 330, 150, Facing.Left);
            yield return Scene(0.5f);
            int hpK = p.health.hp = p.health.max;
            yield return new WaitForSeconds(3.0f);
            yield return Scene();
            Check("the bearers see the key, and find something to look at on the floor", Count<LampBearer>() == 2 && p.health.hp == hpK && Story.Count("bearer_aside") >= 1);
            yield return t.Shot("t34-management", 0.1f);

            // ------------------------------------------------ the king's door
            yield return Stand("threshold", 208, 160, Facing.Up);
            yield return Scene(0.4f);
            yield return Open("t3_kingdoor", 0.85f);
            Check("the ghost of a key goes into the ghost of a lock", Story.Has("door_t3_kingdoor"));
            yield return t.Shot("t35-open", 0.2f);
            Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn);
            var sd = Save.Read();
            Check("a saved journey keeps the Sun Wheel in his hand, the Ghost Key and the tomb's doors",
                sd != null && sd.item == "wheel" && System.Array.IndexOf(sd.flags, "item_wheel") >= 0 && System.Array.IndexOf(sd.flags, "door_t2_seal") >= 0 &&
                System.Array.IndexOf(sd.flags, "on_t2_bridge") >= 0 && System.Array.IndexOf(sd.flags, "dead_t2_roller") >= 0 &&
                System.Array.IndexOf(sd.flags, "ghostkey") >= 0 && System.Array.IndexOf(sd.flags, "door_t3_kingdoor") >= 0);
            yield return WalkUntil(Vector2.up, () => Game.I.CurrentMap != "tomb_hi", 5f);
            yield return new WaitForSeconds(0.9f);
            Check($"and up the last stair to the king ({Game.I.CurrentMap})", Game.I.CurrentMap == "tomb_3" && Game.I.CurrentSpawn == "south");
            Story.Abort();
            Save.ClearAll();
            t.Note(bad == 0 ? "TOMB OK" : $"TOMB: {bad} FAILED");
        }

        // ---------------------------------------------------------------------------- who keeps the tomb, for a contact sheet
        static IEnumerator Cast(AutoTest t)
        {
            DialogueBox.AutoAdvance = 0.1f;
            Kit("door_t1_door", "roller_seen", "dead_t2_roller", "item_wheel", "door_t2_seal", "on_t2_gong0", "bearer_passed", "bearer_lamp", "bearer_off", "roller_tumbled",
                Mech.ClearFlag("tomb_2", "roller"), Mech.ClearFlag("tomb_2", "wardens"), "dead_t2_w0", "dead_t2_w1");
            Game.I.EnterMap("tomb_2", "south");
            Fade.Set(0);
            var p = Player.I;
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.3f);
            yield return Scene(0.5f);
            yield return Stand("wardens", 208, 132, Facing.Down);
            KillAll();
            yield return new WaitForSeconds(0.4f);
            var c = p.pos;
            // four wardens round him: each turns its door to him, so the door shows all four of its faces
            var ws = new[] { Warden.Spawn(c + new Vector2(0, 2.9f)), Warden.Spawn(c + new Vector2(0, -2.5f)), Warden.Spawn(c + new Vector2(-4.2f, 0.4f)), Warden.Spawn(c + new Vector2(4.2f, 0.4f)) };
            for (float w = 0; w < 1.5f; w += Time.deltaTime) { p.health.hp = p.health.max; p.pos = c; yield return null; }
            foreach (var w in ws) if (w) w.StandThere(30f);
            yield return t.Shot("c1-wardens-standing", 0.3f);
            foreach (var w in ws) if (w) w.StandThere(0.01f);
            for (float w = 0; w < 0.9f; w += Time.deltaTime) { p.health.hp = p.health.max; yield return null; }
            yield return t.Shot("c2-wardens-coming", 0f);
            for (float w = 0; w < 1.1f; w += Time.deltaTime) { p.health.hp = p.health.max; yield return null; }
            yield return t.Shot("c3-wardens-shoving", 0f);
            Kill(ws[2]); Kill(ws[3]);
            yield return t.Shot("c4-doors-down", 0.5f);
            KillAll();
            yield return new WaitForSeconds(0.3f);
            // vultures, with nothing under them: sitting, marking, stooping, climbing
            p.pos = c; p.SetState(Player.State.Free, "idle");
            var vs = new[] { Vulture.Spawn(c + new Vector2(0, 3.2f)), Vulture.Spawn(c + new Vector2(-4.6f, 1.0f)), Vulture.Spawn(c + new Vector2(4.6f, 1.0f)), Vulture.Spawn(c + new Vector2(-2.4f, -2.6f)), Vulture.Spawn(c + new Vector2(2.4f, -2.6f)) };
            yield return t.Shot("c5-vultures-sitting", 0.5f);
            for (int i = 0; i < 4; i++)
            {
                for (float w = 0; w < 0.62f; w += Time.deltaTime) { p.health.hp = p.health.max; if (p.state == Player.State.Free) p.pos = c; yield return null; }
                yield return t.Shot($"c{6 + i}-vultures", 0f);
            }
            Controls.FakeHold = Controls.Interact; Controls.FakePress = Controls.Interact;
            for (float w = 0; w < 3.0f; w += Time.deltaTime) { p.health.hp = p.health.max; if (p.state == Player.State.Free) Controls.FakePress = Controls.Interact; yield return null; }
            Controls.FakeHold = null;
            yield return t.Shot("d0-vultures-and-the-shield", 0f);
            KillAll();
            yield return new WaitForSeconds(0.4f);
            // the Sun Roller: waiting, going, and on its back
            p.pos = c + new Vector2(0, -2.5f); p.SetState(Player.State.Free, "idle");
            var roller = SunRoller.Spawn(c + new Vector2(0, 1.5f));
            yield return t.Shot("d1-roller-waiting", 0.4f);
            roller.Begin();
            for (float w = 0; w < 1.0f; w += Time.deltaTime) { p.health.hp = p.health.max; yield return null; }
            yield return t.Shot("d2-roller-sparks", 0f);
            for (float w = 0; w < 12f && roller && !roller.Tumbled; w += Time.deltaTime) { p.health.hp = p.health.max; yield return null; }
            yield return t.Shot("d3-roller-on-its-back", 0.5f);
            Kill(roller);
            yield return new WaitForSeconds(1.5f);
            yield return Scene(0.5f);
            foreach (var pk in Object.FindObjectsByType<Pickup>(FindObjectsSortMode.None)) Object.Destroy(pk.gameObject);
            // two bearers
            p.pos = c; p.SetState(Player.State.Free, "idle");
            LampBearer.Spawn(c + new Vector2(-2.2f, 1.2f)); LampBearer.Spawn(c + new Vector2(2.4f, -0.6f));
            yield return t.Shot("d4-bearers", 0.9f);
            Save.ClearAll();
        }

        // ---------------------------------------------------------------------------- the wheel by itself
        /// <summary>One throw, written down: where it banked, what it rang.</summary>
        static IEnumerator Flight(AutoTest t, string room, Vector2 dir, string flag)
        {
            var p = Player.I;
            var r = Rooms.I.Find(room).rect;
            t.Note($"  from {Local(room).x:0},{Local(room).y:0} state {p.state} out {Thrown.Out("wheel")} flag {Story.Has(flag)}");
            p.ThrowWheel(dir);
            Thrown wh = null;
            int banks = -1; bool home = false, rang = Story.Has(flag);
            for (float w = 0; w < 6f; w += Time.deltaTime)
            {
                if (!wh && Thrown.All.Count > 0) { wh = Thrown.All[0]; t.Note($"  {w:0.00} launched at {(wh.pos.x - r.xMin) * 16f:0},{(r.yMax - wh.pos.y) * 16f:0}"); }
                if (wh)
                {
                    if (wh.Banks != banks) { banks = wh.Banks; if (banks > 0) t.Note($"  {w:0.00} bank {banks} at {(wh.pos.x - r.xMin) * 16f:0},{(r.yMax - wh.pos.y) * 16f:0}"); }
                    if (wh.ComingHome && !home) { home = true; t.Note($"  {w:0.00} home from {(wh.pos.x - r.xMin) * 16f:0},{(r.yMax - wh.pos.y) * 16f:0}"); }
                }
                if (!rang && Story.Has(flag)) { rang = true; t.Note($"  {w:0.00} {flag} set" + (wh ? $" (wheel at {(wh.pos.x - r.xMin) * 16f:0},{(r.yMax - wh.pos.y) * 16f:0})" : "")); }
                if (w > 0.8f && Thrown.Out("wheel") == 0) break;
                yield return null;
            }
            t.Note($"  done: {flag} {Story.Has(flag)}, launched {wh != null || banks >= 0}");
            yield return Scene();
        }

        static IEnumerator Wheel(AutoTest t)
        {
            DialogueBox.AutoAdvance = 0.1f;
            Kit("door_t1_door", "roller_seen", "dead_t2_roller", "item_wheel", "door_t2_seal", Mech.ClearFlag("tomb_2", "roller"));
            Game.I.EnterMap("tomb_2", "south");
            Fade.Set(0);
            var p = Player.I;
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.3f);
            yield return Scene(0.5f);
            Items.Chosen = "wheel";
            Story.I.ApplyItems();
            t.Note("the lyre hall's gong, thrown up from under it");
            yield return Stand("lyre", 340, 108, Facing.Up);
            KillAll();
            yield return Flight(t, "lyre", Vector2.up, "on_t2_gong0");
            yield return new WaitForSeconds(0.6f);
            yield return Scene();
            t.Note($"  east bars shut: {Shut("t2_eastbars")}");
            Game.I.EnterMap("tomb_hi", "south");
            Fade.Set(0);
            p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.3f);
            yield return Scene(0.5f);
            t.Note("the roost's gong, thrown down at it");
            yield return Stand("roost", 208, 70, Facing.Down);
            KillAll();
            yield return Stand("roost", 208, 70, Facing.Down);
            yield return Flight(t, "roost", Vector2.down, "on_t3_gong");
            yield return new WaitForSeconds(0.6f);
            yield return Scene();
            t.Note($"  vessel cage shut: {Shut("t3_vesselcage")}");
            t.Note("and thrown up at it from the south side");
            yield return Stand("roost", 208, 198, Facing.Up);
            Story.Clear("on_t3_gong");
            yield return Flight(t, "roost", Vector2.up, "on_t3_gong");
            Save.ClearAll();
        }

        /// <summary>Three steps off a perched vulture, on whichever side of it has the floor, and the wheel at it.</summary>
        static IEnumerator WheelAt(Vulture v, string room)
        {
            var p = Player.I;
            var r = Rooms.I.Find(room).rect;
            bool south = v.pos.y - r.yMin > 4.3f;
            p.health.hp = p.health.max;
            p.pos = v.pos + new Vector2(0, south ? -3.0f : 3.0f);
            p.Face(south ? Facing.Up : Facing.Down); p.SetState(Player.State.Free, "idle");
            yield return new WaitForSeconds(0.1f);
            yield return Throw(south ? Vector2.up : Vector2.down, 4f);
        }

        /// <summary>Where the door with the sun on it leads.</summary>
        const string Next = "tomb_hi";

        static Facing Opposite(Facing f) => f == Facing.Down ? Facing.Up : f == Facing.Up ? Facing.Down : f == Facing.Left ? Facing.Right : Facing.Left;

        // ---------------------------------------------------------------------------- the Sun Roller, played
        static IEnumerator Roller(AutoTest t)
        {
            DialogueBox.AutoAdvance = 0.1f;
            int wins = 0;
            for (int round = 0; round < 4; round++)
            {
                Kit("door_t1_door", "roller_seen");
                Random.InitState(5200 + round * 91);
                Game.I.EnterMap("tomb_2", "south");
                Fade.Set(0);
                var p = Player.I;
                p.SetState(Player.State.Free, "idle");
                yield return new WaitForSeconds(0.3f);
                yield return Stand("westpass", 60, 128, Facing.Left);
                KillAll();
                yield return WalkUntil(Vector2.left, () => Rooms.I.current != null && Rooms.I.current.id == "roller", 4f);
                for (float w = 0; w < 3f && (Rooms.Sliding || Game.Busy); w += Time.deltaTime) yield return null;
                yield return Scene(0.5f);
                var roller = SunRoller.Current;
                if (!roller) { t.Note("FAIL no Sun Roller in its hall"); yield break; }
                var room = Rooms.I.Find("roller").rect;
                float time = 0, swingCd = 0;
                int hp0 = p.health.hp, swings = 0, tumbles = 0;
                bool was = false;
                while (roller && !roller.health.Dead && p.state != Player.State.Dead && time < 180f)
                {
                    float dt = Time.deltaTime;
                    time += dt; swingCd -= dt;
                    if (roller.Tumbled && !was) tumbles++;
                    was = roller.Tumbled;
                    Vector2 go = Vector2.zero;
                    if (p.state == Player.State.Free)
                    {
                        if (roller.Tumbled)
                        {
                            // in under it, from the south, and the blade
                            var at = roller.pos + new Vector2(0, -0.95f);
                            var d = at - p.pos;
                            if (d.magnitude > 0.25f) go = d.normalized;
                            else
                            {
                                p.Face(Facing.Up);
                                if (swingCd <= 0) { Controls.FakePress = Controls.Attack; swingCd = 0.34f; swings++; }
                            }
                        }
                        else
                        {
                            // keep off the line the sun is on (or is about to be on): the sparks say which way
                            Vector2 b = roller.BallPos, dir = roller.BallDir.sqrMagnitude > 0.01f ? roller.BallDir.normalized : Vector2.down;
                            var rel = p.pos - b;
                            float along = Vector2.Dot(rel, dir);
                            var perp = rel - dir * along;
                            if (roller.Rolling && along > -1.5f && perp.magnitude < 2.4f)
                                go = perp.sqrMagnitude > 0.01f ? perp.normalized : new Vector2(-dir.y, dir.x);
                            else
                            {
                                // otherwise wait in the open middle of the hall, off its walls
                                var wait = new Vector2(room.center.x, room.center.y - 1.0f);
                                if (Vector2.Distance(p.pos, b) < 3.2f) go = (p.pos - b).normalized;
                                else if (Vector2.Distance(p.pos, wait) > 1.5f) go = (wait - p.pos).normalized;
                            }
                            // not into the corners, and not into the drop under the gong
                            var next = p.pos + go * 0.8f;
                            if (next.x < room.xMin + 1.6f || next.x > room.xMax - 1.6f) go.x = 0;
                            if (next.y < room.yMin + 1.2f || next.y > room.yMax - 4.2f) go.y = 0;
                        }
                    }
                    Controls.Fake = go;
                    yield return null;
                }
                Controls.Fake = Vector2.zero;
                bool won = !roller || roller.health.Dead;
                if (won) wins++;
                t.Note($"round {round + 1}: {(won ? "the Sun Roller is down" : p.state == Player.State.Dead ? "Azar fell" : "time ran out")} in {time:0}s; " +
                       $"{tumbles} tumbles, {swings} swings, Azar lost {hp0 - p.health.hp} of {hp0}" + (roller ? $", roller {roller.health.hp}/{roller.health.max}" : ""));
                if (round == 0) yield return t.Shot("r1-after", 0.3f);
                yield return new WaitForSeconds(1.5f);
                yield return Scene(0.5f);
            }
            Save.ClearAll();
            t.Note($"ROLLER: the bot won {wins} of 4");
        }
    }
}
