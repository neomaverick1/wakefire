// The studio. Every 3D character in the game stands in its own square of a hidden stage, far
// from the map, and one camera photographs them all into a single low-resolution sheet at the
// game's own pixel size. The sprite shader then draws each actor from its square, so the dream
// ring, hit flashes and y-sorting treat a posed model exactly like a drawn sprite.
//
// The lens looks level; each model is tipped towards it by the camera pitch instead, which for
// a flat (orthographic) picture is the same thing as looking down on the scene.
using UnityEngine;
using UnityEngine.Rendering.Universal;

namespace Wakefire
{
    public class ModelStage : MonoBehaviour
    {
        public static ModelStage I;
        public const int Layer = 12;
        public const int Cell = 128;              // pixels along one square
        public const int Cols = 8, Rows = 8;
        public const int FeetPx = 36;             // where a model's feet stand, above the bottom of its square
        public const float Pitch = 30f;           // how far the camera looks down on the world
        public const float DepthRange = 4.5f;
        const float CellU = Cell / PixelView.PPU;
        static readonly Vector3 Home = new Vector3(4000, -9000, 0);

        public RenderTexture sheet;
        Camera cam;
        readonly ModelActor[] squares = new ModelActor[Cols * Rows];
        static readonly Sprite[] blanks = new Sprite[4];

        public static ModelStage Ensure()
        {
            if (I) return I;
            var go = new GameObject("ModelStage");
            DontDestroyOnLoad(go);
            go.transform.position = Home;
            I = go.AddComponent<ModelStage>();
            I.Build();
            return I;
        }

        void Build()
        {
            sheet = new RenderTexture(Cols * Cell, Rows * Cell, 24, RenderTextureFormat.ARGB32)
            {
                name = "WF Models", filterMode = FilterMode.Point, wrapMode = TextureWrapMode.Clamp, antiAliasing = 1, useMipMap = false,
            };
            sheet.Create();
            var go = new GameObject("StageCamera");
            go.transform.SetParent(transform, false);
            go.transform.localPosition = new Vector3(0, 0, -40);
            cam = go.AddComponent<Camera>();
            cam.orthographic = true;
            cam.orthographicSize = Rows * CellU / 2f;
            cam.aspect = Cols / (float)Rows;
            cam.nearClipPlane = 1f;
            cam.farClipPlane = 80f;
            cam.clearFlags = CameraClearFlags.SolidColor;
            cam.backgroundColor = new Color(0, 0, 0, 0);
            cam.cullingMask = 1 << Layer;
            cam.allowMSAA = false;
            cam.allowHDR = false;
            cam.depth = -50;                       // before the world camera, every frame
            cam.targetTexture = sheet;
            var d = cam.GetUniversalAdditionalCameraData();
            d.renderPostProcessing = false;
            d.antialiasing = AntialiasingMode.None;
            d.renderShadows = false;
            d.SetRenderer(1);
            Shader.SetGlobalTexture("_WFModels", sheet);
            Shader.SetGlobalVector("_WF_StageDepth", new Vector4(Home.z, 1f / DepthRange, 0, 0));
            Shader.SetGlobalVector("_WF_StagePivot", new Vector4(0.5f, FeetPx / (float)Cell, 0, 0));
        }

        /// <summary>A free square (or block of span x span squares) for an actor; -1 if the stage is full.</summary>
        public int Take(ModelActor a, int span)
        {
            for (int r = 0; r + span <= Rows; r++)
                for (int c = 0; c + span <= Cols; c++)
                {
                    bool free = true;
                    for (int y = 0; y < span && free; y++)
                        for (int x = 0; x < span && free; x++)
                            if (squares[(r + y) * Cols + c + x]) free = false;
                    if (!free) continue;
                    for (int y = 0; y < span; y++)
                        for (int x = 0; x < span; x++)
                            squares[(r + y) * Cols + c + x] = a;
                    return r * Cols + c;
                }
            return -1;
        }

        public void Give(ModelActor a)
        {
            for (int i = 0; i < squares.Length; i++) if (squares[i] == a) squares[i] = null;
        }

        /// <summary>Where a model's feet go on the stage (local to the stage).</summary>
        public Vector3 Feet(int square, int span)
        {
            int c = square % Cols, r = square / Cols;
            return new Vector3((c + span * 0.5f) * CellU - Cols * CellU * 0.5f, r * CellU + span * FeetPx / PixelView.PPU - Rows * CellU * 0.5f, 0);
        }

        /// <summary>The square as a rectangle of the sheet (uv origin, uv size).</summary>
        public Vector4 Rect(int square, int span)
        {
            int c = square % Cols, r = square / Cols;
            return new Vector4(c / (float)Cols, r / (float)Rows, span / (float)Cols, span / (float)Rows);
        }

        /// <summary>A blank sprite the size of a square, pivoted at the feet, for the actor's renderer to carry.</summary>
        public static Sprite Blank(int span)
        {
            if (blanks[span]) return blanks[span];
            var t = new Texture2D(2, 2) { filterMode = FilterMode.Point, name = "WF blank" };
            t.SetPixels(new[] { Color.clear, Color.clear, Color.clear, Color.clear });
            t.Apply();
            blanks[span] = Sprite.Create(t, new Rect(0, 0, 2, 2), new Vector2(0.5f, FeetPx / (float)Cell), 2f / (span * CellU), 0, SpriteMeshType.FullRect);
            return blanks[span];
        }
    }
}
