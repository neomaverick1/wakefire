// Shared 2D helpers: ordered dither, the waking/dream ring, the dream palette.
#ifndef WF_2D_INCLUDED
#define WF_2D_INCLUDED

float4 _WF_Flip;       // xy = ring centre (world), w = ring radius
float4 _WF_FlipState;  // x = 1 if inside the ring is the dream, y = ring glow, z = dream amount, w = time

float WF_Bayer(float2 pixel)
{
    uint2 p = uint2(pixel) & 3u;
    const float m[16] = { 0, 8, 2, 10, 12, 4, 14, 6, 3, 11, 1, 9, 15, 7, 13, 5 };
    return (m[p.y * 4u + p.x] + 0.5) / 16.0;
}

float WF_DreamAt(float2 world)
{
    float inside = step(distance(world, _WF_Flip.xy), _WF_Flip.w);
    return lerp(1.0 - inside, inside, _WF_FlipState.x);
}

// The ring is a crisp gold line two pixels wide with a dithered fringe, not a soft glow.
float WF_RingAt(float2 world)
{
    float edge = abs(distance(world, _WF_Flip.xy) - _WF_Flip.w);
    float core = step(edge, 0.07);
    float fringe = step(edge, 0.19) * step(0.5, frac((floor(world.x * 16) + floor(world.y * 16)) * 0.5));
    return max(core, fringe * 0.6) * _WF_FlipState.y;
}

float WF_Luma(float3 c) { return dot(c, float3(0.299, 0.587, 0.114)); }

// The dream keeps every shape and repaints it: violet shadows, magenta and teal middles, gold
// lights. Worked out in display (sRGB) space so the gradient keeps its depth in a linear project.
float3 WF_ToGamma(float3 c) { return pow(max(c, 0), 1.0 / 2.2); }
float3 WF_ToLinear(float3 c) { return pow(max(c, 0), 2.2); }

float3 WF_DreamPalette(float3 c)
{
    float3 g = WF_ToGamma(c);
    float l = saturate(dot(g, float3(0.299, 0.587, 0.114)) * 1.08);
    float3 s0 = float3(0.09, 0.04, 0.20);
    float3 s1 = float3(0.33, 0.12, 0.50);
    float3 s2 = float3(0.12, 0.56, 0.64);
    float3 s3 = float3(1.00, 0.88, 0.52);
    float3 grad = l < 0.30 ? lerp(s0, s1, l / 0.30) : (l < 0.62 ? lerp(s1, s2, (l - 0.30) / 0.32) : lerp(s2, s3, (l - 0.62) / 0.38));
    // stone, earth and leaves take the dream's colours; strongly coloured things (fire, cloth,
    // gold, faces) keep more of their own so people and props stay recognisable
    float mx = max(g.r, max(g.g, g.b)), mn = min(g.r, min(g.g, g.b));
    float sat = mx > 0.001 ? (mx - mn) / mx : 0;
    float keep = lerp(0.22, 0.78, saturate(sat * 1.6 - 0.25));
    float3 own = g * float3(0.9, 0.95, 1.1);
    return WF_ToLinear(lerp(grad, own, keep));
}
#endif
