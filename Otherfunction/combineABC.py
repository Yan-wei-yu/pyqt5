# 主要功能：將三張圖像水平拼接並保存到指定路徑
import cv2  # OpenCV 庫，用於圖像處理
import numpy as np  # NumPy 庫，用於數組操作

def merge_images(image_A, image_B, image_C, output_path):
    """
    將三張圖像水平拼接並保存到指定路徑。
    參數:
        image_A: 第一張圖像的路徑
        image_B: 第二張圖像的路徑
        image_C: 第三張圖像的路徑
        output_path: 輸出拼接圖像的保存路徑
    """
    # 讀取三張圖像，保留原始通道（包括透明度）
    im_A = cv2.imread(image_A, cv2.IMREAD_UNCHANGED)
    im_B = cv2.imread(image_B, cv2.IMREAD_UNCHANGED)
    im_C = cv2.imread(image_C, cv2.IMREAD_UNCHANGED)

    # 檢查圖像是否成功加載
    if im_A is None or im_B is None or im_C is None:
        raise ValueError("One or more input images could not be loaded.")  # 如果任一圖像加載失敗，拋出異常

    # 定義目標尺寸為 256x256
    target_size = (256, 256)
    # 將所有圖像調整到目標尺寸
    im_A = cv2.resize(im_A, target_size)  # 調整第一張圖像大小
    im_B = cv2.resize(im_B, target_size)  # 調整第二張圖像大小
    im_C = cv2.resize(im_C, target_size)  # 調整第三張圖像大小

    # 水平拼接三張圖像（axis=1 表示沿水平方向拼接）
    im_ABC = np.concatenate([im_A, im_B, im_C], axis=1)

    # 保存拼接後的圖像到指定路徑
    cv2.imwrite(output_path, im_ABC)
    print(f"Saved merged image at {output_path}")  # 打印保存成功的訊息

# # 示例用法
# image_A = "path/to/image_A.png"
# image_B = "path/to/image_B.png"
# image_C = "path/to/image_C.png"
# output_path = "path/to/output.png"

# merge_images(image_A, image_B, image_C, output_path)