package com.lynnlyc.graph;

import com.lynnlyc.Config;
import com.lynnlyc.Util;
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

    // Edge types:
    // OO, TY, MD, DU, CR, UO, UA

    // relationships between classes
    public static final String TYPE_INHERIT = "OO_CC_inh";
    public static final String TYPE_OUTER = "OO_CC_outer";
    public static final String TYPE_IMPLEMENT = "OO_CC_impl";

    // relationships inside class
    public static final String TYPE_FIELD = "OO_CF_has";
    public static final String TYPE_METHOD = "OO_CM_has";
    public static final String TYPE_CONSTRUCTOR = "OO_CM_cons";
    public static final String TYPE_CLASS_MODIFIER = "MD_CO_mod";
    public static final String TYPE_METHOD_MODIFIER = "MD_MO_mod";
    public static final String TYPE_FIELD_MODIFIER = "MD_FO_mod";
    public static final String TYPE_PARAMETER = "TY_MT_para_";
    public static final String TYPE_FIELD_INSTANCE = "TY_FT_ins";

    // inside a method
    public static final String TYPE_METHOD_RET_INSTANCE = "TY_MT_ins";
    public static final String TYPE_EXCEPTION = "CR_MC_exp";
    public static final String TYPE_USE_FIELD = "CR_MF_use";
    public static final String TYPE_USE_METHOD = "CR_MM_use";
    // public static final String TYPE_USE_CONSTANT = "MS_const";
    // Usage order
    public static final String TYPE_USE_ORDER = "UO_MF_MF";

    // define-use relationships
    // a field is used to define another field
    public static final String TYPE_DEFINE_USE_FIELD_TO_FIELD = "DU_FF_ff";
    // a method parameter is used to define a field
    public static final String TYPE_DEFINE_USE_PARA_TO_FIELD = "DU_MF_pf_";
    // a field is used to define a method parameter
    public static final String TYPE_DEFINE_USE_FIELD_TO_PARA = "DU_FM_fp_";
    // a method ret is used to define a field
    public static final String TYPE_DEFINE_USE_RET_TO_FILED = "DU_MF_rf";
    // a field is used to define a method return
    public static final String TYPE_DEFINE_USE_FILED_TO_RET = "DU_FM_fr";
    // a method ret is used to define a method parameter
    public static final String TYPE_DEFINE_USE_RET_TO_PARA = "DU_MM_rp_";
    // a method para is used to define a method ret
    public static final String TYPE_DEFINE_USE_PARA_TO_RET = "DU_MM_pr_";
    // a method para is used to define a method para
    public static final String TYPE_DEFINE_USE_PARA_TO_PARA = "DU_MM_pp_";
    // a method ret is used to define another method's ret
    public static final String TYPE_DEFINE_USE_RET_TO_RET = "DU_MM_rr";

    // packages and classes
    public static final String TYPE_PACKAGE_JOINT = "OO_PP_join";
    public static final String TYPE_BELONG_TO_PACKAGE = "OO_CP_belong";

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

        if (!this.isEnabled())
            return false;

        SootClass source_cls = source.getSootClass();
        SootClass target_cls = target.getSootClass();
        if (source_cls == null || target_cls == null) return true;
        if (source_cls.isApplicationClass() && target_cls.isApplicationClass()) return true;
        if (source_cls.isLibraryClass() && target_cls.isLibraryClass()) return false;
        this.type += "_LIB";
        return true;
    }

    private boolean isEnabled() {
        if (this.type.length() < 2) {
            Util.LOGGER.warning("unknown edge type: " + this.type);
            return false;
        }
        String relationType = this.type.substring(0, 2);
        if (relationType.equals("OO")) {
            return Config.enable_oo;
        }
        if (relationType.equals("TY")) {
            return Config.enable_type;
        }
        if (relationType.equals("MD")) {
            return Config.enable_modifier;
        }
        if (relationType.equals("DU")) {
            return Config.enable_def_use;
        }
        if (relationType.equals("CR")) {
            return Config.enable_call_ret;
        }
        if (relationType.equals("UO")) {
            return Config.enable_usage_order;
        }
        if (relationType.equals("UA")) {
            return Config.enable_usage_after;
        }
        Util.LOGGER.warning("unknown edge type: " + this.type);
        return false;
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

    public String getS2Tstr() {return String.format("%d->%d", source.id, target.id);}
    public String getT2Sstr() {return String.format("%d->%d", target.id, source.id);}
}
