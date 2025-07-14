# 主要目的：此程式碼使用 OpenCV (cv2) 處理深度圖像，旨在清除牙冠深度圖中的雜訊。它通過輪廓檢測、邊緣點尋找和紅線繪製，識別牙冠的邊界，並根據邊界進行濾波，最終生成清除雜訊後的深度圖像，儲存到指定資料夾。

import cv2  # 導入 OpenCV 庫，用於圖像處理和電腦視覺任務。
import numpy as np  # 導入 NumPy 庫，用於數值計算和陣列操作。
import os  # 導入 os 模組，用於處理文件路徑和資料夾操作。

# ======== 自訂參數 ========
depth_map_dir = 'D:/Weekly_Report/Thesis_Weekly_Report/paper/paper_Implementation/pyqt5/toKMU/AIoutput/orignal'  # 原始深度圖像的輸入資料夾路徑。
depth_map2_dir = 'D:/Weekly_Report/Thesis_Weekly_Report/paper/paper_Implementation/pyqt5/toKMU/AIoutput/ai'  # AI 處理後的深度圖像資料夾路徑。
final_output_dir = 'D:/Weekly_Report/Thesis_Weekly_Report/paper/paper_Implementation/pyqt5/toKMU/AIoutput/test'  # 濾波後圖像的輸出資料夾路徑。

# 建立輸出資料夾
os.makedirs(final_output_dir, exist_ok=True)  # 創建最終輸出資料夾，若已存在則不報錯。

# ======== 函式定義 ========
def draw_nearest_red_line(image, green_point, red_points):  # 定義函式，用於在圖像上繪製從綠色點到最近紅色點的紅線。
    distances = np.linalg.norm(red_points - np.array(green_point), axis=1)  # 計算綠色點到所有紅色點的歐氏距離。
    nearest_red = red_points[np.argmin(distances)]  # 找到距離綠色點最近的紅色點。
    cv2.line(image, tuple(green_point), tuple(nearest_red), (0, 0, 255), 1)  # 在圖像上繪製紅色線條（BGR 格式，紅色為 (0, 0, 255)）。

def find_edge_point_left(image, x, y):  # 定義函式，尋找指定點左邊的邊緣點（像素值 < 10）。
    for i in range(x, -1, -1):  # 從指定 x 座標向左遍歷。
        if image[y, i] < 10:  # 如果找到像素值小於 10 的點（邊緣點）。
            return (i, y)  # 返回該點的座標。
    return (x, y)  # 如果未找到邊緣點，返回原始座標。

def find_edge_point_right(image, x, y):  # 定義函式，尋找指定點右邊的邊緣點（像素值 < 10）。
    for i in range(x, image.shape[1]):  # 從指定 x 座標向右遍歷，直到圖像寬度邊界。
        if image[y, i] < 10:  # 如果找到像素值小於 10 的點（邊緣點）。
            return (i, y)  # 返回該點的座標。
    return (x, y)  # 如果未找到邊緣點，返回原始座標。

# ======== 第一階段：畫紅線到 edge_output_dir ========
for filename in os.listdir(depth_map_dir):  # 遍歷原始深度圖像資料夾中的所有文件。
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):  # 檢查文件是否為圖像格式（.png, .jpg, .jpeg）。
        continue  # 如果不是圖像格式，跳過該文件。

    base_name = os.path.splitext(filename)[0]  # 獲取文件名（不含擴展名）。
    path1 = os.path.join(depth_map_dir, filename)  # 構建原始深度圖像的完整路徑。
    path2 = os.path.join(depth_map2_dir, base_name + '.png')  # 構建對應 AI 處理圖像的路徑（假設為 .png 格式）。

    if not os.path.exists(path2):  # 檢查 AI 處理圖像是否存在。
        print(f"[警告] 找不到對應的 AI 圖像: {path2}")  # 如果不存在，打印警告訊息並跳過。
        continue

    depth_map = cv2.imread(path1, cv2.IMREAD_GRAYSCALE)  # 讀取原始深度圖像為灰階圖。
    depth_map2 = cv2.imread(path2, cv2.IMREAD_GRAYSCALE)  # 讀取 AI 處理後的深度圖像為灰階圖。
    height, width = depth_map2.shape  # 獲取 AI 處理圖像的高度和寬度。
    _, binary = cv2.threshold(depth_map, 0, 255, cv2.THRESH_BINARY)  # 對原始深度圖進行二值化處理，閾值為 0，生成 0 和 255 的二值圖。
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)  # 在二值圖中尋找外部輪廓。
    output_image = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)  # 將二值圖轉換為三通道 BGR 彩色圖，以便繪製彩色線條。

    if len(contours) >= 3:  # 檢查是否至少找到 3 個輪廓（假設需要處理多個輪廓）。
        cv2.drawContours(output_image, [contours[0]], 0, (0, 0, 255), 1)  # 在輸出圖像上繪製第一個輪廓（紅色線）。
        cv2.drawContours(output_image, [contours[2]], 0, (0, 0, 255), 1)  # 在輸出圖像上繪製第三個輪廓（紅色線）。

        contour2 = contours[2][:, 0, :]  # 提取第三個輪廓的點座標（去除多餘維度）。
        max_y = np.max(contour2[:, 1])  # 找到第三個輪廓的最大 y 座標（底部）。
        bottom_points = contour2[contour2[:, 1] == max_y]  # 獲取底部點（y 座標等於最大 y 的點）。
        leftmost_bottom = bottom_points[np.argmin(bottom_points[:, 0])]  # 找到底部點中最左邊的點。
        rightmost_bottom = bottom_points[np.argmax(bottom_points[:, 0])]  # 找到底部點中最右邊的點。

        contour0 = contours[0][:, 0, :]  # 提取第一個輪廓的點座標。
        min_y = np.min(contour0[:, 1])  # 找到第一個輪廓的最小 y 座標（頂部）。
        top_points = contour0[contour0[:, 1] == min_y]  # 獲取頂部點（y 座標等於最小 y 的點）。
        leftmost_top = top_points[np.argmin(top_points[:, 0])]  # 找到頂部點中最左邊的點。
        rightmost_top = top_points[np.argmax(top_points[:, 0])]  # 找到頂部點中最右邊的點。

        # 更新座標
        leftmost_bottom = find_edge_point_left(depth_map2, *leftmost_bottom)  # 尋找底部左邊點的邊緣點。
        rightmost_bottom = find_edge_point_right(depth_map2, *rightmost_bottom)  # 尋找底部右邊點的邊緣點。
        leftmost_top = find_edge_point_left(depth_map2, *leftmost_top)  # 尋找頂部左邊點的邊緣點。
        rightmost_top = find_edge_point_right(depth_map2, *rightmost_top)  # 尋找頂部右邊點的邊緣點。

        red_points = np.concatenate((contour0, contour2), axis=0)  # 合併第一和第三輪廓的點，作為紅色點集合。
        draw_nearest_red_line(output_image, leftmost_bottom, red_points)  # 繪製從底部左邊點到最近紅色點的紅線。
        draw_nearest_red_line(output_image, rightmost_bottom, red_points)  # 繪製從底部右邊點到最近紅色點的紅線。
        draw_nearest_red_line(output_image, leftmost_top, red_points)  # 繪製從頂部左邊點到最近紅色點的紅線。
        draw_nearest_red_line(output_image, rightmost_top, red_points)  # 繪製從頂部右邊點到最近紅色點的紅線。

        # 繪製左線
        x, y = leftmost_bottom  # 獲取底部左邊點的座標。
        target_y = leftmost_top[1]  # 設置目標 y 座標為頂部左邊點的 y。
        while y <= target_y:  # 從底部點向上遍歷到頂部點。
            if depth_map2[y, x] >= 10:  # 如果當前點像素值 >= 10（非邊緣）。
                for i in range(x, -1, -1):  # 向左尋找像素值 < 120 的點。
                    if depth_map2[y, i] < 120:  # 找到邊緣點。
                        cv2.circle(output_image, (i, y), 0, (0, 0, 255), -1)  # 在該點繪製紅色像素。
                        break
            else:  # 如果當前點像素值 < 10（邊緣）。
                for i in range(x, width):  # 向右尋找像素值 > 10 的點。
                    if depth_map2[y, i] > 10:  # 找到非邊緣點。
                        cv2.circle(output_image, (i, y), 0, (0, 0, 255), -1)  # 在該點繪製紅色像素。
                        break
            y += 1  # 向上移動到下一行。

        # 繪製右線
        x, y = rightmost_bottom  # 獲取底部右邊點的座標。
        target_y = rightmost_top[1]  # 設置目標 y 座標為頂部右邊點的 y。
        while y <= target_y:  # 從底部點向上遍歷到頂部點。
            if depth_map2[y, x] <= 10:  # 如果當前點像素值 <= 10（邊緣）。
                for i in range(x, -1, -1):  # 向左尋找像素值 > 10 的點。
                    if depth_map2[y, i] > 10:  # 找到非邊緣點。
                        cv2.circle(output_image, (i, y), 0, (0, 0, 255), -1)  # 在該點繪製紅色像素。
                        break
            else:  # 如果當前點像素值 > 10（非邊緣）。
                for i in range(x, width):  # 向右尋找像素值 < 10 的點。
                    if depth_map2[y, i] < 10:  # 找到邊緣點。
                        cv2.circle(output_image, (i, y), 0, (0, 0, 255), -1)  # 在該點繪製紅色像素。
                        break
            y += 1  # 向上移動到下一行。
    else:  # 如果輪廓數量少於 3。
        print(f"[警告] {filename} 只找到 {len(contours)} 個輪廓，跳過。")  # 打印警告訊息並跳過該圖像。
        continue

    # 白底變黑
    white_mask = np.all(output_image == [255, 255, 255], axis=-1)  # 創建白色像素的遮罩（RGB 全為 255）。
    output_image[white_mask] = [0, 0, 0]  # 將白色像素設為黑色。

    border_image = output_image.copy()  # 複製輸出圖像作為邊界圖像。

    # === 濾波階段 ===
    output_filtered = np.zeros_like(depth_map2)  # 創建與 depth_map2 同尺寸的零陣列，用於儲存濾波後的圖像。
    for y in range(height):  # 遍歷圖像的每一行。
        red_pixels = np.where(
            (border_image[y, :, 0] == 0) &
            (border_image[y, :, 1] == 0) &
            (border_image[y, :, 2] == 255)
        )[0]  # 找到當前行中紅色像素（B=0, G=0, R=255）的 x 座標。

        if red_pixels.size == 0:  # 如果當前行沒有紅色像素。
            continue  # 跳過該行。

        start_x = int(np.min(red_pixels))  # 找到紅色像素的最小 x 座標（左邊界）。
        end_x = int(np.max(red_pixels))  # 找到紅色像素的最大 x 座標（右邊界）。
        output_filtered[y, start_x:end_x+1] = depth_map2[y, start_x:end_x+1]  # 將原始深度圖像的對應區域複製到濾波圖像。

    output_path = os.path.join(final_output_dir, filename)  # 構建濾波圖像的輸出路徑。
    cv2.imwrite(output_path, output_filtered)  # 儲存濾波後的圖像。
    print(f"[完成] 已儲存濾波圖：{output_path}")  # 打印完成訊息。