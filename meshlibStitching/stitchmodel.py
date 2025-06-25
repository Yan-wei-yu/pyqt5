import vtk
import numpy as np
from meshlib import mrmeshpy
import os
import pymeshlab
# import meshlib.mrmeshpy as mr
import vtkmodules.all as vtk
import numpy as np

class MeshProcessor:
    def __init__(self, defect_file_path, repair_file_path, output_folder):
        """初始化函數，使用輸入的STL檔案路徑和輸出資料夾"""
        self.inlay_file_path = None  # 初始化賦予自動摳出inlay_surface的檔案路徑
        self.hole_file_path = None   # 初始化賦予自動摳出hole的檔案路徑
        self.defect_file_path = defect_file_path  # 缺陷牙檔案路徑
        self.repair_file_path = repair_file_path  # 修復牙檔案路徑
        self.output_folder = output_folder  # 指定的輸出資料夾
        self.file_name = os.path.splitext(os.path.basename(repair_file_path))[0]  # 從修復牙檔案提取檔案名稱（不含副檔名）
    def run_icp(self):
        icp= vtk.vtkIterativeClosestPointTransform()
        repair_reader = self.get_vtk_reader(self.repair_file_path)
        repair_reader.SetFileName(self.repair_file_path)
        repair_reader.Update()
        repair_polydata = repair_reader.GetOutput()

        defect_reader = self.get_vtk_reader(self.defect_file_path)
        defect_reader.SetFileName(self.defect_file_path)
        defect_reader.Update()
        defect_polydata = defect_reader.GetOutput()
        icp.SetSource(repair_polydata)
        icp.SetTarget(defect_polydata)
        icp.GetLandmarkTransform().SetModeToRigidBody()
        icp.SetMaximumNumberOfIterations(100)
        icp.SetMaximumMeanDistance(0.00001)
        icp.StartByMatchingCentroidsOn()
        icp.Modified()
        icp.Update()
        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetInputData(repair_polydata)
        transform_filter.SetTransform(icp)
        transform_filter.Update()
        target_file_name = f"only_align_{self.file_name}.stl"
        aligned_polydata = vtk.vtkPolyData()
        aligned_polydata.DeepCopy(transform_filter.GetOutput())
        self.save_to_stitch_folder(target_file_name, aligned_polydata)  # 儲存對齊後的模型
        return transform_filter.GetOutput()  # 返回對齊後的模型
    def extract_patch_from_points(self, mesh, points):
        vtk_points = vtk.vtkPoints()
        polyline = vtk.vtkPolyLine()
        polyline.GetPointIds().SetNumberOfIds(len(points))

        for i, pt in enumerate(points):
            vtk_points.InsertNextPoint(pt)
            polyline.GetPointIds().SetId(i, i)

        cells = vtk.vtkCellArray()
        cells.InsertNextCell(polyline)
        loop_data = vtk.vtkPolyData()
        loop_data.SetPoints(vtk_points)
        loop_data.SetLines(cells)

        selector = vtk.vtkSelectPolyData()
        selector.SetInputData(mesh)
        selector.SetLoop(loop_data.GetPoints())
        selector.GenerateSelectionScalarsOn()
        selector.SetSelectionModeToSmallestRegion()
        selector.SetEdgeSearchModeToDijkstra()
        selector.Update()


        clipper = vtk.vtkClipPolyData()
        clipper.SetInputConnection(selector.GetOutputPort())
        clipper.InsideOutOn()
        clipper.Update()

        cleaner = vtk.vtkCleanPolyData()
        cleaner.SetInputConnection(clipper.GetOutputPort())
        cleaner.Update()

        connect = vtk.vtkPolyDataConnectivityFilter()
        connect.SetInputConnection(cleaner.GetOutputPort())
        connect.SetExtractionModeToLargestRegion()
        connect.Update()


        output_file = f"inlay_surface_{self.file_name}.stl"
        
        return self.save_to_stitch_folder(output_file, connect.GetOutput())  # 儲存擷取的模型

    def align_models_icp(self, source_polydata, target_polydata):
        """
        使用 VTK 的 ICP 對齊 source 到 target
        :param source_polydata: 要移動的模型（修復牙）
        :param target_polydata: 目標模型（缺陷牙）
        :return: 回傳修復牙對齊後的絕對路徑
        """
        icp = vtk.vtkIterativeClosestPointTransform()
        icp.SetSource(source_polydata)
        icp.SetTarget(target_polydata)
        icp.GetLandmarkTransform().SetModeToRigidBody()
        icp.SetMaximumNumberOfIterations(100)
        icp.SetMaximumMeanDistance(0.00001)
        icp.StartByMatchingCentroidsOn()
        icp.Modified()
        icp.Update()

        transform_filter = vtk.vtkTransformPolyDataFilter()
        transform_filter.SetInputData(source_polydata)
        transform_filter.SetTransform(icp)
        transform_filter.Update()

        aligned_polydata = vtk.vtkPolyData()
        aligned_polydata.DeepCopy(transform_filter.GetOutput())
        output_file_name = f"only_align_{self.file_name}.stl"

        append_both = vtk.vtkAppendPolyData() # 將對齊後的模型與缺陷牙合併
        append_both.AddInputData(aligned_polydata) # 添加對齊後的模型
        append_both.AddInputData(target_polydata) # 添加缺陷牙模型
        append_both.Update()
        append_both_polydata = append_both.GetOutput() # 取得合併後的模型

        both_file_name = f"./aligned_{self.file_name}.stl" # 設定輸出檔案名稱
        self.save_to_stitch_folder(both_file_name, append_both_polydata) # 儲存合併後的模型
        source_file_name = f"./source_{self.file_name}.stl" # 設定對齊後的模型輸出檔案名稱
        self.save_to_stitch_folder(source_file_name, aligned_polydata)
        return self.save_to_stitch_folder(output_file_name, aligned_polydata)
            


    def get_hole(self, defect_teeth, repair_teeth):
        """以空間距離，根據兩個牙齒模型的距離，計算出接觸面積，取得hole surface"""
        distance_filter = vtk.vtkDistancePolyDataFilter()
        distance_filter.SetInputData(0, defect_teeth)
        distance_filter.SetInputData(1, repair_teeth)
        distance_filter.SignedDistanceOff()
        distance_filter.Update()

        distance_data = distance_filter.GetOutput()

        threshold = vtk.vtkThreshold()
        threshold.SetInputData(distance_data)
        threshold.SetThresholdFunction(vtk.vtkThreshold.THRESHOLD_BETWEEN)
        # 根據檔案名稱設定閾值
        if os.path.basename(self.defect_file_path) == 'data0075.ply':
            threshold.SetLowerThreshold(0.25)
            threshold.SetUpperThreshold(3)
        elif os.path.basename(self.defect_file_path) == 'data0078.ply':
            threshold.SetLowerThreshold(0.5)
            threshold.SetUpperThreshold(4)
        else:
            threshold.SetLowerThreshold(0.8)  # 預設閾值
            threshold.SetUpperThreshold(4)
        threshold.Update()

        geometry_filter = vtk.vtkGeometryFilter()
        geometry_filter.SetInputConnection(threshold.GetOutputPort())
        geometry_filter.Update()
        contact_patch = geometry_filter.GetOutput()

        connectivity_filter = vtk.vtkConnectivityFilter()
        connectivity_filter.SetInputData(contact_patch)
        connectivity_filter.SetExtractionModeToLargestRegion()
        connectivity_filter.Update()
        main_patch = connectivity_filter.GetOutput()

        output_file = f"hole_{self.file_name}.stl"
        self.hole_file_path = output_file
        return self.save_to_stitch_folder(output_file, main_patch)

    def get_merge_source(self):
        repair_file_reader = vtk.vtkSTLReader()
        repair_file_reader.SetFileName(self.repair_file_path)
        repair_file_reader.Update()
        defect_file_reader = self.get_vtk_reader(self.defect_file_path)
        defect_file_reader.SetFileName(self.defect_file_path)
        defect_file_reader.Update()
        self.repair_file_path = self.align_models_icp(repair_file_reader.GetOutput(), defect_file_reader.GetOutput())
        align_repair_file_reader = vtk.vtkSTLReader()
        align_repair_file_reader.SetFileName(self.repair_file_path)
        align_repair_file_reader.Update()

        file_name = f"inlay_surface_{self.file_name}.stl"
        open_path = os.path.join(self.output_folder, file_name)
        open_path = os.path.normpath(open_path)  # 確保路徑格式正確

        self.inlay_file_path = open_path
        self.hole_file_path = self.get_hole(defect_file_reader.GetOutput(), align_repair_file_reader.GetOutput())
        print(f"已儲存合併源檔案")

    def is_white_surface_facing_down(self, polydata):
        """檢查平均法向量是否朝下（Z軸負方向）"""
        normals_filter = vtk.vtkPolyDataNormals()
        normals_filter.SetInputData(polydata)
        normals_filter.Update()

        poly_with_normals = normals_filter.GetOutput()
        normals = poly_with_normals.GetPointData().GetNormals()

        avg_normal = np.zeros(3)
        for i in range(normals.GetNumberOfTuples()):
            avg_normal += np.array(normals.GetTuple(i))
        avg_normal /= normals.GetNumberOfTuples()

        direction = avg_normal / np.linalg.norm(avg_normal)
        print("平均法向量方向:", direction)
        return direction[2] < 0

    def is_white_surface_facing_inner(self, polydata, threshold=0.6):
        """檢查大多數法向量是否朝內"""
        normals_filter = vtk.vtkPolyDataNormals()
        normals_filter.SetInputData(polydata)
        normals_filter.Update()

        polydata = normals_filter.GetOutput()
        center = np.array(polydata.GetCenter())
        points = polydata.GetPoints()
        normals = polydata.GetPointData().GetNormals()

        inward_count = 0
        for i in range(points.GetNumberOfPoints()):
            pt = np.array(points.GetPoint(i))
            n = np.array(normals.GetTuple(i))
            to_center = center - pt
            if np.dot(n, to_center) > 0:
                inward_count += 1

        ratio = inward_count / points.GetNumberOfPoints()
        print(f"朝內法向比例: {ratio}")
        print(f"閾值: {threshold}")
        print(ratio > threshold)
        return ratio > threshold

    def merge_meshes(self):
        """合併嵌體和缺陷牙凹洞網格，並確保正確的法向量方向"""
        inlay_reader = vtk.vtkSTLReader()
        inlay_reader.SetFileName(self.inlay_file_path)
        inlay_reader.Update()

        hole_reader = vtk.vtkSTLReader()
        hole_reader.SetFileName(self.hole_file_path)
        hole_reader.Update()

        inlay_normal = vtk.vtkPolyDataNormals()
        inlay_normal.SetInputData(inlay_reader.GetOutput())
        if self.is_white_surface_facing_down(inlay_reader.GetOutput()):
            inlay_normal.SetAutoOrientNormals(False)
            print("嵌體: 不翻轉法向量")
        else:
            inlay_normal.SetAutoOrientNormals(False)
            inlay_normal.SetFlipNormals(True)
            print("嵌體: 翻轉法向量")
        inlay_normal.SetConsistency(True)
        inlay_normal.SplittingOff()
        inlay_normal.Update()

        hole_normal = vtk.vtkPolyDataNormals()
        hole_normal.SetInputData(hole_reader.GetOutput())
        if self.is_white_surface_facing_inner(hole_reader.GetOutput()):
            hole_normal.SetAutoOrientNormals(False)
            print("缺陷牙: 不翻轉法向量")
        else:
            hole_normal.SetAutoOrientNormals(False)
            hole_normal.SetFlipNormals(True)
            print("缺陷牙: 翻轉法向量")
        hole_normal.SetConsistency(True)
        hole_normal.SplittingOff()
        hole_normal.Update()

        merge_file = vtk.vtkAppendPolyData()
        merge_file.AddInputData(inlay_normal.GetOutput())
        merge_file.AddInputData(hole_normal.GetOutput())
        merge_file.Update()

        output_file = f"merge_{self.file_name}.stl"

        return self.save_to_stitch_folder(output_file, merge_file.GetOutput())

    def process_merged_mesh(self, merged_file_path, thickness=0):
        """處理合併後的網格：修復、偏移、拼接和平滑"""
        mesh = mrmeshpy.loadMesh(merged_file_path)
        original_file_name = os.path.splitext(os.path.basename(merged_file_path))[0]

        mrmeshpy.uniteCloseVertices(mesh, mesh.computeBoundingBox().diagonal() * 1e-6)

        params = mrmeshpy.GeneralOffsetParameters()
        params.voxelSize = 1
        params.signDetectionMode = mrmeshpy.SignDetectionMode.Unsigned
        shell = mrmeshpy.thickenMesh(mesh, thickness, params)

        holes = shell.topology.findHoleRepresentiveEdges()
        print("檢測到的洞數量:", holes.size())
        if holes.size() >= 2:
            new_faces = mrmeshpy.FaceBitSet()
            stitch_params = mrmeshpy.StitchHolesParams()
            stitch_params.metric = mrmeshpy.getMinAreaMetric(shell)
            stitch_params.outNewFaces = new_faces
            mrmeshpy.buildCylinderBetweenTwoHoles(shell, holes[0], holes[1], stitch_params)


            stitch_only = mrmeshpy.Mesh()
            stitch_only.addPartByMask(shell, new_faces)
            stitch_only_file = os.path.join(self.output_folder, f"stitch_only_{original_file_name}.stl")
            mrmeshpy.saveMesh(stitch_only, stitch_only_file)
            print(f"已儲存縫合區域至: {stitch_only_file}")
            subdiv_settings = mrmeshpy.SubdivideSettings()
            subdiv_settings.region = new_faces
            subdiv_settings.maxEdgeSplits = 10000000
            subdiv_settings.maxEdgeLen = 1
            mrmeshpy.subdivideMesh(shell, subdiv_settings)

            mrmeshpy.positionVertsSmoothly(shell, mrmeshpy.getInnerVerts(shell.topology, new_faces))

        output_file = os.path.join(self.output_folder, f"stitched_{original_file_name}.stl")
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        mrmeshpy.saveMesh(shell, output_file)
        print(f"已儲存檔案至: {output_file}")
        return output_file
    def offset_smooth_subdivision(self, smooth_subdivision_file, offset_distance=0.1):
        """對平滑細分後的模型進行偏移處理"""
        ms_smooth = mrmeshpy.loadMesh(smooth_subdivision_file)

        params = mrmeshpy.OffsetParameters()
        params.voxelSize = ms_smooth.computeBoundingBox().diagonal() * 0.01
        offset_mesh = mrmeshpy.offsetMesh(ms_smooth, offset_distance, params)
        output_path = f"offset_smooth_subdivision_{self.file_name}.stl"
        output_path = os.path.join(self.output_folder, output_path)
        mrmeshpy.saveMesh(offset_mesh, output_path)
        print(f"已儲存偏移後的平滑細分檔案至: {output_path}")
        return output_path

    def save_to_stitch_folder(self, input_file_name, poly_data):
        """將處理後的檔案儲存到指定資料夾"""
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        output_path = os.path.join(self.output_folder, input_file_name)
        output_path = os.path.normpath(output_path)  # 確保路徑格式正確
        writer = vtk.vtkSTLWriter()
        writer.SetFileName(output_path)
        writer.SetInputData(poly_data)
        writer.SetFileTypeToBinary()
        writer.Write()
        print(f"已儲存檔案至: {output_path}")
        return output_path
    def open_file(self, file_name):
        """打開指定的檔案"""
        if not os.path.exists(file_name):
            print(f"檔案不存在: {file_name}")
            return None
        if file_name.endswith('.stl'):
            reader = vtk.vtkSTLReader()
        elif file_name.endswith('.ply'):
            reader = vtk.vtkPLYReader()
        else:
            print(f"不支援的檔案格式: {file_name}")
            return None
        open_path = os.path.join(self.output_folder, file_name)
        open_path = os.path.normpath(open_path)  # 確保路徑格式正確
        reader.SetFileName(file_name)
        reader.Update()
        return reader.GetOutput()

    def remesh(self, row_final_file):
        """重網格化處理"""
        ms = pymeshlab.MeshSet()
        ms.load_new_mesh(row_final_file)

        ms.apply_filter("meshing_isotropic_explicit_remeshing",
                        iterations=30,
                        targetlen=pymeshlab.PercentageValue(1),
                        adaptive=False,
                        featuredeg=30,
                        checksurfdist=True,
                        maxsurfdist=pymeshlab.PercentageValue(0.5),
                        splitflag=True,
                        collapseflag=True,
                        swapflag=True,
                        smoothflag=True,
                        reprojectflag=True)

        output_file = os.path.join(self.output_folder, f"remesh_{self.file_name}.stl")
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        ms.save_current_mesh(output_file)
        print(f"已儲存檔案至: {output_file}")
        return output_file

    def smooth_subdivision(self, remesh_final_file):
        """平滑和細分處理"""
        remesh_final_file_reader = vtk.vtkSTLReader()
        remesh_final_file_reader.SetFileName(remesh_final_file)
        remesh_final_file_reader.Update()

        smoother = vtk.vtkSmoothPolyDataFilter()
        smoother.SetInputConnection(remesh_final_file_reader.GetOutputPort())
        smoother.SetNumberOfIterations(20)
        smoother.SetRelaxationFactor(0.1)
        smoother.FeatureEdgeSmoothingOff()
        smoother.BoundarySmoothingOn()
        smoother.Update()

        subdivision = vtk.vtkLoopSubdivisionFilter()
        subdivision.SetInputConnection(smoother.GetOutputPort())
        subdivision.SetNumberOfSubdivisions(2)
        subdivision.Update()

        output_file = os.path.join(self.output_folder, f"smooth_subdivision_{self.file_name}.stl")
        if not os.path.exists(self.output_folder):
            os.makedirs(self.output_folder)
        return self.save_to_stitch_folder(output_file, subdivision.GetOutput())
    def combine_defect_and_smooth(self, smooth_subdivision_file):
        """將缺陷牙和平滑細分後的模型合併"""
        defect_reader = self.get_vtk_reader(self.defect_file_path)
        defect_reader.SetFileName(self.defect_file_path)
        defect_reader.Update()

        smooth_reader = vtk.vtkSTLReader()
        smooth_reader.SetFileName(smooth_subdivision_file)
        smooth_reader.Update()

        append_filter = vtk.vtkAppendPolyData()
        append_filter.AddInputData(defect_reader.GetOutput())
        append_filter.AddInputData(smooth_reader.GetOutput())
        append_filter.Update()

        output_file = os.path.join(self.output_folder, f"final_combined_{self.file_name}.stl")
        return self.save_to_stitch_folder(output_file, append_filter.GetOutput())
    def append_stitch_only(self, stitch_only_file,merge_file):
        """將縫合區域與合併後的模型進行拼接"""
        stitch_reader = vtk.vtkSTLReader()
        stitch_reader.SetFileName(stitch_only_file)
        stitch_reader.Update()

        merge_reader = vtk.vtkSTLReader()
        merge_reader.SetFileName(merge_file)
        merge_reader.Update()

        #翻轉merge_reader的法向量
        merge_polydata = merge_reader.GetOutput()
        merge_normals = vtk.vtkPolyDataNormals()
        merge_normals.SetInputData(merge_polydata)

        append_filter = vtk.vtkAppendPolyData()
        append_filter.AddInputData(stitch_reader.GetOutput())
        append_filter.AddInputData(merge_normals.GetOutput())
        append_filter.Update()
         

        output_file = os.path.join(self.output_folder, f"final_stitch_{self.file_name}.stl")
        return self.save_to_stitch_folder(output_file, append_filter.GetOutput()) 
    

    
    def process_complete_workflow(self, thickness=0):
        """執行完整的工作流程"""

        self.get_merge_source()  
        merged_file = self.merge_meshes()
        row_final_file = self.process_merged_mesh(merged_file, thickness)
        remesh_final_file = self.remesh(row_final_file)
        smooth_subdivision_file = self.smooth_subdivision(remesh_final_file)
        final_file = self.append_stitch_only(smooth_subdivision_file, merged_file)


        
        print(f"完整工作流程已完成，最終檔案儲存於: {final_file}")
        return final_file
    
    def get_vtk_reader(self,file_path):
        ext = file_path.lower().split('.')[-1]
        if ext == "stl":
            return vtk.vtkSTLReader()
        elif ext == "ply":
            return vtk.vtkPLYReader()
        elif ext == "obj":
            return vtk.vtkOBJReader()
        else:
            raise ValueError(f"不支援的檔案格式: .{ext}")