// What the narrator has to say about the bad dreams of Ashkel, the first time each of them does
// the thing it does. Every one of these is said once in a journey and never again.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        /// <summary>For test runs: nothing here stops to talk.</summary>
        public static bool DreamsQuiet;

        void Once(string key, string text)
        {
            if (DreamsQuiet || Count(key) > 0) return;
            Bump(key);
            RunWhenFree(One(Narrate(text)));
        }

        /// <summary>Things on the map that belong with the bad dreams but are not one: a net that is only a net.</summary>
        bool SpawnDreams(string who, Vector2 at)
        {
            if (!who.StartsWith("net")) return false;
            var n = Npc.Create(who, at, "moth", "flat", WorldLayer.Waking, Facing.Down, false, "net");
            n.turnsToTalk = false;
            n.snore = null;
            n.orderBias = -40;                      // it lies on the ground: whoever walks across it is on top of it
            n.talk = () => One(Narrate(Bump("just_a_net") % 3 == 0
                ? "A net, left out to dry forty nights ago.^It is a net. You watched it for a while, to be sure."
                : "A net.^There is no money in this one. That seems to be the difference."));
            return true;
        }

        // ------------------------------------------------------------------------- the Snuffer
        public void SnufferSeen() =>
            Once("snuffer_seen", "Something bronze has come to see about the light.^It is what the lamp seller puts his lamps out with. It is not usually this size, or out on its own.| It has no interest in you. You are not on fire.");

        public void Snuffed(Prop bowl)
        {
            if (Game.I.CurrentMap == "ashkel") FiresChanged();
            Once("snuffer_snuffed", "Out.^It did not ask whose that was.| Every flame in Ashkel went out that night. Now you know who was going round.");
        }

        public void SnufferMetTheWakefire(bool cooked) =>
            Once("snuffer_wakefire", cooked
                ? "The Wakefire never goes out.^It does get hot, when something sits on it.| Next time, ring the bell. It is the only door there is."
                : "The Wakefire never goes out.^The Snuffer has now been told this from the inside.| It is on its side. That end is open.");

        // ------------------------------------------------------------------------------ Wicks
        public void WickSeen() =>
            Once("wick_seen", "A lamp flame, with no lamp.^Every flame in Ashkel went out that night. Nobody asked where to.| This one came up here, to where the oil is made.");

        public void WickHome(Wick w, Prop bowl) =>
            Once("wick_home", "It went into the bowl like a man getting into bed.^The fire is lit. You did not light it.| You will be taking the credit.");

        // ------------------------------------------------------------------------ the Dragnet
        public void DragnetStoodUp(Dragnet d) =>
            Once("dragnet_up", "The net stands up.^There is nobody in it. There is nobody holding it.| It has been fishing for forty nights without either, and it is not about to stop for a watchman.");

        public void DragnetDone(Dragnet d) =>
            Once("dragnet_done", "It comes apart into rope.^Forty nights of catch falls out of it.| Mostly it caught sand.");

        // --------------------------------------------------------------------------- Stay-Ups
        public void StayUpGripped() =>
            Once("stayup_grip", "It has your shadow.^You did not know you could feel that.| A blade is no use. It is not there. Your shadow is, and so is anything that burns.");

        public void StayUpGone(StayUp s) =>
            Once("stayup_gone", "It goes the way shadows go when somebody brings a lamp.^Indoors, somebody turns over, and sleeps properly for the first time in forty nights.");

        // --------------------------------------------------------------------------- the Yawn
        public void CaughtAYawn() =>
            Once("yawn_caught", "You yawned.^You did not decide to. It is going round.| It has been going round for forty nights. Three, and even you are asleep on your feet.");

        public void YawnedOff() =>
            Once("yawn_off", "That was three.^You are asleep, standing up, in the middle of the street.| For the only man in Ashkel who cannot be kept asleep, it is a poor showing.");
    }
}
