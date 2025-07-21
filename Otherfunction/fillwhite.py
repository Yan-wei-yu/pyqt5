# 主要目的：此程式碼定義了一個函數 `process_image_pair`，用於處理一對圖像，其中第一張圖像是帶有紅色邊框的 RGB 圖像（通常來自邊界檢測模組，如 `get_image_bound`），第二張圖像是深度圖像（灰階）。函數的主要功能是提取紅色邊框對應的輪廓，將深度圖像中輪廓內的空白（像素值為 0）填充為白色（255），並去除不符合條件的像素區域（例如從小於 220 到 255 再回到小於 220 的小區域），以修復深度圖中的破洞。處理後的圖像保存到指定路徑，適用於牙科圖像處理流程，與 `DentalModelReconstructor`、GAN 模型和邊界檢測模組整合，用於生成精確的 3D 重建輸入。

import cv2  # 導入 OpenCV 庫，用於圖像處理、輪廓檢測和操作。
import numpy as np  # 導入 NumPy 庫，用於數值運算和陣列處理。

def process_image_pair(img1, img2_path, output_path):  # 定義處理圖像對的函數。
    """
    處理一對圖像：第一張為帶紅色邊框的 RGB 圖像，第二張為灰階深度圖像。
    提取邊框輪廓，填充輪廓內的空白（像素值 0）為 255，並去除特定像素區域。

    參數:
        img1: PIL.Image 或 NumPy 陣列，帶紅色邊框的 RGB 圖像。
        img2_path: 字串，灰階深度圖像的檔案路徑。
        output_path: 字串，處理後圖像的保存路徑。

    返回:
        無返回值，直接將處理後的圖像保存到指定路徑。
    """
    # 將第一張影像從 RGB 轉換為 BGR 格式
    img1 = cv2.cvtColor(np.array(img1), cv2.COLOR_RGB2BGR)  # 將 PIL 圖像或 NumPy 陣列轉為 BGR 格式（OpenCV 使用 BGR）。

    # 讀取第二張影像，將其轉為灰階
    img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)  # 以灰階模式讀取深度圖像（單通道，8 位元）。

    # 提取第二張影像的紅色通道，並進行二值化，將邊框部分設為白色（255），其餘部分為黑色（0）
    _, binary_mask = cv2.threshold(img2, 1, 255, cv2.THRESH_BINARY)  # 對深度圖像進行二值化，閾值為 1，生成 0/255 遮罩。

    # 根據二值化的邊框，找到輪廓
    contours, _ = cv2.findContours(binary_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 檢測外部輪廓，簡化輪廓點。

    # 創建一個與 img2 同大小的空白遮罩圖像
    mask = np.zeros(img2.shape, dtype=np.uint8)  # 創建與深度圖像同尺寸的空白遮罩（全為 0）。

    # 在遮罩上繪製所有的輪廓，並將輪廓內部填滿（255 表示白色）
    cv2.drawContours(mask, contours, -1, (255), thickness=cv2.FILLED)  # 繪製所有輪廓並填充為白色。

    # 將原始影像 (img2) 複製一份，並對遮罩內的深度值為 0 的像素設為 255
    result = img2.copy()  # 複製深度圖像以保留原始數據。
    result[(mask > 0) & (img2 == 0)] = 255  # 將輪廓內像素值為 0 的區域設為 255（修復破洞）。
    result[mask == 0] = 0

    # 處理圖像中某些區域的像素，使得那些從小於 220 變為 255 再從 255 變回小於 220 的區間內的像素被重置為 0
    # 這通常用於去除某些圖像中的小區域、圖像邊緣或不需要的干擾部分
    # 找出從像素值小於 220 變為 255 的位置（起點）
    start_positions = (result[:, :-1] < 220) & (result[:, 1:] == 255)  # 檢測每行中從 <220 到 255 的轉換點。

    # 找出從像素值為 255 變為小於 220 的位置（終點）
    end_positions = (result[:, :-1] == 255) & (result[:, 1:] < 220)  # 檢測每行中從 255 到 <220 的轉換點。

    # 遍歷每一行，將找到的區間（從小於 220 變為 255）設為 0
    for row in range(result.shape[0]):  # 迭代圖像的每一行。
        # 找到該行中的起點和終點位置
        starts = np.where(start_positions[row])[0]  # 獲取起點索引。
        ends = np.where(end_positions[row])[0]  # 獲取終點索引。

        # 確保每行的起點和終點數量一致
        if len(starts) == len(ends):  # 檢查起點和終點數量是否匹配。
            for start, end in zip(starts, ends):  # 遍歷每對起點和終點。
                # 將起點和終點之間的區間內的像素值設為 0
                result[row, start:end+1] = 0  # 重置區間內像素值（去除小區域干擾）。

    # 儲存處理後的影像到指定路徑
    cv2.imwrite(output_path, result)  # 將處理後的圖像保存到指定路徑。
# folder1 = 'D:/Weekly_Report/Thesis_Weekly_Report/paper/paper_Implementation/remesh/c++bug/Downred/' # 包含第一張圖（紅色邊框）的資料夾
# folder2 = 'D:/Weekly_Report/Thesis_Weekly_Report/paper/paper_Implementation/remesh/c++bug/Down/' # 包含第二張圖（深度圖）的資料夾
# output_folder = 'D:/Weekly_Report/Thesis_Weekly_Report/paper/paper_Implementation/remesh/c++bug/Downfill/' # 輸出結果的資料夾

# # 確保輸出資料夾存在
# if not os.path.exists(output_folder):
#  os.makedirs(output_folder)

# # 遍歷資料夾
# for filename in os.listdir(folder1):
#     if filename.endswith(('.png', '.jpg', '.jpeg')): # 可以根據需要調整檔案類型
#         img1_path = os.path.join(folder1, filename)
#         img2_path = os.path.join(folder2, filename)

#         # 檢查對應的檔案是否存在
#         if os.path.exists(img2_path):
#             output_path = os.path.join(output_folder, filename)
#             process_image_pair(img1_path, img2_path, output_path)
#             print(f"Processed: {filename}")
#         else:
#             print(f"Skipped: {filename} (No matching file in folder2)")

# print("Processing completed.")


