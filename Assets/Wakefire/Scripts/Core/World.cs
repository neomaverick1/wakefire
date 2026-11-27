// Moving through Ashkel: walking off the edge of one place into the next (with a dithered
// fade), saving on arrival, falling and getting back up, and the things every map shares:
// chests, locked doors, blocks to shove and the plates they press.
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public partial class Game
    {
        public string CurrentMap, CurrentSpawn;
        public static bool Busy;
        bool exitArmed;

        public void Go(string map, string spawn)
        {
            if (Busy) return;
            StartCoroutine(GoRoutine(map, spawn));
        }

        /// <summary>The insides of a town's houses are a map of their own: rooms, not a place with a name.</summary>
        public static bool Houses(string map) => !string.IsNullOrEmpty(map) && map.EndsWith("_in");

        /// <summary>The place a map belongs to on the world map: itself, or for the rooms of a town's houses, the town.</summary>
        public static string Outer(string map) => Houses(map) ? map.Substring(0, map.Length - 3) : map;

        IEnumerator GoRoutine(string map, string spawn)
        {
            Busy = true;
            var p = Player.I;
            if (p) p.SetState(Player.State.Cutscene);
            yield return Fade.Out(0.22f);
            bool newPlace = map != CurrentMap;
            string was = CurrentMap;
            // (going indoors: where the door was, for the world map)
            if (p && Houses(map) && !Houses(was)) { Story.SetCount("outer_x", Mathf.RoundToInt(p.pos.x * 16f)); Story.SetCount("outer_y", Mathf.RoundToInt(-p.pos.y * 16f)); }
            EnterMap(map, spawn);
            Save.Write(map, spawn);
            // into a house, or from one room of it to another: the room says what it is; out of one, the town does not need to
            if (Houses(map)) { if (Rooms.I && Rooms.I.current != null && !string.IsNullOrEmpty(Rooms.I.current.name)) Notices.Room(Rooms.I.current.name); }
            else if (newPlace && !Houses(was)) Notices.Place(map);
            yield return null;
            yield return Fade.In(0.22f);
            if (p) p.SetState(Player.State.Free, "idle");
            Busy = false;
        }

        float darkFor;

        void Update()
        {
            TouchControls.Poll();
            if (Paused) return;
            Save.PlayTime += Time.unscaledDeltaTime;
            var p = Player.I;
            var m = Map.Current;
            Vector2 was = seenAt;
            if (p) seenAt = p.pos;
            if (!p || !m || Busy) return;
            if (p.state == Player.State.Dead) { StartCoroutine(Respawn()); return; }
            if (p.state != Player.State.Free) return;
            // nothing may leave him walking about in the dark: if the screen is still black with nobody holding it so
            // (no scene playing, no title up, no way through a door), the game lifts it itself
            if (Fade.Amount > 0.98f && Title.I == null && !(Story.I && Story.I.Running))
            {
                darkFor += Time.unscaledDeltaTime;
                if (darkFor > 1.2f) { darkFor = 0; Debug.LogWarning("[game] the screen was left dark; lifting it"); StartCoroutine(Fade.In(0.4f)); }
            }
            else darkFor = 0;
            bool inside = false;
            foreach (var mk in m.data.markers)
            {
                // a way out to another place; or a way that comes out somewhere else in this one (a burrow, a ladder)
                bool warp = mk.kind == "warp";
                if (mk.kind != "exit" && !warp) continue;
                var a = Map.ToWorld(mk.x, mk.y + mk.h);
                var r = new Rect(a.x, a.y, mk.w / 16f, mk.h / 16f);
                if (!r.Contains(p.pos) && !Swept(r, was, p.pos)) continue;
                inside = true;
                if (!exitArmed) continue;
                if (!string.IsNullOrEmpty(mk.who) && !Story.Has(mk.who)) continue;
                if (warp) StartCoroutine(WarpRoutine(mk));
                else Go(mk.id, mk.text);
                return;
            }
            if (!inside) exitArmed = true;
        }

        Vector2 seenAt;

        /// <summary>Did he pass through this on his way from there to here? (One frame's walk: anything longer was
        /// not a walk, and counts for nothing.)</summary>
        static bool Swept(Rect r, Vector2 a, Vector2 b)
        {
            float d = Vector2.Distance(a, b);
            if (d < 0.02f || d > 1.2f) return false;
            int n = Mathf.CeilToInt(d / 0.08f);
            for (int i = 1; i < n; i++) if (r.Contains(Vector2.Lerp(a, b, i / (float)n))) return true;
            return false;
        }

        /// <summary>Through a burrow or up a ladder: in at one end, and out at the other end of it on the same floor.</summary>
        IEnumerator WarpRoutine(MarkerJson mk)
        {
            Busy = true;
            var p = Player.I;
            bool ladder = mk.id == "ladder";
            p.SetState(Player.State.Cutscene, ladder ? "idle" : "roll");
            Sfx.Play(ladder ? "step_wood0" : "roll", 0.7f, 0.05f);
            yield return Fade.Out(0.2f);
            var sp = Map.Current.Marker("spawn", mk.text);
            if (sp != null)
            {
                var at = Map.ToWorld(sp.x, sp.y);
                p.pos = at;
                p.transform.position = new Vector3(at.x, at.y, 0);
                p.Face(Facing.Down);
                if (Rooms.I) Rooms.I.Jump(at);
                View.SnapTo(at);
            }
            exitArmed = false;
            if (ladder) Sfx.Play("step_wood1", 0.7f, 0.05f);
            yield return null;
            yield return Fade.In(0.22f);
            p.SetState(Player.State.Free, "idle");
            Busy = false;
            if (!ladder && Story.I) Story.I.Burrowed();
        }

        /// <summary>He has gone down a hole that has a floor under it: he comes down on that floor, on another
        /// map or in another room of this one.</summary>
        public void Drop(string map, string spawn)
        {
            if (!Busy) StartCoroutine(DropRoutine(map, spawn));
        }

        IEnumerator DropRoutine(string map, string spawn)
        {
            Busy = true;
            var p = Player.I;
            yield return Fade.Out(0.22f);
            if (map == CurrentMap)
            {
                var sp = Map.Current.Marker("spawn", spawn) ?? Map.Current.Marker("spawn");
                var at = Map.ToWorld(sp.x, sp.y);
                p.pos = at;
                p.transform.position = new Vector3(at.x, at.y, 0);
                if (Rooms.I) Rooms.I.Jump(at);
                View.SnapTo(at);
                exitArmed = false;
            }
            else
            {
                EnterMap(map, spawn);
                Save.Write(map, spawn);
                Notices.Place(map);
            }
            p.SetState(Player.State.Cutscene, "hurt");
            yield return null;
            var fade = StartCoroutine(Fade.In(0.25f));
            yield return p.Land();
            yield return fade;
            Busy = false;
            if (Story.I) Story.I.CameDown();
        }

        IEnumerator Respawn()
        {
            Busy = true;
            yield return new WaitForSeconds(1.6f);
            yield return Fade.Out(0.6f);
            // where to pick up: here, at the player's own save, or the title
            yield return Fallen.Ask(CurrentMap);
            var p = Player.I;
            p.health.hp = p.health.max;
            p.health.invulnerable = 1.5f;
            if (Dream.I.Dreaming) Dream.I.SetInstant(false);
            if (Fallen.Choice == Fallen.ToTitle)
            {
                // he fell, so the game's own save still stands at the way into this place
                p.SetState(Player.State.Free, "idle");
                Busy = false;
                Title.Show();
                Fade.Set(0);
                yield break;
            }
            var saved = Fallen.Choice == Fallen.LoadSave ? Save.Read(Fallen.Slot) : null;
            if (saved != null) { Save.Use(Fallen.Slot); Begin(saved); }
            else
            {
                EnterMap(CurrentMap, CurrentSpawn);
                p.SetState(Player.State.Free, "idle");
            }
            yield return Fade.In(0.5f);
            Busy = false;
        }

        /// <summary>Go back to what one of the three journeys last saved, from the pause screen. That
        /// journey becomes the one in play.</summary>
        public void LoadGame(int slot)
        {
            var d = Save.Read(slot);
            if (d == null || Busy) return;
            StartCoroutine(LoadRoutine(slot, d));
        }

        IEnumerator LoadRoutine(int slot, SaveData d)
        {
            Busy = true;
            var p = Player.I;
            if (p) p.SetState(Player.State.Cutscene);
            yield return Fade.Out(0.35f);
            Save.Use(slot);
            Begin(d);
            yield return null;
            yield return Fade.In(0.4f);
            Busy = false;
        }

        /// <summary>Puts down the enemy a map marker stands for.</summary>
        public static Enemy SpawnEnemy(MarkerJson mk)
        {
            if ((mk.who == "unremembered" || mk.who == "bearer") && Story.Has("chapter2_done")) return null;      // they are asleep now, like everyone else up there
            if (Story.FirstNight && Game.I.CurrentMap != "crypt") return null;             // the first night: nothing has come down out of the hills yet
            var at = Map.ToWorld(mk.x, mk.y);
            Enemy e = mk.who switch
            {
                "crab" => Crab.Spawn(at),
                "jackal" => Jackal.Spawn(at),
                "den_mother" => DenMother.Spawn(at),
                "herdsman" => Herdsman.Spawn(at),
                "moth" => Moth.Spawn(at),
                "sentinel" => Sentinel.Spawn(at),
                "unremembered" => Shade.Spawn(at),
                "ushabti" => Ushabti.Spawn(at),
                "scarab" => Scarab.Spawn(at),
                "clay_red" => Spearman.Spawn(at),
                "clay_blue" => Slinger.Spawn(at),
                "last_piece" => LastPiece.Spawn(at),
                "bearer" => LampBearer.Spawn(at),
                "warden" => Warden.Spawn(at),
                "sun_roller" => SunRoller.Spawn(at),
                "vulture" => Vulture.Spawn(at),
                "medusa" => Medusa.Spawn(at),
                "thurifer" => Thurifer.Spawn(at),
                "glass" => BurningGlass.Spawn(at),
                "snuffer" => Snuffer.Spawn(at),
                "wick" => Wick.Spawn(at),
                "dragnet" => Dragnet.Spawn(at),
                "stayup" => StayUp.Spawn(at),
                "yawn" => Yawn.Spawn(at),
                "watch" => SleepWatch.Spawn(at),
                "debt" => Debt.Spawn(at),
                _ => null,
            };
            if (!e) return null;
            e.markerId = mk.id;
            if (!string.IsNullOrEmpty(mk.text) && mk.text.StartsWith("once")) e.spawnId = mk.id;
            if (e is SleepWatch sw) sw.SetBeat(mk.text);
            // "hold:FLAG": a clay soldier that stands like the statue it is until the story has that flag
            if (e is ClaySoldier cs && !string.IsNullOrEmpty(mk.text) && mk.text.Contains("hold:"))
                cs.holdFlag = mk.text.Substring(mk.text.IndexOf("hold:") + 5).Split(' ')[0];
            return e;
        }

        /// <summary>After a map loads: enemies from its markers, and the state of shared things.</summary>
        void Populate(Map m)
        {
            // a floor of rooms fills each room as Azar walks into it (World/Rooms.cs)
            if (!Rooms.I)
                foreach (var mk in m.data.markers)
                {
                    if (mk.kind != "enemy") continue;
                    if (!string.IsNullOrEmpty(mk.id) && Story.Has("dead_" + mk.id)) continue;
                    SpawnEnemy(mk);
                }
            var cut = new List<Prop>();
            foreach (var pr in m.props)
            {
                if (!pr) continue;
                switch (pr.Kind)
                {
                    case "chest":
                        if (Story.Has("chest_" + pr.data.id)) pr.SetSprite(pr.data.s + "_open", pr.data.px, pr.data.py);
                        break;
                    case "bigchest":
                        if (Story.Has("chest_" + pr.data.id)) pr.SetSprite("bigchest_open", pr.data.px, pr.data.py);
                        break;
                    case "roots":
                        if (Story.Has("cut_" + pr.data.id)) cut.Add(pr);
                        break;
                    case "lockdoor":
                    case "bigdoor":
                        if (Story.Has("door_" + pr.data.id)) pr.Open();
                        break;
                }
            }
            foreach (var pr in cut) { m.props.Remove(pr); pr.Clear(); }
        }

        /// <summary>Chests, doors and other things every map shares. Returns true if handled.</summary>
        public static bool CommonProp(Prop p)
        {
            var pl = Player.I;
            switch (p.Kind)
            {
                case "chest":
                    if (Story.Has("chest_" + p.data.id)) { Story.Run(Story.Narrate("Empty. You already have what was in it.")); return true; }
                    Story.Run(OpenChest(p));
                    return true;
                case "bigchest":
                    if (Story.Has("chest_" + p.data.id)) { Story.Run(Story.Narrate("Empty. What was in it is yours now.")); return true; }
                    Story.Run(OpenBigChest(p));
                    return true;
                case "roots":
                    Story.Run(Story.Narrate(pl.hasSword ? "Olive roots, as thick as your arm, grown right across the way.^This is what the blade is for."
                                                        : string.IsNullOrEmpty(p.data.text) ? "Roots, grown right across the way." : p.data.text));
                    return true;
                case "lockdoor":
                    if (pl.keys <= 0) { Story.Run(Story.Narrate("Locked. A small bronze keyhole, green with age.")); return true; }
                    pl.keys--;
                    Story.Set("door_" + p.data.id);
                    p.Open();
                    Sfx.Play("unlock");
                    return true;
                case "dreamthing":
                case "dreamlock":
                case "plankgap":
                case "bluelamp":
                case "scale":
                    return Pocket.Look(p);
                case "standard":
                    Story.Run(Story.I.LowerStandard(p));
                    return true;
                case "bigdoor":
                {
                    // every great door has a key that was made for it and for nothing else
                    bool tomb = Game.I.CurrentMap.StartsWith("tomb");
                    if (!Story.Has(tomb ? "ghostkey" : "bigkey"))
                    {
                        Story.Run(Story.Narrate(tomb
                            ? "The king's own door. Where the keyhole ought to be there is only the place where one was.^Whatever key fits this has been dead as long as he has."
                            : "A great door with a lock shaped like a bull's head.^It wants a bigger key than yours."));
                        return true;
                    }
                    Story.Set("door_" + p.data.id);
                    foreach (var pr in Map.Current.props.ToArray())
                        if (pr && pr.Kind == "bigdoor" && pr.data.id == p.data.id) pr.Open();
                    Sfx.Play("gate_open");
                    PixelView.I.Shake(2, 0.5f);
                    if (tomb)
                    {
                        Sfx.Play("ghost_door", 1f, 0f);
                        Story.Run(Story.Narrate("The ghost of a key goes into the ghost of a lock.^Something turns that has not turned in four hundred years.| It is not the door. The door just opens."));
                    }
                    return true;
                }
            }
            return false;
        }

        /// <summary>A great chest: he sets his shoulder to the lid, it goes back on its hinges with a groan,
        /// and whatever is inside lights the room before he has it in his hands.</summary>
        static IEnumerator OpenBigChest(Prop p)
        {
            var pl = Player.I;
            pl.Face(Facing.Up);
            if (pl.anim.model) { pl.SetState(Player.State.ItemGet, "open"); yield return Story.Wait(0.7f); }
            Sfx.Play("bigchest_open", 1f, 0f);
            PixelView.I.Shake(1, 0.3f);
            yield return Story.Wait(0.9f);
            PixelView.I.Shake(2, 0.22f);
            p.SetSprite("bigchest_open", p.data.px, p.data.py);
            Story.Set("chest_" + p.data.id);
            var glow = LightBlob.Create(p.transform, p.basePos + new Vector2(0, 0.6f), 0.5f, new Color(1f, 0.84f, 0.46f), 0.95f, true);
            glow.height = 0.8f;
            for (float t = 0; t < 1.1f; t += Time.deltaTime)
            {
                glow.radius = Mathf.Lerp(0.5f, 5.5f, t / 1.1f);
                if (Random.value < 0.6f) Fx.Sparks(p.basePos + new Vector2(Random.Range(-0.5f, 0.5f), 0.9f), new Color(1f, 0.9f, 0.55f), 1);
                yield return null;
            }
            yield return Story.Wait(0.3f);
            yield return Story.GiveItem(p.data.text ?? "shield");
            glow.radius = 3.2f; glow.intensity = 0.45f;
        }

        static IEnumerator OpenChest(Prop p)
        {
            var pl = Player.I;
            // he bends to it and throws the lid back
            if (pl.anim.model) { pl.SetState(Player.State.ItemGet, "open"); yield return Story.Wait(0.55f); }
            Sfx.Play("chest_open");
            p.SetSprite(p.data.s + "_open", p.data.px, p.data.py);
            Story.Set("chest_" + p.data.id);
            yield return Story.Wait(pl.anim.model ? 0.6f : 0.35f);
            string what = p.data.text ?? "shekels:10";
            if (what.StartsWith("shekels:"))
            {
                int n = int.Parse(what.Substring(8));
                pl.coins += n;
                yield return Story.ItemGet("gold_bar", $"{n} shekels!^Somebody in Ashkel saved up, and then fell asleep.");
            }
            else if (what == "key")
            {
                pl.keys++;
                yield return Story.ItemGet("small_key", "A small bronze key.^It will open one door in this place, and then it's done.");
            }
            else yield return Story.GiveItem(what);
        }
    }

    public partial class Prop
    {
        /// <summary>Doors swing away: the sprite goes, and so does the wall it made.</summary>
        public void Open()
        {
            if (solid != null) { Solids.Remove(solid); solid = null; }
            sr.enabled = false;
            data.kind = "open";
            Fx.Dust(basePos, 6);
        }
    }
}
