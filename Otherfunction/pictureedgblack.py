# 主要目的：此程式碼提供兩個函數，用於檢測灰階圖像中的邊界像素並以指定顏色（預設為紅色）標記邊界，適用於牙科圖像處理流程。`get_image_bound` 使用像素移位方法檢測邊界，`mark_boundary_points` 使用卷積核檢測邊界，兩者均將結果保存為 RGB 圖像。此模組與 `DentalModelReconstructor` 和 GAN 模型整合，可用於增強牙科模型重建中的圖像邊界可視化。

from PIL import Image  # 導入 PIL 庫，用於圖像處理。
import os  # 導入 os 模組，用於檔案路徑操作和目錄創建。
import numpy as np  # 導入 NumPy 庫，用於數值運算和陣列處理。
from scipy.ndimage import convolve  # 導入 scipy.ndimage 的卷積函數，用於邊界檢測。

def get_image_bound(input_image_path, color=(255, 0, 0)):  # 定義檢測圖像邊界的函數。
    """
    檢測灰階圖像的邊界像素並以指定顏色標記。

    參數:
        input_image_path: 字串，輸入灰階圖像的路徑。
        color: 元組，RGB 顏色值，預設為紅色 (255, 0, 0)。

    返回:
        PIL.Image: 標記了邊界的 RGB 圖像，邊界像素為指定顏色，其餘為黑色。
    """
    # 打開圖像並轉換為灰階
    img = Image.open(input_image_path).convert('L')  # 打開圖像並轉為灰階（單通道，8 位元）。
    
    # 將圖像轉換為 NumPy 陣列
    img_array = np.array(img)  # 將 PIL 圖像轉為 NumPy 陣列，形狀為 (height, width)。
    
    # 將像素值小於 10 的地方設為 0
    img_array = np.where(img_array >= 10, img_array, 0)  # 低於閾值 10 的像素設為 0（去除噪點）。
    
    # 創建一個 RGB 陣列，初始化為黑色
    boundary_img_array = np.zeros((*img_array.shape, 3), dtype=np.uint8)  # 創建形狀為 (height, width, 3) 的全黑 RGB 陣列。
    
    # 獲取邊界條件，檢查上下左右是否是邊界點
    up_shift = np.roll(img_array, -1, axis=0)  # 將圖像向上移位 1 像素（檢查上邊界）。
    down_shift = np.roll(img_array, 1, axis=0)  # 將圖像向下移位 1 像素（檢查下邊界）。
    left_shift = np.roll(img_array, -1, axis=1)  # 將圖像向左移位 1 像素（檢查左邊界）。
    right_shift = np.roll(img_array, 1, axis=1)  # 將圖像向右移位 1 像素（檢查右邊界）。
    
    # 找到邊界像素點
    boundary_mask = ((img_array > 0) & 
                     ((up_shift == 0) | (down_shift == 0) | (left_shift == 0) | (right_shift == 0)))  # 檢測非零像素且至少一個相鄰像素為 0 的點。
    
    # 將邊界點設置為指定顏色
    boundary_img_array[boundary_mask] = color  # 將邊界像素設為指定 RGB 顏色（例如紅色）。
    
    # 將 NumPy 陣列轉換為 PIL 圖像並返回
    boundary_img = Image.fromarray(boundary_img_array)  # 將 RGB 陣列轉為 PIL 圖像。
    
    return boundary_img  # 返回標記了邊界的圖像。

def mark_boundary_points(input_image_path, output_folder, color=(255, 0, 0)):  # 定義標記邊界點並保存的函數。
    """
    使用卷積核檢測灰階圖像的邊界像素並以指定顏色標記，保存到指定資料夾。

    參數:
        input_image_path: 字串，輸入灰階圖像的路徑。
        output_folder: 字串，輸出圖像的保存資料夾。
        color: 元組，RGB 顏色值，預設為紅色 (255, 0, 0)。
    """
    # 開啟影像
    img = Image.open(input_image_path)  # 打開輸入圖像。

    # 確保影像是 8 位元深度的灰階影像
    if img.mode != 'L':  # 檢查圖像是否為灰階模式。
        img = img.convert('L')  # 若不是，轉為灰階（單通道，8 位元）。

    # 將影像轉換為 NumPy 陣列
    img_array = np.array(img)  # 將 PIL 圖像轉為 NumPy 陣列，形狀為 (height, width)。

    # 建立一個新的 RGB 映像用於標記邊界點
    boundary_img_array = np.zeros((img_array.shape[0], img_array.shape[1], 3), dtype=np.uint8)  # 創建全黑 RGB 陣列，形狀為 (height, width, 3)。

    # 建立一個遮罩來標記邊界點
    boundary_mask = np.zeros_like(img_array, dtype=bool)  # 創建與圖像同尺寸的布林遮罩，初始化為 False。

    # 標記所有非零像素點
    non_zero_mask = img_array > 0  # 創建非零像素遮罩（True 表示像素值大於 0）。

    # 使用卷積核來標記邊界點
    kernel = np.array([[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=np.float32)  # 定義拉普拉斯卷積核，用於邊界檢測。
    edge_mask = convolve(non_zero_mask.astype(float), kernel, mode='constant', cval=0.0) != 0  # 對非零遮罩應用卷積，檢測邊界（非零值表示邊界）。

    # 更新邊界掩碼
    boundary_mask[edge_mask] = True  # 將檢測到的邊界點設為 True。

    # 將邊界遮罩應用於邊界影像數組
    boundary_img_array[boundary_mask] = color  # 將邊界像素設為指定 RGB 顏色。

    # 將 NumPy 陣列轉換回影像
    boundary_img = Image.fromarray(boundary_img_array)  # 將 RGB 陣列轉為 PIL 圖像。
    
    # 確保輸出資料夾存在
    if not os.path.exists(output_folder):  # 檢查輸出資料夾是否存在。
        os.makedirs(output_folder)  # 若不存在，創建資料夾。
    
    # 建立輸出檔案路徑
    output_image_path = os.path.join(output_folder, os.path.basename(input_image_path))  # 使用輸入檔案名生成輸出路徑。
    
    # 保存邊界圖像
    boundary_img.save(output_image_path)  # 將標記了邊界的圖像保存到指定路徑。