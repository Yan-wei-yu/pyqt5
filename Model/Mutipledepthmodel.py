from PyQt5.QtCore import pyqtSignal  # 引入 PyQt5 的信號系統
from .BaseModel import BaseModel  # 引入 BaseModel 作為父類
from pathlib import Path  # 引入 pathlib 模組來處理路徑
from Otherfunction import readmodel  # 引入外部函數庫中的 readmodel

class BatchDepthModel(BaseModel):
    model_updated = pyqtSignal()  # 定義一個模型更新的信號

    def __init__(self):
        super().__init__()  # 呼叫父類別的構造函數
        # 初始化屬性
        self.upper_folder = ""  # 上層資料夾路徑
        self.lower_folder = ""  # 下層資料夾路徑
        self.angle = 0  # 模型角度設置，初始為0
        self.output_folder = ""  # 輸出資料夾路徑
        self.upper_opacity = 1.0  # 上層模型的透明度，預設為1.0（完全不透明）
        self.lower_opacity = 1.0  # 下層模型的透明度，預設為1.0（完全不透明）
        self.upper_files = []  # 上層模型檔案列表
        self.lower_files = []  # 下層模型檔案列表

    # 設定上層模型的透明度
    def set_upper_opacity(self, opacity):
        self.upper_opacity = opacity  # 設定上層透明度
        self.model_updated.emit()  # 發送模型更新信號

    # 設定下層模型的透明度
    def set_lower_opacity(self, opacity):
        self.lower_opacity = opacity  # 設定下層透明度
        self.model_updated.emit()  # 發送模型更新信號

    # 儲存深度圖按鈕的處理邏輯
    def save_depth_map_button(self, renderer, render2):
        if self.upper_folder == "":  # 如果沒有設定上層資料夾
            # 對每個下層檔案進行處理
            for lower_file in self.lower_files:
                render2.GetRenderWindow().Render()  # 渲染視窗
                render2.ResetCamera()  # 重設相機
                render2.RemoveAllViewProps()  # 移除所有視覺屬性
                # 設定下層檔案路徑
                self.lower_file = (Path(self.lower_folder) / lower_file).as_posix()
                if not self.lower_file:
                    pass  # 如果沒有檔案，跳過
                if self.lower_file:
                    self.render_model(renderer)  # 渲染模型
                self.set_model_angle(self.angle)  # 設定模型角度
                output_file_path = self.save_depth_map(renderer)  # 儲存深度圖
                readmodel.render_file_in_second_window(render2, output_file_path)  # 在第二視窗中渲染檔案
                self.reset(renderer)  # 重設渲染器
        else:  # 如果設定了上層資料夾
            # 同時處理上層和下層的每對檔案
            for upper_file, lower_file in zip(self.upper_files, self.lower_files):
                render2.GetRenderWindow().Render()  # 渲染視窗
                render2.ResetCamera()  # 重設相機
                render2.RemoveAllViewProps()  # 移除所有視覺屬性
                # 設定上層和下層檔案路徑
                self.upper_file = (Path(self.upper_folder) / upper_file).as_posix()
                self.lower_file = (Path(self.lower_folder) / lower_file).as_posix()
                if not self.lower_file:
                    pass  # 如果沒有下層檔案，跳過
                if self.lower_file:
                    self.render_model(renderer)  # 渲染下層模型
                if self.upper_file:
                    self.render_model(renderer)  # 渲染上層模型
                self.set_model_angle(self.angle)  # 設定模型角度
                output_file_path = self.save_depth_map(renderer)  # 儲存深度圖
                readmodel.render_file_in_second_window(render2, output_file_path)  # 在第二視窗中渲染檔案
                self.reset(renderer)  # 重設渲染器
        return True  # 返回 True 表示處理成功
