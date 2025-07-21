import cv2
import numpy as np

# 讀取兩張圖片
image1 = cv2.imread('./Ablation_Study_60000filter/data0007.png', cv2.IMREAD_GRAYSCALE)
image2 = cv2.imread('../Differentdepth_DCPR_answer/r=1/data0007.png', cv2.IMREAD_GRAYSCALE)

# 確保圖片成功讀取
if image1 is None or image2 is None:
    raise ValueError("無法讀取圖片，請檢查檔案路徑")

# 使用 Canny 邊緣檢測
edges1 = cv2.Canny(image1, 0, 38)
edges2 = cv2.Canny(image2, 0, 38)

# 計算兩張邊緣圖的差異，取絕對值
difference = cv2.absdiff(edges1, edges2)


# 將差異疊加在原圖上
colored_diff = cv2.cvtColor(image2, cv2.COLOR_GRAY2BGR)
colored_diff[difference > 0] = [0, 0, 255]  # 將差異區域標記為紅色

# 計算差異統計數據
num_diff_pixels = np.sum(difference > 0)
total_pixels = difference.size
diff_ratio = num_diff_pixels / total_pixels * 100
print(f"差異像素數量: {num_diff_pixels}, 差異比例: {diff_ratio:.2f}%")


# 在圖片右下角加入文字
text1 = f"Diff px: {num_diff_pixels}"
text2 = f"Diff %: {diff_ratio:.2f}%"
font = cv2.FONT_HERSHEY_SIMPLEX
font_scale = 0.35
font_color = (255, 255, 255)  # 白色文字
thickness = 1

# 計算文字位置
(h, w, _) = colored_diff.shape
text1_size = cv2.getTextSize(text1, font, font_scale, thickness)[0]
text2_size = cv2.getTextSize(text2, font, font_scale, thickness)[0]

text1_x = w - text1_size[0] - 10
text1_y = h - text2_size[1] - 10
text2_x = w - text2_size[0] - 10
text2_y = h - 5

# 繪製文字
cv2.putText(colored_diff, text1, (text1_x, text1_y), font, font_scale, font_color, thickness)
cv2.putText(colored_diff, text2, (text2_x, text2_y), font, font_scale, font_color, thickness)

# 顯示結果
# cv2.imshow('Colored Difference', colored_diff)

# # 顯示結果
cv2.imshow('Edges Image 1', edges1)
cv2.imshow('Edges Image 2', edges2)
cv2.imshow('Difference', difference)
cv2.imshow('Colored Difference', colored_diff)
# 等待按鍵並關閉視窗
cv2.waitKey(0)
cv2.destroyAllWindows()

# 儲存結果
cv2.imwrite('./edgecanny/edges1_ai_60000_data0007.png', edges1)
cv2.imwrite('./edgecanny/edges2_an.png', edges2)
cv2.imwrite('./cannygap/difference_60000_data0007.png', difference)
cv2.imwrite('./cannygap/differencecolor_60000_data0007.png', colored_diff)
