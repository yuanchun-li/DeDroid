package com.lynnlyc.sootextension;

import soot.*;
import soot.jimple.FieldRef;
import soot.jimple.InvokeExpr;
import soot.toolkits.graph.DirectedGraph;
import soot.toolkits.scalar.ArraySparseSet;
import soot.toolkits.scalar.FlowSet;
import soot.toolkits.scalar.ForwardFlowAnalysis;

import java.util.HashMap;
import java.util.HashSet;
import java.util.Map;

/**
 * Created by LiYC on 2015/8/1.
 * Package: com.lynnlyc.sootextension
 */
public class UsageAfterAnalysis extends ForwardFlowAnalysis<Unit, FlowSet<Value>> {
    FlowSet<Value> emptySet = new ArraySparseSet<>();
    Map<Unit, FlowSet<Value>> unitToUsageBefore;
    private HashMap<Unit, HashSet<SootField>> unitToFieldUsagesBefore;
    private HashMap<Unit, HashSet<SootMethod>> unitToMethodUsagesBefore;

    public UsageAfterAnalysis(DirectedGraph graph) {
        super(graph);
        unitToUsageBefore = new HashMap<>();
        unitToFieldUsagesBefore = new HashMap<>();
        unitToMethodUsagesBefore = new HashMap<>();
        doAnalysis();
    }

    @Override
    protected void flowThrough(FlowSet<Value> in, Unit u, FlowSet<Value> out) {
        if (unitToUsageBefore.containsKey(u)) return;
        unitToUsageBefore.put(u, in);
        in.copy(out);
        for (ValueBox vb : u.getUseAndDefBoxes()) {
            Value v = vb.getValue();
            if (v instanceof InvokeExpr || v instanceof FieldRef) {
                out.add(v);
            }
        }

    }

    @Override
    protected FlowSet<Value> newInitialFlow() {
        return emptySet.clone();
    }

    @Override
    protected FlowSet<Value> entryInitialFlow() {
        return emptySet.clone();
    }

    @Override
    protected void merge(FlowSet<Value> in1, FlowSet<Value> in2, FlowSet<Value> out) {
        in1.union(in2, out);
    }

    @Override
    protected void copy(FlowSet<Value> source, FlowSet<Value> dest) {
        source.copy(dest);
    }

    public HashSet<SootField> getFieldUsagesBefore(Unit u) {
        if (!unitToFieldUsagesBefore.containsKey(u)) {
            specifyUsagesBefore(u);
        }
        return unitToFieldUsagesBefore.get(u);
    }

    public HashSet<SootMethod> getMethodUsagesBefore(Unit u) {
        if (!unitToMethodUsagesBefore.containsKey(u)) {
            specifyUsagesBefore(u);
        }
        return unitToMethodUsagesBefore.get(u);
    }

    private void specifyUsagesBefore(Unit u) {
        FlowSet<Value> usagesBefore = unitToUsageBefore.get(u);
        HashSet<SootField> fieldUsages = new HashSet<>();
        HashSet<SootMethod> methodUsages = new HashSet<>();
        for (Value usage : usagesBefore) {
            if (usage instanceof FieldRef) {
                fieldUsages.add(((FieldRef) usage).getField());
            }
            if (usage instanceof InvokeExpr) {
                methodUsages.add(((InvokeExpr) usage).getMethod());
            }
        }
        unitToFieldUsagesBefore.put(u, fieldUsages);
        unitToMethodUsagesBefore.put(u, methodUsages);
    }
}
