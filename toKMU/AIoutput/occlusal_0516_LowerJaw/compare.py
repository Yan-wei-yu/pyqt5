# 主要目的：此程式碼使用 PIL (Python Imaging Library) 
# 載入三張灰階圖像（原始缺陷圖 original.png、AI 修補圖 ai.png 和二值遮罩 modified_patch_0.png），根據遮罩將 AI 修補圖的像素應用到原始缺陷圖的指定區域
# 生成修補後的圖像並保存為 patched_resultV1.png。此程式適用於牙科影像處理中，利用 AI 修補結果和遮罩進行區域性圖像修復。

from PIL import Image  # 導入 PIL 的 Image 模組，用於圖像處理。
import numpy as np  # 導入 NumPy 庫，用於數值運算和陣列處理。

# 讀入三張圖片
defect = Image.open("original.png").convert("L")  # 載入原始缺陷圖像 original.png 並轉為灰階（單通道）。
ai = Image.open("ai.png").convert("L")  # 載入 AI 修補圖像 ai.png 並轉為灰階。
mask = Image.open("modified_patch_0.png").convert("L")  # 載入二值遮罩圖 modified_patch_0.png 並轉為灰階。

# 轉成 numpy 陣列
arr_defect = np.array(defect)  # 將原始缺陷圖像轉為 NumPy 陣列。
arr_ai = np.array(ai)  # 將 AI 修補圖像轉為 NumPy 陣列。
arr_mask = np.array(mask)  # 將遮罩圖像轉為 NumPy 陣列。

# 將 mask 二值化（非零為 True，表示要替換）
mask_binary = arr_mask > 127  # 對遮罩進行二值化，閾值 127，生成布林陣列（像素值大於 127 為 True，表示修補區域）。

# 建立結果圖陣列
result = arr_defect.copy()  # 複製原始缺陷圖陣列作為結果圖的基礎。
result[mask_binary] = arr_ai[mask_binary]  # 將遮罩為 True 的區域替換為 AI 修補圖的對應像素值。

# 存回圖片
result_img = Image.fromarray(result)  # 將結果陣列轉回 PIL Image 對象。
result_img.save("patched_resultV1.png")  # 將修補後的圖像保存為 patched_resultV1.png。
print("修補結果已儲存為 patched_resultV1.png")  # 打印成功訊息，確認修補結果已保存。