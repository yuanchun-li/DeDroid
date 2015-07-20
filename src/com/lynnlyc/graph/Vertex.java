package com.lynnlyc.graph;

import com.lynnlyc.Config;
import com.lynnlyc.Util;
import net.sf.json.JSONArray;
import net.sf.json.JSONObject;
import net.sf.json.util.JSONUtils;
import soot.*;

import java.io.*;
import java.nio.charset.Charset;
import java.nio.file.Files;
import java.util.HashMap;
import java.util.HashSet;

/**
 * Created by LiYC on 2015/7/19.
 */
public class Vertex {
    public Object content;
    public int id;
    public boolean isKnown = false;
    public String name;
    private static int Count = 0;

    public static HashMap<Integer, Vertex> infVertex = new HashMap<Integer, Vertex>();

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
            Vertex newVertex = new Vertex(g, object, name, isKnown);
            VertexMap.put(object, newVertex);
            return newVertex;
        }
        if (object instanceof SootMethod) {
            SootMethod method = (SootMethod) object;
            String name = method.getName();
            boolean isKnown = false;
            if (method.getDeclaringClass().isLibraryClass()) isKnown = true;
            if (method.isConstructor()) isKnown = true;
            Vertex newVertex = new Vertex(g, object, name, isKnown);
            VertexMap.put(object, newVertex);
            return newVertex;
        }
        if (object instanceof SootField) {
            SootField field = (SootField) object;
            String name = field.getName();
            boolean isKnown = false;
            if (field.getDeclaringClass().isLibraryClass()) isKnown = true;
            Vertex newVertex = new Vertex(g, object, name, isKnown);
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
            Vertex newVertex = new Vertex(g, object, name, true);
            VertexMap.put(object, newVertex);
            return newVertex;
        }
        if (object instanceof Integer) {
            int modifier = (Integer)object;
            String name = String.valueOf(modifier);
            Vertex newVertex = new Vertex(g, object, name, true);
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

    public void restoreName(String name) {
        Object object = this.content;
        if (object instanceof SootClass) {
            SootClass cls = (SootClass) object;
            cls.setName(cls.getPackageName() + "." + name);
        }
        if (object instanceof SootMethod) {
            SootMethod method = (SootMethod) object;
            method.setName(name);
        }
        if (object instanceof SootField) {
            SootField field = (SootField) object;
            field.setName(name);
        }
        else {
            String message = "unknown vertex type:" + object.getClass().toString();
            Util.LOGGER.warning(message);
        }
    }
}


class UnknownVertexTypeException extends Exception {
    public UnknownVertexTypeException(String message) {
        super(message);
    }
}