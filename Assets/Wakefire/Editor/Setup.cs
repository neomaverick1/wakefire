// One-time project setup, run from the command line:
//   Unity -batchmode -quit -projectPath . -executeMethod Wakefire.EditorTools.Setup.Run
// Configures the render pipeline (outline + 15-bit passes, a plain renderer for the pixel HUD),
// materials, post-processing, layers, the empty scene and the app's identity. Safe to re-run.
using System.IO;
using System.Linq;
using System.Reflection;
using UnityEditor;
using UnityEditor.Build;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;
using UnityEngine.Rendering.Universal;

namespace Wakefire.EditorTools
{
    public static class Setup
    {
        const string Root = "Assets/Wakefire";
        public const string Id = "com.neomaverick.wakefire";

        public static void Run()
        {
            Layers();
            var mats = Materials();
            Pipeline(mats.outline, mats.quantize);
            Volume();
            Scene();
            Player();
            AssetDatabase.SaveAssets();
            Debug.Log("[setup] done");
        }

        static void Layers()
        {
            var tm = new SerializedObject(AssetDatabase.LoadAllAssetsAtPath("ProjectSettings/TagManager.asset")[0]);
            var layers = tm.FindProperty("layers");
            void Set(int i, string n) { layers.GetArrayElementAtIndex(i).stringValue = n; }
            Set(6, "PixelUI");
            Set(7, "Actor");
            Set(8, "Trigger");
            Set(9, "Ground");
            Set(10, "Hitbox");
            Set(11, "Light");
            tm.ApplyModifiedProperties();
        }

        static Material SaveMat(string name, Shader s, System.Action<Material> init = null)
        {
            string path = $"{Root}/Resources/Materials/{name}.mat";
            var m = AssetDatabase.LoadAssetAtPath<Material>(path);
            if (!m)
            {
                m = new Material(s) { name = name };
                AssetDatabase.CreateAsset(m, path);
            }
            m.shader = s;
            init?.Invoke(m);
            EditorUtility.SetDirty(m);
            return m;
        }

        static (Material outline, Material quantize) Materials()
        {
            Directory.CreateDirectory($"{Root}/Resources/Materials");
            var toon = Shader.Find("Wakefire/Toon");
            if (!toon) throw new System.Exception("Wakefire/Toon didn't compile");
            SaveMat("Toon", toon, m => { m.DisableKeyword("_TRIPLANAR"); m.SetFloat("_Triplanar", 0); });
            SaveMat("ToonTri", toon, m => { m.EnableKeyword("_TRIPLANAR"); m.SetFloat("_Triplanar", 1); });
            foreach (var s in new[] { "Wakefire/Sprite", "Wakefire/Light", "Wakefire/Composite" })
            {
                var sh = Shader.Find(s);
                if (sh) SaveMat(s.Substring(9), sh);
            }
            var outline = SaveMat("Outline", Shader.Find("Wakefire/Outline"));
            var quant = SaveMat("Quantize", Shader.Find("Wakefire/Quantize"));
            return (outline, quant);
        }

        static void Pipeline(Material outlineMat, Material quantMat)
        {
            var asset = AssetDatabase.LoadAssetAtPath<UniversalRenderPipelineAsset>("Assets/Settings/Mobile_RPAsset.asset");
            var rd = AssetDatabase.LoadAssetAtPath<UniversalRendererData>("Assets/Settings/Mobile_Renderer.asset");

            foreach (var f in rd.rendererFeatures.ToArray()) if (f) Object.DestroyImmediate(f, true);
            rd.rendererFeatures.Clear();
            FullScreenPassRendererFeature Feature(string n, Material m, FullScreenPassRendererFeature.InjectionPoint at, ScriptableRenderPassInput req)
            {
                var f = ScriptableObject.CreateInstance<FullScreenPassRendererFeature>();
                f.name = n;
                f.passMaterial = m;
                f.injectionPoint = at;
                f.requirements = req;
                f.fetchColorBuffer = true;
                AssetDatabase.AddObjectToAsset(f, rd);
                rd.rendererFeatures.Add(f);
                return f;
            }
            // the game is 2D pixel art now: outlines are drawn into the sprites, so no full-screen passes
            typeof(ScriptableRendererData).GetMethod("UpdateMap", BindingFlags.NonPublic | BindingFlags.Instance)?.Invoke(rd, null);
            rd.depthPrimingMode = DepthPrimingMode.Disabled;
            rd.renderingMode = RenderingMode.Forward;
            EditorUtility.SetDirty(rd);

            // a plain renderer for the pixel HUD camera (no outline, no dither)
            const string uiPath = "Assets/Settings/WF_UI_Renderer.asset";
            var uiRd = AssetDatabase.LoadAssetAtPath<UniversalRendererData>(uiPath);
            if (!uiRd)
            {
                uiRd = ScriptableObject.CreateInstance<UniversalRendererData>();
                uiRd.postProcessData = null;
                AssetDatabase.CreateAsset(uiRd, uiPath);
            }

            var so = new SerializedObject(asset);
            var list = so.FindProperty("m_RendererDataList");
            list.arraySize = 2;
            list.GetArrayElementAtIndex(0).objectReferenceValue = rd;
            list.GetArrayElementAtIndex(1).objectReferenceValue = uiRd;
            so.FindProperty("m_DefaultRendererIndex").intValue = 0;
            so.FindProperty("m_RequireDepthTexture").boolValue = false;
            so.FindProperty("m_SupportsHDR").boolValue = false;
            so.FindProperty("m_MSAA").intValue = 1;
            so.FindProperty("m_RenderScale").floatValue = 1f;
            so.FindProperty("m_MainLightShadowsSupported").boolValue = false;
            so.FindProperty("m_MainLightShadowmapResolution").intValue = 2048;
            so.FindProperty("m_AdditionalLightsRenderingMode").intValue = 1;
            so.FindProperty("m_AdditionalLightsPerObjectLimit").intValue = 8;
            so.FindProperty("m_ShadowDistance").floatValue = 60f;
            so.FindProperty("m_ShadowCascadeCount").intValue = 1;
            so.FindProperty("m_SoftShadowsSupported").boolValue = false;
            so.FindProperty("m_ShadowDepthBias").floatValue = 1.0f;
            so.FindProperty("m_ShadowNormalBias").floatValue = 0.6f;
            so.FindProperty("m_UseAdaptivePerformance").boolValue = false;
            so.FindProperty("m_SupportsLightCookies").boolValue = false;
            so.ApplyModifiedProperties();
            EditorUtility.SetDirty(asset);

            GraphicsSettings.defaultRenderPipeline = asset;
            int levels = QualitySettings.names.Length;
            for (int i = 0; i < levels; i++)
            {
                QualitySettings.SetQualityLevel(i, false);
                QualitySettings.renderPipeline = asset;
                QualitySettings.vSyncCount = 0;
                QualitySettings.antiAliasing = 0;
            }
            QualitySettings.SetQualityLevel(0, false);
        }

        static void Volume()
        {
            const string path = Root + "/Resources/WFVolume.asset";
            var p = AssetDatabase.LoadAssetAtPath<VolumeProfile>(path);
            if (p) AssetDatabase.DeleteAsset(path);
            p = ScriptableObject.CreateInstance<VolumeProfile>();
            AssetDatabase.CreateAsset(p, path);
            var bloom = p.Add<Bloom>(true);
            bloom.threshold.Override(1.0f);
            bloom.intensity.Override(0.9f);
            bloom.scatter.Override(0.55f);
            bloom.highQualityFiltering.Override(false);
            var tm = p.Add<Tonemapping>(true);
            tm.mode.Override(TonemappingMode.None);
            var ca = p.Add<ColorAdjustments>(true);
            ca.contrast.Override(8f);
            ca.saturation.Override(6f);
            foreach (var c in p.components) AssetDatabase.AddObjectToAsset(c, p);
            EditorUtility.SetDirty(p);
        }

        static void Scene()
        {
            const string path = "Assets/Scenes/Main.unity";
            Directory.CreateDirectory("Assets/Scenes");
            if (!File.Exists(path))
            {
                var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                EditorSceneManager.SaveScene(scene, path);
            }
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(path, true) };
        }

        static void Player()
        {
            PlayerSettings.companyName = "Randy Kundinger";
            PlayerSettings.productName = "Wakefire";
            foreach (var t in new[] { NamedBuildTarget.Android, NamedBuildTarget.iOS, NamedBuildTarget.Standalone, NamedBuildTarget.WebGL })
                PlayerSettings.SetApplicationIdentifier(t, Id);
            PlayerSettings.defaultInterfaceOrientation = UIOrientation.AutoRotation;
            PlayerSettings.allowedAutorotateToPortrait = false;
            PlayerSettings.allowedAutorotateToPortraitUpsideDown = false;
            PlayerSettings.allowedAutorotateToLandscapeLeft = true;
            PlayerSettings.allowedAutorotateToLandscapeRight = true;
            PlayerSettings.runInBackground = true;
            PlayerSettings.resizableWindow = true;
            PlayerSettings.fullScreenMode = FullScreenMode.Windowed;
            PlayerSettings.defaultScreenWidth = 1280;
            PlayerSettings.defaultScreenHeight = 720;
            PlayerSettings.visibleInBackground = true;
            PlayerSettings.colorSpace = ColorSpace.Linear;
            PlayerSettings.SplashScreen.backgroundColor = new Color32(6, 5, 12, 255);
            PlayerSettings.SplashScreen.unityLogoStyle = PlayerSettings.SplashScreen.UnityLogoStyle.LightOnDark;
            PlayerSettings.SplashScreen.animationMode = PlayerSettings.SplashScreen.AnimationMode.Dolly;

            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Standalone, ScriptingImplementation.Mono2x);
            PlayerSettings.SetScriptingBackend(NamedBuildTarget.Android, ScriptingImplementation.IL2CPP);
            PlayerSettings.Android.targetArchitectures = AndroidArchitecture.ARM64;
            PlayerSettings.Android.minSdkVersion = AndroidSdkVersions.AndroidApiLevel26;
            PlayerSettings.Android.renderOutsideSafeArea = true;
            PlayerSettings.iOS.targetOSVersionString = "15.0";
            PlayerSettings.iOS.requiresFullScreen = true;
            PlayerSettings.iOS.appleEnableAutomaticSigning = false;
            PlayerSettings.statusBarHidden = true;
            foreach (var t in new[] { NamedBuildTarget.Android, NamedBuildTarget.iOS, NamedBuildTarget.WebGL })
            {
                PlayerSettings.SetManagedStrippingLevel(t, ManagedStrippingLevel.Medium);
                PlayerSettings.SetIl2CppCodeGeneration(t, Il2CppCodeGeneration.OptimizeSize);
            }
            PlayerSettings.bundleVersion = "1.0.0";
            PlayerSettings.Android.bundleVersionCode = 1;
            PlayerSettings.iOS.buildNumber = "1";
        }
    }
}
