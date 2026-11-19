// Every sprite and the ground: crisp alpha-tested pixels, hit flash, dissolve, and the
// waking/dream flip (the dream repaints colours inside/outside the travelling ring; dream-only
// and waking-only things appear and vanish as the ring passes).
Shader "Wakefire/Sprite"
{
    Properties
    {
        [PerRendererData] _MainTex ("Sprite", 2D) = "white" {}
        _Color ("Tint", Color) = (1,1,1,1)
        _Layer ("World layer (0 both, 1 waking, 2 dream)", Float) = 0
        _Flash ("Flash", Float) = 0
        _FlashColor ("Flash colour", Color) = (1,1,1,1)
        _Dissolve ("Dissolve", Float) = 0
        _DreamGlow ("Dream glow", Float) = 0
        _DreamKeep ("Keep own colours in the dream", Float) = 0
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" "IgnoreProjector"="True" "PreviewType"="Plane" }
        Cull Off ZWrite Off ZTest Always
        Blend SrcAlpha OneMinusSrcAlpha

        Pass
        {
            Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "WF2D.hlsl"

            TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);
            CBUFFER_START(UnityPerMaterial)
                float4 _MainTex_ST;
                float4 _Color;
                float _Layer;
                float _Flash;
                float4 _FlashColor;
                float _Dissolve;
                float _DreamGlow;
                float _DreamKeep;
            CBUFFER_END

            struct A { float4 positionOS : POSITION; float2 uv : TEXCOORD0; float4 color : COLOR; };
            struct V { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; float4 color : COLOR; float2 world : TEXCOORD1; };

            V vert(A i)
            {
                V o;
                float3 ws = TransformObjectToWorld(i.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(ws);
                o.uv = i.uv;
                o.color = i.color * _Color;
                o.world = ws.xy;
                return o;
            }

            half4 frag(V i) : SV_Target
            {
                half4 c = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, i.uv) * i.color;
                clip(c.a - 0.5);
                float bayer = WF_Bayer(i.positionCS.xy);
                clip(bayer - _Dissolve - 0.0001);
                float dream = WF_DreamAt(i.world);
                float vis = _Layer < 0.5 ? 1 : (_Layer < 1.5 ? 1 - dream : dream);
                clip(vis - 0.5);
                float3 col = c.rgb;
                float3 dcol = lerp(WF_DreamPalette(col) + col * _DreamGlow, col * 1.08, _DreamKeep);
                col = lerp(col, dcol, dream);
                col = lerp(col, float3(1.0, 0.55, 0.14), saturate(WF_RingAt(i.world)));
                col = lerp(col, _FlashColor.rgb, saturate(_Flash));
                return half4(col, 1);
            }
            ENDHLSL
        }
    }
}
