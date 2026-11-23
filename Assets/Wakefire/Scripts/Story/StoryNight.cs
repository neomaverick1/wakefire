// The first night: the part of the story before the story. The god lies down, his sleep takes the
// city, and the night watchman, who was already asleep at his post, wakes up into the quietest
// town in the world with no blade and no light. He finds both under the old shrine of the First
// Watch, and with the Wakefire the one thing nobody else in Ashkel can do: go to sleep and come back.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        /// <summary>True from the start of a new journey until the Wakefire has been carried back to the gate.</summary>
        public static bool FirstNight => Has("prequel") && !Has("prequel_done");

        public IEnumerator Prologue()
        {
            var p = Player.I;
            Fade.Set(1);
            Music.Play("title");
            ApplyItems();
            p.Face(Facing.Down);
            p.SetState(Player.State.Cutscene, "sleep");
            yield return Card("Ashkel. An ordinary night.",
                "On top of the ziggurat, Ninhal, god of the sky,\nlay down. Only for a moment.",
                "His sleep came down the steps and through the streets,\nand everyone awake in Ashkel breathed it in.",
                "It had no use for the one man\nwho was already asleep.");
            Music.Play(Map.Current.data.music);
            Notices.Chapter("Prologue", "The First Night");
            yield return Fade.In(1.4f);
            yield return Wait(1.0f);
            Sfx.Play("snore_small", 0.8f, 0);
            yield return Wait(1.3f);
            p.SetState(Player.State.Cutscene, "wake");
            yield return Wait(0.9f);
            p.SetState(Player.State.Talk, "idle");
            yield return AzarSays("...I was not asleep.| I was resting my eyes.");
            yield return Narrate("It is very quiet.^Captain Dur is standing by the gate with his mouth open, the way he stands when he is about to shout.| He does not shout.");
            yield return AzarSays("Captain?| ...Captain.");
            yield return Narrate("You shake him. You try the rattle. You try the bucket.^Nothing in Ashkel wakes.");
            yield return Narrate("There is one rule of the night watch older than all the others, cut over the watch-house door where every watchman reads it and none has ever needed it:^{g}'IF THE CITY WILL NOT WAKE, GO TO THE FIRST WATCH.'{/}");
            yield return Narrate("The shrine of the First Watch is on the olive terraces: down through the lower town, and out by its west gate.");
            yield return Narrate(Lesson(TouchControls.Wanted));
        }

        static readonly string[] nightLines =
        {
            "Asleep. Not dozing: gone, between one breath and the next.^You shake a shoulder. Nothing.",
            "You say the name. You say it louder. You say it the way Captain Dur would.^Nothing.",
            "Whatever this is, it took the whole street in the same moment.",
            "Fast asleep, and smiling a little. It is hard not to take that personally.",
            "Nothing.^The rule over the watch-house door says {g}the First Watch{/}. Their shrine is on the olive terraces: through the lower town, and out by its west gate.",
        };

        /// <summary>What poking a sleeper gets him on the first night, before there is any dream to meet them in.</summary>
        public IEnumerator FirstNightTalk(Npc n)
        {
            if (n.id == "dur")
            {
                yield return Narrate("Captain Dur of the Temple Gate, asleep on his feet, one hand on the gate key.^He was halfway through a word. It was probably 'Azar'.");
                yield return Say("Captain Dur", "Hnnh...| asleep on watch...| ...again...", "dur");
                yield return AzarSays("One of us is, sir.");
                yield break;
            }
            yield return Narrate(nightLines[Bump("night_poke") % nightLines.Length]);
        }

        /// <summary>After the Wakefire is lifted out of its chest: why he is awake, what the flame is for,
        /// and the way out of the room he is shut in.</summary>
        public IEnumerator TheFlameExplained()
        {
            yield return Narrate("Cut into the stone behind it, in a careful hand:^{g}'WHEN THE GOD SLEEPS, THE CITY SLEEPS WITH HIM. HIS SLEEP TAKES EVERYONE AWAKE TO BREATHE IT, AND IT KEEPS THEM.'{/}^{g}'IT CANNOT KEEP THE ONE WHO CARRIES THE FLAME.'{/}");
            yield return AzarSays("So that's why I'm awake.| ...No.| I'm awake because I was asleep. On watch. When it came.");
            yield return Narrate("The god's sleep came down over Ashkel like smoke, and everyone awake breathed it in.^It had no use for a man already snoring at his post. By the time he woke, it had settled.");
            yield return Narrate("It is still there, like water in a cellar. Anyone who lies down in it now stays down.^Which is why he has not dared so much as blink slowly.");
            yield return Narrate("{g}But the flame burns sleep off like fog.{/}^Whoever carries it wakes, however deep he goes.");
            yield return AzarSays("So the one man in Ashkel who can't be kept asleep...| can go under. And come back.");
            yield return Narrate("Under is where everyone is: the whole city, in one sleep, dreaming the same streets.");
            yield return Narrate(LessonFlame(TouchControls.Wanted));
            if (FirstNight)
            {
                yield return Narrate("One more line, cut low down, where a man would only read it lying down:^{g}'WE BRICKED UP THE BACK DOOR. THE DREAM NEVER HEARD ABOUT THE BRICKS.'{/}");
                yield return AzarSays("The bars are down behind me, and the back door is bricks.| ...Good night, then.");
            }
        }

        /// <summary>He comes up out of the crypt with the flame; forty nights go by; the story begins.</summary>
        IEnumerator EndOfNight()
        {
            while (Game.Busy) yield return null;
            var p = Player.I;
            p.SetState(Player.State.Talk, "idle");
            yield return Wait(0.7f);
            yield return AzarSays("Back to my post, then.| Somebody ought to be on watch.");
            yield return Fade.Out(1.0f);
            Music.Play("title");
            yield return Card("He carried the flame back down to the gate.",
                "He lit the watch-fire. He walked his rounds.\nHe waited for somebody to wake up.",
                "Forty nights later, he was still waiting.");
            Set("prequel_done");
            if (Dream.I.Dreaming) Dream.I.SetInstant(false);
            Game.I.EnterMap("ashkel", null);
            Save.Write("ashkel", null);
            p = Player.I;
            p.Face(Facing.Down);
            p.SetState(Player.State.Talk, "idle");
            p.health.hp = p.health.max;
            Music.Play(Map.Current.data.music);
            Notices.Chapter("Chapter One", "The Sleeping God");
            yield return Fade.In(1.2f);
            yield return Wait(0.4f);
            yield return AzarSays("Night forty. Still awake. Still on watch.| Still nobody to watch.");
            Sfx.Play("goat");
            yield return Wait(0.6f);
            yield return AzarSays("...Almost nobody.");
            yield return Narrate("The god is still asleep on top of his ziggurat, and the city with him.^The temple gate is locked, and Captain Dur has the key.");
        }

        /// <summary>The crypt under the old shrine: what waits in it, and what it says when it is over.</summary>
        void SetupCrypt(Map m)
        {
            Rooms.Entered -= CryptRoom;
            Rooms.Entered += CryptRoom;
            // he is already standing in the first room by the time anything is listening
            if (Rooms.I && Rooms.I.current != null) CryptRoom(Rooms.I.current);
        }

        void CryptRoom(Room r)
        {
            if (!Game.I || Game.I.CurrentMap != "crypt") return;
            switch (r.id)
            {
                case "stair":
                    if (Bump("crypt_seen") == 0)
                        RunWhenFree(One(Narrate("The lamps down here are lit.^Nobody has come down these steps in a hundred years. They are lit anyway.")));
                    break;
                case "beds":
                    if (!Has("item_sword") && !Has("cut_crypt_roots") && Bump("beds_seen") == 0)
                        RunWhenFree(One(Narrate("Three jackals look up from what they are eating.^They look at the roots between you and them. Then, with real regret, back at you.")));
                    break;
                case "den":
                    if (!Has("dead_crypt_mother")) RunWhenFree(DenScene(Bump("den_seen") == 0));
                    break;
            }
        }

        IEnumerator DenScene(bool first)
        {
            yield return Wait(0.25f);
            if (first)
                yield return Narrate("Something in the dark is breathing.^Jackals have been denning down here longer than the watch has been forgetting to look.| This is the one the others bring it to.");
            Music.Play("boss");
        }

        /// <summary>Called by the Den Mother as she falls.</summary>
        public void DenCleared()
        {
            Music.Play(Map.Current.data.music);
            RunWhenFree(One(Narrate("The den is quiet.^Behind the bars, something is still burning that has been burning for four hundred years.")));
        }
    }
}
