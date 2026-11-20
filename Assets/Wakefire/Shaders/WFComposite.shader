// Puts the night together on the display: the pixel world multiplied by the light layer
// (moonlit ambient plus torch rings), so fire pools warm the stone and the rest stays blue.
// Inside the dream there is no night: the world shows at full strength.
// Anything fiery (flames, the Wakefire, molten eyes, bright gold, the dream ring) throws a soft
// glow, and the corners of the picture fall away a little into the dark.
Shader "Wakefire/Composite"
{
    Properties
    {
        [PerRendererData] _MainTex ("World", 2D) = "white" {}
        _LightTex ("Light", 2D) = "white" {}
        _Strength ("Night strength", Float) = 1
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" "IgnoreProjector"="True" }
        Cull Off ZWrite Off ZTest Always
        Blend Off

        Pass
        {
            CGPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "UnityCG.cginc"
            #include "WF2D.hlsl"

            sampler2D _MainTex;
            float4 _MainTex_TexelSize;
            float4 _WF_RTWorld;   // world camera centre xy, world size of the render target zw

            // how much a pixel burns: bright and strongly warm-coloured, or not at all
            float3 Ember(float2 uv)
            {
                float3 c = tex2D(_MainTex, uv).rgb;
                float hi = max(c.r, max(c.g, c.b)), lo = min(c.r, min(c.g, c.b));
                float sat = hi > 0.001 ? (hi - lo) / hi : 0;
                return c * smoothstep(0.70, 0.92, hi) * smoothstep(0.74, 0.90, sat) * step(c.b, c.r);
            }
            sampler2D _LightTex;
            float _Strength;

            struct A { float4 vertex : POSITION; float2 uv : TEXCOORD0; float4 color : COLOR; };
            struct V { float4 pos : SV_POSITION; float2 uv : TEXCOORD0; };

            V vert(A i)
            {
                V o;
                o.pos = UnityObjectToClipPos(i.vertex);
                o.uv = i.uv;
                return o;
            }

            fixed4 frag(V i) : SV_Target
            {
                float3 w = tex2D(_MainTex, i.uv).rgb;
                float3 l = tex2D(_LightTex, i.uv).rgb;
                float3 lit = w * lerp(float3(1, 1, 1), l, _Strength);
                // the dream is lit from within: no night, the fires still glow
                float2 wp = _WF_RTWorld.xy + (i.uv - 0.5) * _WF_RTWorld.zw;
                float dream = WF_DreamAt(wp);
                float3 dlit = w * max(l, float3(0.96, 0.94, 1.0));
                lit = lerp(lit, dlit, dream);
                // light above 1 blooms gently towards warm white instead of clipping
                float3 over = max(lit - 1, 0);
                lit = min(lit, 1) + over * float3(0.6, 0.45, 0.3);

                // the glow of fire: two rings of samples round each pixel, the nearer weighing more
                float2 t = _MainTex_TexelSize.xy;
                float3 glow = 0;
                glow += (Ember(i.uv + t * float2(1.5, 0)) + Ember(i.uv + t * float2(-1.5, 0)) + Ember(i.uv + t * float2(0, 1.5)) + Ember(i.uv + t * float2(0, -1.5))) * 0.11;
                glow += (Ember(i.uv + t * float2(1.1, 1.1)) + Ember(i.uv + t * float2(-1.1, 1.1)) + Ember(i.uv + t * float2(1.1, -1.1)) + Ember(i.uv + t * float2(-1.1, -1.1))) * 0.10;
                glow += (Ember(i.uv + t * float2(3.2, 0)) + Ember(i.uv + t * float2(-3.2, 0)) + Ember(i.uv + t * float2(0, 3.2)) + Ember(i.uv + t * float2(0, -3.2))) * 0.045;
                glow += (Ember(i.uv + t * float2(2.3, 2.3)) + Ember(i.uv + t * float2(-2.3, 2.3)) + Ember(i.uv + t * float2(2.3, -2.3)) + Ember(i.uv + t * float2(-2.3, -2.3))) * 0.045;
                lit += glow * float3(1.0, 0.82, 0.55);

                // the corners fall away into the night
                float2 q = i.uv - 0.5;
                lit *= 1.0 - smoothstep(0.16, 0.56, dot(q, q)) * 0.34;
                return fixed4(min(lit, 1), 1);
            }
            ENDCG
        }
    }
}
