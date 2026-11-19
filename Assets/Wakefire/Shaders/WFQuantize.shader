// Last full-screen pass: quantise to 15-bit colour (32 levels a channel) with a 4x4 ordered
// dither, the way 32-bit consoles drew gradients, plus a soft vignette.
Shader "Wakefire/Quantize"
{
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }
        ZWrite Off Cull Off ZTest Always

        Pass
        {
            Name "Quantize"
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl"
            #include "WFCommon.hlsl"

            float4 _WF_Grade; // x levels, y vignette, z saturation, w unused

            half4 frag(Varyings input) : SV_Target
            {
                float2 uv = input.texcoord;
                float3 c = SAMPLE_TEXTURE2D_X(_BlitTexture, sampler_PointClamp, uv).rgb;
                float l = WF_Luma(c);
                c = lerp(l.xxx, c, _WF_Grade.z);
                float2 v = uv - 0.5;
                c *= 1.0 - dot(v, v) * _WF_Grade.y;
                float3 s = LinearToSRGB(saturate(c));
                float levels = max(_WF_Grade.x, 2.0);
                float b = (WF_Bayer(input.positionCS.xy) - 0.5) * 0.7;
                s = floor(s * levels + 0.5 + b) / levels;
                return half4(SRGBToLinear(saturate(s)), 1);
            }
            ENDHLSL
        }
    }
}
