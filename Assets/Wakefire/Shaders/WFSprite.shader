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
        _Model ("Drawn from the model stage (1 body, 2 cast shadow)", Float) = 0
        _Cell ("Square of the model stage (uv origin, uv size)", Vector) = (0,0,0,0)
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
                float _Model;
                float4 _Cell;
            CBUFFER_END
            TEXTURE2D(_WFModels);          // sampler_PointClamp comes with Core.hlsl
            float4 _WFModels_TexelSize;
            float4 _WF_StagePivot;         // where a model's feet stand in its square (uv)

            // The same figure laid over on the ground, away from the moon: for each pixel of ground,
            // which part of the standing figure would be in the way of the light?
            half ModelShadow(float2 uv)
            {
                float2 cellPx = _Cell.zw * _WFModels_TexelSize.zw;
                float2 px = floor(uv * cellPx) + 0.5 - _WF_StagePivot.xy * cellPx;
                float up = px.y / -0.40;
                float along = px.x - 0.66 * up;
                float2 suv = _WF_StagePivot.xy + float2(along, up) / cellPx;
                if (up < 0.0 || suv.x < 0.01 || suv.x > 0.99 || suv.y > 0.99) return 0;
                float2 p = (floor((_Cell.xy + suv * _Cell.zw) * _WFModels_TexelSize.zw) + 0.5) * _WFModels_TexelSize.xy;
                return SAMPLE_TEXTURE2D(_WFModels, sampler_PointClamp, p).a;
            }

            // A character posed on the model stage, read out of its square of the stage sheet and
            // inked: a dark line round the outside, and a line wherever one part of the body
            // passes in front of another (the sheet's alpha is depth).
            half4 ModelPixel(float2 uv)
            {
                float2 t = _WFModels_TexelSize.xy;
                float2 p = (floor((_Cell.xy + uv * _Cell.zw) * _WFModels_TexelSize.zw) + 0.5) * t;
                half4 m = SAMPLE_TEXTURE2D(_WFModels, sampler_PointClamp, p);
                half4 a = SAMPLE_TEXTURE2D(_WFModels, sampler_PointClamp, p + float2(t.x, 0));
                half4 b = SAMPLE_TEXTURE2D(_WFModels, sampler_PointClamp, p - float2(t.x, 0));
                half4 c = SAMPLE_TEXTURE2D(_WFModels, sampler_PointClamp, p + float2(0, t.y));
                half4 d = SAMPLE_TEXTURE2D(_WFModels, sampler_PointClamp, p - float2(0, t.y));
                if (m.a < 0.25)
                {
                    half4 best = a.a > b.a ? a : b;
                    best = c.a > best.a ? c : best;
                    best = d.a > best.a ? d : best;
                    if (best.a < 0.25) return half4(0, 0, 0, 0);
                    return half4(best.rgb * float3(0.16, 0.13, 0.24) + float3(0.012, 0.010, 0.026), 1);
                }
                float nearest = min(min(a.a < 0.25 ? 1.0 : a.a, b.a < 0.25 ? 1.0 : b.a), min(c.a < 0.25 ? 1.0 : c.a, d.a < 0.25 ? 1.0 : d.a));
                float crease = step(0.030, m.a - nearest);
                return half4(m.rgb * lerp(float3(1, 1, 1), float3(0.42, 0.36, 0.52), crease), 1);
            }

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
                float bayer = WF_Bayer(i.positionCS.xy);
                clip(bayer - _Dissolve - 0.0001);
                float dream = WF_DreamAt(i.world);
                float vis = _Layer < 0.5 ? 1 : (_Layer < 1.5 ? 1 - dream : dream);
                clip(vis - 0.5);
                if (_Model > 1.5)
                {
                    clip(ModelShadow(i.uv) - 0.25);
                    return half4(0.012, 0.014, 0.05, 0.58);
                }
                half4 c;
                if (_Model > 0.5) c = ModelPixel(i.uv) * i.color;
                else c = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, i.uv) * i.color;
                clip(c.a - 0.5);
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
