// Phone controls check (run with -touch): a simulated thumb lands on the left of the screen, the
// stick appears under it and Azar walks; then a tap on the khopesh button swings it.
using System.Collections;
using UnityEngine;
using UnityEngine.InputSystem;
using UnityEngine.InputSystem.LowLevel;

namespace Wakefire
{
    public static class TouchTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["touch"] = Run;

        static Touchscreen ts;

        static void Touch(int id, UnityEngine.InputSystem.TouchPhase ph, Vector2 at)
        {
            InputSystem.QueueStateEvent(ts, new TouchState { touchId = id, phase = ph, position = at });
        }

        static Vector2 ScreenOf(string name)
        {
            var t = TouchControls.I.transform.Find(name) as RectTransform;
            var c = new Vector3[4];
            t.GetWorldCorners(c);
            return (c[0] + c[2]) * 0.5f;
        }

        static IEnumerator Run(AutoTest t)
        {
            // the build machine's window never has focus; let device events through anyway
            InputSystem.settings.backgroundBehavior = InputSettings.BackgroundBehavior.IgnoreFocus;
            ts = Touchscreen.current ?? InputSystem.AddDevice<Touchscreen>();
            foreach (var d in InputSystem.devices) if (!d.enabled) InputSystem.EnableDevice(d);
            Game.I.EnterMap("ashkel", "south");
            Fade.Set(0);
            yield return new WaitForSeconds(0.8f);
            t.Note("touch controls " + (TouchControls.I ? "on" : "MISSING"));
            yield return t.Shot("t1-layout", 0.2f);
            var p = Player.I;
            float x0 = p.pos.x;
            var at = new Vector2(Screen.width * 0.22f, Screen.height * 0.42f);
            Touch(1, UnityEngine.InputSystem.TouchPhase.Began, at);
            yield return null;
            {
                var es = UnityEngine.EventSystems.EventSystem.current;
                var ped = new UnityEngine.EventSystems.PointerEventData(es) { position = at };
                var hits = new System.Collections.Generic.List<UnityEngine.EventSystems.RaycastResult>();
                es.RaycastAll(ped, hits);
                t.Note($"es={es?.name} module={es?.currentInputModule?.GetType().Name} hits=" + string.Join(",", hits.ConvertAll(h => h.gameObject.name)));
                t.Note($"touchscreen={ts.deviceId} touches active={ts.touches[0].isInProgress} pos={ts.touches[0].position.ReadValue()}");
                var ring = TouchControls.I.transform.Find("StickZone/StickBase") as RectTransform;
                t.Note("ring at " + (ring ? ring.anchoredPosition.ToString() : "none"));
            }
            for (int i = 1; i <= 10; i++)
            {
                Touch(1, UnityEngine.InputSystem.TouchPhase.Moved, at + new Vector2(i * 12f, 0));
                yield return null;
            }
            yield return new WaitForSeconds(0.6f);
            {
                string pads = "";
                foreach (var g in Gamepad.all) pads += $"[{g.name} enabled={g.enabled} stick={g.leftStick.ReadValue()}]";
                t.Note($"move={Controls.Move.ReadValue<Vector2>()} pads={pads} state={p.state} story={(Story.I ? Story.I.Running : false)} touch1={ts.touches[0].position.ReadValue()} phase={ts.touches[0].phase.ReadValue()}");
                var knob = TouchControls.I.transform.Find("StickZone/Stick") as RectTransform;
                t.Note("knob at " + knob.anchoredPosition);
            }
            yield return t.Shot("t2-thumb-down", 0.0f);
            Touch(1, UnityEngine.InputSystem.TouchPhase.Ended, at + new Vector2(120, 0));
            yield return new WaitForSeconds(0.3f);
            float x1 = p.pos.x;
            t.Note($"walked {x1 - x0:0.00} tiles to the right (want > 0.5)");
            // a tap on the khopesh button
            var btn = ScreenOf("Attack");
            Touch(2, UnityEngine.InputSystem.TouchPhase.Began, btn);
            yield return null;
            yield return null;
            string st = p.anim ? p.anim.anim : "?";
            Touch(2, UnityEngine.InputSystem.TouchPhase.Ended, btn);
            t.Note("after tapping the khopesh button: anim " + st);
            yield return new WaitForSeconds(0.5f);
            // text on screen: the buttons get out of its way, and a tap anywhere turns the page
            t.Note($"buttons showing in play: {TouchControls.Showing}");
            Story.Run(DialogueBox.Say("Azar", "Night forty. Still awake.^Still on watch.", "azar"));
            yield return new WaitForSecondsRealtime(0.9f);
            var cg = TouchControls.I.GetComponent<CanvasGroup>();
            t.Note($"text up: box busy={DialogueBox.I.Busy} buttons showing={TouchControls.Showing} alpha={(cg ? cg.alpha : -1):0.00}  (want False, 0.00)");
            yield return t.Shot("t3-text-no-buttons", 0.1f);
            var mid = new Vector2(Screen.width * 0.5f, Screen.height * 0.6f);
            for (int k = 0; k < 4 && DialogueBox.I.Busy; k++)
            {
                Touch(3, UnityEngine.InputSystem.TouchPhase.Began, mid);
                yield return null; yield return null;
                Touch(3, UnityEngine.InputSystem.TouchPhase.Ended, mid);
                yield return new WaitForSecondsRealtime(0.5f);
            }
            t.Note($"after tapping the middle of the screen: box busy={DialogueBox.I.Busy} (want False)");
            yield return new WaitForSecondsRealtime(0.5f);
            t.Note($"buttons back: {TouchControls.Showing} (want True)");
            // a question: touching an answer chooses it, a tap elsewhere chooses nothing
            Story.Run(DialogueBox.Ask("Kesh", "Forty shekels. Very sacred. Very forty shekels.", "Buy", "Not now", "potter"));
            yield return new WaitForSecondsRealtime(2.2f);
            Touch(4, UnityEngine.InputSystem.TouchPhase.Began, mid);
            yield return null; yield return null;
            Touch(4, UnityEngine.InputSystem.TouchPhase.Ended, mid);
            yield return new WaitForSecondsRealtime(0.4f);
            yield return t.Shot("t4-question", 0.1f);
            t.Note($"question up, stray tap ignored: busy={DialogueBox.I.Busy} (want True)");
            // find "Not now" on the screen: the box draws it at a known place
            var at2 = DialogueBox.I.OptionCentre(1);
            Touch(5, UnityEngine.InputSystem.TouchPhase.Began, at2);
            yield return null; yield return null;
            Touch(5, UnityEngine.InputSystem.TouchPhase.Ended, at2);
            yield return new WaitForSecondsRealtime(0.5f);
            t.Note($"touched 'Not now': busy={DialogueBox.I.Busy} choice={DialogueBox.Choice} (want False, 1)");
        }
    }
}
