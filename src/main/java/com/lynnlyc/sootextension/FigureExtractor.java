package com.lynnlyc.sootextension;

import com.lynnlyc.Config;
import com.lynnlyc.Predictor;
import com.lynnlyc.Util;
import com.lynnlyc.graph.Edge;
import com.lynnlyc.graph.Graph;
import com.lynnlyc.graph.Vertex;
import soot.*;
import soot.Body;
import soot.dava.toolkits.base.AST.structuredAnalysis.ReachingDefs;
import soot.jimple.*;
import soot.jimple.Stmt;
import soot.jimple.internal.*;
import soot.toolkits.graph.BriefUnitGraph;
import soot.toolkits.graph.pdg.HashMutablePDG;
import soot.toolkits.scalar.*;

import java.util.HashSet;
import java.util.List;

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
            new Edge(g, Edge.TYPE_CLASS_MODIFIER, v_cls, v_cls_modifier);

            // Consider the scope inside the class
            HashSet<Vertex> classScope = g.getNewScope();
            classScope.add(v_cls);
            // for each field
            for (SootField field : cls.getFields()) {
                // add field edges
                Vertex v_field = Vertex.getVertexAndAddToScope(
                        g, classScope, field);
                new Edge(g, Edge.TYPE_FIELD, v_cls, v_field);

                // add field type edges
                Type type = field.getType();
                Vertex v_type = Vertex.getVertexAndAddToScope(
                        g, classScope, type);
                new Edge(g, Edge.TYPE_FIELD_INSTANCE, v_field, v_type);

                // add field modifier edges
                int field_modifier = field.getModifiers();
                Vertex v_field_modifier = Vertex.getVertexFromObject(
                        g, field_modifier);
                new Edge(g, Edge.TYPE_FIELD_MODIFIER, v_field, v_field_modifier);
            }

            // for each method
            for (SootMethod method : cls.getMethods()) {
                // add method edges
                Vertex v_method = Vertex.getVertexAndAddToScope(
                        g, classScope, method);
                if (method.isConstructor())
                    new Edge(g, Edge.TYPE_CONSTRUCTOR, v_cls, v_method);
                else
                    new Edge(g, Edge.TYPE_METHOD, v_cls, v_method);

                // add method return type edges
                Type ret_type = method.getReturnType();
                Vertex v_ret_type = Vertex.getVertexAndAddToScope(
                        g, classScope, ret_type);
                new Edge(g, Edge.TYPE_METHOD_RET_INSTANCE, v_method, v_ret_type);

                // add method parameter type edges
                int para_index = 0;
                for (Type para_type : method.getParameterTypes()) {
                    Vertex v_para_type = Vertex.getVertexAndAddToScope(
                            g, classScope, para_type);
                    new Edge(g, Edge.TYPE_PARAMETER + para_index++, v_method, v_para_type);
                }

                // add exception edges
                for (SootClass exception_cls : method.getExceptions()) {
                    Vertex v_exception_cls = Vertex.getVertexAndAddToScope(
                            g, classScope, exception_cls);
                    new Edge(g, Edge.TYPE_EXCEPTION, v_method, v_exception_cls);
                }

                // add method modifier edges
                int method_modifier = method.getModifiers();
                Vertex v_method_modifier = Vertex.getVertexFromObject
                        (g, method_modifier);
                new Edge(g, Edge.TYPE_METHOD_MODIFIER, v_method, v_method_modifier);

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
//                        else if (value instanceof Constant) {
//                            Vertex v_used_constant = Vertex.getVertexFromObject(g, value);
//                            new Edge(g, Edge.TYPE_USE_CONSTANT, v_method, v_used_constant);
//                        }
                    }

                    BriefUnitGraph ug = new BriefUnitGraph(body);
                    SimpleLocalDefs localDefs = new SimpleLocalDefs(ug);
                    SimpleLocalUses localUses = new SimpleLocalUses(body, localDefs);

                    // consider field def-use relationships
                    for (Unit u : body.getUnits()) {
                        for (ValueBox useBox : u.getUseBoxes()) {
                            Value value = useBox.getValue();
                            if (value instanceof FieldRef) {
                                // if this stmt used a field
                                // get all usages of this stmt, and add field-use edges
                                Vertex v_used_field = Vertex.getVertexAndAddToScope(
                                        g, methodScope, ((FieldRef) value).getField());
                                HashSet<UnitValueBoxPair> allUses = new HashSet<>();
                                getAllUsesOf(u, allUses, localUses);

                                for (UnitValueBoxPair u_vb : allUses) {
                                    Unit u_use = u_vb.getUnit();
                                    if (!(u_use instanceof Stmt))
                                        continue;
                                    Stmt s_use = (Stmt) u_use;

                                    Value v_use = u_vb.getValueBox().getValue();
                                    if (s_use instanceof JAssignStmt) {
                                        Value leftOpValue = ((JAssignStmt) s_use).getLeftOp();
                                        if (leftOpValue instanceof FieldRef) {
                                            Vertex v_def_field = Vertex.getVertexAndAddToScope(
                                                    g, methodScope, ((FieldRef) value).getField());
                                            new Edge(g, Edge.TYPE_DEFINE_USE_FIELD_FIELD,
                                                    v_used_field, v_def_field);
                                        }
                                    }
                                    else if (s_use instanceof JReturnStmt) {
                                        new Edge(g, Edge.TYPE_DEFINE_USE_FILED_RET,
                                                v_used_field, v_method);
                                    }
                                    if (s_use.containsInvokeExpr()) {
                                        InvokeExpr invoke_expr = s_use.getInvokeExpr();
                                        Vertex v_invoked = Vertex.getVertexAndAddToScope(
                                                g, methodScope, invoke_expr.getMethod());
                                        int para_idx = invoke_expr.getArgs().indexOf(v_use);
                                        if (para_idx < 0) continue;
                                        new Edge(g, Edge.TYPE_DEFINE_USE_FIELD_PARA + para_idx,
                                                v_used_field, v_invoked);
                                    }
                                }
                            }
                        }

                        for (ValueBox defBox : u.getDefBoxes()) {
                            Value value = defBox.getValue();
                            if (value instanceof FieldRef) {
                                // if this stmt defined a field
                                // get all defs of this stmt, and add field-def edges
                                Vertex v_defined_field = Vertex.getVertexAndAddToScope(
                                        g, methodScope, ((FieldRef) value).getField());
                                HashSet<Unit> allDefs = new HashSet<>();
                                getAllDefsOf(u, allDefs, localDefs);

                                for (Unit u_def : allDefs) {
                                    if (!(u_def instanceof Stmt))
                                        continue;
                                    Stmt s_def = (Stmt) u_def;

                                    if (s_def instanceof JIdentityStmt) {
                                        Value rOp = ((JIdentityStmt) s_def).getRightOp();
                                        if (rOp instanceof ParameterRef) {
                                            int para_idx = ((ParameterRef) rOp).getIndex();
                                            new Edge(g, Edge.TYPE_DEFINE_USE_PARA_FIELD + para_idx,
                                                    v_method, v_defined_field);
                                        }
                                    }
                                    else if (s_def instanceof JInvokeStmt) {
                                        Value rOp = ((JIdentityStmt) s_def).getRightOp();
                                        if (rOp instanceof InvokeExpr) {
                                            Vertex v_invoked = Vertex.getVertexAndAddToScope(
                                                    g, methodScope, ((InvokeExpr) rOp).getMethod());
                                            new Edge(g, Edge.TYPE_DEFINE_USE_RET_FILED,
                                                    v_invoked, v_defined_field);
                                        }
                                    }
                                }
                            }
                        }
                    }

                    // consider field/method usage order
                    UsageOrderAnalysis uoa = new UsageOrderAnalysis(ug);
                    for (Unit u : body.getUnits()) {
                        Vertex v_usage = null;
                        if (!(u instanceof Stmt)) continue;
                        Stmt s = (Stmt) u;
                        if (s.containsFieldRef()) {
                            v_usage = Vertex.getVertexAndAddToScope(g, methodScope,
                                    s.getFieldRef().getField());
                        } else if (s.containsInvokeExpr()) {
                            v_usage = Vertex.getVertexAndAddToScope(g, methodScope,
                                    s.getInvokeExpr().getMethod());
                        }
                        if (v_usage == null) continue;
                        for (SootField f_usage_before : uoa.getFieldUsagesBefore(u)) {
                            Vertex v_usage_before = Vertex.getVertexAndAddToScope(g,
                                    methodScope, f_usage_before);
                            new Edge(g, Edge.TYPE_USE_ORDER, v_usage, v_usage_before);
                        }
                        for (SootMethod m_usage_before : uoa.getMethodUsagesBefore(u)) {
                            Vertex v_usage_before = Vertex.getVertexAndAddToScope(g,
                                    methodScope, m_usage_before);
                            new Edge(g, Edge.TYPE_USE_ORDER, v_usage, v_usage_before);
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
        g.sortGraph();
        return g;
    }

    public void getAllUsesOf(Unit u, HashSet<UnitValueBoxPair> allUses, LocalUses localUses) {
        List<UnitValueBoxPair> uses = localUses.getUsesOf(u);
        for (UnitValueBoxPair unitValueBoxPair : uses) {
            if (allUses.contains(unitValueBoxPair)) continue;
            Unit use = unitValueBoxPair.getUnit();
            allUses.add(unitValueBoxPair);
            getAllUsesOf(use, allUses, localUses);
        }
    }

    public void getAllDefsOf(Unit u, HashSet<Unit> allDefs, LocalDefs localDefs) {
        HashSet<Unit> usedLocalDefs = new HashSet<>();
        for (ValueBox use : u.getUseBoxes()) {
            Value useValue = use.getValue();
            if (useValue instanceof Local) {
                usedLocalDefs.addAll(localDefs.getDefsOfAt((Local) useValue, u));
            }
        }
        for (Unit defUnit : usedLocalDefs) {
            if (allDefs.contains(defUnit)) continue;
            allDefs.add(defUnit);
            getAllDefsOf(defUnit, allDefs, localDefs);
        }
    }
}
