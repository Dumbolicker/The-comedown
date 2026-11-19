using System.IO;
using UnityEditor;
using UnityEditor.SceneManagement;
using UnityEngine;

namespace BorrowedTime.EditorTools
{
    /// <summary>Opening the project in the editor shows the game right away: the first time, it prepares the project
    /// (the materials and the boot scene, see CiBuild.Prepare), and it opens Assets/Scenes/Main.unity when no scene is
    /// open. Press Play to start. Batch mode (GitHub's builds) is left alone.</summary>
    [InitializeOnLoad]
    static class AutoOpen
    {
        static AutoOpen()
        {
            if (Application.isBatchMode) return;
            EditorApplication.delayCall += Open;
        }

        static void Open()
        {
            if (EditorApplication.isPlayingOrWillChangePlaymode) return;
            if (!File.Exists(CiBuild.ScenePath) || AssetDatabase.LoadAssetAtPath<Material>("Assets/Resources/BT_Base.mat") == null)
                CiBuild.Prepare();
            var active = EditorSceneManager.GetActiveScene();
            if (string.IsNullOrEmpty(active.path) && !active.isDirty) EditorSceneManager.OpenScene(CiBuild.ScenePath);
        }
    }
}
