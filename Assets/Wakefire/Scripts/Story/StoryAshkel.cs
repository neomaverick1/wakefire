// Ashkel, the Temple Gate square: who is asleep where, what their dream-selves have to say,
// and the first lock: Captain Dur's key, which his six-year-old dream-self will only give up
// once the three braziers are burning.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        Npc dur, durChild, goat;

        public void SetupAshkel(Map m)
        {
            foreach (var mk in m.data.markers)
            {
                if (mk.kind != "npc") continue;
                var at = Map.ToWorld(mk.x, mk.y);
                if (!SpawnHouse(mk.who, at)) Spawn(mk.who, at);
            }
            propHandler = OnProp;
            // what was done here stays done
            if (Has("braziers"))
                foreach (var id in new[] { "square_0", "square_1", "square_2" }) { var b = m.Find(id); if (b) b.Ignite(); }
            // ...and so does what it brought on: the thing that has come to see about the light
            if (Has("key") && !Has("dead_" + SquareSnuffer) && !FirstNight) SnufferComes(false);
            if (Has("gate_open"))
            {
                var gate = m.Find("temple_gate");
                if (gate)
                {
                    if (gate.solid != null) { Solids.Remove(gate.solid); gate.solid = null; }
                    foreach (var o in m.data.objects)
                        if (o.s == "gate_temple_open") { gate.data.px = o.px; gate.data.py = o.py; gate.SetSprite(o.s, o.px, o.py); }
                }
            }
        }

        const string SquareSnuffer = "ak_snuffer";

        /// <summary>The lamp seller's bad dream walks out of the lamp seller's door.</summary>
        void SnufferComes(bool now)
        {
            foreach (var e in Enemy.All) if (e is Snuffer) return;
            var s = Snuffer.Spawn(Map.ToWorld(910, now ? 222 : 240));
            s.spawnId = SquareSnuffer;
            if (now) { Sfx.Play("snuffer_clang", 0.5f, 0.03f); PixelView.I.Shake(1, 0.2f); }
        }

        /// <summary>A fire in the square has gone out, or come back: the boy in the dream knows at once.</summary>
        void FiresChanged()
        {
            if (durChild && Has("braziers") && !Has("gate_open")) durChild.SetIdle(LitBraziers() >= 3 ? "idle" : "cower");
        }

        void Spawn(string who, Vector2 at)
        {
            switch (who)
            {
                case "captain":
                    dur = Npc.Create("dur", at, "captain", "lean", WorldLayer.Waking);
                    dur.turnsToTalk = false;
                    dur.voice = "dur";
                    dur.talk = TalkDur;
                    durChild = Npc.Create("dur_child", at + new Vector2(0, -0.1f), "captain_child", Has("braziers") ? "idle" : "cower", WorldLayer.Dream);
                    durChild.voice = "child";
                    durChild.talk = TalkDurChild;
                    break;
                case "goat":
                    goat = Npc.Create("goat", at, "goat", "stare", WorldLayer.Both, Facing.Right);
                    goat.turnsToTalk = false;
                    goat.talk = TalkGoat;
                    break;
                case "dreamer":
                {
                    var body = Npc.Create("dreamer", at, "sleeper_b", "lie", WorldLayer.Waking, Facing.Down, false);
                    body.turnsToTalk = false;
                    body.talk = () => One(Narrate("A man asleep on the paving stones, smiling.^Whatever he's dreaming, it beats Ashkel."));
                    var self = Npc.Create("dreamer_self", at + new Vector2(0.6f, 0), "sleeper_b", "idle", WorldLayer.Dream);
                    self.talk = TalkDreamer;
                    break;
                }
                case "walker":
                {
                    var body = Npc.Create("walker", at, "sleeper_c", "sleepwalk", WorldLayer.Waking, Facing.Right);
                    body.route = new[] { at, at + new Vector2(4.5f, 2.2f), at + new Vector2(6.5f, 2.2f), at + new Vector2(4.5f, 2.2f) };
                    body.walkAnim = "sleepwalk";
                    body.pauseAnim = "sleep";
                    body.walkSpeed = 0.9f;
                    body.turnsToTalk = false;
                    body.talk = () => One(Narrate("Widow Ilta, sleepwalking her morning round. Well. Stall. Well. Stall.^Forty nights. Her feet know the way better than she does."));
                    var self = Npc.Create("walker_self", at + new Vector2(-1.2f, 0.4f), "sleeper_c", "idle", WorldLayer.Dream);
                    self.voice = "woman";
                    self.talk = TalkWidow;
                    break;
                }
                case "merchant":
                {
                    var body = Npc.Create("merchant", at, "sleeper_a", "sleep", WorldLayer.Waking);
                    body.turnsToTalk = false;
                    body.talk = () => One(Say("Fig Seller", "Three for a shekel...| two for a shekel...| everything must go...", "merchant"));
                    var self = Npc.Create("merchant_self", at, "sleeper_a", "idle", WorldLayer.Dream);
                    self.talk = () => One(Say("Fig Seller", "In dreams, everything is free.^That's why I hate them.", "merchant", true));
                    break;
                }
            }
        }

        static IEnumerator One(IEnumerator e) { yield return e; }

        // ------------------------------------------------------------------ Captain Dur
        IEnumerator TalkDur()
        {
            if (Has("key"))
            {
                yield return Narrate("Captain Dur sleeps on, one key lighter.^He looks... relieved.");
                yield break;
            }
            int n = Bump("dur");
            if (n == 0)
            {
                yield return Narrate("Captain Dur of the Temple Gate, asleep on his feet for forty nights.^The {g}Gate Key{/} hangs from his belt.");
                yield return Say("Captain Dur", "Hnnh... hold the line...| hold...| the...| bread...", "dur");
                yield return AzarSays("Forty nights and he hasn't fallen over once. Respect.");
            }
            else if (n == 1)
                yield return Narrate("You reach for the key. Dur's fist closes over it without waking.^Even asleep, he outranks you.");
            else
            {
                yield return Say("Captain Dur", "Mmh... Mother...| the dark has teeth...", "dur");
                yield return Narrate("Whatever Dur is dreaming, the key to it is in there with him.^{t}Nod off{/} beside him and see.");
            }
        }

        IEnumerator TalkDurChild()
        {
            const string who = "Dur, age six";
            if (Has("braziers") && LitBraziers() < 3)
            {
                yield return Say(who, "It came BACK! The dark came back!| It's got legs now!", "child", true);
                yield return Say(who, Has("key") ? "You can keep the key. I don't want it. I want the fires." : "Light them again! All {g}three{/}!", "child", true);
                yield break;
            }
            if (Has("key"))
            {
                yield return Say(who, "Don't tell the captain. He'd be so cross.", "child", true);
                yield break;
            }
            if (Has("braziers"))
            {
                yield return Say(who, "You did it! The dark went somewhere else.", "child", true);
                yield return Say(who, "I'm brave now. And brave people don't need keys. Here.", "child", true);
                yield return ItemGet("gate_key", "You got the {g}GATE KEY{/}!^It's warm, like it was held very tightly for a very long time.");
                Player.I.keys++;
                Set("key");
                yield return Say(who, "Don't tell the captain.", "child", true);
                yield return Say(who, "And if you're going up the ziggurat, ask the oracle in the {g}lower town{/} first. Down the road, south.^She knows everything. She says so herself.", "child", true);
                // (three fires burning in a city where every flame went out: something was bound to come and see about it)
                if (!Has("dead_" + SquareSnuffer)) SnufferComes(true);
                yield break;
            }
            int n = Bump("dur_child");
            if (n == 0)
            {
                yield return Say(who, "Who's there?! Are you the dark?", "child", true);
                yield return AzarSays("I'm the night watch. Technically, I'm in charge of the dark.");
                yield return Say(who, "Then make it go away! Mother says the dark has teeth.", "child", true);
                yield return Say(who, "Light the fires. All {g}three{/}. Then I'll be brave.", "child", true);
                Set("dur_asked");
            }
            else
            {
                int lit = LitBraziers();
                yield return Say(who, lit == 0 ? "The fires! Your lamp can light them, can't it?" : $"That's {lit}.| That's not three.| I can count, you know.", "child", true);
            }
        }

        int LitBraziers()
        {
            int n = 0;
            var m = Map.Current;
            if (!m) return 0;
            foreach (var p in m.props) if (p && p.Kind == "brazier" && p.lit && p.data.id != null && p.data.id.StartsWith("square_")) n++;
            return n;
        }

        // ------------------------------------------------------------------ townsfolk
        IEnumerator TalkGoat()
        {
            bool dream = Dream.I.IsDreamAt(goat.pos);
            if (dream && !Has("goat_dream"))
            {
                Set("goat_dream");
                yield return Narrate("In the dream, the goat looks exactly the same.^The goat does not dream.");
                yield break;
            }
            if (FirstNight)
            {
                // the night it happened: the only other one awake, and no help at all
                int k = Bump("goat_night");
                if (k == 0) { goat.Play("bleat", true); Sfx.Play("goat"); }
                string[] night =
                {
                    "A goat. It's awake.^Of everyone in Ashkel the god's sleep could have missed, it missed you and the goat.",
                    "You get the feeling the goat was not asleep before, either.",
                    "You ask the goat what happened.| The goat chews.| That is its statement.",
                    "The goat has no rattle, no post and no captain, and it is having a better night than you are.",
                };
                yield return Narrate(night[Mathf.Min(k, night.Length - 1)]);
                goat.SetIdle("stare");
                yield break;
            }
            int n = Bump("goat");
            if (n == 0) { goat.Play("bleat", true); Sfx.Play("goat"); }
            string[] lines =
            {
                "A goat. It's awake.",
                "The goat is awake.| The goat has always been awake.",
                "The goat stares at you. You stare at the goat.| You blink first.",
                "You have lost a staring contest to a goat.^Forty nights without sleep will do that to a man.",
                "The goat is chewing something. It's leather.| It's your sandal strap.",
            };
            yield return Narrate(lines[Mathf.Min(n, lines.Length - 1)]);
            goat.SetIdle("stare");
        }

        IEnumerator TalkDreamer()
        {
            int n = Bump("dreamer");
            if (n == 0)
            {
                yield return Say("Fishmonger", "Behold, friend! My palace!", "man", true);
                yield return AzarSays("That's a bush.");
                yield return Say("Fishmonger", "In here it's a palace. Out there, I gut fish.|\n...Don't wake me.", "man", true);
            }
            else yield return Say("Fishmonger", "Mind the moat. It's very deep.| It's a puddle.| Mind it anyway.", "man", true);
        }

        IEnumerator TalkWidow()
        {
            if (Has("item_figs") && !Has("figs_given")) { yield return FigsDelivered(); yield break; }
            if (Has("figs_given"))
            {
                yield return Say("Widow Ilta", "Forty years, and he sends a watchman.| ...I've kept one back for him. Don't tell him that either.", "woman", true);
                yield break;
            }
            int n = Bump("widow");
            if (n == 0)
            {
                yield return Say("Widow Ilta", "Have you seen my husband? He went out for figs.", "woman", true);
                yield return Say("Widow Ilta", "...Forty years ago.", "woman", true);
                yield return Say("Widow Ilta", "They must be very good figs.", "woman", true);
            }
            else yield return Say("Widow Ilta", "When he comes back, I'll have a word. Several words.| Most of them about figs.", "woman", true);
        }

        // ------------------------------------------------------------------ things in the square
        void OnProp(Prop p)
        {
            bool dream = Dream.I.IsDreamAt(p.basePos);
            switch (p.Kind)
            {
                case "brazier":
                    FiresChanged();
                    if (p.lit && !Has("braziers") && LitBraziers() >= 3)
                    {
                        Set("braziers");
                        Sfx.Play("secret", 1f, 0f);
                        if (durChild) durChild.SetIdle("idle");
                        Run(Narrate("Three fires burn in the square.^Somewhere in a dream, a small boy stops shaking."));
                    }
                    break;
                case "sign":
                    Run(dream ? Narrate("The letters crawl around and rearrange themselves:^{t}KNOCK ANYWAY.{/}")
                              : Narrate("{g}TEMPLE OF NINHAL{/}\nThe god is resting. Do not knock.\nBy order of Ebrum, High Priest."));
                    break;
                case "well":
                    Run(dream ? Narrate("The well whispers: {t}Drink, and forget.{/}^You have enough to forget already.")
                              : Narrate("A well. Somewhere down there, a frog is asleep too."));
                    break;
                case "gate":
                    Run(Has("key") ? OpenGate(p) : Narrate("The Temple Gate. Bronze, cedar, and very locked.^Captain Dur has the key. Captain Dur has had a long night."));
                    break;
                case "pot":
                    Run(Narrate(Bump("pot") == 0 ? "A storage jar, sealed with wax. It smells like old olives and older secrets." : "Another jar. Someone in Ashkel really liked olives."));
                    break;
            }
        }

        IEnumerator OpenGate(Prop gate)
        {
            if (Has("gate_open")) { yield return Narrate("The gate stands open. The ziggurat waits beyond it."); yield break; }
            yield return Narrate("The bronze lock turns with a sound like a sigh.");
            Sfx.Play("gate_open", 1f, 0f);
            PixelView.I.Shake(2, 0.6f);
            Set("gate_open");
            if (gate.solid != null) { Solids.Remove(gate.solid); gate.solid = null; }
            foreach (var o in Map.Current.data.objects)
                if (o.s == "gate_temple_open") { gate.data.px = o.px; gate.data.py = o.py; gate.SetSprite(o.s, o.px, o.py); }
            Fx.Dust(gate.basePos + new Vector2(-1, 0.2f), 6);
            Fx.Dust(gate.basePos + new Vector2(1, 0.2f), 6);
            yield return Wait(0.8f);
            yield return Narrate("Somewhere above, a god snores.");
        }
    }
}
