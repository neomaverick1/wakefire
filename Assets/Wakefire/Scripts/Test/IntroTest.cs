// The opening on the build machine: title, the cards over black, Azar's first lines.
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
            DialogueBox.AutoAdvance = 1.2f;
            Game.I.Begin(false);
            yield return t.Shot("01-card", 2.2f);
            yield return t.Shot("02-card", 3.6f);
            yield return t.Shot("03-card", 3.6f);
            yield return t.Shot("04-first-frame", 5.0f);
            yield return t.Shot("05-first-line", 2.0f);
            yield return t.Shot("06-tutorial", 5.0f);
        }
    }
}
