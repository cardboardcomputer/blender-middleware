Shader "Vertex/Basic/Unlit Transparent" {
    Properties {
        _Albedo ("Albedo", Float) = 1.0
        _Alpha ("Alpha", Float) = 1.0
    }

    SubShader {
        Tags { "Queue" = "Transparent" }

        Pass {
            Zwrite Off
            Blend SrcAlpha OneMinusSrcAlpha

            BindChannels {
                Bind "Vertex", vertex
                Bind "Color", color
            }

            SetTexture[_] {
                ConstantColor ([_Albedo], [_Albedo], [_Albedo], [_Alpha])
                combine constant * primary
            }
        }
    }
}
