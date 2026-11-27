// The rest of Ashkel and the climb: Hesha's bread, Kesh's pots, the oracle Ummi who dreams the
// way forward, Abu-Nur and his stolen Night Oil, the goat (everywhere, somehow), the temple yard
// and its road of moonlight, the ziggurat's floors, the Brazen Bull, and how chapter one ends.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        partial void SetupRegion(string map, Map m)
        {
            foreach (var mk in m.data.markers)
                if (mk.kind == "npc") SpawnRegion(mk.who, Map.ToWorld(mk.x, mk.y));
            propHandler = RegionProp;
            switch (map)
            {
                case "terraces": if (Has("hill_gate")) SwingOpen(m.Find("hill_gate"), "hill_gate_open"); break;
                case "temple_yard": SetupYard(m); break;
                case "zig_3": StartCoroutine(SetupSummit(m)); break;
            }
        }

        /// <summary>Called by the Bronze Herdsman as he falls.</summary>
        public void HerdsmanDown()
        {
            Music.Play(Map.Current.data.music);
            RunWhenFree(One(Narrate("The Herdsman goes down like a dropped bell, and takes about as long to stop.^Behind him, bars lift. Whatever he was keeping, he kept it in there.")));
        }

        void OpenProp(string id)
        {
            var p = Map.Current.Find(id);
            if (p != null) p.Open();
        }

        Npc Pair(string id, Vector2 at, string sheet, string wakeAnim, string dreamAnim, string voice, System.Func<IEnumerator> wake, System.Func<IEnumerator> dream,
                 Facing f = Facing.Down)
        {
            var body = Npc.Create(id, at, sheet, wakeAnim, WorldLayer.Waking, f);
            body.turnsToTalk = false;
            body.voice = voice;
            body.talk = wake;
            var self = Npc.Create(id + "_self", at, sheet, dreamAnim, WorldLayer.Dream, f, false);
            self.voice = voice;
            self.talk = dream;
            return self;
        }

        void SpawnRegion(string who, Vector2 at)
        {
            if (SpawnHouse(who, at)) return;
            switch (who)
            {
                case "hesha":
                    Pair("hesha", at, "baker", "knead", "idle", "baker",
                        () => One(Narrate("Hesha the baker, kneading dough that isn't there.^Forty nights of it. Her arms are enormous.")), TalkHesha);
                    break;
                case "kesh":
                    Pair("kesh", at, "potter", "sleep", "idle", "potter",
                        () => One(Say("Kesh", "Mmm... spin... spin... don't crack...| don't crack...", "potter")), TalkKesh);
                    break;
                case "ummi":
                    Pair("ummi", at, "oracle", "sleep", "idle", "oracle", TalkUmmiAsleep, TalkUmmi);
                    break;
                case "abunur":
                    Pair("abunur", at, "fisher", "lie", "idle", "fisher",
                        () => One(Narrate("Abu-Nur the fisherman, asleep in a heap of net, smiling at a fish only he can see.")), TalkAbuNur);
                    break;
                case "taxman":
                    Pair("taxman", at, "sleeper_b", "lie", "idle", "man",
                        () => One(Narrate("The tax collector, asleep in the middle of the road.^Nobody has stepped over him in forty nights. Some have stepped on him.")),
                        () => Bump("taxman") == 0
                            ? One(Say("Tax Collector", "Forty nights without taxes. The city has never been happier.| I have never been sadder.", "man", true))
                            : One(Say("Tax Collector", "If you see the goat, tell it it owes eleven years of grazing fees.", "man", true)));
                    break;
                case "flourboy":
                    Pair("flourboy", at, "captain_child", "cower", "idle", "child",
                        () => One(Narrate("The baker's boy, asleep on the flour sacks, white to the eyebrows.")),
                        () => Bump("flourboy") == 0
                            ? One(Say("Baker's Boy", "I'm not asleep. I'm guarding the flour.| From the goat.", "child", true))
                            : One(Say("Baker's Boy", "It came back. It ate a whole sack.| It looked at me the entire time.", "child", true)));
                    break;
                case "lover":
                    Pair("lover", at, "sleeper_c", "sleep", "idle", "man",
                        () => One(Narrate("A young man asleep under a window, lyre in hand, mid-serenade.")),
                        () => One(Say("Young Man", "Forty nights I've been singing to her. She's asleep too.| It's the best relationship I've ever had.", "man", true)));
                    break;
                case "dog":
                    Pair("dog", at, "dog", "sleep", "idle", "dog",
                        () => One(Narrate("A dog, asleep by the well, paws twitching. Chasing something.^Probably the goat.")),
                        () => Bump("dog") == 0
                            ? One(Say("Dog", "In here, I'm a lion.| Well.| A big dog.| A medium dog.", "dog", true))
                            : One(Say("Dog", "If you see the goat, tell it I said nothing. I'm a lion. Lions don't talk to goats.", "dog", true)), Facing.Left);
                    break;
                case "goat_roof":
                {
                    var g = Npc.Create("goat_roof", at, "goat", "idle", WorldLayer.Both, Facing.Down, false);
                    g.orderBias = 2000;
                    g.notice = () => One(Narrate("The goat is standing on the roof.^Nobody knows how. The goat isn't telling."));
                    g.talk = null;
                    break;
                }
                case "goat_cliff": GoatCameo(at, "The goat is here too. On a cliff, over the sea, chewing.^Of course it is.", Facing.Left); break;
                case "goat_terrace": GoatCameo(at, "The goat got up the hill before you did.^It doesn't look tired. It never looks tired.", Facing.Right); break;
                case "goat_yard": GoatCameo(at, "The goat is waiting by the temple gate, as if it has been here for hours.^It has a key-shaped look about it.", Facing.Right); break;
            }
        }

        void GoatCameo(Vector2 at, string line, Facing f)
        {
            var g = Npc.Create("goat_c", at, "goat", "stare", WorldLayer.Both, f);
            g.turnsToTalk = false;
            g.talk = () => GoatLine(g, line);
        }

        IEnumerator GoatLine(Npc g, string line)
        {
            g.Play("bleat", true);
            Sfx.Play("goat");
            yield return Narrate(line);
            g.SetIdle("stare");
        }

        // ------------------------------------------------------------------ lower town
        IEnumerator TalkHesha()
        {
            int n = Bump("hesha");
            if (n == 0)
            {
                yield return Say("Hesha", "Oh, a customer! In here the bread never burns.", "baker", true);
                yield return Say("Hesha", "Out there it's been rising for forty nights. It's taller than me now.| It has opinions.", "baker", true);
                yield return Say("Hesha", "Abu-Nur used to bring oil for my oven. {g}Night Oil{/}, he called it. One sip and you'd dream till noon.", "baker", true);
                yield return Say("Hesha", "Then his own net took it. He left one out, you know. It never stopped.", "baker", true);
            }
            else yield return Say("Hesha", Has("item_oil") ? "You found the oil? Good. Dream a long one for me." : "The cliffs are east, love. Mind the nets. Most of them are only nets.", "baker", true);
        }

        IEnumerator TalkKesh()
        {
            if (Has("kesh_sold"))
            {
                yield return Say("Kesh", "In here my pots never crack. Out there, a goat knocked over my best one.| It looked me in the eye while it did it.", "potter", true);
                yield break;
            }
            yield return Say("Kesh", "A vessel for a flame. Sacred. Holds one more flame of life.", "potter", true);
            yield return DialogueBox.Ask("Kesh", "Forty shekels. Very sacred. Very forty shekels.", "Buy", "Not now", "potter", true);
            if (DialogueBox.Choice != 0) { yield return Say("Kesh", "Suit yourself. It's not going anywhere. Neither am I.", "potter", true); yield break; }
            var p = Player.I;
            if (p.coins < 40) { yield return Say("Kesh", "That's not forty. I can count in my sleep.| I am counting in my sleep.", "potter", true); yield break; }
            p.coins -= 40;
            Set("kesh_sold");
            yield return GiveItem("vessel");
        }

        IEnumerator TalkUmmiAsleep()
        {
            string[] lines =
            {
                "The bull...| the bull is lonely...| bring snacks...",
                "A man who will not sleep...| a goat who cannot...| one of them is the key...",
                "Five more minutes...| that's what he said...| five more minutes...",
            };
            yield return Say("Ummi", lines[Bump("ummi_sleep") % lines.Length], "oracle");
            yield return Narrate("The oracle prophesies in her sleep. Mostly about snacks.");
        }

        IEnumerator TalkUmmi()
        {
            int n = Bump("ummi");
            if (Has("item_oil"))
            {
                yield return Say("Ummi", "The oil. Good. Now dream long, watchman, and climb.", "oracle", true);
                yield return Say("Ummi", "The road of moonlight starts in the temple yard. It's longer than your old naps.| Your new naps will do.", "oracle", true);
                yield break;
            }
            if (n == 0)
            {
                yield return Say("Ummi", "Ah. The one who doesn't sleep. I dreamed you'd come. I dream a lot lately.", "oracle", true);
                yield return Say("Ummi", "Ninhal sleeps on the summit, and the city sleeps with him. Something keeps him down.| Something heavy.| Something bronze.", "oracle", true);
                yield return Say("Ummi", "The way up is a road of moonlight across the chasm in the temple yard. But it's long, and you nod off in short naps.", "oracle", true);
                yield return Say("Ummi", "Find Abu-Nur's {g}Night Oil{/}. His own net has it, on the {g}cliffs to the east{/}. He left it out.", "oracle", true);
                yield return Say("Ummi", "And on the {g}terraces to the west{/}, an old shrine keeps a lamp for anyone who looks twice.", "oracle", true);
            }
            else yield return Say("Ummi", "East for the oil. West for the lamp. Up for the god.| Down for snacks. I'm hungry in here.", "oracle", true);
        }

        // ------------------------------------------------------------------ the cliffs
        IEnumerator TalkAbuNur()
        {
            if (Has("item_oil"))
            {
                yield return Say("Abu-Nur", "You got it back! Keep it, keep it. A sip before a nap and your dreams go twice as far.", "fisher", true);
                yield return Say("Abu-Nur", "Don't tell my wife it's mostly fish.", "fisher", true);
                yield break;
            }
            yield return Say("Abu-Nur", "My net! My own net took my {g}Night Oil{/}! A whole jar! It hauled it off to the cove.| I left it out one night. One! It has been fishing ever since, and it is better at it than I am.", "fisher", true);
            yield return Say("Abu-Nur", "Out there the cove is across the water. But in here, see? The moon's laid a road.", "fisher", true);
            yield return Say("Abu-Nur", "Quick, though. Dreams don't last. Yours especially. You look terrible.", "fisher", true);
        }

        // ------------------------------------------------------------------ the temple yard
        Map yardMap;

        void SetupYard(Map m)
        {
            yardMap = m;
            Prop bridge = null;
            foreach (var pr in m.props) if (pr && pr.Kind == "drawbridge") bridge = pr;
            if (Has("yard_bridge")) LowerBridge(m, bridge, false);
            else if (bridge) bridge.sr.enabled = false;
        }

        void LowerBridge(Map m, Prop bridge, bool show)
        {
            var mk = m.Marker("drawbridge");
            if (mk != null)
            {
                var a = Map.ToWorld(mk.x, mk.y + mk.h);
                var r = new Rect(a.x + 0.05f, a.y + 0.05f, mk.w / 16f - 0.1f, mk.h / 16f - 0.1f);
                foreach (var s in Solids.All) if (s.pit && s.r.Overlaps(r) && Mathf.Abs(s.r.center.x - r.center.x) < r.width / 2) s.enabled = false;
            }
            if (bridge) bridge.sr.enabled = true;
        }

        void Update()
        {
            HillUpdate();
            BarrowUpdate();
            TombUpdate();
            // the yard's old drawbridge: once Azar stands on the far side, he can kick it down
            var m = Map.Current;
            if (m && m == yardMap && !Has("yard_bridge") && !Running && Player.I && Player.I.state == Player.State.Free)
            {
                var p = Player.I.pos;
                if (p.y > -200 / 16f && !Dream.I.IsDreamAt(p)) Run(KickBridge(m));
            }
            // NPCs that say something when Azar comes near
            foreach (var n in Npc.All)
            {
                if (!n || n.notice == null || Running || !Player.I || Game.Busy || !n.Present || Player.I.state != Player.State.Free) continue;
                if (Vector2.Distance(n.pos, Player.I.pos) < 3.2f) { var f = n.notice; n.notice = null; Run(f()); }
            }
        }

        IEnumerator KickBridge(Map m)
        {
            Set("yard_bridge");
            yield return Narrate("On this side of the chasm, an old drawbridge lever, green with age.^You kick it.");
            Prop bridge = null;
            foreach (var pr in m.props) if (pr && pr.Kind == "drawbridge") bridge = pr;
            Sfx.Play("gate_open");
            PixelView.I.Shake(2, 0.6f);
            LowerBridge(m, bridge, true);
            yield return Wait(0.6f);
            yield return Narrate("The bridge drops across with a sound like a giant clearing its throat.^The way home is open.");
        }

        void RegionProp(Prop pr)
        {
            bool dream = Dream.I.IsDreamAt(pr.basePos);
            switch (pr.Kind)
            {
                case "sign":
                    if (pr.data.text == "sign_lowtown")
                        Run(Narrate("{g}LOWER ASHKEL{/}\nNorth: the Temple Gate.  East: the sea cliffs.\nWest: the olive terraces."));
                    else if (pr.data.text == "sign_yard")
                        Run(dream ? Narrate("In the dream the sign is blank, except for one small word:^{t}up.{/}")
                                  : Narrate("{g}SANCTUM OF NINHAL{/}\nPilgrims: please do not wake the god.\nSeriously. -Ebrum"));
                    break;
                case "well":
                    Run(dream ? Narrate("The well whispers: {t}Drink, and forget.{/}^You have enough to forget already.")
                              : Narrate("A well. Somewhere down there, a frog is asleep too."));
                    break;
                case "gate":
                    if (pr.data.id == "hill_gate") Run(HillGate(pr));
                    break;
                case "pot":
                    Run(Narrate(Player.I.hasSword ? "A storage jar. Your khopesh has opinions about storage jars."
                                                  : "A storage jar. You have no quarrel with it.^You have nothing to quarrel with."));
                    break;
                case "look":
                    if (pr.data.id == "shrine_altar")
                        Run(dream ? Narrate("In the dream, the altar is not empty.")
                          : FirstNight ? Narrate("The shrine of the First Watch. Nobody has left anything on the altar in years.^Behind it there is a doorway in the rock, and steps going down.")
                                  : Narrate("An old shrine. Whatever was offered here is long gone.^Or long asleep. In Ashkel, it's hard to tell."));
                    break;
            }
        }

        // ------------------------------------------------------------------ the summit
        Npc god, ebrum;

        IEnumerator SetupSummit(Map m)
        {
            var gm = m.Marker("god");
            god = Npc.Create("ninhal", Map.ToWorld(gm.x, gm.y), "god", "lie", WorldLayer.Both, Facing.Down, false);
            god.turnsToTalk = false;
            god.talk = () => One(Narrate(Has("chapter_done") ? "Ninhal sleeps. He snores like distant thunder.| He IS distant thunder." :
                                                               "Ninhal, god of the sky, asleep on his own summit. He snores like distant thunder."));
            var am = m.Marker("altar");
            ebrum = Npc.Create("ebrum", Map.ToWorld(am.x, am.y), "priest", "lie", WorldLayer.Both, Facing.Down, false);
            ebrum.turnsToTalk = false;
            ebrum.talk = () => One(Narrate(Has("item_hillkey") ? "High Priest Ebrum, asleep on the altar, one key lighter.^He has rolled over onto the dent it left."
                                                              : "High Priest Ebrum, asleep on the altar with a very satisfied look on his face."));
            if (Has("chapter2_done"))
                god.talk = () => One(Narrate("Ninhal sleeps. He asked for ten more minutes.^He has had them several times."));
            if (Has("bull_dead"))
            {
                // the bull is broken: whatever comes next in the story starts from here
                if (!Has("chapter2_done")) StartCoroutine(AfterTheBull());
                yield break;
            }
            // wait for Azar to step into the room
            while (Player.I && Player.I.pos.y < Map.ToWorld(0, 300).y) yield return null;
            while (Running) yield return null;
            Run(BullRises(m));
        }

        IEnumerator BullRises(Map m)
        {
            // the whole scene the first time; after a defeat, straight back to the fight
            bool again = Has("bull_seen");
            Set("bull_seen");
            Music.Stop();
            if (!again)
            {
                yield return CamTo(god.pos + new Vector2(0, -1.5f), 1.6f);
                yield return Narrate("The summit. Ninhal, god of the sky, asleep on his own altar steps, snoring like distant thunder.^Beside him, High Priest Ebrum, asleep and smiling.");
                yield return Say("Ebrum", "Quiet...| finally quiet...| don't let anyone...| wake him...", "priest");
            }
            Sfx.Play("bull_roar");
            PixelView.I.Shake(3, 1.0f);
            var bm = m.Marker("boss");
            var bull = BrazenBull.Spawn(Map.ToWorld(bm.x, bm.y));
            if (!again)
            {
                yield return CamTo(bull.pos + new Vector2(0, 1f), 0.8f);
                yield return Wait(0.6f);
                yield return Narrate("Bronze groans. Something in the priest's dream has been sitting on his chest for forty nights.^Now it stands up.");
                yield return CamBack(0.7f);
            }
            else yield return Wait(0.9f);
            Music.Play("boss");
            bull.Defeated = () => Run(Ending());
            bull.Begin();
        }

        public IEnumerator Ending()
        {
            Set("bull_dead");
            Music.Play("ending");
            var p = Player.I;
            yield return Wait(0.6f);
            Dream.I.Drowsiness = 1;
            Dream.I.Seconds = 9999;
            Dream.I.Flip(p.pos, true);
            yield return Wait(1.2f);
            var self = Npc.Create("ebrum_self", ebrum.pos + new Vector2(1.2f, 0), "priest", "idle", WorldLayer.Dream, Facing.Down, false);
            yield return Say("Ebrum", "You broke it. My lovely bull. My lovely, heavy guilt.", "priest", true);
            yield return Say("Ebrum", "I sang him a lullaby. Just one. Forty years of prayers at dawn, at noon, at dusk, at midnight.| Forty years!", "priest", true);
            yield return Say("Ebrum", "I wanted one quiet night. He liked the song. He said, {g}five more minutes{/}.", "priest", true);
            yield return Say("Ebrum", "That was forty nights ago.", "priest", true);
            yield return AzarSays("So wake him.");
            yield return Say("Ebrum", "Me?| I've never been so rested in my life.", "priest", true);
            yield return CamTo(god.pos + new Vector2(0, -1.0f), 1.2f);
            PixelView.I.Shake(2, 1.2f);
            Sfx.Play("god_rumble");
            yield return Wait(0.8f);
            yield return Say("Ninhal", "...five...| more...| minutes...", "god", true);
            yield return CamBack(1.0f);
            yield return Wait(0.4f);
            yield return AzarSays("Forty nights.| Maybe...| just five minutes.");
            p.SetState(Player.State.Cutscene, "doze");
            yield return Wait(1.6f);
            yield return Fade.Out(1.2f);
            yield return Wait(1.4f);
            Fade.Set(0);
            p.SetState(Player.State.Cutscene, "wake");
            Sfx.Play("dream_out");
            yield return AzarSays("Nope.");
            Dream.I.SetInstant(false);
            // up the stairs behind him, unhurried: of course
            var goatEnd = Npc.Create("goat_end", Map.ToWorld(240, 372), "goat", "walk", WorldLayer.Both, Facing.Up, false);
            goatEnd.turnsToTalk = false;
            var lo = Map.ToWorld(72, 330); var hi = Map.ToWorld(408, 110);
            var goatTo = p.pos + new Vector2(p.pos.x + 2.4f > hi.x ? -2.4f : 2.4f, -1.4f);
            goatTo = new Vector2(Mathf.Clamp(goatTo.x, lo.x, hi.x), Mathf.Clamp(goatTo.y, lo.y, hi.y));
            while (Vector2.Distance(goatEnd.pos, goatTo) > 0.08f)
            {
                var step = Vector2.MoveTowards(goatEnd.pos, goatTo, 1.6f * Time.deltaTime) - goatEnd.pos;
                goatEnd.pos += step;
                goatEnd.facing = Mathf.Abs(step.x) > Mathf.Abs(step.y) ? (step.x < 0 ? Facing.Left : Facing.Right) : Facing.Up;
                goatEnd.Play("walk");
                yield return null;
            }
            goatEnd.FaceTowards(p.pos);
            goatEnd.SetIdle("stare");
            p.Face(goatEnd.pos.x > p.pos.x ? Facing.Right : Facing.Left);
            yield return Wait(0.9f);
            goatEnd.Play("bleat", true);
            Sfx.Play("goat");
            yield return Wait(1.0f);
            goatEnd.SetIdle("stare");
            yield return AzarSays("...Four hundred steps.| To tell me that.");
            yield return Wait(0.6f);
            yield return AzarSays("Fair.");
            ApplyItems();
            Set("chapter_done");
            Save.Write(Game.I.CurrentMap, null);
            yield return Fade.Out(1.0f);
            Music.Play("ending");
            yield return Card("END OF CHAPTER ONE",
                "Ninhal still sleeps.\nBut now somebody knows why.");
            // and straight on: knowing why is not the same as waking him
            yield return ChapterTwoOpens(self, goatEnd);
        }
    }
}
