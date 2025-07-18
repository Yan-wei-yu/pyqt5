# 主要目的：此程式碼定義了一個函數 `compare_images`，用於比較兩張圖像的結構相似度（SSIM），並返回相似度百分比。輸入可以是圖像文件路徑（字串或 Path 物件）或 OpenCV 格式的圖像（NumPy 陣列），支援彩色或灰階圖像，自動轉換為灰階進行比較。此程式碼適用於牙科圖像處理流程，例如比較 GAN 模型修復的圖像（來自 `apply_gan_model`）與標準答案圖像（來自 `DentalModelReconstructor` 或 `setup_camera_with_obb`），或評估邊界檢測結果（來自 `get_image_bound` 或 `mark_boundary_points`）的相似性，與遮罩裁剪（`crop_to_mask`）模組間接整合。

import numpy as np  # 導入 NumPy 庫，用於陣列操作和圖像數據處理。
import cv2  # 導入 OpenCV 庫，用於圖像處理（如色彩轉換、調整大小）。
from PIL import Image  # 導入 PIL 庫，用於讀取圖像文件並轉換格式。
from skimage.metrics import structural_similarity as ssim  # 導入 SSIM 函數，用於計算結構相似性。
from pathlib import Path  # 導入 Path 類，用於處理文件路徑（跨平台兼容）。

def compare_images(image1, image2):  # 定義比較兩張圖像相似度的函數。
    """
    比較兩張圖片的相似度，支持文件路徑(str/Path)或cv2圖像作為輸入
    
    Parameters:
    image1: str/Path/numpy.ndarray - 第一張圖片的路徑或cv2圖像
    image2: str/Path/numpy.ndarray - 第二張圖片的路徑或cv2圖像
    
    Returns:
    float: 相似度百分比
    """
    # 檢查輸入類型並相應處理
    def process_input(img):  # 定義內部函數，處理輸入圖像格式。
        if isinstance(img, (str, Path)):  # 檢查輸入是否為字串或 Path 物件（文件路徑）。
            # 如果輸入是路徑(str)或Path物件
            return np.array(Image.open(str(img)).convert('L'))  # 打開圖像並轉為灰階，轉換為 NumPy 陣列。
        elif isinstance(img, np.ndarray):  # 檢查輸入是否為 NumPy 陣列（OpenCV 圖像）。
            # 如果輸入是cv2圖像
            if len(img.shape) == 3:  # 檢查是否為彩色圖像（3 維陣列）。
                # 如果是彩色圖片，轉換為灰度圖
                return cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)  # 將彩色圖像轉為灰階。
            return img  # 如果已是灰階圖像，直接返回。
        else:
            raise TypeError("輸入必須是圖片路徑(str/Path)或cv2圖像(numpy.ndarray)")  # 若輸入類型無效，拋出異常。

    # 處理兩張圖片
    img1_array = process_input(image1)  # 處理第一張圖像，轉為灰階 NumPy 陣列。
    img2_array = process_input(image2)  # 處理第二張圖像，轉為灰階 NumPy 陣列。

    # # 使用 Canny 邊緣檢測（已註解）
    # img1_array = cv2.Canny(img1_array, 0, 80)  # 對第一張圖像應用 Canny 邊緣檢測（閾值 0 和 80）。
    # img2_array = cv2.Canny(img2_array, 0, 80)  # 對第二張圖像應用 Canny 邊緣檢測（閾值 0 和 80）。

    # # 顯示圖像（已註解，僅用於調試）
    # cv2.imshow('1', img1_array)  # 顯示第一張圖像。
    # cv2.imshow('2', img2_array)  # 顯示第二張圖像。
    # cv2.waitKey(0)  # 等待用戶按鍵。
    # cv2.destroyAllWindows()  # 關閉所有顯示窗口。

    # 確保兩張圖片大小相同
    if img1_array.shape != img2_array.shape:  # 檢查兩張圖像的尺寸是否相同。
        img2_array = cv2.resize(img2_array, (img1_array.shape[1], img1_array.shape[0]))  # 將第二張圖像調整為第一張圖像的尺寸。

    # 計算結構相似性指數 (SSIM)
    similarity = ssim(img1_array, img2_array)  # 使用 skimage 的 SSIM 函數計算結構相似性。

    # 轉換為百分比
    percentage = similarity * 100  # 將 SSIM 值（範圍 [-1, 1]）轉換為百分比（範圍 [-100, 100]）。

    return percentage  # 返回相似度百分比。