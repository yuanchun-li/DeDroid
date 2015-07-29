package com.lynnlyc.sootextension;

import com.lynnlyc.Config;
import com.lynnlyc.Predictor;
import com.lynnlyc.Util;
import com.lynnlyc.graph.Edge;
import com.lynnlyc.graph.Graph;
import com.lynnlyc.graph.Vertex;
import soot.*;
import soot.jimple.FieldRef;
import soot.jimple.InvokeExpr;

import java.util.ArrayList;
import java.util.HashSet;

/**
 * Created by LiYC on 2015/7/19.
 * Package: UnuglifyDEX
 */
public class FigureExtractor {

    public FigureExtractor() {
        ObfuscationDetector.v();
    }

    public Graph run() {
        Util.LOGGER.info("extracting features");
        if (!Config.isInitialized) {
            Util.LOGGER.warning("Configuration not initialized");
            return null;
        }
//        PackManager.v().runPacks();
        Graph g = new Graph();
        HashSet<Vertex> globalScope = g.getNewScope();
        globalScope.add(g.v_root);

        Util.LOGGER.info("generating graph");
        for (SootClass cls : Config.applicationClasses) {
            if (Config.isTraining && ObfuscationDetector.v().isObfuscated(cls))
                continue;

            Vertex v_cls = Vertex.getVertexAndAddToScope(g, globalScope, cls);

            // add belong to package edges
            // add package_joint edges (inside this call)
            new Edge(g, Edge.TYPE_BELONG_TO_PACKAGE, v_cls,
                    Vertex.getLastSegVertex(g, globalScope, cls.getPackageName()));

            // add INHERIT edges
            if (cls.hasSuperclass()) {
                SootClass super_cls = cls.getSuperclass();
                Vertex v_super_cls = Vertex.getVertexAndAddToScope(
                        g, globalScope, super_cls);
                new Edge(g, Edge.TYPE_INHERIT, v_cls, v_super_cls);
            }

            // add OUTER edges
            if (cls.hasOuterClass()) {
                SootClass outer_cls = cls.getOuterClass();
                Vertex v_outer_cls = Vertex.getVertexAndAddToScope(
                        g, globalScope, outer_cls);
                new Edge(g, Edge.TYPE_OUTER, v_cls, v_outer_cls);
            }

            // add implement edges
            for (SootClass interface_cls : cls.getInterfaces()) {
                Vertex v_interface_cls = Vertex.getVertexAndAddToScope(
                        g, globalScope, interface_cls);
                new Edge(g, Edge.TYPE_IMPLEMENT, v_cls, v_interface_cls);
            }

            // add class modifier edges
            int cls_modifier = cls.getModifiers();
            Vertex v_cls_modifier = Vertex.getVertexFromObject(
                    g, cls_modifier);
            new Edge(g, Edge.TYPE_MODIFIER, v_cls, v_cls_modifier);

            // Consider the scope inside the class
            HashSet<Vertex> classScope = g.getNewScope();
            classScope.add(v_cls);
            // for each field
            for (SootField field : cls.getFields()) {
                // add field edges
                Vertex v_field = Vertex.getVertexAndAddToScope
                        (g, classScope, field);
                new Edge(g, Edge.TYPE_FIELD, v_cls, v_field);

                // add field type edges
                Type type = field.getType();
                Vertex v_type = Vertex.getVertexAndAddToScope(
                        g, classScope, type);
                new Edge(g, Edge.TYPE_INSTANCE, v_field, v_type);

                // add field modifier edges
                int field_modifier = field.getModifiers();
                Vertex v_field_modifier = Vertex.getVertexFromObject
                        (g, field_modifier);
                new Edge(g, Edge.TYPE_MODIFIER, v_field, v_field_modifier);
            }

            // for each method
            for (SootMethod method : cls.getMethods()) {
                // add method edges
                Vertex v_method = Vertex.getVertexAndAddToScope(
                        g, classScope, method);
                new Edge(g, Edge.TYPE_METHOD, v_cls, v_method);

                // add method return type edges
                Type ret_type = method.getReturnType();
                Vertex v_ret_type = Vertex.getVertexAndAddToScope(
                        g, classScope, ret_type);
                new Edge(g, Edge.TYPE_INSTANCE, v_method, v_ret_type);

                // add method parameter type edges
                for (Type para_type : method.getParameterTypes()) {
                    Vertex v_para_type = Vertex.getVertexAndAddToScope(
                            g, classScope, para_type);
                    new Edge(g, Edge.TYPE_PARAMETER, v_method, v_para_type);
                }

                // add exception edges
                for (SootClass exception_cls : method.getExceptions()) {
                    Vertex v_exception_cls = Vertex.getVertexAndAddToScope(
                            g, classScope, exception_cls);
                    new Edge(g, Edge.TYPE_EXCEPTION, v_method, v_exception_cls);
                }

                // consider the scope inside a method
                if (method.getSource() == null) continue;
                try {
                    HashSet<Vertex> methodScope = g.getNewScope();
                    methodScope.add(v_method);
                    Body body = method.retrieveActiveBody();
                    for (ValueBox valueBox : body.getUseAndDefBoxes()) {
                        Value value = valueBox.getValue();
                        if (value instanceof FieldRef) {
                            Vertex v_used_field = Vertex.getVertexAndAddToScope(
                                    g, methodScope, ((FieldRef) value).getField());
                            new Edge(g, Edge.TYPE_USE_FIELD, v_method, v_used_field);
                        } else if (value instanceof InvokeExpr) {
                            Vertex v_used_method = Vertex.getVertexAndAddToScope(
                                    g, methodScope, ((InvokeExpr) value).getMethod());
                            new Edge(g, Edge.TYPE_USE_METHOD, v_method, v_used_method);
                        }
                    }
                } catch (Exception e) {
                    Util.logException(e);
                }
            }
        }
        Util.LOGGER.info("finished extracting features");
        if (!Config.isTraining)
            Predictor.transform(g);
        return g;
    }
}
