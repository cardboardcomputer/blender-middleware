#ifndef _BLENDER
#define _BLENDER

float4 uv2rgba(in float2 uv)
  {
    float precision = 4096;
    float p = precision - 1;
    float4 c = half4(0, 0, 0, 0);

    c.r = floor(uv.x / precision) / p;
    c.g = fmod(uv.x, precision) / p;
    c.b = floor(uv.y / precision) / p;
    c.a = fmod(uv.y, precision) / p;

    return c;
  }

#endif
