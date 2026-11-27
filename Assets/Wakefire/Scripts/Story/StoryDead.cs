// Who is at home in the houses of the dead, on the road and on the hill. Up here it is the dead who cannot
// sleep: in the waking world somebody is in, in the dream there is nobody anywhere, and once the dawn has
// come and gone they are all in bed at last.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    /// <summary>The light one of the dead carries indoors: there when they are, and gone with them in the dream.</summary>
    public class GhostGlow : MonoBehaviour
    {
        Npc who; LightBlob glow; float full;
        public void Bind(Npc n, LightBlob g) { who = n; glow = g; full = g.intensity; }
        void Update() { if (who && glow) glow.intensity = who.Present ? full : 0f; }
    }

    public partial class Story
    {
        IEnumerator Thrice(string key, string name, string voice, string first, string then, string after)
        {
            int n = Bump(key);
            yield return Say(name, n == 0 ? first : n == 1 ? then : after, voice, true);
        }

        /// <summary>One of the dead in a room of their own: by the lamps the dead keep they would be hard to see, so each
        /// carries a little of their own cold light. whole: all of them is there, down to the feet (somebody lying
        /// down, or sitting, or standing on something, with no ground to fade into).</summary>
        Npc AtHome(Npc n, bool whole = false)
        {
            var glow = LightBlob.Create(n.transform, n.pos + new Vector2(0, 0.7f + n.lift), 1.7f, new Color(0.55f, 0.95f, 0.9f), 0.5f, false);
            n.gameObject.AddComponent<GhostGlow>().Bind(n, glow);
            if (whole) n.anim.sr.material.SetVector("_GhostFade", new Vector4(-1f, -0.5f, 0, 0));
            return n;
        }

        /// <summary>The dead at home. True if `who` is one of them.</summary>
        bool SpawnTombs(string who, Vector2 at)
        {
            if (!who.StartsWith("t_")) return SpawnDreams(who, at);
            if (Has("chapter2_done")) return true;                  // asleep, every one of them
            switch (who)
            {
                // ------------------------------------------------------------ the road of the dead
                case "t_sweeper":
                {
                    var n = Dead(who, at, "t_sweeper", "scrub", "ghost_f", () => Thrice("t_sweeper", "Amat", "ghost_f",
                        "Wipe your feet.| Not on that. That is the mat for looking at.",
                        "Forty nights awake, and I have got on top of the dust at last.^Do you know where it comes from? I do, now.| It comes from us.",
                        "If you see a goat, tell it that I know.| It will understand."), Facing.Left);
                    n.turnsToTalk = false;
                    AtHome(n);
                    return true;
                }
                case "t_shepherd":
                {
                    var n = Dead(who, at, "t_shepherd", "lie", "ghost", () => Thrice("t_shepherd", "Shepherd", "ghost",
                        "...nine thousand and six. Nine thousand and seven. Nine thou...^No. Don't speak. I had it.| ...One.",
                        "It works on the living. I have watched it work. I had a boy who was gone by the fourth ewe.^It is knowing them by name that does for me. I keep stopping to see how each one is.",
                        "One. Two. Three.| Close the door quietly on your way out. Not for me. For them."), Facing.Down, false);
                    n.turnsToTalk = false; n.lift = 0.45f; n.orderBias = 44;
                    AtHome(n, true);
                    return true;
                }
                case "t_proud":
                {
                    var n = Dead(who, at, "t_proud", "wait", "ghost", () => Thrice("t_proud", "Ki-Ag", "ghost",
                        "You came in by the roof. Good.^Everybody ought to have to look down to find me, and then up.",
                        "The man next door put a moon over his door. I put a third storey on.^I have never asked him what he thinks. I do not need to.| I can see him not looking.",
                        "Take what is in the chest. I had it put there so that somebody would have to come and be grateful.| You will do."), Facing.Down, false);
                    n.turnsToTalk = false; n.lift = 0.62f; n.orderBias = 44;
                    AtHome(n, true);
                    return true;
                }
                case "t_wife":
                    AtHome(Dead(who, at, "t_wife", "wait", "ghost_f", () => Twice("t_wife", "Wife", "ghost_f",
                        "He lay on the left for fifty years. That was in life.| It is my turn.",
                        "Do not take his part. He will tell you he has no part.| That is his part."), Facing.Right));
                    return true;
                case "t_husband":
                    AtHome(Dead(who, at, "t_husband", "idle", "ghost", () => Twice("t_husband", "Husband", "ghost",
                        "She says that as though being dead were a fresh start.",
                        "We were going to have it out, the night the god lay down.^Now nobody up here can sleep, so it does not matter which side nobody sleeps on.| We have not told each other that. It would leave us with nothing to say."), Facing.Left));
                    return true;
                // ------------------------------------------------------------ the hilltop
                case "t_rich":
                {
                    var n = Dead(who, at, "t_rich", "sit", "ghost", () => Thrice("t_rich", "Puzur", "ghost",
                        "Sit, sit. You are the first to arrive.^The others are late. They have been late for two hundred years.| One makes allowances, with people of quality.",
                        "Twelve places, I had laid, in the will. The lawyer said eleven would be plenty.^Where is he now? Not here. Nobody is.| That is the point I am making.",
                        "Take something for the road. Not from the table. That is for guests.| The chest. The chest is for people who actually come."), Facing.Right, false);
                    n.turnsToTalk = false; n.orderBias = 44;
                    AtHome(n, true);
                    return true;
                }
                case "t_knocker":
                    AtHome(Dead(who, at, "t_knocker", "knock", "ghost", () => Thrice("t_knocker", "Ibbi", "ghost",
                        "You knocked back!^Three hundred years I have been knocking, and you are the first to knock back. With a gong.| Well. One cannot have everything.",
                        "I do not want to come out. It is not that.^I only like to know that there is an out, and somebody in it.",
                        "There is a hole in my floor. Men came up through it once, with sacks, and looked at me. I looked at them.^It was the nicest evening I have had.| Use it if you like. It goes next door, and she is never in."), Facing.Down));
                    return true;
                case "t_scribe":
                {
                    var n = Dead(who, at, "t_scribe", "talk", "clerk", () => Twice("t_scribe", "Adapa", "clerk",
                        "'...and in the eleventh year of the same king, the barley tax was assessed as follows.'^Shh. I am reading.| It is my own work. Sixty tablets. We are on the ninth.",
                        "We have been on the ninth for forty nights. She keeps asking me to go back and read a part again.| It is the mark of a careful listener."), Facing.Right);
                    n.turnsToTalk = false;
                    AtHome(n);
                    return true;
                }
                case "t_listener":
                {
                    var n = Dead(who, at, "t_listener", "sit", "ghost_old", () => Twice("t_listener", "His Wife's Mother", "ghost_old",
                        "I ask him to go back because the first eight were worse, and it uses up the night.| Do not tell him.",
                        "He thinks it is the writing that keeps me awake.^Everybody on this hill is awake. I have not had the heart.| It is the only good notice he has ever had."), Facing.Left, false);
                    n.turnsToTalk = false; n.orderBias = 44;
                    AtHome(n, true);
                    return true;
                }
                case "t_watchman":
                {
                    var n = Dead(who, at, "t_watchman", "knead", "ghost_old", () => Thrice("t_watchman", "Old Watchman", "ghost_old",
                        "You're the watch. I can tell by the feet.^I had your gate, three hundred years back. Never once slept on duty.| They cut it on my stone and everything.",
                        "I am owed, do you see. Three hundred years of nights.| And now that I have come to collect, the pillow has gone hard.",
                        "Fell asleep at your post, did you. The one night it mattered.^...Best thing a watchman ever did, by the sound of it.| Don't tell your captain I said so. Don't tell mine."), Facing.Up);
                    n.turnsToTalk = false;
                    AtHome(n);
                    return true;
                }
            }
            return true;
        }
    }
}
