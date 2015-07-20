package com.lynnlyc;

import com.lynnlyc.graph.Edge;
import com.lynnlyc.graph.Graph;
import com.lynnlyc.graph.Vertex;
import soot.*;
import soot.jimple.FieldRef;
import soot.jimple.InvokeExpr;

import java.io.PrintStream;
import java.util.HashSet;

/**
 * Created by LiYC on 2015/7/19.
 * Package: UnuglifyDEX
 */
public class SootAnalysis {

    public SootAnalysis() {
        Scene.v().loadNecessaryClasses();
    }

    public void dump(PrintStream os) {
        os.println("===Application Classes===");
        for (SootClass cls : Scene.v().getApplicationClasses()) {
            os.println("---class info---");
            os.println(cls);
            os.println("getPackageName" + ":" + cls.getPackageName());
            os.println("getJavaPackageName:" + ":" + cls.getJavaPackageName());
            os.println("getName" + ":" + cls.getName());
            os.println("getModifiers" + ":" + cls.getModifiers());
            os.println("getSuperclass" + ":" + cls.getSuperclass());

            os.println("--fields--");
            for (SootField f : cls.getFields()) {
                os.println("-field info-");
                os.println(f);
                os.println("getDeclaration" + ":" + f.getDeclaration());
                os.println("getDeclaringClass" + ":" + f.getDeclaringClass());
                os.println("getName" + ":" + f.getName());
                os.println("getModifiers" + ":" + f.getModifiers());
                os.println("getNumber" + ":" + f.getNumber());
                os.println("getSignature" + ":" + f.getSignature());
                os.println("getType" + ":" + f.getType());
                os.println("getSubSignature" + ":" + f.getSubSignature());
                os.println("-end of field info-");

            }
            for (SootMethod m : cls.getMethods()) {
                os.println("-method info-");
                os.println(m);
                os.println("getDeclaration" + ":" + m.getDeclaration());
                os.println("getDeclaringClass" + ":" + m.getDeclaringClass());
                os.println("getName" + ":" + m.getName());
                os.println("getModifiers" + ":" + m.getModifiers());
                os.println("getBytecodeParms" + ":" + m.getBytecodeParms());
                os.println("getBytecodeSignature" + ":" + m.getBytecodeSignature());
                os.println("getSignature" + ":" + m.getSignature());
                os.println("getParameterTypes" + ":" + m.getParameterTypes());
                os.println("getExceptions" + ":" + m.getExceptions());

                os.println("method body:");
                Body b = m.retrieveActiveBody();
                os.println(b);
                os.println("-end of method info-");
            }
            os.println("---end of class info---");
        }
        os.println("===end of Application Classes===");
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

        Util.LOGGER.info("generating graph");
        for (SootClass cls : Scene.v().getApplicationClasses()) {
            Vertex v_cls = Vertex.getVertexAndAddToScope(g, globalScope, cls);

            // add INHERIT edges
            SootClass super_cls = cls.getSuperclass();
            if (super_cls != null) {
                Vertex v_super_cls = Vertex.getVertexAndAddToScope(
                        g, globalScope, super_cls);
                new Edge(g, Edge.TYPE_INHERIT, v_cls, v_super_cls);
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
        return g;
    }
}
