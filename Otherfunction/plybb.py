# 主要目的：此程式碼（plybb.py）提供了一組工具函數，用於處理 PLY 格式的 3D 模型檔案，提取頂點數據、計算邊界框、質心，以及將灰階值映射到深度值。它是牙科 3D 模型重建流程的輔助模組，與 `DentalModelReconstructor` 等模組結合，支援從灰階圖像和 3D 模型生成點雲和網格。程式碼包含一個被註解掉的階梯式深度映射函數，適用於特殊場景。

import numpy as np  # 導入 NumPy 庫，用於數值運算和陣列處理。
from plyfile import PlyData  # 導入 PlyData 類，用於讀取 PLY 格式檔案。

def get_bounding_box(vertices):  # 定義計算頂點邊界框的函數。
    """
    計算頂點集的軸對齊邊界框（AABB）。

    參數:
        vertices: NumPy 陣列，形狀為 (N, 3)，表示 3D 頂點坐標 (x, y, z)。

    返回:
        元組 (xmin, xmax, ymin, ymax, zmin, zmax)，表示邊界框的範圍。
    """
    return (np.min(vertices[:, 0]), np.max(vertices[:, 0]),  # X 軸最小值和最大值
            np.min(vertices[:, 1]), np.max(vertices[:, 1]),  # Y 軸最小值和最大值
            np.min(vertices[:, 2]), np.max(vertices[:, 2]))  # Z 軸最小值和最大值

def read_ply(file_path):  # 定義讀取 PLY 檔案的函數。
    """
    讀取 PLY 檔案並提取頂點數據。

    參數:
        file_path: 字串，PLY 檔案的路徑。

    返回:
        NumPy 陣列，形狀為 (N, 3)，表示頂點的 x, y, z 坐標。
    """
    ply_data = PlyData.read(file_path)  # 讀取 PLY 檔案。
    vertices = np.vstack([ply_data['vertex']['x'],  # 提取 X 坐標
                          ply_data['vertex']['y'],  # 提取 Y 坐標
                          ply_data['vertex']['z']]).T  # 提取 Z 坐標並組成 (N, 3) 陣列
    return vertices  # 返回頂點陣列。

def get_depth_from_gray_value(gray_value, depth_max, depth_min, min_z, max_z):  # 定義灰階值到深度值的映射函數。
    """
    將灰階值線性映射到 3D 模型的 Z 軸深度範圍。

    參數:
        gray_value: 浮點數，輸入的灰階值（通常為 0-255）。
        depth_max: 浮點數，灰階值的最大值（例如 255）。
        depth_min: 浮點數，灰階值的最小值（例如 0）。
        min_z: 浮點數，Z 軸的最小值（模型空間）。
        max_z: 浮點數，Z 軸的最大值（模型空間）。

    返回:
        浮點數，映射後的 Z 坐標。
    """
    depth_scale = (depth_max - depth_min) / (max_z - min_z)  # 計算灰階到深度的縮放比例。
    z = (gray_value / depth_scale) + min_z  # 將灰階值映射到 Z 軸範圍。
    return z  # 返回映射後的 Z 值。

def get_centroid(vertices):  # 定義計算頂點質心的函數。
    """
    計算頂點集的質心（幾何中心）。

    參數:
        vertices: NumPy 陣列，形狀為 (N, 3)，表示 3D 頂點坐標 (x, y, z)。

    返回:
        NumPy 陣列，形狀為 (3,)，表示質心的 x, y, z 坐標。
    """
    return np.mean(vertices, axis=0)  # 計算所有頂點的平均坐標。

# def get_step_depth(gray_value, max_gray, min_gray, min_z, max_z, steps=3):
#     """
#     根據灰階值分段重建深度，適用於樓梯結構。
#
#     參數:
#         gray_value: 浮點數，輸入的灰階值。
#         max_gray: 浮點數，灰階值的最大值。
#         min_gray: 浮點數，灰階值的最小值。
#         min_z: 浮點數，Z 軸的最小值。
#         max_z: 浮點數，Z 軸的最大值。
#         steps: 整數，分段數量（預設為 3）。
#
#     返回:
#         浮點數，分段映射後的 Z 坐標。
#     """
#     step_size = (max_gray - min_gray) / steps  # 計算每個灰階段的大小。
#     depth_step = (max_z - min_z) / steps  # 計算每個深度段的大小。
#     # 將灰階分成多個深度階段
#     step_index = int((gray_value - min_gray) // step_size)  # 計算灰階值所在的段索引。
#     step_index = max(0, min(step_index, steps - 1))  # 限制索引在有效範圍內。
#     return min_z + step_index * depth_step  # 返回對應的深度值。