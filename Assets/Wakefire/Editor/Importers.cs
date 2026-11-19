// Import rules: textures and UI art stay pixel-crisp (point filter, no compression, no mips);
// models from Blender come in with legacy animations, vertex colours and no materials.
using UnityEditor;
using UnityEngine;

namespace Wakefire.EditorTools
{
    public class Importers : AssetPostprocessor
    {
        public override uint GetVersion() => 7;

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
            t.alphaIsTransparency = true;
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
