# 主要目的：此程式碼使用 OpenCV (cv2) 對修補後的灰階圖像（patched_resultV1.png）進行邊界平滑處理。
# 它載入圖像和遮罩（mask_boundary.png），通過膨脹操作生成過渡邊界區域，對邊界應用高斯模糊，然後將模糊結果應用於邊界區域，保留非邊界區域的原始值，最終保存處理後的圖像為 tworestore.png，適用於牙科影像處理中修補區域邊界的平滑優化。

import cv2  # 導入 OpenCV 庫，用於圖像處理。
import numpy as np  # 導入 NumPy 庫，用於數值運算和陣列處理。

# 載入修補後的圖片
depth_fixed = cv2.imread('./patched_resultV1.png', cv2.IMREAD_GRAYSCALE)  # 以灰階模式載入修補後的圖像 'patched_resultV1.png'。

# 建立遮罩：手動框選修補區域 + dilate 擴展出過渡邊界
mask = cv2.imread('./mask_boundary.png', 0)  # 以灰階模式載入二值遮罩圖 'mask_boundary.png'，缺損區域為 255，其餘為 0。
border = cv2.dilate(mask, np.ones((2,2), np.uint8)) - mask  # 對遮罩進行 2x2 膨脹操作，然後減去原遮罩，生成過渡邊界區域（邊界像素為非零值）。

# 針對邊界模糊處理
smoothed = cv2.GaussianBlur(depth_fixed, (11, 11), 5)  # 對修補後的圖像應用高斯模糊，核大小為 11x11，標準差為 5。

# 只保留邊界部分的模糊值，其餘保留原值
depth_result = depth_fixed.copy()  # 複製原始修補圖像，作為最終結果的基礎。
depth_result[border > 0] = smoothed[border > 0]  # 將邊界區域（border > 0）的像素值替換為模糊後的值，非邊界區域保留原始值。

cv2.imwrite('./tworestore.png', depth_result)  # 將處理後的圖像保存為 'tworestore.png'。