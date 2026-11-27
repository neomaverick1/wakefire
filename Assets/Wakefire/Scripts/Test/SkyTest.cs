// The sky, played through: the rain begins on the terraces and is on every street; a bowl will
// not take in it, no shadow stays up with no moon, and under a roof there is none; the drummer
// has the stick; in the dream the drum on the beat ends the rain and the cold comes down; two
// beats end the cold; and once chapter two is done the Dawn Horn makes it morning for as long
// as a god's ten minutes last.
//   -wfScene sky
using System.Collections;
using System.Linq;
using UnityEngine;

namespace Wakefire
{
    public static class SkyTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["sky"] = Run;

        static AutoTest T;
        static int bad;
        static void Check(string what, bool ok) { T.Note((ok ? "ok   " : "FAIL ") + what); if (!ok) bad++; }
        static bool Talking => (Story.I && Story.I.Running) || Game.Busy;
        static Vector4 Global => Shader.GetGlobalVector("_WF_Sky");

        static IEnumerator Quiet(float atLeast = 0.3f, float atMost = 90f)
        {
            float w = 0;
            while ((w < atLeast || Talking) && w < atMost) { w += Time.deltaTime; yield return null; }
        }

        static IEnumerator Go(string map, string spawn)
        {
            Game.I.EnterMap(map, spawn);
            Fade.Set(0);
            yield return Quiet(0.6f);
        }

        static IEnumerator Dreaming(bool on)
        {
            var p = Player.I;
            if (on) { Dream.I.Drowsiness = 1; Dream.I.Seconds = 9999; Dream.I.Flip(p.pos, true); yield return new WaitForSeconds(1.4f); }
            else { Dream.I.Flip(p.pos, false); yield return new WaitForSeconds(1.2f); Dream.I.SetInstant(false); Dream.I.Seconds = 7; Story.I.ApplyItems(); }
        }

        /// <summary>Hit the drum when the dreamer's beat says so (how long after the cane starts up), up to a few tries of waiting for it.</summary>
        static IEnumerator Beat(Prop drum, float after)
        {
            var p = Player.I;
            // wait for the cane to start up, then `after` more
            float w = 0;
            while (w < 8f && !(Story.I.BeatAge < 0.12f)) { w += Time.deltaTime; yield return null; }
            while (Story.I.BeatAge < after) yield return null;
            p.SetState(Player.State.Free, "idle");
            p.pos = drum.basePos + new Vector2(0, -0.7f); p.Face(Facing.Up);
            Controls.FakePress = Controls.Interact;
            yield return null; yield return null;
        }

        static IEnumerator Run(AutoTest t)
        {
            T = t; bad = 0;
            DialogueBox.AutoAdvance = 0.08f;
            Save.ClearAll(); Save.Use(0);
            Game.I.Begin(false);
            Story.Abort();
            Story.GiveKit();
            var p = Player.I;
            p.health.max = p.health.hp = 20;
            // ---------------------------------------------------------------- the rain begins
            Game.I.EnterMap("terraces", "east");
            Fade.Set(0);
            yield return new WaitForSeconds(0.4f);
            var dancer = Npc.All.FirstOrDefault(n => n && n.id == "rain_dancer");
            Check($"on the threshing floor of the terraces, the rain-dancer, on one leg ({(dancer ? dancer.anim.anim : "nobody")}), and it is not raining yet ({Sky.Raining})",
                  dancer && dancer.anim.anim == "onefoot" || Sky.Raining || Story.Has("rain_begun"));
            yield return t.Shot("k0-the-rain-dancer", 0.2f);
            yield return Quiet(1f, 120f);
            foreach (var e in Enemy.All.ToArray()) Object.Destroy(e.gameObject);
            yield return new WaitForSeconds(1.0f);
            Check($"the Wakefire's light crosses his eyelids, he tips the cane ({(dancer ? dancer.anim.anim : "?")}), and it rains ({Sky.Raining}, {Sky.I.rain:0.0} in the picture, sky {Global})",
                  dancer && dancer.anim.anim == "pour" && Sky.Raining && Sky.I.rain > 0.9f && Global.x > 0.9f && Global.w > 0.5f);
            Check($"the light of the street is the rain's ({PixelView.I.ambient})", PixelView.I.ambient.r < 0.6f);
            yield return t.Shot("k1-it-rains", 0.2f);
            // a bowl under this sky will not take
            var bowl = Map.Current.props.FirstOrDefault(q => q && q.Kind == "brazier" && !q.lit);
            if (bowl)
            {
                Items.Choose("wakefire");
                p.SetState(Player.State.Free, "idle"); p.pos = bowl.basePos + new Vector2(0, -0.6f); p.Face(Facing.Up);
                yield return new WaitForSeconds(0.2f);
                Controls.FakePress = Controls.Item;
                yield return Quiet(0.8f);
                Check($"a fire bowl under it will not take ({bowl.lit}), and the game says why ({Story.Count("rain_bowl")})", !bowl.lit && Story.Count("rain_bowl") > 0);
            }
            else Check("there is an unlit bowl on the terraces to try", false);
            // ---------------------------------------------------------------- it is raining everywhere, and nowhere under a roof
            yield return Go("lowtown", "west");
            Check($"it is raining on the Lower Town too ({Sky.I.rain:0.0}, sky {Global}), and it has been said ({Story.Count("rain_seen_lowtown")})", Global.x > 0.9f && Story.Count("rain_seen_lowtown") > 0);
            Check($"with no moon no shadow stays up ({Enemy.All.OfType<StayUp>().Count()} Stay-Ups)", !Enemy.All.OfType<StayUp>().Any());
            yield return t.Shot("k2-rain-on-the-lower-town", 0.3f);
            // the Seven Jars: no rain under a roof, and the drummer under the table
            Game.I.EnterMap("lowtown_in", null);
            Fade.Set(0);
            yield return Quiet(0.6f);
            Check($"under a roof there is no weather in the picture (sky {Global}), only the sound of it", Global.w < 0.5f && Global.x < 0.01f && Sky.Raining);
            var man = Npc.All.FirstOrDefault(n => n && n.id == "drinker_a");
            Check("the regular under the table of the Seven Jars is there", man);
            if (man) { Story.Run(man.talk()); yield return Quiet(0.5f); }
            Check($"he is Kessi the drummer, and he lets go of the stick ({Story.Has("item_drumstick")})", Story.Has("item_drumstick"));
            // ---------------------------------------------------------------- the twelfth step
            yield return Go("terraces", "east");
            foreach (var e in Enemy.All.ToArray()) Object.Destroy(e.gameObject);
            var drum = Map.Current.Find("rain_drum");
            Check("the dance drum is at the edge of the floor", drum);
            if (!drum) { t.Note("SKY FAILED: no drum"); yield break; }
            p.pos = drum.basePos + new Vector2(0, -0.7f); p.Face(Facing.Up);
            yield return new WaitForSeconds(0.3f);
            Check($"at the drum the action button says {p.Action}", p.Action == Player.Act.Look);
            Controls.FakePress = Controls.Interact;
            yield return Quiet(0.5f);
            Check($"awake, the drum is only a drum: it still rains ({Sky.Raining})", Sky.Raining && !Story.Has("rain_done"));
            yield return Dreaming(true);
            Check($"in the dream it does not rain (sky at him {(Dream.I.IsDreamAt(p.pos) ? "dream" : "awake")}), and the dancer is dancing", Dream.I.IsDreamAt(p.pos) && Npc.All.Any(n => n && n.id == "rain_dancer_self"));
            yield return t.Shot("k3-in-the-dream", 0.3f);
            // off the beat first
            yield return Beat(drum, 2.2f);
            yield return Quiet(0.5f);
            Check($"off the beat he stays on eleven ({Story.Has("rain_done")}, told {Story.Count("drum_miss")})", !Story.Has("rain_done") && Story.Count("drum_miss") > 0);
            yield return Beat(drum, 0.45f);
            yield return Quiet(1f, 120f);
            Check($"on the beat: twelve. The rain stops ({Sky.Raining}), he is paid ({p.coins} shekels), and the cold comes down ({Sky.Cold})", Story.Has("rain_done") && !Sky.Raining && p.coins >= 60 && Sky.Cold);
            yield return Dreaming(false);
            yield return new WaitForSeconds(4.5f);
            Check($"snow, on everything that faces the sky ({Sky.I.snow:0.0} in the picture, sky {Global})", Sky.I.snow > 0.9f && Global.y > 0.9f);
            yield return t.Shot("k4-the-cold-spell", 0.3f);
            // ---------------------------------------------------------------- everyone is freezing, everywhere
            yield return Go("ashkel", null);
            foreach (var e in Enemy.All.ToArray()) Object.Destroy(e.gameObject);
            Check($"the cold is on the gate square too (sky {Global}), and it has been said ({Story.Count("cold_seen_ashkel")})", Global.y > 0.9f && Story.Count("cold_seen_ashkel") > 0);
            yield return t.Shot("k5-snow-on-the-square", 0.4f);
            yield return Go("cliffs", null);
            var nets = Enemy.All.OfType<Dragnet>().ToArray();
            p.SetState(Player.State.Free, "idle");
            if (nets.Length > 0) p.pos = nets[0].pos + new Vector2(1.5f, 0);
            yield return new WaitForSeconds(2.5f);
            Check($"a Dragnet is frozen on the line ({nets.Length} nets, the nearest {(nets.Length > 0 && nets[0] ? nets[0].s.ToString() : "none")})", nets.Length > 0 && nets[0] && nets[0].s == Dragnet.S.Flat);
            yield return t.Shot("k6-the-sea-under-the-cold", 0.3f);
            // ---------------------------------------------------------------- the thirteenth step
            yield return Go("terraces", "east");
            foreach (var e in Enemy.All.ToArray()) Object.Destroy(e.gameObject);
            drum = Map.Current.Find("rain_drum");
            p.pos = drum.basePos + new Vector2(0, -0.7f); p.Face(Facing.Up);
            yield return Dreaming(true);
            // one beat is not thirteen
            yield return Beat(drum, 0.45f);
            yield return new WaitForSeconds(3.2f);
            Check($"one beat is not thirteen ({Sky.Cold})", Sky.Cold && !Story.Has("cold_done"));
            // up, and down
            yield return Beat(drum, 0.45f);
            for (float k = 0; k < 1.25f; k += Time.deltaTime) yield return null;
            p.SetState(Player.State.Free, "idle");
            Controls.FakePress = Controls.Interact;
            yield return Quiet(1f, 120f);
            Check($"up and down: thirteen. The cold lifts ({Sky.Cold}), and he pays for it himself ({p.coins})", Story.Has("cold_done") && !Sky.Cold && p.coins >= 140);
            yield return Dreaming(false);
            yield return new WaitForSeconds(5f);
            Check($"the picture is a clear night again (rain {Sky.I.rain:0.0}, snow {Sky.I.snow:0.0}, light {PixelView.I.ambient})", Sky.I.rain < 0.05f && Sky.I.snow < 0.05f && PixelView.I.ambient.b > 0.9f);
            // ---------------------------------------------------------------- morning, by the horn
            Items.Choose("horn");
            Check($"before the Dawn Horn has been blown in earnest it is not a thing for the street ({(Items.Current != null ? Items.Current.id : "none")})", Items.Current == null || Items.Current.id != "horn");
            Story.Set("item_horn"); Story.Set("chapter_done"); Story.Set("chapter2_done");
            yield return Go("ashkel", null);
            int night = Enemy.All.Count(e => e && Story.NightOnly(e));
            Items.Choose("horn");
            p.SetState(Player.State.Free, "idle");
            Controls.FakePress = Controls.Item;
            yield return Quiet(1.5f, 60f);
            yield return new WaitForSeconds(4.5f);
            Check($"after chapter two he blows it under open sky and it is morning ({Sky.Day}, {Sky.I.day:0.0} in the picture, light {PixelView.I.ambient})", Sky.Day && Sky.I.day > 0.9f && PixelView.I.ambient.r > 1.0f);
            Check($"nothing that walks the night walks in it ({night} before, {Enemy.All.Count(e => e && Story.NightOnly(e))} now)", night > 0 && !Enemy.All.Any(e => e && Story.NightOnly(e)));
            yield return t.Shot("k7-morning-on-the-square", 0.4f);
            yield return Go("lowtown", null);
            Check($"it is morning in the Lower Town too, and its dreams have gone home ({Enemy.All.Count(e => e && Story.NightOnly(e))})", Sky.Day && !Enemy.All.Any(e => e && Story.NightOnly(e)));
            yield return t.Shot("k8-morning-in-the-lower-town", 0.4f);
            // a god's ten minutes
            Story.SetCount("day_left", 2);
            yield return Go("ashkel", null);
            yield return new WaitForSeconds(3.0f);
            yield return Quiet(0.5f, 60f);
            yield return new WaitForSeconds(6f);
            Check($"and when his ten minutes are up it is night again ({Sky.Day}, {Sky.I.day:0.0})", !Sky.Day && Sky.I.day < 0.1f);
            yield return Go("lowtown", null);
            Check($"and what walks the night is back ({Enemy.All.Count(e => e && Story.NightOnly(e))})", Enemy.All.Any(e => e && Story.NightOnly(e)));
            t.Note(bad == 0 ? "SKY OK" : $"SKY FAILED: {bad}");
        }
    }
}
