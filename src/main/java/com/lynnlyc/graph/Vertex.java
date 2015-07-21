package com.lynnlyc.graph;

import com.lynnlyc.Config;
import com.lynnlyc.Util;
import org.json.JSONArray;
import org.json.JSONObject;
import soot.*;

import java.io.*;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.util.HashMap;
import java.util.HashSet;

/**
 * Created by LiYC on 2015/7/19.
 * Package: UnuglifyDEX
 */
public class Vertex {
    public Object content;
    public int id;
    public boolean isKnown = false;
    public String name;
    private static int Count = 0;

    public Vertex(Graph g, Object content, String name, boolean isKnown) {
        this.content = content;
        this.name = name;
        this.isKnown = isKnown;
        this.id = Count;
        if (!Config.isTraining && !this.isKnown) {
            g.unknownVertex.put(this.id, this);
        }
        Count++;
    }

    public static Vertex getVertexFromObject (Graph g, Object object) {
        HashMap<Object, Vertex> VertexMap = g.vertexMap;
        if (VertexMap.containsKey(object)) {
            return VertexMap.get(object);
        }
        if (object instanceof SootClass) {
            SootClass cls = (SootClass) object;
            String name = cls.getShortName();
            boolean isKnown = false;
            if (cls.isLibraryClass()) isKnown = true;
            Vertex newVertex = new Vertex(g, cls, name, isKnown);
            VertexMap.put(object, newVertex);
            return newVertex;
        }
        if (object instanceof SootMethod) {
            SootMethod method = (SootMethod) object;
            String name = method.getName();
            boolean isKnown = false;
            if (method.getDeclaringClass().isLibraryClass()) isKnown = true;
            else if (method.isConstructor()) isKnown = true;
            else if (name.startsWith("<") && name.endsWith(">")) isKnown = true;
            Vertex newVertex = new Vertex(g, method, name, isKnown);
            VertexMap.put(object, newVertex);
            return newVertex;
        }
        if (object instanceof SootField) {
            SootField field = (SootField) object;
            String name = field.getName();
            boolean isKnown = false;
            if (field.getDeclaringClass().isLibraryClass()) isKnown = true;
            Vertex newVertex = new Vertex(g, field, name, isKnown);
            VertexMap.put(object, newVertex);
            return newVertex;
        }
        if (object instanceof Type) {
            Type type = (Type) object;
            if (type instanceof RefType) {
                RefType refType = (RefType) type;
                return getVertexFromObject(g, refType.getSootClass());
            }
            String name = type.toString();
            Vertex newVertex = new Vertex(g, type, name, true);
            VertexMap.put(object, newVertex);
            return newVertex;
        }
        if (object instanceof Integer) {
            Integer modifier = (Integer)object;
            String name = String.valueOf(modifier);
            Vertex newVertex = new Vertex(g, modifier, name, true);
            VertexMap.put(object, newVertex);
            return newVertex;
        }
        else {
            String message = "unknown vertex type:" + object.getClass().toString();
            Util.LOGGER.warning(message);
            return null;
        }
    }

    public static Vertex getVertexAndAddToScope(Graph g, HashSet<Vertex> scope, Object object) {
        Vertex v = getVertexFromObject(g, object);
        if (v != null) {
            scope.add(v);
        }
        return v;
    }

    public String toString() {
        return this.toJson().toString();
    }

    public JSONObject toJson() {
        JSONObject jsonObject = new JSONObject();
        jsonObject.put("v", id);
        if (isKnown)
            jsonObject.put("giv", name);
        else
            jsonObject.put("inf", name);
        return jsonObject;
    }

    public HashMap<String, Object> toMap() {
        HashMap<String, Object> vertexMap = new HashMap<>();
        vertexMap.put("v", id);
        if (isKnown)
            vertexMap.put("giv", name);
        else
            vertexMap.put("inf", name);
        return vertexMap;
    }

    public void restoreName(String name) {
        if (!name.endsWith(">"))
            name += "_predict";
        if (this.content instanceof SootClass) {
            SootClass cls = (SootClass) this.content;
            cls.setName(cls.getPackageName() + "." + name);
        }
        else if (this.content instanceof SootMethod) {
            SootMethod method = (SootMethod) this.content;
            method.setName(name);
        }
        else if (this.content instanceof SootField) {
            SootField field = (SootField) this.content;
            field.setName(name);
        }
        else {
            String message = "unknown vertex type:" + this.content.getClass().toString();
            Util.LOGGER.warning(message);
        }
    }
}