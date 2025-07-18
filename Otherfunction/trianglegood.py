# 主要目的：此程式碼定義了 `DentalModelReconstructor` 類，用於從 2D 灰階圖像和 3D 模型檔案（支援 PLY、STL、OBJ 格式）重建牙科 3D 模型，生成 STL 格式的點雲和網格。它使用 VTK 處理 3D 模型，結合灰階圖像生成點雲，支援咬合面（0°）、舌側（90°）和頰側（-90°）視角，並反轉網格法向量以確保正確朝向，適用於牙科模型的 AI 修復流程。相較於前一版本，此程式碼簡化了點雲生成邏輯，移除 OBB 對齊功能，直接使用模型的原始邊界框，並優化旋轉矩陣計算。

from .plybb import get_depth_from_gray_value  # 導入自定義函數，用於將灰階值或像素坐標映射到指定範圍的深度值。
import numpy as np  # 導入 NumPy 庫，用於數值運算和陣列處理。
from stl import mesh  # 導入 mesh 模組，用於處理和保存 STL 檔案。
from PIL import Image  # 導入 PIL 庫，用於處理 2D 圖像。
import vtk  # 導入 VTK 庫，用於 3D 模型處理和視覺化。
import os  # 導入 os 模組，用於檔案路徑操作。

class DentalModelReconstructor:
    def __init__(self, image_path, ply_path, stl_output_path):  # 初始化方法，接收圖像路徑、3D 模型路徑和輸出 STL 路徑。
        self.image_path = image_path  # 儲存灰階圖像路徑。
        self.ply_path = ply_path  # 儲存 3D 模型檔案路徑（支援 PLY、STL、OBJ）。
        self.stl_output_path = stl_output_path  # 儲存輸出的 STL 檔案路徑。
        self.image = None  # 初始化圖像物件。
        self.vertices = None  # 初始化頂點數據（未使用，可能是遺留變數）。
        self.bounds = None  # 初始化邊界框數據（未使用，可能是遺留變數）。

    def preprocess_image(self):  # 預處理灰階圖像。
        """增強圖像預處理，專門針對牙齒模型特徵"""
        self.image = Image.open(self.image_path).convert('L')  # 讀取圖像並轉為灰階（單通道）。

    def generate_point_cloud(self, angle=0):  # 生成點雲數據。
        """
        生成點雲資料，根據角度選擇視角。
        
        參數:
        - angle (int): 旋轉角度，0 表示咬合面，90 表示舌側，-90 表示頰側。

        回傳:
        - np.array: 生成的點雲座標陣列
        """
        vertices_list = []  # 初始化點雲列表。
        image = self.image  # 獲取預處理的灰階圖像。
        width, height = image.size  # 獲取圖像尺寸（寬、高）。
        min_x_value, max_x_value = width, 0  # 初始化圖像 X 軸範圍（非零像素）。
        max_value, min_value = 0, 255  # 初始化圖像灰階值範圍。

        # 計算圖片中非零像素的 X 範圍和灰階值範圍
        for y in range(height):  # 迭代圖像行。
            for x in range(width):  # 迭代圖像列。
                pixel_value = image.getpixel((x, y))  # 獲取像素灰階值。
                max_value = max(max_value, pixel_value)  # 更新最大灰階值。
                min_value = min(min_value, pixel_value)  # 更新最小灰階值。
                if pixel_value != 0:  # 如果像素非背景。
                    min_x_value = min(min_x_value, x)  # 更新 X 軸最小值。
                    max_x_value = max(max_x_value, x)  # 更新 X 軸最大值。

        # 根據檔案副檔名選擇合適的讀取器
        file_extension = os.path.splitext(self.ply_path)[1].lower()  # 獲取檔案副檔名。
        if file_extension == '.ply':  # 如果是 PLY 檔案。
            reader = vtk.vtkPLYReader()
        elif file_extension == '.stl':  # 如果是 STL 檔案。
            reader = vtk.vtkSTLReader()
        elif file_extension == '.obj':  # 如果是 OBJ 檔案。
            reader = vtk.vtkOBJReader()
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Supported formats are .ply, .stl, .obj")

        # 讀取檔案並提取頂點
        reader.SetFileName(self.ply_path)  # 設置輸入檔案路徑。
        reader.Update()  # 讀取檔案。
        polydata = reader.GetOutput()  # 獲取 PolyData。
        points = polydata.GetPoints()  # 獲取點數據。
        vertices = np.array([points.GetPoint(i) for i in range(points.GetNumberOfPoints())])  # 轉為 NumPy 陣列。

        # 根據角度進行旋轉
        if angle != 0:  # 如果需要舌側（90°）或頰側（-90°）視角。
            centroid = np.mean(vertices, axis=0)  # 計算點雲質心。
            vertices -= centroid  # 平移到原點。

            # 定義旋轉矩陣（沿 Y 軸旋轉）
            if angle == 90:  # 舌側視角（順時針 90 度）。
                rotation_matrix = np.array([[0, 0, 1], [0, 1, 0], [-1, 0, 0]])  # X->Z, Z->-X
            elif angle == -90:  # 頰側視角（逆時針 90 度）。
                rotation_matrix = np.array([[0, 0, -1], [0, 1, 0], [1, 0, 0]])  # X->-Z, Z->X

            vertices = vertices @ rotation_matrix.T  # 應用旋轉矩陣。
            vertices += centroid  # 平移回原始位置。

        # 從旋轉後的 vertices 計算邊界框
        min_x, max_x = np.min(vertices[:, 0]), np.max(vertices[:, 0])  # X 軸邊界。
        min_y, max_y = np.min(vertices[:, 1]), np.max(vertices[:, 1])  # Y 軸邊界。
        min_z, max_z = np.min(vertices[:, 2]), np.max(vertices[:, 2])  # Z 軸邊界。

        # 如果不是咬合面視角，壓縮 Z 軸範圍
        if angle != 0:  # 舌側或頰側視角。
            min_z = max_z - (max_z - min_z) * 0.5  # 取上半部分 Z 軸範圍。

        # 生成點雲
        for y in range(height - 1, -1, -1):  # 從下到上迭代圖像（Y 軸翻轉）。
            for x in range(width - 1, -1, -1):  # 從右到左迭代圖像（X 軸翻轉）。
                gray_value = image.getpixel((x, y))  # 獲取像素灰階值。
                new_x = get_depth_from_gray_value(x, max_x_value, min_x_value, min_x, max_x)  # 將 X 映射到模型範圍。
                new_y = get_depth_from_gray_value(height - y - 1, 255, 0, min_y, max_y)  # 將 Y 映射到模型範圍。
                new_z = get_depth_from_gray_value(gray_value, max_value, min_value, min_z, max_z)  # 將灰階映射到 Z。
                vertices_list.append([new_x, new_y, new_z])  # 添加點到點雲列表。

        return np.array(vertices_list)  # 返回點雲陣列。

    def generate_mesh(self, points):  # 生成三角形網格。
        """生成三角形網格，並反轉法向量方向"""
        height, width = int(np.sqrt(len(points))), int(np.sqrt(len(points)))  # 假設點雲為方形網格。
        faces = []  # 初始化三角形面列表。

        for y in range(height - 1):  # 迭代網格行。
            for x in range(width - 1):  # 迭代網格列。
                v0 = y * width + x  # 左下頂點索引。
                v1 = v0 + 1  # 右下頂點索引。
                v2 = (y + 1) * width + x  # 左上頂點索引。
                v3 = v2 + 1  # 右上頂點索引。

                d1 = np.linalg.norm(points[v0] - points[v3])  # 對角線 1 長度（v0-v3）。
                d2 = np.linalg.norm(points[v1] - points[v2])  # 對角線 2 長度（v1-v2）。

                if d1 < d2:  # 選擇較短對角線分割，逆序添加三角形以反轉法向量。
                    faces.extend([[v0, v3, v1], [v0, v2, v3]])
                else:
                    faces.extend([[v0, v2, v1], [v1, v2, v3]])

        min_z_depth = np.min([point[2] for point in points])  # 獲取點雲的最小 Z 值。
        new_faces = []  # 初始化過濾後的面列表。
        for face in faces:  # 迭代三角形面。
            triangle_points = [points[idx] for idx in face]  # 獲取三角形頂點。
            z_values = [point[2] for point in triangle_points]  # 獲取 Z 坐標。
            x_values = [point[0] for point in triangle_points]  # 獲取 X 坐標。
            y_values = [point[1] for point in triangle_points]  # 獲取 Y 坐標。

            skip_triangle = (
                sum(z == min_z_depth for z in z_values) == 3 or  # 如果三角形完全平坦（背景）。
                min(x_values) == max(x_values) or  # 如果 X 坐標無變化。
                min(y_values) == max(y_values)  # 如果 Y 坐標無變化。
            )

            if not skip_triangle:  # 如果三角形有效，保留。
                new_faces.append(face)

        mesh_data = mesh.Mesh(np.zeros(len(new_faces), dtype=mesh.Mesh.dtype))  # 創建 STL 網格。
        for i, face in enumerate(new_faces):  # 迭代有效三角形。
            for j in range(3):  # 設置三角形頂點。
                mesh_data.vectors[i][j] = points[face[j]]

            normal = np.cross(
                mesh_data.vectors[i][1] - mesh_data.vectors[i][0],
                mesh_data.vectors[i][2] - mesh_data.vectors[i][0]
            )  # 計算三角形法向量。
            mesh_data.normals[i] = -normal / np.linalg.norm(normal)  # 反轉法向量並歸一化。

        mesh_data.save(self.stl_output_path)  # 保存 STL 檔案。

    def reconstruct(self, angle=0):  # 執行完整重建流程。
        """執行完整的重建過程"""
        self.preprocess_image()  # 預處理圖像。
        points = self.generate_point_cloud(angle)  # 生成點雲。
        self.generate_mesh(points)  # 生成網格並保存。