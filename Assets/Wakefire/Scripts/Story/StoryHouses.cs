// Who is inside the houses of the Lower Town, asleep where the god's yawn caught them, and what
// each of them has to say for themselves in the dream.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        /// <summary>A sleeper and their dream-self in a bed, a heap of net, anywhere that is not the floor: drawn that
        /// much higher, over whatever they lie on, and no more in the way than the bed is.</summary>
        Npc Abed(string id, Vector2 at, string sheet, string dreamAnim, string voice, System.Func<IEnumerator> wake, System.Func<IEnumerator> dream, float lift, Facing f = Facing.Down)
        {
            var body = Npc.Create(id, at, sheet, "lie", WorldLayer.Waking, f, false);
            body.turnsToTalk = false; body.voice = voice; body.talk = wake; body.lift = lift; body.orderBias = 44;
            var self = Npc.Create(id + "_self", at + new Vector2(0.9f, -0.6f), sheet, dreamAnim, WorldLayer.Dream, Facing.Down, false);
            self.voice = voice; self.talk = dream;
            return self;
        }

        IEnumerator Twice(string key, string name, string voice, string first, string then)
        {
            yield return Say(name, Bump(key) == 0 ? first : then, voice, true);
        }

        /// <summary>The people of the houses. True if `who` is one of them.</summary>
        bool SpawnHouse(string who, Vector2 at)
        {
            switch (who)
            {
                case "urbau":
                    Pair("urbau", at, "sleeper_a", "sleep", "idle", "man",
                        () => One(Narrate("Urbau, Hesha's husband, asleep on his feet behind the counter with a coin in each hand.^He was counting the day's takings. He had got as far as four.")),
                        () => Twice("urbau", "Urbau", "man",
                            "Four! No. Wait.| I had the whole day counted, and then the god yawned.^In here I have counted to a hundred thousand. Out there I am still on four, aren't I.",
                            "If you buy a loaf in here, I can't give you change out there.| I am working on it. It is a problem of accounting."));
                    return true;
                case "granny":
                    Abed("granny", at, "baker", "idle", "baker",
                        () => One(Narrate("Hesha's grandmother, asleep under a blanket she wove before the town had walls.^She went to bed forty nights ago and has missed nothing she had not seen before.")),
                        () => Twice("granny", "Grandmother", "baker",
                            "Don't stand in the door, boy, you'll let the night in.| Forty nights? I have slept through three kings. I was about due.",
                            "Tell my granddaughter the oven is too hot.| It has been too hot since she was nine."), 0.42f);
                    return true;
                case "cat_bed":
                {
                    var cat = Npc.Create("cat_bed", at, "cat", "sleep", WorldLayer.Waking, Facing.Left, false);
                    cat.turnsToTalk = false; cat.voice = "dog"; cat.lift = 0.4f; cat.orderBias = 44;
                    cat.talk = () => One(Narrate("A cat, asleep in the exact middle of the bed.^Nothing about this is new."));
                    var self = Npc.Create("cat_bed_self", at + new Vector2(-0.8f, -1.0f), "cat", "idle", WorldLayer.Dream, Facing.Left, false);
                    self.voice = "dog";
                    self.talk = () => Twice("cat", "Cat", "dog",
                        "I was asleep before any of this.| I am not part of your problem.",
                        "The goat and I have an arrangement. It has the roofs.| I have everything under them.");
                    return true;
                }
                case "alewife":
                    Pair("alewife", at, "baker", "lean", "idle", "baker",
                        () => One(Narrate("The alewife of the Seven Jars, asleep with her chin on the counter and one hand still on a drinking reed.^She has not spilled a drop in forty nights.")),
                        () => Twice("alewife", "Alewife", "baker",
                            "Seven jars, seven beers, and I've forgotten what is in three of them.| Nobody has complained. Nobody who drank from those three has said anything at all.",
                            "The cellar? Bolted from underneath. My husband's idea, rest him.| It keeps the sea out of the hall. It keeps me out of the cellar. He thought of everything."));
                    return true;
                case "drinker_a":
                    Pair("drinker_a", at, "sleeper_a", "lie", "idle", "man",
                        () => One(LookAtDrummer()),
                        () => One(Say("Regular", "In here I'm not under the table. In here I'm on it. Singing.| Don't tell me how it sounds.", "man", true)));
                    return true;
                case "drinker_b":
                    Pair("drinker_b", at, "oracle", "sleep", "idle", "oracle",
                        () => One(Narrate("A woman asleep bolt upright with a cup in her hand, still winning an argument.")),
                        () => Twice("drinker_b", "Regular", "oracle",
                            "And ANOTHER thing...| Oh. You're not him.^He fell asleep in the middle of being wrong. Forty nights I have waited to finish that sentence.",
                            "When he wakes up, I'm starting again from the beginning. He missed some of it."), Facing.Left);
                    return true;
                case "dog_beer":
                    Pair("dog_beer", at, "dog", "sleep", "idle", "dog",
                        () => One(Narrate("A dog by the fire, belly up.^The only regular who has never run up a slate.")),
                        () => One(Say("Dog", "The one by the well is my brother. He thinks he's a lion.| I think I'm a dog. One of us is happy.", "dog", true)), Facing.Right);
                    return true;
                case "potboy":
                    Pair("potboy", at, "captain_child", "sleep", "idle", "child",
                        () => One(Narrate("Kesh's apprentice, asleep on his feet with a jar handle in his hand.^Only the handle.")),
                        () => Twice("potboy", "Apprentice", "child",
                            "It was like that when I picked it up.| ...Is Kesh asleep? Really asleep? Then it was the goat.",
                            "He has a room back there with no door. He goes in through the roof and thinks nobody knows.| Everybody knows. The plaster is still soft in one place, if you hit it hard enough."));
                    return true;
                case "sister_a":
                    Pair("sister_a", at, "baker", "sleep", "idle", "baker",
                        () => One(Narrate("The elder sister, asleep at her loom with her back to the room.^She is half way through a red cloth. She has been half way through it for forty nights and nine years.")),
                        () => One(Say("Elder Sister", "Tell my sister her selvedge is crooked.| No. Don't tell her anything. We don't speak.", "baker", true)), Facing.Up);
                    return true;
                case "sister_b":
                    Pair("sister_b", at, "oracle", "sleep", "idle", "oracle",
                        () => One(Narrate("The younger sister, asleep at her loom with her back to the room, and to her sister, in that order of importance.")),
                        () => One(Say("Younger Sister", "Tell my sister I said nothing.| Use those words. She'll know what I mean.", "oracle", true)), Facing.Up);
                    return true;
                case "clerk":
                    Pair("clerk", at, "sleeper_b", "lean", "idle", "man",
                        () => One(Narrate("The collector's clerk, asleep face down in the tablets.^The top one has taken the print of his cheek. It is the most honest record in the building.")),
                        () => Twice("clerk", "Clerk", "man",
                            "Name? Trade? Anything to declare?| 'Asleep.' Everyone says asleep. It isn't a trade, I can't tax it, and it is killing me.",
                            "The strongroom key? The collector wears it round his neck. Wore it.| Then the goat was seen wearing it. I have filed a report."));
                    return true;
                case "client":
                    Pair("client", at, "sleeper_c", "cower", "idle", "man",
                        () => One(Narrate("A man asleep on his knees on the oracle's mat.^He came with a question forty nights ago. From his face, he has not liked the answer once in all that time.")),
                        () => One(Say("Client", "I only asked if I should buy the boat!| She said: yes, but not the way you are hoping.^I've been here ever since, working out which part to worry about.", "man", true)), Facing.Up);
                    return true;
                case "roof_drinker":
                    Pair("roof_drinker", at, "sleeper_c", "lie", "idle", "man",
                        () => One(Narrate("A man asleep on the roof of the Seven Jars, where they sit when the weather is good.^The weather has been good for forty nights. He has not wasted a minute of it.")),
                        () => One(Say("Regular", "Best seat in the house. You can see the whole town from up here, and none of it is moving.| I used to think that would be restful.", "man", true)));
                    return true;
                case "oldfisher":
                    Abed("oldfisher", at, "fisher", "idle", "fisher",
                        () => One(Narrate("An old man asleep in a heap of net, the way fishermen do.^Abu-Nur's father. The skiff on the trestles is the one he is going to finish in the morning, and has been for thirty years.")),
                        () => Twice("oldfisher", "Old Fisherman", "fisher",
                            "That skiff will be the fastest thing in the harbour.| I only need the morning. You haven't seen one about?",
                            "My boy sleeps in his boat. I sleep in my nets. His mother slept in a bed, and look where it got her.| Comfortable. It got her comfortable."), 0.3f);
                    return true;
            }
            return SpawnGate(who, at);
        }
    }
}
