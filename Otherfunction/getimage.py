# 主要目的：此程式碼定義了一個函數 `apply_blue_mask`，用於將藍色掩碼應用於灰階圖像，生成遮罩後的圖像並保存。具體來說，它將原始圖像的白色部分（像素值 255）設為黑色，然後使用藍色掩碼（轉為二值化遮罩）保留原始圖像中對應的區域。此功能適用於牙科圖像處理流程，例如將交互式選取（來自 `LassoInteractor`）的藍色遮罩應用於 GAN 修復的圖像，生成最終的處理結果，與 `DentalModelReconstructor` 等模組整合。

import cv2  # 導入 OpenCV 庫，用於圖像處理和操作。
import numpy as np  # 導入 NumPy 庫，用於數值運算和陣列處理。

def apply_blue_mask(original_image_array, blue_mask_array, outdata_name):  # 定義應用藍色掩碼的函數。
    """
    將藍色掩碼應用於灰階圖像，生成遮罩後的圖像並保存。

    參數:
        original_image_array: NumPy 陣列，原始灰階圖像（單通道，8 位元）。
        blue_mask_array: NumPy 陣列，藍色掩碼圖像（BGR 格式，藍色區域表示保留區域）。
        outdata_name: 字串，輸出圖像的保存路徑。

    返回:
        無返回值，直接將結果圖像保存到指定路徑。
    """
    # 將原始圖像的白色部分變為黑色
    white_mask = cv2.inRange(original_image_array, np.array([255]), np.array([255]))  # 創建白色像素（值為 255）的遮罩。
    original_image_array[np.where(white_mask > 0)] = [0]  # 將白色像素設為黑色（值為 0）。

    # 應用藍色區塊掩碼
    blue_mask_gray = cv2.cvtColor(blue_mask_array, cv2.COLOR_BGR2GRAY)  # 將藍色掩碼圖像轉為灰階。
    _, thresholded_mask = cv2.threshold(blue_mask_gray, 1, 255, cv2.THRESH_BINARY)  # 對灰階掩碼進行二值化（閾值 1，保留非零像素）。
    
    # 使用藍色掩碼到原始圖像
    result_image_array = cv2.bitwise_and(original_image_array, original_image_array, mask=thresholded_mask)  # 應用二值化遮罩，保留遮罩為 255 的區域。

    # 保存結果圖像
    cv2.imwrite(outdata_name, result_image_array)  # 將遮罩後的圖像保存到指定路徑。



# # 原始图像文件夹和蓝色区块图像文件夹
# original_folder = "D:/Users/user/Desktop/papergan/paper/crown/traincode/combineimage/"
# blue_mask_folder = "D:/Users/user/Desktop/papergan/paper/crown/traincode/bluemask/"
# output_folder = "D:/Users/user/Desktop/papergan/paper/crown/traincode/final/"

# # 确保输出文件夹存在
# os.makedirs(output_folder, exist_ok=True)

# # 遍历原始图像文件夹
# for filename in os.listdir(original_folder):
#     if filename.endswith(".png"):  # 确保是PNG文件
#         original_image = cv2.imread(os.path.join(original_folder, filename))
#         blue_mask_filename = os.path.join(blue_mask_folder, filename)

#         # 处理一些白色部分并将其变为黑色
#         white_mask = cv2.inRange(original_image, (255, 255, 255), (255, 255, 255))
#         original_image[np.where(white_mask > 0)] = [0, 0, 0]

#         # 查找对应的蓝色区块图像
#         if os.path.exists(blue_mask_filename):
#             blue_mask_image = cv2.imread(blue_mask_filename)
#             blue_mask_gray = cv2.cvtColor(blue_mask_image, cv2.COLOR_BGR2GRAY)
#             _, thresholded_mask = cv2.threshold(blue_mask_gray, 1, 255, cv2.THRESH_BINARY)
#             # 应用掩码
#             result_image = cv2.bitwise_and(original_image, original_image, mask=thresholded_mask)
#             result_image_8bit = cv2.convertScaleAbs(result_image)

#             # 保存结果图像到输出文件夹
#             output_filename = os.path.join(output_folder, filename)
#             cv2.imwrite(output_filename, result_image_8bit)
#             # cv2.imwrite(output_filename, result_image)
           

# print("操作完成。")
