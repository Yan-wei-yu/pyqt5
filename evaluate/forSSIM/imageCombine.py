# 主要目的：此程式碼定義了一個函數 `combine_images_with_text`，用於將多張圖像水平合併，並在每張圖像下方以及畫布頂部和底部添加文字標籤，生成一個包含所有圖像和文字的單一圖像。圖像支援灰階或彩色格式，自動轉換為三通道（BGR）格式以保持一致性。此程式碼適用於牙科圖像處理流程，例如展示 GAN 模型修復圖像（來自 `apply_gan_model`）與標準答案圖像（來自 `DentalModelReconstructor` 或 `setup_camera_with_obb`）的比較，或顯示邊界檢測結果（來自 `get_image_bound` 或 `mark_boundary_points`）的視覺化結果，與遮罩裁剪（`crop_to_mask`）模組間接整合，用於結果展示或報告生成。

import cv2  # 導入 OpenCV 庫，用於圖像處理（合併、文字繪製、保存等）。
import numpy as np  # 導入 NumPy 庫，用於陣列操作和創建畫布。

def combine_images_with_text(images, texts, output_path=None, top_padding=50, bottom_padding=50):  # 定義合併圖像並添加文字的函數。
    """
    合併多張圖片並在每張圖片上添加文字，支援在頂部和底部添加額外文字
    
    參數:
    images: 圖片列表，每個元素都是 numpy.ndarray（灰階或彩色圖像）
    texts: 要添加的文字列表（必須比圖片數量多二個，第一個是頂部文字，最後一個是底部文字）
    output_path: 輸出圖片的路徑（可選，字串）
    top_padding: 頂部文字的預留空間（預設 50 像素）
    bottom_padding: 底部文字的預留空間（預設 50 像素）
    
    返回:
    combined_image: 合併後的圖片 (numpy.ndarray)
    """
    if not images or not isinstance(images, list):  # 檢查圖像列表是否為非空且為列表。
        raise ValueError("images 必須是非空的圖片列表")  # 若無效，拋出異常。

    if len(texts) != len(images) + 2:  # 檢查文字數量是否比圖像數量多兩個（頂部和底部文字）。
        raise ValueError("文字數量必須比圖片數量多二個（頂部和底部文字）")  # 若無效，拋出異常。

    # 計算合併後圖片的尺寸
    max_height = max(img.shape[0] for img in images)  # 獲取所有圖像的最大高度。
    total_width = sum(img.shape[1] for img in images)  # 計算所有圖像寬度的總和。

    # 創建一個新的畫布（加上頂部和底部文字的空間）
    combined_image = np.zeros((max_height + top_padding + bottom_padding, total_width, 3), dtype=np.uint8)  # 創建三通道（BGR）空白畫布，尺寸為 (高度+上下間距, 總寬度, 3)。

    # 設定文字參數
    font = cv2.FONT_HERSHEY_SIMPLEX  # 設定字體為 Hershey Simplex。
    font_scale = 0.7  # 設定字體縮放比例。
    font_color = (0, 0, 255)  # 設定字體顏色為紅色 (BGR 格式)。
    thickness = 2  # 設定文字線條粗細。

    # 添加頂部文字
    top_text = texts[0]  # 獲取第一個文字作為頂部文字。
    text_size = cv2.getTextSize(top_text, font, font_scale, thickness)[0]  # 計算頂部文字的尺寸。
    text_x = (total_width - text_size[0]) // 2  # 計算頂部文字的 x 座標（水平置中）。
    text_y = top_padding - 20  # 計算頂部文字的 y 座標（頂部空間內置中）。

    cv2.putText(combined_image, top_text, (text_x, text_y), 
                font, font_scale, font_color, thickness)  # 在畫布上繪製頂部文字。

    # 合併圖片並添加文字
    current_x = 0  # 初始化當前 x 座標（用於水平排列圖像）。
    for i, (img, text) in enumerate(zip(images, texts[1:-1])):  # 迭代圖像和對應的中間文字（排除頂部和底部文字）。
        # 確保圖片是 3 通道的
        if len(img.shape) == 2:  # 檢查圖像是否為灰階（2 維陣列）。
            img = cv2.cvtColor(img, cv2.COLOR_GRAY2BGR)  # 將灰階圖像轉為三通道 BGR 格式。

        # 將圖片放到新畫布上（注意要考慮頂部padding）
        h, w = img.shape[:2]  # 獲取圖像的高度和寬度。
        combined_image[top_padding:top_padding+h, current_x:current_x+w] = img  # 將圖像複製到畫布的指定區域（考慮頂部間距）。

        # 計算圖片下方文字位置
        text_size = cv2.getTextSize(text, font, font_scale, thickness)[0]  # 計算文字尺寸。
        text_x = current_x + (w - text_size[0]) // 2  # 計算文字的 x 座標（圖像下方置中）。
        text_y = top_padding + h - 20  # 計算文字的 y 座標（圖像下方 20 像素處）。

        # 添加圖片文字
        cv2.putText(combined_image, text, (text_x, text_y), 
                    font, font_scale, font_color, thickness)  # 在圖像下方繪製文字。

        current_x += w  # 更新 x 座標，移動到下一張圖像的起始位置。

    # 添加底部文字
    bottom_text = texts[-1]  # 獲取最後一個文字作為底部文字。
    text_size = cv2.getTextSize(bottom_text, font, font_scale, thickness)[0]  # 計算底部文字的尺寸。
    text_x = (total_width - text_size[0]) // 2  # 計算底部文字的 x 座標（水平置中）。
    text_y = max_height + top_padding + bottom_padding - 20  # 計算底部文字的 y 座標（底部空間內置中）。

    cv2.putText(combined_image, bottom_text, (text_x, text_y), 
                font, font_scale, font_color, thickness)  # 在畫布上繪製底部文字。

    # 如果提供輸出路徑，就儲存圖片
    if output_path:  # 檢查是否提供了輸出路徑。
        cv2.imwrite(output_path, combined_image)  # 將合併後的圖像保存到指定路徑。

    return combined_image  # 返回合併後的圖像（NumPy 陣列）。