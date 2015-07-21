package com.lynnlyc;

/**
 * Created by LiYC on 2015/7/18.
 * Package: UnuglifyDEX
 */
import soot.options.Options;

import javax.swing.text.html.Option;
import java.io.*;
import java.util.ArrayList;
import java.util.HashSet;
import java.util.List;
import java.util.logging.FileHandler;
import java.util.logging.Level;
import java.util.logging.SimpleFormatter;

public class Config {
    // nice2predict server url for predicting
    public static final String serverUrl = "http://localhost:5745";

    // Mode (training or predicting)
    public static boolean isTraining = false;

    // Directory path to find android.jar
    public static String androidPlatformDir = "";
    // File path of android.jar which is forced to use by soot
    public static String forceAndroidJarPath = "";
    // Libraries' directory, to be added to soot classpath
    public static String librariesDir = "";

    // If it is training mode
    // Directory path of training data
    // The trainer will scan the directory and its sub directory,
    // and find .jars and .javas to train

    // If it is predicting mode
    // The predictor needs an apk as input
    // File path of apk
    // public static String appFilePath = "";
    // TODO Currently we only predict .java files, add .dex predicting
    // TODO currently we only train .java files, add .jar training
    public static String codeDir = "";

    // Directory for result output
    // It should output a json format of training/predicting data
    public static String outputDirPath = "output";

    public static boolean isInitialized = false;

    // printer of output
    private static File logFile;
    private static PrintStream logPs;
    private static File resultFile;
    private static PrintStream resultPs;

    public static boolean parseArgs(String[] args) {
        int i;
        if (args.length % 2 == 1)
            return false;

        String mode = Config.isTraining ? "train" : "predict";
        for (i = 0; i < args.length; i += 2) {
            String key = args[i];
            String value = args[i+1];
            switch (key) {
                case "-i": Config.codeDir = value; break;
                case "-o": Config.outputDirPath = value; break;
                case "-l": Config.librariesDir = value; break;
                case "-m": mode = value;
                case "-android-jars": Config.androidPlatformDir = value; break;
                case "-force-android-jar": Config.forceAndroidJarPath = value; break;
                default: return false;
            }
        }

//        if ("".equals(Config.androidPlatformDir) && "".equals(Config.forceAndroidJarPath)) {
//            return false;
//        }

        if ("train".equals(mode)) {
            Config.isTraining = true;
        }
        else if ("predict".equals(mode)) {
            Config.isTraining = false;
        }
        else {
            System.out.println("Unknown mode, should be train or predict.");
            return false;
        }

        if ("".equals(Config.codeDir)) {
            System.out.println("Input file cannot be empty.");
            return false;
        }

        File codeDirFile = new File(Config.codeDir);
        if (!codeDirFile.exists()) {
            System.out.println("Input file does not exist.");
            return false;
        }

        File workingDir = new File(String.format("%s/UnuglifyDex_%S_%s/", Config.outputDirPath,
                mode, Util.getTimeString()));

        Config.outputDirPath = workingDir.getPath();
        if (!workingDir.exists() && !workingDir.mkdirs()) {
            System.out.println("Error generating output directory.");
            return false;
        }
        logFile = new File(String.format("%s/%s.log", Config.outputDirPath, mode));
        resultFile = new File(String.format("%s/%s.json", Config.outputDirPath, mode));

        if (!"".equals(Config.librariesDir)){
            File lib = new File(Config.librariesDir);
            if (!lib.exists()) {
                System.out.println("Library does not exist.");
                return false;
            }
            if (lib.isFile() && !lib.getName().endsWith(".jar")) {
                System.out.println("Library format error, should be directory or jar.");
                return false;
            }
        }

        try {
            logPs = new PrintStream(new FileOutputStream(logFile));
            FileHandler fh = new FileHandler(logFile.getAbsolutePath());
            fh.setFormatter(new SimpleFormatter());
            Util.LOGGER.addHandler(fh);
            resultPs = new PrintStream(new FileOutputStream(resultFile));
        } catch (IOException e) {
            e.printStackTrace();
            return false;
        }
        Util.LOGGER.info(String.format("[mode]%s, [input]%s, [output]%s",
                mode, Config.codeDir, Config.outputDirPath));
        return true;
    }

    public static void init() {
        Util.LOGGER.log(Level.INFO, "initializing...");
        Options.v().set_prepend_classpath(true);
        Options.v().set_allow_phantom_refs(true);
//        Options.v().set_whole_program(true);
//        Options.v().set_src_prec(Options.src_prec_apk);
        Options.v().set_output_dir(Config.outputDirPath);

        List<String> process_dirs = new ArrayList<>();
        process_dirs.add(Config.codeDir);
        Options.v().set_process_dir(process_dirs);

        if (Config.codeDir.endsWith(".apk")) {
            Options.v().set_src_prec(Options.src_prec_apk);
            Options.v().set_output_format(Options.output_format_force_dex);
        }
        else if (Config.codeDir.endsWith(".jar")) {
            Options.v().set_src_prec(Options.src_prec_class);
            Options.v().set_output_jar(true);
        }
        else {
            Options.v().set_src_prec(Options.src_prec_java);
            Options.v().set_output_format(Options.output_format_jimple);
        }

        Options.v().set_output_format(Options.output_format_jimple);

        String classpath = "";
        if (Config.librariesDir != null && !"".equals(Config.librariesDir)) {
            File lib = new File(Config.librariesDir);
            if (lib.isFile() && lib.getName().endsWith(".jar"))
                classpath = lib.getAbsolutePath();
            else if (lib.isDirectory()) {
                FileFilter fileFilter = new FileFilter() {
                    @Override
                    public boolean accept(File pathname) {
                        return pathname.getName().endsWith(".jar");
                    }
                };
                for (File file : lib.listFiles(fileFilter)) {
                    classpath += file.getAbsolutePath() + ";";
                }
            }
            Options.v().set_soot_classpath(classpath);
        }
//        Options.v().set_ast_metrics(true);
//        Options.v().set_polyglot(true);

        if (!("".equals(Config.androidPlatformDir)))
            Options.v().set_android_jars(Config.androidPlatformDir);
        if (!("".equals(Config.forceAndroidJarPath)))
            Options.v().set_force_android_jar(Config.forceAndroidJarPath);

        Config.isInitialized = true;
        Util.LOGGER.info("initialization finished...");
    }

    public static PrintStream getResultPs() {
        if (resultPs == null) {
            Util.LOGGER.warning("result printer is null, use stdout instead.");
            return System.out;
        }
        return resultPs;
    }

    public static PrintStream getLogPs() {
        if (logPs == null) {
            Util.LOGGER.warning("log printer is null, use stdout instead.");
            return System.out;
        }
        return logPs;
    }

    public static File getResultFile() {
        return resultFile;
    }
}