using System;
using System.IO;
using UnityEditor;
using UnityEditor.Build.Reporting;
using UnityEditor.SceneManagement;
using UnityEngine;
using UnityEngine.Rendering;

namespace BorrowedTime.EditorTools
{
    /// <summary>Makes the project buildable from a bare checkout (no hand-made scenes or assets needed),
    /// and builds it headlessly. GameCI calls Build() with -customBuildPath.</summary>
    public static class CiBuild
    {
        public const string ScenePath = "Assets/Scenes/Main.unity";

        [MenuItem("Borrowed Time/Prepare Project")]
        public static void Prepare()
        {
            Directory.CreateDirectory("Assets/Resources");
            Directory.CreateDirectory("Assets/Scenes");
            MakeMat("Assets/Resources/BT_Base.mat", m => m.color = Color.white);
            MakeMat("Assets/Resources/BT_Emissive.mat", m => { m.EnableKeyword("_EMISSION"); m.SetColor("_EmissionColor", Color.white); });
            MakeMat("Assets/Resources/BT_Glass.mat", m =>
            {
                m.SetFloat("_Mode", 3f);
                m.SetInt("_SrcBlend", (int)BlendMode.One); m.SetInt("_DstBlend", (int)BlendMode.OneMinusSrcAlpha); m.SetInt("_ZWrite", 0);
                m.DisableKeyword("_ALPHATEST_ON"); m.DisableKeyword("_ALPHABLEND_ON"); m.EnableKeyword("_ALPHAPREMULTIPLY_ON");
                m.renderQueue = 3000; m.color = new Color(0.62f, 0.78f, 0.86f, 0.32f); m.SetFloat("_Glossiness", 0.9f);
            });
            if (AssetDatabase.LoadAssetAtPath<Material>("Assets/Resources/BT_Sky.mat") == null)
                AssetDatabase.CreateAsset(new Material(Shader.Find("Skybox/Procedural")), "Assets/Resources/BT_Sky.mat");
            if (!File.Exists(ScenePath))
            {
                var scene = EditorSceneManager.NewScene(NewSceneSetup.EmptyScene, NewSceneMode.Single);
                EditorSceneManager.SaveScene(scene, ScenePath);
            }
            EditorBuildSettings.scenes = new[] { new EditorBuildSettingsScene(ScenePath, true) };
            PlayerSettings.productName = "Borrowed Time";
            PlayerSettings.companyName = "Borrowed Time";
            PlayerSettings.WebGL.compressionFormat = WebGLCompressionFormat.Disabled; // plays from any static host, GitHub Pages included
            // The game builds its whole world from code at runtime (CreatePrimitive, AddComponent), so nothing in a scene
            // tells the build which engine classes are used. Stripping them broke the web build (colliders and other
            // classes "doesn't exist" / "Could not produce class"), so keep the engine whole and strip C# only lightly.
            PlayerSettings.stripEngineCode = false;
            PlayerSettings.SetManagedStrippingLevel(UnityEditor.Build.NamedBuildTarget.WebGL, ManagedStrippingLevel.Minimal);
            PlayerSettings.SetManagedStrippingLevel(UnityEditor.Build.NamedBuildTarget.Standalone, ManagedStrippingLevel.Minimal);
            AssetDatabase.SaveAssets();
            AssetDatabase.Refresh();
        }

        static void MakeMat(string path, Action<Material> setup)
        {
            if (AssetDatabase.LoadAssetAtPath<Material>(path) != null) return;
            var m = new Material(Shader.Find("Standard"));
            setup(m);
            AssetDatabase.CreateAsset(m, path);
        }

        public static void Build()
        {
            Prepare();
            BuildTarget target = EditorUserBuildSettings.activeBuildTarget;
            string path = Arg("-customBuildPath");
            if (string.IsNullOrEmpty(path)) path = Path.Combine("build", target.ToString(), target == BuildTarget.StandaloneWindows64 ? "BorrowedTime.exe" : "BorrowedTime");
            var options = new BuildPlayerOptions
            {
                scenes = new[] { ScenePath },
                locationPathName = path,
                target = target,
                targetGroup = BuildPipeline.GetBuildTargetGroup(target),
                options = BuildOptions.None
            };
            BuildReport report = BuildPipeline.BuildPlayer(options);
            Debug.Log($"Borrowed Time build {report.summary.result}: {report.summary.totalSize} bytes, {report.summary.totalErrors} errors, {report.summary.totalTime}");
            if (report.summary.result != BuildResult.Succeeded) EditorApplication.Exit(1);
        }

        static string Arg(string name)
        {
            string[] a = Environment.GetCommandLineArgs();
            for (int i = 0; i < a.Length - 1; i++) if (a[i] == name) return a[i + 1];
            return null;
        }
    }
}
