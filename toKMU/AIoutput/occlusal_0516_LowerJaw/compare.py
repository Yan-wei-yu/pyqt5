from PIL import Image
import numpy as np

# 讀入三張圖片
defect = Image.open("original.png").convert("L")
ai = Image.open("ai.png").convert("L")
mask = Image.open("modified_patch_0.png").convert("L")  # 只需灰階遮罩

# 轉成 numpy 陣列
arr_defect = np.array(defect)
arr_ai = np.array(ai)
arr_mask = np.array(mask)

# 將 mask 二值化（非零為 True，表示要替換）
mask_binary = arr_mask > 127  # 可以調整這個 threshold

# 建立結果圖陣列
result = arr_defect.copy()
result[mask_binary] = arr_ai[mask_binary]

# 存回圖片
result_img = Image.fromarray(result)
result_img.save("patched_resultV1.png")
print("修補結果已儲存為 patched_resultV1.png")
