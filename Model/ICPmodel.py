# 執行 ICP（Iterative Closest Point）演算法 將這三個模型對齊並輸出整合後的結果 STL。
from PyQt5.QtCore import  pyqtSignal
from .BaseModel import BaseModel
import os
from Otherfunction import readmodel
from ICP import main
from PyQt5.QtCore import pyqtSignal
from .BaseModel import BaseModel
import os
from Otherfunction import readmodel
from ICP import main


class ICPModel(BaseModel):
    # 定義 PyQt 訊號，用於通知 UI 進行更新（例如按鈕啟用或狀態刷新）
    model_updated = pyqtSignal()

    def __init__(self):
        """初始化屬性"""
        super().__init__()  # 呼叫父類的初始化方法
        self.front_file = ""      # 前視模型檔案路徑
        self.left_file = ""       # 左視模型檔案路徑
        self.right_file = ""      # 右視模型檔案路徑
        self.output_folder = ""   # ICP 對齊後輸出資料夾路徑

    # ======================== 設定檔案 ========================
    def set_reference_file(self, file_path, position_type):
        """
        設定對應位置的 STL 檔案。
        position_type 可為：'front', 'left', 'right'
        """
        if os.path.exists(file_path):
            # 根據位置類型儲存路徑
            if position_type == "front":
                self.front_file = file_path
            elif position_type == "left":
                self.left_file = file_path
            elif position_type == "right":
                self.right_file = file_path
            # 發送更新信號
            self.model_updated.emit()
            return True
        return False

    # ======================== 執行 ICP 並顯示結果 ========================
    def save_icp_file(self, renderer, render2):
        """
        執行 ICP 對齊流程，並將結果渲染到第二個視窗。
        """
        # 先重置主渲染視窗（避免舊模型干擾）
        renderer.ResetCamera()
        renderer.GetRenderWindow().Render()

        # 通知 UI 更新
        self.model_updated.emit()

        # 執行 ICP 對齊，並輸出整合後 STL 檔案
        icp_stl = main.process_and_reconstruct(
            self.front_file, self.left_file, self.right_file, self.output_folder
        )

        # 將對齊結果渲染在第二個視窗
        readmodel.render_file_in_second_window(render2, icp_stl)

        # 設定視窗大小（768x768）
        renderer.GetRenderWindow().SetSize(768, 768)

        return True

    # ======================== 渲染輸入模型 ========================
    def render_model_icp(self, renderer):
        """
        將前、左、右三個輸入模型渲染到第一個視窗，並加上光澤與材質效果。
        """
        # 移除現有所有 Actor（清空場景）
        renderer.RemoveAllViewProps()

        # -------- 渲染 front 模型 --------
        if hasattr(self, 'front_file') and self.front_file != '':
            self.model1 = readmodel.load_3d_model(self.front_file)
            self.front_actor = readmodel.create_actor(self.model1, (0.98, 0.98, 0.92))  # 淺灰色
            self.front_actor.GetProperty().SetSpecular(0.5)        # 增加高光
            self.front_actor.GetProperty().SetSpecularPower(20)    # 高光集中
            self.front_actor.GetProperty().SetDiffuse(0.6)         # 柔和散射
            self.front_actor.GetProperty().SetAmbient(0.3)         # 增加環境光
            self.front_actor.GetProperty().SetOpacity(1)           # 完全不透明
            # 計算模型中心點
            self.upper_center = readmodel.calculate_center(self.front_actor)
            renderer.AddActor(self.front_actor)

        # -------- 渲染 left 模型 --------
        if self.left_file:
            self.model2 = readmodel.load_3d_model(self.left_file)
            self.left_actor = readmodel.create_actor(self.model2, (0.98, 0.98, 0.92))
            self.left_actor.GetProperty().SetOpacity(1)
            self.left_actor.GetProperty().SetSpecular(0.5)
            self.left_actor.GetProperty().SetSpecularPower(20)
            self.left_actor.GetProperty().SetDiffuse(0.6)
            self.left_actor.GetProperty().SetAmbient(0.3)
            renderer.AddActor(self.left_actor)

        # -------- 渲染 right 模型 --------
        if self.right_file:
            self.model3 = readmodel.load_3d_model(self.right_file)
            self.right_actor = readmodel.create_actor(self.model3, (0.98, 0.98, 0.92))
            self.right_actor.GetProperty().SetOpacity(1)
            self.right_actor.GetProperty().SetSpecular(1.0)         # 提高高光
            self.right_actor.GetProperty().SetSpecularPower(20)
            self.right_actor.GetProperty().SetDiffuse(0.6)
            self.right_actor.GetProperty().SetAmbient(0.3)
            renderer.AddActor(self.right_actor)

        # 重置相機並刷新渲染器
        renderer.ResetCamera()
        renderer.GetRenderWindow().Render()
