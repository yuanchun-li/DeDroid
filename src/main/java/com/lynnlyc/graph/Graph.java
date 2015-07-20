package com.lynnlyc.graph;

import net.sf.json.JSONArray;
import net.sf.json.JSONObject;

import java.io.File;
import java.io.IOException;
import java.io.PrintStream;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.util.HashMap;
import java.util.HashSet;
import java.util.Iterator;

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
        vertexMap = new HashMap<Object, Vertex>();
        edges = new HashSet<Edge>();
        scopes = new HashSet<HashSet<Vertex>>();
        unknownVertex = new HashMap<Integer, Vertex>();
    }

    public HashSet<Vertex> getNewScope() {
        HashSet<Vertex> scope = new HashSet<Vertex>();
        scopes.add(scope);
        return scope;
    }

    public void dump(PrintStream ps) {
        ps.println(this.toJson().toString(0, 4));
        ps.flush();
    }

    public JSONObject toJson() {
        JSONObject jsonObject = new JSONObject();
        JSONArray query = new JSONArray();
        JSONArray assign = new JSONArray();
        for (Edge e : edges) {
            query.add(e.toJson());
        }
        for (HashSet<Vertex> scope : scopes) {
            query.add(scope2Json(scope));
        }
        for (Vertex v : vertexMap.values()) {
            assign.add(v.toJson());
        }
        jsonObject.put("query", query);
        jsonObject.put("assign", assign);
        return jsonObject;
    }

    public JSONObject scope2Json(HashSet<Vertex> scope) {
        JSONObject jsonObject = new JSONObject();
        JSONArray jsonArray = new JSONArray();
        for (Vertex v : scope) {
            jsonArray.add(v.id);
        }
        jsonObject.put("cn", "!=");
        jsonObject.put("n", jsonArray);
        return jsonObject;
    }

    public void restoreUnknownFromFile(File resultFile) {
        try {
            byte[] encoded = Files.readAllBytes(resultFile.toPath());
            String resultStr = new String(encoded, Charset.defaultCharset());
            JSONArray resultJson = JSONArray.fromObject(resultStr);
            for (Object aResultJson : resultJson) {
                JSONObject jsonObject = (JSONObject) aResultJson;
                if (jsonObject.containsKey("giv"))
                    continue;
                Integer id = (Integer) jsonObject.get("v");
                String name = (String) jsonObject.get("inf");
//                System.out.println(id);
                Vertex vertex = unknownVertex.get(id);
                vertex.restoreName(name);
//                System.out.println(vertex);
//                System.out.println(vertex.content);
            }

        } catch (IOException e) {
            e.printStackTrace();
        }

    }
}
