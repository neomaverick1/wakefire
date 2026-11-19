// Automated check run on a build machine: started with -wfShots <folder> [-wfScene name], it
// builds a test setup, plays a scripted sequence and saves screenshots. Does nothing otherwise.
using System;
using System.Collections;
using System.Collections.Generic;
using System.IO;
using UnityEngine;

namespace Wakefire
{
    public partial class Game
    {
        partial void OnBoot()
        {
            var dir = Boot.Arg("-wfShots");
            if (dir != null)
            {
                var t = gameObject.AddComponent<AutoTest>();
                t.dir = dir;
                t.scene = Boot.Arg("-wfScene") ?? "render";
                return;
            }
            StartGame();
        }

        partial void StartGame();
    }

    public class AutoTest : MonoBehaviour
    {
        public string dir, scene;
        readonly List<string> log = new List<string>();
        public static readonly Dictionary<string, Func<AutoTest, IEnumerator>> Scenes = new Dictionary<string, Func<AutoTest, IEnumerator>>();

        IEnumerator Start()
        {
            Directory.CreateDirectory(dir);
            Application.logMessageReceived += (msg, trace, type) =>
            {
                if (type != LogType.Log) log.Add($"{type}: {msg}\n{trace}");
            };
            yield return null;
            if (Scenes.TryGetValue(scene, out var run)) yield return StartCoroutine(run(this));
            else log.Add("unknown test scene " + scene);
            File.WriteAllText(Path.Combine(dir, "log.txt"), string.Join("\n\n", log));
            yield return new WaitForSecondsRealtime(0.3f);
            Application.Quit();
        }

        public IEnumerator Shot(string name, float wait = 0)
        {
            if (wait > 0) yield return new WaitForSecondsRealtime(wait);
            yield return new WaitForEndOfFrame();
            ScreenCapture.CaptureScreenshot(Path.Combine(dir, name + ".png"));
            yield return null;
            yield return null;
        }

        public void Note(string s) => log.Add(s);
    }
}
