// What the story has to say about the Sleeping Watch and the Debt, and the two things they leave
// behind them: a Snuffer in the lock-up, and a debt lying down where it was paid.
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        // --------------------------------------------------------------------- the Sleeping Watch
        public void StruckASleeper()
        {
            int n = Bump("struck_sleeper");
            if (DreamsQuiet || Running) return;
            if (n == 0)
                RunWhenFree(One(Narrate("You do not hit a man who is asleep.^It is the first rule of the watch. He taught it to you himself.| He was awake at the time.")));
            else if (n % 4 == 2)
                RunWhenFree(One(Say("Watchman", "...mmf...| ...five more minutes, Captain...", "man")));
        }

        partial void SetupLate(string map, Map m)
        {
            if (map == "ashkel_in" && Has("nicked_snuffer"))
            {
                var mk = m.Marker("spot", "nicked");
                if (mk != null)
                {
                    var n = Npc.Create("nicked", Map.ToWorld(mk.x, mk.y), "moth", "cover", WorldLayer.Waking, Facing.Down, true, "snuffer");
                    n.turnsToTalk = false;
                    n.snore = null;
                    n.talk = () => One(Narrate(Bump("nicked_look") == 0
                        ? "A Snuffer, in the lock-up.^It was run in for being abroad after dark without a light. It was dark because of it. The watch does not see the difficulty.| "
                          + "It has sat down over the prisoner's lamp. The prisoner says it snores."
                        : "The Snuffer has not moved.^Neither has the charge sheet. Somebody will have to wake up and write one."));
                }
            }
            if (map == "necro_road" && Has("debt_paid")) PaidPile(new Vector2(Count("debt_x") / 16f, Count("debt_y") / 16f));
        }

        // ------------------------------------------------------------------------------ the Debt
        void PaidPile(Vector2 at)
        {
            var n = Npc.Create("debt_pile", at, "priest", "lie", WorldLayer.Waking, Facing.Down, false, "debt");
            n.turnsToTalk = false;
            n.snore = null;
            n.orderBias = -20;
            n.talk = () => One(Narrate(Bump("debt_pile") == 0
                ? "A debt, paid.^In Ashkel these are kept in the temple, with the other miracles.| The top tablet says {g}PAID IN FULL{/}. Somebody has pressed a thumb into it, to be sure."
                : "It is lying down.^It is the first rest it has had in three hundred years, and it has earned it. At eleven parts in the hundred."));
        }

        public void DebtLiesDown() => PaidPile(new Vector2(Count("debt_x") / 16f, Count("debt_y") / 16f));

        public void DebtBilled() =>
            Once("debt_billed", "It is holding something out to you.^It is the sum.| It will wait while you read it. It will not wait long, and waiting is charged for.");

        public void DebtRestacked(int level)
        {
            if (level == 2)
                Once("debt_restacked", "The pieces find each other.^It is a tablet taller than it was. So is the sum.| Breaking it has been entered as a late payment.");
            else if (level == Debt.Last)
                Once("debt_last", "It is taller than the tombs now, and thinner.^It cannot have much clay left to write on.");
        }

        public void DebtOutOfClay() =>
            Once("debt_gone", "The last tablet breaks, and that is the end of the paperwork.^In Ashkel a debt with no tablet is called a rumour.| "
                              + "Nobody has ever managed it before. Nobody else had a khopesh and this much of the night to spare.");

        public void DebtWeighed() =>
            Once("debt_weighed", "The plate goes down under it like a step under a fat man.^Three hundred years of interest. The vault knows what that weighs.");

        /// <summary>Paid, or out of clay: either way there is nothing owed any more, and the assessor's vault,
        /// which opens to what is owed when it comes to be weighed, opens to the news that nothing is.</summary>
        public void DebtSettled(bool paid)
        {
            var map = Map.Current;
            var plate = map ? map.Find("nr_weigh") : null;
            if (plate && !plate.lit) map.Press(plate);
            else Set("on_nr_weigh");
        }
    }
}
