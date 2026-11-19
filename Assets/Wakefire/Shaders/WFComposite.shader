// Puts the night together on the display: the pixel world multiplied by the light layer
// (moonlit ambient plus torch rings), so fire pools warm the stone and the rest stays blue.
// Inside the dream there is no night: the world shows at full strength.
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
            float4 _WF_RTWorld;   // world camera centre xy, world size of the render target zw
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
                return fixed4(lit, 1);
            }
            ENDCG
        }
    }
}
