// The action button and the mirror shield: -wfScene guard checks that the button knows what is in
// front of Azar (someone to talk to, a sign to read, a chest to open), that with the shield and
// nothing in front it raises the shield for as long as it is held, and what the raised shield
// does and does not stop.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class GuardTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["guard"] = Run;

        static IEnumerator Enter(string map, string spawn = null)
        {
            Game.I.EnterMap(map, spawn);
            Story.Abort();
            Fade.Set(0);
            Player.I.SetState(Player.State.Free, "idle");
            foreach (var e in Enemy.All.ToArray()) if (e) Object.Destroy(e.gameObject);
            yield return new WaitForSeconds(0.4f);
        }

        static Prop Find(string kind)
        {
            foreach (var pr in Map.Current.props) if (pr && pr.Kind == kind) return pr;
            return null;
        }

        static IEnumerator Run(AutoTest t)
        {
            int bad = 0;
            void Check(string what, bool ok) { t.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
            Save.ClearAll(); Save.Use(0);
            Game.I.Begin(false);
            Story.Abort();
            // what the game tells the player about the buttons fits its pages on an ordinary screen
            int lt = DialogueBox.PageCount(Story.Lesson(true)), lk = DialogueBox.PageCount(Story.Lesson(false)), sh = DialogueBox.PageCount(Story.ShieldText);
            Check($"the first lesson is three pages for thumbs and for keys ({lt}, {lk}), the shield's four ({sh})", lt == 3 && lk == 3 && sh == 4);
            yield return Enter("lowtown", "north");
            var p = Player.I;
            p.pos = Map.ToWorld(480, 60);
            p.Face(Facing.Down);
            yield return new WaitForSeconds(0.2f);
            Check($"no shield, nothing in front: nothing to do ({p.Action})", p.Action == Player.Act.None);
            Npc who = null;
            foreach (var n in Npc.All) if (n && n.talk != null && n.Present && n.anim.anim != "lie") { who = n; break; }
            if (who)
            {
                p.pos = who.pos + new Vector2(0, -0.9f); p.Face(Facing.Up);
                yield return new WaitForSeconds(0.2f);
                Check($"someone in front ({who.id}): {p.Action}", p.Action == Player.Act.Talk);
            }
            var sign = Find("sign");
            if (sign)
            {
                p.pos = sign.basePos + new Vector2(0, -0.7f); p.Face(Facing.Up);
                yield return new WaitForSeconds(0.2f);
                Check($"a sign in front: {p.Action}", p.Action == Player.Act.Read);
            }
            yield return Enter("zig_1", "south");
            var chest = Find("chest");
            p.pos = chest.basePos + new Vector2(0, -0.75f); p.Face(Facing.Up);
            yield return new WaitForSeconds(0.2f);
            Check($"a chest in front: {p.Action}", p.Action == Player.Act.Open);

            // the shield
            Story.Set("item_shield"); Story.I.ApplyItems();
            p.pos = Map.ToWorld(256, 300); p.Face(Facing.Right);
            yield return new WaitForSeconds(0.2f);
            Check($"with the shield and nothing in front: {p.Action}", p.Action == Player.Act.Guard);
            Controls.FakeHold = Controls.Interact; Controls.FakePress = Controls.Interact;
            yield return new WaitForSeconds(0.5f);
            Check("holding the button raises the shield", p.Guarding);
            yield return t.Shot("g1-guard", 0.2f);
            // how it looks each way he can face
            int shot = 0;
            foreach (var f in new[] { Facing.Down, Facing.Left, Facing.Up })
            {
                Controls.FakeHold = null;
                yield return new WaitForSeconds(0.3f);
                p.Face(f);
                Controls.FakeHold = Controls.Interact; Controls.FakePress = Controls.Interact;
                yield return new WaitForSeconds(0.5f);
                yield return t.Shot("g1-guard-" + (++shot), 0.1f);
            }
            Controls.FakeHold = null;
            yield return new WaitForSeconds(0.3f);
            p.Face(Facing.Right);
            Controls.FakeHold = Controls.Interact; Controls.FakePress = Controls.Interact;
            yield return new WaitForSeconds(0.5f);
            int hp = p.health.hp;
            p.Hurt(new HitInfo { damage = 1, from = p.pos + Vector2.right, knockback = 6, kind = HitKind.Slash });
            Check($"a blow from the front stops on it (life {p.health.hp}/{hp})", p.health.hp == hp && p.Guarding);
            yield return t.Shot("g2-blocked", 0.05f);
            yield return new WaitForSeconds(0.5f);
            // fire comes back off it
            var ball = Projectile.Fireball(p.pos + Vector2.right * 4f, Vector2.left * 5f, null);
            bool back = false;
            for (float w = 0; w < 1.6f && ball; w += Time.deltaTime) { back |= ball.reflected; yield return null; }
            Check($"fire meets the raised shield and goes back (life {p.health.hp})", back && p.health.hp == hp);
            yield return new WaitForSeconds(0.4f);
            p.Hurt(new HitInfo { damage = 1, from = p.pos + Vector2.right, knockback = 6, kind = HitKind.Crush });
            Check($"what comes down like a mace does not stop for a shield (life {p.health.hp})", p.health.hp == hp - 1);
            yield return new WaitForSeconds(1.3f);
            Controls.FakePress = Controls.Interact;
            yield return new WaitForSeconds(0.4f);
            p.Hurt(new HitInfo { damage = 1, from = p.pos + Vector2.left, knockback = 6, kind = HitKind.Slash });
            Check($"a blow from behind lands (life {p.health.hp})", p.health.hp == hp - 2);
            yield return new WaitForSeconds(1.3f);
            // moving with it up is slow, and he keeps facing the way he was
            Controls.FakePress = Controls.Interact;
            yield return new WaitForSeconds(0.3f);
            var from = p.pos; var faced = p.facing;
            Controls.Fake = Vector2.left;
            yield return new WaitForSeconds(1.0f);
            Controls.Fake = Vector2.zero;
            float walked = (p.pos - from).magnitude;
            Check($"shield up: he backs away slowly, still facing {p.facing} (moved {walked:0.0} tiles in a second)", p.Guarding && p.facing == faced && walked > 0.8f && walked < 2.6f);
            Controls.FakeHold = null;
            yield return new WaitForSeconds(0.3f);
            Check("letting go lowers it", !p.Guarding && p.state == Player.State.Free);
            // down, it does nothing: the same fire burns
            var ball2 = Projectile.Fireball(p.pos + Vector2.right * 4f, Vector2.left * 5f, null);
            int before = p.health.hp;
            for (float w = 0; w < 1.6f && ball2; w += Time.deltaTime) yield return null;
            Check($"shield down, the fire lands (life {p.health.hp})", p.health.hp < before);
            t.Note(bad == 0 ? "ACTION AND SHIELD OK" : $"FAILED {bad}");
        }
    }
}
