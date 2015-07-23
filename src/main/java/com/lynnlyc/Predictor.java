package com.lynnlyc;

import com.lynnlyc.graph.Graph;
import com.thetransactioncompany.jsonrpc2.JSONRPC2Request;
import com.thetransactioncompany.jsonrpc2.JSONRPC2Response;
import com.thetransactioncompany.jsonrpc2.client.JSONRPC2Session;
import com.thetransactioncompany.jsonrpc2.client.JSONRPC2SessionException;
import net.sf.json.JSONArray;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.net.URL;

/**
 * Created by LiYC on 2015/7/18.
 * Package: UnuglifyDEX
 */
public class Predictor {
    public static void predict(Graph g) {
        Util.LOGGER.info("start predicting");

        try {
            URL serverURL = new URL(Config.serverUrl);
            JSONRPC2Session predictSession = new JSONRPC2Session(serverURL);
            String predictMethod = "infer";
            int requestID = 0;

            JSONRPC2Request predictRequest = new JSONRPC2Request(
                    predictMethod, g.toMap(), requestID);

            JSONRPC2Response response = predictSession.send(predictRequest);

            // Print response result / error
            if (response.indicatesSuccess()) {
                Util.LOGGER.info("finished predicting");
                String resultStr = response.getResult().toString();
                File resultFile = new File(Config.outputDirPath + "/result.json");
                FileWriter resultFileWriter = new FileWriter(resultFile);
                resultFileWriter.write(resultStr);
                resultFileWriter.close();
                g.restoreUnknownFromString(resultStr);
            }
            else
                Util.LOGGER.warning(response.getError().getMessage());
        } catch (IOException | JSONRPC2SessionException e) {
            Util.LOGGER.warning("exception happened during predicting");
            e.printStackTrace();
        }
    }

    /**
     * evaluate the result of prediction
     * @param origin: original vertex array,
     *              i.e. the ``assign'' element of predict.json
     * @param result: prediction result,
     *              i.e. the predicted vertex array
     */
    public static void evaluate_result(JSONArray origin, JSONArray result) {
        Util.LOGGER.info("start evaluation");
        File reportFile = new File(Config.outputDirPath + "/report.txt");
        // TODO export evaluation result to report.txt
        // Assign to @YZY
    }

    /**
     * generate a proguard-like mapping.txt
     * @param origin: original vertex array,
     *              i.e. the ``assign'' element of predict.json
     * @param result: prediction result,
     *              i.e. the predicted vertex array
     */
    public static void generate_mapping(JSONArray origin, JSONArray result) {
        Util.LOGGER.info("generating mapping.txt");
        File reportFile = new File(Config.outputDirPath + "/mapping.txt");
        // TODO generate a mapping.txt file
        // See proguard for more details
        // Assign to @YZY or @ZYH
    }
}
