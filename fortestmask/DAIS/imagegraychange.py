import cv2
import numpy as np

# 讀取圖片
image_path = "./Ablation_Study_Test1/diff_data0402.png"
image = cv2.imread(image_path, cv2.IMREAD_GRAYSCALE)

# 創建輸出影像，先複製原圖
output_image = image.copy()

# 找到所有非 0 的像素，將其值乘以 4，並限制最大值為 255
output_image[output_image != 0] = np.clip(output_image[output_image != 0] * 2, 0, 255)

# 保存結果
output_path = "./diff_data0402_test1_2.png"
cv2.imwrite(output_path, output_image)

print(f"處理完成，已保存至: {output_path}")