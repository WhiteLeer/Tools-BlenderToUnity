using UnityEditor;
using UnityEngine;
using System.IO;

public static class PrefabCreator
{
    // 添加菜单项以显示按钮
    [MenuItem("Tools/0.资产生成-Prefab")]
    public static void ConvertAllFbxToPrefabs()
    {
        // 获取所有包含FBX的目录
        string[] fbxFolders = Directory.GetDirectories(Application.dataPath, "Fbx", SearchOption.AllDirectories);

        foreach (string fbxFolder in fbxFolders)
        {
            // 为每个FBX目录创建相应的预制体目录
            string prefabFolder = Path.Combine(Path.GetDirectoryName(fbxFolder), "Prefab");
            EnsureDirectoryExists(prefabFolder);

            // 获取FBX目录中的所有FBX文件
            string[] fbxFiles = Directory.GetFiles(fbxFolder, "*.fbx", SearchOption.AllDirectories);
            foreach (string fbxFile in fbxFiles)
            {
                // 将每个FBX文件转换为预制体
                CreatePrefabFromFbx(fbxFile, prefabFolder);
            }
        }

        // 刷新AssetDatabase以应用更改
        AssetDatabase.Refresh();
        Debug.Log("All FBX files have been converted to Prefabs.");
    }

    // 确保目录存在，不存在则创建
    private static void EnsureDirectoryExists(string path)
    {
        if (!Directory.Exists(path))
        {
            Directory.CreateDirectory(path);
            AssetDatabase.Refresh(); // 刷新以确保Unity更新其数据库
        }
    }

    // 从FBX文件创建预制体
    private static void CreatePrefabFromFbx(string fbxFile, string prefabFolder)
    {
        // 转换为相对路径
        string relativeFbxPath = ConvertToRelativePath(fbxFile);
        // 生成预制体路径
        string relativePrefabPath = GeneratePrefabPath(fbxFile, prefabFolder);

        // 加载FBX资源
        GameObject fbxAsset = AssetDatabase.LoadAssetAtPath<GameObject>(relativeFbxPath);
        if (fbxAsset == null)
        {
            Debug.LogError($"Failed to load FBX asset at path: {relativeFbxPath}");
            return;
        }

        // 保存为预制体
        PrefabUtility.SaveAsPrefabAsset(fbxAsset, relativePrefabPath);
        Debug.Log($"Created Prefab: {relativePrefabPath}");
    }

    // 将完整路径转换为相对路径
    private static string ConvertToRelativePath(string fullPath)
    {
        return "Assets" + fullPath.Replace(Application.dataPath, "").Replace("\\", "/");
    }

    // 生成预制体的路径
    private static string GeneratePrefabPath(string fbxFile, string prefabFolder)
    {
        string prefabFile = Path.Combine(prefabFolder, Path.GetFileNameWithoutExtension(fbxFile) + ".prefab");
        return "Assets" + prefabFile.Replace("\\", "/").Replace(Application.dataPath, "");
    }
}