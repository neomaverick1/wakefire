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

        IEnumerator GoRoutine(string map, string spawn)
        {
            Busy = true;
            var p = Player.I;
            if (p) p.SetState(Player.State.Cutscene);
            yield return Fade.Out(0.22f);
            bool newPlace = map != CurrentMap;
            EnterMap(map, spawn);
            Save.Write(map, spawn);
            if (newPlace) Notices.Place(map);
            yield return null;
            yield return Fade.In(0.22f);
            if (p) p.SetState(Player.State.Free, "idle");
            Busy = false;
        }

        void Update()
        {
            TouchControls.Poll();
            if (Paused) return;
            Save.PlayTime += Time.unscaledDeltaTime;
            var p = Player.I;
            var m = Map.Current;
            if (!p || !m || Busy) return;
            if (p.state == Player.State.Dead) { StartCoroutine(Respawn()); return; }
            if (p.state != Player.State.Free) return;
            bool inside = false;
            foreach (var mk in m.data.markers)
            {
                if (mk.kind != "exit") continue;
                var a = Map.ToWorld(mk.x, mk.y + mk.h);
                var r = new Rect(a.x, a.y, mk.w / 16f, mk.h / 16f);
                if (!r.Contains(p.pos)) continue;
                inside = true;
                if (!exitArmed) continue;
                if (!string.IsNullOrEmpty(mk.who) && !Story.Has(mk.who)) continue;
                Go(mk.id, mk.text);
                return;
            }
            if (!inside) exitArmed = true;
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
            if (mk.who == "unremembered" && Story.Has("chapter2_done")) return null;      // they are asleep now, like everyone else up there
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
                _ => null,
            };
            if (!e) return null;
            e.markerId = mk.id;
            if (!string.IsNullOrEmpty(mk.text) && mk.text.StartsWith("once")) e.spawnId = mk.id;
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
                        if (Story.Has("chest_" + pr.data.id)) pr.SetSprite("chest_open", pr.data.px, pr.data.py);
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
                case "bigdoor":
                    if (!Story.Has("bigkey")) { Story.Run(Story.Narrate("A great door with a lock shaped like a bull's head.^It wants a bigger key than yours.")); return true; }
                    Story.Set("door_" + p.data.id);
                    p.Open();
                    Sfx.Play("gate_open");
                    PixelView.I.Shake(2, 0.5f);
                    return true;
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
            p.SetSprite("chest_open", p.data.px, p.data.py);
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
