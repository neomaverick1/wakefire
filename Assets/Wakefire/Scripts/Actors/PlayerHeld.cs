// The things that can be done to Azar by what walks the city at night, besides hurting him:
// held (a net round him, a bell over him), and rooted (something has hold of his shadow).
using UnityEngine;

namespace Wakefire
{
    public partial class Player
    {
        MonoBehaviour holder;
        bool hidden;
        float lanternWas = -1f;

        /// <summary>Seconds his feet will not answer him (something has hold of his shadow). He can still cut,
        /// guard, and hold out the flame; he cannot walk or roll. Whatever is holding him keeps this topped up.</summary>
        public float rooted;
        public bool Rooted => rooted > 0;
        /// <summary>Out of sight (under a bell): nothing draws him and nothing should aim at him.</summary>
        public bool Hidden => hidden;

        /// <summary>Something has him. He cannot go anywhere; what he can do about it is the holder's business
        /// (it reads the buttons). False if he cannot be taken just now: mid-roll, in a story, already held.</summary>
        public bool Hold(MonoBehaviour by, string animName = null, bool hide = false)
        {
            if (state == State.Dead || state == State.Cutscene || state == State.Talk || state == State.ItemGet || state == State.Stone ||
                state == State.Held || state == State.Rail || state == State.Nod) return false;
            if (state == State.Roll && stateClock < 0.36f) return false;        // rolled clear
            if (Story.I && Story.I.Running) return false;
            holder = by;
            state = State.Held;
            stateClock = 0;
            vel = Vector2.zero; knock = Vector2.zero; combo = 0; queued = false;
            if (animName != null) anim.Play(animName, facing, true);
            if (hide) Hide(true);
            return true;
        }

        public bool HeldBy(MonoBehaviour by) => state == State.Held && holder == by;

        /// <summary>Let go (by whoever had him: anyone else asking is ignored).</summary>
        public void Release(MonoBehaviour by)
        {
            if (holder != by) return;
            holder = null;
            if (hidden) Hide(false);
            if (state == State.Held) ToFree();
        }

        void Hide(bool on)
        {
            hidden = on;
            if (shadow) shadow.enabled = !on;
            if (lantern)
            {
                if (on) { lanternWas = lantern.intensity; lantern.intensity = 0f; }
                else if (lanternWas >= 0) { lantern.intensity = lanternWas; lanternWas = -1f; }
            }
            if (!on) anim.sr.enabled = true;
        }

        /// <summary>A Snuffer has come down over him.</summary>
        public bool GoUnder(Snuffer s) => Hold(s, "cower", true);

        /// <summary>...and he is out from under it, wherever he is put.</summary>
        public void ComeOut(Vector2 at)
        {
            var by = holder;
            if (by != null) Release(by);
            if (!Solids.Overlaps(new Rect(at - half, half * 2), at, this)) pos = at;
            health.invulnerable = Mathf.Max(health.invulnerable, 0.5f);
        }

        /// <summary>Seconds left of the Wakefire held out at arm's length: for that long it is a light on the ground
        /// round him like any other fire (a shadow that is only a shadow cannot stand in it).</summary>
        public float flare;

        /// <summary>A yawn has gone through him: for as long as it takes, he can do nothing else.
        /// False if he is in no state to (mid-roll, held, in a story, asleep already).</summary>
        public bool YawnHelplessly()
        {
            if (state != State.Free && state != State.Guard && state != State.Attack) return false;
            if (Story.I && Story.I.Running) return false;
            state = State.Use;
            stateClock = 0;
            striking = false; pocketing = false; combo = 0; queued = false;
            vel = Vector2.zero;
            anim.Play("yawn", facing == Facing.Up ? Facing.Down : facing, true);
            return true;
        }

        /// <summary>One yawn too many: he is asleep where he stands. With the Wakefire that means the dream, whether
        /// he meant to go or not; where there is no dream to go to, he simply sleeps for a moment, standing up.</summary>
        public void AsleepOnHisFeet()
        {
            var d = Dream.I;
            if (d && !d.Dreaming && !d.Locked && hasLantern)
            {
                d.Drowsiness = Mathf.Max(d.Drowsiness, 0.5f);
                state = State.Nod;
                stateClock = 0;
                vel = Vector2.zero;
                anim.Play("nod", facing == Facing.Up ? Facing.Down : facing, true);
            }
            else
            {
                state = State.Use;
                stateClock = 0;
                striking = false; pocketing = false;
                vel = Vector2.zero;
                anim.Play("doze", Facing.Down, true);
            }
            if (Story.I) Story.I.YawnedOff();
        }

        /// <summary>While held: nothing of his own moves him. If whatever had him has gone, he is free.</summary>
        void HeldUpdate(float dt)
        {
            vel = Vector2.zero;
            Action = Act.None;
            if (holder == null || !holder) { holder = null; if (hidden) Hide(false); ToFree(); }
        }
    }
}
