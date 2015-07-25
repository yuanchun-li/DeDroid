package com.lynnlyc;

import com.lynnlyc.graph.Graph;
import com.lynnlyc.sootextension.FigureExtractor;
import com.lynnlyc.sootextension.ObfuscationDetector;
import com.lynnlyc.sootextension.OutputUtils;

import java.io.PrintStream;

public class Main {
    //TODO 1: add method override edges
    //TODO 2: (done, but need debugging) filter training data and predicting data
    //TODO 3: (done, but need debugging) generate mapping
    //TODO 4: evaluate with open source apps:
    // for each open-sourced app, generate a debug version,
    // a release version and the mapping.txt corresponding to the release version

    public static void main(String[] args) {
	// write your code here
        PrintStream os = System.out;

        if (!Config.parseArgs(args)) {
            Util.printUsage();
            return;
        }

        Config.init();

//        OutputUtils.dumpInfo(os);

        FigureExtractor figureExtractor = new FigureExtractor();
        Graph g = figureExtractor.run();
        g.dump(Config.getResultPs());
        ObfuscationDetector.getObfuscationRate(os);
        if (Config.isTraining) {
            Trainer.train(g);
        }
        else {
            Predictor.mockPredict(g);
        }
    }
}
