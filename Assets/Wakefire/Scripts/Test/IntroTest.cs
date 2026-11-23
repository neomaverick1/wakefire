// The opening on the build machine: title, the cards over black, Azar waking at his post on the first night.
using System.Collections;
using UnityEngine;

namespace Wakefire
{
    public static class IntroTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["intro"] = Run;

        static IEnumerator Run(AutoTest t)
        {
            Save.Clear();
            Title.Show();
            yield return t.Shot("00-title", 1.2f);
            Object.Destroy(Title.I.gameObject);
            DialogueBox.AutoAdvance = 1.6f;
            Game.I.Begin(false);
            yield return t.Shot("01-card", 2.0f);
            yield return t.Shot("02-card", 3.4f);
            yield return t.Shot("03-card", 5.0f);
            yield return t.Shot("04-card", 5.6f);
            yield return t.Shot("05-asleep-at-his-post", 5.4f);
            yield return t.Shot("06-first-line", 4.2f);
            yield return t.Shot("07-quiet", 3.0f);
            yield return t.Shot("08-the-rule", 6.5f);
            yield return t.Shot("09-lesson", 5.0f);
        }
    }
}
