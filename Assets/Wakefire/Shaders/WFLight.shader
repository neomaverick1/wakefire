// A light drawn into the light layer: warm stepped rings (pixel-art falloff) with a little
// dither between steps, added on top of the moonlit ambient.
Shader "Wakefire/Light"
{
    Properties
    {
        _Color ("Colour", Color) = (1, 0.6, 0.3, 1)
        _Steps ("Steps", Float) = 5
    }
    SubShader
    {
        Tags { "Queue"="Transparent" "RenderType"="Transparent" "RenderPipeline"="UniversalPipeline" }
        Cull Off ZWrite Off ZTest Always
        Blend One One

        Pass
        {
            Tags { "LightMode"="UniversalForward" }
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "WF2D.hlsl"

            CBUFFER_START(UnityPerMaterial)
                float4 _Color;
                float _Steps;
            CBUFFER_END

            struct A { float4 positionOS : POSITION; float2 uv : TEXCOORD0; float4 color : COLOR; };
            struct V { float4 positionCS : SV_POSITION; float2 uv : TEXCOORD0; float4 color : COLOR; };

            V vert(A i)
            {
                V o;
                o.positionCS = TransformObjectToHClip(i.positionOS.xyz);
                o.uv = i.uv;
                o.color = i.color;
                return o;
            }

            half4 frag(V i) : SV_Target
            {
                float d = length(i.uv * 2 - 1);
                float f = saturate(1 - d);
                f = f * f * (3 - 2 * f);
                float q = floor(f * _Steps + 0.5 + (WF_Bayer(i.positionCS.xy) - 0.5) * 0.5) / _Steps;
                return half4(_Color.rgb * i.color.rgb * i.color.a * q, 1);
            }
            ENDHLSL
        }
    }
}
