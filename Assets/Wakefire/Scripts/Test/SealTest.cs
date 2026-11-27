// The Seal and what it prints, played through in the temple yard: it rolls its beat and seals the
// ground, a Print gets up, edge-on a blade goes past him and side-on one blow breaks him, a blade
// rings off the Seal from the side and sends it back from the front, and three stops split it.
//   -wfScene seal
using System.Collections;
using System.Linq;
using UnityEngine;

namespace Wakefire
{
    public static class SealTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["seal"] = Run;

        static AutoTest T;
        static int bad;
        static void Check(string what, bool ok) { T.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
        static bool Talking => (Story.I && Story.I.Running) || Game.Busy;

        static IEnumerator Quiet(float atLeast = 0.2f, float atMost = 40f)
        {
            float w = 0;
            while ((w < atLeast || Talking) && w < atMost) { w += Time.deltaTime; yield return null; }
        }

        /// <summary>He is kept somewhere (the place may move) until something is so, or the time is up. Story time does not count.</summary>
        static IEnumerator Hold(System.Func<Vector2> at, Facing f, float seconds, System.Func<bool> until = null)
        {
            var p = Player.I;
            for (float w = 0; w < seconds; )
            {
                if (until != null && until()) yield break;
                if (!Talking)
                {
                    if (p.state == Player.State.Free) { p.pos = at(); p.Face(f); }
                    w += Time.deltaTime;
                }
                yield return null;
            }
        }

        static Facing Against(Vector2 along) => Mathf.Abs(along.x) > Mathf.Abs(along.y) ? (along.x > 0 ? Facing.Left : Facing.Right) : (along.y > 0 ? Facing.Down : Facing.Up);

        static IEnumerator Run(AutoTest t)
        {
            T = t; bad = 0;
            DialogueBox.AutoAdvance = 0.1f;
            Save.ClearAll(); Save.Use(0);
            Game.I.Begin(false);
            Story.Abort();
            Story.GiveKit();
            Story.DreamsQuiet = true;
            Game.I.EnterMap("temple_yard", "south");
            Story.Abort();
            Fade.Set(0);
            yield return new WaitForSeconds(0.5f);
            var p = Player.I;
            p.health.max = p.health.hp = 40;
            var seal = Enemy.All.OfType<Seal>().FirstOrDefault();
            Check($"the temple yard: the temple's own seal, loose ({Enemy.All.OfType<Seal>().Count()})", seal);
            if (!seal) { t.Note("SEAL FAILED: 1"); yield break; }
            float len = Vector2.Distance(seal.EndA, seal.EndB);
            Check($"its beat is the way between the gate and the bridge ({len:0.0} tiles, north and south)", len > 5f && Mathf.Abs(seal.EndA.x - seal.EndB.x) < 0.1f);

            // ---------------------------------------------------------------- it rolls, and seals the ground
            var aside = new Vector2(seal.EndA.x - 6f, (seal.EndA.y + seal.EndB.y) * 0.5f);
            float turn0 = seal.Turn; Vector2 at0 = seal.pos;
            yield return Hold(() => aside, Facing.Right, 14f, () => seal.prints.Count(q => q) >= 1);
            Check($"it rolls ({Vector2.Distance(seal.pos, at0):0.0} tiles, the drum {Mathf.Abs(seal.Turn - turn0):0} degrees round), and once round it has printed a spearman ({seal.prints.Count})",
                  seal.prints.Count(q => q) >= 1 && Mathf.Abs(seal.Turn - turn0) > 90f);
            yield return t.Shot("s0-the-seal", 0.25f);
            var first = seal.prints.FirstOrDefault(q => q);
            Check($"he lies in the clay he was pressed in, and nothing can be done to him there ({(first ? first.s.ToString() : "gone")})", first && first.s == Print.S.Flat);
            yield return Hold(() => aside, Facing.Right, 4f, () => !first || first.s == Print.S.March || first.s == Print.S.Edge);
            Check($"then he gets up ({(first ? first.s.ToString() : "gone")}), off the Seal's way ({(first ? Mathf.Abs(first.pos.x - seal.pos.x) : 0):0.0} tiles to the side)",
                  first && first.s != Print.S.Flat && Mathf.Abs(first.pos.x - seal.pos.x) > 0.8f);
            yield return t.Shot("s1-a-print", 0.2f);
            yield return Hold(() => aside, Facing.Right, 16f, () => seal.prints.Count(q => q) >= 3);
            int most = 0;
            for (float w = 0; w < 14f; w += Time.deltaTime) { most = Mathf.Max(most, seal.prints.Count(q => q)); if (p.state == Player.State.Free) { p.pos = aside + new Vector2(-3f, 0); } yield return null; }
            Check($"there are never more than four ({most})", most >= 3 && most <= Seal.Most);

            // ---------------------------------------------------------------- a Print: a line, and then a man
            var man = seal.prints.Where(q => q && (q.s == Print.S.March || q.s == Print.S.Edge)).OrderBy(q => Vector2.Distance(q.pos, p.pos)).FirstOrDefault();
            Check("one of them is on his feet", man);
            if (man)
            {
                // not in his row: he turns to get there, and turned he is a line
                yield return Hold(() => man ? man.pos + new Vector2(0, 2.2f) : p.pos, Facing.Down, 5f, () => !man || (man.s == Print.S.Edge && man.EdgeOn));
                Check($"out of his row he turns to come ({(man ? man.s.ToString() : "gone")}), and turned he is a line ({(man ? man.HitBox.width : 0):0.00} tiles wide)", man && man.EdgeOn && man.HitBox.width < 0.3f);
                yield return t.Shot("s2-edge-on", 0.05f);
                if (man)
                {
                    p.SetState(Player.State.Free, "idle");
                    p.pos = man.pos + new Vector2(0, 1.1f); p.Face(Facing.Down);
                    Controls.FakePress = Controls.Attack;
                    for (float w = 0; w < 0.45f; w += Time.deltaTime) yield return null;
                    Check("a blade goes past a line", man && !man.health.Dead);
                }
                // in his row he has to be side-on to use the spear, and side-on one blow breaks him
                int hp = p.health.hp;
                yield return Hold(() => man ? man.pos + new Vector2(2.6f, 0) : p.pos, Facing.Left, 6f, () => !man || (man.s == Print.S.March && !man.EdgeOn));
                yield return Hold(() => p.pos, Facing.Left, 3.0f, () => !man || p.health.hp < hp);
                Check($"in his row he turns side-on, comes on, and uses the spear ({hp} -> {p.health.hp})", p.health.hp < hp);
                yield return t.Shot("s3-side-on", 0.05f);
                for (float w = 0, next = 0; w < 8f && man; w += Time.deltaTime)
                {
                    if (!Talking && w >= next && (p.state == Player.State.Free || p.state == Player.State.Attack) && !man.EdgeOn)
                    {
                        bool east = p.pos.x > man.pos.x;
                        p.pos = man.pos + new Vector2(east ? 1.0f : -1.0f, -0.3f); p.Face(east ? Facing.Left : Facing.Right);
                        Controls.FakePress = Controls.Attack; next = w + 0.4f;
                    }
                    yield return null;
                }
                Check("side-on, one blow and he is a handful of dry clay", !man);
            }

            // ---------------------------------------------------------------- the Seal: from the side, and from the front
            p.health.hp = p.health.max;
            yield return Hold(() => aside, Facing.Right, 12f, () => seal.s == Seal.S.Roll && Vector2.Distance(seal.pos, seal.EndA) > 1.5f && Vector2.Distance(seal.pos, seal.EndB) > 1.5f);
            p.SetState(Player.State.Free, "idle");
            p.pos = seal.pos + new Vector2(1.9f, -0.2f) + seal.Along * 0.3f; p.Face(Facing.Left);
            Controls.FakePress = Controls.Attack;
            for (float w = 0; w < 0.5f; w += Time.deltaTime) yield return null;
            Check($"from the side a blade rings off it ({seal.s}, {seal.Cracks} cracks)", seal.s == Seal.S.Roll && seal.Cracks == 0);
            // (...and from behind)
            p.SetState(Player.State.Free, "idle");
            p.pos = seal.pos - seal.Along * (seal.Along.y < 0 ? 1.9f : 1.25f); p.Face(Against(-seal.Along));
            Controls.FakePress = Controls.Attack;
            for (float w = 0; w < 0.5f; w += Time.deltaTime) yield return null;
            Check($"and from behind ({seal.s}, {seal.Cracks} cracks)", seal.s == Seal.S.Roll && seal.Cracks == 0);
            // from the front: three times
            float start = Time.time, next2 = 0;
            int sent = 0, taken = 0, before = 0, cracks = seal.Cracks;
            bool wasBack = false, shotBack = false, shotCrack = false;
            System.Func<int> standing = () => seal.prints.Count(q => q && q.s != Print.S.Taken);
            System.Func<bool> fresh = () => seal.prints.Any(q => q && (q.s == Print.S.Flat || q.s == Print.S.Peel));
            while (seal && Time.time - start < 90f)
            {
                if (Talking) { yield return null; continue; }
                // (a stop is counted by the crack it leaves: sent back from a stride off its own end, it is there within the frame)
                if (seal.Cracks > cracks) { sent += seal.Cracks - cracks; cracks = seal.Cracks; taken += Mathf.Max(0, before - standing()); }
                if (!seal.GoingBack) before = standing();
                wasBack = seal.GoingBack;
                if (seal.GoingBack && !shotBack) { shotBack = true; yield return t.Shot("s4-sent-back", 0.12f); continue; }
                if (seal.Cracks == 1 && seal.s == Seal.S.Dazed && !shotCrack) { shotCrack = true; yield return t.Shot("s5-a-crack-right-round-it", 0.2f); continue; }
                if (seal.s == Seal.S.Roll)
                {
                    // in its way, facing it, with a print just laid behind it if there is one to be had
                    var along = seal.Along;
                    var stand = seal.pos + along * (along.y < 0 ? 1.25f : 1.9f);
                    bool room = Vector2.Distance(seal.pos, along.y < 0 ? seal.EndB : seal.EndA) > 2.4f;
                    // (the first time, he waits for it to have just printed: what it has just printed is behind it, in its way)
                    if (sent == 0 && !fresh() && Time.time - start < 40f) room = false;
                    if (room && (p.state == Player.State.Free || p.state == Player.State.Attack))
                    {
                        p.pos = stand; p.Face(Against(along));
                        if (Time.time >= next2) { Controls.FakePress = Controls.Attack; next2 = Time.time + 0.4f; }
                    }
                    else if (p.state == Player.State.Free) p.pos = aside;
                }
                else if (p.state == Player.State.Free) p.pos = aside;
                yield return null;
            }
            if (!seal) sent++;
            Check($"from the front it is sent back the way it came ({sent} times), over what it printed ({taken} taken back)", sent >= 3 && taken >= 1);
            Check($"three stops and it is in two halves ({!seal}, flag {Story.Has("dead_ty_seal")}) in {Time.time - start:0}s, and it cost him {p.health.max - p.health.hp} of {p.health.max}",
                  !seal && Story.Has("dead_ty_seal"));
            yield return t.Shot("s6-in-two", 0.3f);
            yield return new WaitForSeconds(0.6f);
            Check($"and every spearman it pressed has stopped being one ({Enemy.All.OfType<Print>().Count(q => q)})", Enemy.All.OfType<Print>().Count(q => q) == 0);
            // it does not come back
            Game.I.EnterMap("temple_yard", "south");
            Fade.Set(0);
            yield return new WaitForSeconds(0.5f);
            Check($"it does not come back ({Enemy.All.OfType<Seal>().Count()})", !Enemy.All.OfType<Seal>().Any());
            t.Note(bad == 0 ? "SEAL OK" : $"SEAL FAILED: {bad}");
        }
    }
}
