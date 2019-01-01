#ifndef _COLOR_CONVERSION
#define _COLOR_CONVERSION

float3 hue2rgb(in float h)
  {
    float r = abs(h * 6 - 3) - 1;
    float g = 2 - abs(h * 6 - 2);
    float b = 2 - abs(h * 6 - 4);
    return saturate(float3(r, g, b));
  }

float rgbcv2hue(in float3 rgb, in float c, in float v)
  {
    float3 delta = (v - rgb) / c;
    delta.rgb -= delta.brg;
    delta.rgb += float3(2,4,6);
    delta.brg = step(v, rgb) * delta.brg;
    float h;
    h = max(delta.r, max(delta.g, delta.b));
    return frac(h / 6);
  }

float3 rgb2hsv(in float3 rgb)
  {
    float3 hsv = 0;
    hsv.z = max(rgb.r, max(rgb.g, rgb.b));
    float m = min(rgb.r, min(rgb.g, rgb.b));
    float c = hsv.z - m;
    if (c != 0)
      {
        hsv.x = rgbcv2hue(rgb, c, hsv.z);
        hsv.y = c / hsv.z;
      }
    return hsv;
  }

float3 hsv2rgb(in float3 hsv)
  {
    float3 rgb = hue2rgb(hsv.x);
    return ((rgb - 1) * hsv.y + 1) * hsv.z;
  }

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
