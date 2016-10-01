using UnityEngine;

public class HSV
{
  public float h;
  public float s;
  public float v;
  public float a;

  public HSV(float h, float s, float v, float a)
  {
    this.h = h;
    this.s = s;
    this.v = v;
    this.a = a;
  }
}

public class ColorUtils
{
  static public Color Alpha(float a)
  {
    return new Color(1, 1, 1, a);
  }

  static public Color Alpha(Color c, float a)
  {
    return new Color(c.r, c.g, c.b, a);
  }

  static public Vector2 Color2UV(Color c)
  {
    int precision = 4096;
    int p = precision - 1;

    float r, g, b, a, u, v;

    r = Mathf.Floor(c.r * p);
    g = Mathf.Floor(c.g * p);
    b = Mathf.Floor(c.b * p);
    a = Mathf.Floor(c.a * p);

    u = (r * precision) + g;
    v = (b * precision) + a;

    return new Vector2(u, v);
  }

  static public HSV Color2HSV(Color c)
  {
    float h, s, v;
    ColorToHSV(c, out h, out s, out v);
    return new HSV(h, s, v, c.a);
  }

  static public Color HSV2Color(HSV c)
  {
    return ColorFromHSV(c.h, c.s, c.v, c.a);
  }

  static protected Color ColorFromHSV(float h, float s, float v, float a = 1)
  {
	// no saturation, we can return the value across the board (grayscale)
    if (s == 0)
      return new Color(v, v, v, a);

    // which chunk of the rainbow are we in?
    float sector = h / 60;

    // split across the decimal (ie 3.87 into 3 and 0.87)
    int i = (int)sector;
    float f = sector - i;

    float p = v * (1 - s);
    float q = v * (1 - s * f);
    float t = v * (1 - s * (1 - f));

    // build our rgb color
    Color color = new Color(0, 0, 0, a);

    switch(i)
      {
      case 0:
        color.r = v;
        color.g = t;
        color.b = p;
        break;

      case 1:
        color.r = q;
        color.g = v;
        color.b = p;
        break;

      case 2:
        color.r  = p;
        color.g  = v;
        color.b  = t;
        break;

      case 3:
        color.r  = p;
        color.g  = q;
        color.b  = v;
        break;

      case 4:
        color.r  = t;
        color.g  = p;
        color.b  = v;
        break;

      default:
        color.r  = v;
        color.g  = p;
        color.b  = q;
        break;
      }

    return color;
  }

  static protected void ColorToHSV(Color color, out float h, out float s, out float v)
  {
	float min = Mathf.Min(Mathf.Min(color.r, color.g), color.b);
    float max = Mathf.Max(Mathf.Max(color.r, color.g), color.b);
    float delta = max - min;

    // value is our max color
    v = max;

    // saturation is percent of max
    if (!Mathf.Approximately(max, 0))
      s = delta / max;
    else
      {
        // all colors are zero, no saturation and hue is undefined
        s = 0;
        h = -1;
        return;
      }

    // grayscale image if min and max are the same
    if (Mathf.Approximately(min, max))
      {
        v = max;
        s = 0;
        h = -1;
        return;
      }

    // hue depends which color is max (this creates a rainbow effect)
    if (color.r == max)
      h = (color.g - color.b) / delta;         	// between yellow & magenta
    else if (color.g == max)
      h = 2 + (color.b - color.r) / delta; 		// between cyan & yellow
    else
      h = 4 + (color.r - color.g) / delta; 		// between magenta & cyan

    // turn hue into 0-360 degrees
    h *= 60;
    if (h < 0 )
      h += 360;
  }
}
