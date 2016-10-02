Shader "Vertex/Mapped/Unlit Transparent" {
    Properties {
        _VertexData ("Vertex Data", 2D) = "white" {}
        _Albedo ("Albedo", Float) = 1.0
        _Alpha ("Alpha", Float) = 1.0
        _Stride ("Stride", Float) = 1.0
        _From ("From", Float) = 0.0
        _To ("To", Float) = 0.0
        _Blend ("Blend", Float) = 0.0
    }

    SubShader {
        Tags { "Queue" = "Transparent" }

        CGPROGRAM
            #pragma glsl
            #pragma target 3.0
            #pragma surface surf Unlit vertex:vert alpha

            struct Input {
                half4 color : COLOR;
                half2 uv_VertexData;
            };

            sampler2D _VertexData;
            half _Albedo;
            half _Alpha;
            half _Stride;
            half _From;
            half _To;
            half _Blend;

            half4 LightingUnlit (SurfaceOutput s, half3 lightDir, half atten) {
                return half4(0, 0, 0, 1);
            }

            void vert (inout appdata_full v) {
                half2 uvFrom = v.texcoord + half2(0.0, _From * _Stride);
                half2 uvTo = v.texcoord + half2(0.0, _To * _Stride);
                half4 colorFrom = tex2Dlod (_VertexData, half4(uvFrom, 0, 0));
                half4 colorTo = tex2Dlod (_VertexData, half4(uvTo, 0, 0));
                half4 colorBlend = colorFrom * (1.0 - _Blend) + colorTo * _Blend;
                v.color = colorBlend;
            }

            void surf (Input IN, inout SurfaceOutput o) {
                o.Emission = IN.color.rgb * _Albedo;
                o.Alpha = IN.color.a * _Alpha;
            }
        ENDCG
    }
}
