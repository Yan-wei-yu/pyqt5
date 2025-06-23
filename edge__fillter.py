import cv2
import numpy as np
import os

# ======== 自訂參數 ========
depth_map_dir = 'D:/Weekly_Report/Thesis_Weekly_Report/paper/paper_Implementation/pyqt5/toKMU/AIoutput/orignal'
depth_map2_dir = 'D:/Weekly_Report/Thesis_Weekly_Report/paper/paper_Implementation/pyqt5/toKMU/AIoutput/ai'
final_output_dir = 'D:/Weekly_Report/Thesis_Weekly_Report/paper/paper_Implementation/pyqt5/toKMU/AIoutput/test'

# 建立輸出資料夾
# os.makedirs(edge_output_dir, exist_ok=True)
os.makedirs(final_output_dir, exist_ok=True)

# ======== 函式定義 ========
def draw_nearest_red_line(image, green_point, red_points):
    distances = np.linalg.norm(red_points - np.array(green_point), axis=1)
    nearest_red = red_points[np.argmin(distances)]
    cv2.line(image, tuple(green_point), tuple(nearest_red), (0, 0, 255), 1)

def find_edge_point_left(image, x, y):
    for i in range(x, -1, -1):
        if image[y, i] < 10:
            return (i, y)
    return (x, y)

def find_edge_point_right(image, x, y):
    for i in range(x, image.shape[1]):
        if image[y, i] < 10:
            return (i, y)
    return (x, y)

# ======== 第一階段：畫紅線到 edge_output_dir ========
for filename in os.listdir(depth_map_dir):
    if not filename.lower().endswith(('.png', '.jpg', '.jpeg')):
        continue

    base_name = os.path.splitext(filename)[0]
    path1 = os.path.join(depth_map_dir, filename)
    path2 = os.path.join(depth_map2_dir, base_name + '.png')

    if not os.path.exists(path2):
        print(f"[警告] 找不到對應的 AI 圖像: {path2}")
        continue

    depth_map = cv2.imread(path1, cv2.IMREAD_GRAYSCALE)
    depth_map2 = cv2.imread(path2, cv2.IMREAD_GRAYSCALE)
    height, width = depth_map2.shape
    # 這行是 二值化處理，將 depth_map（灰階圖像）轉換為只有 0 和 255 的圖像：
    #  提取輪廓，在二值圖中尋找物件邊緣：
    # 這行是將單通道灰階圖轉換成 三通道 BGR 彩色圖：
    _, binary = cv2.threshold(depth_map, 0, 255, cv2.THRESH_BINARY)
    contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    output_image = cv2.cvtColor(binary, cv2.COLOR_GRAY2BGR)

    if len(contours) >= 3:
        cv2.drawContours(output_image, [contours[0]], 0, (0, 0, 255), 1)
        cv2.drawContours(output_image, [contours[2]], 0, (0, 0, 255), 1)

        contour2 = contours[2][:, 0, :]
        max_y = np.max(contour2[:, 1])
        bottom_points = contour2[contour2[:, 1] == max_y]
        leftmost_bottom = bottom_points[np.argmin(bottom_points[:, 0])]
        rightmost_bottom = bottom_points[np.argmax(bottom_points[:, 0])]

        contour0 = contours[0][:, 0, :]
        min_y = np.min(contour0[:, 1])
        top_points = contour0[contour0[:, 1] == min_y]
        leftmost_top = top_points[np.argmin(top_points[:, 0])]
        rightmost_top = top_points[np.argmax(top_points[:, 0])]

        # 更新座標
        leftmost_bottom = find_edge_point_left(depth_map2, *leftmost_bottom)
        rightmost_bottom = find_edge_point_right(depth_map2, *rightmost_bottom)
        leftmost_top = find_edge_point_left(depth_map2, *leftmost_top)
        rightmost_top = find_edge_point_right(depth_map2, *rightmost_top)

        red_points = np.concatenate((contour0, contour2), axis=0)
        draw_nearest_red_line(output_image, leftmost_bottom, red_points)
        draw_nearest_red_line(output_image, rightmost_bottom, red_points)
        draw_nearest_red_line(output_image, leftmost_top, red_points)
        draw_nearest_red_line(output_image, rightmost_top, red_points)

        # 繪製左線
        x, y = leftmost_bottom
        target_y = leftmost_top[1]
        while y <= target_y:
            if depth_map2[y, x] >= 10:
                for i in range(x, -1, -1):
                    if depth_map2[y, i] < 120:
                        cv2.circle(output_image, (i, y), 0, (0, 0, 255), -1)
                        break
            else:
                for i in range(x, width):
                    if depth_map2[y, i] > 10:
                        cv2.circle(output_image, (i, y), 0, (0, 0, 255), -1)
                        break
            y += 1

        # 繪製右線
        x, y = rightmost_bottom
        target_y = rightmost_top[1]
        while y <= target_y:
            if depth_map2[y, x] <= 10:
                for i in range(x, -1, -1):
                    if depth_map2[y, i] > 10:
                        cv2.circle(output_image, (i, y), 0, (0, 0, 255), -1)
                        break
            else:
                for i in range(x, width):
                    if depth_map2[y, i] < 10:
                        cv2.circle(output_image, (i, y), 0, (0, 0, 255), -1)
                        break
            y += 1
    else:
        print(f"[警告] {filename} 只找到 {len(contours)} 個輪廓，跳過。")
        continue

    # 白底變黑
    white_mask = np.all(output_image == [255, 255, 255], axis=-1)
    output_image[white_mask] = [0, 0, 0]

    # edge_output_path = os.path.join(edge_output_dir, base_name + '.png')
    # cv2.imwrite(edge_output_path, output_image)
    # print(f"[完成] 已儲存紅線圖：{edge_output_path}")

# ======== 第二階段：根據紅線篩選 AI 圖像區域並輸出 ========
# for filename in os.listdir(depth_map2_dir):
#     if not filename.lower().endswith('.png'):
#         continue

#     ai_path = os.path.join(depth_map2_dir, filename)
#     border_path = os.path.join(edge_output_dir, filename)

#     ai_image = cv2.imread(ai_path, cv2.IMREAD_GRAYSCALE)
#     border_image = cv2.imread(border_path)

#     if ai_image is None or border_image is None:
#         print(f"[跳過] 無法讀取：{filename}")
#         continue

#     height, width = ai_image.shape
#     output_image = np.zeros_like(ai_image)

#     for y in range(height):
#         red_pixels = np.where(
#             (border_image[y, :, 0] == 0) &
#             (border_image[y, :, 1] == 0) &
#             (border_image[y, :, 2] == 255)
#         )[0]

#         if red_pixels.size == 0:
#             continue

#         start_x = int(np.min(red_pixels))
#         end_x = int(np.max(red_pixels))
#         output_image[y, start_x:end_x+1] = ai_image[y, start_x:end_x+1]

#     output_path = os.path.join(final_output_dir, filename)
#     cv2.imwrite(output_path, output_image)
#     print(f"[完成] 已儲存濾波圖：{output_path}")
    border_image = output_image.copy()

    # === 濾波階段 ===
    output_filtered = np.zeros_like(depth_map2)
    for y in range(height):
        red_pixels = np.where(
            (border_image[y, :, 0] == 0) &
            (border_image[y, :, 1] == 0) &
            (border_image[y, :, 2] == 255)
        )[0]

        if red_pixels.size == 0:
            continue

        start_x = int(np.min(red_pixels))
        end_x = int(np.max(red_pixels))
        output_filtered[y, start_x:end_x+1] = depth_map2[y, start_x:end_x+1]

    output_path = os.path.join(final_output_dir, filename)
    cv2.imwrite(output_path, output_filtered)
    print(f"[完成] 已儲存濾波圖：{output_path}")