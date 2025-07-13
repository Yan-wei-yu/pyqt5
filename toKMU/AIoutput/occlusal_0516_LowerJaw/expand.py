import cv2
import numpy as np
import matplotlib.pyplot as plt

# 讀取圖片（0 表示以灰階模式讀取）
mask = cv2.imread('modified_patch_0.png', 0)

# 二值化，確保只有 0 與 255
_, binary = cv2.threshold(mask, 127, 255, cv2.THRESH_BINARY)

# 找輪廓（邊界）
contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

# 建立一個空白畫布來畫輪廓
edge_image = np.zeros_like(mask)

# 畫出輪廓
cv2.drawContours(edge_image, contours, -1, (255), 1)  # 1 表示邊界的粗細

kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
edge_thick = cv2.dilate(edge_image, kernel, iterations=1)

# 儲存邊界圖
cv2.imwrite('mask_boundary.png', edge_thick)