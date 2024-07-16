using System;
using System.IO;
using UnityEditor;
using UnityEngine;
using System.Collections.Generic;
using System.Text.RegularExpressions;

public class SizeSorter : MonoBehaviour
{
    [MenuItem("Tools/1.物体分类-From Json")]
    public static void InstantiateObjects()
    {
        GameObject[] selectedObjects = Selection.gameObjects;
    
        if (selectedObjects.Length != 1)
        {
            Debug.LogError("Please select exactly one object.");
            return;
        }
        
        // 获取子集物体
        GameObject selectedObject = selectedObjects[0];
        List<GameObject> childObjects = new List<GameObject>();
        for (int i = 0; i < selectedObject.transform.childCount; i++)
        {
            childObjects.Add(selectedObject.transform.GetChild(i).gameObject);
        }
        
        // 读取 Json 数据
        string targetFolderPath = Application.dataPath + "/Art/MapSources/Architecture/XSJArtEditorTools/胡家豪";
        string[] jsonFiles = Directory.GetFiles(targetFolderPath, "*.json");
        if (jsonFiles.Length == 0)
        {
            Debug.LogError($"No JSON files found in folder '{targetFolderPath}'.");
            return;
        }
    
        string jsonContent = File.ReadAllText(jsonFiles[0]);
        SizeJsonWrapper objectDataWrapper;
    
        try
        {
            objectDataWrapper = JsonUtility.FromJson<SizeJsonWrapper>(jsonContent);
        }
        catch (System.ArgumentException e)
        {
            Debug.LogError("Failed to parse JSON: " + e.Message);
            return;
        }
    
        Dictionary<string, string> sizeData = new Dictionary<string, string>();
        foreach (SizeJsonStruct item in objectDataWrapper.items)
        {
            string name = Regex.Replace(item.name, @"\.\d+$", "");
            string size = Regex.Replace(item.size, @"\.\d+$", "");
            sizeData[name] = size; // 修改：使用索引器来避免重复键引发的问题
        }
    
        // 遍历选中物体的子对象
        if(GameObject.Find($"Level_L") == null);
        {
            GameObject levelL = new GameObject($"Level_L");
            levelL.transform.SetParent(selectedObject.transform);
            GameObject levelM = new GameObject($"Level_M");
            levelM.transform.SetParent(selectedObject.transform);
            GameObject levelS = new GameObject($"Level_S");
            levelS.transform.SetParent(selectedObject.transform);
        }
        
        foreach (var child in childObjects)
        {
            string baseName = child.name;
            string childName = baseName.IndexOf('(') != -1 ? baseName.Substring(0, baseName.IndexOf('(')) : baseName; 

            if (sizeData.TryGetValue(childName, out string size))
            {
                if (size.Length == 1)
                {
                    var targetParent = GameObject.Find($"{"Level_" + size}");
                    child.transform.SetParent(targetParent.transform);
                }
                else
                {
                    var index = size.Length - 1;
                    var boundSize = CalculateObjectBounds(child).size;

                    float nowSize = boundSize.x * boundSize.y * boundSize.z;
                    var target = (nowSize > 60) ? 'L' : (nowSize > 30) ? 'M' : 'S';
                    target = (target < size[0]) ? size[0] : (target > size[index]) ? size[index] : target;
                    
                    var targetParent = GameObject.Find($"{"Level_" + target}");
                    child.transform.SetParent(targetParent.transform);
                }
            }
        }
    }
    
    public static Bounds CalculateObjectBounds(GameObject obj)
    {
        // 初始化一个空的 bounds 对象
        Bounds bounds = new Bounds(obj.transform.position, Vector3.zero);
        
        // 获取当前物体以及所有子物体的 Renderer 组件
        Renderer[] renderers = obj.GetComponentsInChildren<Renderer>();

        foreach (Renderer renderer in renderers)
        {
            bounds.Encapsulate(renderer.bounds);
        }

        return bounds;
    }
}

[Serializable]
public class SizeJsonStruct
{
    public string name;
    public string size;
}

[Serializable]
public class SizeJsonWrapper
{
    public List<SizeJsonStruct> items;
}