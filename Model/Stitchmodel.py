from PyQt5.QtCore import pyqtSignal
from .BaseModel import BaseModel
import os
from Otherfunction import readmodel
from meshlibStitching import stitchmodel

class StitchModel(BaseModel):
    model_updated = pyqtSignal()  # 定義模型更新信號

    def __init__(self):
        super().__init__()  # 呼叫父類的構造函數
        # 初始化物件的屬性
        self.prepare_file = ""  # 缺陷模型檔案路徑
        self.smooth_ai_file = ""  # AIsmooth模型檔案路徑
        self.output_folder = ""  # 輸出資料夾路徑
        self.prepare_actor = None  # 缺陷模型的渲染演員
        self.smooth_ai_actor = None  # AIsmooth模型的渲染演員

    def set_prepare_file(self, file_path):
        """設置缺陷模型檔案路徑"""
        if os.path.exists(file_path):  # 檢查檔案是否存在
            self.prepare_file = file_path  # 設置檔案路徑
            self.model_updated.emit()  # 發送模型更新信號
            return True
        return False  # 檔案不存在時返回 False

    def set_smooth_ai_file(self, file_path):
        """設置AIsmooth模型檔案路徑"""
        if os.path.exists(file_path):  # 檢查檔案是否存在
            self.smooth_ai_file = file_path  # 設置檔案路徑
            self.model_updated.emit()  # 發送模型更新信號
            return True
        return False  # 檔案不存在時返回 False

    def set_output_folder(self, folder_path):
        """設置輸出資料夾路徑"""
        if os.path.isdir(folder_path):  # 檢查資料夾是否存在
            self.output_folder = folder_path  # 設置資料夾路徑
            self.model_updated.emit()  # 發送模型更新信號
            return True
        return False  # 資料夾不存在時返回 False
    def render_model(self, renderer):
        """渲染缺陷模型和AIsmooth模型"""
        renderer.RemoveAllViewProps()  # 清除所有現有物件
        # readmodel.add_lighting(renderer)

        # 若有設定缺陷模型檔案則載入並渲染
        if self.prepare_file:
            self.prepare_model = readmodel.load_3d_model(self.prepare_file)  # 載入缺陷模型
            self.prepare_actor = readmodel.create_actor(self.prepare_model, (0.98, 0.98, 0.92))  # 設定淺色材質
            renderer.AddActor(self.prepare_actor)

        # 若有設定AIsmooth模型檔案則載入並渲染
        if self.smooth_ai_file:
            self.smooth_ai_model = readmodel.load_3d_model(self.smooth_ai_file)  # 載入AIsmooth模型
            self.smooth_ai_actor = readmodel.create_actor(self.smooth_ai_model, (0.98, 0.98, 0.92))  # 設定淺色材質
            renderer.AddActor(self.smooth_ai_actor)

        renderer.ResetCamera()  # 重置相機視角
        renderer.GetRenderWindow().Render()  # 重新渲染畫面

    def save_stitch_button(self, renderer, renderer2):
        """保存縫合結果"""
        if not self.prepare_file or not self.smooth_ai_file or not self.output_folder:
            return False  # 如果缺少必要檔案或輸出資料夾，返回 False
        processor = stitchmodel.MeshProcessor(self.prepare_file, self.smooth_ai_file, self.output_folder)  # 傳入輸出資料夾
        final_output = processor.process_complete_workflow(thickness=0)  # 執行完整工作流程
        if final_output and os.path.exists(final_output):
            readmodel.render_file_in_second_window(renderer2, final_output)  # 在第二窗口渲染
    def run_icp_button(self, renderer):
        """執行ICP算法進行模型對齊"""
        if not self.prepare_file or not self.smooth_ai_file or not self.output_folder:
            return False
        processor = stitchmodel.MeshProcessor(self.prepare_file, self.smooth_ai_file, self.output_folder)
        self.target_output = processor.run_icp()  # 執行ICP對齊

        # 移除現有的AIsmooth模型
        renderer.RemoveActor(self.smooth_ai_actor)
        self.smooth_ai_actor = None

        self.target_output_actor = readmodel.create_actor(self.target_output, (0.98, 0.98, 0.92))
        self.target_output_actor.GetProperty().SetOpacity(0.8)  # 設定透明度為50%
        renderer.AddActor(self.target_output_actor)  # 添加新的AIsmooth模型到渲染器
        renderer.ResetCamera()  # 重置相機視角
        renderer.GetRenderWindow().Render()  # 重新渲染畫面
    def crop_complete(self,collect_points):
        """完成裁剪操作"""
        if not self.prepare_file or not self.smooth_ai_file or not self.output_folder:
            return False
        processor = stitchmodel.MeshProcessor(self.prepare_file, self.smooth_ai_file, self.output_folder)
        processor.extract_patch_from_points(self.target_output,collect_points)  # 執行裁剪操作




