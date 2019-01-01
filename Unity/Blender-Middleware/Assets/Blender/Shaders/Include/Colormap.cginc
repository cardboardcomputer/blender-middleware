#ifndef _COLORMAP
#define _COLORMAP

inline half4 colormap(half2 coord, sampler2D data, float stride, float idx) {
    half2 uv = coord + half2(0.0, idx * stride);
    half4 color = tex2Dlod (data, half4(uv, 0, 0));
    return color;
}

inline half4 colormapb(half2 coord, sampler2D data, float stride, float from, float to, float blend) {
    half2 uvFrom = coord + half2(0.0, from * stride);
    half2 uvTo = coord + half2(0.0, to * stride);
    half4 colorFrom = tex2Dlod (data, half4(uvFrom, 0, 0));
    half4 colorTo = tex2Dlod (data, half4(uvTo, 0, 0));
    half4 colorBlend = colorFrom * (1.0 - blend) + colorTo * blend;
    return colorBlend;
}

#endif