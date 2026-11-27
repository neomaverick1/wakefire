// Who is inside the houses of the gate square, asleep where the god's yawn caught them, and what each
// of them has to say for themselves in the dream: the day watch, their one prisoner, Ilu-Bani and his
// household, the master of the tablet house and three of his boys, the lamp seller.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        /// <summary>The people of the gate square's houses. True if `who` is one of them.</summary>
        bool SpawnGate(string who, Vector2 at)
        {
            switch (who)
            {
                // ------------------------------------------------------------ the watch house
                case "watch_a":
                    Pair("watch_a", at, "sleeper_b", "lean", "idle", "man",
                        () => One(Narrate("Watchman Kuri of the day watch, asleep face down on the game of twenty squares.^He was one throw from winning. The knuckle-bones are still in his fist.")),
                        () => Twice("watch_a", "Kuri", "man",
                            "Don't touch the board!| One throw. I need a four. Forty nights I have needed a four.^In here I throw it every time. In here it doesn't count.",
                            "Azar? You're awake?| ...Of course you are. You sleep on watch, so when the whole city sleeps, you're up. That is you all over."));
                    return true;
                case "watch_b":
                    Pair("watch_b", at, "sleeper_a", "sleep", "idle", "man",
                        () => One(Narrate("Watchman Hadad, asleep at attention beside the spear rack.^The only man in the watch who has ever slept the way the captain says it can't be done.")),
                        () => Twice("watch_b", "Hadad", "man",
                            "Stand easy? I have never stood easy in my life.| I'm on duty in here as well. Somebody has to guard the dream.^Nobody asked me to. That's how you know it's needed.",
                            "If you see the captain, tell him the day watch held the watch house.| Leave out the part where we were asleep. He'll have enough on his mind."));
                    return true;
                case "watch_c":
                    Abed("watch_c", at, "sleeper_c", "idle", "man",
                        () => One(Narrate("A watchman in his bunk, off duty, asleep the honest way.^Of everybody in Ashkel, he is the one man the god's sleep made no difference to at all.")),
                        () => Twice("watch_c", "Watchman", "man",
                            "I was already asleep! I was off! I did everything right!| Does this count as my rest day or doesn't it? I want it in the book.",
                            "Forty nights' sleep, and I'm still tired.| I think it's the worry."), 0.4f);
                    return true;
                case "prisoner":
                    Pair("prisoner", at, "fisher", "lie", "idle", "fisher",
                        () => One(Narrate("The watch's one prisoner, asleep on the floor of his cell with an arm down a hole.^The hole is new. The spoon beside him is worn to a stub.")),
                        () => Twice("prisoner", "Prisoner", "fisher",
                            "A year. A YEAR with a spoon, and I came up in a cellar full of cedar and silver.^I thought: I'll just rest my eyes before I carry it out.| ...How long ago was that?",
                            "Go through, if you like. Mind your head, I am not a big man.| And if anybody asks, the hole was there when I moved in."));
                    return true;
                // ------------------------------------------------------------ Ilu-Bani's
                case "ilubani":
                    Pair("ilubani", at, "priest", "sleep", "idle", "merchant",
                        () => One(Narrate("Ilu-Bani, cedar merchant to the Temple, asleep on his feet with one hand flat on his strongbox.^Forty nights, and the hand has not moved. Thieves have retired with worse grips.")),
                        () => Twice("ilubani", "Ilu-Bani", "merchant",
                            "You came in through my CELLAR?| ...Is the front door still barred? Good.^Then nothing has been stolen, because nothing has left by the door. That is how I do my accounts.",
                            "The box? In here I open it every hour, to look. It is always full.| Out there I have never dared open it once. A man can't be robbed of what he hasn't counted."));
                    return true;
                case "servant":
                    Pair("servant", at, "potter", "sleep", "idle", "man",
                        () => One(Narrate("A servant, asleep on his feet beside the tray, waiting to be told he may go.^Nobody has told him. He is very well trained.")),
                        () => Twice("servant", "Servant", "man",
                            "Is the master asleep? Truly asleep?| Then for forty nights I have been standing up for NOBODY.",
                            "...I'll stay as I am. It would be just like him to wake the moment I sat down."));
                    return true;
                case "hound":
                    Pair("hound", at, "dog", "sleep", "idle", "dog",
                        () => One(Narrate("A hound, asleep beside the pool with its feet going.^It was bought to guard the house. It is guarding the pool. Nothing has happened to the pool.")),
                        () => One(Say("Hound", "I heard you in the cellar. I heard you on the stair. I heard you lift the bar.| I was asleep. It is not my fault. I want that understood.", "dog", true)), Facing.Left);
                    return true;
                case "wife":
                    Abed("wife", at, "oracle", "idle", "oracle",
                        () => One(Narrate("Ilu-Bani's wife, asleep in a bed the size of a fishing boat.^His side has not been slept in. From the look of the pillow, it was not being slept in before, either.")),
                        () => Twice("wife", "Lady Belit", "oracle",
                            "If you have come about the bill for the cedar, he is downstairs with his hand on it.| If you have come to rob us, the good things are up here. He has never once looked.",
                            "Forty nights of quiet. No hammering, no haggling, no Temple.| When you wake the god, watchman, do me one kindness. Don't run."), 0.42f);
                    return true;
                case "child_a":
                    Abed("child_a", at, "captain_child", "idle", "child",
                        () => One(Narrate("A boy, asleep with a wooden sword under the blanket, in case.")),
                        () => One(Say("Merchant's Son", "Are you the night watch? The real one?| I'm going to be the night watch. Father says I'm going to be cedar.| I don't even know how you BE cedar.", "child", true)), 0.42f);
                    return true;
                case "child_b":
                    Abed("child_b", at, "captain_child", "idle", "child",
                        () => One(Narrate("A girl, asleep with ink on her fingers and a tablet under her pillow.^She is not allowed in the tablet house. The tablet has more on it than any of theirs.")),
                        () => One(Say("Merchant's Daughter", "I'm not asleep. I'm reading.| It's everything father sold the Temple, and what he told them it cost. They are different lists.| I'm keeping it for when I'm older.", "child", true)), 0.42f);
                    return true;
                // ------------------------------------------------------------ the tablet house
                case "master":
                    Pair("master", at, "priest", "sleep", "idle", "man",
                        () => One(Narrate("The master of the tablet house, asleep on his feet with the stick raised.^It has been about to come down for forty nights. The boy under it has had time to think about what he did.")),
                        () => Twice("master", "The Master", "man",
                            "Sit up straight! Stylus in the right hand!| ...Oh. It's you. Azar. Slept through his letters and half his numbers.^And now the only man in Ashkel awake. I shall have to think again about everything I ever told a boy.",
                            "Next door? Confiscations. No boy has ever seen inside.| No, I do not keep a jug in there. Who told you about the jug?"));
                    return true;
                case "boy_a":
                    Pair("boy_a", at, "captain_child", "cower", "idle", "child",
                        () => One(Narrate("A boy, asleep where the stick was going to find him, with his hands over his head.^He has been about to be hit for forty nights. Nobody in the tablet house has ever got away with anything for so long.")),
                        () => One(Say("Schoolboy", "It wasn't me! It was the frog! It got out by itself!| ...Is he still holding the stick up? His arm must be KILLING him.| Good.", "child", true)));
                    return true;
                case "boy_b":
                    Abed("boy_b", at, "captain_child", "idle", "child",
                        () => One(Narrate("A boy, asleep along the bench with his tablet for a pillow.^He was doing that before the god lay down. It is the one thing he has ever been ahead of the class in.")),
                        () => One(Say("Schoolboy", "Is it morning? Don't tell me if it's morning.| In here there isn't a tablet house. I looked. There's a sort of gap where it ought to be.", "child", true)), 0.28f);
                    return true;
                case "boy_c":
                    Pair("boy_c", at, "captain_child", "sleep", "idle", "child",
                        () => One(Narrate("A boy, asleep on his feet in the corner with his face to the wall.^He was sent there forty nights ago and told not to move until the master said. He is the best-behaved boy in Ashkel, and nobody is awake to see it.")),
                        () => One(Say("Schoolboy", "I can't turn round. I haven't been told.| Could you ask him? ...No. Don't. If he has forgotten me, I am safer where I am.", "child", true)), Facing.Up);
                    return true;
                // ------------------------------------------------------------ the lamp seller's
                case "lampseller":
                    Pair("lampseller", at, "potter", "lean", "idle", "merchant",
                        () => One(Narrate("The lamp seller, asleep across his counter with a taper burnt down to his fingers.^Every lamp in the shop is lit. He was showing a customer how bright it could be. The customer left with the god.")),
                        () => Twice("lampseller", "Lamp Seller", "merchant",
                            "Mind the moths! In here they come as big as cats.| Every flame in Ashkel went out that night, bar mine and the watch fire.^Do you know what forty nights of that costs in oil? I do. I dream the sum.",
                            "The cellar is dark and it stays dark. One spark down there and the Temple gets all its light at once.| ...You are carrying a flame. Of course you are. Walk like a cat."));
                    return true;
                // ------------------------------------------------------------ on Widow Ilta's roof
                case "cat_roof":
                {
                    var cat = Npc.Create("cat_roof", at, "cat", "sleep", WorldLayer.Waking, Facing.Right, false);
                    cat.turnsToTalk = false; cat.voice = "dog"; cat.lift = 0.3f; cat.orderBias = 44;
                    cat.talk = () => One(Narrate("The widow's cat, asleep on the widow's bed, on the widow's roof.^It has had the only bed in the house to itself for forty nights. It does not look like a cat that wants the god woken."));
                    var self = Npc.Create("cat_roof_self", at + new Vector2(1.2f, -0.2f), "cat", "idle", WorldLayer.Dream, Facing.Left, false);
                    self.voice = "dog";
                    self.talk = () => One(Say("Cat", "She walks all night and I sleep all night. It is the best arrangement we have ever had.| Whatever you are about to do to this town, think of the cat.", "dog", true));
                    return true;
                }
            }
            return false;
        }
    }
}
