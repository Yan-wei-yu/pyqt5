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
tf = tf.compat.v1
tf.disable_v2_behavior()  # Use TF 1.x-style static graph

parser = argparse.ArgumentParser()
parser.add_argument("--model_dir", help="Directory containing the exported model")
parser.add_argument("--input_file", help="Input PNG image file")
parser.add_argument("--output_file", help="Output PNG image file")
a = parser.parse_args()


def apply_gan_model(model_dir, input_file, output_file):
    try:
        with open(input_file, "rb") as f:
            input_data = f.read()

        input_instance = dict(input=base64.urlsafe_b64encode(input_data).decode("ascii"), key="0")
        input_instance = json.loads(json.dumps(input_instance))

        with tf.Session() as sess:
            checkpoint_path = tf.train.latest_checkpoint(model_dir)
            if not checkpoint_path:
                raise ValueError(f"No checkpoint found in {model_dir}")

            saver = tf.train.import_meta_graph(checkpoint_path + ".meta")
            saver.restore(sess, checkpoint_path)

            input_vars = json.loads(tf.get_collection("inputs")[0].decode())
            output_vars = json.loads(tf.get_collection("outputs")[0].decode())
            input_tensor = tf.get_default_graph().get_tensor_by_name(input_vars["input"])
            output_tensor = tf.get_default_graph().get_tensor_by_name(output_vars["output"])

            input_value = np.array(input_instance["input"])
            output_value = sess.run(output_tensor, feed_dict={input_tensor: np.expand_dims(input_value, axis=0)})[0]

        output_instance = dict(output=output_value.decode("ascii"), key="0")
        b64data = output_instance["output"]
        b64data += "=" * (-len(b64data) % 4)
        output_data = base64.urlsafe_b64decode(b64data.encode("ascii"))
        nparr = np.frombuffer(output_data, np.uint8)
        img = cv2.imdecode(nparr, cv2.IMREAD_GRAYSCALE)

        if img is None:
            raise ValueError("Failed to decode image data. Check model output format.")

        img[img < 20] = 0
        _, buffer = cv2.imencode(".png", img)
        with open(output_file, "wb") as f:
            f.write(buffer.tobytes())

    except Exception as e:
        print(f"Error in apply_gan_model: {e}")
        raise


# model_path = "D:/Weekly_Report/Thesis_Weekly_Report/paper/paper_Implementation/pyqt5/aimodel/DAISdepthr=2andcollision/"                # 模型資料夾
# input_img = "D:/Weekly_Report/Thesis_Weekly_Report/paper/paper_Implementation/pyqt5/toKMU/AIoutput/onlay-14_LowerJawGOICPdown/flipped_256x768.png"          # 輸入圖片
# output_img = "D:/Weekly_Report/Thesis_Weekly_Report/paper/paper_Implementation/pyqt5/toKMU/AIoutput/onlay-14_LowerJawGOICPdown/aitest.png"        # 輸出圖片

# apply_gan_model(model_path, input_img, output_img)
# print("影像處理完成，輸出檔案已儲存於：", output_img)