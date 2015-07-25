package com.lynnlyc.graph;

import com.lynnlyc.Util;
import com.lynnlyc.sootextension.PackageSeg;
import org.json.JSONArray;
import org.json.JSONObject;
import soot.*;

import java.io.File;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.util.*;

/**
 * Created by LiYC on 2015/7/19.
 * Package: UnuglifyDEX
 */
public class Graph {
    private static final String rootCode = "UnunlifyDEX_ROOT";

    public HashMap<Object, Vertex> vertexMap;
    public HashSet<Edge> edges;
    public HashSet<HashSet<Vertex>> scopes;
    public HashMap<Integer, Vertex> unknownVertex;
    public HashMap<String, Vertex> lastSegVertexOfPackage;
    public Vertex v_root;

    public Graph() {
        vertexMap = new HashMap<>();
        edges = new HashSet<>();
        scopes = new HashSet<>();
        unknownVertex = new HashMap<>();
        lastSegVertexOfPackage = new HashMap<>();
        predictedPackageNames = new HashMap<>();
        PackageSeg rootSeg = new PackageSeg(rootCode, rootCode);
        v_root = new Vertex(this, rootSeg, rootSeg.getSegName(), true);
        vertexMap.put(rootSeg, v_root);
    }

    public HashSet<Vertex> getNewScope() {
        HashSet<Vertex> scope = new HashSet<>();
        scopes.add(scope);
        return scope;
    }

    public void dump(PrintStream ps) {
        ps.println(this.toJson().toString());
        ps.flush();
    }

    public JSONObject toJson() {
        JSONObject jsonObject = new JSONObject();
        JSONArray query = new JSONArray();
        JSONArray assign = new JSONArray();
        for (Edge e : edges) {
            query.put(e.toJson());
        }
        for (HashSet<Vertex> scope : scopes) {
            query.put(scope2Json(scope));
        }
        for (Vertex v : vertexMap.values()) {
            assign.put(v.toJson());
        }
        jsonObject.put("query", query);
        jsonObject.put("assign", assign);
        return jsonObject;
    }

    public Map<String, Object> toMap() {
        HashMap<String, Object> requestMap = new HashMap<>();
        ArrayList<Map> query = new ArrayList<>();
        ArrayList<Map> assign = new ArrayList<>();
        for (Edge e : edges) {
            query.add(e.toMap());
        }
        for (HashSet<Vertex> scope : scopes) {
            query.add(scope2Map(scope));
        }
        for (Vertex v : vertexMap.values()) {
            assign.add(v.toMap());
        }
        requestMap.put("query", query);
        requestMap.put("assign", assign);
        return requestMap;
    }

    public JSONObject scope2Json(HashSet<Vertex> scope) {
        JSONObject jsonObject = new JSONObject();
        JSONArray jsonArray = new JSONArray();
        for (Vertex v : scope) {
            jsonArray.put(v.id);
        }
        jsonObject.put("cn", "!=");
        jsonObject.put("n", jsonArray);
        return jsonObject;
    }

    public HashMap<String, Object> scope2Map(HashSet<Vertex> scope) {
        HashMap<String, Object> scopeMap = new HashMap<>();
        ArrayList<Integer> vertexArray = new ArrayList<>();
        for (Vertex v : scope) {
            vertexArray.add(v.id);
        }
        scopeMap.put("cn", "!=");
        scopeMap.put("n", vertexArray);
        return scopeMap;
    }

    public void restoreUnknownFromFile(File resultFile) {
        try {
            byte[] encoded = Files.readAllBytes(resultFile.toPath());
            String resultStr = new String(encoded, Charset.defaultCharset());
            restoreUnknownFromString(resultStr);
        } catch (IOException e) {
            e.printStackTrace();
        }

    }

    public void restoreUnknownFromString(String resultStr) {
        JSONArray resultJson = new JSONArray(resultStr);
        restoreUnknownFromJson(resultJson);
    }

    public void restoreUnknownFromJson(JSONArray resultJson) {
        for (int i = 0; i < resultJson.length(); i++) {
            JSONObject jsonObject = resultJson.getJSONObject(i);
            if (jsonObject.has("giv"))
                continue;
            Integer id = (Integer) jsonObject.get("v");
            String name = (String) jsonObject.get("inf");
            Vertex vertex = unknownVertex.get(id);
            vertex.setPredictedName(name);
        }
    }

    public HashMap<String, String> predictedPackageNames;
    public String getPredictedPackageName(String packageName) {
        if (packageName == null || packageName.length() == 0) {
            return null;
        }
        if (predictedPackageNames.containsKey(packageName)) {
            return predictedPackageNames.get(packageName);
        }

        if (!lastSegVertexOfPackage.containsKey(packageName)) {
            Util.LOGGER.warning("cannot find Vertex of package: " + packageName);
            return Util.UNKNOWN;
        }

        Vertex v_lastSeg = lastSegVertexOfPackage.get(packageName);

//        String lastSegStr;
        String prevSegsStr, predictedPackageName;
        int lastDot = packageName.lastIndexOf('.');
        if (lastDot < 0) {
//            lastSegStr = packageName;
            predictedPackageName = v_lastSeg.getPredictedName();
        } else {
//            lastSegStr = packageName.substring(lastDot + 1);
            prevSegsStr = packageName.substring(0, lastDot);
            String predictedNameOfPrevSegs = getPredictedPackageName(prevSegsStr);
            predictedPackageName = predictedNameOfPrevSegs + "." + v_lastSeg.getPredictedName();
        }

        predictedPackageNames.put(packageName, predictedPackageName);
        return predictedPackageName;
    }

    public String getPredictedClassName(SootClass cls) {
        if (cls == null)
            return null;
        if (!vertexMap.containsKey(cls))
            return cls.getName();
        String predictedShortName = vertexMap.get(cls).getPredictedName();
        String predictedPackageName = getPredictedPackageName(cls.getPackageName());
        if (predictedPackageName == null || predictedPackageName.isEmpty())
            return predictedShortName;
        return predictedPackageName + "." + predictedShortName;
    }

    public String getPredictedTypeName(Type type) {
        if (type == null)
            return null;
        if (type instanceof RefType) {
            return getPredictedClassName(((RefType) type).getSootClass());
        }
        return type.toString();
    }

    public String getPredictedMethodName(SootMethod method) {
        if (method == null)
            return null;
        if (!vertexMap.containsKey(method))
            return method.getName();
        return vertexMap.get(method).getPredictedName();
    }

    public String getPredictedFieldName(SootField field) {
        if (field == null)
            return null;
        if (!vertexMap.containsKey(field))
            return field.getName();
        return vertexMap.get(field).getPredictedName();
    }
}
