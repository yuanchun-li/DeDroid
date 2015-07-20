package com.lynnlyc.graph;

import net.sf.json.JSONObject;

/**
 * Created by LiYC on 2015/7/19.
 * Package: UnuglifyDEX
 */
public class Edge {
    public String type;
    public Vertex source;
    public Vertex target;

    public static final String TYPE_INHERIT = "inherit";
    public static final String TYPE_IMPLEMENT = "implement";
    public static final String TYPE_FIELD = "field";
    public static final String TYPE_METHOD = "method";
    public static final String TYPE_MODIFIER = "modifier";
    public static final String TYPE_PARAMETER = "parameter";
    public static final String TYPE_INSTANCE = "instance";
    public static final String TYPE_EXCEPTION = "exception";
    public static final String TYPE_USE_FIELD = "use_field";
    public static final String TYPE_USE_METHOD = "use_method";

    public Edge(Graph g, String type, Vertex source, Vertex target) {
        this.type = type;
        this.source = source;
        this.target = target;
        g.edges.add(this);
    }

    public JSONObject toJson() {
        JSONObject jsonObject = new JSONObject();
        jsonObject.put("a", source.id);
        jsonObject.put("b", target.id);
        jsonObject.put("f2", type);
        return jsonObject;
    }

    public String toString() {
        return this.toJson().toString();
    }
}
