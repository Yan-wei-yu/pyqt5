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
    output_image_path = os.path.join(output_folder, os.path.basename(input2_image_path))  # 設定輸出圖像的完整路徑
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

# def combine_image(input_image_path, input2_image_path, output_folder):
#     # 确保输出文件夹存在
#     if not os.path.exists(output_folder):
#         os.makedirs(output_folder)
#     # 打开图像
#     img = Image.open(input_image_path)
#     img1 = Image.open(input2_image_path)

#     # 确保图像是24位的彩色图像
#     if img.mode != 'RGB':
#         img = img.convert('RGB')
#     if img1.mode != 'RGB':
#         img1 = img1.convert('RGB')

#     # 将图像转换为 numpy 数组
#     img_array = np.array(img)
#     img1_array = np.array(img1)

#     # 创建一个新图像来标记边界点，初始化为黑色
#     boundary_img_array = np.zeros_like(img_array)

#     # 条件：img1的像素不是黑色
#     red_condition = (img1_array[:, :, 0] != 0) | (img1_array[:, :, 1] != 0) | (img1_array[:, :, 2] != 0)
    
#     # 条件：img的像素不是黑色
#     yellow_condition = (img_array[:, :, 0] != 0) | (img_array[:, :, 1] != 0) | (img_array[:, :, 2] != 0)

#     # 标记为黄色（255, 255, 0）: 满足 red_condition 的像素
#     boundary_img_array[red_condition] = [255, 255, 0]

#     # 标记为红色（255, 0, 0）: 满足 yellow_condition 且 boundary_img_array 还没有标记的像素
#     boundary_img_array[yellow_condition & ~red_condition] = [255, 0, 0]

#     # 标记为绿色（0, 255, 0）: 满足 yellow_condition 且已经标记为黄色的像素
#     boundary_img_array[yellow_condition & red_condition] = [0, 255, 0]

#     # 将结果保存为图像
#     boundary_img = Image.fromarray(boundary_img_array)
    


#     # 保存结果图像
#     output_image_path = os.path.join(output_folder, os.path.basename(input_image_path))
#     boundary_img.save(output_image_path)

#     blue = [0, 0, 255]
#     yellow = [100, 100, 0]
#     red = [2, 0, 0]
#     green = [0, 255, 0]
#     reader = vtk.vtkPNGReader()
#     reader.SetFileName(output_image_path)
#     reader.Update()

#     image = reader.GetOutput()
#     dimensions = image.GetDimensions()


#     for y in range(dimensions[1]):
#         red_start_x = yellow_start_x = red_end_x = yellow_end_x = start_x = end_x = 0
#         start_red_x_set = start_yellow_x_set = False

#         for x in range(dimensions[0]):
#             pixel = get_pixel(image, x, y)
            
#             # 檢查紅色或綠色像素
#             if (pixel[0] != 0 and pixel[1] == red[1] and pixel[2] == red[2]) or \
#                 (pixel[0] == green[0] and pixel[1] == green[1] and pixel[2] == green[2]):
#                 if not start_red_x_set:
#                     red_start_x = x
#                 red_end_x = x
#                 start_red_x_set = True

#             # 檢查黃色或綠色像素
#             if (pixel[0] != 0 and pixel[1] != 0 and pixel[2] == yellow[2]) or \
#                 (pixel[0] == green[0] and pixel[1] == green[1] and pixel[2] == green[2]):
#                 if not start_yellow_x_set:
#                     yellow_start_x = x
#                 yellow_end_x = x
#                 start_yellow_x_set = True

#         # 決定起始和結束點
#         start_x = max(red_start_x, yellow_start_x)
#         end_x = min(red_end_x, yellow_end_x)

#         # 將起點到終點之間的像素塗成藍色
#         if end_x > start_x:
#             for x in range(start_x, end_x + 1):
#                 set_pixel(image, x, y, blue)

#     # 移除黃色、紅色和綠色像素
#     for y in range(dimensions[1]):
#         for x in range(dimensions[0]):
#             pixel = get_pixel(image, x, y)
#             if (pixel[0] != 0 and pixel[1] != 0 and pixel[2] == 0) or \
#                 (pixel[0] != 0 and pixel[1] == 0 and pixel[2] == 0) or \
#                 (pixel[0] == 0 and pixel[1] != 0 and pixel[2] == 0):
#                     set_pixel(image, x, y, [0, 0, 0])

#     # 保存處理後的圖像
#     writer = vtk.vtkPNGWriter()
#     writer.SetFileName(output_image_path)
#     writer.SetInputData(image)
#     writer.Write()


# # 函數來獲取像素值
# def get_pixel(image, x, y):
#     return [int(image.GetScalarComponentAsDouble(x, y, 0, i)) for i in range(3)]

# # 函數來設置像素值
# def set_pixel(image, x, y, color):
#     for i in range(3):
#         image.SetScalarComponentFromDouble(x, y, 0, i, color[i])
# red_image_files = os.listdir(red_folder_path)


# for image_file in red_image_files:
#     if image_file.endswith(".png"):  # 假設圖像檔案是PNG格式
#         input_image_path = os.path.join(red_folder_path, image_file)
#         input2_image_path = os.path.join(yellow_output_folder, image_file)
#         output_image_path = os.path.join(output_folder, image_file)
#         combine_image(input_image_path, input2_image_path, output_image_path)
