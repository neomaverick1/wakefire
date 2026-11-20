// A posed 3D character photographed for the sprite sheet. Flat colour in a few hard bands
// (deep shade, shade, base, light, and a glint on metal), lit by one fixed studio lamp, so every
// character is shaded the same way whichever way they turn. A cool rim from behind picks the
// figure out of the night. Alpha carries depth, so the sprite shader can ink a line where an
// arm crosses a chest.
Shader "Wakefire/Model"
{
    Properties
    {
        _BaseMap ("Texture", 2D) = "white" {}
        _Color ("Colour", Color) = (1,1,1,1)
        _Metal ("Metal glint", Range(0,1)) = 0
        _Glow ("Unlit", Range(0,1)) = 0
        _Rim ("Rim light", Range(0,1)) = 1
        _Both ("Seen from both sides (cloth)", Float) = 0
        _Fire ("Firelight: direction to it (view space), strength", Vector) = (0,1,0,0)
        _FireColor ("Firelight colour", Color) = (1,0.62,0.26,1)
        [Enum(UnityEngine.Rendering.CullMode)] _Cull ("Cull", Float) = 2
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "Queue"="Geometry" "RenderPipeline"="UniversalPipeline" }
        Pass
        {
            Tags { "LightMode"="UniversalForward" }
            Cull [_Cull] ZWrite On ZTest LEqual Blend Off
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            TEXTURE2D(_BaseMap); SAMPLER(sampler_BaseMap);
            CBUFFER_START(UnityPerMaterial)
                float4 _BaseMap_ST;
                float4 _Color;
                float _Metal;
                float _Glow;
                float _Rim;
                float _Both;
                float4 _Fire;
                float4 _FireColor;
                float _Cull;
            CBUFFER_END
            float4 _WF_StageDepth;   // x = z of the stage floor line, y = 1 / depth range

            // colour and the metal/glow flags are per face, not blended across it: paint stays in hard blocks
            struct A { float4 positionOS : POSITION; float3 normalOS : NORMAL; float2 uv : TEXCOORD0; float2 flags : TEXCOORD1; float4 color : COLOR; };
            struct V { float4 positionCS : SV_POSITION; float3 normalVS : TEXCOORD0; float2 uv : TEXCOORD1; nointerpolation float4 color : COLOR; float depth : TEXCOORD2; nointerpolation float2 flags : TEXCOORD3; };

            V vert(A i)
            {
                V o;
                float3 ws = TransformObjectToWorld(i.positionOS.xyz);
                o.positionCS = TransformWorldToHClip(ws);
                o.normalVS = TransformWorldToViewDir(TransformObjectToWorldNormal(i.normalOS), false);
                o.uv = TRANSFORM_TEX(i.uv, _BaseMap);
                o.color = i.color;
                o.flags = i.flags;
                o.depth = (ws.z - _WF_StageDepth.x) * _WF_StageDepth.y + 0.5;
                return o;
            }

            half4 frag(V i) : SV_Target
            {
                float3 n = normalize(i.normalVS);
                if (_Both > 0.5 && n.z < -0.15) n = -n;      // the far side of cloth is lit as it faces the lens
                float metal = max(_Metal, i.flags.x), glow = max(_Glow, i.flags.y);
                float3 base = SAMPLE_TEXTURE2D(_BaseMap, sampler_BaseMap, i.uv).rgb * _Color.rgb * i.color.rgb;

                // view space: x right, y up, z towards the lens
                float3 L = normalize(float3(-0.52, 0.70, 0.49));
                float d = dot(n, L);
                float3 deep = base * float3(0.19, 0.16, 0.30);
                float3 shade = base * float3(0.44, 0.40, 0.60);
                float3 light = min(base * float3(1.38, 1.30, 1.10) + float3(0.025, 0.02, 0.0), 1.0);
                float3 col = d > 0.60 ? light : (d > 0.12 ? base : (d > -0.34 ? shade : deep));

                // moonlight from behind and to the right, only where the lamp doesn't reach
                float rim = dot(n, normalize(float3(0.80, 0.30, -0.52)));
                if (rim > 0.50 && d < 0.12) col = lerp(col, base * float3(0.62, 0.74, 1.05) + float3(0.02, 0.04, 0.09), _Rim);

                // firelight: whatever burns nearby (a brazier, the Wakefire itself) paints the side that faces it
                float fire = dot(n, normalize(_Fire.xyz));
                if (_Fire.w > 0.02 && fire > 0.28)
                    col = lerp(col, min(base * _FireColor.rgb * 1.55 + _FireColor.rgb * 0.08, 1.0), _Fire.w * (fire > 0.62 ? 1.0 : 0.55));

                // bronze catches the lamp
                float3 H = normalize(L + float3(0, 0, 1));
                float spec = dot(n, H);
                if (metal > 0.01 && spec > lerp(1.0, 0.962, metal)) col = lerp(light, float3(1.0, 0.88, 0.52), 0.55);

                col = lerp(col, base, glow);
                return half4(col, 0.5 + 0.5 * saturate(i.depth));
            }
            ENDHLSL
        }
    }
}
