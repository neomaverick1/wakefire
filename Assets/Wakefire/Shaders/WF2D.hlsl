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

// ---- the sky: x = rain, y = snow and the cold, z = day (each 0..1), w = 1 where there is sky over the picture
float4 _WF_Sky;

float WF_Hash(float n) { return frac(sin(n * 12.9898) * 43758.5453); }
float WF_Hash2(float2 p) { return frac(sin(dot(p, float2(12.9898, 78.233))) * 43758.5453); }

// One sheet of rain, in whole pixels of the world: a column in so many has drops in it, each `len` long, one
// every `gap`, falling `speed` pixels a second and a pixel sideways for every `slant` it falls.
float WF_Streak(float2 px, float t, float speed, float len, float gap, float density, float slant, float seed)
{
    float col = px.x - floor(px.y / slant);
    float h = WF_Hash(col + seed);
    float on = step(WF_Hash(col * 1.37 + seed * 3.1), density);
    float y = px.y + floor(t * speed * (0.8 + 0.4 * h)) + floor(h * 977.0);
    float ph = y - gap * floor(y / gap);
    return on * step(ph, len - 0.5);
}

// One layer of snow: a flake to a cell, most cells, drifting down and a little from side to side.
float WF_Flakes(float2 px, float t, float cell, float speed, float size, float seed)
{
    float yy = px.y + floor(t * speed);
    float row = floor(yy / cell);
    float xx = px.x + floor(sin(t * 0.9 + row * 1.7 + seed) * 2.5);
    float2 p = float2(xx, yy);
    float2 c = floor(p / cell);
    float2 l = p - c * cell;
    float2 f = floor(float2(WF_Hash2(c + seed), WF_Hash2(c * 1.7 + seed + 9.0)) * (cell - size));
    float2 d = l - f;
    return step(0.0, d.x) * step(d.x, size - 0.5) * step(0.0, d.y) * step(d.y, size - 0.5) * step(WF_Hash2(c * 2.3 + seed), 0.72);
}

// Rain on a flat surface: a ring to a cell, opening and fading, seen aslant like the ground it is on.
float WF_Rings(float2 world, float t)
{
    float2 c = floor(world * 1.6);
    float h = WF_Hash2(c);
    float beat = t * (0.9 + h * 0.6) + h * 7.0;
    float ph = frac(beat);
    float n = floor(beat);
    float2 centre = (c + 0.2 + 0.6 * float2(WF_Hash2(c + 3.1 + n), WF_Hash2(c + 7.7 + n))) / 1.6;
    float2 d = (floor(world * 16.0) + 0.5) / 16.0 - centre;
    d.y *= 2.0;
    float r = length(d);
    return step(abs(r - ph * 0.27), 0.034) * step(ph, 0.7) * (1.0 - ph);
}

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
