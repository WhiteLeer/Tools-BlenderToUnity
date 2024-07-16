using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using System.Collections.Generic;
using System.Text.RegularExpressions;

public class MultiObjectCreator : MonoBehaviour
{
    [MenuItem("Tools/2.多物体组装-From Json")]
    public static void InstantiateObjects()
    {
        GameObject[] selectedObjects = Selection.gameObjects;

        if (selectedObjects.Length != 1)
        {
            Debug.LogError("Please select exactly one object.");
            return;
        }

        GameObject selectedObject = selectedObjects[0];
        string selectedName = selectedObject.name.Split('.')[0];

        string[] basePath = Directory.GetDirectories(Application.dataPath, "*", SearchOption.AllDirectories);
        string targetFolderPath = null;

        foreach (string path in basePath)
        {
            if (Path.GetFileName(path) == selectedName)
            {
                targetFolderPath = Path.Combine(path, "Json");
                break;
            }
        }

        if (targetFolderPath == null || !Directory.Exists(targetFolderPath))
        {
            Debug.LogError($"No 'Json' folder found under '{selectedName}' directory in the project.");
            return;
        }

        string[] jsonFiles = Directory.GetFiles(targetFolderPath, "*.json");
        if (jsonFiles.Length == 0)
        {
            Debug.LogError($"No JSON files found in folder '{targetFolderPath}'.");
            return;
        }

        string jsonContent = File.ReadAllText(jsonFiles[0]);
        BaseJsonWrapper objectDataWrapper;

        try
        {
            objectDataWrapper = JsonUtility.FromJson<BaseJsonWrapper>(jsonContent);
        }
        catch (System.ArgumentException e)
        {
            Debug.LogError("Failed to parse JSON: " + e.Message);
            return;
        }

        foreach (BaseMultiJsonStruct item in objectDataWrapper.items)
        {
            string prefabName = Regex.Replace(item.name, @"\.\d+$", "");

            string[] guids = AssetDatabase.FindAssets(prefabName);
            if (guids.Length < 1)
            {
                Debug.LogError($"Prefab not found for: '{prefabName}'");
                continue;
            }

            string assetPath = AssetDatabase.GUIDToAssetPath(guids[0]);
            GameObject prefab = AssetDatabase.LoadAssetAtPath<GameObject>(assetPath);

            if (prefab == null)
            {
                Debug.LogError($"Prefab '{prefabName}' not found");
                continue;
            }

            Vector3 blenderPosition = ParseVector(item.data.Find(d => d.location != null).location);
            Vector3 blenderRotation = ParseEuler(item.data.Find(d => d.euler != null).euler);
            Vector3 blenderScale = ParseVector(item.data.Find(d => d.scale != null).scale);
            (blenderScale.y, blenderScale.z) = (blenderScale.z, blenderScale.y);

            Vector3 unityPosition = new Vector3(-blenderPosition.x, blenderPosition.z, -blenderPosition.y);
            Quaternion unityRotation = Quaternion.Euler(new Vector3(blenderRotation.x, -blenderRotation.z, -blenderRotation.y));
            Vector3 unityScale = blenderScale; 

            // 创建一个同名空物体
            var newParent = GameObject.Find(selectedObject.name + "_Decoration");
            if(newParent == null)
                newParent = new GameObject(selectedObject.name + "_Decoration");
            newParent.transform.SetParent(selectedObject.transform);
            
            GameObject newObj = Instantiate(prefab, newParent.transform, true);
            newObj.transform.position = unityPosition;
            newObj.transform.rotation = unityRotation;
            newObj.transform.localScale = unityScale;
        }

        AssetDatabase.Refresh();
    }

    private static Vector3 ParseVector(string vectorString)
    {
        var match = Regex.Match(vectorString, @"<Vector \(([^,]+), ([^,]+), ([^,]+)\)>");
        if (match.Success)
        {
            float x = float.Parse(match.Groups[1].Value);
            float y = float.Parse(match.Groups[2].Value);
            float z = float.Parse(match.Groups[3].Value);
            return new Vector3(x, y, z);
        }
        else
        {
            throw new ArgumentException("Invalid vector format");
        }
    }

    private static Vector3 ParseEuler(string eulerString)
    {
        var match = Regex.Match(eulerString, @"<Euler \(x=([^,]+), y=([^,]+), z=([^,]+)\), order='XYZ'>");
        if (match.Success)
        {
            float x = float.Parse(match.Groups[1].Value) * (180 / (float)Math.PI);
            float y = -float.Parse(match.Groups[2].Value) * (180 / (float)Math.PI);
            float z = float.Parse(match.Groups[3].Value) * (180 / (float)Math.PI);
            return new Vector3(x, y, z);
        }
        else
        {
            throw new ArgumentException("Invalid euler format");
        }
    }
}

[Serializable]
public class BaseMultiJsonStruct
{
    public string name;
    public List<BaseMultiJsonData> data;
}

[Serializable]
public class BaseMultiJsonData
{
    public string location;
    public string euler;
    public string scale;
}

[Serializable]
public class BaseJsonWrapper
{
    public List<BaseMultiJsonStruct> items;
}