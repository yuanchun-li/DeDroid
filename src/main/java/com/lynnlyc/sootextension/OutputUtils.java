package com.lynnlyc.sootextension;

import com.lynnlyc.Util;
import com.lynnlyc.graph.Graph;
import org.apache.commons.lang.StringUtils;
import soot.*;
import sun.nio.cs.ArrayDecoder;

import java.io.PrintStream;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;

/**
 * Created by LiYC on 2015/7/25.
 * Package: com.lynnlyc.sootextension
 */
public class OutputUtils {
    public static void dumpInfo(PrintStream ps) {
        ps.println("===Application Classes===");
        for (SootClass cls : Scene.v().getApplicationClasses()) {
            ps.println("---class info---");
            ps.println(cls);
            ps.println("getPackageName" + ":" + cls.getPackageName());
            ps.println("getJavaPackageName:" + ":" + cls.getJavaPackageName());
            ps.println("getName" + ":" + cls.getName());
            ps.println("getModifiers" + ":" + cls.getModifiers());
            ps.println("getSuperclass" + ":" + cls.getSuperclass());

            ps.println("--fields--");
            for (SootField f : cls.getFields()) {
                ps.println("-field info-");
                ps.println(f);
                ps.println("getDeclaration" + ":" + f.getDeclaration());
                ps.println("getDeclaringClass" + ":" + f.getDeclaringClass());
                ps.println("getName" + ":" + f.getName());
                ps.println("getModifiers" + ":" + f.getModifiers());
                ps.println("getNumber" + ":" + f.getNumber());
                ps.println("getSignature" + ":" + f.getSignature());
                ps.println("getType" + ":" + f.getType());
                ps.println("getSubSignature" + ":" + f.getSubSignature());
                ps.println("-end of field info-");

            }
            ps.println("--methods--");
            for (SootMethod m : cls.getMethods()) {
                ps.println("-method info-");
                ps.println(m);
                ps.println("getDeclaration" + ":" + m.getDeclaration());
                ps.println("getDeclaringClass" + ":" + m.getDeclaringClass());
                ps.println("getName" + ":" + m.getName());
                ps.println("getModifiers" + ":" + m.getModifiers());
                ps.println("getBytecodeParms" + ":" + m.getBytecodeParms());
                ps.println("getBytecodeSignature" + ":" + m.getBytecodeSignature());
                ps.println("getSignature" + ":" + m.getSignature());
                ps.println("getParameterTypes" + ":" + m.getParameterTypes());
                ps.println("getExceptions" + ":" + m.getExceptions());

                ps.println("method body:");
                Body b = m.retrieveActiveBody();
                ps.println(b);
                ps.println("-end of method info-");
            }
            ps.println("---end of class info---");
        }
        ps.println("===end of Application Classes===");
    }

    public static void lightDump(PrintStream ps) {
        for (SootClass cls : Scene.v().getApplicationClasses()) {
            ps.println("[class]");
            ps.println(cls);

            ps.println("\t[fields]");
            for (SootField f : cls.getFields()) {
                ps.println("\t" + f);
            }
            ps.println("\t[methods]");
            for (SootMethod m : cls.getMethods()) {
                ps.println("\t" + m);
            }
        }
    }

    public static void output() {
        PackManager.v().writeOutput();
    }

    public static void dumpMapping(Graph g, PrintStream ps) {
        ArrayList<ClassMappingSlot> classMappingSlots = new ArrayList<>();

        for (SootClass cls : Scene.v().getApplicationClasses()) {
            String originClassName = cls.getName();
            String predictedClassName = g.getPredictedClassName(cls);

            ClassMappingSlot classMappingSlot = new ClassMappingSlot(
                    originClassName, predictedClassName);

            for (SootField f : cls.getFields()) {
                String typeName = g.getPredictedTypeName(f.getType());
                String originFieldName = f.getName();
                String predictedFieldName = g.getPredictedFieldName(f);
                FieldMappingSlot fieldMappingSlot = new FieldMappingSlot(
                    originFieldName, predictedFieldName, typeName);
                if (!fieldMappingSlot.isSame())
                    classMappingSlot.fieldMappingSlots.add(fieldMappingSlot);
            }

            for (SootMethod m : cls.getMethods()) {
                String retTypeName = g.getPredictedTypeName(m.getReturnType());
                String originMethodName = m.getName();
                String predictedMethodName = g.getPredictedMethodName(m);
                String paramNames = "";
                List<Type> paramTypes = m.getParameterTypes();
                if (paramTypes != null) {
                    int arraySize = paramTypes.size();
                    for(int i = 0; i < arraySize; ++i) {
                        if(i > 0) {
                            paramNames += ',';
                        }
                        String paramName = g.getPredictedTypeName(paramTypes.get(i));
                        paramNames += paramName;
                    }
                }
                MethodMappingSlot methodMappingSlot = new MethodMappingSlot(
                        originMethodName, predictedMethodName, retTypeName, paramNames);

                if (!methodMappingSlot.isSame())
                    classMappingSlot.methodMappingSlots.add(methodMappingSlot);
            }

            if (!classMappingSlot.isSame())
                classMappingSlots.add(classMappingSlot);
        }

        Collections.sort(classMappingSlots, new Comparator<ClassMappingSlot>() {
            @Override
            public int compare(ClassMappingSlot o1, ClassMappingSlot o2) {
                return String.CASE_INSENSITIVE_ORDER.compare(
                        o1.predictedClassName, o2.predictedClassName);
            }
        });

        for (ClassMappingSlot classMappingSlot : classMappingSlots)
            ps.print(classMappingSlot);
    }

    static class ClassMappingSlot {
        public String originClassName;
        public String predictedClassName;
        public ArrayList<FieldMappingSlot> fieldMappingSlots;
        public ArrayList<MethodMappingSlot> methodMappingSlots;

        public ClassMappingSlot(String originClassName, String predictedClassName) {
            this.originClassName = originClassName;
            this.predictedClassName = predictedClassName;
            this.fieldMappingSlots = new ArrayList<>();
            this.methodMappingSlots = new ArrayList<>();
        }

        public boolean isSame() {
            return originClassName.equals(predictedClassName) &&
                    fieldMappingSlots.isEmpty() && methodMappingSlots.isEmpty();
        }

        public String toString() {
            String retStr = String.format("%s -> %s",
                    predictedClassName, originClassName);
            if (fieldMappingSlots.isEmpty() && methodMappingSlots.isEmpty())
                retStr += "\n";
            else retStr += ":\n";
            for (FieldMappingSlot fieldMappingSlot : fieldMappingSlots) {
                retStr += String.format("\t%s\n", fieldMappingSlot.toString());
            }
            for (MethodMappingSlot methodMappingSlot : methodMappingSlots) {
                retStr += String.format("\t%s\n", methodMappingSlot.toString());
            }
            return retStr;
        }
    }

    static class FieldMappingSlot {
        public String typeName;
        public String originFieldName;
        public String predictedFieldName;

        public FieldMappingSlot(String originFieldName, String predictedFieldName,
                                String typeName) {
            this.typeName = typeName;
            this.originFieldName = originFieldName;
            this.predictedFieldName = predictedFieldName;
        }

        public boolean isSame() {
            return originFieldName.equals(predictedFieldName);
        }

        public String toString() {
            return String.format("%s %s -> %s",
                    typeName, predictedFieldName, originFieldName);
        }
    }

    static class MethodMappingSlot {
        public String retTypeName;
        public String paramTypeNames;
        public String originMethodName;
        public String predictedMethodName;

        public MethodMappingSlot(String originMethodName, String predictedMethodName,
                                 String retTypeName, String paramTypeNames) {
            this.originMethodName = originMethodName;
            this.predictedMethodName = predictedMethodName;
            this.paramTypeNames = paramTypeNames;
            this.retTypeName = retTypeName;
        }

        public boolean isSame() {
            return originMethodName.equals(predictedMethodName);
        }

        public String toString() {
            return String.format("%s %s(%s) -> %s",
                    retTypeName, predictedMethodName,
                    paramTypeNames, originMethodName);
        }
    }
}
