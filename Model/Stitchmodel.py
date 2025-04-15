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

        # 若有設定缺陷模型檔案則載入並渲染
        if self.prepare_file:
            self.prepare_model = readmodel.load_3d_model(self.prepare_file)  # 載入缺陷模型
            self.prepare_actor = readmodel.create_actor(self.prepare_model, (0.98, 0.98, 0.92))  # 設定淺色材質
            self.prepare_actor.GetProperty().SetSpecular(0.5)  # 增加高光
            self.prepare_actor.GetProperty().SetSpecularPower(20)  # 讓光澤更集中
            self.prepare_actor.GetProperty().SetDiffuse(0.6)  # 光線柔和散射
            self.prepare_actor.GetProperty().SetAmbient(0.3)  # 提高環境光影響
            # 目前未實現透明度，若需要可添加 self.prepare_opacity 屬性
            renderer.AddActor(self.prepare_actor)

        # 若有設定AIsmooth模型檔案則載入並渲染
        if self.smooth_ai_file:
            self.smooth_ai_model = readmodel.load_3d_model(self.smooth_ai_file)  # 載入AIsmooth模型
            self.smooth_ai_actor = readmodel.create_actor(self.smooth_ai_model, (0.98, 0.98, 0.92))  # 設定淺色材質
            self.smooth_ai_actor.GetProperty().SetSpecular(0.5)  # 增加高光
            self.smooth_ai_actor.GetProperty().SetSpecularPower(20)  # 讓光澤更集中
            self.smooth_ai_actor.GetProperty().SetDiffuse(0.6)  # 光線柔和散射
            self.smooth_ai_actor.GetProperty().SetAmbient(0.3)  # 提高環境光影響
            # 目前未實現透明度，若需要可添加 self.smooth_ai_opacity 屬性
            renderer.AddActor(self.smooth_ai_actor)

        renderer.ResetCamera()  # 重置相機視角
        renderer.GetRenderWindow().Render()  # 重新渲染畫面

    def save_stitch_button(self, renderer, renderer2):
        """保存縫合結果"""
        if not self.prepare_file or not self.smooth_ai_file or not self.output_folder:
            return False  # 如果缺少必要檔案或輸出資料夾，返回 False
        try:
            processor = stitchmodel.MeshProcessor(self.prepare_file, self.smooth_ai_file, self.output_folder)  # 傳入輸出資料夾
            final_output = processor.process_complete_workflow(thickness=0)  # 執行完整工作流程
            if final_output and os.path.exists(final_output):
                # 在第二個渲染器中顯示結果
                stitched_model = readmodel.load_3d_model(final_output)  # 載入AIsmooth模型
                stitched_actor = readmodel.create_actor(stitched_model, (0.98, 0.98, 0.92))  # 假設 read_3d_file 返回 VTK actor
                if stitched_actor:
                    renderer2.RemoveAllViewProps()  # 清空第二渲染器
                    renderer2.AddActor(stitched_actor)
                    renderer2.ResetCamera()
                    renderer2.GetRenderWindow().Render()
                    print(f"Stitch saved successfully to: {final_output}")
                    return True
            return False
        except Exception as e:
            print(f"Error during stitching: {e}")
            return False