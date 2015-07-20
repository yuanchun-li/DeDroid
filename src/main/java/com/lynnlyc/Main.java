package com.lynnlyc;

import com.lynnlyc.graph.Graph;
import com.lynnlyc.graph.Vertex;

import java.io.File;
import java.io.PrintStream;

public class Main {

    public static void main(String[] args) {
	// write your code here
        PrintStream os = System.out;

        if (!Config.parseArgs(args)) {
            Util.printUsage();
            return;
        }

        Config.init();

        SootAnalysis sootAnalysis = new SootAnalysis();
//        sootAnalysis.dump(os);
        Graph g = sootAnalysis.run();
        g.dump(Config.getResultPs());

        if (Config.isTraining) {
            Trainer.train(Config.getResultFile());
        }
        else {
            File result = Predictor.predict(Config.getResultFile());
            g.restoreUnknownFromFile(result);
            sootAnalysis.output();
        }
    }
}
