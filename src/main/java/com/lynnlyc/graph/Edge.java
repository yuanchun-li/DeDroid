package com.lynnlyc.graph;

import org.json.JSONObject;
import soot.SootClass;

import java.util.HashMap;

/**
 * Created by LiYC on 2015/7/19.
 * Package: UnuglifyDEX
 */
public class Edge {
    public String type;
    public Vertex source;
    public Vertex target;

    // Each edge describe a relation between two elements
    // Class: C, Type: T, Method: M, Field: F, Package: P, Modifier: O, Constant: S

    // relationships between classes
    public static final String TYPE_INHERIT = "CC_inh";
    public static final String TYPE_OUTER = "CC_outer";
    public static final String TYPE_IMPLEMENT = "CC_impl";

    // relationships inside class
    public static final String TYPE_FIELD = "CF_has";
    public static final String TYPE_METHOD = "CM_has";
    public static final String TYPE_CONSTRUCTOR = "CM_cons";
    public static final String TYPE_CLASS_MODIFIER = "CO_mod";
    public static final String TYPE_METHOD_MODIFIER = "MO_mod";
    public static final String TYPE_FIELD_MODIFIER = "FO_mod";
    public static final String TYPE_PARAMETER = "MT_para_";
    public static final String TYPE_FIELD_INSTANCE = "FT_ins";

    // inside a method
    public static final String TYPE_METHOD_RET_INSTANCE = "MT_ins";
    public static final String TYPE_EXCEPTION = "MC_exp";
    public static final String TYPE_USE_FIELD = "MF_use";
    public static final String TYPE_USE_METHOD = "MM_use";
    // public static final String TYPE_USE_CONSTANT = "MS_const";
    // Usage order
    public static final String TYPE_USE_ORDER = "MF_MF_usage_order";

    // define-use relationships
    // a field is used to define another field
    public static final String TYPE_DEFINE_USE_FIELD_TO_FIELD = "FF_DU_ff";
    // a method parameter is used to define a field
    public static final String TYPE_DEFINE_USE_PARA_TO_FIELD = "MF_DU_pf_";
    // a field is used to define a method parameter
    public static final String TYPE_DEFINE_USE_FIELD_TO_PARA = "FM_DU_fp_";
    // a method ret is used to define a field
    public static final String TYPE_DEFINE_USE_RET_TO_FILED = "MF_DU_rf";
    // a field is used to define a method return
    public static final String TYPE_DEFINE_USE_FILED_TO_RET = "FM_DU_fr";
    // a method ret is used to define a method parameter
    public static final String TYPE_DEFINE_USE_RET_TO_PARA = "MM_DU_rp_";
    // a method para is used to define a method ret
    public static final String TYPE_DEFINE_USE_PARA_TO_RET = "MM_DU_pr_";
    // a method para is used to define a method para
    public static final String TYPE_DEFINE_USE_PARA_TO_PARA = "MM_DU_pp_";
    // a method ret is used to define another method's ret
    public static final String TYPE_DEFINE_USE_RET_TO_RET = "MM_DU_rr";

    // packages and classes
    public static final String TYPE_PACKAGE_JOINT = "PP_join";
    public static final String TYPE_BELONG_TO_PACKAGE = "CP_belong";

    public Edge(Graph g, String type, Vertex source, Vertex target) {
        this.type = type;
        this.source = source;
        this.target = target;

        if (this.isValid())
            g.edgeSet.add(this);
    }

    private boolean isValid() {
        if (source == null || target == null || source == target)
            return false;
        SootClass source_cls = source.getSootClass();
        SootClass target_cls = target.getSootClass();
        if (source_cls == null || target_cls == null) return true;
        if (source_cls.isApplicationClass() && target_cls.isApplicationClass()) return true;
        if (source_cls.isLibraryClass() && target_cls.isLibraryClass()) return false;
        this.type += "_LIB";
        return true;
    }

    @Override
    public boolean equals(Object o) {
        return ((o instanceof Edge) && this.type.equals(((Edge) o).type)
                && this.source == ((Edge) o).source && this.target == ((Edge) o).target);
    }

    public JSONObject toJson() {
        return new JSONObject(this.toMap());
    }

    public HashMap<String, Object> toMap() {
        HashMap<String, Object> edgeMap = new HashMap<>();
        edgeMap.put("a", source.id);
        edgeMap.put("b", target.id);
        edgeMap.put("f2", type);
        return edgeMap;
    }

    public String toString() {
        return this.toJson().toString();
    }
}
