// The weather, and whose fault it is. The temple keeps a man to dance the rain in at the turn of
// the season: twelve steps, a cane full of seeds, and a drum for the last of them. He was on the
// eleventh when the god lay down, and he is still on it, on one leg, on the threshing floor of
// the olive terraces, asleep. The first time the Wakefire's light goes across his eyelids he
// tips the cane, and it rains: on the terraces, on the square, on the Lower Town, on the hill of
// the dead, and on the sea, which did not need it. It rains until the dance is finished, and
// the dance wants the drum, and the drum wants its stick. Then he overdoes the twelfth step,
// and the cold comes down on a city that went to bed in summer. And after the Dawn Horn has been
// blown once in earnest, it can be blown again: the god turns over, and it is morning for as
// long as a god's ten minutes last.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        /// <summary>For the tests of other things: the weather keeps out of them.</summary>
        public static bool SkyQuiet;
        Npc dancer, dancerSelf;
        float beatAt = -99f, firstBeat = -99f;   // when the dreamer last brought the cane up; and the beat he was given on it
        float dayLeft, breath;
        const float BeatEvery = 3.4f, UpFrom = 0.20f, UpTo = 1.30f, DownFrom = 1.40f, DownTo = 2.50f;
        /// <summary>How long a god's ten minutes last, in ours.</summary>
        public const float DayLasts = 180f;

        /// <summary>People the weather brought. True if `who` is one of them.</summary>
        bool SpawnSky(string who, Vector2 at)
        {
            if (who != "rain_dancer") return false;
            // asleep on one leg, the cane upright; tipped once the rain has begun; upright again when it is done
            dancer = Npc.Create("rain_dancer", at, "priest", Has("rain_done") ? "sleep" : Has("rain_begun") ? "pour" : "onefoot", WorldLayer.Waking, Facing.Down, true, "raindancer");
            dancer.turnsToTalk = false;
            dancer.talk = () => One(LookAtDancer());
            dancerSelf = Npc.Create("rain_dancer_self", at, "priest", "dance", WorldLayer.Dream, Facing.Down, false, "raindancer");
            dancerSelf.voice = "man";
            dancerSelf.turnsToTalk = false;
            dancerSelf.talk = () => One(TalkDancer());
            return true;
        }

        void SetupSky(string map, Map m)
        {
            Sky.Ensure();
            if (map != "terraces") dancer = dancerSelf = null;
            dayLeft = Count("day_left");
            if (FirstNight || SkyQuiet) return;          // (the night it happened: nothing has crossed his eyelids yet)
            if (map == "terraces" && dancer && !Has("rain_begun")) RunWhenFree(RainBegins());
            else if (Sky.Open(map) && Sky.Raining) SeenHere("rain_seen_", map, RainLine(map));
            else if (Sky.Open(map) && Sky.Cold) SeenHere("cold_seen_", map, ColdLine(map));
        }

        void SeenHere(string key, string map, string say)
        {
            if (say != null && Bump(key + map) == 0) RunWhenFree(One(Narrate(say)));
        }

        /// <summary>The dream dancer keeps time whether anybody is listening or not; the morning runs out; breath shows in the cold.</summary>
        void SkyTick()
        {
            var p = Player.I;
            if (dancerSelf && !(Has("rain_done") && !Sky.Cold) && Time.time - beatAt >= BeatEvery)
            {
                beatAt = Time.time;
                dancerSelf.Play("beat", true);
                if (p && Dream.I && Dream.I.IsDreamAt(dancerSelf.pos) && Vector2.Distance(p.pos, dancerSelf.pos) < 9f) Sfx.Play("rain_stick", 0.3f, 0.05f);
            }
            // (the cane is up for the first of it, and comes down for the rest)
            if (dancerSelf && Time.time - beatAt > UpTo + 0.05f && dancerSelf.anim.anim == "beat") dancerSelf.Play("dance");
            if (Sky.Day && !Running && !Game.Paused)
            {
                dayLeft -= Time.deltaTime;
                if (Mathf.Abs(dayLeft - Count("day_left")) >= 1f) SetCount("day_left", Mathf.Max(0, Mathf.RoundToInt(dayLeft)));
                if (dayLeft <= 0) NightFalls();
            }
            if (p && Sky.ColdAt(p.pos) && !Running && (breath -= Time.deltaTime) <= 0)
            {
                breath = 1.9f;
                var d = p.Dir;
                for (int i = 0; i < 3; i++)
                    Fx.Spawn(p.pos + new Vector2(d.x * 0.35f, d.y * 0.1f), new Vector2(d.x * 0.5f + Random.Range(-0.1f, 0.1f), d.y * 0.2f), 1.3f, 0.15f + i * 0.1f,
                        0.55f, new Color(0.86f, 0.90f, 0.96f, 0.55f), new Color(0.86f, 0.90f, 0.96f, 0f), -0.3f, i == 0 ? 2 : 1);
            }
        }

        /// <summary>How long since the dreamer last began to bring the cane up.</summary>
        public float BeatAge => Time.time - beatAt;
        bool OnUp => Time.time - beatAt > UpFrom && Time.time - beatAt < UpTo;
        bool OnDown => Time.time - beatAt > DownFrom && Time.time - beatAt < DownTo;

        // ------------------------------------------------------------------------------ the rain begins
        IEnumerator RainBegins()
        {
            var p = Player.I;
            Set("rain_begun");
            p.SetState(Player.State.Cutscene, "idle");
            yield return Wait(0.5f);
            yield return CamTo(dancer.pos + new Vector2(0, 0.8f), 1.6f);
            yield return Narrate("On the threshing floor a man is standing on one leg, dressed as a fish.^He has been standing on it for forty nights. In his fist, upright, a cane as long as he is, full of seeds.| "
                                 + "The temple keeps him to dance the rain in at the turn of the season. Twelve steps. He was on the eleventh when the god lay down.");
            yield return Narrate("The light of the Wakefire goes across his eyelids.^He does not wake. Nobody wakes.| But a man who has waited forty nights for a drumbeat decides, in his sleep, that he has heard one.");
            dancer.SetIdle("pour");
            Sfx.Play("rain_stick", 1f, 0f);
            yield return Wait(1.7f);
            if (Sky.I) Sky.I.ease = 5f;
            Sky.Set("rain", true);
            yield return Wait(1.4f);
            Sfx.Play("thunder_far", 0.6f, 0f);
            yield return Narrate("He tips the cane, and every seed in it runs to the other end.^It sounds like rain. Then it is rain.| On the terraces. On the square. On the Lower Town. On the hill, where the dead had only just got the place dry. On the sea, which did not need it.");
            yield return CamBack(1.2f);
            yield return AzarSays("...That wasn't me.| That was a bit me.");
            if (Sky.I) Sky.I.ease = 2.5f;
            p.SetState(Player.State.Free, "idle");
            Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn);
        }

        IEnumerator LookAtDancer()
        {
            if (!Has("rain_begun"))
            {
                yield return Narrate("A man asleep on one leg in the middle of the threshing floor, dressed as a fish, with a cane as long as he is.^The temple's rain-dancer. Whatever he was in the middle of, he is still in the middle of it.");
                yield break;
            }
            if (Sky.Cold)
            {
                yield return Narrate(Bump("dancer_cold") == 0
                    ? "Asleep on both feet, the cane upright, snow settling on the fish.^He is the only man in Ashkel dressed for this, and it is by accident."
                    : "There is frost on his eyelashes and he is smiling.^It is the smile of a man who got to twelve. He has not yet been told what twelve did.");
                yield break;
            }
            if (Has("rain_done"))
            {
                yield return Narrate("The rain-dancer of the temple, asleep on both feet for the first time in forty nights, the cane upright.^He is smiling. It is the smile of a man who got to thirteen, which nobody does.");
                yield break;
            }
            int n = Bump("dancer_look");
            if (n == 0)
                yield return Narrate("Asleep, on one leg, in the rain, in a fish.^The cane is tipped over and he has it in a grip like a mooring. You try one finger. It is like trying one finger on the ziggurat.| "
                                     + "It will rain until he stands it up again. He will stand it up on the twelfth step. He is asleep on the eleventh.");
            else if (n == 1)
                yield return Narrate("The fish is the proper dress. Its head goes over his own, nose to the sky, and the rest of it down his back.^Nobody has ever asked the fish.| Nobody has ever needed to ask it what it thinks of rain.");
            else
                yield return Narrate("He has not put the other foot down.^You stand on one leg yourself for a moment, out of respect. Then you stop, because it is raining, and nobody is paying you.");
        }

        IEnumerator TalkDancer()
        {
            if (Sky.Cold)
            {
                yield return Say("Ubar", Bump("ubar_cold") == 0
                    ? "It is the clear sky. No cloud, no blanket.^There is a thirteenth step. It puts back exactly as much cloud as a city needs to sleep under.| Nobody dances the thirteenth. It wants TWO beats: one as the cane comes up, one as it comes down. Kessi could never count to two."
                    : "Up, and then down. Two.| I believe in you more than I ever believed in Kessi, which I admit is not saying a great deal.", "man", true);
                yield break;
            }
            if (Has("rain_done"))
            {
                yield return Say("Ubar", Bump("ubar_after") == 0
                    ? "Thirteen. I have danced the thirteenth. They will want it every year now.| Same time next year. ...It is always the same time, here. Come when you like."
                    : "They will say the rain was late this year.| It was forty nights late, it fell on everybody at once, and there was snow after. I call that value.", "man", true);
                yield break;
            }
            int n = Bump("ubar");
            if (n == 0)
            {
                yield return Say("Ubar", "Eleven! Eleven! Eleven!| ...Forgive me. I cannot stop on eleven. It is unlucky, and out there it is raining on me.", "man", true);
                yield return AzarSays("Then stop on twelve.");
                yield return Say("Ubar", "Twelve wants the drum. One beat, as the cane comes up.^The drum wants its stick. The stick went home with Kessi, and Kessi went home to the Seven Jars.| You see the difficulty. I have had forty nights to see it.", "man", true);
            }
            else if (!Has("item_drumstick"))
                yield return Say("Ubar", "Eleven!| I have danced this step four thousand times tonight. It is a good step. I am beginning to take against it.", "man", true);
            else
                yield return Say("Ubar", "You have the stick! ...You are holding it like a spoon.| No matter. When the cane comes UP, hit the drum. Not before. Kessi was 'before' for nine years.", "man", true);
        }

        // ------------------------------------------------------------------------------ the drum
        /// <summary>The dance drum by the threshing floor. Awake it is a drum with a puddle on it; in the dream it is the last step.</summary>
        bool SkyProp(Prop pr)
        {
            if (pr.Kind != "look" || pr.data == null || pr.data.id != "rain_drum") return false;
            Run(Drum(pr));
            return true;
        }

        IEnumerator Drum(Prop pr)
        {
            bool dream = Dream.I && Dream.I.IsDreamAt(pr.basePos);
            bool wanted = Has("rain_begun") && (!Has("rain_done") || Sky.Cold);
            if (!wanted)
            {
                Sfx.Play(Has("item_drumstick") ? "drum_big" : "drum_hand", 0.8f, 0.04f);
                yield return Narrate(Has("rain_done")
                    ? "The dance drum.^It has been hit three times this year, by a watchman, on the beat. It is not going to hear the end of it from the other drums."
                    : "The dance drum of the temple, on the edge of the threshing floor.^There is a peg on the side for the stick, and nothing on the peg.");
                yield break;
            }
            if (!Has("item_drumstick"))
            {
                Sfx.Play("drum_hand", 0.8f, 0.04f);
                yield return Narrate(dream
                    ? "You hit the drum with your hand.^It makes the noise a drum makes when it is hit with a hand. The dancer winces, and stays on eleven."
                    : "The dance drum, with a puddle on it.^There is a peg for the stick. There is no stick.| A drummer takes his stick home with him. Home, for a drummer, is wherever they are still serving.");
                yield break;
            }
            if (!dream)
            {
                Sfx.Play("drum_big", 0.9f, 0.03f);
                Noise.Make(pr.basePos, 14f);
                yield return Narrate("You hit the drum. It is a good drum.^The man on the threshing floor does not stir: he is not dancing out here. He is dancing in there.| Whatever beat he is waiting for, he is waiting for it asleep.");
                yield break;
            }
            // in the dream, with the stick: on the beat or not
            Sfx.Play("drum_big", 1f, 0.02f);
            PixelView.I.Shake(2, 0.18f);
            Fx.Dust(pr.basePos + new Vector2(0, 0.9f), 4);
            if (!Sky.Cold)
            {
                // the twelfth step: one beat, as the cane comes up
                if (OnUp) { yield return RainEnds(); yield break; }
                bool early = Time.time - beatAt > BeatEvery * 0.6f;
                yield return Say("Ubar", Bump("drum_miss") == 0
                    ? (early ? "Early!| It is all right. Kessi was early for nine years. As the cane comes UP." : "Late!| Kessi was never late. Kessi was early, or Kessi was not there. As the cane comes UP.")
                    : (early ? "Early. Eleven it is, then." : "Late. Eleven again. I know it well."), "man", true);
                yield break;
            }
            // the thirteenth: two, one as it comes up and one as it comes down
            if (OnUp) { firstBeat = beatAt; yield break; }
            if (OnDown && firstBeat == beatAt) { yield return ColdEnds(); yield break; }
            firstBeat = -99f;
            yield return Say("Ubar", Bump("drum_miss2") == 0
                ? "One beat as it comes UP. One as it comes DOWN. That is all thirteen is.| Take your time. It is the one thing in Ashkel nobody is short of."
                : "Up. Then down. ...Kessi used to hum it. Do not hum it.", "man", true);
        }

        IEnumerator RainEnds()
        {
            var p = Player.I;
            Set("rain_done");
            p.SetState(Player.State.Cutscene, "idle");
            yield return Say("Ubar", "TWELVE!", "man", true);
            if (Sky.I) Sky.I.ease = 3.5f;
            Sky.Set("rain", false);
            if (dancer) dancer.SetIdle("sleep");
            Sfx.Play("rain_stick", 0.9f, 0f);
            yield return Wait(1.8f);
            yield return Narrate("In the dream he bows.^On the threshing floor, in his sleep, he puts his other foot down and stands the cane upright, and every seed in it goes home.| The rain stops between one drop and the next.");
            p.coins += 60;
            Sfx.Play("coin_big", 0.9f, 0.02f);
            yield return Say("Ubar", "The temple pays sixty for a rain. Take it: the clerk has paid me every night for forty nights, in his sleep, and I have nowhere in this fish to keep it.", "man", true);
            // ...and then what twelve did
            yield return Wait(1.2f);
            yield return Narrate("He has danced the clouds off. All of them.^The sky over Ashkel is the clearest anyone alive has seen, and there is nothing left between the city and the cold.");
            if (Sky.I) Sky.I.ease = 6f;
            Sky.Set("cold", true);
            Sfx.Play("thunder_far2", 0.3f, 0f);
            yield return Wait(3.0f);
            yield return Narrate("It starts to snow anyway. Nobody can say out of what.^On the terraces, on the square, on the Lower Town: on a whole city that went to bed in summer, in what it was wearing.| Everyone in Ashkel is now freezing cold, and not one of them is awake to complain.");
            yield return Say("Ubar", "...Ah.| I put my back into twelve. Forty nights of run-up. You understand.", "man", true);
            if (Sky.I) Sky.I.ease = 2.5f;
            p.SetState(Player.State.Free, "idle");
            Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn);
        }

        IEnumerator ColdEnds()
        {
            var p = Player.I;
            Set("cold_done");
            p.SetState(Player.State.Cutscene, "idle");
            yield return Say("Ubar", "THIRTEEN!", "man", true);
            if (Sky.I) Sky.I.ease = 4f;
            Sky.Set("cold", false);
            if (dancerSelf) dancerSelf.Play("dance");
            yield return Wait(2.2f);
            yield return Narrate("The thirteenth step puts back exactly as much cloud as a city needs to sleep under.^The snow stops. The cold goes out of the ground like a guest who has been told the time.| A whole city stops shivering in its sleep, all at once, and not one of them will ever know.");
            p.coins += 80;
            Sfx.Play("coin_big", 0.9f, 0.02f);
            yield return Say("Ubar", "The temple has never paid for a thirteenth. Nobody has ever done one.| So I am paying you myself. Eighty. Do not tell the clerk: he will want it written down, and he is asleep.", "man", true);
            if (Sky.I) Sky.I.ease = 2.5f;
            p.SetState(Player.State.Free, "idle");
            Save.Write(Game.I.CurrentMap, Game.I.CurrentSpawn);
        }

        // ------------------------------------------------------------------------------ the stick, and who has it
        /// <summary>The regular under the table of the Seven Jars is the temple's drummer. He has the stick in one fist.</summary>
        IEnumerator LookAtDrummer()
        {
            if (!Has("rain_begun") || Has("item_drumstick"))
            {
                yield return Narrate(Has("item_drumstick")
                    ? "Kessi, the temple's drummer, under the table.^The fist that had the stick in it has closed on the leg of the table instead. He seems as happy with it."
                    : "A man asleep under the table.^He got there by the usual road, some time before the god did.");
                yield break;
            }
            yield return Narrate("A man asleep under the table, with a cup in one fist and a drumstick in the other.^This is Kessi, who drums for the temple, when the temple can find him.");
            Set("item_drumstick");
            yield return ItemGet("drumstick", "{g}Kessi's drumstick!{/}^He lets go of it the way a man lets go of work.| You do not try for the cup.");
        }

        // ------------------------------------------------------------------------------ what the weather does, place by place
        static string RainLine(string map) => map switch
        {
            "ashkel" => "It is raining on the Temple Gate square.^It runs off Captain Dur's helmet in a steady line, on to his boots. He has slept through worse. He has slept through you.",
            "lowtown" => "Rain on the Lower Town.^Every awning in the market has a bellyful of it. Nobody is awake to poke them with a stick, which is the best job in the market.| There is no moon to throw a shadow by. Whatever stays up after its owner in these streets has had to go home.",
            "cliffs" => "It is raining on the sea.^The sea has not noticed. The nets on the beach have: wet, they are in a better mood, and that is not good news.",
            "temple_yard" => "Rain in the temple yard.^Whatever the Seal presses in this, it presses in soup. Its spearmen lie there a moment and go back to being mud.",
            "necro_road" => "It is raining on the Road of the Dead.^The dead do not get wet. They have noticed that it is raining, though, and would like it known that they had only just got the place dry.",
            "necropolis" => "Rain on the Hill of Sleepers.^It goes straight through the residents. Several of them have put a hand out anyway, to see.",
            "zig_3" => "It rains on the summit too.^It is raining on the god. He has pulled a cloud up to his chin.",
            _ => null,
        };

        static string ColdLine(string map) => map switch
        {
            "ashkel" => "Snow on the Temple Gate square.^Captain Dur has a small hat of it on top of his helmet. He is asleep at attention and blue to the knuckles.| It is the quietest cold snap in the city's history. Nobody is awake to say so.",
            "lowtown" => "Snow in the Lower Town.^The fishmonger's slab has frozen with the fish on it, which is the best thing to happen to those fish in forty nights.",
            "cliffs" => "The spray has frozen on the cliffs.^The nets on the beach are as stiff as boards. A Dragnet in this stands where it was hung, and cannot so much as flap.",
            "temple_yard" => "The temple yard is white.^The Seal goes on rolling, and prints nothing: the ground is too hard to take it. It has not noticed. It is very thorough.",
            "necro_road" => "Snow on the Road of the Dead.^The dead do not feel the cold. They would like it known that they are not gloating.",
            "necropolis" => "Snow on the Hill of Sleepers.^It lies on the tombs and goes through the residents. One of them is trying to make a snowball, and has been for some time.",
            "zig_3" => "It is snowing on the god.^He has pulled the cloud up over his head.",
            _ => null,
        };

        /// <summary>A fire bowl under open sky will not take while it is raining on it.</summary>
        public bool RainOnBowl(Prop bowl)
        {
            if (bowl == null || !Sky.WetAt(bowl.basePos)) return false;
            Sfx.Play("fizzle", 0.8f, 0.06f);
            for (int i = 0; i < 8; i++)
                Fx.Spawn(bowl.basePos + new Vector2(Random.Range(-0.2f, 0.2f), 0), new Vector2(Random.Range(-0.3f, 0.3f), 0.1f), 1.0f, Random.Range(0.5f, 1.4f),
                    Random.Range(0.5f, 0.9f), new Color(0.72f, 0.72f, 0.76f, 0.9f), new Color(0.30f, 0.30f, 0.34f, 0f), -0.7f, i % 3 == 0 ? 2 : 1);
            if (Bump("rain_bowl") == 0)
                RunWhenFree(One(Narrate("The bowl catches. The rain puts it out.^You light it again, for the look of the thing. The rain puts it out again.| Nothing under this sky is going to stay lit until somebody does something about the sky.")));
            return true;
        }

        public void PrintSlumps() =>
            Once("print_slumps", "The Seal has pressed a spearman into the wet.^He lies there, runs at the edges, and is mud again before he can think of getting up.| In the rain the Seal is only a barrel that will not stop.");

        public void DebtRuns() =>
            Once("debt_runs", "In the rain the tablet has run.^The sum on it is now a matter of opinion. The Debt's opinion is the old figure. Yours is half.| It looks at the tablet for some time, and takes yours.");

        // ------------------------------------------------------------------------------ morning, for ten of a god's minutes
        /// <summary>Things that only walk at night: under the sun they are a lamp snuffer, a wick, a net, a shadow, and a watchman on a bench.</summary>
        public static bool NightOnly(Enemy e) => e is Snuffer || e is StayUp || e is Yawn || e is Wick || e is Dragnet || e is SleepWatch;
        public static bool NightOnly(string who) => who == "snuffer" || who == "stayup" || who == "yawn" || who == "wick" || who == "dragnet" || who == "watch";

        public IEnumerator BlowHorn()
        {
            var p = Player.I;
            if (!Has("chapter2_done"))
            {
                yield return Narrate("The Dawn Horn.^It is not a horn for the street. It wants the top of the ziggurat, and one god's ear.");
                yield break;
            }
            if (!Sky.Outdoors)
            {
                yield return Narrate("Not under a roof.^The sun would only have to come in and look for you.");
                yield break;
            }
            if (Sky.Day)
            {
                yield return Narrate("It is already morning.^Blowing it again would be nagging, and he is a god.");
                yield break;
            }
            p.Face(Facing.Down);
            p.SetState(Player.State.ItemGet, "itemget");
            Sfx.Play("horn", 1f, 0f);
            yield return Wait(1.6f);
            if (Sky.I) Sky.I.ease = 4f;
            Sky.Set("day", true);
            dayLeft = DayLasts; SetCount("day_left", (int)DayLasts);
            foreach (var e in Enemy.All.ToArray())
                if (e && NightOnly(e)) { Fx.Dust(e.pos, 6); Destroy(e.gameObject); }
            yield return Wait(1.0f);
            yield return Narrate(Bump("horn_blown") == 0
                ? "Up on the ziggurat a god turns over, opens one eye, and says what he said last time.^{g}Ten more minutes.{/}| It is morning in Ashkel. A god's ten minutes are about three of yours.^Nothing that walks the night will walk in this. Be quick."
                : "{g}Ten more minutes.{/}^Morning, again. He is getting used to you. That may not be a good thing.");
            if (Sky.I) Sky.I.ease = 2.5f;
            p.SetState(Player.State.Free, "idle");
        }

        void NightFalls()
        {
            if (Sky.I) Sky.I.ease = 5f;
            Sky.Set("day", false);
            dayLeft = 0; SetCount("day_left", 0);
            RunWhenFree(One(Narrate(Bump("night_fell") == 0
                ? "The ten minutes are up.^The night comes back down over Ashkel like a blanket pulled up to the chin.| Somewhere a Snuffer picks up where it left off."
                : "The ten minutes are up.^Night, again.")));
        }
    }
}
