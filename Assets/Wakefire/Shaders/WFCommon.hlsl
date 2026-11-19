// Shared helpers for every Wakefire surface: the waking/dream flip, ordered dither,
// dream palette, height fog and the see-through circle around the player.
#ifndef WF_COMMON_INCLUDED
#define WF_COMMON_INCLUDED

// x,y,z = flip centre (world), w = radius of the expanding ring
float4 _WF_Flip;
// x = 1 when the inside of the ring is the dream, 0 when the inside is waking
// y = ring glow strength, z = global dream amount (0..1, for audio-free effects), w = time
float4 _WF_FlipState;
float4 _WF_PlayerPos;      // xyz player position, w = see-through radius in pixels
float4 _WF_AmbSky;         // waking ambient from above
float4 _WF_AmbGround;      // waking ambient from below
float4 _WF_DreamSky;       // dream ambient from above
float4 _WF_DreamGround;    // dream ambient from below
float4 _WF_FogColor;       // rgb, a = height fog start (world y)
float4 _WF_DreamFog;
float4 _WF_Wind;           // xy direction, z strength, w speed
float4 _WF_PixelSize;      // x = render width, y = render height, z = pixels per unit

// 4x4 Bayer threshold in [0,1) for the given pixel
float WF_Bayer(float2 pixel)
{
    uint2 p = uint2(pixel) & 3u;
    const float m[16] = { 0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5 };
    return (m[p.y * 4u + p.x] + 0.5) / 16.0;
}

// 1 where this point of the world is currently in the dream, 0 where it is awake.
float WF_DreamAt(float3 positionWS)
{
    float d = distance(positionWS.xz, _WF_Flip.xz);
    float inside = step(d, _WF_Flip.w);
    return lerp(1.0 - inside, inside, _WF_FlipState.x);
}

// Glow of the travelling ring (0 away from the edge)
float WF_RingAt(float3 positionWS)
{
    float d = distance(positionWS.xz, _WF_Flip.xz);
    float edge = abs(d - _WF_Flip.w);
    return saturate(1.0 - edge / 0.9) * _WF_FlipState.y;
}

// Layer test: layer 0 = both worlds, 1 = waking only, 2 = dream only.
// Returns the dither threshold the fragment must beat to stay visible (clip if < 0).
float WF_LayerVisible(float layer, float3 positionWS)
{
    if (layer < 0.5) return 1.0;
    float dream = WF_DreamAt(positionWS);
    return (layer < 1.5) ? (1.0 - dream) : dream;
}

float WF_Luma(float3 c) { return dot(c, float3(0.299, 0.587, 0.114)); }

// The dream keeps the shapes of the waking world but repaints them: deep violet shadows,
// teal middles and gold highlights, with a little of the original hue left in.
float3 WF_DreamPalette(float3 c)
{
    float l = saturate(WF_Luma(c) * 1.35);
    float3 a = float3(0.055, 0.020, 0.140);   // deep violet
    float3 b = float3(0.060, 0.330, 0.390);   // teal
    float3 g = float3(0.950, 0.640, 0.180);   // gold
    float3 grad = l < 0.5 ? lerp(a, b, l * 2.0) : lerp(b, g, (l - 0.5) * 2.0);
    return lerp(grad, c * float3(0.7, 0.9, 1.15), 0.28);
}

float3 WF_Ambient(float3 n, float dream)
{
    float t = saturate(n.y * 0.5 + 0.5);
    float3 wake = lerp(_WF_AmbGround.rgb, _WF_AmbSky.rgb, t);
    float3 drm = lerp(_WF_DreamGround.rgb, _WF_DreamSky.rgb, t);
    return lerp(wake, drm, dream);
}

float3 WF_Fog(float3 col, float3 positionWS, float dream)
{
    float4 fog = lerp(_WF_FogColor, _WF_DreamFog, dream);
    float k = saturate((fog.a - positionWS.y) / 6.0);
    return lerp(col, fog.rgb, k * k);
}

#endif
