// Azar's portrait for the cover: the big title-screen figure, saved straight off the model
// stage with its depth in the alpha (the outline is inked afterwards). Run with -wfScene portrait.
using System.Collections;
using System.IO;
using UnityEngine;

namespace Wakefire
{
    public static class PortraitTest
    {
        [RuntimeInitializeOnLoadMethod(RuntimeInitializeLoadType.BeforeSceneLoad)]
        static void Register() => AutoTest.Scenes["portrait"] = Run;

        static IEnumerator Run(AutoTest t)
        {
            var host = new GameObject("Portrait");
            host.transform.position = (Vector2)PixelView.I.world.transform.position;
            var body = new GameObject("Sprite");
            body.transform.SetParent(host.transform, false);
            var sr = body.AddComponent<SpriteRenderer>();
            sr.sharedMaterial = Map.SpriteMat;
            sr.enabled = false;
            var anim = body.AddComponent<SpriteAnim>();
            anim.sr = sr;
            anim.modelAs = "azar_title";
            anim.sheet = SpriteSheet.Load("azar");
            anim.Play("idle", Facing.Right, true);
            var m = anim.model;
            m.ownVelocity = true;
            m.velocity = new Vector2(2.8f, 0.5f);
            string[] names = { "threequarter", "front", "side" };
            Vector2[] aims = { new Vector2(0.8f, -0.6f), new Vector2(0.15f, -1f), new Vector2(1f, 0.1f) };
            for (int i = 0; i < names.Length; i++)
            {
                m.Aim(aims[i], true);
                for (float c = 0; c < 2.2f; c += Time.deltaTime) { anim.Tick(Time.deltaTime); yield return null; }
                yield return new WaitForEndOfFrame();
                var rt = ModelStage.I.sheet;
                var cell = m.Cell;
                var rect = new Rect(cell.x * rt.width, cell.y * rt.height, cell.z * rt.width, cell.w * rt.height);
                var prev = RenderTexture.active;
                RenderTexture.active = rt;
                var tex = new Texture2D((int)rect.width, (int)rect.height, TextureFormat.RGBA32, false);
                tex.ReadPixels(rect, 0, 0);
                tex.Apply();
                RenderTexture.active = prev;
                File.WriteAllBytes(Path.Combine(t.dir, $"azar-{names[i]}.png"), tex.EncodeToPNG());
            }
        }
    }
}
