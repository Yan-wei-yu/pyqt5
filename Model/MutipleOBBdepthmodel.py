from PyQt5.QtCore import pyqtSignal  # 引入 PyQt5 的信號系統
from .BaseModel import BaseModel  # 引入 BaseModel 作為父類
from pathlib import Path  # 引入 pathlib 模組來處理路徑
from Otherfunction import readmodel, pictureedgblack, fillwhite   # 引入外部函數庫中的 readmodel
import os
class OBBBatchDepthModel(BaseModel):
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
                # self.set_model_angle(self.angle)  # 設定模型角度
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
                output_file_path = self.save_depth_map(renderer)  # 儲存深度圖
                readmodel.render_file_in_second_window(render2, output_file_path)  # 在第二視窗中渲染檔案
                self.reset(renderer)  # 重設渲染器
        return True  # 返回 True 表示處理成功

    def save_depth_map(self, renderer):
    # 設定渲染視窗的大小為 256x256 像素
        renderer.GetRenderWindow().SetSize(256, 256)
        
        # 檢查是否設定了 lower_actor 和 output_folder
        if self.lower_actor and self.output_folder:
            # 清理檔案名稱，去除多餘的空格或單引號
            upper_file_cleaned = self.lower_file.strip("' ").strip()
            
            # 從 upper_file_cleaned 中提取檔案的基本名稱（不包含副檔名）
            base_name = os.path.splitext(os.path.basename(upper_file_cleaned))[0]
            
            # 生成輸出的檔案路徑，將 output_folder 與基本名稱和 ".png" 副檔名結合
            output_file_path = self.output_folder + '/' + base_name + ".png"
            
            # 如果 upper_opacity 等於 0，處理上層物件的透明度並進行深度圖處理
            if self.upper_opacity == 0 and  hasattr(self, 'upper_actor'):
                # 設定上層物件的透明度為指定值
                self.upper_actor.GetProperty().SetOpacity(self.upper_opacity)
                
                # 使用幫助函數設定基於 BB（有向邊界框）的相機
                scale_filter = readmodel.setup_camera_with_obb(renderer, renderer.GetRenderWindow(),self.upper_actor,
                                                            None, self.lower_actor, self.upper_opacity, self.angle)
                
                # 儲存深度圖像到輸出的路徑
                readmodel.save_depth_image(output_file_path, scale_filter)
                
                # 獲取圖像邊界並進行處理，將邊界內的區域填充為白色
                bound_image = pictureedgblack.get_image_bound(output_file_path)
                fillwhite.process_image_pair(bound_image, output_file_path, output_file_path)
            
            # 如果 upper_opacity 等於 1，設定上下層物件的透明度並處理深度圖
            elif self.upper_opacity == 1:
                # 設定上層和下層物件的透明度
                self.upper_actor.GetProperty().SetOpacity(self.upper_opacity)
                self.lower_actor.GetProperty().SetOpacity(self.lower_opacity)
                
                # 設定相機，這次使用 upper_center 並處理透明度和角度
                scale_filter = readmodel.setup_camera_with_obb(renderer, renderer.GetRenderWindow(),self.upper_actor,
                                                            self.upper_center, self.lower_actor, self.upper_opacity, self.angle)
                
                # 儲存深度圖像
                readmodel.save_depth_image(output_file_path, scale_filter)
            # 如果只要打舌頰側的話
            else:
                # 使用幫助函數設定基於 BB（有向邊界框）的相機
                scale_filter = readmodel.setup_camera_with_obb(renderer, renderer.GetRenderWindow(),None,
                                                            None, self.lower_actor, self.upper_opacity, self.angle)

                # 儲存深度圖像到輸出的路徑
                readmodel.save_depth_image(output_file_path, scale_filter)
                
                # 獲取圖像邊界並進行處理，將邊界內的區域填充為白色
                bound_image = pictureedgblack.get_image_bound(output_file_path)
                fillwhite.process_image_pair(bound_image, output_file_path, output_file_path)

            
            # 還原渲染視窗大小為 768x768 像素
            renderer.GetRenderWindow().SetSize(768, 768)
            
            # 返回儲存的深度圖像檔案路徑
            return output_file_path
        else:
            # 如果 output_folder 未設定，打印提示訊息
            print("Output folder not set")
        
        # 若未成功執行，返回 None
        return None