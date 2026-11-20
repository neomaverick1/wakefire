// Moon shadows. Everything that stands up (a tree, a pillar, a house, a person) throws its own
// shape across the ground, away from the moon: a drawn sprite is simply laid over (sheared) and
// filled with shade; a figure from the model stage is looked up the other way round (for each
// pixel of ground, which part of the standing figure is in the way of the light?).
// The stencil stops shadows stacking: where two overlap, the ground is shaded once.
Shader "Wakefire/Shade"
{
    Properties
    {
        [PerRendererData] _MainTex ("Sprite", 2D) = "white" {}
        _Layer ("World layer (0 both, 1 waking, 2 dream)", Float) = 0
        _Model ("Cast by a figure on the model stage", Float) = 0
        _Cell ("Square of the model stage (uv origin, uv size)", Vector) = (0,0,0,0)
        _Sway ("Sway in the wind", Float) = 0
        _Flat ("The sprite is already the shadow's shape on the ground", Float) = 0
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" "IgnoreProjector"="True" }
        Cull Off ZWrite Off ZTest Always
        Blend SrcAlpha OneMinusSrcAlpha
        Stencil { Ref 1 Comp NotEqual Pass Replace }

        Pass
        {
            Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "WF2D.hlsl"

            TEXTURE2D(_MainTex); SAMPLER(sampler_MainTex);
            TEXTURE2D(_WFModels);
            float4 _WFModels_TexelSize;
            float4 _WF_StagePivot;
            CBUFFER_START(UnityPerMaterial)
                float4 _MainTex_ST;
                float _Layer;
                float _Model;
                float4 _Cell;
                float _Sway;
                float _Flat;
            CBUFFER_END

            // how far a shadow runs for each unit of height: along the ground to the right, and down the screen
            static const float2 Cast = float2(0.66, 0.40);

            struct A { float4 positionOS : POSITION; float2 uv : TEXCOORD0; };
            struct V { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; float2 world : TEXCOORD1; };

            V vert(A i)
            {
                V o;
                float3 p = i.positionOS.xyz;
                if (_Model < 0.5 && _Flat < 0.5)
                {
                    float h = max(p.y, 0.0);
                    float3 base = TransformObjectToWorld(float3(0, 0, 0));
                    p.x += _Sway * h * sin(_Time.y * 1.1 + base.x * 0.35 + base.y * 0.2);
                    p.x += Cast.x * h;
                    p.y -= (1.0 + Cast.y) * h;
                }
                float3 ws = TransformObjectToWorld(p);
                o.positionCS = TransformWorldToHClip(ws);
                o.uv = i.uv;
                o.world = ws.xy;
                return o;
            }

            half4 frag(V i) : SV_Target
            {
                float dream = WF_DreamAt(i.world);
                float vis = _Layer < 0.5 ? 1 : (_Layer < 1.5 ? 1 - dream : dream);
                clip(vis - 0.5);
                half a;
                if (_Model > 0.5)
                {
                    float2 cellPx = _Cell.zw * _WFModels_TexelSize.zw;
                    float2 px = floor(i.uv * cellPx) + 0.5 - _WF_StagePivot.xy * cellPx;
                    float up = px.y / -Cast.y;
                    float along = px.x - Cast.x * up;
                    float2 suv = _WF_StagePivot.xy + float2(along, up) / cellPx;
                    if (up < 0.0 || suv.x < 0.01 || suv.x > 0.99 || suv.y > 0.99) discard;
                    float2 p = (floor((_Cell.xy + suv * _Cell.zw) * _WFModels_TexelSize.zw) + 0.5) * _WFModels_TexelSize.xy;
                    a = SAMPLE_TEXTURE2D(_WFModels, sampler_PointClamp, p).a;
                    clip(a - 0.25);
                }
                else
                {
                    a = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, i.uv).a;
                    clip(a - 0.5);
                }
                // deeper in the dream, where the light is stranger
                return half4(lerp(float3(0.012, 0.014, 0.05), float3(0.05, 0.01, 0.10), dream), 0.5);
            }
            ENDHLSL
        }
    }
}
