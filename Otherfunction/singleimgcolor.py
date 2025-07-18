# 主要目的：此程式碼定義了一個命令列工具，使用 TensorFlow 1.x 的靜態圖執行模式，從指定的模型目錄載入預訓練的生成對抗網絡（GAN）模型，處理輸入的 PNG 灰階圖像，生成修復後的圖像並保存為 PNG 檔案。它適用於牙科圖像修復流程，通過命令列參數指定模型目錄、輸入圖像和輸出圖像路徑，並包含基本的圖像後處理（例如去除低於閾值的像素）。

from __future__ import absolute_import
from __future__ import division
from __future__ import print_function

try:
    import tensorflow as tf
except ImportError as e:
    print(f"Error importing tensorflow: {e}")
    print("Install TensorFlow 2.2.0: python -m pip install tensorflow==2.2.0")
    exit(1)

import numpy as np
import argparse
import json
import base64
import cv2

tf = tf.compat.v1  # 使用 TensorFlow 1.x 兼容模式。
tf.disable_v2_behavior()  # 禁用 TensorFlow 2.x 行為，使用靜態圖執行模式。

# 創建命令列參數解析器
parser = argparse.ArgumentParser()  # 初始化 ArgumentParser 物件。
parser.add_argument("--model_dir", help="Directory containing the exported model")  # 添加模型目錄參數。
parser.add_argument("--input_file", help="Input PNG image file")  # 添加輸入 PNG 圖像檔案參數。
parser.add_argument("--output_file", help="Output PNG image file")  # 添加輸出 PNG 圖像檔案參數。
a = parser.parse_args()  # 解析命令列參數，儲存到變數 a。

def apply_gan_model(model_dir, input_file, output_file):  # 定義應用 GAN 模型的函數。
    try:
        with open(input_file, "rb") as f:  # 以二進制讀取模式打開輸入圖像檔案。
            input_data = f.read()  # 讀取圖像的二進制數據。

        # 將輸入圖像數據編碼為 base64 並轉為 JSON 格式
        input_instance = dict(input=base64.urlsafe_b64encode(input_data).decode("ascii"), key="0")  # 將圖像數據編碼為 base64 字串。
        input_instance = json.loads(json.dumps(input_instance))  # 將字典轉為 JSON 字串後再解析回字典（確保格式一致）。

        with tf.Session() as sess:  # 創建 TensorFlow 1.x 會話。
            checkpoint_path = tf.train.latest_checkpoint(model_dir)  # 獲取模型目錄中最新的檢查點檔案。
            if not checkpoint_path:  # 檢查是否存在檢查點。
                raise ValueError(f"No checkpoint found in {model_dir}")  # 若無檢查點，拋出錯誤。

            # 載入模型圖結構和權重
            saver = tf.train.import_meta_graph(checkpoint_path + ".meta")  # 導入模型的圖結構（.meta 檔案）。
            saver.restore(sess, checkpoint_path)  # 恢復模型的權重。

            # 獲取模型的輸入和輸出張量
            input_vars = json.loads(tf.get_collection("inputs")[0].decode())  # 從圖中獲取輸入張量名稱（JSON 格式）。
            output_vars = json.loads(tf.get_collection("outputs")[0].decode())  # 從圖中獲取輸出張量名稱（JSON 格式）。
            input_tensor = tf.get_default_graph().get_tensor_by_name(input_vars["input"])  # 獲取輸入張量。
            output_tensor = tf.get_default_graph().get_tensor_by_name(output_vars["output"])  # 獲取輸出張量。

            # 準備輸入數據
            input_value = np.array(input_instance["input"])  # 將輸入 JSON 中的 base64 字串轉為 NumPy 陣列。
            # 執行模型推斷
            output_value = sess.run(output_tensor, feed_dict={input_tensor: np.expand_dims(input_value, axis=0)})[0]  # 將輸入數據擴展維度並運行模型。

        # 處理模型輸出
        output_instance = dict(output=output_value.decode("ascii"), key="0")  # 將輸出數據轉為字典格式。
        b64data = output_instance["output"]  # 獲取輸出的 base64 字串。
        b64data += "=" * (-len(b64data) % 4)  # 補齊 base64 字串的填充字符（=）。
        output_data = base64.urlsafe_b64decode(b64data.encode("ascii"))  # 解碼 base64 字串為二進制數據。
        nparr = np.frombuffer(output_data, np.uint8)  # 將二進制數據轉為 NumPy 陣列。
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)  # 將陣列解碼為灰階圖像。

        if img is None:  # 檢查圖像是否成功解碼。
            raise ValueError("Failed to decode image data. Check model output format.")  # 若解碼失敗，拋出錯誤。

        # 圖像後處理
        img[img < 20] = 0  # 將低於閾值 20 的像素設為 0（去除噪點）。
        _, buffer = cv2.imencode(".png", img)  # 將圖像編碼為 PNG 格式的二進制數據。
        with open(output_file, "wb") as f:  # 以二進制寫入模式打開輸出檔案。
            f.write(buffer.tobytes())  # 將編碼後的圖像數據寫入檔案。

    except Exception as e:  # 捕獲所有異常。
        print(f"Error in apply_gan_model: {e}")  # 打印錯誤訊息。
        raise  # 重新拋出異常以便調試。


# model_path = "D:/Weekly_Report/Thesis_Weekly_Report/paper/paper_Implementation/pyqt5/aimodel/DAISdepthr=2andcollision/"                # 模型資料夾
# input_img = "D:/Weekly_Report/Thesis_Weekly_Report/paper/paper_Implementation/pyqt5/toKMU/AIoutput/onlay-14_LowerJawGOICPdown/flipped_256x768.png"          # 輸入圖片
# output_img = "D:/Weekly_Report/Thesis_Weekly_Report/paper/paper_Implementation/pyqt5/toKMU/AIoutput/onlay-14_LowerJawGOICPdown/aitest.png"        # 輸出圖片

# apply_gan_model(model_path, input_img, output_img)
# print("影像處理完成，輸出檔案已儲存於：", output_img)