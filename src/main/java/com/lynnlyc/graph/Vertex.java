package com.lynnlyc.graph;

import com.lynnlyc.Config;
import com.lynnlyc.Util;
import com.lynnlyc.sootextension.ObfuscationDetector;
import com.lynnlyc.sootextension.PackageSeg;
import org.json.JSONObject;
import soot.*;

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

    private String predictedName;

    private static int count = 0;

    public Vertex(Graph g, Object content, String name, boolean isKnown) {
        this.content = content;
        this.name = name;
        this.isKnown = isKnown;
        this.id = count;
        this.predictedName = name;
        count++;
        g.vertexes.add(this);
        g.vertexMap.put(content, this);
    }

    public static Vertex getVertexFromObject(Graph g, Object object) {
        HashMap<Object, Vertex> VertexMap = g.vertexMap;
        if (VertexMap.containsKey(object)) {
            return VertexMap.get(object);
        }

        if (Config.isTraining && ObfuscationDetector.v().isObfuscated(object))
            return null;

        if (object instanceof SootClass) {
            SootClass cls = (SootClass) object;
            String name = cls.getShortName();
            boolean isKnown = false;
            if (cls.isLibraryClass()) isKnown = true;
            return new Vertex(g, cls, name, isKnown);
        }
        if (object instanceof SootMethod) {
            SootMethod method = (SootMethod) object;
            String name = method.getName();
            boolean isKnown = false;
            if (method.getDeclaringClass().isLibraryClass()) isKnown = true;
            else if (method.isConstructor()) isKnown = true;
            else if (name.startsWith("<") && name.endsWith(">")) isKnown = true;
            return new Vertex(g, method, name, isKnown);
        }
        if (object instanceof SootField) {
            SootField field = (SootField) object;
            String name = field.getName();
            boolean isKnown = false;
            if (field.getDeclaringClass().isLibraryClass()) isKnown = true;
            return new Vertex(g, field, name, isKnown);
        }
        if (object instanceof Type) {
            Type type = (Type) object;
            if (type instanceof RefType) {
                RefType refType = (RefType) type;
                return getVertexFromObject(g, refType.getSootClass());
            }
            String name = type.toString();
            return new Vertex(g, type, name, true);
        }
        if (object instanceof Integer) {
            Integer modifier = (Integer)object;
            String name = String.valueOf(modifier);
            return new Vertex(g, modifier, name, true);
        }
        if (object instanceof PackageSeg) {
            PackageSeg packageSeg = (PackageSeg) object;
            return new Vertex(g, packageSeg, packageSeg.getSegName(), false);
        }
        else {
            String message = "unknown vertex type:" + object.getClass().toString();
            Util.LOGGER.warning(message);
            return null;
        }
    }

    public static Vertex getVertexAndAddToScope(Graph g, HashSet<Vertex> scope, Object object) {
        Vertex v = getVertexFromObject(g, object);
        if (v != null && scope != null) {
            scope.add(v);
        }
        return v;
    }

    public static Vertex getLastSegVertex(Graph g, HashSet<Vertex> scope, String packageName) {
        if (packageName == null || packageName.length() == 0) {
            return g.v_root;
        }
        if (g.lastSegVertexOfPackage.containsKey(packageName)) {
            return g.lastSegVertexOfPackage.get(packageName);
        }

        String lastSegStr, prevSegsStr;
        int lastDot = packageName.lastIndexOf('.');
        if (lastDot < 0) {
            lastSegStr = packageName;
            prevSegsStr = null;
        } else {
            lastSegStr = packageName.substring(lastDot + 1);
            prevSegsStr = packageName.substring(0, lastDot);
        }

        PackageSeg lastSeg = new PackageSeg(packageName, lastSegStr);
        Vertex v_lastSeg = Vertex.getVertexAndAddToScope(g, scope, lastSeg);
        Vertex v_prevSeg = getLastSegVertex(g, scope, prevSegsStr);
        new Edge(g, Edge.TYPE_PACKAGE_JOINT, v_lastSeg, v_prevSeg);
        g.lastSegVertexOfPackage.put(packageName, v_lastSeg);

        return v_lastSeg;
    }

    public String toString() {
        return this.toJson().toString();
    }

    public JSONObject toJson() {
        return new JSONObject(this.toMap());
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

    public String getPredictedName() {
        return predictedName;
    }

    public void setPredictedName(String predictedName) {
        this.predictedName = predictedName;
    }
}