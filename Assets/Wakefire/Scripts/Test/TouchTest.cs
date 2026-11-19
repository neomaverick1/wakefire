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
        }
    }
}
