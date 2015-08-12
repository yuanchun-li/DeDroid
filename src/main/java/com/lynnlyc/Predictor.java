package com.lynnlyc;

import com.lynnlyc.graph.Graph;
import com.lynnlyc.graph.Vertex;
import com.lynnlyc.sootextension.ObfuscationDetector;
import com.lynnlyc.sootextension.OutputUtils;
import com.thetransactioncompany.jsonrpc2.JSONRPC2Request;
import com.thetransactioncompany.jsonrpc2.JSONRPC2Response;
import com.thetransactioncompany.jsonrpc2.client.JSONRPC2Session;
import com.thetransactioncompany.jsonrpc2.client.JSONRPC2SessionException;
import org.json.JSONObject;
import org.json.JSONArray;


import java.io.*;
import java.net.URL;

/**
 * Created by LiYC on 2015/7/18.
 * Package: UnuglifyDEX
 */
public class Predictor {
    public static void mockPredict(Graph g) {
        Util.LOGGER.info("start predicting");
        JSONObject originObject = g.toJson();
        JSONArray originJson = (JSONArray) originObject.get("assign");
        JSONArray mockResultJson = originJson;

        generateMapping(g, mockResultJson);
//        evaluateResult(originJson, mockResultJson);
    }

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
                File resultFile = new File(Config.outputDir + "/result.json");
                FileWriter resultFileWriter = new FileWriter(resultFile);
                resultFileWriter.write(resultStr);
                resultFileWriter.close();
                JSONArray resultJson = new JSONArray(resultStr);
                generateMapping(g, resultJson);

                // Modified to insert a evaluation pass
                JSONObject originObject = g.toJson();
                JSONArray originJson = (JSONArray) originObject.get("assign");
                evaluateResult(originJson, resultJson);
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
    public static void evaluateResult(JSONArray origin, JSONArray result) {
        Util.LOGGER.info("start evaluation");

        try {
            File reportFile = new File(Config.outputDir + "/report.txt");
            FileWriter reportFileWriter = new FileWriter(reportFile);

            Integer infSameNum = 0, allSameNum = 0, infNum = 0;
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
                    allSameNum++;
                } else {
                    infNum++;
                    if (resultList[i].equals(originList[i])){
                        infSameNum++;
                        allSameNum++;
                    }
                    String reportStr = originList[i] + " -> " + resultList[i];
                    reportFileWriter.write(reportStr + "\n");
                }
            }
            reportFileWriter.close();

            double errorRate = (double)(infNum - infSameNum) / (double)infNum;

            Util.LOGGER.info("evaluation finished.");
            Util.LOGGER.info(infNum + " inf's in total with "
                             + (infNum - infSameNum) + " different labels. ");
            Util.LOGGER.info("diff rate " + errorRate);

        } catch (IOException e) {
            Util.LOGGER.warning("exception happened during evaluation");
            e.printStackTrace();
        }
    }

    /**
     * generate a proguard-like mapping.txt
     * @param g: The feature graph generated by FeatureExtractor,
     *              i.e. the ``assign'' element of predict.json
     * @param result: prediction result,
     *              i.e. the predicted vertex array
     */
    public static void generateMapping(Graph g, JSONArray result) {
        Util.LOGGER.info("generating mapping.txt");
        g.restoreUnknownFromJson(result);
        File reportFile = new File(Config.outputDir + "/mapping.txt");
        try {
            PrintStream ps = new PrintStream(reportFile);
            OutputUtils.dumpMapping(g, ps);
        } catch (FileNotFoundException e) {
            e.printStackTrace();
            Util.LOGGER.warning("generating mapping.txt failed");
        }
    }

    /**
     * transform the graph
     * convert `well-named` inf vertexes to giv
     * @param g: the original graph generate during feature extraction
     */
    public static void transform(Graph g) {
        for (Vertex v : g.vertexMap.values()) {
            if (!v.isKnown && !ObfuscationDetector.v().isObfuscated(v.content))
                v.isKnown = true;
        }
    }
}
