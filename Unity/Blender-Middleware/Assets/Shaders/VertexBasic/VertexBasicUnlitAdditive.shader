Shader "Vertex/Basic/Unlit Additive" {
    Properties {
        _Albedo ("Albedo", Float) = 1.0
    }

    SubShader {
        Tags { "Queue" = "Transparent" }

        Pass {
            ZWrite Off
            Blend One One

            BindChannels {
                Bind "Vertex", vertex
                Bind "Color", color
            }

            SetTexture[_] {
                ConstantColor ([_Albedo], [_Albedo], [_Albedo], 1)
                combine constant * primary
            }
        }
    }
}
