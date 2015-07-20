package com.lynnlyc;

import net.sf.json.JSONArray;
import net.sf.json.JSONObject;

import java.io.File;
import java.io.FileWriter;
import java.io.IOException;
import java.nio.charset.Charset;
import java.nio.file.Files;

/**
 * Created by LiYC on 2015/7/18.
 */
public class Predictor {
    public static File predict(File predictingData) {
        // TODO use the generated data to predict
        File resultFile = new File(Config.outputDirPath + "/output.json");
        try {
            byte[] encoded = Files.readAllBytes(predictingData.toPath());
            String resultStr = new String(encoded, Charset.defaultCharset());
            JSONObject resultJson = JSONObject.fromObject(resultStr);
            FileWriter fileWriter = new FileWriter(resultFile);
            fileWriter.write(resultJson.get("assign").toString());
            fileWriter.close();
        } catch (IOException e) {
            e.printStackTrace();
        }
        return resultFile;
    }
}
