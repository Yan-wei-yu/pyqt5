from PyQt5.QtCore import pyqtSignal  # 引入pyqtSignal，用於在模型狀態變更時發送信號
import os  # 引入os模組來處理文件路徑檢查
from .BaseModel import BaseModel  # 引入BaseModel作為父類別

class SingleDepthModel(BaseModel):
    model_updated = pyqtSignal()  # 定義一個信號，用來通知模型已經更新

    def __init__(self):
        super().__init__()  # 呼叫父類別的構造函數，否則僅繼承不會執行父類別的初始化邏輯
        # 初始化物件的屬性
        self.upper_file = ""  # 上層文件的路徑
        self.lower_file = ""  # 下層文件的路徑
        self.angle = 0  # 角度設置，初始為0
        self.output_folder = ""  # 輸出資料夾的路徑
        self.upper_opacity = 1.0  # 上層模型的透明度，預設為1.0（完全不透明）
        self.lower_opacity = 1.0  # 下層模型的透明度，預設為1.0（完全不透明）
        self.upper_center = None  # 上層模型的中心點，初始為None
        self.lower_center = None  # 下層模型的中心點，初始為None
        self.models_center = None  # 模型總體的中心點，初始為None

    # 設定上層模型的文件
    def set_upper_file(self, file_path):
        if os.path.exists(file_path):  # 檢查文件是否存在
            self.upper_file = file_path  # 設定文件路徑
            self.upper_center = None  # 清空上層模型的中心
            self.models_center = None  # 清空總體模型的中心
            self.model_updated.emit()  # 發送模型更新信號
            return True
        return False  # 如果文件不存在，返回False

    # 設定下層模型的文件
    def set_lower_file(self, file_path):
        if os.path.exists(file_path):  # 檢查文件是否存在
            self.lower_file = file_path  # 設定文件路徑
            self.lower_center = None  # 清空下層模型的中心
            self.models_center = None  # 清空總體模型的中心
            self.model_updated.emit()  # 發送模型更新信號
            return True
        return False  # 如果文件不存在，返回False
    
    # 設定輸出資料夾的路徑
    def set_output_folder(self, file_path):
        if os.path.exists(file_path):  # 檢查資料夾是否存在
            self.output_folder = file_path  # 設定資料夾路徑
            self.model_updated.emit()  # 發送模型更新信號
            return True
        return False  # 如果資料夾不存在，返回False

    # 設定上層模型的透明度
    def set_upper_opacity(self, opacity):
        self.upper_opacity = opacity  # 設定上層透明度
        if hasattr(self, 'upper_actor') and self.upper_actor:  # 如果有設定上層演員
            self.upper_actor.GetProperty().SetOpacity(opacity)  # 設定上層演員的透明度
        self.model_updated.emit()  # 發送模型更新信號

    # 設定下層模型的透明度
    def set_lower_opacity(self, opacity):
        self.lower_opacity = opacity  # 設定下層透明度
        if hasattr(self, 'lower_actor') and self.lower_actor:  # 如果有設定下層演員
            self.lower_actor.GetProperty().SetOpacity(opacity)  # 設定下層演員的透明度
        self.model_updated.emit()  # 發送模型更新信號
