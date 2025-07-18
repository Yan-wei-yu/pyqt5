# 匯入 PyQt5 的 pyqtSignal，用來定義自訂訊號
from PyQt5.QtCore import pyqtSignal

# 匯入自訂的 BaseModel 類別
from .BaseModel import BaseModel

# 匯入系統模組 os，用於檔案與路徑操作
import os

# 匯入自訂的 readmodel 模組，負責載入及渲染 3D 模型
from Otherfunction import readmodel

# 匯入自訂的 stitchmodel 模組，用於模型縫合、ICP 對齊與裁切功能
from meshlibStitching import stitchmodel


# 定義 StitchModel 類別，繼承 BaseModel
class StitchModel(BaseModel):
    # 定義一個 PyQt 訊號，用於通知模型更新
    model_updated = pyqtSignal()

    def __init__(self):
        # 呼叫父類別(BaseModel)的建構子
        super().__init__()

        # 初始化屬性
        self.prepare_file = ""       # 缺陷模型的檔案路徑
        self.smooth_ai_file = ""     # AI 修復後模型的檔案路徑
        self.output_folder = ""      # 輸出結果存放的資料夾路徑
        self.prepare_actor = None    # 缺陷模型的渲染演員（VTK Actor）
        self.smooth_ai_actor = None  # AI 修復模型的渲染演員（VTK Actor）

    # ---------------------- 設定檔案路徑方法 ----------------------

    def set_prepare_file(self, file_path):
        """設置缺陷模型檔案路徑"""
        if os.path.exists(file_path):  # 檢查檔案是否存在
            self.prepare_file = file_path  # 設置檔案路徑
            self.model_updated.emit()      # 發送「模型更新」訊號
            return True
        return False  # 檔案不存在時返回 False

    def set_smooth_ai_file(self, file_path):
        """設置 AI 修復模型檔案路徑"""
        if os.path.exists(file_path):  # 檢查檔案是否存在
            self.smooth_ai_file = file_path  # 設置檔案路徑
            self.model_updated.emit()        # 發送「模型更新」訊號
            return True
        return False  # 檔案不存在時返回 False

    def set_output_folder(self, folder_path):
        """設置輸出資料夾路徑"""
        if os.path.isdir(folder_path):  # 檢查資料夾是否存在
            self.output_folder = folder_path  # 設置資料夾路徑
            self.model_updated.emit()          # 發送「模型更新」訊號
            return True
        return False  # 資料夾不存在時返回 False

    # ---------------------- 渲染方法 ----------------------

    def render_model(self, renderer):
        """渲染缺陷模型和 AI 修復模型"""
        renderer.RemoveAllViewProps()  # 清除渲染器中的所有現有物件

        # 如果有缺陷模型檔案，載入並渲染
        if self.prepare_file:
            self.prepare_model = readmodel.load_3d_model(self.prepare_file)      # 載入缺陷模型
            self.prepare_actor = readmodel.create_actor(self.prepare_model, (0.98, 0.98, 0.92))  # 建立淺灰色 Actor
            renderer.AddActor(self.prepare_actor)  # 將缺陷模型加入渲染器

        # 如果有 AI 修復模型檔案，載入並渲染
        if self.smooth_ai_file:
            self.smooth_ai_model = readmodel.load_3d_model(self.smooth_ai_file)  # 載入 AI 修復模型
            self.smooth_ai_actor = readmodel.create_actor(self.smooth_ai_model, (0.98, 0.98, 0.92))  # 建立淺灰色 Actor
            renderer.AddActor(self.smooth_ai_actor)  # 將修復模型加入渲染器

        # 重置相機視角並重新渲染畫面
        renderer.ResetCamera()
        renderer.GetRenderWindow().Render()

    # ---------------------- 模型縫合並顯示 ----------------------

    def save_stitch_button(self, renderer, renderer2):
        """保存縫合後的結果並在第二視窗顯示"""
        # 如果缺少必要檔案或資料夾，直接返回 False
        if not self.prepare_file or not self.smooth_ai_file or not self.output_folder:
            return False

        # 建立 MeshProcessor 物件並執行完整縫合流程
        processor = stitchmodel.MeshProcessor(self.prepare_file, self.smooth_ai_file, self.output_folder)
        final_output = processor.process_complete_workflow(thickness=0)  # thickness=0 表示無額外厚度補償

        # 如果縫合結果檔案存在，則在第二個渲染視窗顯示
        if final_output and os.path.exists(final_output):
            readmodel.render_file_in_second_window(renderer2, final_output)

    # ---------------------- ICP 對齊功能 ----------------------

    def run_icp_button(self, renderer):
        """執行 ICP 算法對模型進行對齊"""
        # 檢查必要條件
        if not self.prepare_file or not self.smooth_ai_file or not self.output_folder:
            return False

        # 建立 MeshProcessor 並執行 ICP 對齊
        processor = stitchmodel.MeshProcessor(self.prepare_file, self.smooth_ai_file, self.output_folder)
        self.target_output = processor.run_icp()  # 對齊後模型路徑

        # 移除舊的 AI 修復模型 Actor
        renderer.RemoveActor(self.smooth_ai_actor)
        self.smooth_ai_actor = None

        # 生成新的 Actor，並設定透明度為 0.8（80%）
        self.target_output_actor = readmodel.create_actor(self.target_output, (0.98, 0.98, 0.92))
        self.target_output_actor.GetProperty().SetOpacity(0.8)
        renderer.AddActor(self.target_output_actor)  # 加入新的 Actor

        # 更新畫面
        renderer.ResetCamera()
        renderer.GetRenderWindow().Render()

    # ---------------------- 裁切功能 ----------------------

    def crop_complete(self, collect_points):
        """完成裁切操作"""
        # 檢查必要條件
        if not self.prepare_file or not self.smooth_ai_file or not self.output_folder:
            return False

        # 使用 MeshProcessor 執行基於點的裁切
        processor = stitchmodel.MeshProcessor(self.prepare_file, self.smooth_ai_file, self.output_folder)
        processor.extract_patch_from_points(self.target_output, collect_points)  # 傳入 ICP 對齊後的模型和選擇的點
