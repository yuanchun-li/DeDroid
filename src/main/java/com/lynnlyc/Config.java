package com.lynnlyc;

/**
 * Created by LiYC on 2015/7/18.
 * Package: UnuglifyDEX
 */
import org.apache.commons.cli.*;
import soot.Scene;
import soot.SootClass;
import soot.options.Options;

import java.io.*;
import java.net.MalformedURLException;
import java.net.URL;
import java.util.ArrayList;
import java.util.Collections;
import java.util.Comparator;
import java.util.List;
import java.util.logging.FileHandler;
import java.util.logging.Level;
import java.util.logging.SimpleFormatter;

public class Config {
    // nice2predict server url for predicting
    public static String serverUrl = "http://localhost:5745";
    public static final String projectName = "UnuglifyDEX";

    // Mode (training or predicting)
    public static boolean isTraining = false;
    private static String mode = null;

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
    public static String codeDir = "";

    // Directory for result output
    // It should output a json format of training/predicting data
    public static String outputDir = "output";

    public static ArrayList<SootClass> applicationClasses;
    public static boolean isInitialized = false;

    private static PrintStream resultPs;

    public static boolean enable_oo = true;
    public static boolean enable_type = true;
    public static boolean enable_modifier = true;
    public static boolean enable_def_use = true;
    public static boolean enable_call_ret = true;
    public static boolean enable_usage_order = false;
    public static boolean enable_usage_after = false;

    public static boolean parseArgs(String[] args) {
        org.apache.commons.cli.Options options = new org.apache.commons.cli.Options();
        Option quiet = new Option("quiet", "be extra quiet");
        Option debug = new Option("debug", "print debug information");
        Option train = new Option("train", "run in training mode, default is predicting mode");
        Option output = Option.builder("o").argName("directory").required()
                .longOpt("output").hasArg().desc("path to output dir").build();
        Option input = Option.builder("i").argName("directory").required()
                .longOpt("input").hasArg().desc("path to target app").build();
        Option library = Option.builder("l").argName("directory")
                .longOpt("library").hasArg().desc("path to library dir").build();
        Option sdk = Option.builder("sdk").argName("android.jar").required()
                .longOpt("android-sdk").hasArg().desc("path to android.jar").build();
        Option server = Option.builder("server").argName("url").hasArg()
                .desc("Nice2Predict server address, default http://localhost:5745").build();

        Option OOOpt = Option.builder("enable_oo").argName("true or false").hasArg()
                .desc("enable language-specific relations, default is true").build();
        Option TYOpt = Option.builder("enable_type").argName("true or false").hasArg()
                .desc("enable type relations, default is true").build();
        Option MDOpt = Option.builder("enable_modifier").argName("true or false").hasArg()
                .desc("enable modifier relations, default is true").build();
        Option DUOpt = Option.builder("enable_def_use").argName("true or false").hasArg()
                .desc("enable def-use relations, default is true").build();
        Option CROpt = Option.builder("enable_call_ret").argName("true or false").hasArg()
                .desc("enable call-ret analysis, default is true").build();
        Option UOOpt = Option.builder("enable_usage_order").argName("true or false").hasArg()
                .desc("enable usage-order analysis, default is false").build();
        Option UAOpt = Option.builder("enable_usage_after").argName("true or false").hasArg()
                .desc("enable usage-after analysis, default is false").build();

        options.addOption(quiet);
        options.addOption(debug);
        options.addOption(train);
        options.addOption(output);
        options.addOption(input);
        options.addOption(library);
        options.addOption(sdk);
        options.addOption(server);

        options.addOption(OOOpt);
        options.addOption(TYOpt);
        options.addOption(MDOpt);
        options.addOption(DUOpt);
        options.addOption(CROpt);
        options.addOption(UOOpt);

        CommandLineParser parser = new DefaultParser();

        try {
            CommandLine cmd = parser.parse(options, args);
            if (cmd.hasOption("debug")) Util.LOGGER.setLevel(Level.ALL);
            if (cmd.hasOption("quiet")) Util.LOGGER.setLevel(Level.WARNING);
            if (cmd.hasOption("train")) Config.isTraining = true;
            mode = Config.isTraining ? "train" : "predict";
            if (cmd.hasOption("i")) {
                Config.codeDir = cmd.getOptionValue("i");
                File codeDirFile = new File(Config.codeDir);
                if (!codeDirFile.exists()) {
                    throw new ParseException("Input file does not exist.");
                }
            }
            if (cmd.hasOption('o')) {
                Config.outputDir = cmd.getOptionValue('o');
                File workingDir = new File(String.format("%s/UnuglifyDex_%S_%s/",
                        Config.outputDir, mode, Util.getTimeString()));

                Config.outputDir = workingDir.getPath();
                if (!workingDir.exists() && !workingDir.mkdirs()) {
                    throw new ParseException("Error generating output directory.");
                }
            }
            if (cmd.hasOption('l')) {
                Config.librariesDir = cmd.getOptionValue('l');
                File lib = new File(Config.librariesDir);
                if (!lib.exists()) {
                    throw new ParseException("Library does not exist.");
                }
                if (lib.isFile() && !lib.getName().endsWith(".jar")) {
                    throw new ParseException("Library format error, should be directory or jar.");
                }
            }
            if (cmd.hasOption("sdk")) {
                Config.forceAndroidJarPath = cmd.getOptionValue("sdk");
                File sdkFile = new File(Config.forceAndroidJarPath);
                if (!sdkFile.exists()) {
                    throw new ParseException("Android jar does not exist.");
                }
            }
            if (cmd.hasOption("server")) {
                Config.serverUrl = cmd.getOptionValue("server");
                try {
                    new URL(Config.serverUrl);
                } catch (MalformedURLException e) {
                    throw new ParseException("Server url error. " + e.getMessage());
                }
            }
            if (cmd.hasOption("enable_oo")) {
                String opt = cmd.getOptionValue("enable_oo").toLowerCase();
                if ("true".equals(opt))
                    Config.enable_oo = true;
                else if ("false".equals(opt))
                    Config.enable_oo = false;
                else
                    throw new ParseException("enable_oo option receives true or false, not " + opt);
            }
            if (cmd.hasOption("enable_type")) {
                String opt = cmd.getOptionValue("enable_type").toLowerCase();
                if ("true".equals(opt))
                    Config.enable_type = true;
                else if ("false".equals(opt))
                    Config.enable_type = false;
                else
                    throw new ParseException("enable_type option receives true or false, not " + opt);
            }
            if (cmd.hasOption("enable_modifier")) {
                String opt = cmd.getOptionValue("enable_modifier").toLowerCase();
                if ("true".equals(opt))
                    Config.enable_modifier = true;
                else if ("false".equals(opt))
                    Config.enable_modifier = false;
                else
                    throw new ParseException("enable_modifier option receives true or false, not " + opt);
            }
            if (cmd.hasOption("enable_call_ret")) {
                String opt = cmd.getOptionValue("enable_call_ret").toLowerCase();
                if ("true".equals(opt))
                    Config.enable_call_ret = true;
                else if ("false".equals(opt))
                    Config.enable_call_ret = false;
                else
                    throw new ParseException("enable_call_ret option receives true or false, not " + opt);
            }
            if (cmd.hasOption("enable_def_use")) {
                String opt = cmd.getOptionValue("enable_def_use").toLowerCase();
                if ("true".equals(opt))
                    Config.enable_def_use = true;
                else if ("false".equals(opt))
                    Config.enable_def_use = false;
                else
                    throw new ParseException("enable_def_use option receives true or false, not " + opt);
            }
            if (cmd.hasOption("enable_usage_order")) {
                String opt = cmd.getOptionValue("enable_usage_order").toLowerCase();
                if ("true".equals(opt))
                    Config.enable_usage_order = true;
                else if ("false".equals(opt))
                    Config.enable_usage_order = false;
                else
                    throw new ParseException("enable_usage_order option receives true or false, not " + opt);
            }
            if (cmd.hasOption("enable_usage_after")) {
                String opt = cmd.getOptionValue("enable_usage_after").toLowerCase();
                if ("true".equals(opt))
                    Config.enable_usage_after = true;
                else if ("false".equals(opt))
                    Config.enable_usage_after = false;
                else
                    throw new ParseException("enable_usage_after option receives true or false, not " + opt);
            }

        } catch (ParseException e) {
            System.out.println(e.getMessage());
            HelpFormatter formatter = new HelpFormatter();
            formatter.setOptionComparator(new Comparator<Option>() {
                @Override
                public int compare(Option o1, Option o2) {
                    return o1.getOpt().length() - o2.getOpt().length();
                }
            });
            formatter.printHelp(Config.projectName, options, true);
            return false;
        }
        return true;
    }

    public static void init() {
        Util.LOGGER.log(Level.INFO, "initializing...");

        File logFile = new File(String.format("%s/%s.log", Config.outputDir, mode));
        File resultFile = new File(String.format("%s/%s.json", Config.outputDir, mode));

        try {
            FileHandler fh = new FileHandler(logFile.getAbsolutePath());
            fh.setFormatter(new SimpleFormatter());
            Util.LOGGER.addHandler(fh);
            resultPs = new PrintStream(new FileOutputStream(resultFile));
        } catch (IOException e) {
            e.printStackTrace();
        }

        Options.v().set_debug(false);
        Options.v().set_prepend_classpath(true);
        Options.v().set_allow_phantom_refs(true);
//        Options.v().set_whole_program(true);
//        Options.v().set_src_prec(Options.src_prec_apk);
        Options.v().set_output_dir(Config.outputDir);

        List<String> process_dirs = new ArrayList<>();
        process_dirs.add(Config.codeDir);
        Options.v().set_process_dir(process_dirs);

        if (Config.codeDir.endsWith(".apk")) {
            Options.v().set_src_prec(Options.src_prec_apk);
            Options.v().set_output_format(Options.output_format_dex);
        }
        else if (Config.codeDir.endsWith(".jar")) {
            Options.v().set_src_prec(Options.src_prec_class);
            Options.v().set_output_jar(true);
        }
        else {
            Options.v().set_src_prec(Options.src_prec_java);
            Options.v().set_output_format(Options.output_format_jimple);
        }

        String classpath = "";
        if (Config.librariesDir != null && Config.librariesDir.length() != 0) {
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

        Options.v().set_force_android_jar(Config.forceAndroidJarPath);


        Scene.v().loadNecessaryClasses();
        Config.isInitialized = true;

        applicationClasses = new ArrayList<>();
        for (SootClass cls : Scene.v().getApplicationClasses()) {
            applicationClasses.add(cls);
        }
        Collections.sort(applicationClasses, new Comparator<SootClass>() {
            @Override
            public int compare(SootClass o1, SootClass o2) {
                return String.CASE_INSENSITIVE_ORDER.compare(
                        o1.getName(), o2.getName());
            }
        });

        Util.LOGGER.info("initialization finished...");
        Util.LOGGER.info(String.format("[mode]%s, [input]%s, [output]%s",
                mode, Config.codeDir, Config.outputDir));
    }

    public static PrintStream getResultPs() {
        if (resultPs == null) {
            Util.LOGGER.warning("result printer is null, use stdout instead.");
            return System.out;
        }
        return resultPs;
    }
}