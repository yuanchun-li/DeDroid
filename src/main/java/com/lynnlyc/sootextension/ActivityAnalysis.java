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
            in.close();
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
                HashSet<SootMethod> deltaRelMethods = new HashSet<>();

                while (relMethodsItr.hasNext()){
                    SootMethod method = relMethodsItr.next().method();
                    activityMethodExpand.get(activityClass).add(method);
                    SootClass declaringClass = method.getDeclaringClass();
                    activityClassExpand.get(activityClass).add(declaringClass);
                    if (declaringClass.hasSuperclass()) {
                        SootClass superClass = declaringClass.getSuperclass();
                        if (superClass.getName().equals("android.os.AsyncTask") ||
                            superClass.getName().equals("java.lang.Thread") ||
                            superClass.getName().equals("java.util.concurrent.ForkJoinWorkerThread") ||
                            superClass.getName().equals("android.os.HandlerThread") ||
                            superClass.implementsInterface("Runnable") ||
                            superClass.getName().equals("java.util.concurrent.FutureTask") ||
                            superClass.implementsInterface("RunnableFuture") ||
                            superClass.implementsInterface("ScheduledFuture") ||
                            superClass.implementsInterface("RunnableScheduledFuture") ||
                            superClass.getName().equals("android.os.Handler") ||
                            superClass.getName().equals("android.content.AsyncQueryHandler") ||
                            superClass.getName().equals("android.content.AsyncQueryHandler.WorkerHandler") ||
                            superClass.getName().equals("android.webkit.HttpAuthHandler") ||
                            superClass.getName().equals("android.webkit.HttpAuthHandler"))
                            deltaRelMethods.addAll(declaringClass.getMethods());
                    }
                }
                activityMethodExpand.get(activityClass).addAll(deltaRelMethods);
                Util.LOGGER.info(activityClass.toString() + " finished");
            }
            else
                System.out.println(activityClass.toString() + " not found");

            // extract text features
            try {
                File tempFile = new File(Config.outputDir + "/" + activityClass.getName() + "_text_feature.txt");
                BufferedWriter out = new BufferedWriter(new OutputStreamWriter(
                    new FileOutputStream(tempFile), "UTF8"));

                JSONObject outInfo = new JSONObject();

                for (SootClass appClass: activityClassExpand.get(activityClass)){
                    // class name
                    outInfo.put(appClass.getName(), new JSONObject());
                    // package name
                    JSONObject appClassInfo = (JSONObject)outInfo.get(appClass.getName());
                    appClassInfo.put("package_name", appClass.getPackageName());
                    // field names
                    appClassInfo.put("fields", new JSONArray());
                    JSONArray appClassFields = (JSONArray)appClassInfo.get("fields");
                    for (SootField classField: appClass.getFields())
                        appClassFields.put(classField.getDeclaration());
                    // reserve method list
                    appClassInfo.put("methods", new JSONArray());
                }
                // class names, method names and field names
                for (SootMethod appMethod: activityMethodExpand.get(activityClass)) {
                    JSONObject appClassInfo = (JSONObject)outInfo.get(appMethod.getDeclaringClass().getName());
                    JSONArray methodList = (JSONArray)appClassInfo.get("methods");
                    methodList.put(appMethod.getDeclaration());
                }

                out.write(outInfo.toString());
                out.close();
            }
            catch (Exception e){
                System.out.println("Output failed");
            }
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
