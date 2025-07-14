# 主要目的：此程式碼使用 OpenCV (cv2) 載入一張灰階圖像（original_patch_0.png）
# 將所有非零像素值設為 255（白色），並將處理後的圖像保存為 modified_patch_0.png，適用於牙科影像處理中對圖像進行二值化處理的場景。
# 用在遮罩區域塗成白色覆蓋在缺陷處

import cv2  # 導入 OpenCV 庫，用於圖像處理。
import numpy as np  # 導入 NumPy 庫，用於數值運算和陣列處理。

# Load the image in grayscale
image = cv2.imread('original_patch_0.png', cv2.IMREAD_GRAYSCALE)  # 以灰階模式載入圖像 'original_patch_0.png'。

# Check if the image was loaded successfully
if image is None:  # 檢查圖像是否成功載入。
    print("Error: Could not load the image.")  # 如果載入失敗，打印錯誤訊息。
else:
    # Set all non-zero pixels to 255
    image[image != 0] = 255  # 將圖像中所有非零像素值設置為 255（白色），實現二值化效果。

    # Save the modified image
    cv2.imwrite('modified_patch_0.png', image)  # 將處理後的圖像保存為 'modified_patch_0.png'。
    print("Image processed and saved as 'modified_patch_0.png'.")  # 打印成功訊息，確認圖像已處理並保存。