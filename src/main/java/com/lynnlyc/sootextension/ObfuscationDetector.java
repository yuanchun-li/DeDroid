package com.lynnlyc.sootextension;

import org.apache.commons.lang.StringUtils;
import soot.Scene;
import soot.SootClass;
import soot.SootField;
import soot.SootMethod;

import java.io.PrintStream;

/**
 * Created by LiYC on 2015/7/25.
 * Package: com.lynnlyc.sootextension
 */
public class ObfuscationDetector {
    public static boolean isObfuscated(Object obj) {
        if (obj instanceof SootClass) return isClassObfuscated((SootClass) obj);
        if (obj instanceof SootField) return isFieldObfuscated((SootField) obj);
        if (obj instanceof SootMethod) return isMethodObfuscated((SootMethod) obj);
        if (obj instanceof String) return isNameObfuscated((String) obj);
        return false;
    }

    public static boolean isClassObfuscated(SootClass cls) {
        return isPackageObfuscated(cls.getPackageName()) ||
                isNameObfuscated(cls.getShortName());
    }

    public static boolean isFieldObfuscated(SootField field) {
        return isNameObfuscated(field.getName());
    }

    public static boolean isMethodObfuscated(SootMethod method) {
        return isNameObfuscated(method.getName());
    }

    public static boolean isPackageObfuscated(String packageName) {
        String lastSeg = StringUtils.substringAfterLast(packageName, ".");
        return isNameObfuscated(lastSeg);
    }

    public static final String excludedNames = "os;tv;up;go;it;do;";

    public static boolean isNameObfuscated(String name) {
        return name == null || name.length() <= 2 &&
                !excludedNames.contains(name.toLowerCase());
    }

    public static float getObfuscationRate(PrintStream ps) {
        int totalClass = 0, obfuscatedClass = 0;
        for (SootClass cls : Scene.v().getApplicationClasses()) {
            int total = 0, obfuscated = 0;
            for (SootField f : cls.getFields()) {
                total++;
                if (isFieldObfuscated(f)) obfuscated++;
            }
            for (SootMethod m : cls.getMethods()) {
                total++;
                if (isMethodObfuscated(m)) obfuscated++;
            }
            float rate = obfuscated / total;
            totalClass++;
            if (isClassObfuscated(cls)) obfuscatedClass++;
            ps.println(String.format("%s -- %f", cls, rate));
        }
        float rate = obfuscatedClass / totalClass;
        ps.println(String.format("classes total:%d, obfuscated:%d, rate:%f",
                totalClass, obfuscatedClass, rate));
        return rate;
    }
}
