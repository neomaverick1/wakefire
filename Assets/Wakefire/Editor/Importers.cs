// Import rules: textures and UI art stay pixel-crisp (point filter, no compression, no mips);
// models from Blender come in with legacy animations, vertex colours and no materials.
using UnityEditor;
using UnityEngine;

namespace Wakefire.EditorTools
{
    public class Importers : AssetPostprocessor
    {
        public override uint GetVersion() => 9;

        void OnPreprocessAudio()
        {
            if (!assetPath.StartsWith("Assets/Wakefire/Resources/")) return;
            var a = (AudioImporter)assetImporter;
            bool music = assetPath.Contains("/Resources/Music/") || System.IO.Path.GetFileName(assetPath).StartsWith("amb_");
            var s = a.defaultSampleSettings;
            s.loadType = music ? AudioClipLoadType.Streaming : AudioClipLoadType.DecompressOnLoad;
            s.compressionFormat = AudioCompressionFormat.Vorbis;
            s.quality = music ? 0.42f : 0.7f;
            s.sampleRateSetting = AudioSampleRateSetting.PreserveSampleRate;
            s.preloadAudioData = !music;
            a.defaultSampleSettings = s;
            a.forceToMono = !music;
            a.loadInBackground = music;
        }

        void OnPreprocessTexture()
        {
            if (assetPath.StartsWith("Assets/Wakefire/Icon/"))
            {
                var ic = (TextureImporter)assetImporter;
                ic.textureType = TextureImporterType.Default;
                ic.filterMode = FilterMode.Point;
                ic.mipmapEnabled = false;
                ic.textureCompression = TextureImporterCompression.Uncompressed;
                ic.npotScale = TextureImporterNPOTScale.None;
                ic.maxTextureSize = 1024;
                return;
            }
            if (!assetPath.StartsWith("Assets/Wakefire/Resources/")) return;
            var t = (TextureImporter)assetImporter;
            t.filterMode = FilterMode.Point;
            t.mipmapEnabled = false;
            t.textureCompression = TextureImporterCompression.Uncompressed;
            t.npotScale = TextureImporterNPOTScale.None;
            t.alphaIsTransparency = !assetPath.Contains("_lin");      // normal maps keep the height in alpha: don't let the importer repaint them
            t.maxTextureSize = 8192;
            t.isReadable = assetPath.Contains("/Resources/Fonts/");
            if (assetPath.Contains("/Resources/UI/"))
            {
                t.textureType = TextureImporterType.Sprite;
                t.spritePixelsPerUnit = 1;
                t.wrapMode = TextureWrapMode.Clamp;
            }
            else
            {
                t.textureType = TextureImporterType.Default;
                t.wrapMode = TextureWrapMode.Repeat;
                t.sRGBTexture = !assetPath.Contains("_lin");
            }
        }

        void OnPreprocessModel()
        {
            if (assetPath.StartsWith("Assets/Wakefire/Models/"))
            {
                // rigged characters and their clips: the game dresses and colours them itself, so
                // nothing but meshes, bones and motion comes in. Loose gear (Models/Gear) is plain mesh.
                var r = (ModelImporter)assetImporter;
                bool gear = assetPath.Contains("/Gear/");
                r.materialImportMode = ModelImporterMaterialImportMode.None;
                r.animationType = gear ? ModelImporterAnimationType.None : ModelImporterAnimationType.Generic;
                if (!gear) r.avatarSetup = ModelImporterAvatarSetup.CreateFromThisModel;
                r.importAnimation = !gear;
                r.importBlendShapes = false;
                r.importCameras = false;
                r.importLights = false;
                r.importVisibility = false;
                r.meshCompression = ModelImporterMeshCompression.Off;
                r.isReadable = true;                 // the game measures and paints the body when it dresses it
                r.importNormals = ModelImporterNormals.Import;
                r.animationCompression = ModelImporterAnimationCompression.KeyframeReduction;
                r.animationRotationError = 0.4f;
                r.animationPositionError = 0.4f;
                r.animationScaleError = 0.5f;
                r.optimizeGameObjects = false;
                r.useFileScale = true;
                r.globalScale = 1f;
                return;
            }
            if (!assetPath.StartsWith("Assets/Wakefire/Resources/Models/")) return;
            var m = (ModelImporter)assetImporter;
            m.materialImportMode = ModelImporterMaterialImportMode.None;
            m.animationType = ModelImporterAnimationType.Legacy;
            m.importAnimation = true;
            m.bakeAxisConversion = true;
            m.globalScale = 1f;
            m.useFileScale = true;
            m.importBlendShapes = false;
            m.importCameras = false;
            m.importLights = false;
            m.meshCompression = ModelImporterMeshCompression.Off;
            m.isReadable = assetPath.Contains("/Terrain/");
            m.importNormals = ModelImporterNormals.Import;
            m.animationCompression = ModelImporterAnimationCompression.Off;
            m.resampleCurves = false;
        }
    }
}
