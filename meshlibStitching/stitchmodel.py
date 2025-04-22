import vtk  # VTK 用於 3D 模型處理和可視化
import numpy as np  # NumPy 用於數值計算和陣列操作
from meshlib import mrmeshpy  # meshlib 的 mrmeshpy 用於網格處理
import os  # os 模組用於檔案和資料夾操作
import pymeshlab  # pymeshlab 用於網格重網格化和處理

class MeshProcessor:
    def __init__(self, defect_file_path, repair_file_path, output_folder):
        """初始化函數，設置輸入的 STL 檔案路徑和輸出資料夾
        :param defect_file_path: 缺陷牙模型的檔案路徑
        :param repair_file_path: 修復牙模型的檔案路徑
        :param output_folder: 處理結果的輸出資料夾路徑
        """
        self.inlay_file_path = None  # 用於儲存自動生成的 inlay surface 檔案路徑
        self.hole_file_path = None   # 用於儲存自動生成的 hole 檔案路徑
        self.defect_file_path = defect_file_path  # 缺陷牙模型的路徑
        self.repair_file_path = repair_file_path  # 修復牙模型的路徑
        self.output_folder = output_folder  # 輸出資料夾路徑
        self.file_name = os.path.splitext(os.path.basename(repair_file_path))[0]  # 從修復牙檔案提取檔案名稱（不含副檔名）

    def align_models_icp(self, source_polydata, target_polydata):
        """使用 VTK 的 ICP 演算法將 source 模型對齊到 target 模型
        :param source_polydata: 要移動的模型（修復牙）
        :param target_polydata: 目標模型（缺陷牙）
        :return: 對齊後的修復牙模型檔案的絕對路徑
        """
        icp = vtk.vtkIterativeClosestPointTransform()  # 創建 ICP 變換物件
        icp.SetSource(source_polydata)  # 設置來源模型
        icp.SetTarget(target_polydata)  # 設置目標模型
        icp.GetLandmarkTransform().SetModeToRigidBody()  # 設置為剛體變換模式
        icp.SetMaximumNumberOfIterations(100)  # 設置最大迭代次數
        icp.SetMaximumMeanDistance(0.00001)  # 設置最大平均距離閾值
        icp.StartByMatchingCentroidsOn()  # 啟用質心對齊作為初始步驟
        icp.Modified()  # 更新 ICP 物件
        icp.Update()  # 執行 ICP 對齊

        transform_filter = vtk.vtkTransformPolyDataFilter()  # 創建變換過濾器
        transform_filter.SetInputData(source_polydata)  # 設置輸入模型
        transform_filter.SetTransform(icp)  # 應用 ICP 變換
        transform_filter.Update()  # 執行變換

        aligned_polydata = vtk.vtkPolyData()  # 創建對齊後的模型物件
        aligned_polydata.DeepCopy(transform_filter.GetOutput())  # 複製變換結果
        output_file_name = f"only_align_{self.file_name}.stl"  # 設置輸出檔案名稱
        return self.save_to_stitch_folder(output_file_name, aligned_polydata)  # 儲存並返回檔案路徑

    def get_inlay_surface(self, defect_teeth, repair_teeth):
        """根據兩個牙齒模型的空間距離，計算接觸面積以提取 inlay surface
        :param defect_teeth: 缺陷牙模型
        :param repair_teeth: 修復牙模型
        :return: inlay surface 檔案的絕對路徑
        """
        distance_filter = vtk.vtkDistancePolyDataFilter()  # 創建距離計算過濾器
        distance_filter.SetInputData(0, repair_teeth)  # 設置修復牙作為第一輸入
        distance_filter.SetInputData(1, defect_teeth)  # 設置缺陷牙作為第二輸入
        distance_filter.SignedDistanceOff()  # 關閉簽名距離計算
        distance_filter.Update()  # 執行距離計算

        distance_data = distance_filter.GetOutput()  # 獲取距離計算結果

        threshold = vtk.vtkThreshold()  # 創建閾值過濾器
        threshold.SetInputData(distance_data)  # 設置輸入數據
        threshold.SetThresholdFunction(vtk.vtkThreshold.THRESHOLD_BETWEEN)  # 設置閾值範圍
        # 根據檔案名稱動態設定閾值
        if os.path.basename(self.defect_file_path) == 'data0075.ply':
            threshold.SetLowerThreshold(0.22)  # 設置下限閾值
            threshold.SetUpperThreshold(3.5)   # 設置上限閾值
        elif os.path.basename(self.defect_file_path) == 'data0078.ply':
            threshold.SetLowerThreshold(0.55)  # 設置下限閾值
            threshold.SetUpperThreshold(4)     # 設置上限閾值
        else:
            threshold.SetLowerThreshold(0.22)  # 預設下限閾值
            threshold.SetUpperThreshold(3.5)   # 預設上限閾值
        threshold.Update()  # 執行閾值過濾

        geometry_filter = vtk.vtkGeometryFilter()  # 創建幾何過濾器
        geometry_filter.SetInputConnection(threshold.GetOutputPort())  # 設置輸入
        geometry_filter.Update()  # 執行幾何提取
        contact_patch = geometry_filter.GetOutput()  # 獲取接觸區域

        connectivity_filter = vtk.vtkConnectivityFilter()  # 創建連通性過濾器
        connectivity_filter.SetInputData(contact_patch)  # 設置輸入
        connectivity_filter.SetExtractionModeToLargestRegion()  # 提取最大連通區域
        connectivity_filter.Update()  # 執行連通性過濾
        main_patch = connectivity_filter.GetOutput()  # 獲取主要區域

        output_file = f"inlay_surface_{self.file_name}.stl"  # 設置輸出檔案名稱
        return self.save_to_stitch_folder(output_file, main_patch)  # 儲存並返回檔案路徑

    def get_hole(self, defect_teeth, repair_teeth):
        """根據兩個牙齒模型的空間距離，計算接觸面積以提取 hole surface
        :param defect_teeth: 缺陷牙模型
        :param repair_teeth: 修復牙模型
        :return: hole surface 檔案的絕對路徑
        """
        distance_filter = vtk.vtkDistancePolyDataFilter()  # 創建距離計算過濾器
        distance_filter.SetInputData(0, defect_teeth)  # 設置缺陷牙作為第一輸入
        distance_filter.SetInputData(1, repair_teeth)  # 設置修復牙作為第二輸入
        distance_filter.SignedDistanceOff()  # 關閉簽名距離計算
        distance_filter.Update()  # 執行距離計算

        distance_data = distance_filter.GetOutput()  # 獲取距離計算結果

        threshold = vtk.vtkThreshold()  # 創建閾值過濾器
        threshold.SetInputData(distance_data)  # 設置輸入數據
        threshold.SetThresholdFunction(vtk.vtkThreshold.THRESHOLD_BETWEEN)  # 設置閾值範圍
        # 根據檔案名稱動態設定閾值
        if os.path.basename(self.defect_file_path) == 'data0075.ply':
            threshold.SetLowerThreshold(0.25)  # 設置下限閾值
            threshold.SetUpperThreshold(3)     # 設置上限閾值
        elif os.path.basename(self.defect_file_path) == 'data0078.ply':
            threshold.SetLowerThreshold(0.5)   # 設置下限閾值
            threshold.SetUpperThreshold(4)     # 設置上限閾值
        else:
            threshold.SetLowerThreshold(0.25)  # 預設下限閾值
            threshold.SetUpperThreshold(3)     # 預設上限閾值
        threshold.Update()  # 執行閾值過濾

        geometry_filter = vtk.vtkGeometryFilter()  # 創建幾何過濾器
        geometry_filter.SetInputConnection(threshold.GetOutputPort())  # 設置輸入
        geometry_filter.Update()  # 執行幾何提取
        contact_patch = geometry_filter.GetOutput()  # 獲取接觸區域

        connectivity_filter = vtk.vtkConnectivityFilter()  # 創建連通性過濾器
        connectivity_filter.SetInputData(contact_patch)  # 設置輸入
        connectivity_filter.SetExtractionModeToLargestRegion()  # 提取最大連通區域
        connectivity_filter.Update()  # 執行連通性過濾
        main_patch = connectivity_filter.GetOutput()  # 獲取主要區域

        output_file = f"hole_{self.file_name}.stl"  # 設置輸出檔案名稱
        return self.save_to_stitch_folder(output_file, main_patch)  # 儲存並返回檔案路徑

    def get_merge_source(self):
        """生成合併所需的源檔案，包括對齊修復牙、提取 inlay surface 和 hole surface"""
        repair_file_reader = vtk.vtkSTLReader()  # 創建 STL 檔案讀取器
        repair_file_reader.SetFileName(self.repair_file_path)  # 設置修復牙檔案路徑
        repair_file_reader.Update()  # 讀取檔案
        defect_file_reader = vtk.vtkPLYReader()  # 創建 PLY 檔案讀取器
        defect_file_reader.SetFileName(self.defect_file_path)  # 設置缺陷牙檔案路徑
        defect_file_reader.Update()  # 讀取檔案
        # 對齊修復牙到缺陷牙並更新修復牙檔案路徑
        self.repair_file_path = self.align_models_icp(repair_file_reader.GetOutput(), defect_file_reader.GetOutput())
        align_repair_file_reader = vtk.vtkSTLReader()  # 創建 STL 檔案讀取器
        align_repair_file_reader.SetFileName(self.repair_file_path)  # 設置對齊後的修復牙檔案路徑
        align_repair_file_reader.Update()  # 讀取檔案

        # 提取 inlay surface 和 hole surface
        self.inlay_file_path = self.get_inlay_surface(defect_file_reader.GetOutput(), align_repair_file_reader.GetOutput())
        self.hole_file_path = self.get_hole(defect_file_reader.GetOutput(), align_repair_file_reader.GetOutput())
        print(f"已儲存合併源檔案")  # 輸出完成訊息

    def is_white_surface_facing_down(self, polydata):
        """檢查模型的平均法向量是否朝下（Z軸負方向）
        :param polydata: 輸入的網格模型
        :return: 如果平均法向量朝下，返回 True，否則返回 False
        """
        normals_filter = vtk.vtkPolyDataNormals()  # 創建法向量計算過濾器
        normals_filter.SetInputData(polydata)  # 設置輸入模型
        normals_filter.Update()  # 計算法向量

        poly_with_normals = normals_filter.GetOutput()  # 獲取帶法向量的模型
        normals = poly_with_normals.GetPointData().GetNormals()  # 獲取法向量數據

        avg_normal = np.zeros(3)  # 初始化平均法向量
        for i in range(normals.GetNumberOfTuples()):  # 遍歷所有法向量
            avg_normal += np.array(normals.GetTuple(i))  # 累加法向量
        avg_normal /= normals.GetNumberOfTuples()  # 計算平均法向量

        direction = avg_normal / np.linalg.norm(avg_normal)  # 歸一化平均法向量
        print("平均法向量方向:", direction)  # 輸出平均法向量方向
        return direction[2] < 0  # 如果 Z 分量小於 0，則朝下

    def is_white_surface_facing_inner(self, polydata, threshold=0.6):
        """檢查大多數法向量是否朝向模型內部
        :param polydata: 輸入的網格模型
        :param threshold: 朝內法向量的比例閾值
        :return: 如果朝內法向量比例超過閾值，返回 True，否則返回 False
        """
        normals_filter = vtk.vtkPolyDataNormals()  # 創建法向量計算過濾器
        normals_filter.SetInputData(polydata)  # 設置輸入模型
        normals_filter.Update()  # 計算法向量

        polydata = normals_filter.GetOutput()  # 獲取帶法向量的模型
        center = np.array(polydata.GetCenter())  # 計算模型中心
        points = polydata.GetPoints()  # 獲取模型的點數據
        normals = polydata.GetPointData().GetNormals()  # 獲取法向量數據

        inward_count = 0  # 記錄朝內法向量的數量
        for i in range(points.GetNumberOfPoints()):  # 遍歷所有點
            pt = np.array(points.GetPoint(i))  # 獲取點座標
            n = np.array(normals.GetTuple(i))  # 獲取法向量
            to_center = center - pt  # 計算從點到中心的向量
            if np.dot(n, to_center) > 0:  # 如果法向量與中心向量點積大於 0，則朝內
                inward_count += 1

        ratio = inward_count / points.GetNumberOfPoints()  # 計算朝內法向量的比例
        print(f"朝內法向比例: {ratio}")  # 輸出朝內比例
        print(f"閾值: {threshold}")  # 輸出閾值
        print(ratio > threshold)  # 輸出比較結果
        return ratio > threshold  # 返回比較結果

    def merge_meshes(self):
        """合併 inlay 和 hole 網格，並確保法向量方向正確
        :return: 合併後的網格檔案路徑
        """
        inlay_reader = vtk.vtkSTLReader()  # 創建 STL 檔案讀取器
        inlay_reader.SetFileName(self.inlay_file_path)  # 設置 inlay 檔案路徑
        inlay_reader.Update()  # 讀取檔案

        hole_reader = vtk.vtkSTLReader()  # 創建 STL 檔案讀取器
        hole_reader.SetFileName(self.hole_file_path)  # 設置 hole 檔案路徑
        hole_reader.Update()  # 讀取檔案

        inlay_normal = vtk.vtkPolyDataNormals()  # 創建法向量處理過濾器
        inlay_normal.SetInputData(inlay_reader.GetOutput())  # 設置輸入
        if self.is_white_surface_facing_down(inlay_reader.GetOutput()):  # 檢查法向量是否朝下
            inlay_normal.SetAutoOrientNormals(False)  # 不自動調整法向量
            print("嵌體: 不翻轉法向量")  # 輸出訊息
        else:
            inlay_normal.SetAutoOrientNormals(True)  # 自動調整法向量
            print("嵌體: 翻轉法向量")  # 輸出訊息
        inlay_normal.SetConsistency(True)  # 確保法向量一致性
        inlay_normal.SplittingOff()  # 關閉三角形分割
        inlay_normal.Update()  # 執行法向量處理

        hole_normal = vtk.vtkPolyDataNormals()  # 創建法向量處理過濾器
        hole_normal.SetInputData(hole_reader.GetOutput())  # 設置輸入
        if self.is_white_surface_facing_inner(hole_reader.GetOutput()):  # 檢查法向量是否朝內
            hole_normal.SetAutoOrientNormals(False)  # 不自動調整法向量
            print("缺陷牙: 不翻轉法向量")  # 輸出訊息
        else:
            hole_normal.SetAutoOrientNormals(False)  # 不自動調整法向量
            hole_normal.SetFlipNormals(True)  # 翻轉法向量
            print("缺陷牙: 翻轉法向量")  # 輸出訊息
        hole_normal.SetConsistency(True)  # 確保法向量一致性
        hole_normal.SplittingOff()  # 關閉三角形分割
        hole_normal.Update()  # 執行法向量處理

        merge_file = vtk.vtkAppendPolyData()  # 創建網格合併物件
        merge_file.AddInputData(inlay_normal.GetOutput())  # 添加 inlay 網格
        merge_file.AddInputData(hole_normal.GetOutput())  # 添加 hole 網格
        merge_file.Update()  # 執行合併

        output_file = f"merge_{self.file_name}.stl"  # 設置輸出檔案名稱
        return self.save_to_stitch_folder(output_file, merge_file.GetOutput())  # 儲存並返回檔案路徑

    def process_merged_mesh(self, merged_file_path, thickness=0):
        """處理合併後的網格，包括修復、偏移、拼接和平滑
        :param merged_file_path: 合併網格的檔案路徑
        :param thickness: 網格增厚的厚度
        :return: 處理後的網格檔案路徑
        """
        mesh = mrmeshpy.loadMesh(merged_file_path)  # 載入合併網格
        original_file_name = os.path.splitext(os.path.basename(merged_file_path))[0]  # 提取檔案名稱

        mrmeshpy.uniteCloseVertices(mesh, mesh.computeBoundingBox().diagonal() * 1e-6)  # 合併靠近的頂點

        params = mrmeshpy.GeneralOffsetParameters()  # 創建偏移參數
        params.voxelSize = 1  # 設置體素大小
        params.signDetectionMode = mrmeshpy.SignDetectionMode.Unsigned  # 設置無符號檢測模式
        shell = mrmeshpy.thickenMesh(mesh, thickness, params)  # 增厚網格

        holes = shell.topology.findHoleRepresentiveEdges()  # 檢測網格中的洞
        print("檢測到的洞數量:", holes.size())  # 輸出洞的數量
        if holes.size() >= 2:  # 如果檢測到至少兩個洞
            new_faces = mrmeshpy.FaceBitSet()  # 創建新面集合
            stitch_params = mrmeshpy.StitchHolesParams()  # 創建拼接參數
            stitch_params.metric = mrmeshpy.getMinAreaMetric(shell)  # 設置最小面積度量
            stitch_params.outNewFaces = new_faces  # 設置新面輸出
            mrmeshpy.buildCylinderBetweenTwoHoles(shell, holes[0], holes[1], stitch_params)  # 在兩個洞之間建立圓柱

            subdiv_settings = mrmeshpy.SubdivideSettings()  # 創建細分參數
            subdiv_settings.region = new_faces  # 設置細分區域
            subdiv_settings.maxEdgeSplits = 10000000  # 設置最大邊分割數
            subdiv_settings.maxEdgeLen = 1  # 設置最大邊長
            mrmeshpy.subdivideMesh(shell, subdiv_settings)  # 細分網格

            mrmeshpy.positionVertsSmoothly(shell, mrmeshpy.getInnerVerts(shell.topology, new_faces))  # 平滑頂點位置

        output_file = os.path.join(self.output_folder, f"stitched_{original_file_name}.stl")  # 設置輸出檔案路徑
        if not os.path.exists(self.output_folder):  # 如果輸出資料夾不存在
            os.makedirs(self.output_folder)  # 創建資料夾
        mrmeshpy.saveMesh(shell, output_file)  # 儲存網格
        print(f"已儲存檔案至: {output_file}")  # 輸出儲存訊息
        return output_file  # 返回檔案路徑

    def save_to_stitch_folder(self, input_file_name, poly_data):
        """將處理後的網格儲存到指定資料夾
        :param input_file_name: 輸出檔案名稱
        :param poly_data: 要儲存的網格數據
        :return: 儲存的檔案路徑
        """
        if not os.path.exists(self.output_folder):  # 如果輸出資料夾不存在
            os.makedirs(self.output_folder)  # 創建資料夾
        output_path = os.path.join(self.output_folder, input_file_name)  # 設置輸出檔案路徑
        writer = vtk.vtkSTLWriter()  # 創建 STL 寫入器
        writer.SetFileName(output_path)  # 設置輸出檔案路徑
        writer.SetInputData(poly_data)  # 設置輸入網格
        writer.SetFileTypeToBinary()  # 設置為二進位格式
        writer.Write()  # 執行寫入
        print(f"已儲存檔案至: {output_path}")  # 輸出儲存訊息
        return output_path  # 返回檔案路徑

    def remesh(self, row_final_file):
        """對網格進行重網格化處理
        :param row_final_file: 輸入的網格檔案路徑
        :return: 重網格化後的檔案路徑
        """
        ms = pymeshlab.MeshSet()  # 創建 MeshSet 物件
        ms.load_new_mesh(row_final_file)  # 載入網格檔案

        # 應用等向顯式重網格化濾波器
        ms.apply_filter("meshing_isotropic_explicit_remeshing",
                        iterations=30,  # 迭代次數
                        targetlen=pymeshlab.PercentageValue(1),  # 目標邊長（百分比）
                        adaptive=False,  # 禁用自適應重網格化
                        featuredeg=30,  # 特徵角度
                        checksurfdist=True,  # 檢查表面距離
                        maxsurfdist=pymeshlab.PercentageValue(0.5),  # 最大表面距離
                        splitflag=True,  # 啟用分割
                        collapseflag=True,  # 啟用塌陷
                        swapflag=True,  # 啟用交換
                        smoothflag=True,  # 啟用平滑
                        reprojectflag=True)  # 啟用重新投影

        output_file = os.path.join(self.output_folder, f"remesh_{self.file_name}.stl")  # 設置輸出檔案路徑
        if not os.path.exists(self.output_folder):  # 如果輸出資料夾不存在
            os.makedirs(self.output_folder)  # 創建資料夾
        ms.save_current_mesh(output_file)  # 儲存網格
        print(f"已儲存檔案至: {output_file}")  # 輸出儲存訊息
        return output_file  # 返回檔案路徑

    def smooth_subdivision(self, remesh_final_file):
        """對網格進行平滑和細分處理
        :param remesh_final_file: 輸入的網格檔案路徑
        :return: 平滑和細分後的檔案路徑
        """
        remesh_final_file_reader = vtk.vtkSTLReader()  # 創建 STL 檔案讀取器
        remesh_final_file_reader.SetFileName(remesh_final_file)  # 設置輸入檔案路徑
        remesh_final_file_reader.Update()  # 讀取檔案

        smoother = vtk.vtkSmoothPolyDataFilter()  # 創建平滑過濾器
        smoother.SetInputConnection(remesh_final_file_reader.GetOutputPort())  # 設置輸入
        smoother.SetNumberOfIterations(20)  # 設置迭代次數
        smoother.SetRelaxationFactor(0.1)  # 設置鬆弛因子
        smoother.FeatureEdgeSmoothingOff()  # 關閉特徵邊平滑
        smoother.BoundarySmoothingOn()  # 啟用邊界平滑
        smoother.Update()  # 執行平滑

        subdivision = vtk.vtkLoopSubdivisionFilter()  # 創建細分過濾器
        subdivision.SetInputConnection(smoother.GetOutputPort())  # 設置輸入
        subdivision.SetNumberOfSubdivisions(2)  # 設置細分次數
        subdivision.Update()  # 執行細分

        output_file = os.path.join(self.output_folder, f"smooth_subdivision_{self.file_name}.stl")  # 設置輸出檔案路徑
        if not os.path.exists(self.output_folder):  # 如果輸出資料夾不存在
            os.makedirs(self.output_folder)  # 創建資料夾
        return self.save_to_stitch_folder(output_file, subdivision.GetOutput())  # 儲存並返回檔案路徑

    def process_complete_workflow(self, thickness=0):
        """執行完整的網格處理工作流程
        :param thickness: 網格增厚的厚度
        :return: 最終處理完成的檔案路徑
        """
        self.get_merge_source()  # 生成合併源檔案
        merged_file = self.merge_meshes()  # 合併網格
        row_final_file = self.process_merged_mesh(merged_file, thickness)  # 處理合併網格
        remesh_final_file = self.remesh(row_final_file)  # 重網格化
        smooth_subdivision_file = self.smooth_subdivision(remesh_final_file)  # 平滑和細分
        return smooth_subdivision_file  # 返回最終檔案路徑