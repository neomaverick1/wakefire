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
        _Model ("Drawn from the model stage", Float) = 0
        _Cell ("Square of the model stage (uv origin, uv size)", Vector) = (0,0,0,0)
        _Sway ("Sway in the wind (trees, bushes)", Float) = 0
        [PerRendererData] _NormalTex ("Normals (rgb) and height (a)", 2D) = "bump" {}
        _HasNormal ("Has a normal map", Float) = 0
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
                float _Sway;
                float _HasNormal;
            CBUFFER_END
            float4 _MainTex_TexelSize;
            TEXTURE2D(_NormalTex);
            float4 _WF_Ambient;
            // the fires nearest the camera: xy = where, z = how far the light reaches, w = strength
            float4 _WF_Lights[12];
            float4 _WF_LightColors[12];
            float _WF_LightCount;

            // The light layer treats the world as flat ground: a fire brightens everything inside its
            // rings alike. This puts that right for one pixel whose true shape is known: a wall
            // turned to the fire takes more of it, a wall turned away or a roof above it takes none.
            // Returned as the factor to multiply the pixel by before the light layer does its part.
            float3 FireShape(float3 n, float h, float2 world, float2 pix)
            {
                float bay = (WF_Bayer(pix) - 0.5) * 0.5;
                float3 assumed = _WF_Ambient.rgb, shaped = _WF_Ambient.rgb;
                float3 P = float3(world.x, world.y - h, h);
                for (int k = 0; k < 12; k++)
                {
                    if (k >= _WF_LightCount) break;
                    float4 L = _WF_Lights[k];
                    float f = saturate(1.0 - length(world - L.xy) / L.z);
                    f = f * f * (3.0 - 2.0 * f);
                    float q = max(floor(f * 5.0 + 0.5 + bay), 0.0) / 5.0;
                    float3 b = _WF_LightColors[k].rgb * q;
                    float3 at = float3(L.x, L.y - L.w, L.w);
                    float3 dir = normalize(at - P);
                    float flatZ = normalize(at - float3(world, 0.0)).z;
                    float g = min(saturate(dot(n, dir)) / max(flatZ, 0.05), 1.9);
                    assumed += b;
                    shaped += b * g;
                }
                return shaped / assumed;
            }

            // A figure keeps its own colours beside a fire: the flat wash of the light layer is turned
            // down on it (the model is lit from the fire's side instead, in its own shader).
            float3 FireOnFigure(float2 world, float2 pix)
            {
                float bay = (WF_Bayer(pix) - 0.5) * 0.5;
                float3 sum = 0;
                for (int k = 0; k < 12; k++)
                {
                    if (k >= _WF_LightCount) break;
                    float4 L = _WF_Lights[k];
                    float f = saturate(1.0 - length(world - L.xy) / L.z);
                    f = f * f * (3.0 - 2.0 * f);
                    sum += _WF_LightColors[k].rgb * (max(floor(f * 5.0 + 0.5 + bay), 0.0) / 5.0);
                }
                return (_WF_Ambient.rgb + sum * 0.38) / (_WF_Ambient.rgb + sum);
            }

            TEXTURE2D(_WFModels);          // sampler_PointClamp comes with Core.hlsl
            float4 _WFModels_TexelSize;
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
                // leaves move in the night wind: the top of a tree leans a pixel or so, its foot stays put
                float3 foot = TransformObjectToWorld(float3(0, 0, 0));
                ws.x += _Sway * max(i.positionOS.y, 0.0) * sin(_Time.y * 1.1 + foot.x * 0.35 + foot.y * 0.2);
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
                half4 c;
                if (_Model > 0.5) c = ModelPixel(i.uv) * i.color;
                else c = SAMPLE_TEXTURE2D(_MainTex, sampler_MainTex, i.uv) * i.color;
                clip(c.a - 0.5);
                float3 col = c.rgb;
                if (_Model > 0.5 && _WF_LightCount > 0.5) col *= FireOnFigure(i.world, i.positionCS.xy);
                if (_HasNormal > 0.5)
                {
                    half4 nt = SAMPLE_TEXTURE2D(_NormalTex, sampler_PointClamp, i.uv);
                    float3 n = nt.xyz * 2.0 - 1.0;
                    if (nt.a < 0.002)
                    {
                        // the sea (marked by a zero in the height): moonlight breaking on the swell
                        float2 p = floor(i.world * 16.0) / 16.0;
                        float t = _Time.y;
                        float a = sin(p.x * 2.3 + sin(p.y * 1.7 + t * 0.6) * 1.4 + t * 0.9);
                        float b = sin(p.y * 5.1 - t * 1.1 + sin(p.x * 0.9 + t * 0.4) * 2.0);
                        col += step(1.55, a + b) * float3(0.10, 0.16, 0.26);
                        col *= 1.0 - step(a + b, -1.7) * 0.2;
                    }
                    // flames and lit windows carry no normal: they are light, they don't take it
                    else if (_WF_LightCount > 0.5 && dot(n, n) > 0.25) col *= FireShape(normalize(n), max(nt.a * 255.0 - 1.0, 0.0) / 24.0, i.world, i.positionCS.xy);
                }
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
