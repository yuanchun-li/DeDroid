package com.lynnlyc.graph;

import com.lynnlyc.Util;
import org.json.JSONArray;
import org.json.JSONObject;

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
    public HashMap<Object, Vertex> vertexMap;
    public HashSet<Edge> edges;
    public HashSet<HashSet<Vertex>> scopes;
    public HashMap<Integer, Vertex> unknownVertex;

    public Graph() {
        vertexMap = new HashMap<>();
        edges = new HashSet<>();
        scopes = new HashSet<>();
        unknownVertex = new HashMap<>();
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
        for (int i = 0; i < resultJson.length(); i++) {
            JSONObject jsonObject = resultJson.getJSONObject(i);
            if (jsonObject.has("giv"))
                continue;
            Integer id = (Integer) jsonObject.get("v");
            String name = (String) jsonObject.get("inf");
//                System.out.println(id);
            Vertex vertex = unknownVertex.get(id);
            vertex.restoreName(name);
//                System.out.println(vertex);
//                System.out.println(vertex.content);
        }
    }
}
