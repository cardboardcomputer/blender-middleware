Shader "Examples/TestAuxColors" {
    Properties {
        _Albedo ("Albedo", Float) = 1.0
    }

    SubShader {
        CGPROGRAM
            #pragma surface surf Unlit vertex:vert
            #include "../../Shaders/Include/Blender.cginc"

            struct Input {
                half4 color : COLOR;
                half4 color2;
            };

            half _Albedo;

            half4 LightingUnlit (SurfaceOutput s, half3 lightDir, half atten) {
                return half4(0, 0, 0, 1);
            }

            void vert (inout appdata_full v, out Input o) {
                UNITY_INITIALIZE_OUTPUT(Input, o);
                o.color2 = uv2rgba(v.texcoord1);
            }

            void surf (Input IN, inout SurfaceOutput o) {
                o.Emission = lerp(IN.color.rgb, IN.color2.rgb, IN.color2.a) * _Albedo;
            }
        ENDCG
    }
}
