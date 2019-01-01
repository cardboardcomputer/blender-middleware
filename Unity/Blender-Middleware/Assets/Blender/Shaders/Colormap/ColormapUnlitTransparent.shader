Shader "Colormap/Unlit Transparent" {
    Properties {
        _VertexData ("Vertex Data", 2D) = "white" {}
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
        #include "../Include/Colormap.cginc"

        struct Input {
            half4 color : COLOR;
        };

        sampler2D _VertexData;
        half _Stride;
        half _From;
        half _To;
        half _Blend;

        half4 LightingUnlit (SurfaceOutput s, half3 lightDir, half atten) {
            return half4(0, 0, 0, 1);
        }

        void vert (inout appdata_full v) {
            v.color = colormapb(v.texcoord, _VertexData, _Stride, _From, _To, _Blend);
        }

        void surf (Input IN, inout SurfaceOutput o) {
            o.Emission = IN.color.rgb;
            o.Alpha = IN.color.a;
        }

        ENDCG
    }
}
