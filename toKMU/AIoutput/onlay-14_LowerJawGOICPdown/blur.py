import cv2
import numpy as np

# 載入修補後的圖片
depth_fixed = cv2.imread('./ai.png', cv2.IMREAD_GRAYSCALE)

# 建立遮罩：手動框選修補區域 + dilate 擴展出過渡邊界
mask = cv2.imread('./maskedge.png', 0)  # 二值遮罩圖，中間缺損為255，其餘為0
border = cv2.dilate(mask, np.ones((2,2), np.uint8)) - mask

# 針對邊界模糊處理
smoothed = cv2.GaussianBlur(depth_fixed, (11, 11), 5)

# 只保留邊界部分的模糊值，其餘保留原值
depth_result = depth_fixed.copy()
depth_result[border > 0] = smoothed[border > 0]

cv2.imwrite('./endGaussian.png', depth_result)


# import cv2

# # 修補後的圖片（要貼上來的）
# src = cv2.imread("./original.png")

# # 原始有缺陷的圖片（要被貼上去）
# dst = cv2.imread("./ai.png")

# # 讀入灰階遮罩
# mask_gray = cv2.imread("./maskedge.png", cv2.IMREAD_GRAYSCALE)

# # 計算缺陷區的幾何中心點
# M = cv2.moments(mask_gray)
# if M["m00"] != 0:
#     cx = int(M["m10"] / M["m00"])
#     cy = int(M["m01"] / M["m00"])
#     center = (cx, cy)
# else:
#     center = (128, 128)

# # OpenCV 要求 mask 為三通道
# mask_3ch = cv2.merge([mask_gray, mask_gray, mask_gray])

# # 執行 Poisson 融合
# output = cv2.seamlessClone(src, dst, mask_3ch, center, cv2.NORMAL_CLONE)

# # 儲存結果
# cv2.imwrite("./poisson_blendedge.png", output)
