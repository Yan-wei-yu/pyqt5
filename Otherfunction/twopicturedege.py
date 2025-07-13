import numpy as np  # 導入 NumPy 用於數值運算和陣列處理
from PIL import Image  # 導入 PIL 的 Image 模組用於圖像處理
import os  # 導入 os 模組用於檔案系統操作
import numba  # 導入 numba 用於 JIT 編譯和性能優化
from .imageProcess import calculate_image_difference  # 從 imageProcess 模組導入特定函數
from .getimage import apply_blue_mask  # 從 getimage 模組導入特定函數

@numba.jit(nopython=True)  # 裝飾器將函數編譯為機器碼以加快執行速度
def process_image(img_array, img1_array):  # 定義處理兩個圖像陣列的函數
    height, width = img_array.shape[:2]  # 獲取圖像尺寸（高度和寬度）
    result = np.zeros_like(img_array)  # 創建與輸入相同形狀的空陣列用於儲存結果

    for y in range(height):  # 遍歷圖像的每一行
        # 初始化用於追蹤紅色和黃色區域的變數
        red_start_x = yellow_start_x = red_end_x = yellow_end_x = 0
        start_red_x_set = start_yellow_x_set = False
        
        for x in range(width):  # 遍歷當前行中的每個像素
            pixel_img = img_array[y, x]  # 從第一張圖像獲取像素值
            pixel_img1 = img1_array[y, x]  # 從第二張圖像獲取像素值
            
            # 檢查 img1 中的像素是否為紅色（非零）或綠色 ([0, 255, 0])
            is_red_or_green = np.any(pixel_img1 != 0) or np.all(pixel_img1 == np.array([0, 255, 0]))
            # 檢查 img 中的像素是否為黃色（非零）或綠色 ([0, 255, 0])
            is_yellow_or_green = np.any(pixel_img != 0) or np.all(pixel_img == np.array([0, 255, 0]))
            
            if is_red_or_green:  # 如果檢測到紅色或綠色
                if not start_red_x_set:  # 如果尚未設置紅色起始點
                    red_start_x = x  # 記錄紅色區域的起始 x 座標
                red_end_x = x  # 更新紅色區域的結束 x 座標
                start_red_x_set = True  # 標記紅色起始點已設置
            
            if is_yellow_or_green:  # 如果檢測到黃色或綠色
                if not start_yellow_x_set:  # 如果尚未設置黃色起始點
                    yellow_start_x = x  # 記錄黃色區域的起始 x 座標
                yellow_end_x = x  # 更新黃色區域的結束 x 座標
                start_yellow_x_set = True  # 標記黃色起始點已設置
        
        # 計算重疊區域的起點和終點
        start_x = max(red_start_x, yellow_start_x)  # 取紅色和黃色起始點的最大值
        end_x = min(red_end_x, yellow_end_x)  # 取紅色和黃色終點的最小值
        
        if end_x > start_x:  # 如果存在有效重疊區域
            result[y, start_x:end_x+1] = np.array([255, 0, 0])  # 將重疊區域設為藍色 (BGR 格式)
    
    return result  # 返回處理後的圖像陣列

def ensure_png_extension(file_path):  # 確保檔案路徑以 .png 結尾的函數
    return file_path if file_path.lower().endswith(".png") else file_path + ".png"  # 如果不是 .png 則添加副檔名

def combine_image(input_image_path, input2_image_path, output_folder, downimage, upimage):  # 定義合併圖像的函數
    input_image_path = ensure_png_extension(input_image_path)  # 確保第一張圖像路徑有 .png 副檔名
    input2_image_path = ensure_png_extension(input2_image_path)  # 確保第二張圖像路徑有 .png 副檔名
    if not os.path.exists(output_folder):  # 檢查輸出資料夾是否存在
        os.makedirs(output_folder)  # 如果不存在則創建資料夾
    output_image_path = os.path.join(output_folder, os.path.basename(input_image_path))  # 設定輸出圖像的完整路徑
    img = Image.open(input_image_path).convert('RGB')  # 打開第一張圖像並轉換為 RGB 格式
    img1 = Image.open(input2_image_path).convert('RGB')  # 打開第二張圖像並轉換為 RGB 格式
    img_array = np.array(img)  # 將第一張圖像轉換為 NumPy 陣列
    img1_array = np.array(img1)  # 將第二張圖像轉換為 NumPy 陣列
    # 處理圖像
    blue_result_array = process_image(img_array, img1_array)  # 調用 process_image 函數處理圖像
    # cv2.imwrite(output_image_path, blue_result_array)  # (註釋掉) 將結果保存為圖像檔案
    get_combine_data = calculate_image_difference(upimage, downimage)  # 計算上下圖像的差異
    combine_image_array_np = np.array(get_combine_data)  # 將合併數據轉換為 NumPy 陣列
    blue_image_array_np = np.array(blue_result_array)  # 將藍色結果轉換為 NumPy 陣列
    
    # 保存結果
    apply_blue_mask(combine_image_array_np, blue_image_array_np, output_image_path)  # 應用藍色遮罩並保存最終圖像

