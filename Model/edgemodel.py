from PyQt5.QtCore import pyqtSignal
from .BaseModel import BaseModel
from pathlib import Path
from Otherfunction import readmodel, pictureedgblack, twopicturedege
import os

class EdgeModel(BaseModel):
    model_updated = pyqtSignal()  # 定義 PyQt 訊號，當模型更新時可發送此訊號

    def __init__(self):
        super().__init__()  # 調用父類別的構造函數
        self.upper_file = ""  # 上顎檔案路徑
        self.lower_file = ""  # 下顎檔案路徑
        self.output_folder = ""  # 輸出資料夾路徑
        self.upper_files = []  # 上顎檔案列表
        self.lower_files = []  # 下顎檔案列表

    def save_edge_button(self, renderer, render2):
        """
        對上下顎檔案進行邊緣檢測並合併結果。
        :param renderer: 第一個渲染窗口
        :param render2: 第二個渲染窗口
        :return: True 表示處理完成
        """
        # 處理上顎檔案
        for upper_file in self.upper_files:
            render2.GetRenderWindow().Render()
            render2.ResetCamera()
            render2.RemoveAllViewProps()  # 清除視圖內容
            self.upper_file = ""
            self.lower_file = ""
            
            # 設定當前處理的上顎檔案
            self.upper_file = (Path(self.upper_folder) / upper_file).as_posix()
            
            # 在第一個視窗中渲染模型
            readmodel.render_file_in_second_window(renderer, self.upper_file)
            
            # 標記上顎邊界點並存入對應資料夾
            pictureedgblack.mark_boundary_points(
                self.upper_file, self.output_folder + "/edgeUp", color=(255, 255, 0)
            )
            
            # 在第二個視窗中渲染標記後的模型
            readmodel.render_file_in_second_window(
                render2, self.output_folder + "/edgeUp/" + upper_file
            )
        
        # 處理下顎檔案
        for lower_file in self.lower_files:
            render2.GetRenderWindow().Render()
            render2.ResetCamera()
            render2.RemoveAllViewProps()  # 清除視圖內容
            self.upper_file = ""
            self.lower_file = ""
            # 設定當前處理的下顎檔案
            self.lower_file = (Path(self.lower_folder) / lower_file).as_posix()
            
            # 在第一個視窗中渲染模型
            readmodel.render_file_in_second_window(renderer, self.lower_file)
            
            # 標記下顎邊界點並存入對應資料夾
            pictureedgblack.mark_boundary_points(
                self.lower_file, self.output_folder + "/edgeDown"
            )
            
            # 在第二個視窗中渲染標記後的模型
            readmodel.render_file_in_second_window(
                render2, self.output_folder + "/edgeDown/" + lower_file
            )
        
        # 讀取標記後的下顎影像檔案
        red_image_files = os.listdir(self.output_folder + "/edgeDown/")
        
        # 合併上下顎邊界圖，並匯出第三張咬合間隙的圖
        for image in red_image_files:
            twopicturedege.combine_image(
                self.output_folder + "/edgeDown/" + image,
                self.output_folder + "/edgeUp/" + image,
                self.output_folder + "/combinetwoedge/",
                (Path(self.lower_folder) / image).as_posix(),
                (Path(self.upper_folder) / image).as_posix(),
            )
        
        return True
