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
    public ArrayList<Vertex> vertexes;

    public HashSet<Edge> edgeSet;
    public ArrayList<Edge> edges;

    public ArrayList<HashSet<Vertex>> scopes;
    public HashMap<String, Vertex> lastSegVertexOfPackage;
    public Vertex v_root;

    public Graph() {
        vertexMap = new HashMap<>();
        vertexes = new ArrayList<>();

        edgeSet = new HashSet<>();
        edges = new ArrayList<>();

        scopes = new ArrayList<>();
        lastSegVertexOfPackage = new HashMap<>();
        predictedPackageNames = new HashMap<>();
        PackageSeg rootSeg = new PackageSeg(rootCode, rootCode);
        v_root = new Vertex(this, rootSeg, rootSeg.getSegName(), true);
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

    public void sortGraph() {
        ArrayList<Edge> dup_edges = new ArrayList<>();
        dup_edges.addAll(edgeSet);
        Collections.sort(dup_edges, new Comparator<Edge>() {
            @Override
            public int compare(Edge o1, Edge o2) {
                if (o1.source.id == o2.source.id) {
                    if (o1.target.id == o2.target.id) {
                        return String.CASE_INSENSITIVE_ORDER.compare(o1.type, o2.type);
                    }
                    return o1.target.id - o2.target.id;
                }
                return o1.source.id - o2.source.id;
            }
        });
        Edge prev_edge = null;
        for (Edge edge : dup_edges) {
            if (edge.equals(prev_edge)) continue;
            edges.add(edge);
            prev_edge = edge;
        }
    }

    public JSONObject toJson() {
        return new JSONObject(this.toMap());
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
        for (Vertex v : vertexes) {
            assign.add(v.toMap());
        }
        requestMap.put("query", query);
        requestMap.put("assign", assign);
        return requestMap;
    }

    public HashMap<String, Object> scope2Map(HashSet<Vertex> scope) {
        HashMap<String, Object> scopeMap = new HashMap<>();
        ArrayList<Integer> vertexArray = new ArrayList<>();
        ArrayList<Vertex> vertexes = new ArrayList<>();
        vertexes.addAll(scope);
        Collections.sort(vertexes, new Comparator<Vertex>() {
            @Override
            public int compare(Vertex v1, Vertex v2) {
                return v1.id - v2.id;
            }
        });
        for (Vertex v : vertexes) {
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
        HashMap<Integer, Vertex> id2VertexMap = new HashMap<>();
        for (Vertex v : this.vertexMap.values())
            id2VertexMap.put(v.id, v);
        for (int i = 0; i < resultJson.length(); i++) {
            JSONObject jsonObject = resultJson.getJSONObject(i);
            if (jsonObject.has("giv"))
                continue;
            Integer id = (Integer) jsonObject.get("v");
            String name = (String) jsonObject.get("inf");
            Vertex vertex = id2VertexMap.get(id);
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
        if (!vertexMap.containsKey(cls) || !cls.isApplicationClass())
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
