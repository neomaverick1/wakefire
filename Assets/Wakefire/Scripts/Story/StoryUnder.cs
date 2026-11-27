// What the story has to say about the Underbed: the arm from under the bed, the edge of the
// light, and the place under every bed that is the same place.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public partial class Story
    {
        public void ReachSeen() =>
            Once("reach_seen", "An arm, from under the bed.^It is long, and grey, and it has more elbows than an arm needs.| "
                               + "There is nobody on the other end of it. You are almost sure there is nobody on the other end of it.");

        public void ReachPeeks() =>
            Once("reach_peeks", "Four grey fingers, at the edge of the bed, drumming.^They stop when you look. They start again when you stop.| It has felt your belt for a blade and not found one. You are, for the moment, beneath its notice.");

        public void ReachWaits() =>
            Once("reach_waits", "It has stopped at the edge of the torchlight, and is drumming its fingers.^It will not put its hand in the light.| It has all night. It has had four hundred years of them.");

        public void ReachGone(Reach r) =>
            Once("reach_gone", "It goes back under, and it stays there.^You get the feeling the rest of it has been told.");

        /// <summary>It has him. Under one bed is under all of them: he is put out again from under another, a little the
        /// worse for it and a little the poorer, and what fell out of his purse stays under there with everything else.</summary>
        public IEnumerator TakenUnder(Reach r)
        {
            var p = Player.I;
            int n = Bump("taken_under");
            p.SetState(Player.State.Cutscene, "push");
            Sfx.Play("under_take", 1f, 0.03f);
            yield return Fade.Out(0.28f);
            // where that arm's fancy runs to
            Vector2 at = r ? (r.owner ? r.owner.pos - r.mouth * 2.4f : r.pos + r.mouth * 1.4f) : p.pos;
            var map = Map.Current;
            // the first bed has no use for a man who came without the blade: it puts him outside its room
            bool turnedOut = false;
            if (r && r.owner && !p.hasSword && Rooms.I)
            {
                var crawl = Rooms.I.Find("run");
                if (crawl != null) { at = new Vector2(crawl.rect.xMin + 46 / 16f, crawl.rect.yMax - 128 / 16f); turnedOut = true; }
            }
            if (r && !string.IsNullOrEmpty(r.to) && map)
            {
                var mk = map.Marker("spawn", r.to);
                if (mk != null) at = Map.ToWorld(mk.x, mk.y);
            }
            if (r) p.Release(r);
            p.pos = at;
            p.Face(Facing.Down);
            int took = Mathf.Min(p.coins, 6 + 2 * Mathf.Min(n, 4));
            if (took > 0) { p.coins -= took; SetCount("under_hoard", Count("under_hoard") + took); }
            for (float t = 0; t < 0.55f; t += Time.unscaledDeltaTime) yield return null;
            Sfx.Play("under_out", 0.9f, 0.04f);
            yield return Fade.In(0.3f);
            p.SetState(Player.State.Free, "idle");
            p.health.invulnerable = 0;
            p.Hurt(new HitInfo { damage = 1, from = p.pos + Vector2.up, knockback = 2.5f, kind = HitKind.Crush });
            Fx.Dust(p.pos, 8);
            if (turnedOut)
            {
                p.SetState(Player.State.Talk, "idle");
                yield return Narrate("The first bed of the First Watch has gone through your belt for a blade, found none, and put you out of its room.^It has standards.| "
                                     + "{g}'TAKE THE BLADE'{/}, it said on the stair, first. You had assumed the order was a suggestion.");
            }
            else if (n == 0)
            {
                p.SetState(Player.State.Talk, "idle");
                yield return Narrate("Under the bed.^It is the same under as under every other bed. You knew that when you were four.| "
                                     + "It keeps you a moment, decides against you, and puts you out from under a different one."
                                     + (took > 0 ? $"| It has kept {took} shekels. They will turn up. Things do, under beds." : "| It has kept your left sandal. You had not noticed you still had one."));
            }
            else if (took > 0 && n == 1)
            {
                p.SetState(Player.State.Talk, "idle");
                yield return Narrate($"{took} more shekels, gone under.^Somewhere down here there is a heap with your name on it. In your own purse's handwriting.");
            }
        }

        // ------------------------------------------------------------------- the bed in the last room
        public void UnderbedGetsUp() =>
            Once("underbed_up", "The bed is getting up.^It has its hands on the floor. All of them.| It does not need to see you. It only needs you to be where it comes down.");

        /// <summary>It is only a bed now: it stays where it stopped, and can be looked at.</summary>
        public void BedAtRest()
        {
            var map = Map.Current;
            if (!map || Game.I.CurrentMap != "crypt") return;
            Vector2 at = new Vector2(Count("underbed_x") / 16f, Count("underbed_y") / 16f);
            if (Count("underbed_x") == 0 && Count("underbed_y") == 0)
            {
                // (a journey from before there was a bed here: it is where the map says it stood)
                MarkerJson mk = null;
                foreach (var m in map.data.markers) if (m.kind == "enemy" && m.id == "crypt_mother") mk = m;
                if (mk == null) return;
                at = Map.ToWorld(mk.x, mk.y);
            }
            foreach (var n in Npc.All) if (n && n.id == "first_bed") return;
            var bed = Npc.Create("first_bed", at, "moth", "idle", WorldLayer.Waking, Facing.Down, true, "bedstead");
            bed.turnsToTalk = false;
            bed.snore = null;
            bed.talk = () => One(Narrate(Bump("first_bed") == 0
                ? "The first bed of the First Watch.^Nobody is in it. Nothing is under it but floor.| You looked. You looked twice. You are not proud of the second time."
                : "A bed.^It is the most restful thing in Ashkel, and you are the only man in the city who cannot use it."));
        }

        /// <summary>The heap at the end of its run: every left sandal of the First Watch, and whatever it has had off Azar.</summary>
        public IEnumerator UnderHoard()
        {
            int had = Count("under_hoard");
            if (had > 0)
            {
                SetCount("under_hoard", 0);
                Player.I.coins += had;
                Sfx.Play("coin_big", 0.9f, 0.02f);
                yield return Narrate($"On top of four hundred years of left sandals: {{g}}{had} shekels{{/}}, with your thumbprint still on them.^You take them back. Nothing under the heap objects.| Nothing under the heap is in a position to.");
            }
            else
                yield return Narrate("Sandals. Four hundred years of them, and every one of them a left.^The First Watch was buried in its boots. Something under the beds has been correcting this, a night at a time.| "
                                     + "Nobody knows what it has against the right foot.");
        }
    }
}
