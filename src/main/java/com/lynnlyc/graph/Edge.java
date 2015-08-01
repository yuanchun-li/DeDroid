package com.lynnlyc.graph;

import org.json.JSONObject;

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
    // Class: C, Type: T, Method: M, Field: F, Package: P, Modifier: O

    // relationships between classes
    public static final String TYPE_INHERIT = "C_C_inherit";
    public static final String TYPE_OUTER = "C_C_outer";
    public static final String TYPE_IMPLEMENT = "C_C_implement";

    // relationships inside class
    public static final String TYPE_FIELD = "C_F_field";
    public static final String TYPE_METHOD = "C_M_method";
    public static final String TYPE_CLASS_MODIFIER = "C_O_modifier";
    public static final String TYPE_METHOD_MODIFIER = "M_O_modifier";
    public static final String TYPE_FIELD_MODIFIER = "F_O_modifier";
    public static final String TYPE_PARAMETER = "M_T_para_";
    public static final String TYPE_FIELD_INSTANCE = "F_T_instance";

    // inside a method
    public static final String TYPE_METHOD_RET_INSTANCE = "M_T_instance";
    public static final String TYPE_EXCEPTION = "M_C_exception";
    public static final String TYPE_USE_FIELD = "M_F_use";
    public static final String TYPE_USE_METHOD = "M_M_use";

    // define-use relationships
    // a field is used to define another field
    public static final String TYPE_DEFINE_USE_FIELD_FILED = "F_F_define_use";
    // a method parameter is used to define a field
    public static final String TYPE_DEFINE_USE_PARA_FIELD = "M_F_define_use_para_";
    // a field is used to define a method parameter
    public static final String TYPE_DEFINE_USE_FIELD_PARA = "F_M_define_use_para_";
    // return of a method is used to define a field
    public static final String TYPE_DEFINE_USE_RET_FILED = "M_F_define_use_ret";
    // a field is used to define a method return
    public static final String TYPE_DEFINE_USE_FILED_RET = "F_M_define_use_ret";


    // packages and classes
    public static final String TYPE_PACKAGE_JOINT = "P_P_joint";
    public static final String TYPE_BELONG_TO_PACKAGE = "C_P_belong";

    public Edge(Graph g, String type, Vertex source, Vertex target) {
        this.type = type;
        this.source = source;
        this.target = target;
        if (source != null && target != null && source != target)
            g.edgeSet.add(this);
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
