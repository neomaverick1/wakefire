// Is the game actually audible? For the build machine: -wfScene sound plays the title music, walks
// into the square, swings the blade and nods off, while a tap on the listener writes everything
// that reaches the speakers to a WAV file and the log says how loud each part was.
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace Wakefire
{
    public class SoundTap : MonoBehaviour
    {
        public readonly List<float> samples = new List<float>();
        public int channels = 2;
        readonly object gate = new object();

        void OnAudioFilterRead(float[] data, int ch)
        {
            channels = ch;
            lock (gate) samples.AddRange(data);
        }

        public float[] Take()
        {
            lock (gate) { var a = samples.ToArray(); samples.Clear(); return a; }
        }
    }

    public static class SoundTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["sound"] = Run;

        static float Rms(float[] a)
        {
            if (a.Length == 0) return 0;
            double s = 0;
            foreach (var v in a) s += v * v;
            return Mathf.Sqrt((float)(s / a.Length));
        }

        static IEnumerator Run(AutoTest t)
        {
            if (Boot.Flag("-wfNoListener"))
            {
                // the game as it shipped up to 1.2.0 had nothing listening. Render the engine's own
                // final mix that way, then with a listener, and compare.
                var had = Object.FindObjectsByType<AudioListener>(FindObjectsSortMode.None);
                foreach (var l in had) Object.DestroyImmediate(l);
                Fade.Set(0);
                Music.Play("title");
                Time.captureFramerate = 60;
                bool ok = AudioRenderer.Start();
                for (int pass = 0; pass < 2; pass++)
                {
                    if (pass == 1) Game.I.gameObject.AddComponent<AudioListener>();
                    double sum = 0; long count = 0;
                    for (int i = 0; i < 180; i++)
                    {
                        yield return null;
                        int n = AudioRenderer.GetSampleCountForCaptureFrame();
                        var buf = new Unity.Collections.NativeArray<float>(n * 2, Unity.Collections.Allocator.Temp);
                        AudioRenderer.Render(buf);
                        if (i >= 60) foreach (var v in buf) { sum += v * v; count++; }
                        buf.Dispose();
                    }
                    int on = 0;
                    foreach (var src in Object.FindObjectsByType<AudioSource>(FindObjectsSortMode.None)) if (src.isPlaying && src.volume > 0.01f) on++;
                    int ls = Object.FindObjectsByType<AudioListener>(FindObjectsSortMode.None).Length;
                    t.Note($"renderer={ok} listeners={ls} sources playing={on} final mix rms={System.Math.Sqrt(sum / System.Math.Max(1, count)):0.000000}");
                }
                AudioRenderer.Stop();
                Time.captureFramerate = 0;
                yield break;
            }
            var listeners = Object.FindObjectsByType<AudioListener>(FindObjectsSortMode.None);
            t.Note($"listeners={listeners.Length} driver rate={AudioSettings.outputSampleRate} speakers={AudioSettings.speakerMode} dsp={AudioSettings.dspTime:0.00}");
            if (listeners.Length == 0) { t.Note("FAIL no listener"); yield break; }
            var tap = listeners[0].gameObject.AddComponent<SoundTap>();
            var all = new List<float>();
            Fade.Set(0);
            // the title music
            Music.Play("title");
            yield return new WaitForSeconds(3f);
            var part = tap.Take(); all.AddRange(part);
            var probe = new float[1024];
            AudioListener.GetOutputData(probe, 0);
            t.Note($"title music rms={Rms(part):0.0000} samples={part.Length} output probe rms={Rms(probe):0.0000}");
            // the square: town music and the night under it
            var g = Game.I;
            var p = g.EnterMap("ashkel");
            Music.Play("town");
            yield return new WaitForSeconds(3f);
            part = tap.Take(); all.AddRange(part);
            t.Note($"town music + ambience rms={Rms(part):0.0000}");
            int playing = 0;
            foreach (var s in Object.FindObjectsByType<AudioSource>(FindObjectsSortMode.None)) if (s.isPlaying && s.volume > 0.01f) playing++;
            t.Note($"sources playing={playing}");
            // steps and three cuts
            Controls.Fake = Vector2.right;
            yield return new WaitForSeconds(1.2f);
            Controls.Fake = Vector2.zero;
            for (int i = 0; i < 3; i++) { Controls.FakePress = Controls.Attack; yield return new WaitForSeconds(0.3f); }
            yield return new WaitForSeconds(0.6f);
            part = tap.Take(); all.AddRange(part);
            t.Note($"steps + combo rms={Rms(part):0.0000}");
            // into the dream: the other half of the score
            Dream.I.Drowsiness = 1;
            p.NodOff();
            yield return new WaitForSeconds(3.5f);
            part = tap.Take(); all.AddRange(part);
            t.Note($"dream rms={Rms(part):0.0000}");
            Controls.Fake = null;
            // everything that reached the speakers
            string path = Path.Combine(t.dir, "mix.wav");
            int rate = AudioSettings.outputSampleRate, ch = Mathf.Max(1, tap.channels);
            using (var w = new BinaryWriter(File.Create(path)))
            {
                int bytes = all.Count * 2;
                w.Write(System.Text.Encoding.ASCII.GetBytes("RIFF")); w.Write(36 + bytes); w.Write(System.Text.Encoding.ASCII.GetBytes("WAVEfmt "));
                w.Write(16); w.Write((short)1); w.Write((short)ch); w.Write(rate); w.Write(rate * ch * 2); w.Write((short)(ch * 2)); w.Write((short)16);
                w.Write(System.Text.Encoding.ASCII.GetBytes("data")); w.Write(bytes);
                foreach (var v in all) w.Write((short)Mathf.Clamp(v * 32767f, -32768f, 32767f));
            }
            float peak = 0;
            foreach (var v in all) peak = Mathf.Max(peak, Mathf.Abs(v));
            t.Note($"wrote {path} seconds={all.Count / (float)(rate * ch):0.0} peak={peak:0.000} overall rms={Rms(all.ToArray()):0.0000}");
            t.Note(Rms(all.ToArray()) > 0.005f ? "SOUND OK" : "FAIL silent");
        }
    }
}
