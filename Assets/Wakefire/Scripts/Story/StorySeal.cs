// What the story has to say about the Seal and what it prints.
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        public void SealSeen() =>
            Once("seal_seen", "A cylinder seal: lapis, capped in gold, cut with a row of spearmen. The temple seals every door it owns with one.^That one is the length of a finger. This one is the size of a barrel, and nobody is rolling it.| "
                              + "Where it has been, the ground has spearmen in it.");

        public void PrintPeels() =>
            Once("print_peels", "The print gets up.^He is a spearman as deep as a thumbnail. From the side he is a man with a spear. From the front he is a line.| "
                                + "A line cannot be hit. A line cannot hit you either: to use that spear he will have to turn.");

        public void PrintBroken() =>
            Once("print_broken", "One blow, and he is a handful of dry clay.^Behind you, the Seal goes on rolling. It has the pattern. It can make as many as it likes.");

        public void SealStruck() =>
            Once("seal_struck", "Struck from the front, it goes back the way it came, a good deal faster.^Everything it printed on the way out, it takes back on the way home.| It will not stop until something stops it.");

        public void SealCracked(int cracks) =>
            Once(cracks == 1 ? "seal_cracked" : "seal_cracked2", cracks == 1
                ? "The end of its beat stopped it.^Lapis does not like stopping: there is a crack right round it."
                : "A second crack.^It is rolling slower, and it is not printing straight. The last spearman had two spears.");

        public void SealSplit() =>
            Once("seal_split", "It is in two halves.^Every spearman it ever pressed has just stopped being one.| Inside, where the cord went through: four hundred years of dust, and the cord.");
    }
}
