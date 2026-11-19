using System.Collections.Generic;
using UnityEngine;

namespace BorrowedTime
{
    /// <summary>Shared materials built at runtime from three Standard-shader base materials that the build
    /// script saves into Resources (so the shader and its emission/transparent variants are kept in builds).</summary>
    public static class Mat
    {
        static Material baseMat, emissiveMat, glassMat;
        static readonly Dictionary<long, Material> cache = new Dictionary<long, Material>();

        static Material Load(string name, ref Material slot)
        {
            if (slot == null) slot = Resources.Load<Material>(name);
            if (slot == null) slot = new Material(Shader.Find("Standard"));
            return slot;
        }

        public static Material Get(Color c, float smoothness = 0.2f, float metallic = 0f, Color? emission = null)
        {
            long key = ((long)Mathf.RoundToInt(c.r * 255) << 40) | ((long)Mathf.RoundToInt(c.g * 255) << 32) | ((long)Mathf.RoundToInt(c.b * 255) << 24)
                     | ((long)Mathf.RoundToInt(smoothness * 100) << 16) | ((long)Mathf.RoundToInt(metallic * 100) << 8) | (emission.HasValue ? 1L : 0L);
            if (cache.TryGetValue(key, out var m)) return m;
            m = new Material(emission.HasValue ? Load("BT_Emissive", ref emissiveMat) : Load("BT_Base", ref baseMat));
            m.color = c;
            m.SetFloat("_Glossiness", smoothness);
            m.SetFloat("_Metallic", metallic);
            if (emission.HasValue)
            {
                m.EnableKeyword("_EMISSION");
                m.SetColor("_EmissionColor", emission.Value);
                m.globalIlluminationFlags = MaterialGlobalIlluminationFlags.RealtimeEmissive;
            }
            cache[key] = m;
            return m;
        }

        public static Material Glass() => Load("BT_Glass", ref glassMat);

        public static Color Hex(int h) => new Color(((h >> 16) & 255) / 255f, ((h >> 8) & 255) / 255f, (h & 255) / 255f);
    }
}
