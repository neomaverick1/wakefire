// Who plays the people of the Hill of Sleepers: the dead (the same bodies as the living, with a
// few habits only the patient pick up), three tomb robbers, the unremembered, the king's clay
// soldiers, the scarabs, and Kurashtar himself.
using System;
using UnityEngine;

namespace Wakefire
{
    public static partial class ModelDefs
    {
        /// <summary>What the dead do with four hundred years: wait with their arms folded, say no,
        /// sit, hold a lamp up to see who it is.</summary>
        static ModelDef Dead(float scale, Action<ModelActor> dress)
        {
            var d = Human(scale, dress);
            d.Own("wait", "Idle_FoldArms_Loop", fade: 0.2f);
            d.Own("no", "Idle_No_Loop", fade: 0.15f);
            d.Own("yes", "Yes", fade: 0.15f);
            d.Own("sit", "Sitting_Idle_Loop", fade: 0.1f);
            d.Own("sit_talk", "Sitting_Talking_Loop", fade: 0.15f);
            d.Own("lamp", "Idle_Lantern_Loop", fade: 0.2f);
            // and at home: down on their knees at a floor that is already clean, and knocking on the inside of a door
            d.Own("scrub", "Fixing_Kneeling", 1.0f, 4.2f, fade: 0.25f);
            d.Own("knock", "Interact", fade: 0.12f);
            return d;
        }

        static void Hill()
        {
            foreach (var who in new[] { "namtar", "gran", "belu", "poet", "herald", "servant", "robber", "robber_b" })
                Add(who, Dead(1.33f, Cast.Person(who)));
            // townsfolk of other centuries, standing in the queue
            Add("dead_baker", Dead(1.33f, Cast.Person("baker")));
            Add("dead_fisher", Dead(1.33f, Cast.Person("fisher")));
            Add("dead_potter", Dead(1.33f, Cast.Person("potter")));
            Add("dead_sleeper", Dead(1.33f, Cast.Person("sleeper_b")));
            // the dead at home, in the houses of the road and the hill
            foreach (var who in new[] { "t_sweeper", "t_shepherd", "t_proud", "t_wife", "t_husband", "t_rich", "t_knocker", "t_scribe", "t_listener", "t_watchman" })
                Add(who, Dead(1.33f, Cast.Person(who)));
            Add("general_a", Dead(1.40f, Cast.General(0)));
            Add("general_b", Dead(1.40f, Cast.General(1)));

            // the unremembered: nobody says their names any more, and they have stopped standing up straight
            var shade = Human(1.38f, Cast.Person("shade"));
            shade.Own("idle", "Zombie_Idle_Loop", fade: 0.2f);
            var drift = shade.Fit("walk", "Zombie_Walk_Fwd_Loop", loop: true, fade: 0.16f);
            drift.fps = 8f / 1.333f; drift.frames = 8; drift.stride = 0.62f * 1.38f; drift.paceMax = 3f;
            var claw = shade.Fit("scratch", "Zombie_Scratch", 0.20f, 1.10f, warp: new[] { 0f, 0f, 0.5f, 0.53f, 1f, 1f }, fade: 0.06f);
            claw.frames = 8; claw.fps = 12f;
            Add("shade", shade);

            // a clay soldier of the king's guard
            var clay = Human(1.46f, Cast.Clay);
            Run(clay, 1.46f, 5.6f).With(Gesture.Level);
            Add("ushabti", clay);

            // the two clay armies of the Generals' Barrow, and the piece on the board
            var red = Human(1.5f, Cast.ClayOf(0));
            Run(red, 1.5f, 5.9f).With(Gesture.Level);
            Add("clay_red", red);
            // (a slinger winds for as long as the game gives him, and lets go at the end of it)
            var blue = Human(1.42f, Cast.ClayOf(1));
            var sling = blue.Fit("throw", "OverhandThrow", 0f, 1.05f, warp: new[] { 0f, 0f, 0.78f, 0.33f, 1f, 1f }, fade: 0.08f);
            sling.frames = 12; sling.fps = 15f;
            Add("clay_blue", blue);
            var piece = Human(2.35f, Cast.Piece);
            piece.span = 2;
            Add("last_piece", piece);

            // Kurashtar
            var king = Dead(1.80f, Cast.King);
            var stride = king.Fit("walk", "Walk_Formal_Loop", loop: true, fade: 0.16f);
            stride.fps = 8f / 1.333f; stride.frames = 8; stride.stride = 0.95f * 1.80f; stride.paceMax = 3f;
            // the mace goes up, hangs there long enough to be seen, and comes down on frame 9 of 12
            var slam = king.Fit("slam", "TreeChopping_Loop", 0f, 0.46f, warp: new[] { 0f, 0f, 0.62f, 0.10f, 0.75f, 0.50f, 1f, 1f }, fade: 0.14f);
            slam.frames = 12; slam.fps = 13f;
            var cast = king.Fit("cast", "OverhandThrow", 0f, 0.95f, warp: new[] { 0f, 0f, 0.44f, 0.36f, 1f, 1f }, fade: 0.08f);
            cast.frames = 9; cast.fps = 12f;
            king.Own("rise", "Sitting_Exit", loop: false, fade: 0.05f);
            king.Own("reel", "Hit_Knockback", loop: false, fade: 0.04f);
            king.Own("kneel", "Fixing_Kneeling", 1.0f, 4.2f, fade: 0.25f);
            Add("king", king);

            Add("scarab", Built(1.30f, a => CrabBeast.Make(a, true)));

            // the king's tomb: a lamp bearer (one of the dead, with a habit of holding a lamp up to see who it is),
            // a warden behind his door of a shield, and the scarab that thinks it is rolling the sun
            Add("bearer", Dead(1.33f, Cast.Person("servant")));
            var warden = Human(1.52f, Cast.Warden);
            Run(warden, 1.52f, 5.6f).With(Gesture.Carry);
            warden.Own("guard", "Idle_Loop", fade: 0.07f).With(Gesture.Carry);
            warden.Map("idle").pose = Gesture.Carry;
            warden.Map("walk").pose = Gesture.Carry;
            Add("warden", warden);
            Add("sun_roller", Built(3.6f, a => CrabBeast.Make(a, true), 2));
            Add("vulture", Built(2.7f, a => VultureBeast.Make(a), 3));
        }
    }
}
