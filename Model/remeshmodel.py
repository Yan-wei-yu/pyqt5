# 提供 2D 影像與 3D 參考模型結合 的流程，重建對應面（咬合面、舌側或頰側）的 3D 模型，並支援 BB（Bounding Box）或 OBB（Oriented Bounding Box） 兩種模式。
# 匯入 PyQt5 模組，用於定義信號
from PyQt5.QtCore import pyqtSignal

# 匯入系統模組 os，用於檔案路徑操作
import os

# 匯入自訂的 BaseModel 類別（MVC 結構中模型的基類）
from .BaseModel import BaseModel

# 匯入自訂模組，負責 3D 模型載入與顯示
from Otherfunction import readmodel, trianglegood, trianglegoodobbox

# 匯入 VTK，用於 3D 資料處理（STL 讀取、平滑）
import vtk


class RemeshModel(BaseModel):
    # 定義 PyQt 信號，用於通知 UI（例如更新渲染或狀態）
    model_updated = pyqtSignal()

    def __init__(self):
        """初始化模型屬性"""
        super().__init__()  # 呼叫父類初始化

        # 檔案與參數屬性
        self.image_file = ""       # 2D 影像檔案路徑
        self.reference_file = ""   # 3D 參考模型檔案路徑
        self.output_folder = ""    # 輸出資料夾路徑
        self.mode = None           # 模式：BB 或 OBB
        self.face = None           # 面：咬合面、舌側或頰側
        self.rotate_angle = 0      # 根據面設定的旋轉角度

    # ==================== 設定檔案與模式 ====================

    def set_reference_file(self, file_path):
        """設定 3D 參考模型檔案"""
        if os.path.exists(file_path):
            self.reference_file = file_path
            self.model_updated.emit()  # 發送更新信號
            return True
        return False

    def set_image_file(self, file_path):
        """設定 2D 影像檔案"""
        if os.path.exists(file_path):
            self.image_file = file_path
            self.model_updated.emit()
            return True
        return False

    def set_mode(self, mode):
        """設定模式（BB 或 OBB）"""
        if mode in ["BB", "OBB"]:
            self.mode = mode
            self.model_updated.emit()
            return True
        return False

    def set_face(self, face):
        """設定重建的牙齒面，並根據面設定旋轉角度"""
        if self.mode is None:  # 模式必須先設定
            return False
        if face in ["咬合面", "舌側", "頰側"]:
            self.face = face
            # 根據選擇的面設定旋轉角度
            if face == "咬合面":
                self.rotate_angle = 0
            elif face == "舌側":
                self.rotate_angle = 90
            elif face == "頰側":
                self.rotate_angle = -90
            self.model_updated.emit()
            return True
        return False

    # ==================== 重建與平滑流程 ====================

    def save_remesh_file(self, renderer, render2):
        """
        執行 3D 重建並平滑 STL，最後顯示在第二視窗。
        """
        # 檢查必要條件：檔案路徑、輸出資料夾、模式與面
        if self.image_file and self.output_folder and self.reference_file and self.mode and self.face:
            # 清理圖片檔案路徑中的多餘符號
            image_file_cleaned = self.image_file.strip("' ").strip()
            # 取得不含副檔名的檔名
            base_name = os.path.splitext(os.path.basename(image_file_cleaned))[0]
            # 定義輸出 STL 檔案路徑
            output_stl_path = self.output_folder + '/' + base_name + f"_{self.mode}_{self.face}.stl"

            # 根據模式選擇不同的重建方法
            if self.mode == "BB":
                reconstructor = trianglegood.DentalModelReconstructor(
                    self.image_file, self.reference_file, output_stl_path
                )
            elif self.mode == "OBB":
                reconstructor = trianglegoodobbox.DentalModelReconstructor(
                    self.image_file, self.reference_file, output_stl_path
                )

            # 執行 3D 重建，並傳入旋轉角度
            reconstructor.reconstruct(self.rotate_angle)

            # 平滑處理 STL
            smoothed_stl_path = os.path.splitext(output_stl_path)[0] + "_smoothed.stl"
            self.smooth_stl(output_stl_path, smoothed_stl_path)

            # 顯示平滑後結果於第二視窗
            readmodel.render_file_in_second_window(render2, smoothed_stl_path)
            return True
        return False

    def smooth_stl(self, input_stl_path, output_stl_path, iterations=20, relaxation_factor=0.2):
        """
        對 STL 模型進行平滑處理：
        - iterations：迭代次數（數值越高越平滑）
        - relaxation_factor：平滑強度（0~1）
        """
        # 讀取 STL
        reader = vtk.vtkSTLReader()
        reader.SetFileName(input_stl_path)

        # VTK 平滑過濾器
        smoother = vtk.vtkSmoothPolyDataFilter()
        smoother.SetInputConnection(reader.GetOutputPort())
        smoother.SetNumberOfIterations(iterations)
        smoother.SetRelaxationFactor(relaxation_factor)
        smoother.FeatureEdgeSmoothingOff()  # 關閉特徵邊平滑
        smoother.BoundarySmoothingOn()      # 啟用邊界平滑
        smoother.Update()

        # 寫出平滑後 STL
        writer = vtk.vtkSTLWriter()
        writer.SetFileName(output_stl_path)
        writer.SetInputConnection(smoother.GetOutputPort())
        writer.Write()
