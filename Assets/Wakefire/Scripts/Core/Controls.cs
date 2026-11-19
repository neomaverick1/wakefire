// Every way to play: keyboard, gamepad, and the on-screen controls (which drive a virtual
// gamepad), read through one set of actions. Buffered presses make combos and rolls feel tight.
using UnityEngine;
using UnityEngine.InputSystem;

namespace Wakefire
{
    public static class Controls
    {
        public static InputAction Move, Attack, Roll, Nod, Interact, Item, Pause, Confirm, Back;
        static bool ready;
        public static bool Enabled = true;

        public static void Init()
        {
            if (ready) return;
            ready = true;
            Move = new InputAction("Move", InputActionType.Value);
            Move.AddCompositeBinding("2DVector").With("Up", "<Keyboard>/w").With("Down", "<Keyboard>/s").With("Left", "<Keyboard>/a").With("Right", "<Keyboard>/d");
            Move.AddCompositeBinding("2DVector").With("Up", "<Keyboard>/upArrow").With("Down", "<Keyboard>/downArrow").With("Left", "<Keyboard>/leftArrow").With("Right", "<Keyboard>/rightArrow");
            Move.AddBinding("<Gamepad>/leftStick");
            Move.AddBinding("<Gamepad>/dpad");

            Attack = Button("Attack", "<Keyboard>/j", "<Keyboard>/space", "<Mouse>/leftButton", "<Gamepad>/buttonWest");
            Roll = Button("Roll", "<Keyboard>/k", "<Keyboard>/leftShift", "<Gamepad>/buttonEast");
            Nod = Button("Nod", "<Keyboard>/l", "<Keyboard>/q", "<Gamepad>/buttonNorth");
            Interact = Button("Interact", "<Keyboard>/e", "<Keyboard>/enter", "<Gamepad>/buttonSouth");
            Item = Button("Item", "<Keyboard>/i", "<Keyboard>/f", "<Mouse>/rightButton", "<Gamepad>/rightShoulder");
            Pause = Button("Pause", "<Keyboard>/escape", "<Keyboard>/p", "<Gamepad>/start");
            Confirm = Button("Confirm", "<Keyboard>/enter", "<Keyboard>/space", "<Keyboard>/e", "<Keyboard>/j", "<Gamepad>/buttonSouth", "<Gamepad>/buttonWest", "<Mouse>/leftButton");
            Back = Button("Back", "<Keyboard>/escape", "<Keyboard>/backspace", "<Gamepad>/buttonEast");
            foreach (var a in new[] { Move, Attack, Roll, Nod, Interact, Item, Pause, Confirm, Back }) a.Enable();
        }

        static InputAction Button(string name, params string[] paths)
        {
            var a = new InputAction(name, InputActionType.Button);
            foreach (var p in paths) a.AddBinding(p);
            return a;
        }

        /// <summary>Test runs steer Azar through here instead of a stick.</summary>
        public static Vector2? Fake;

        public static Vector2 MoveVector
        {
            get
            {
                if (Fake.HasValue) return Fake.Value;
                if (!Enabled) return Vector2.zero;
                var v = Move.ReadValue<Vector2>();
                return v.sqrMagnitude > 1 ? v.normalized : v;
            }
        }

        public static bool Down(InputAction a) => Enabled && a.WasPressedThisFrame();
        public static bool Held(InputAction a) => Enabled && a.IsPressed();
        public static bool Up(InputAction a) => Enabled && a.WasReleasedThisFrame();
    }
}
