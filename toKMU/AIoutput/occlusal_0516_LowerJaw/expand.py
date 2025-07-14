# 主要目的：此程式碼使用 OpenCV (cv2) 載入一張灰階圖像（modified_patch_0.png，通常為二值化遮罩）
# ，對其進行二值化處理，提取外部輪廓，繪製輪廓線並進行膨脹處理，最終生成並保存邊界圖（mask_boundary.png）。
# 此程式適用於牙科影像處理中提取牙齒或修補區域的邊界，生成用於後續平滑或分析的邊界圖。

import cv2  # 導入 OpenCV 庫，用於圖像處理和輪廓檢測。
import numpy as np  # 導入 NumPy 庫，用於數值運算和陣列處理。
import matplotlib.pyplot as plt  # 導入 Matplotlib 庫（本程式碼中未使用，可能是遺留代碼）。

# 讀取圖片（0 表示以灰階模式讀取）
mask = cv2.imread('modified_patch_0.png', 0)  # 以灰階模式載入圖像 'modified_patch_0.png'，通常為二值化遮罩。

# 二值化，確保只有 0 與 255
_, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)  # 對圖像進行二值化處理，閾值 127，將像素值轉為 0 或 255。

# 找輪廓（邊界）
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 檢測二值圖像的外部輪廓，使用簡單近似方法。

# 建立一個空白畫布來畫輪廓
edge_image = np.zeros_like(mask)  # 創建與輸入圖像相同大小的空白陣列（全零），作為繪製輪廓的畫布。

# 畫出輪廓
cv2.drawContours(edge_image, contours, -1, (255), 1)  # 在空白畫布上繪製所有輪廓，顏色為 255（白色），線條粗細為 1 像素。

kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))  # 創建 5x5 橢圓形結構元素，用於膨脹操作。
edge_thick = cv2.dilate(edge_image, kernel, iterations=1)  # 對輪廓圖進行一次膨脹操作，增粗邊界線。

# 儲存邊界圖
cv2.imwrite('mask_boundary.png', edge_thick)  # 將膨脹後的邊界圖保存為 'mask_boundary.png'。