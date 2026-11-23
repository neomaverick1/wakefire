// Nod's Pocket. A soldier's belt pouch that is itself a little bit asleep: one small thing picked
// up in a dream comes back with Azar when he wakes. In the dream the action button pockets what
// he is facing; awake, the item button uses it on whatever is in front of him. It holds one thing
// at a time: take a second and the first goes back where it was dreamed.
//
// The rule is the whole of it, so a new thing is one line in Things below and a prop in a map
// (kind "dreamthing", dream layer, text = the thing's id; who "source" = there is always another).
// What the things act on in the waking world:
//   key    a lock with no waking key        prop kind "dreamlock"  (flag door_<id>)
//   plank  two brackets across a drop       prop kind "plankgap", the plank itself kind "plank" (flag on_<id>)
//   flame  a cold lamp of the dead          prop kind "bluelamp"   (flag on_<id>, so a grille can say lit:<id>)
//   snore  whatever is awake in front of him
//   goat   an offering scale with an empty pan      prop kind "scale" (flag on_<id>)
//   order  the king's clay, which stands there      (and the servants it was taken from sit down)
using System;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace Wakefire
{
    public static class Pocket
    {
        public class Thing
        {
            public string id, name, about;
            /// <summary>What the game says the first time it goes in, and when it is used with nothing in front that wants it.</summary>
            public string took, nothing;
            /// <summary>Uses it on what is in front of him. True if it did something.</summary>
            public Func<Player, bool> use;
            /// <summary>Still in the pocket after it has done its job.</summary>
            public bool keeps;
        }

        public static readonly Thing[] Things =
        {
            new Thing { id = "key", name = "Dream Key", use = UseKey,
                about = "A key that was only ever dreamed.|It opens one lock that has no other key, and then it has done what it came for.",
                took = "A key, hanging where the dream remembers one.^It weighs nothing, and it is cold the way a thought is cold. It goes in the Pocket.",
                nothing = "The dream key turns over in your fingers.^Nothing here wants unlocking. Or nothing here admits to it." },
            new Thing { id = "plank", name = "Plank of Moonlight", use = UsePlank,
                about = "Cut from a road only dreamers walk.|Laid across a drop between two brackets, it is a bridge for a man with his eyes open.",
                took = "A plank of moonlight, off the top of the stack.^It is lighter than the idea of a plank. It folds into the Pocket like a letter.",
                nothing = "You hold the plank of moonlight out over nothing in particular.^It wants a drop, and two brackets to rest on." },
            new Thing { id = "flame", name = "Blue Flame", use = UseFlame,
                about = "A flame the dream kept burning. It is cold.|The lamps of the dead will take no other.",
                took = "You cup a tongue of the blue fire and it comes away in your hand.^It burns cold. It does not mind the Pocket at all.",
                nothing = "The blue flame leans one way and then the other, looking for a lamp.^At your belt the Wakefire pretends not to have noticed it." },
            new Thing { id = "snore", name = "Nod's Snore", use = UseSnore,
                about = "Four hundred years old and still going.|Let it out at something that is awake, and it will not be for long.",
                took = "A snore, hanging over the bench where it was left.^It is the only part of Nod still on duty.| You fold it up small. It goes on snoring, quietly, in the Pocket.",
                nothing = "You let the snore out.^It goes once round the room, finds nobody to settle on, and comes back to the Pocket looking hurt." },
            new Thing { id = "goat", name = "A Whole Gold Goat", use = UseGoat,
                about = "Out of a thief's dream of being rich.|It weighs exactly what a king's offering should. Somebody was counting.",
                took = "A whole gold goat, off the top of a thief's dream.^It ought not to fit. The Pocket takes it the way a sleeper takes a blanket.| {g}'HALVES!'{/} says Zimu, in his sleep.",
                nothing = "You take out the gold goat and look at it.^It looks back the way gold does: as if you owed it something.| It wants an offering pan to stand in." },
            new Thing { id = "order", name = "A Standing Order", use = UseOrder,
                about = "The king's own, four hundred years old: 'STAND THERE.'|Let it out and his clay will do it, for a while.",
                took = "An order, hanging in the doorway where the king left it four hundred years ago:^{g}'STAND THERE.'{/}| Nobody is standing there now. You fold it once and it goes in the Pocket.^It is heavy, for something nobody can see.",
                nothing = "You let the order out.^{g}'STAND THERE.'{/}| Nobody here was made to take orders. You, least of all.^It comes back to the Pocket, a little put out." },
            new Thing { id = "word", name = "The Last Word", use = UseWord,
                about = "The last word of an argument that has run three hundred and ninety-one years.|Neither general has ever had it.",
                took = "The last word of the argument, lying where it was dropped.^Neither of them has had it in three hundred and ninety-one years. You have it now." },
        };

        public static Thing Find(string id)
        {
            foreach (var t in Things) if (t.id == id) return t;
            return null;
        }

        public static bool Have => Story.Has("item_pocket");

        /// <summary>What is in it (one flag, "pocket_" + the thing).</summary>
        public static Thing Holding
        {
            get
            {
                foreach (var t in Things) if (Story.Has("pocket_" + t.id)) return t;
                return null;
            }
        }

        /// <summary>Where what is in it was dreamed (the prop's id), if it was the only one of its kind.</summary>
        static string Origin
        {
            get
            {
                foreach (var f in Story.Flags) if (f.StartsWith("took_")) return f.Substring(5);
                return null;
            }
        }

        public static string Art => Holding != null ? "pocket_" + Holding.id : "pocket";
        public static string About => Holding == null
            ? "One thing you pick up in a dream comes back with you when you wake.|It is empty. Nod off, find something small, and take it."
            : "In it: " + Holding.name + ".|" + Holding.about.Replace("|", " ");

        static bool Source(Prop pr) => pr.data.who == "source";

        /// <summary>Is this dream thing where the dream keeps it (not in the pocket, not used up)?</summary>
        public static bool There(Prop pr) => pr && pr.Kind == "dreamthing" && (Source(pr) || (!Story.Has("took_" + pr.data.id) && !Story.Has("spent_" + pr.data.id)));

        static bool InDream(Vector2 at) => Dream.I && Dream.I.IsDreamAt(at);

        // ------------------------------------------------------------------ when a map loads
        /// <summary>What is in the pocket is not where it was; what has been done with the rest stays done.</summary>
        public static void Setup(Map m)
        {
            foreach (var pr in m.props)
            {
                if (!pr) continue;
                switch (pr.Kind)
                {
                    case "dreamthing":
                        if (!There(pr)) pr.Bar(false);
                        if (pr.data.text == "flame") pr.gameObject.AddComponent<DreamGlow>().Init(pr, new Color(0.45f, 0.62f, 1f), 3.2f, 0.7f);
                        break;
                    case "dreamlock":
                        if (Story.Has("door_" + pr.data.id)) pr.Open();
                        break;
                    case "plank":
                        if (Story.Has("on_" + pr.data.id)) Lay(pr, true); else pr.sr.enabled = false;
                        break;
                    case "bluelamp":
                        if (Story.Has("on_" + pr.data.id)) Kindle(pr, true);
                        break;
                    case "scale":
                        if (Story.Has("on_" + pr.data.id)) Weigh(pr, true);
                        break;
                    case "rope":
                    case "bridgeup":
                        if (Story.Has("on_" + pr.data.id)) pr.Bar(false);
                        break;
                }
            }
            if (Dream.I) { Dream.I.Flipped -= OnFlip; Dream.I.Flipped += OnFlip; }
        }

        /// <summary>Waking with something in it: it is still there, and the game says so once in a small way every time.</summary>
        static void OnFlip(bool toDream)
        {
            if (toDream || Holding == null || !Player.I) return;
            Sfx.Play("pocket_keep", 0.7f, 0.02f);
            Hud.Pulse();
        }

        // ------------------------------------------------------------------ in the dream: the action button
        public static void Take(Prop pr)
        {
            var t = Find(pr.data.text);
            var p = Player.I;
            if (t == null || !p) return;
            if (!Have)
            {
                Sfx.Play("deny", 0.5f);
                Story.Run(Story.Narrate("Your hand closes on it and comes away with nothing.^It is a dream. You would need something to put it in that was, itself, a little bit asleep."));
                return;
            }
            if (Holding == t && Source(pr)) { Sfx.Play("deny", 0.5f); return; }       // he has one already
            PutBack();
            Story.Set("pocket_" + t.id);
            if (!Source(pr)) { Story.Set("took_" + pr.data.id); pr.Bar(false); }
            Items.Chosen = "pocket";
            Sfx.Play("pocket_in", 0.9f, 0.02f);
            for (int i = 0; i < 10; i++)
            {
                var from = pr.basePos + new Vector2(0, 0.5f) + UnityEngine.Random.insideUnitCircle * 0.25f;
                Fx.Spawn(from, ((p.pos + new Vector2(0, 0.6f)) - from) * 2.6f, 0f, 0f, 0.38f, new Color(0.80f, 0.88f, 1f), new Color(0.32f, 0.42f, 0.86f), 0f, 1);
            }
            Hud.Pulse();
            if (Story.Bump("pocketed_" + t.id) == 0 && !string.IsNullOrEmpty(t.took)) Story.Run(Story.Narrate(t.took));
        }

        /// <summary>What was in it goes back where it was dreamed.</summary>
        static void PutBack()
        {
            var h = Holding;
            if (h == null) return;
            Story.Clear("pocket_" + h.id);
            string o = Origin;
            if (o == null) return;
            Story.Clear("took_" + o);
            var pr = Map.Current ? Map.Current.Find(o) : null;        // (dreamed on another map: it will be there when he next is)
            if (pr && pr.Kind == "dreamthing") pr.Bar(true);
        }

        static void Spend()
        {
            var h = Holding;
            if (h == null) return;
            Story.Clear("pocket_" + h.id);
            string o = Origin;
            if (o != null) { Story.Clear("took_" + o); Story.Set("spent_" + o); }
        }

        // ------------------------------------------------------------------ awake: the item button
        /// <summary>The item button with the Pocket on it. True if there is something in it to reach for (the
        /// player plays the reach, then calls Apply).</summary>
        public static bool Reach(Player p)
        {
            if (InDream(p.pos))
            {
                Sfx.Play("deny", 0.5f);
                if (Story.Bump("pocket_dreaming") % 4 == 0 && !Story.I.Running)
                    Story.Run(Story.Narrate("Not here.^What is in the Pocket came out of a dream. It only means anything on the other side of one."));
                return false;
            }
            if (Holding == null)
            {
                Sfx.Play("deny", 0.5f);
                if (Story.Bump("pocket_empty") % 4 == 0 && !Story.I.Running)
                    Story.Run(Story.Narrate("Nod's Pocket is empty.^It only holds what a dream has in it. Nod off, find something small, and take it."));
                return false;
            }
            return true;
        }

        public static void Apply(Player p)
        {
            var t = Holding;
            if (t == null) return;
            if (t.use(p)) { if (!t.keeps) Spend(); Hud.Pulse(); return; }
            Sfx.Play("deny", 0.5f);
            if (!string.IsNullOrEmpty(t.nothing) && Story.Bump("pocket_nothing_" + t.id) % 3 == 0 && !Story.I.Running) Story.Run(Story.Narrate(t.nothing));
        }

        // ---- the key
        static bool UseKey(Player p)
        {
            var d = p.InFront(0.7f, q => q.Kind == "dreamlock");
            if (!d) return false;
            string id = d.data.id;
            Story.Set("door_" + id);
            foreach (var pr in Map.Current.props.ToArray())
                if (pr && pr.Kind == "dreamlock" && pr.data.id == id) pr.Open();
            Sfx.Play("unlock", 1f, 0f);
            Sfx.Play("pocket_use", 0.8f, 0f);
            PixelView.I.Shake(1, 0.2f);
            if (Story.Bump("dreamkey_used") == 0)
                Story.Run(Story.Narrate("The key turns in a lock that has had no key for four hundred years.^Then it is not in your hand any more.| Things out of dreams do one job, and they do it properly."));
            return true;
        }

        // ---- the plank
        static bool UsePlank(Player p)
        {
            var g = p.InFront(0.9f, q => q.Kind == "plankgap" && !Story.Has("on_" + q.data.id));
            if (!g) return false;
            string id = g.data.id;
            Story.Set("on_" + id);
            foreach (var pr in Map.Current.props)
                if (pr && pr.Kind == "plank" && pr.data.id == id) Lay(pr, false);
            if (Story.Bump("plank_used") == 0)
                Story.Run(Story.Narrate("The plank goes down across the dark, and stays.^It should not hold a man's weight.| Neither should the moon's road, and you have run on that."));
            return true;
        }

        /// <summary>The plank across its drop: there to be seen, and the drop under it no longer a drop. Its text
        /// is the piece of the pit it covers, "x0,y0,x1,y1" in map pixels.</summary>
        public static void Lay(Prop pr, bool quiet)
        {
            pr.sr.enabled = true;
            var q = (pr.data.text ?? "").Split(',');
            if (q.Length == 4 && int.TryParse(q[0], out int x0) && int.TryParse(q[1], out int y0) && int.TryParse(q[2], out int x1) && int.TryParse(q[3], out int y1))
            {
                var a = Map.ToWorld(x0, y1);
                var r = new Rect(a.x - 0.01f, a.y - 0.01f, (x1 - x0) / 16f + 0.02f, (y1 - y0) / 16f + 0.02f);
                foreach (var s in Solids.All)
                    if (s.pit && r.Contains(s.r.min) && r.Contains(s.r.max)) s.enabled = false;
            }
            if (quiet) return;
            if (pr.data.who == "bridge")
            {
                // a drawbridge of cedar and bronze, let go: it comes down like a door being slammed on four hundred years
                Sfx.Play("stone_door", 1f, 0f);
                Sfx.Play("bars_down", 0.8f, 0f);
                PixelView.I.Shake(3, 0.3f);
                for (int i = 0; i < 6; i++) Fx.Dust(pr.basePos + new Vector2(UnityEngine.Random.Range(-0.6f, 0.6f), UnityEngine.Random.Range(0.2f, 2.4f)), 4);
                return;
            }
            Sfx.Play("plank_down", 1f, 0f);
            PixelView.I.Shake(1, 0.15f);
            for (int i = 0; i < 14; i++)
                Fx.Spawn(pr.basePos + new Vector2(UnityEngine.Random.Range(-0.4f, 0.4f), UnityEngine.Random.Range(0.2f, 2.2f)), new Vector2(UnityEngine.Random.Range(-0.6f, 0.6f), UnityEngine.Random.Range(0.3f, 1.2f)),
                    0f, 0f, UnityEngine.Random.Range(0.4f, 0.8f), new Color(0.82f, 0.9f, 1f), new Color(0.3f, 0.4f, 0.85f), 0f, 1);
        }

        // ---- the blue flame
        static bool UseFlame(Player p)
        {
            var l = p.InFront(0.8f, q => q.Kind == "bluelamp" && !Story.Has("on_" + q.data.id));
            if (!l) return false;
            Story.Set("on_" + l.data.id);
            Kindle(l, false);
            p.Notify(l);
            if (Story.Bump("blueflame_used") == 0)
                Story.Run(Story.Narrate("The lamp takes the cold fire like something it has been owed.^Blue light climbs the wall.| Somewhere close, the dead sit up a little straighter."));
            return true;
        }

        static void Kindle(Prop pr, bool quiet)
        {
            pr.lit = true;
            string s = pr.data.s;
            pr.SetFrames(new[] { s + "_lit_0", s + "_lit_1", s + "_lit_2" });
            Map.Normals(pr.sr, s + "_lit_0_lin");
            var glow = LightBlob.Create(pr.transform, pr.basePos + new Vector2(0, 1.0f), 5.0f, new Color(0.42f, 0.6f, 1f), 0.9f, true);
            glow.height = 1.0f;
            if (quiet) return;
            Sfx.Play("blue_lit", 1f, 0f);
            for (int i = 0; i < 12; i++)
                Fx.Spawn(pr.basePos + new Vector2(0, 1.0f), UnityEngine.Random.insideUnitCircle * 1.6f + new Vector2(0, 1.2f), 0f, 0.5f, UnityEngine.Random.Range(0.4f, 0.8f),
                    new Color(0.75f, 0.86f, 1f), new Color(0.2f, 0.3f, 0.8f), 0f, 1);
        }

        // ---- Nod's snore
        static bool UseSnore(Player p)
        {
            Enemy best = null;
            float bd = 4.2f;
            foreach (var e in Enemy.All)
            {
                if (!e || e.health.Dead || !e.Present || !e.Sleeps) continue;
                var d = e.pos - p.pos;
                if (Vector2.Dot(d.normalized, p.Dir) < 0.2f) continue;
                if (d.magnitude < bd) { bd = d.magnitude; best = e; }
            }
            if (!best) return false;
            best.Sleep(6f);
            Sfx.Play("snore", 1f, 0f);
            for (int i = 0; i < 8; i++)
            {
                var from = p.pos + new Vector2(0, 0.7f);
                Fx.Spawn(from, (best.pos + new Vector2(0, 0.8f) - from) * 1.8f + UnityEngine.Random.insideUnitCircle * 0.6f, 0f, 0f, 0.5f, new Color(0.86f, 0.9f, 1f), new Color(0.4f, 0.45f, 0.8f), 0f, 1);
            }
            return true;
        }

        // ---- the gold goat
        static bool UseGoat(Player p)
        {
            var sc = p.InFront(0.9f, q => q.Kind == "scale" && !Story.Has("on_" + q.data.id));
            if (!sc) return false;
            Story.Set("on_" + sc.data.id);
            Weigh(sc, false);
            if (Story.Bump("goat_used") == 0)
                Story.Run(Story.Narrate("You set the gold goat in the pan.^The pan goes down. It is, to the grain, the weight the king was promised.| Back by the door a thief is going to wake up poorer one day, and never know why."));
            return true;
        }

        static void Weigh(Prop pr, bool quiet)
        {
            pr.SetSprite(pr.data.s + "_full", pr.data.px, pr.data.py);
            if (quiet) return;
            Sfx.Play("coin_big", 1f, 0f);
            Sfx.Play("plate", 1f, 0f);
            PixelView.I.Shake(1, 0.15f);
            Fx.Dust(pr.basePos, 5);
        }

        // ---- the king's order
        static bool Clay(Enemy e) => e is Ushabti || e is Warden;

        static bool UseOrder(Player p)
        {
            Enemy best = null;
            float bd = 5.2f;
            foreach (var e in Enemy.All)
            {
                if (!e || e.health.Dead || !e.Present || !Clay(e)) continue;
                var d = e.pos - p.pos;
                if (Vector2.Dot(d.normalized, p.Dir) < 0.2f) continue;
                if (d.magnitude < bd) { bd = d.magnitude; best = e; }
            }
            if (!best) return false;
            // every one of the king's clay near enough to hear it
            foreach (var e in Enemy.All)
                if (e && !e.health.Dead && e.Present && Clay(e) && Vector2.Distance(e.pos, p.pos) < 7.5f) e.StandThere(9f);
            Sfx.Play("king_wave", 0.9f, 0f);
            PixelView.I.Shake(1, 0.2f);
            if (Story.Bump("order_used") == 0)
                Story.Run(Story.Narrate("You let the order out. It is in the king's voice, and it is four hundred years old:^{g}'STAND THERE.'{/}| The clay stands there. It was made to.^It will not last. Orders wear off. Ask anyone who has given one."));
            return true;
        }

        // ---- the last word
        static bool UseWord(Player p)
        {
            Sfx.Play("pocket_use", 0.8f, 0f);
            Story.Run(Story.Narrate(Story.Bump("lastword_used") == 0
                ? "You take out the last word, and have it.^Up on the hill two generals stop mid-sentence and feel in their robes for something.| It was {g}'anyway'{/}."
                : "You have the last word again.^It was {g}'anyway'{/} again. It usually is."));
            return true;
        }

        // ------------------------------------------------------------------ what the waking things say when looked at
        public static bool Look(Prop pr)
        {
            switch (pr.Kind)
            {
                case "dreamthing":
                    Take(pr);
                    return true;
                case "dreamlock":
                    if (Game.I && Game.I.CurrentMap.StartsWith("tomb"))
                        Story.Run(Story.Narrate(InDream(pr.basePos)
                            ? "Locked, here too. But in the dream there is a key on the wall beside it, where a careful man would hang one."
                            : "A grille across the treasury, and a lock with no key.^The steward who kept it took it to bed with him. He has been in bed four hundred years.| A key like that is only ever anywhere in a dream."));
                    else
                        Story.Run(Story.Narrate(InDream(pr.basePos)
                            ? "Locked, here too. But in the dream the lock looks pleased with itself, like a lock that knows where its key is."
                            : "A grille, and a lock on it with no key.^Not lost. There never was one, awake.| The quartermaster did his stocktaking in his sleep."));
                    return true;
                case "scale":
                    Story.Run(Story.Narrate(Story.Has("on_" + pr.data.id)
                        ? "The gold goat stands in the offering pan, where the king can count it.^It is the only goat in Ashkel that has ever stayed where it was put."
                        : "An offering scale, as tall as you are. One pan holds a stone goat-weight; the other is empty.^Cut in the beam: {g}'ONE GOAT, IN GOLD, OR NOTHING OPENS.'{/}| The king was very specific."));
                    return true;
                case "plankgap":
                    Story.Run(Story.Narrate(Story.Has("on_" + pr.data.id)
                        ? "A plank of moonlight, on two bronze brackets.^It does not creak. You wish it would. Creaking is how you know where you are with a plank."
                        : "Two bronze brackets, one on each side of the drop, and nothing between them.^Somebody meant to put a plank here.| Somebody was probably asleep."));
                    return true;
                case "bluelamp":
                    Story.Run(Story.Narrate(Story.Has("on_" + pr.data.id)
                        ? "It burns blue and gives no heat.^You hold your hand over it anyway. Habit."
                        : "A lamp of the dead, cold. Its wick has never been lit by anything a living man could carry.^The Wakefire will not take on it.| You tried. They looked at each other."));
                    return true;
            }
            return false;
        }
    }

    /// <summary>A light that is only there for a dreamer (the blue fire the dream keeps in).</summary>
    public class DreamGlow : MonoBehaviour
    {
        LightBlob glow;
        float full;
        Prop prop;

        public void Init(Prop pr, Color c, float radius, float intensity)
        {
            prop = pr;
            full = intensity;
            glow = LightBlob.Create(transform, pr.basePos + new Vector2(0, 0.9f), radius, c, 0f, true);
            glow.height = 0.9f;
        }

        void Update()
        {
            if (!glow || !prop) return;
            bool on = Dream.I && Dream.I.IsDreamAt(prop.basePos) && prop.sr.enabled;
            glow.intensity = Mathf.MoveTowards(glow.intensity, on ? full : 0f, Time.deltaTime * 2.5f);
        }
    }
}
