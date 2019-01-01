Shader "Vertex/Basic/Unlit" {
    Properties {
        _Albedo ("Albedo", Float) = 1.0
    }

    SubShader {
        Pass {
            BindChannels {
                Bind "Vertex", vertex
                Bind "Color", color
            }

            SetTexture[_] {
                ConstantColor ([_Albedo], [_Albedo], [_Albedo])
                combine constant * primary
            }
        }
    }
}
