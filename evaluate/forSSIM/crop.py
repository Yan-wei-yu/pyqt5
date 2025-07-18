# 主要目的：此程式碼定義了一個函數 `crop_to_mask`，用於根據遮罩圖裁剪原始圖像，僅保留與遮罩重疊的區域，並生成一張標記了遮罩邊界框的圖像（不保存）。遮罩圖假設為灰階圖，0 表示保留區域，1 表示移除區域。此程式碼適用於牙科圖像處理流程，例如從原始牙科圖像中裁剪出牙齒區域（與 `apply_gan_model`、 `DentalModelReconstructor` 或 `setup_camera_with_obb` 生成的圖像結合），並與邊界檢測（`get_image_bound` 或 `mark_boundary_points`）或圖像比較（`compare_images` 或 `compare_image_folders`）模組整合，用於聚焦牙齒區域的分析或品質評估。

import cv2  # 導入 OpenCV 庫，用於圖像讀取、處理、輪廓檢測和繪製邊界框。
import numpy as np  # 導入 NumPy 庫，用於陣列操作和遮罩處理。

def crop_to_mask(original_image_path, mask_path):  # 定義根據遮罩裁剪圖像的函數。
    """
    根據遮罩圖裁剪原始圖片,只保留與遮罩圖重疊的區域。
    並在原圖上標出遮罩的邊界框,但不會保存在最終圖像中。
    
    Parameters:
    original_image_path (str): 原始圖片的路徑
    mask_path (str): 遮罩圖的路徑（0表示要保留的區域,1表示要移除的區域）
    
    Returns:
    numpy.ndarray: 裁剪後的圖片
    numpy.ndarray: 標記了遮罩邊界框的圖片
    """
    # 讀取圖片
    original_image = cv2.imread(original_image_path)  # 讀取原始圖像（預設為 BGR 格式）。
    mask = cv2.imread(mask_path, 0)  # 讀取遮罩圖，指定為灰階模式（單通道）。

    # 確保遮罩和原圖大小相同
    if original_image.shape[:2] != mask.shape[:2]:  # 檢查原始圖像和遮罩圖的尺寸（高度和寬度）是否相同。
        mask = cv2.resize(mask, (original_image.shape[1], original_image.shape[0]))  # 若不同，將遮罩調整為與原始圖像相同的尺寸。

    # 找到遮罩的邊界框
    contours, _ = cv2.findContours(mask.astype(np.uint8), cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 檢測遮罩的外部輪廓，轉為 uint8 格式以符合 OpenCV 要求。
    x, y, w, h = cv2.boundingRect(contours[0])  # 獲取第一個輪廓的邊界框（左上角 x, y 座標及寬度 w 和高度 h）。

    # 根據邊界框裁剪原始圖片
    cropped_image = original_image[y:y+h, x:x+w]  # 根據邊界框座標裁剪原始圖像，保留指定區域。

    # 複製一份原始圖片以在上面畫框
    marked_image = original_image.copy()  # 複製原始圖像，用於繪製邊界框（不影響原始圖像）。

    # 在複製的原始圖上畫出遮罩的邊界框
    cv2.rectangle(marked_image, (x, y), (x+w, y+h), (0, 0, 255), 2)  # 在複製的圖像上繪製紅色邊界框（BGR 格式，線條粗細為 2）。

    return cropped_image, marked_image  # 返回裁剪後的圖像和標記邊界框的圖像（均為 NumPy 陣列）。