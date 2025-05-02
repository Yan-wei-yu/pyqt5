from .plybb import  get_depth_from_gray_value
import numpy as np
from stl import mesh
from PIL import Image
import vtk
import os


class DentalModelReconstructor:
    def __init__(self, image_path, ply_path, stl_output_path):
        self.image_path = image_path
        self.ply_path = ply_path
        self.stl_output_path = stl_output_path
        self.image = None
        self.vertices = None
        self.bounds = None
        
    def preprocess_image(self):
        """增強圖像預處理，專門針對牙齒模型特徵"""
        # 讀取並轉換為灰階
        self.image = Image.open(self.image_path).convert('L')
        img_array = np.array(self.image)
        
        self.image = Image.fromarray(img_array)
        
    @staticmethod
    def compute_obb_aligned_bounds(polydata, upper_polydata=None, angle=None):
        """
        計算 OBB 的邊界並將傳入的polydata對齊到世界坐標軸，可選擇沿 Y 軸額外旋轉角度。
        
        參數:
        polydata: vtkPolyData 對象，表示輸入的 3D 資料
        upper_polydata: 可選的第二個 vtkPolyData 對象
        angle: 可選的旋轉角度（度），預設為 None
        
        返回:
        aligned_bounds: 對齊後的邊界框
        """
        # 檢查輸入資料是否有點
        if polydata.GetNumberOfPoints() == 0:
            raise ValueError("PLY 檔案中沒有點資料！")

        # 初始化 vtkOBBTree 物件以計算 OBB
        obb_tree = vtk.vtkOBBTree()
        corner, max_vec, mid_vec, min_vec, size = [0.0]*3, [0.0]*3, [0.0]*3, [0.0]*3, [0.0]*3
        obb_tree.ComputeOBB(polydata, corner, max_vec, mid_vec, min_vec, size)

        # 轉換為 NumPy 陣列
        corner = np.array(corner)
        max_vec = np.array(max_vec)
        mid_vec = np.array(mid_vec)
        min_vec = np.array(min_vec)

        # 計算 OBB 中心
        obb_center = corner + (max_vec + mid_vec + min_vec) / 2.0

        # (1) 計算旋轉矯正矩陣
        # OBB 的主軸方向 (V1, V2, V3)
        # 根據軸長度排序
        sizes = np.array([np.linalg.norm(max_vec), np.linalg.norm(mid_vec), np.linalg.norm(min_vec)])
        axis_order = np.argsort(sizes)[::-1]  # 從大到小排序
        vectors = [max_vec, mid_vec, min_vec]

        # 動態分配軸
        V1 = vectors[axis_order[0]] / np.linalg.norm(vectors[axis_order[0]])  # 最長軸作為 Y
        V2 = vectors[axis_order[1]] / np.linalg.norm(vectors[axis_order[1]])  # 次長軸作為 X
        V3 = vectors[axis_order[2]] / np.linalg.norm(vectors[axis_order[2]])  # 最短軸作為 Z

        # 檢查 V3 方向並校正
        points = np.array(polydata.GetPoints().GetData())
        top_point = points[np.argmax(points[:, 2])]
        direction_to_top = top_point - obb_center
        if np.dot(direction_to_top, V3) < 0:
            V3 = -V3

        # 檢查 V2 方向並校正（新增）
        left_point = points[np.argmax(points[:, 0])]  # 找到 X 座標最大的點
        direction_to_left = left_point - obb_center
        if np.dot(direction_to_left, V2) < 0:  # 如果 V2 指向「右」
            V2 = -V2

        # 檢查 V1 方向並校正（新增）
        right_point = points[np.argmax(points[:, 1])]  # 找到 Y 座標最大的點
        direction_to_right = right_point - obb_center
        if np.dot(direction_to_right, V1) < 0:  # 如果 V1 指向「左」
            V1 = -V1

        # 目標標準基向量
        E1 = np.array([1, 0, 0])  # X 軸
        E2 = np.array([0, 1, 0])  # Y 軸
        E3 = np.array([0, 0, 1])  # Z 軸

        # 當前基向量矩陣 A (OBB 的原始基向量)
        A = np.column_stack((V3, V2, V1))  # V3, V2, V1

        # 目標基向量矩陣 B (將 V1 對齊到 Z 軸)
        B = np.column_stack((E3, E1, E2))  # X, Y, Z (V3 -> X, V2 -> Y, V1 -> Z)

        # 計算旋轉矩陣 R，使得 R * A = B
        rotation_matrix = B @ np.linalg.inv(A)

        # (2) 應用旋轉到模型
        points = np.array(polydata.GetPoints().GetData())
        points = points - obb_center  # 平移到原點
        aligned_points = (rotation_matrix @ points.T).T  # 應用旋轉
        aligned_points = aligned_points + obb_center  # 平移回原始位置

        # 更新 polydata 的點
        new_points = vtk.vtkPoints()
        new_points.SetData(np_to_vtk(aligned_points))
        polydata.SetPoints(new_points)

        # 如果提供了 upper_polydata，同步變換
        if upper_polydata is not None:
            upper_points = np.array(upper_polydata.GetPoints().GetData())
            upper_points = upper_points - obb_center
            aligned_upper_points = (rotation_matrix @ upper_points.T).T
            aligned_upper_points = aligned_upper_points + obb_center
            new_upper_points = vtk.vtkPoints()
            new_upper_points.SetData(np_to_vtk(aligned_upper_points))
            upper_polydata.SetPoints(new_upper_points)

        if angle ==90 or angle ==-90:
            # 計算旋轉矩陣（沿 Y 軸旋轉）
            aligned_points = np.array(polydata.GetPoints().GetData())
            aligned_center = np.mean(aligned_points, axis=0)
            theta = np.radians(angle)
            cos_theta = np.cos(theta)
            sin_theta = np.sin(theta)
            rotation_y = np.array([
                [cos_theta, 0, sin_theta],
                [0, 1, 0],
                [-sin_theta, 0, cos_theta]
            ])
            points = np.array(polydata.GetPoints().GetData())
            points = points - aligned_center
            rotated_points = (rotation_y @ points.T).T
            rotated_points = rotated_points + aligned_center
            new_points = vtk.vtkPoints()
            new_points.SetData(np_to_vtk(rotated_points))
            polydata.SetPoints(new_points)

        # (3) 可選：計算對齊後的 AABB
        aligned_bounds = polydata.GetBounds()  # 返回 (xmin, xmax, ymin, ymax, zmin, zmax)


        # # 計算各軸方向長度
        # x_length = aligned_bounds[1] - aligned_bounds[0]
        # y_length = aligned_bounds[3] - aligned_bounds[2]
        # z_length = aligned_bounds[5] - aligned_bounds[4]

        # print(f"x_length: {x_length}, y_length: {y_length}, z_length: {z_length}")

        return aligned_bounds

            
    def generate_point_cloud(self, angle=0):
        """
        生成點雲資料，根據角度選擇視角。
        
        參數:
        - angle (int): 旋轉角度，0 表示咬合面，90 表示舌側，-90 表示頰側。

        回傳:
        - np.array: 生成的點雲座標陣列
        """
        # 初始化與讀取
        vertices_list = []
        image = self.image
        width, height = image.size
        min_x_value, max_x_value = width, 0
        # 根據文件擴展名選擇合適的讀取器
        file_extension = os.path.splitext(self.ply_path)[1].lower()
        if file_extension == '.ply':
            reader = vtk.vtkPLYReader()
        elif file_extension == '.stl':
            reader = vtk.vtkSTLReader()
        elif file_extension == '.obj':
            reader = vtk.vtkOBJReader()
        else:
            raise ValueError(f"Unsupported file format: {file_extension}. Supported formats are .ply, .stl, .obj")
        reader.SetFileName(self.ply_path)
        reader.Update()
        polydata = reader.GetOutput()

        # 計算 OBB 邊界並將polydata對齊到世界坐標軸
        bounds = self.compute_obb_aligned_bounds(polydata)

        # 提取頂點數據
        points = polydata.GetPoints()
        vertices = np.array([points.GetPoint(i) for i in range(points.GetNumberOfPoints())])

        # 若需要側面，再做 Y 軸旋轉
        if angle in (90, -90): # 90 表示舌側，-90 表示頰側
            # 計算質心並移動至原點
            centroid = np.mean(vertices, axis=0)
            vertices -= centroid

            # 角度轉弧度
            theta = np.radians(angle) # angle = ±90 → theta = ±π/2

            # 定義 Y 軸旋轉矩陣
            rotation_y = np.array([
                [ np.cos(theta), 0, np.sin(theta)], # X → X, Z → X
                [            0, 1,            0], # Y 維不變
                [-np.sin(theta), 0, np.cos(theta)] # X → Z, Z → Z
            ])
            vertices = vertices @ rotation_y.T # 套用旋轉矩陣
            vertices += centroid # 將點雲移回原位置
            new_pts = vtk.vtkPoints()
            new_pts.SetData(np_to_vtk(vertices))
            polydata.SetPoints(new_pts)

            # 從旋轉後的 vertices 計算邊界
            bounds = polydata.GetBounds()

        min_x, max_x = bounds[0], bounds[1]
        min_y, max_y = bounds[2], bounds[3]
        min_z, max_z = bounds[4], bounds[5]

        # 如果不是咬合面視角，壓縮 Z 軸
        if angle != 0:
            min_z = max_z - (max_z - min_z) * 0.5

        # 生成點雲
        # 找出灰階影像中亮度不為 0 的區域與最大亮度，用來對應後面深度的 Z 軸轉換比例。
        max_value, min_value = 0, 255
        for y in range(height):
            for x in range(width):
                pixel_value = image.getpixel((x, y))
                max_value = max(max_value, pixel_value)
                min_value = min(min_value, pixel_value)
                if pixel_value != 0:
                    min_x_value = min(min_x_value, x)
                    max_x_value = max(max_x_value, x)
        
        for y in range(height-1, -1, -1):
            for x in range(width-1, -1, -1):
                gray_value = image.getpixel((x, y))
                new_x = get_depth_from_gray_value(x, max_x_value, min_x_value, min_x, max_x)
                new_y = get_depth_from_gray_value(height - y - 1, 255, 0, min_y, max_y)
                new_z = get_depth_from_gray_value(gray_value, max_value, min_value, min_z, max_z)
                vertices_list.append([new_x, new_y, new_z])
        
        return np.array(vertices_list)

        
    def generate_mesh(self, points):
        """生成三角形網格，並反轉法向量方向"""
        height, width = int(np.sqrt(len(points))), int(np.sqrt(len(points)))
        faces = []
        
        for y in range(height - 1):
            for x in range(width - 1):
                # 計算頂點索引
                v0 = y * width + x
                v1 = v0 + 1
                v2 = (y + 1) * width + x
                v3 = v2 + 1
                
                # 計算對角線長度來決定三角形的分割方式
                d1 = np.linalg.norm(points[v0] - points[v3])
                d2 = np.linalg.norm(points[v1] - points[v2])
                
                # 選擇較短的對角線作為分割線，並反轉三角形頂點順序以顛倒法向量
                if d1 < d2:
                    faces.extend([[v0, v3, v1], [v0, v2, v3]])  # 順序反轉
                else:
                    faces.extend([[v0, v2, v1], [v1, v2, v3]])  # 順序反轉
                    
            # 移除多餘的網格
        min_z_depth = np.min([point[2] for point in points])
        new_faces = []
        for face in faces:
            # 提取頂點座標
            triangle_points = [points[idx] for idx in face]
            z_values = [point[2] for point in triangle_points]
            x_values = [point[0] for point in triangle_points]
            y_values = [point[1] for point in triangle_points]

            # 判斷是否應移除 (完全平坦或超出範圍的網格)
            skip_triangle = (
                sum(z == min_z_depth for z in z_values) == 3 or
                min(x_values) == max(x_values) or
                min(y_values) == max(y_values)
            )

            if not skip_triangle:
                new_faces.append(face)
        # 創建和保存STL網格，計算時保留反轉後的法向量
        mesh_data = mesh.Mesh(np.zeros(len(new_faces), dtype=mesh.Mesh.dtype))
        for i, face in enumerate(new_faces):
            for j in range(3):
                mesh_data.vectors[i][j] = points[face[j]]
            
            # 手動反轉法向量方向
            normal = np.cross(
                mesh_data.vectors[i][1] - mesh_data.vectors[i][0],
                mesh_data.vectors[i][2] - mesh_data.vectors[i][0]
            )
            mesh_data.normals[i] = -normal / np.linalg.norm(normal)  # 反轉法向量
            
        mesh_data.save(self.stl_output_path)
        
    def reconstruct(self,angle=0):
        """執行完整的重建過程"""
        self.preprocess_image()
        points = self.generate_point_cloud(angle)
        self.generate_mesh(points)

def np_to_vtk(np_array):
    """將 NumPy 陣列轉換為 VTK 格式"""
    vtk_array = vtk.vtkDoubleArray()
    vtk_array.SetNumberOfComponents(3)
    vtk_array.SetNumberOfTuples(np_array.shape[0])
    for i, point in enumerate(np_array):
        vtk_array.SetTuple3(i, point[0], point[1], point[2])
    return vtk_array


def smooth_stl( input_stl_path, output_stl_path, iterations=20, relaxation_factor=0.2):
    """對 STL 進行平滑處理"""
    reader = vtk.vtkSTLReader()
    reader.SetFileName(input_stl_path)
    
    smoother = vtk.vtkSmoothPolyDataFilter()
    smoother.SetInputConnection(reader.GetOutputPort())
    smoother.SetNumberOfIterations(iterations)  # 設定平滑迭代次數
    smoother.SetRelaxationFactor(relaxation_factor)  # 控制平滑強度
    smoother.FeatureEdgeSmoothingOff()
    smoother.BoundarySmoothingOn()
    smoother.Update()

    writer = vtk.vtkSTLWriter()
    writer.SetFileName(output_stl_path)
    writer.SetInputConnection(smoother.GetOutputPort())
    writer.Write()

# reconstructor =DentalModelReconstructor("D:/Users/user/Desktop/weiyundontdelete/GANdata/pyqt/Aiobboutput/re_ai_data0119.png","D:/Users/user/Desktop/weiyundontdelete/GANdata/pyqt/Testdata/Prep/data0119.ply","D:/Users/user/Desktop/weiyundontdelete/GANdata/pyqt/Aiobboutput/re_ai_data0119.stl")
# reconstructor.reconstruct()
# smoothed_stl_path = "./ai_data0119_smooth.stl"
# smooth_stl("D:/Users/user/Desktop/weiyundontdelete/GANdata/pyqt/Aiobboutput/re_ai_data0119.stl", smoothed_stl_path)



