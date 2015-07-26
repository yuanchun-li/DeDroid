package com.lynnlyc;

import com.lynnlyc.graph.Graph;
import com.lynnlyc.sootextension.FigureExtractor;

public class Main {
    //TODO 1: check overrides when restoring vertexes;
    //DONE 2: filter training data and predicting data
    //DONE 3: generate mapping
    //TODO 4: evaluate with open source apps:
    // for each open-sourced app, generate a debug version,
    // a release version and the mapping.txt corresponding to the release version

    public static void main(String[] args) {
	// write your code here
//        PrintStream os = System.out;

        if (!Config.parseArgs(args)) {
            Util.printUsage();
            return;
        }

        Config.init();

//        OutputUtils.dumpInfo(os);

        FigureExtractor figureExtractor = new FigureExtractor();
        Graph g = figureExtractor.run();
        g.dump(Config.getResultPs());
        if (Config.isTraining) {
            Trainer.train(g);
        }
        else {
            Predictor.predict(g);
        }
    }
}
