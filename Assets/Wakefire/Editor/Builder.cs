// Builds the game for each platform from the command line.
//   Unity -batchmode -quit -projectPath . -executeMethod Wakefire.EditorTools.Builder.Linux
// Android signing comes from WAKEFIRE_KEYSTORE (a path), WAKEFIRE_KEYSTORE_PASS, WAKEFIRE_KEY_ALIAS
// and WAKEFIRE_KEY_PASS when they're set; otherwise the debug key signs it.
using System;
using System.IO;
using System.Reflection;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEngine;

namespace Wakefire.EditorTools
{
    public static class Builder
    {
        static string[] Scenes => new[] { "Assets/Scenes/Main.unity" };

        static string Version()
        {
            var v = Environment.GetEnvironmentVariable("WAKEFIRE_VERSION");
            return string.IsNullOrEmpty(v) ? PlayerSettings.bundleVersion : v;
        }

        static void Run(BuildTarget target, BuildTargetGroup group, string path, BuildOptions options = BuildOptions.None)
        {
            PlayerSettings.bundleVersion = Version();
            var parts = Version().Split('.');
            // 1.3.0 -> 1300, 2.0.0 -> 2000: every release's number is higher than the last, so a phone will install it over the old one
            if (parts.Length == 3 && int.TryParse(parts[2], out int patch) && int.TryParse(parts[1], out int minor) && int.TryParse(parts[0], out int major))
            {
                PlayerSettings.Android.bundleVersionCode = major * 1000 + minor * 100 + patch;
                PlayerSettings.iOS.buildNumber = (major * 1000 + minor * 100 + patch).ToString();
            }
            ApplyIconAndSplash();
            Models.Build();
            if (EditorUserBuildSettings.activeBuildTarget != target) EditorUserBuildSettings.SwitchActiveBuildTarget(group, target);
            Directory.CreateDirectory(Path.GetDirectoryName(Path.GetFullPath(path)));
            var report = BuildPipeline.BuildPlayer(new BuildPlayerOptions
            {
                scenes = Scenes,
                locationPathName = path,
                target = target,
                targetGroup = group,
                options = options,
            });
            var s = report.summary;
            Debug.Log($"[build] {target}: {s.result}, {s.totalSize / 1048576f:0.0} MB, {s.totalTime.TotalSeconds:0}s, {s.totalErrors} errors");
            if (s.result != BuildResult.Succeeded) EditorApplication.Exit(1);
        }

        /// <summary>The lantern icon everywhere, and straight into the game (no engine splash).</summary>
        static void ApplyIconAndSplash()
        {
            var icon = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Wakefire/Icon/icon_512.png");
            if (icon) PlayerSettings.SetIcons(UnityEditor.Build.NamedBuildTarget.Unknown, new[] { icon }, IconKind.Any);
            PlayerSettings.SplashScreen.show = false;
            PlayerSettings.SplashScreen.showUnityLogo = false;
        }

        public static void Linux() => Run(BuildTarget.StandaloneLinux64, BuildTargetGroup.Standalone, "Builds/Linux/Wakefire.x86_64");

        static void Sign()
        {
            var ks = Environment.GetEnvironmentVariable("WAKEFIRE_KEYSTORE");
            if (string.IsNullOrEmpty(ks) || !File.Exists(ks))
            {
                PlayerSettings.Android.useCustomKeystore = false;
                return;
            }
            PlayerSettings.Android.useCustomKeystore = true;
            PlayerSettings.Android.keystoreName = ks;
            PlayerSettings.Android.keystorePass = Environment.GetEnvironmentVariable("WAKEFIRE_KEYSTORE_PASS");
            PlayerSettings.Android.keyaliasName = Environment.GetEnvironmentVariable("WAKEFIRE_KEY_ALIAS");
            PlayerSettings.Android.keyaliasPass = Environment.GetEnvironmentVariable("WAKEFIRE_KEY_PASS");
        }

        /// <summary>Android 8+ masks icons into circles and squircles: give it the night sky and the
        /// lantern as separate layers so the launcher can shape them cleanly. Found by reflection
        /// so this file still compiles on machines without the Android module.</summary>
        static void AdaptiveIcon()
        {
            Type kindType = null;
            foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
                if ((kindType = asm.GetType("UnityEditor.Android.AndroidPlatformIconKind")) != null) break;
            if (kindType == null) { Debug.Log("[build] adaptive icon skipped (no Android module)"); return; }
            var member = (object)kindType.GetProperty("Adaptive", BindingFlags.Public | BindingFlags.Static)?.GetValue(null)
                         ?? kindType.GetField("Adaptive", BindingFlags.Public | BindingFlags.Static)?.GetValue(null);
            if (!(member is PlatformIconKind adaptive)) { Debug.Log("[build] adaptive icon kind not found"); return; }
            var bg = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Wakefire/Icon/icon_bg_432.png");
            var fg = AssetDatabase.LoadAssetAtPath<Texture2D>("Assets/Wakefire/Icon/icon_fg_432.png");
            if (!bg || !fg) return;
            var target = UnityEditor.Build.NamedBuildTarget.Android;
            var icons = PlayerSettings.GetPlatformIcons(target, adaptive);
            foreach (var ic in icons) ic.SetTextures(bg, fg);
            PlayerSettings.SetPlatformIcons(target, adaptive, icons);
            Debug.Log($"[build] adaptive icon set ({icons.Length} sizes)");
        }

        /// <summary>Gradle's share of the build machine's memory. Unity hands it four gigabytes by default,
        /// which is more than a small build machine has left once the editor has the project open: the
        /// daemon is killed halfway and the build fails with "daemon disappeared". Found by reflection so
        /// this file still compiles on machines without the Android module.</summary>
        static void GradleHeap()
        {
            int mb = int.TryParse(Environment.GetEnvironmentVariable("WAKEFIRE_GRADLE_HEAP"), out int v) && v >= 512 ? v : 1536;
            foreach (var asm in AppDomain.CurrentDomain.GetAssemblies())
            {
                var t = asm.GetType("UnityEditor.Android.AndroidExternalToolsSettings");
                if (t == null) continue;
                var prop = t.GetProperty("maxJvmHeapSize", BindingFlags.Public | BindingFlags.Static);
                if (prop == null) { Debug.Log("[build] Gradle heap: no such setting in this editor"); return; }
                prop.SetValue(null, mb);
                Debug.Log($"[build] Gradle heap {prop.GetValue(null)} MB");
                return;
            }
            Debug.Log("[build] Gradle heap not set (no Android module)");
        }

        public static void Android()
        {
            Sign();
            AdaptiveIcon();
            GradleHeap();
            EditorUserBuildSettings.buildAppBundle = false;
            Run(BuildTarget.Android, BuildTargetGroup.Android, "Builds/Android/Wakefire.apk");
        }

        public static void AndroidBundle()
        {
            Sign();
            AdaptiveIcon();
            GradleHeap();
            EditorUserBuildSettings.buildAppBundle = true;
            Run(BuildTarget.Android, BuildTargetGroup.Android, "Builds/Android/Wakefire-Play.aab");
            EditorUserBuildSettings.buildAppBundle = false;
        }

        public static void IOS() => Run(BuildTarget.iOS, BuildTargetGroup.iOS, "Builds/iOS");

        public static void Web()
        {
            if (Directory.Exists("Assets/WebGLTemplates/Wakefire")) PlayerSettings.WebGL.template = "PROJECT:Wakefire";
            PlayerSettings.WebGL.compressionFormat = WebGLCompressionFormat.Brotli;
            PlayerSettings.WebGL.decompressionFallback = true;
            PlayerSettings.WebGL.dataCaching = true;
            PlayerSettings.WebGL.exceptionSupport = WebGLExceptionSupport.None;
            Run(BuildTarget.WebGL, BuildTargetGroup.WebGL, "Builds/Web");
        }
    }
}
