package com.lynnlyc.sootextension;

import com.lynnlyc.Config;
import com.lynnlyc.Util;
import soot.Scene;
import soot.SootClass;
import soot.SootField;
import soot.SootMethod;

import java.io.File;
import java.io.FileNotFoundException;
import java.io.PrintStream;
import java.util.HashMap;
import java.util.HashSet;

/**
 * Created by LiYC on 2015/7/25.
 * Package: com.lynnlyc.sootextension
 */
public class ObfuscationDetector {
    private static ObfuscationDetector obfuscateDetector;
    private HashMap<SootClass, Float> classObfuscationRates;
    private float obfuscationRate;
    private ObfuscationDetector() {
        Util.LOGGER.info("measuring obfuscation rates");
        getObfuscationRates();
        File reportFile = new File(Config.outputDirPath + "/obfuscation_rates.txt");
        try {
            PrintStream ps = new PrintStream(reportFile);
            this.dump(ps);
        } catch (FileNotFoundException e) {
            e.printStackTrace();
            Util.LOGGER.warning("measuring obfuscation rates failed");
        }
    }
    public static ObfuscationDetector v() {
        if (obfuscateDetector == null)
            obfuscateDetector = new ObfuscationDetector();
        return obfuscateDetector;
    }

    public boolean isObfuscated(Object obj) {
        if (obj instanceof SootClass) return isClassObfuscated((SootClass) obj);
        if (obj instanceof SootField) return isFieldObfuscated((SootField) obj);
        if (obj instanceof SootMethod) return isMethodObfuscated((SootMethod) obj);
        if (obj instanceof PackageSeg) return isPackageSegObfuscated((PackageSeg) obj);
        if (obj instanceof String) return isNameObfuscated((String) obj);
        return false;
    }

    private boolean isPackageSegObfuscated(PackageSeg seg) {
        return !Config.isTraining && isNameObfuscated(seg.getSegName());
    }

    private boolean isClassObfuscated(SootClass cls) {
        if (Config.isTraining) {
            return cls.isApplicationClass() && classObfuscationRates.get(cls) > OBFUSCATE_THRESHOLD;
        }
        return cls.isApplicationClass() && isNameObfuscated(cls.getShortName());
    }

    private boolean isFieldObfuscated(SootField field) {
        if (Config.isTraining) {
            return isClassObfuscated(field.getDeclaringClass());
        }
        return isNameObfuscated(field.getName());
    }

    private boolean isMethodObfuscated(SootMethod method) {
        if (Config.isTraining) {
            return isClassObfuscated(method.getDeclaringClass());
        }
        return isNameObfuscated(method.getName());
    }

    private static final String excludedNames = "os;tv;up;go;it;do;io;id;of;op;on;or;";

    private boolean isNameObfuscated(String name) {
        if (name == null) return true;
        for(String seg : name.split("\\$")) {
            if (name.length() <= 2 && !excludedNames.contains(name))
                return true;
        }
        return false;
    }

    private static final float OBFUSCATE_THRESHOLD = (float) 0.1;
    private void getObfuscationRates() {
        classObfuscationRates = new HashMap<>();
        int totalClass = 0, obfuscatedClass = 0;
        for (SootClass cls : Scene.v().getApplicationClasses()) {
            int total = 0, obfuscated = 0;
            for (SootField f : cls.getFields()) {
                total++;
                if (isNameObfuscated(f.getName())) obfuscated++;
            }
            for (SootMethod m : cls.getMethods()) {
                total++;
                if (isNameObfuscated(m.getName())) obfuscated++;
            }
            float rate = Util.safeDivide(obfuscated, total);
            classObfuscationRates.put(cls, rate);

            totalClass++;
            if (rate > OBFUSCATE_THRESHOLD) obfuscatedClass++;
        }
        obfuscationRate = Util.safeDivide(obfuscatedClass, totalClass);
    }

    public void dump(PrintStream ps) {
        for (SootClass cls : classObfuscationRates.keySet()) {
            ps.println(String.format("%s -- %f", cls, classObfuscationRates.get(cls)));
        }
        ps.println(String.format("Overall: %f", obfuscationRate));
    }
}
