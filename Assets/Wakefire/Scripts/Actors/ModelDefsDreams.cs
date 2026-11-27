// Who plays the bad dreams of Ashkel. Most of them have no stock body: a bell on three legs,
// a flame on its wick, a net. A Stay-Up is a man, of whom only the shadow is ever drawn.
using UnityEngine;

namespace Wakefire
{
    public static partial class ModelDefs
    {
        static void Dreams()
        {
            // the Snuffer: it rears for most of a second and comes down in an eighth of one
            var snuffer = Built(1.33f, a => SnufferProp.Make(a));
            snuffer.Time("idle", 3f, 4);
            snuffer.Time("walk", 8f, 8);
            snuffer.Time("sniff", 6f, 4);
            snuffer.Time("rear", 10f, 7, once: true);
            snuffer.Time("drop", 30f, 4, once: true);
            snuffer.Time("cover", 3f, 4);
            snuffer.Time("rise", 10f, 6, once: true);
            snuffer.Time("tipped", 3f, 4);
            snuffer.Time("up", 10f, 7, once: true);
            Add("snuffer", snuffer);

            // a Wick
            var wick = Built(1.33f, a => WickProp.Make(a));
            wick.Time("idle", 6f, 4);
            wick.Time("walk", 8f, 4);
            wick.Time("dart", 10f, 7, once: true);
            wick.Time("leap", 10f, 4, once: true);
            Add("wick", wick);

            // the Dragnet, and a net that is only a net (no money in it)
            foreach (var (name, live) in new[] { ("dragnet", true), ("net", false) })
            {
                bool l = live;
                var net = Built(1.33f, a => DragnetProp.Make(a, l));
                net.Time("flat", 2f, 2);
                net.Time("rise", 8f, 6, once: true);
                net.Time("cast", 12f, 6, once: true);
                net.Time("spent", 2f, 2);
                net.Time("creep", 8f, 8);
                net.Time("wrap", 6f, 4);
                Add(name, net);
            }

            // a Stay-Up: somebody's shadow. It goes low, the way a shadow lies, and it reaches.
            var stay = Human(1.6f, Cast.Person("sleeper_a"));
            stay.Own("idle", "Zombie_Idle_Loop", speed: 0.6f, fade: 0.25f);
            var creep = stay.Fit("walk", "Zombie_Walk_Fwd_Loop", loop: true, fade: 0.18f);
            creep.fps = 8f / 1.333f; creep.frames = 8; creep.stride = 0.62f * 1.6f; creep.paceMax = 3.5f;
            stay.Own("grip", "Zombie_Scratch", 0.20f, 1.10f, speed: 0.8f, fade: 0.08f);
            Add("stayup", stay);
        }
    }
}
