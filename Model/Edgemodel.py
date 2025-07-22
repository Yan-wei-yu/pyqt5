# 將上下顎的邊界檢測結果 合併成一張影像，用於後續分析（如咬合間隙分析）。
from PyQt5.QtCore import pyqtSignal
from .BaseModel import BaseModel
from pathlib import Path
from Otherfunction import readmodel, pictureedgblack, twopicturedege
import os


class EdgeModel(BaseModel):
    # 定義 PyQt 信號，用於當模型更新時通知 UI
    model_updated = pyqtSignal()

    def __init__(self):
        """初始化模型屬性"""
        super().__init__()
        self.upper_file = ""        # 當前處理的上顎檔案路徑
        self.lower_file = ""        # 當前處理的下顎檔案路徑
        self.output_folder = ""     # 輸出結果存放資料夾
        self.upper_files = []       # 上顎檔案列表（批次處理）
        self.lower_files = []       # 下顎檔案列表（批次處理）

    def save_edge_button(self, renderer, render2):
        """
        對上下顎檔案進行邊緣檢測，並將結果渲染到視窗。
        最後，將上下顎邊界檢測結果合併成一張影像。
        
        :param renderer: 第一個渲染窗口（顯示原始模型）
        :param render2: 第二個渲染窗口（顯示邊界標記後模型）
        :return: True 表示處理完成
        """

        # ================== 處理上顎模型 ==================
        for upper_file in self.upper_files:
            # 每次更新第二個視窗內容前先清空舊畫面
            render2.GetRenderWindow().Render()
            render2.ResetCamera()
            render2.RemoveAllViewProps()

            # 重設當前檔案屬性
            self.upper_file = ""
            self.lower_file = ""

            # 組合完整路徑
            self.upper_file = (Path(self.upper_folder) / upper_file).as_posix()

            # 第一個視窗顯示原始模型
            readmodel.render_file_in_second_window(renderer, self.upper_file)

            # 邊界標記（使用黃色邊界），並輸出到 edgeUp 資料夾
            pictureedgblack.mark_boundary_points(
                self.upper_file, self.output_folder + "/edgeUp", color=(255, 255, 0)
            )

            # 第二個視窗顯示標記後的模型
            readmodel.render_file_in_second_window(
                render2, self.output_folder + "/edgeUp/" + upper_file
            )

        # ================== 處理下顎模型 ==================
        for lower_file in self.lower_files:
            # 每次更新第二個視窗內容前先清空舊畫面
            render2.GetRenderWindow().Render()
            render2.ResetCamera()
            render2.RemoveAllViewProps()

            # 重設當前檔案屬性
            self.upper_file = ""
            self.lower_file = ""

            # 組合完整路徑
            self.lower_file = (Path(self.lower_folder) / lower_file).as_posix()

            # 第一個視窗顯示原始模型
            readmodel.render_file_in_second_window(renderer, self.lower_file)

            # 邊界標記（顏色預設），並輸出到 edgeDown 資料夾
            pictureedgblack.mark_boundary_points(
                self.lower_file, self.output_folder + "/edgeDown"
            )

            # 第二個視窗顯示標記後的模型
            readmodel.render_file_in_second_window(
                render2, self.output_folder + "/edgeDown/" + lower_file
            )

        # ================== 合併上下顎邊界 ==================
        # 讀取下顎處理後的檔案列表
        red_image_files = os.listdir(self.output_folder + "/edgeDown/")

        # 將每對上下顎的邊界結果合併成單一影像，輸出到 combinetwoedge 資料夾
        for image in red_image_files:
            twopicturedege.combine_image(
                self.output_folder + "/edgeDown/" + image,  # 下顎邊界影像
                self.output_folder + "/edgeUp/" + image,    # 上顎邊界影像
                self.output_folder + "/combinetwoedge/",    # 輸出資料夾
                (Path(self.lower_folder) / image).as_posix(),  # 下顎原圖路徑
                (Path(self.upper_folder) / image).as_posix(),  # 上顎原圖路徑
            )

        return True
