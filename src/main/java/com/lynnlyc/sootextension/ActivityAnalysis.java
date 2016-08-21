package com.lynnlyc.sootextension;

import com.lynnlyc.Config;
import com.lynnlyc.Predictor;
import com.lynnlyc.Util;
import com.lynnlyc.derg.core.Edge;
import com.lynnlyc.derg.core.Graph;
import com.lynnlyc.derg.core.Vertex;
import soot.*;
import soot.Body;
import soot.dava.internal.SET.SETSynchronizedBlockNode;
import soot.jimple.*;
import soot.jimple.Stmt;
import soot.jimple.internal.*;
import soot.jimple.toolkits.callgraph.CHATransformer;
import soot.jimple.toolkits.callgraph.CallGraph;
import soot.jimple.toolkits.callgraph.ReachableMethods;
import soot.toolkits.graph.BriefUnitGraph;
import soot.toolkits.scalar.*;

import java.io.*;
import java.lang.reflect.Method;
import java.util.*;
import java.util.logging.Level;

import org.json.*;

/**
 * Created by yzy on 8/17/16.
 */
public class ActivityAnalysis {
    public static List<String> getActivityListFromMappingFile(String filePath, String apkPath){
        String activityTextMappingStr = new String();
        try {
            File activityTextMappingFile = new File(filePath);
            BufferedReader in = new BufferedReader(new InputStreamReader(
                new FileInputStream(activityTextMappingFile), "UTF8"));
            String line;
            while ((line = in.readLine()) != null) {
                activityTextMappingStr += line;
            }
        }
        catch (Exception e){
            System.out.println("Reading " + filePath + " failed");
            return null;
        }
        try {
            JSONObject activityTextMapping = new JSONObject(activityTextMappingStr);
            String[] pathSeq = apkPath.split("/");
            String apkName = pathSeq[pathSeq.length - 1];
            String packageName = apkName.substring(0, apkName.length() - ".apk".length());

            Iterator<?> activityListItr = activityTextMapping.getJSONObject(packageName).keys();
            ArrayList<String> activityList = new ArrayList<>();

            while (activityListItr.hasNext())
                activityList.add((String) activityListItr.next());

            return activityList;
        }
        catch (Exception e){
            System.out.println(apkPath + " not found in mapping file");
            return null;
        }
    }

    public static void activityExpand(List<String> activityList){
        // First generate a list of activity classes
        List<SootClass> activityClassList = new ArrayList<>();
        for (String activityStr: activityList) {
            SootClass activityClass = Scene.v().getSootClass(activityStr);
            if (!activityClass.isPhantom())
                activityClassList.add(activityClass);
        }
        // Then generate a list of activity class expand sets
        Map<SootClass, Set<SootMethod>> activityMethodExpand = new HashMap<>();
        Map<SootClass, Set<SootClass>> activityClassExpand = new HashMap<>();

        for (SootClass activityClass : activityClassList) {
            if (Config.applicationClasses.contains(activityClass)) {
                System.out.println(activityClass.toString() + " found");
                // Generate call graph conservatively, using activity class as main class
                // add activity methods as entrypoints
                Scene.v().setEntryPoints(activityClass.getMethods());
                CHATransformer.v().transform();
                CallGraph cg = Scene.v().getCallGraph();
                // get method set
                ReachableMethods relMethods = Scene.v().getReachableMethods();
                Iterator<MethodOrMethodContext> relMethodsItr = relMethods.listener();

                activityMethodExpand.put(activityClass, new HashSet<SootMethod>());
                activityClassExpand.put(activityClass, new HashSet<SootClass>());

                while (relMethodsItr.hasNext()){
                    SootMethod method = relMethodsItr.next().method();
                    activityMethodExpand.get(activityClass).add(method);
                    activityClassExpand.get(activityClass).add(method.getDeclaringClass());
                }
                Util.LOGGER.info(activityClass.toString() + " finished");
            }
            else
                System.out.println(activityClass.toString() + " not found");
        }
    }

    public static void main(String[] args) {
        Util.LOGGER.setLevel(Level.ALL);
        if (!Config.parseArgs(args)) {
            return;
        }

        Config.init();

        List<String> activityList = getActivityListFromMappingFile("/mnt/data/activity_text_mapping.json",
                Config.codeDir);
        activityExpand(activityList);
    }
}
