package com.lynnlyc;

import com.lynnlyc.graph.Graph;
import com.thetransactioncompany.jsonrpc2.JSONRPC2Request;
import com.thetransactioncompany.jsonrpc2.JSONRPC2Response;
import com.thetransactioncompany.jsonrpc2.client.JSONRPC2Session;
import com.thetransactioncompany.jsonrpc2.client.JSONRPC2SessionException;
//import net.sf.json.JSONArray;
import org.json.JSONObject;
import org.json.JSONArray;
import org.json.JSONTokener;


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

                // Modified to insert a evaluation pass
                JSONTokener tokener = new JSONTokener(resultStr);
                JSONArray result = (JSONArray) tokener.nextValue();

                JSONObject originObject = g.toJson();
                JSONArray origin = (JSONArray) originObject.get("assign");

                evaluate_result(origin, result);
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

        try {
            File reportFile = new File(Config.outputDirPath + "/report.txt");
            FileWriter reportFileWriter = new FileWriter(reportFile);

            // TODO export evaluation result to report.txt
            // Assign to @YZY

            Integer infCorrectNum = 0, allCorrectNum = 0, infNum = 0;
            Integer allNum = origin.length();

            // Prepare the array for evaluation

            String[] resultList = new String[allNum];
            String[] originList = new String[allNum];

            // Fill the arrays

            for (int i = 0; i < allNum; i++){
                JSONObject resultJsonObject = result.getJSONObject(i);
                JSONObject originJsonObject = origin.getJSONObject(i);

                Integer resultId = (Integer) resultJsonObject.get("v");
                Integer originId = (Integer) originJsonObject.get("v");
                
                if (resultJsonObject.has("giv")){
                    // given nodes filled with "null" identifier
                    resultList[resultId] = null;
                }
                else{
                    String resultName = (String) resultJsonObject.get("inf");
                    resultList[resultId] = resultName;
                }

                if (originJsonObject.has("giv")){
                    originList[originId] = null;
                } else {
                    String originName = (String) originJsonObject.get("inf");
                    originList[originId] = originName;
                }
            }

            // Evaluate and output
            for (int i = 0; i < allNum; i++){
                if (resultList[i] == null){
                    allCorrectNum++;
                } else {
                    infNum++;
                    if (resultList[i].equals(originList[i])){
                        infCorrectNum++;
                        allCorrectNum++;
                    }
                    String reportStr = originList[i] + " -> " + resultList[i];
                    reportFileWriter.write(reportStr + "\n");
                }
            }
            reportFileWriter.close();

            double errorRate = (double)(infNum - infCorrectNum) / (double)infNum;

            Util.LOGGER.info("evaluation finished.");
            Util.LOGGER.info(infNum + " inf's in total with "
                             + (infNum - infCorrectNum) + " wrong labels. ");
            Util.LOGGER.info("error rate " + errorRate);

        } catch (IOException e) {
            Util.LOGGER.warning("exception happened during evaluation");
            e.printStackTrace();
        }
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
