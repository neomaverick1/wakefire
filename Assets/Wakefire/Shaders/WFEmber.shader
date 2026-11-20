// The glow of fire, worked out small: what burns in the pixel picture (flames, the Wakefire,
// molten eyes, bright gold, the dream ring) is picked out and blurred at the game's own low
// resolution, then laid over the display by the composite. Two passes: across, then down.
Shader "Hidden/Wakefire/Ember"
{
    Properties { _MainTex ("Source", 2D) = "black" {} }
    SubShader
    {
        Cull Off ZWrite Off ZTest Always

        CGINCLUDE
        #include "UnityCG.cginc"
        sampler2D _MainTex;
        float4 _MainTex_TexelSize;
        struct V { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; };
        V vert(appdata_img i) { V o; o.pos = UnityObjectToClipPos(i.vertex); o.uv = i.texcoord; return o; }

        // how much a pixel burns: bright and strongly warm-coloured, or not at all
        float3 Ember(float2 uv)
        {
            float3 c = tex2D(_MainTex, uv).rgb;
            float hi = max(c.r, max(c.g, c.b)), lo = min(c.r, min(c.g, c.b));
            float sat = hi > 0.001 ? (hi - lo) / hi : 0;
            return c * smoothstep(0.70, 0.92, hi) * smoothstep(0.74, 0.90, sat) * step(c.b, c.r);
        }
        ENDCG

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            fixed4 frag(V i) : SV_Target
            {
                float2 t = float2(_MainTex_TexelSize.x, 0);
                float3 g = Ember(i.uv) * 0.30 + (Ember(i.uv + t) + Ember(i.uv - t)) * 0.22 + (Ember(i.uv + t * 2.4) + Ember(i.uv - t * 2.4)) * 0.13;
                return fixed4(g, 1);
            }
            ENDCG
        }
        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            fixed4 frag(V i) : SV_Target
            {
                float2 t = float2(0, _MainTex_TexelSize.y);
                float3 g = tex2D(_MainTex, i.uv).rgb * 0.30 + (tex2D(_MainTex, i.uv + t).rgb + tex2D(_MainTex, i.uv - t).rgb) * 0.22
                         + (tex2D(_MainTex, i.uv + t * 2.4).rgb + tex2D(_MainTex, i.uv - t * 2.4).rgb) * 0.13;
                return fixed4(g, 1);
            }
            ENDCG
        }
    }
}
