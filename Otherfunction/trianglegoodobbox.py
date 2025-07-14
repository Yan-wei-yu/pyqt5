# 主要目的：此程式碼定義了 `DentalModelReconstructor` 類，用於從 2D 灰階圖像和 3D 模型檔案（支援 PLY、STL、OBJ 格式）重建牙科 3D 模型，生成 STL 格式的點雲和網格。它使用 VTK 進行 3D 處理，結合灰階圖像生成點雲，並支援 OBB 對齊、視角旋轉和法向量反轉，適用於牙科模型的 AI 修復流程。此外，還提供 `smooth_stl` 函數對 STL 模型進行平滑處理。

from .plybb import get_depth_from_gray_value  # 導入自定義函數，用於將灰階值映射到深度值。
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
        self.vertices = None  # 初始化頂點數據。
        self.bounds = None  # 初始化邊界框數據。

    def preprocess_image(self):  # 預處理灰階圖像。
        """增強圖像預處理，專門針對牙齒模型特徵"""
        self.image = Image.open(self.image_path).convert('L')  # 讀取圖像並轉為灰階（單通道）。
        img_array = np.array(self.image)  # 將圖像轉為 NumPy 陣列。
        self.image = Image.fromarray(img_array)  # 將陣列轉回 PIL 圖像（此步可簡化，僅用於一致性）。

    @staticmethod
    def compute_obb_aligned_bounds(polydata, upper_polydata=None, angle=None):  # 計算 OBB 對齊邊界框。
        """
        計算 OBB 的邊界並將傳入的polydata對齊到世界坐標軸，可選擇沿 Y 軸額外旋轉角度。
        
        參數:
        polydata: vtkPolyData 對象，表示輸入的 3D 資料
        upper_polydata: 可選的第二個 vtkPolyData 對象
        angle: 可選的旋轉角度（度），預設為 None
        
        返回:
        aligned_bounds: 對齊後的邊界框
        """
        if polydata.GetNumberOfPoints() == 0:  # 檢查輸入 PolyData 是否有點。
            raise ValueError("PLY 檔案中沒有點資料！")

        obb_tree = vtk.vtkOBBTree()  # 初始化 VTK OBB 樹，用於計算定向邊界框（OBB）。
        corner, max_vec, mid_vec, min_vec, size = [0.0]*3, [0.0]*3, [0.0]*3, [0.0]*3, [0.0]*3  # 初始化 OBB 參數。
        obb_tree.ComputeOBB(polydata, corner, max_vec, mid_vec, min_vec, size)  # 計算 OBB。

        corner = np.array(corner)  # 將 OBB 角點轉為 NumPy 陣列。
        max_vec = np.array(max_vec)  # 最大軸向量。
        mid_vec = np.array(mid_vec)  # 中間軸向量。
        min_vec = np.array(min_vec)  # 最小軸向量。

        obb_center = corner + (max_vec + mid_vec + min_vec) / 2.0  # 計算 OBB 中心。

        # 計算旋轉矯正矩陣
        sizes = np.array([np.linalg.norm(max_vec), np.linalg.norm(mid_vec), np.linalg.norm(min_vec)])  # 計算各軸長度。
        axis_order = np.argsort(sizes)[::-1]  # 按軸長從大到小排序。
        vectors = [max_vec, mid_vec, min_vec]  # 儲存 OBB 軸向量。

        V1 = vectors[axis_order[0]] / np.linalg.norm(vectors[axis_order[0]])  # 最長軸作為 Y 軸。
        V2 = vectors[axis_order[1]] / np.linalg.norm(vectors[axis_order[1]])  # 次長軸作為 X 軸。
        V3 = vectors[axis_order[2]] / np.linalg.norm(vectors[axis_order[2]])  # 最短軸作為 Z 軸。

        points = np.array(polydata.GetPoints().GetData())  # 獲取 PolyData 的點數據。
        top_point = points[np.argmax(points[:, 2])]  # 找到 Z 軸最大點。
        direction_to_top = top_point - obb_center  # 計算到頂點的方向向量。
        if np.dot(direction_to_top, V3) < 0:  # 如果 V3 方向與頂點相反。
            V3 = -V3  # 反轉 V3 方向。

        left_point = points[np.argmax(points[:, 0])]  # 找到 X 軸最大點。
        direction_to_left = left_point - obb_center  # 計算到左側點的方向向量。
        if np.dot(direction_to_left, V2) < 0:  # 如果 V2 指向右側。
            V2 = -V2  # 反轉 V2 方向。

        right_point = points[np.argmax(points[:, 1])]  # 找到 Y 軸最大點。
        direction_to_right = right_point - obb_center  # 計算到右側點的方向向量。
        if np.dot(direction_to_right, V1) < 0:  # 如果 V1 指向左側。
            V1 = -V1  # 反轉 V1 方向。

        E1 = np.array([1, 0, 0])  # 目標 X 軸（世界坐標）。
        E2 = np.array([0, 1, 0])  # 目標 Y 軸（世界坐標）。
        E3 = np.array([0, 0, 1])  # 目標 Z 軸（世界坐標）。

        A = np.column_stack((V3, V2, V1))  # 當前 OBB 基向量矩陣。
        B = np.column_stack((E3, E1, E2))  # 目標世界坐標基向量矩陣。
        rotation_matrix = B @ np.linalg.inv(A)  # 計算旋轉矩陣。
        points = np.array(polydata.GetPoints().GetData())# 獲取 PolyData 的點數據。
        points = points - obb_center  # 平移點到原點。
        aligned_points = (rotation_matrix @ points.T).T  # 應用旋轉。
        aligned_points = aligned_points + obb_center  # 平移回原始位置。

        new_points = vtk.vtkPoints()  # 創建新的 VTK 點集。
        new_points.SetData(np_to_vtk(aligned_points))  # 設置對齊後的點。
        polydata.SetPoints(new_points)  # 更新 PolyData 的點數據。

        if upper_polydata is not None:  # 如果提供了第二個 PolyData（例如上顎模型）。
            upper_points = np.array(upper_polydata.GetPoints().GetData())  # 獲取點數據。
            upper_points = upper_points - obb_center  # 平移到原點。
            aligned_upper_points = (rotation_matrix @ upper_points.T).T  # 應用旋轉。
            aligned_upper_points = aligned_upper_points + obb_center  # 平移回原始位置。
            new_upper_points = vtk.vtkPoints()  # 創建新的點集。
            new_upper_points.SetData(np_to_vtk(aligned_upper_points))  # 設置對齊後的點。
            upper_polydata.SetPoints(new_upper_points)  # 更新上顎 PolyData。

        if angle == 90 or angle == -90:  # 如果需要沿 Y 軸旋轉（舌側或頰側視角）。
            aligned_points = np.array(polydata.GetPoints().GetData())  # 獲取對齊後的點。
            aligned_center = np.mean(aligned_points, axis=0)  # 計算質心。
            theta = np.radians(angle)  # 將角度轉為弧度。
            cos_theta = np.cos(theta)  # 計算 cos(θ)。
            sin_theta = np.sin(theta)  # 計算 sin(θ)。
            rotation_y = np.array([
                [cos_theta, 0, sin_theta],
                [0, 1, 0],
                [-sin_theta, 0, cos_theta]
            ])  # 定義 Y 軸旋轉矩陣。
            points = np.array(polydata.GetPoints().GetData())  # 獲取當前點。
            points = points - aligned_center  # 平移到原點。
            rotated_points = (rotation_y @ points.T).T  # 應用旋轉。
            rotated_points = rotated_points + aligned_center  # 平移回原始位置。
            new_points = vtk.vtkPoints()  # 創建新的點集。
            new_points.SetData(np_to_vtk(rotated_points))  # 設置旋轉後的點。
            polydata.SetPoints(new_points)  # 更新 PolyData。

        aligned_bounds = polydata.GetBounds()  # 獲取對齊後的 AABB 邊界框。
        return aligned_bounds  # 返回邊界框 (xmin, xmax, ymin, ymax, zmin, zmax)。

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
        width, height = image.size  # 獲取圖像尺寸。
        min_x_value, max_x_value = width, 0  # 初始化圖像 X 軸範圍。

        file_extension = os.path.splitext(self.ply_path)[1].lower()  # 獲取檔案副檔名。
        if file_extension == '.ply':  # 如果是 PLY 檔案。
            reader = vtk.vtkPLYReader()
        elif file_extension == '.stl':  # 如果是 STL 檔案。
            reader = vtk.vtkSTLReader()
        elif file_extension == '.obj':  # 如果是 OBJ 檔案。
            reader = vtk.vtkOBJReader()
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Supported formats are .ply, .stl, .obj")
        reader.SetFileName(self.ply_path)  # 設置輸入檔案路徑。
        reader.Update()  # 讀取檔案。
        polydata = reader.GetOutput()  # 獲取 PolyData。

        bounds = self.compute_obb_aligned_bounds(polydata)  # 計算 OBB 對齊邊界框。

        points = polydata.GetPoints()  # 獲取 PolyData 的點數據。
        vertices = np.array([points.GetPoint(i) for i in range(points.GetNumberOfPoints())])  # 轉為 NumPy 陣列。

        if angle in (90, -90):  # 如果需要舌側或頰側視角。
            centroid = np.mean(vertices, axis=0)  # 計算質心。
            vertices -= centroid  # 平移到原點。
            theta = np.radians(angle)  # 將角度轉為弧度。
            rotation_y = np.array([
                [np.cos(theta), 0, np.sin(theta)],
                [0, 1, 0],
                [-np.sin(theta), 0, np.cos(theta)]
            ])  # 定義 Y 軸旋轉矩陣。
            vertices = vertices @ rotation_y.T  # 應用旋轉。
            vertices += centroid  # 平移回原始位置。
            new_pts = vtk.vtkPoints()  # 創建新的點集。
            new_pts.SetData(np_to_vtk(vertices))  # 設置旋轉後的點。
            polydata.SetPoints(new_pts)  # 更新 PolyData。
            bounds = polydata.GetBounds()  # 更新邊界框。

        min_x, max_x = bounds[0], bounds[1]  # X 軸邊界。
        min_y, max_y = bounds[2], bounds[3]  # Y 軸邊界。
        min_z, max_z = bounds[4], bounds[5]  # Z 軸邊界。

        if angle != 0:  # 如果不是咬合面視角，壓縮 Z 軸範圍。
            min_z = max_z - (max_z - min_z) * 0.5  # 取上半部分 Z 軸。

        max_value, min_value = 0, 255  # 初始化圖像灰階範圍。
        for y in range(height):  # 迭代圖像像素。
            for x in range(width):
                pixel_value = image.getpixel((x, y))  # 獲取像素灰階值。
                max_value = max(max_value, pixel_value)  # 更新最大灰階值。
                min_value = min(min_value, pixel_value)  # 更新最小灰階值。
                if pixel_value != 0:  # 如果像素非背景。
                    min_x_value = min(min_x_value, x)  # 更新 X 軸最小值。
                    max_x_value = max(max_x_value, x)  # 更新 X 軸最大值。

        for y in range(height - 1, -1, -1):  # 從下到上迭代圖像（Y 軸翻轉）。
            for x in range(width - 1, -1, -1):  # 從右到左迭代圖像（X 軸翻轉）。
                gray_value = image.getpixel((x, y))  # 獲取灰階值。
                new_x = get_depth_from_gray_value(x, max_x_value, min_x_value, min_x, max_x)  # 將 X 映射到模型範圍。
                new_y = get_depth_from_gray_value(height - y - 1, 255, 0, min_y, max_y)  # 將 Y 映射到模型範圍。
                new_z = get_depth_from_gray_value(gray_value, max_value, min_value, min_z, max_z)  # 將灰階映射到 Z。
                vertices_list.append([new_x, new_y, new_z])  # 添加點到點雲。

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

                d1 = np.linalg.norm(points[v0] - points[v3])  # 對角線 1 長度。
                d2 = np.linalg.norm(points[v1] - points[v2])  # 對角線 2 長度。

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

def np_to_vtk(np_array):  # 將 NumPy 陣列轉為 VTK 格式。
    """將 NumPy 陣列轉換為 VTK 格式"""
    vtk_array = vtk.vtkDoubleArray()  # 創建 VTK 雙精度陣列。
    vtk_array.SetNumberOfComponents(3)  # 設置為 3 分量（X, Y, Z）。
    vtk_array.SetNumberOfTuples(np_array.shape[0])  # 設置陣列大小。
    for i, point in enumerate(np_array):  # 迭代點數據。
        vtk_array.SetTuple3(i, point[0], point[1], point[2])  # 設置每個點的坐標。
    return vtk_array

def smooth_stl(input_stl_path, output_stl_path, iterations=20, relaxation_factor=0.2):  # 對 STL 檔案進行平滑處理。
    """對 STL 進行平滑處理"""
    reader = vtk.vtkSTLReader()  # 創建 STL 讀取器。
    reader.SetFileName(input_stl_path)  # 設置輸入檔案路徑。

    smoother = vtk.vtkSmoothPolyDataFilter()  # 創建平滑濾波器。
    smoother.SetInputConnection(reader.GetOutputPort())  # 設置輸入為 STL 讀取器輸出。
    smoother.SetNumberOfIterations(iterations)  # 設置平滑迭代次數（預設 20）。
    smoother.SetRelaxationFactor(relaxation_factor)  # 設置平滑強度（預設 0.2）。
    smoother.FeatureEdgeSmoothingOff()  # 關閉邊緣平滑，保留特徵邊。
    smoother.BoundarySmoothingOn()  # 啟用邊界平滑。
    smoother.Update()  # 更新濾波器。

    writer = vtk.vtkSTLWriter()  # 創建 STL 寫入器。
    writer.SetFileName(output_stl_path)  # 設置輸出檔案路徑。
    writer.SetInputConnection(smoother.GetOutputPort())  # 設置輸入為平滑濾波器輸出。
    writer.Write()  # 寫入 STL 檔案。
# reconstructor =DentalModelReconstructor("D:/Users/user/Desktop/weiyundontdelete/GANdata/pyqt/Aiobboutput/re_ai_data0119.png","D:/Users/user/Desktop/weiyundontdelete/GANdata/pyqt/Testdata/Prep/data0119.ply","D:/Users/user/Desktop/weiyundontdelete/GANdata/pyqt/Aiobboutput/re_ai_data0119.stl")
# reconstructor.reconstruct()
# smoothed_stl_path = "./ai_data0119_smooth.stl"
# smooth_stl("D:/Users/user/Desktop/weiyundontdelete/GANdata/pyqt/Aiobboutput/re_ai_data0119.stl", smoothed_stl_path)



