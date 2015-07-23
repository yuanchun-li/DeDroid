package com.lynnlyc;

import com.lynnlyc.graph.Graph;
import com.thetransactioncompany.jsonrpc2.JSONRPC2Request;
import com.thetransactioncompany.jsonrpc2.JSONRPC2Response;
import com.thetransactioncompany.jsonrpc2.client.JSONRPC2Session;
import com.thetransactioncompany.jsonrpc2.client.JSONRPC2SessionException;
import org.json.JSONArray;
import org.json.JSONObject;
import soot.Scene;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.net.URL;
import java.nio.charset.Charset;
import java.nio.file.Files;

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
}
