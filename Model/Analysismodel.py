from PyQt5.QtCore import pyqtSignal
import os
from .BaseModel import BaseModel
from evaluate import elismated, compare

class AnalysisModel(BaseModel):
    model_updated = pyqtSignal()  # 定義類級別的信號，用於通知模型更新

    # 初始化函數
    def __init__(self):
        super().__init__()  # 調用父類的構造函數
        self.groudtruth_file = ""  # 真實圖檔資料夾路徑
        self.result_file = ""  # 修復圖檔資料夾路徑
        self.mask_file = ""  # 遮罩圖檔資料夾路徑
        self.output_folder = ""  # 輸出文件夾路徑

    # 設置真實圖檔資料夾
    def set_groudtruth_folder(self, file_path):
        if os.path.exists(file_path):  # 檢查路徑是否存在
            self.groudtruth_file = file_path  # 設置真實圖檔資料夾路徑
            self.model_updated.emit()  # 發送信號通知模型已更新
            return True
        return False

    # 設置修復圖檔資料夾
    def set_result_folder(self, file_path):
        if os.path.exists(file_path):  # 檢查路徑是否存在
            self.result_file = file_path  # 設置修復圖檔資料夾路徑
            self.model_updated.emit()  # 發送信號通知模型已更新
            return True
        return False

    # 設置遮罩圖檔資料夾
    def set_mask_folder(self, file_path):
        if os.path.exists(file_path):  # 檢查路徑是否存在
            self.mask_file = file_path  # 設置遮罩圖檔資料夾路徑
            self.model_updated.emit()  # 發送信號通知模型已更新
            return True
        return False

    # 設置輸出文件夾
    def set_output_folder(self, file_path):
        if os.path.exists(file_path):  # 檢查路徑是否存在
            self.output_folder = file_path  # 設置輸出文件夾路徑
            self.model_updated.emit()  # 發送信號通知模型已更新
            return True
        return False

    # 保存分析數值
    def save_value_button(self, renderer, render2):
        # 從修復圖檔資料夾路徑中提取基本名稱
        r_value = os.path.basename(os.path.normpath(self.result_file))
        # 定義輸出文件路徑（以修復圖檔名稱為基礎的txt文件）
        output_folder = os.path.join(self.output_folder, f"{r_value}.txt")
        # 調用 elismated.cal_all 計算所有分析數值並保存
        elismated.cal_all(self.groudtruth_file, self.result_file,
                          output_folder, self.mask_file)
        # 調用 compare.compare_image_folders 比較圖像資料夾並保存結果
        compare.compare_image_folders(self.groudtruth_file, self.result_file,
                                      self.output_folder, image_size=(256, 256))
        return True  # 返回True表示操作完成（未檢查實際執行結果）