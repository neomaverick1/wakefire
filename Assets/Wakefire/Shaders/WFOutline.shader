// Full-screen pass at the game's native low resolution: a 1-pixel dark line wherever a surface
// sits in front of something much farther away (silhouettes), and a 1-pixel light line on
// convex creases (roof edges, steps, armour plates). Runs before bloom and grading.
Shader "Wakefire/Outline"
{
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }
        ZWrite Off Cull Off ZTest Always

        Pass
        {
            Name "Outline"
            HLSLPROGRAM
            #pragma vertex Vert
            #pragma fragment frag
            #pragma multi_compile_fragment _ _GBUFFER_NORMALS_OCT
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
            #include "Packages/com.unity.render-pipelines.core/Runtime/Utilities/Blit.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareDepthTexture.hlsl"
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/DeclareNormalsTexture.hlsl"

            float4 _WF_Outline;       // x depth threshold (m), y outline darkness, z crease brightness, w crease threshold
            float4 _WF_OutlineTint;   // colour mixed into outlines

            float EyeDepth(float2 uv)
            {
                float raw = SampleSceneDepth(uv);
            #if UNITY_REVERSED_Z
                raw = 1.0 - raw;
            #endif
                return lerp(_ProjectionParams.y, _ProjectionParams.z, raw);
            }

            half4 frag(Varyings input) : SV_Target
            {
                float2 uv = input.texcoord;
                float2 ts = 1.0 / _ScaledScreenParams.xy;
                float3 col = SAMPLE_TEXTURE2D_X(_BlitTexture, sampler_PointClamp, uv).rgb;

                float d = EyeDepth(uv);
                float2 o[4] = { float2(-ts.x, 0), float2(ts.x, 0), float2(0, ts.y), float2(0, -ts.y) };
                float depthDiff = 0;
                float creases = 0;
                float3 n = SampleSceneNormals(uv);
                [unroll] for (int k = 0; k < 4; k++)
                {
                    float dn = EyeDepth(uv + o[k]);
                    depthDiff += max(0, dn - d);
                    float3 nn = SampleSceneNormals(uv + o[k]);
                    float nd = 1.0 - saturate(dot(n, nn));
                    // only light the side of the crease that faces up/towards the moon
                    float bias = smoothstep(-0.02, 0.02, dot(n - nn, float3(0.3, 1.0, -0.4)));
                    float flat = step(abs(dn - d), _WF_Outline.x * 0.6);
                    creases += nd * bias * flat;
                }

                if (d < _ProjectionParams.z * 0.999)
                {
                    if (depthDiff > _WF_Outline.x)
                        col = col * _WF_Outline.y + _WF_OutlineTint.rgb;
                    else if (creases > _WF_Outline.w)
                        col = col * _WF_Outline.z + 0.012;
                }
                return half4(col, 1);
            }
            ENDHLSL
        }
    }
}
