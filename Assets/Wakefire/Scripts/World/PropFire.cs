// A fire bowl that has been lit can be put out again (by something whose trade that is). Out,
// it is exactly the bowl it was before: cold, waiting, and anything that was answering to its
// fire stops answering.
using UnityEngine;

namespace Wakefire
{
    public partial class Prop
    {
        int coldPx = int.MinValue, coldPy;

        /// <summary>Put a lit fire bowl out. False if it was not one, or was not burning.</summary>
        public bool Snuff()
        {
            if (Kind != "brazier" || !lit) return false;
            lit = false;
            frames = null;
            if (coldPx != int.MinValue) { data.px = coldPx; data.py = coldPy; }
            sr.sprite = Map.GetSprite(data.s, data.px, data.py);
            if (data.n != 0) Map.Normals(sr, data.s + "_lin");
            if (glow) { Destroy(glow.gameObject); glow = null; }
            if (!string.IsNullOrEmpty(data.id)) Story.Clear("on_" + data.id);
            for (int i = 0; i < 10; i++)
                Fx.Spawn(basePos + new Vector2(Random.Range(-0.2f, 0.2f), 0), new Vector2(Random.Range(-0.3f, 0.3f), 0.2f), 1.0f, Random.Range(0.5f, 1.4f),
                    Random.Range(0.6f, 1.1f), new Color(0.66f, 0.64f, 0.66f, 0.9f), new Color(0.28f, 0.27f, 0.30f, 0f), -0.7f, i % 3 == 0 ? 2 : 1);
            return true;
        }
    }
}
