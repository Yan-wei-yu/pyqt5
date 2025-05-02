from PyQt5.QtCore import pyqtSignal
import os
from .BaseModel import BaseModel
from Otherfunction import readmodel, trianglegood,trianglegoodobbox
import vtk

class RemeshModel(BaseModel):
    model_updated = pyqtSignal()  # 定義類級別的信號，用於通知模型更新

    def __init__(self):
        super().__init__()  # 調用父類的構造函數
        self.image_file = ""  # 2D圖片文件路徑
        self.reference_file = ""  # 3D參考模型文件路徑
        self.output_folder = ""  # 輸出文件夾路徑
        self.mode = None  # 新增：BB 或 OBB 模式，初始為 None
        self.face = None  # 新增：咬合面、舌側或頰側，初始為 None
        self.rotate_angle = 0  # 新增：旋轉角度，根據面選擇設置

    # 設置3D參考文件
    def set_reference_file(self, file_path):
        if os.path.exists(file_path):  # 檢查文件是否存在
            self.reference_file = file_path  # 設置參考文件路徑
            self.model_updated.emit()  # 發送信號通知模型已更新
            return True
        return False

    # 設置2D圖片文件
    def set_image_file(self, file_path):
        if os.path.exists(file_path):  # 檢查文件是否存在
            self.image_file = file_path  # 設置圖片文件路徑
            self.model_updated.emit()  # 發送信號通知模型已更新
            return True
        return False

    # 新增：設置模式（BB 或 OBB）
    def set_mode(self, mode):
        if mode in ["BB", "OBB"]:  # 確保模式有效
            self.mode = mode
            self.model_updated.emit()  # 發送信號通知模型已更新
            return True
        return False

    # 新增：設置面（咬合面、舌側、頰側）並更新旋轉角度
    def set_face(self, face):
        if self.mode is None:  # 如果未選擇模式，禁止設置面
            return False
        if face in ["咬合面", "舌側", "頰側"]:  # 確保面有效
            self.face = face
            # 根據面設置旋轉角度
            if face == "咬合面":
                self.rotate_angle = 0
            elif face == "舌側":
                self.rotate_angle = 90
            elif face == "頰側":
                self.rotate_angle = -90
            self.model_updated.emit()  # 發送信號通知模型已更新
            return True
        return False

    # 保存3D重建結果
    def save_remesh_file(self, renderer, render2):
        # 檢查是否所有必要文件、路徑、模式和面都已設置
        if self.image_file and self.output_folder and self.reference_file and self.mode and self.face:
            # 清理圖片文件路徑中的多餘引號和空格
            image_file_cleaned = self.image_file.strip("' ").strip()
            # 提取文件名（不含擴展名）
            base_name = os.path.splitext(os.path.basename(image_file_cleaned))[0]
            # 定義輸出STL文件路徑
            output_stl_path = self.output_folder + '/' + base_name + f"_{self.mode}_{self.face}.stl"
            # 使用DentalModelReconstructor進行3D重建，傳入旋轉角度
           # 根據模式選擇不同的重建類
            if self.mode == "BB":
                reconstructor = trianglegood.DentalModelReconstructor(
                    self.image_file, 
                    self.reference_file, 
                    output_stl_path,
                )
            elif self.mode == "OBB":
                reconstructor = trianglegoodobbox.DentalModelReconstructor(
                    self.image_file, 
                    self.reference_file, 
                    output_stl_path,
                )
            reconstructor.reconstruct(self.rotate_angle)  # 執行重建，傳入旋轉角度

            # 平滑處理STL文件
            smoothed_stl_path = os.path.splitext(output_stl_path)[0] + "_smoothed.stl"
            self.smooth_stl(output_stl_path, smoothed_stl_path)  # 平滑處理STL文件

            # 在第二個渲染窗口中顯示重建結果
            readmodel.render_file_in_second_window(render2, smoothed_stl_path)
            return True
        return False  # 如果條件不滿足，返回 False
    
    def smooth_stl(self, input_stl_path, output_stl_path, iterations=20, relaxation_factor=0.2):
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
