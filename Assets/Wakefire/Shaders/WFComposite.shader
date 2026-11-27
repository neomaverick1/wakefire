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
        _GlowTex ("Glow", 2D) = "black" {}
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

            sampler2D _LightTex;
            sampler2D _GlowTex;      // what burns, blurred small (WFEmber)
            float _Strength;
            float4 _WF_Bends[4];     // xy = where (world), z = how wide, w = how strong (pixels)
            float _WF_BendCount;

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
                float2 uv = i.uv;
                float2 here = _WF_RTWorld.xy + (uv - 0.5) * _WF_RTWorld.zw;
                float2 push = 0;
                float haze = 0, rim = 0;
                for (int b = 0; b < 4; b++)
                {
                    float4 B = _WF_Bends[b];
                    float2 d = here - B.xy;
                    float r = length(d) / max(B.z, 0.001);
                    float on = step(r, 1.0) * step(b + 0.5, _WF_BendCount);
                    float f = sin(saturate(r) * 3.14159);
                    float wob = 0.72 + 0.28 * sin(_Time.y * 9.0 - r * 7.0);
                    push += normalize(d + 0.0001) * f * f * wob * B.w * on;
                    haze += f * on;
                    // the edge of it: a broken ring that goes round
                    float ang = atan2(d.y, d.x) + _Time.y * 1.7;
                    rim += on * step(0.84, r) * step(0.35, frac(ang * 0.955));
                }
                uv += floor(push + 0.5) * _MainTex_TexelSize.xy;
                float3 w = tex2D(_MainTex, uv).rgb;
                float3 l = tex2D(_LightTex, uv).rgb;
                float3 lit = w * lerp(float3(1, 1, 1), l, _Strength);
                // the dream is lit from within: no night, the fires still glow
                float2 wp = _WF_RTWorld.xy + (i.uv - 0.5) * _WF_RTWorld.zw;
                float dream = WF_DreamAt(wp);
                float3 dlit = w * max(l, float3(0.96, 0.94, 1.0));
                lit = lerp(lit, dlit, dream);
                // light above 1 blooms gently towards warm white instead of clipping
                float3 over = max(lit - 1, 0);
                lit = min(lit, 1) + over * float3(0.6, 0.45, 0.3);

                // the glow of fire, laid softly over everything near it
                lit += tex2D(_GlowTex, i.uv).rgb * float3(1.15, 0.94, 0.62);

                // bent air is a breath colder and paler than the air round it, and has an edge you can just see
                lit = lerp(lit, lit * float3(0.90, 0.98, 1.12) + float3(0.02, 0.03, 0.05), saturate(haze) * 0.55);
                lit += saturate(rim) * float3(0.10, 0.12, 0.16) * step(0.5, WF_Bayer(uv * _MainTex_TexelSize.zw));

                // the corners fall away into the night
                float2 q = i.uv - 0.5;
                lit *= 1.0 - smoothstep(0.16, 0.56, dot(q, q)) * 0.34;
                return fixed4(min(lit, 1), 1);
            }
            ENDCG
        }
    }
}
