// Wakefire's surface shader: banded "pixel art" lighting from the moon and from every torch,
// hard shadows, ordered dither on the band edges, bronze highlights, emissive fire,
// the waking/dream repaint, the travelling flip ring and the see-through circle around Azar.
// Albedo comes from vertex colours (models) or from point-sampled world-space textures (_TRIPLANAR).
Shader "Wakefire/Toon"
{
    Properties
    {
        _BaseColor ("Tint", Color) = (1,1,1,1)
        _TopTex ("Top texture", 2D) = "white" {}
        _SideTex ("Side texture", 2D) = "white" {}
        _TexDensity ("Texels per metre", Float) = 20
        _Layer ("World layer (0 both, 1 waking, 2 dream)", Float) = 0
        _Occluder ("Fades around the player", Float) = 0
        _WindAmt ("Wind sway", Float) = 0
        _Emission ("Emission strength", Float) = 2.5
        _DreamGlow ("Extra glow in the dream", Float) = 0
        _Flash ("Hit flash", Float) = 0
        _FlashColor ("Hit flash colour", Color) = (1,1,1,1)
        _Dissolve ("Dissolve", Float) = 0
        [Toggle(_TRIPLANAR)] _Triplanar ("World-space textures", Float) = 0
    }

    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" "Queue"="Geometry" }

        HLSLINCLUDE
        #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"
        #include "WFCommon.hlsl"

        CBUFFER_START(UnityPerMaterial)
            float4 _BaseColor;
            float4 _TopTex_ST;
            float4 _SideTex_ST;
            float _TexDensity;
            float _Layer;
            float _Occluder;
            float _WindAmt;
            float _Emission;
            float _DreamGlow;
            float _Flash;
            float4 _FlashColor;
            float _Dissolve;
            float _Triplanar;
        CBUFFER_END

        TEXTURE2D(_TopTex); SAMPLER(sampler_TopTex);
        TEXTURE2D(_SideTex); SAMPLER(sampler_SideTex);

        struct Attributes
        {
            float4 positionOS : POSITION;
            float3 normalOS : NORMAL;
            float4 color : COLOR;
            UNITY_VERTEX_INPUT_INSTANCE_ID
        };

        // Wind bends things more the higher they are above their own origin.
        float3 WF_ApplyWind(float3 positionOS, float3 positionWS)
        {
            if (_WindAmt <= 0) return positionWS;
            float h = max(positionOS.y, 0);
            float t = _WF_FlipState.w * _WF_Wind.w;
            float phase = dot(positionWS.xz, float2(0.37, 0.21));
            float sway = sin(t + phase) * 0.6 + sin(t * 2.3 + phase * 1.7) * 0.4;
            positionWS.xz += _WF_Wind.xy * sway * _WF_Wind.z * _WindAmt * h * h * 0.12;
            return positionWS;
        }

        // Shared clip test: wrong world layer, dissolving away, or between the camera and Azar
        // (walls, roofs and trees in front of him open a dithered window so he never disappears).
        void WF_ClipCommon(float3 positionWS, float4 positionCS)
        {
            float bayer = WF_Bayer(positionCS.xy);
            float vis = WF_LayerVisible(_Layer, positionWS);
            clip(vis - 0.5);
            clip(bayer - _Dissolve - 0.0001);
            if (_Occluder > 0.5 && _WF_PlayerPos.w > 0)
            {
                float3 pp = _WF_PlayerPos.xyz + float3(0, 0.9, 0);
                float4 pcs = TransformWorldToHClip(pp);
                float2 puv = pcs.xy / pcs.w * 0.5 + 0.5;
                float4 fcs = TransformWorldToHClip(positionWS);
                float2 fuv = fcs.xy / fcs.w * 0.5 + 0.5;
                float distPx = length((fuv - puv) * _WF_PixelSize.xy);
                float fragDepth = -TransformWorldToView(positionWS).z;
                float plDepth = -TransformWorldToView(pp).z;
                if (fragDepth < plDepth - 0.6 && positionWS.y > _WF_PlayerPos.y + 0.35)
                {
                    float r = _WF_PlayerPos.w;
                    float fade = saturate((r - distPx) / (r * 0.45));
                    clip(bayer - fade * 0.92);
                }
            }
        }
        ENDHLSL

        Pass
        {
            Name "ForwardLit"
            Tags { "LightMode"="UniversalForward" }
            Cull Back
            ZWrite On

            HLSLPROGRAM
            #pragma target 3.0
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile _ _MAIN_LIGHT_SHADOWS _MAIN_LIGHT_SHADOWS_CASCADE
            #pragma multi_compile _ _ADDITIONAL_LIGHTS_VERTEX _ADDITIONAL_LIGHTS
            #pragma multi_compile _ _CLUSTER_LIGHT_LOOP
            #pragma multi_compile_instancing
            #pragma shader_feature_local _TRIPLANAR
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Lighting.hlsl"

            struct Varyings
            {
                float4 positionCS : SV_POSITION;
                float3 positionWS : TEXCOORD0;
                float3 normalWS : TEXCOORD1;
                float4 color : TEXCOORD2;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            Varyings vert(Attributes input)
            {
                Varyings o = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_TRANSFER_INSTANCE_ID(input, o);
                float3 ws = TransformObjectToWorld(input.positionOS.xyz);
                ws = WF_ApplyWind(input.positionOS.xyz, ws);
                o.positionWS = ws;
                o.positionCS = TransformWorldToHClip(ws);
                o.normalWS = TransformObjectToWorldNormal(input.normalOS);
                o.color = input.color;
                return o;
            }

            float3 SampleAlbedo(Varyings i, float3 n)
            {
                float3 vc = SRGBToLinear(i.color.rgb);
                float3 albedo = vc * _BaseColor.rgb;
            #if defined(_TRIPLANAR)
                float3 an = abs(n);
                float3 p = i.positionWS * _TexDensity / 64.0; // textures are 64 texels wide
                float3 tex;
                if (an.y >= an.x && an.y >= an.z)
                    tex = SAMPLE_TEXTURE2D(_TopTex, sampler_TopTex, p.xz).rgb;
                else if (an.x >= an.z)
                    tex = SAMPLE_TEXTURE2D(_SideTex, sampler_SideTex, float2(p.z, p.y)).rgb;
                else
                    tex = SAMPLE_TEXTURE2D(_SideTex, sampler_SideTex, float2(p.x, p.y)).rgb;
                albedo *= tex;
            #endif
                return albedo;
            }

            half4 frag(Varyings i) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(i);
                WF_ClipCommon(i.positionWS, i.positionCS);
                float bayer = WF_Bayer(i.positionCS.xy);

                float3 n = normalize(i.normalWS);
                float3 albedo = SampleAlbedo(i, n);
                float mtype = i.color.a;
                float dream = WF_DreamAt(i.positionWS);

                // moonlight: three bands with a dithered terminator and hard shadows
                float4 shadowCoord = TransformWorldToShadowCoord(i.positionWS);
                Light mainLight = GetMainLight(shadowCoord);
                float ndl = dot(n, mainLight.direction);
                float raw = ndl * mainLight.shadowAttenuation;
                float jitter = (bayer - 0.5) * 0.22;
                float band = (raw + jitter > 0.38) ? 1.0 : ((raw + jitter > 0.02) ? 0.55 : 0.0);
                float3 ambient = WF_Ambient(n, dream);
                float3 lightSum = ambient + mainLight.color * band;

                float3 viewDir = normalize(GetWorldSpaceViewDir(i.positionWS));
                float metal = (mtype > 0.4 && mtype < 0.8) ? 1.0 : 0.0;
                float3 spec = 0;
                if (metal > 0)
                {
                    float3 h = normalize(mainLight.direction + viewDir);
                    float s = pow(saturate(dot(n, h)), 28.0) * mainLight.shadowAttenuation;
                    spec += mainLight.color * step(0.45 - jitter * 0.5, s) * 0.9;
                }

                // torches, braziers and windows: stepped warm rings with dithered steps
                InputData inputData = (InputData)0;
                inputData.positionWS = i.positionWS;
                inputData.normalizedScreenSpaceUV = GetNormalizedScreenSpaceUV(i.positionCS);
                uint lightCount = GetAdditionalLightsCount();
                LIGHT_LOOP_BEGIN(lightCount)
                    Light l = GetAdditionalLight(lightIndex, i.positionWS, half4(1, 1, 1, 1));
                    float wrap = saturate(dot(n, l.direction) * 0.6 + 0.4);
                    float a = l.distanceAttenuation * wrap;
                    float q = floor(saturate(a * 1.15) * 5.0 + 0.5 + (bayer - 0.5) * 0.4) / 5.0;
                    float3 lc = l.color;
                    lc = lerp(lc, float3(lc.b * 0.6, lc.r * 0.9, lc.g * 1.3), dream);
                    lightSum += lc * q;
                    if (metal > 0)
                    {
                        float3 h2 = normalize(l.direction + viewDir);
                        float s2 = pow(saturate(dot(n, h2)), 20.0) * a;
                        spec += lc * step(0.35, s2) * 0.8;
                    }
                LIGHT_LOOP_END

                float3 col = albedo * lightSum + spec * (albedo * 0.6 + 0.4);
                if (mtype < 0.15) col = albedo * _Emission;              // fire, embers, lit windows

                // the dream repaints the world; dream-only things glow a little
                float3 dreamCol = WF_DreamPalette(col) * 1.08 + albedo * _DreamGlow;
                col = lerp(col, dreamCol, dream);
                col += float3(1.0, 0.72, 0.28) * WF_RingAt(i.positionWS) * 2.2;
                col = WF_Fog(col, i.positionWS, dream);
                col = lerp(col, _FlashColor.rgb * 2.0, saturate(_Flash));
                return half4(col, 1);
            }
            ENDHLSL
        }

        Pass
        {
            Name "ShadowCaster"
            Tags { "LightMode"="ShadowCaster" }
            ZWrite On
            ZTest LEqual
            ColorMask 0
            Cull Back

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #pragma multi_compile_vertex _ _CASTING_PUNCTUAL_LIGHT_SHADOW
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Shadows.hlsl"

            float3 _LightDirection;
            float3 _LightPosition;

            struct Varyings { float4 positionCS : SV_POSITION; float3 positionWS : TEXCOORD0; };

            Varyings vert(Attributes input)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(input);
                float3 ws = TransformObjectToWorld(input.positionOS.xyz);
                ws = WF_ApplyWind(input.positionOS.xyz, ws);
                float3 nws = TransformObjectToWorldNormal(input.normalOS);
            #if _CASTING_PUNCTUAL_LIGHT_SHADOW
                float3 ld = normalize(_LightPosition - ws);
            #else
                float3 ld = _LightDirection;
            #endif
                float4 cs = TransformWorldToHClip(ApplyShadowBias(ws, nws, ld));
            #if UNITY_REVERSED_Z
                cs.z = min(cs.z, UNITY_NEAR_CLIP_VALUE);
            #else
                cs.z = max(cs.z, UNITY_NEAR_CLIP_VALUE);
            #endif
                o.positionCS = cs;
                o.positionWS = ws;
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                clip(WF_LayerVisible(_Layer, i.positionWS) - 0.5);
                clip(0.5 - _Dissolve);
                return 0;
            }
            ENDHLSL
        }

        Pass
        {
            Name "DepthOnly"
            Tags { "LightMode"="DepthOnly" }
            ZWrite On
            ColorMask R
            Cull Back

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing

            struct Varyings { float4 positionCS : SV_POSITION; float3 positionWS : TEXCOORD0; };

            Varyings vert(Attributes input)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(input);
                float3 ws = TransformObjectToWorld(input.positionOS.xyz);
                ws = WF_ApplyWind(input.positionOS.xyz, ws);
                o.positionWS = ws;
                o.positionCS = TransformWorldToHClip(ws);
                return o;
            }

            half frag(Varyings i) : SV_Target
            {
                WF_ClipCommon(i.positionWS, i.positionCS);
                return i.positionCS.z;
            }
            ENDHLSL
        }

        Pass
        {
            Name "DepthNormals"
            Tags { "LightMode"="DepthNormals" }
            ZWrite On
            Cull Back

            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing
            #pragma multi_compile_fragment _ _GBUFFER_NORMALS_OCT

            struct Varyings { float4 positionCS : SV_POSITION; float3 positionWS : TEXCOORD0; float3 normalWS : TEXCOORD1; };

            Varyings vert(Attributes input)
            {
                Varyings o;
                UNITY_SETUP_INSTANCE_ID(input);
                float3 ws = TransformObjectToWorld(input.positionOS.xyz);
                ws = WF_ApplyWind(input.positionOS.xyz, ws);
                o.positionWS = ws;
                o.positionCS = TransformWorldToHClip(ws);
                o.normalWS = TransformObjectToWorldNormal(input.normalOS);
                return o;
            }

            half4 frag(Varyings i) : SV_Target
            {
                WF_ClipCommon(i.positionWS, i.positionCS);
                float3 n = normalize(i.normalWS);
            #if defined(_GBUFFER_NORMALS_OCT)
                float2 oct = PackNormalOctQuadEncode(n);
                float2 rem = saturate(oct * 0.5 + 0.5);
                return half4(PackFloat2To888(rem), 0.0);
            #else
                return half4(n, 0.0);
            #endif
            }
            ENDHLSL
        }
    }
}
