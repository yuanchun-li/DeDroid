package com.lynnlyc;

import java.io.*;
import java.text.SimpleDateFormat;
import java.util.*;
import java.util.logging.Logger;
import soot.Scene;
import soot.SootClass;
import soot.SootMethod;

public class Util {
    public static final Logger LOGGER = Logger.getLogger("UnuglifyDEX");

    public static String getTimeString() {
        long timeMillis = System.currentTimeMillis();
        SimpleDateFormat sdf = new SimpleDateFormat("yyyyMMdd-hhmmss");
        Date date = new Date(timeMillis);
        return sdf.format(date);
    }

    public static void printUsage() {
        String usage = "Usage: java Main [options]\n" +
                "\t-i\tinput directory\n" +
                "\t-o\toutput directory\n" +
                "\t-m\tmode, train or predict\n" +
                "\t-l\tlibraies directory\n" +
                "\t-android-jars\tpath to sdk platforms\n" +
                "\t-force-android-jar\tpath to android.jar\n" +
                "\texample: java Main -i examples/train -o output -android-jars path/to/sdk/platforms\n";
        System.out.println(usage);
    }

	public static void logException(Exception e) {
		StringWriter sw = new StringWriter();
		e.printStackTrace(new PrintWriter(sw));
		Util.LOGGER.warning(sw.toString());
	}
}
