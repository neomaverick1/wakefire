// Story state and the script runner: flags, counters, and coroutine scenes that hold Azar
// still while people talk, items are handed over, and gates groan open.
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public partial class Story : MonoBehaviour
    {
        public static Story I;
        public static readonly HashSet<string> Flags = new HashSet<string>();
        static readonly Dictionary<string, int> counts = new Dictionary<string, int>();
        public static IEnumerable<KeyValuePair<string, int>> Counts => counts;
        public static void SetCount(string k, int v) => counts[k] = v;
        public static void ResetAll() { Flags.Clear(); counts.Clear(); }

        public bool Running { get; private set; }
        public Npc Speaker { get; private set; }
        System.Action<Prop> propHandler;

        /// <summary>Called whenever a map has loaded: people, and what touching things does.</summary>
        public void Setup(string map, Map m)
        {
            var p = Player.I;
            p.Interacted -= OnPropAny;
            p.Interacted += OnPropAny;
            p.Fell -= OnFell;
            p.Fell += OnFell;
            propHandler = null;
            if (map == "terraces" && FirstNight && Has("item_wakefire")) RunWhenFree(EndOfNight());
            switch (map)
            {
                case "ashkel": SetupAshkel(m); break;
                case "crypt": SetupRegion(map, m); SetupCrypt(m); break;
                case "zig_2": case "zig_hi": SetupRegion(map, m); SetupZig(m); break;
                case "barrow": SetupRegion(map, m); SetupBarrow(m); break;
                case "necro_road": case "necropolis": case "tomb_3": SetupHill(map, m); break;
                case "tomb_1": case "tomb_2": case "tomb_hi": SetupHill(map, m); SetupTomb(map, m); break;
                default: SetupRegion(map, m); break;
            }
        }

        partial void SetupRegion(string map, Map m);

        void OnFell()
        {
            if (Game.I.CurrentMap == "temple_yard" && !Has("item_oil") && Bump("yard_falls") == 0)
                Run(Narrate("Too far for one nap. The dream gave out halfway and the chasm took you.^Somebody in town must know how to dream for longer."));
            else if (Game.I.CurrentMap == "cliffs" && Bump("sea_falls") == 0)
                Run(Narrate("Cold, salty and awake. The road of moonlight is only there while you dream.^Nod off right at the end of the pier, and run."));
            else if (Game.I.CurrentMap == "necropolis" && Bump("hill_falls") == 0)
                Run(Narrate("The split in the hill goes down further than the hill does.^There is a road of moonlight across it. For dreamers."));
            else if (Game.I.CurrentMap.StartsWith("tomb") && Bump("tomb_falls") == 0)
                Run(Narrate("The dead filled every drop in this tomb with dark, so that nobody living should cross one.^It works. You are back where you started, colder.| The Sun Wheel does not mind what is under it. You do."));
        }

        void OnPropAny(Prop pr)
        {
            if (Running) return;
            if (Game.CommonProp(pr)) return;
            // things that only have something to say about themselves (a barred way, a wreck, the boats):
            // the map carries the words, "waking~~dream" when the dream sees it differently
            if (pr.Kind == "look" && pr.data != null && pr.data.id == "say" && !string.IsNullOrEmpty(pr.data.text))
            {
                // "waking~~dream~~after": a third part is what it says once the dead of the hill are asleep
                var parts = pr.data.text.Split(new[] { "~~" }, System.StringSplitOptions.None);
                bool dream = Dream.I && Dream.I.IsDreamAt(pr.basePos);
                string say = dream && parts.Length > 1 && parts[1].Length > 0 ? parts[1] : parts.Length > 2 && Has("chapter2_done") ? parts[2] : parts[0];
                // on the first night nothing has been lying about for forty of them yet
                if (FirstNight && say.ToLowerInvariant().Contains("forty")) say = "Quiet. Everything in Ashkel is exactly where it was put down an hour ago.";
                Run(Narrate(say));
                return;
            }
            // a wall with a crack in it says what it is hiding, more or less
            if (pr.Kind == "crack" && pr.data != null && !string.IsNullOrEmpty(pr.data.text))
            {
                Run(Narrate(pr.data.text));
                return;
            }
            propHandler?.Invoke(pr);
        }

        /// <summary>Stats that follow from what Azar carries.</summary>
        public void ApplyItems()
        {
            var p = Player.I;
            if (!p) return;
            p.hasShield = Has("item_shield");
            p.hasSword = Has("item_sword");
            p.hasLantern = Has("item_wakefire");
            if (Dream.I) Dream.I.Locked = !p.hasLantern;
            Dream.I.Seconds = Has("item_oil") ? 14f : 7f;
            int max = 6 + (Has("item_lamp") ? 2 : 0) + 2 * Count("vessels");
            if (p.health.max != max) { p.health.max = max; p.health.hp = Mathf.Min(max, Mathf.Max(p.health.hp, 1)); }
        }

        /// <summary>What to call the action button and the item button for whoever is playing.</summary>
        public static string ActName => TouchControls.Wanted ? "the {g}action{/} button" : "{g}E{/}";
        public static string ItemName => TouchControls.Wanted ? "the {g}item{/} button" : "{g}F{/}";

        public static IEnumerator GiveItem(string what)
        {
            switch (what)
            {
                case "sword":
                    Set("item_sword"); I.ApplyItems();
                    yield return MainItemGet("khopesh", SwordText);
                    yield return Narrate(LessonBlade(TouchControls.Wanted));
                    break;
                case "wakefire":
                    Set("item_wakefire"); I.ApplyItems();
                    Items.Chosen = "wakefire";
                    yield return MainItemGet("wakefire", WakefireText);
                    yield return I.TheFlameExplained();
                    break;
                case "shield":
                    Set("item_shield"); I.ApplyItems();
                    yield return MainItemGet("mirror_shield", ShieldText);
                    break;
                case "map_zig":
                    Set("item_map_zig");
                    yield return ItemGet("scroll", "You got the {g}SCROLL OF THE ZIGGURAT{/}!^The builders' own drawing, floor by floor.| Open your pack and turn to the map: every room is on it.");
                    break;
                case "map_tomb":
                    Set("item_map_tomb");
                    yield return ItemGet("scroll", "You got the {g}SCROLL OF THE KING'S TOMB{/}!^The tomb as its architect drew it, and as he was told to forget it.| Every room is on the map page now.");
                    break;
                case "fork_zig":
                    Set("item_fork_zig");
                    yield return ItemGet("fork_zig", "You got the {g}LAPIS FORK{/}!^A tuning fork, enamelled temple blue. Strike it and it listens for chests nobody has opened: the nearer one is, the higher it hums.| A room it has found goes on the ziggurat's plan.^It is in your pack. Put it on the {g}item button{/} to strike it.| The temple's treasurers carried one. The temple's thieves carried two.^The temple lends it, and takes it back at the door: outside the ziggurat it is not in your pack. Inside, it is.| The temple has always been like this about its things.");
                    break;
                case "fork_tomb":
                    Set("item_fork_tomb");
                    yield return ItemGet("fork_tomb", "You got the {g}CARNELIAN FORK{/}!^The king's own, the red of old blood. It listens for his chests the way the lapis one listens for the temple's.| He had it made to keep count of what he was buried with.^He was buried with it, which nobody thought through.| Like the other, it stays in its own house.");
                    break;
                case "wheel":
                    Set("item_wheel"); I.ApplyItems();
                    Items.Chosen = "wheel";
                    yield return MainItemGet("sun_wheel", WheelText);
                    yield return Narrate(LessonWheel(TouchControls.Wanted));
                    break;
                case "pocket":
                    Set("item_pocket"); I.ApplyItems();
                    Items.Chosen = "pocket";
                    yield return MainItemGet("pocket", PocketText);
                    break;
                case "map_barrow":
                    Set("item_map_barrow");
                    yield return ItemGet("scroll", "You got the {g}BARROW ROLL{/}!^A plan of the barrow, drawn up for the funeral.| Both generals have corrected it. In ink. Over each other.^Open your pack and turn to the map: every room is on it.");
                    break;
                case "map_crypt":
                    Set("item_map_crypt");
                    yield return ItemGet("scroll", "You got the {g}WATCH ROLL{/}!^A plan of the crypt, kept up by four hundred years of sergeants.| One of them drew a goat in the margin.^Open your pack and turn to the map: every room is on it.");
                    break;
                case "oil":
                    Set("item_oil"); I.ApplyItems();
                    yield return ItemGet("night_oil", "You got the {g}NIGHT OIL{/}!^A sip before you nod off and your dreams last twice as long.| Abu-Nur swears it isn't just fish oil.| It's mostly fish oil.");
                    break;
                case "lamp":
                    Set("item_lamp"); I.ApplyItems(); Player.I.health.hp = Player.I.health.max;
                    yield return ItemGet("bronze_lamp", "You got the {g}BRONZE LAMP{/}!^A second little flame to keep the Wakefire company.| Your {g}LIFE{/} grows by one flame.");
                    break;
                case "bigkey":
                    Set("bigkey");
                    yield return ItemGet("big_key", "You got the {g}BULL KEY{/}!^Horned, heavy, and warm to the touch, as if something has been breathing on it.");
                    break;
                case "ghostkey":
                    Set("ghostkey");
                    Sfx.Play("ghost_key", 0.9f, 0f);
                    yield return ItemGet("ghost_key", "You got the {g}GHOST KEY{/}!^The key to the king's own door. It was buried with the steward who kept it, and it has not been a real key for four hundred years.| "
                                                    + "You can see your hand through it. It still knows which lock is its lock.");
                    break;
                case "vessel":
                    Bump("vessels"); I.ApplyItems(); Player.I.health.hp = Player.I.health.max;
                    yield return ItemGet("flame_vessel", "A {g}FLAME VESSEL{/}! Your {g}LIFE{/} grows by one flame.");
                    break;
                default:
                    yield return Narrate("...");
                    break;
            }
        }

        /// <summary>Text on the dark, between scenes.</summary>
        public static IEnumerator Card(params string[] lines)
        {
            Fade.Backdrop("title_bg");
            foreach (var l in lines)
            {
                for (float t = 0; t < 0.25f; t += Time.unscaledDeltaTime) yield return null;
                Fade.Set(0.8f, l, true);
                float hold = 1.2f + l.Length * 0.045f;
                for (float t = 0; t < hold; t += Time.unscaledDeltaTime)
                {
                    if (t > 0.4f && (Controls.Down(Controls.Interact) || Controls.Down(Controls.Attack) || Controls.Tapped)) break;
                    yield return null;
                }
                Fade.Set(0.8f, "", true);
            }
            Fade.Set(1);
            Fade.Backdrop(null);
        }

        /// <summary>The first lesson: what each button does, for thumbs or for keys.</summary>
        public static string Lesson(bool touch) => touch
            ? "Put your thumb down anywhere on the left to {g}walk{/}. The {g}action{/} button does whatever is in front of you: talk, open, read, look.^The button at the top opens your {g}pack{/}: what you carry, your journeys, the map."
            : "Move with {g}WASD{/} or the arrows. {g}E{/} does whatever is in front of you: talk, open, read, look.^{g}Esc{/} opens your {g}pack{/}: what you carry, your journeys, the map.";

        public static string SwordText => "You got the {g}KHOPESH OF THE WATCH{/}!^The first watchman's own blade, hooked like a sickle, and still sharp.^The night watch of Ashkel has not been trusted with one in living memory.| They get a rattle.";

        /// <summary>The second lesson, when there is a blade to swing.</summary>
        public static string LessonBlade(bool touch) => touch
            ? "Swing it with the {g}blade{/} button: three cuts, if you keep swinging. Roll out of trouble with the {g}circle{/}."
            : "Swing it with {g}J{/} or {g}Space{/}: three cuts, if you keep swinging. Roll out of trouble with {g}K{/}.";

        public static string WakefireText => "You got the {g}WAKEFIRE{/}!^The watch-flame of Ashkel. The first watchman lit it from the sky god's own lamp, the night the city was founded.^He said: while this burns, someone is awake.| It has not gone out since.";

        /// <summary>The third lesson, when there is a flame to carry and a sleep to dare.</summary>
        public static string LessonFlame(bool touch) => touch
            ? "Hold out the {g}Wakefire{/} with the {g}lamp{/} button. It lights what ought to be lit.^And nod off with the {t}moon{/}. You go where the whole city has gone, and the flame brings you back before long."
            : "Hold out the {g}Wakefire{/} with {g}F{/}. It lights what ought to be lit.^And nod off with {t}Q{/}. You go where the whole city has gone, and the flame brings you back before long.";

        /// <summary>What the mirror shield says when Azar lifts it out of its chest.</summary>
        public static string ShieldText => "You got the {g}BRONZE MIRROR SHIELD{/}!^Polished so bright you can see how tired you look.^With nothing in front of you, hold " + ActName + " to raise it.^A blow from the front glances off it. And fire goes back where it came from.";

        public static string PocketText => "You got {g}NOD'S POCKET{/}!^A soldier's belt pouch, worn soft. Whatever is in it is, at the moment, asleep.| "
            + "One thing you pick up in a dream comes back with you when you wake.^In a dream, face something small and press " + ActName + " to pocket it. Awake, " + ItemName + " uses it.| "
            + "It holds one thing at a time. Take a second, and the first goes back where you dreamed it.^"
            + "Nod was the best they ever had. He was always finding useful things in his dreams.| The only problem was, they always caught him sleeping on the job.";

        public static Story Ensure()
        {
            if (I) return I;
            var go = new GameObject("Story");
            DontDestroyOnLoad(go);
            I = go.AddComponent<Story>();
            return I;
        }

        public static bool Has(string f) => Flags.Contains(f);
        public static void Set(string f) => Flags.Add(f);
        public static void Clear(string f) => Flags.Remove(f);

        /// <summary>For checks: everything Azar is carrying by the time chapter one begins.</summary>
        public static void GiveKit()
        {
            Set("item_sword"); Set("item_wakefire"); Set("prequel_done");
            if (I) I.ApplyItems();
        }
        public static int Count(string key) => counts.TryGetValue(key, out var n) ? n : 0;
        /// <summary>Increments a counter and returns its value before the increment (0 the first time).</summary>
        public static int Bump(string key) { int n = Count(key); counts[key] = n + 1; return n; }

        /// <summary>Drop whatever scene is playing (a new game or a return to the title must never
        /// wait behind, or be swallowed by, the end of the last one).</summary>
        public static void Abort()
        {
            var s = Ensure();
            s.StopAllCoroutines();
            if (s.Speaker) s.Speaker.EndTalk();
            s.Speaker = null;
            s.Running = false;
            DialogueBox.Reset();
            Fade.Backdrop(null);            // a scene cut short must not leave its picture over the world
            var v = PixelView.I;
            if (v && Player.I) v.target = Player.I.transform;
        }

        /// <summary>Play a scene as soon as whatever is playing now has finished.</summary>
        public static void RunWhenFree(IEnumerator scene)
        {
            var s = Ensure();
            s.StartCoroutine(s.Queue(scene));
        }

        IEnumerator Queue(IEnumerator scene)
        {
            while (Running) yield return null;
            Run(scene);
        }

        public static void Run(IEnumerator scene, Npc speaker = null)
        {
            var s = Ensure();
            if (s.Running) return;
            s.StartCoroutine(s.Wrap(scene, speaker));
        }

        IEnumerator Wrap(IEnumerator scene, Npc speaker)
        {
            Running = true;
            Speaker = speaker;
            var p = Player.I;
            if (p) p.SetState(Player.State.Talk, "idle");
            if (speaker) speaker.BeginTalk(p ? p.pos : speaker.pos);
            yield return scene;
            if (speaker) speaker.EndTalk();
            if (p && p.state == Player.State.Talk) p.SetState(Player.State.Free, "idle");
            Speaker = null;
            Running = false;
        }

        // ------------------------------------------------------------------ scene helpers
        public static IEnumerator Say(string who, string text, string voice = "narrator", bool dream = false) => DialogueBox.Say(who, text, voice, dream);
        public static IEnumerator Narrate(string text) => DialogueBox.Say(null, text, "narrator");
        public static IEnumerator AzarSays(string text) => DialogueBox.Say("Azar", text, "azar");

        /// <summary>Glide the camera to a point (the player stops being followed until CamBack).</summary>
        public static IEnumerator CamTo(Vector2 to, float seconds)
        {
            var v = PixelView.I;
            v.target = null;
            var from = v.focus;
            for (float t = 0; t < seconds; t += Time.deltaTime)
            {
                v.focus = Vector2.Lerp(from, to, Mathf.SmoothStep(0, 1, t / seconds));
                yield return null;
            }
            v.focus = to;
        }

        public static IEnumerator CamBack(float seconds)
        {
            var p = Player.I;
            if (!p) yield break;
            yield return CamTo(p.pos, seconds);
            PixelView.I.target = p.transform;
        }

        public static IEnumerator Wait(float s)
        {
            float t = 0;
            while (t < s) { t += Time.deltaTime; yield return null; }
        }

        /// <summary>Azar lifts a new item over his head while the fanfare plays.</summary>
        /// <summary>One of the few things the whole game turns on, lifted out of a great chest: it rises
        /// in its own light, the music stands aside for a fanfare, and only then does anyone speak.</summary>
        public static IEnumerator MainItemGet(string itemSprite, string text)
        {
            var p = Player.I;
            p.Face(Facing.Down);
            p.SetState(Player.State.ItemGet, "itemget");
            var go = new GameObject("ItemShown");
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sharedMaterial = Map.SpriteMat;
            sr.sprite = Map.GetSprite("Items/" + itemSprite, 8, 16);
            sr.sortingOrder = Map.Order(p.pos.y) + 4;
            var glow = LightBlob.Create(go.transform, p.pos, 1.0f, new Color(1f, 0.86f, 0.5f), 0.9f, true);
            glow.height = 2.4f;
            Music.Duck(0.25f, 5.6f);
            Sfx.Play("main_item", 1f, 0f);
            Vector2 from = p.pos + new Vector2(0, 0.9f), to = p.pos + new Vector2(0, 2.75f);
            for (float t = 0; t < 2.1f; t += Time.deltaTime)
            {
                float k = Mathf.SmoothStep(0, 1, t / 2.1f);
                go.transform.position = Vector2.Lerp(from, to, k);
                glow.radius = Mathf.Lerp(1.0f, 6.5f, k);
                if (Random.value < 0.5f) Fx.Sparks((Vector2)go.transform.position + Random.insideUnitCircle * 0.35f, new Color(1f, 0.9f, 0.55f), 1);
                yield return null;
            }
            PixelView.I.Shake(1, 0.25f);
            for (int i = 0; i < 16; i++)
            {
                float a = i / 16f * Mathf.PI * 2f;
                Fx.Spawn(to, new Vector2(Mathf.Cos(a), Mathf.Sin(a)) * 3.4f, 0.2f, 1.5f, 0.7f, new Color(1f, 0.92f, 0.6f), new Color(0.9f, 0.5f, 0.15f), 0f, 1);
            }
            yield return Wait(1.3f);
            yield return Narrate(text);
            Destroy(go);
            p.SetState(Player.State.Talk, "idle");
            if (Game.I && Game.I.CurrentMap != null) Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn);
        }

        public static IEnumerator ItemGet(string itemSprite, string text)
        {
            var p = Player.I;
            p.Face(Facing.Down);
            p.SetState(Player.State.ItemGet, "itemget");
            var go = new GameObject("ItemShown");
            var sr = go.AddComponent<SpriteRenderer>();
            sr.sharedMaterial = Map.SpriteMat;
            sr.sprite = Map.GetSprite("Items/" + itemSprite, 8, 16);
            go.transform.position = (Vector3)(p.pos + new Vector2(0, 2.55f));
            sr.sortingOrder = Map.Order(p.pos.y) + 2;
            Sfx.Play("itemget", 1f, 0f);
            PixelView.I.Shake(0, 0);
            yield return Wait(0.5f);
            yield return Narrate(text);
            Destroy(go);
            p.SetState(Player.State.Talk, "idle");
            if (Game.I && Game.I.CurrentMap != null) Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn);
        }
    }
}
