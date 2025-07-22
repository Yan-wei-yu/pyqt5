from PyQt5.QtCore import pyqtSignal
from .BaseModel import BaseModel
import os
from Otherfunction import readmodel, singleimgcolor, trianglegood, pictureedgblack, twopicturedege, combineABC
import vtk

class AipredictModel(BaseModel):
    model_updated = pyqtSignal()  # 定義類級別的信號，用於通知模型更新

    # 初始化函數
    def __init__(self):
        super().__init__()  # 調用父類的構造函數
        self.model_folder = ""  # 預訓練模型文件夾路徑
        self.upper_file = ""  # 上顎模型文件路徑
        self.lower_file = ""  # 下顎模型文件路徑
        # self.lower_actor = None  # 下顎模型的演員對象
        # self.upper_actor = None  # 上顎模型的演員對象
        self.upper_opacity = 1.0  # 上顎模型透明度，預設為不透明
        self.lower_opacity = 1.0  # 下顎模型透明度，預設為不透明
        self.output_folder = ""  # 輸出文件夾路徑
        self.angle = 0  # 模型旋轉角度

    # 設置參考文件（上顎或下顎）
    def set_reference_file(self, file_path, position_type):
        if os.path.exists(file_path):  # 檢查文件是否存在
            if position_type == "down":  # 如果是下顎
                self.lower_file = file_path
            else:  # 如果是上顎
                self.upper_file = file_path
            self.model_updated.emit()  # 發送信號通知模型已更新
            return True
        return False

    # 設置預訓練模型文件夾
    def set_model_folder(self, folder_path):
        if os.path.isdir(folder_path):  # 檢查路徑是否為有效目錄
            self.model_folder = folder_path
            self.model_updated.emit()  # 發送信號通知模型已更新
            return True
        return False

    # 保存AI預測結果
    def save_ai_file(self, renderer, render2):
        # 清理文件路徑中的多餘引號和空格
        image_file_cleaned = self.lower_file.strip("' ").strip()
        upimage_file_cleaned = self.upper_file.strip("' ").strip()

        # 提取文件名（不含擴展名）
        base_name = os.path.splitext(os.path.basename(image_file_cleaned))[0]
        base_name_up = os.path.splitext(os.path.basename(upimage_file_cleaned))[0]
        
        renderer.ResetCamera()  # 重置攝像機
        renderer.GetRenderWindow().Render()  # 渲染窗口
        renderer.GetRenderWindow().SetSize(256, 256)  # 設置渲染窗口大小
        self.lower_file_modify = self.output_folder + "/" + base_name + "_modtify.ply"  # 修改後的下顎文件路徑

        # 根據是否有上下顎文件執行不同邏輯
        if self.lower_file and self.output_folder and self.model_folder and self.upper_file:
            # 處理上下顎都存在的情況
            self.upper_opacity = 0  # 隱藏上顎
            self.upper_actor.GetProperty().SetOpacity(self.upper_opacity)
            # 生成下顎的深度圖
            output_file_path_down = self.combine_three_depth(renderer, base_name)
            self.upper_opacity = 1  # 顯示上顎
            self.lower_opacity = 0  # 隱藏下顎
            self.upper_actor.GetProperty().SetOpacity(self.upper_opacity)
            self.lower_actor.GetProperty().SetOpacity(self.lower_opacity)
            # 生成上顎的深度圖
            output_file_path_up = self.combine_three_depth(renderer, base_name_up)
            # 標記邊界點
            pictureedgblack.mark_boundary_points(output_file_path_up, self.output_folder + "/edgeUp", color=(255, 255, 0))
            pictureedgblack.mark_boundary_points(output_file_path_down, self.output_folder + "/edgeDown")
            # 合併上下顎邊界圖，並匯出第三張咬合間隙的圖
            twopicturedege.combine_image(
                self.output_folder + "/edgeDown/" + base_name + "down",
                self.output_folder + "/edgeUp/" + base_name_up,
                self.output_folder + "/combinetwoedge/",
                output_file_path_down,
                output_file_path_up
            )
            predictthree_pic = self.output_folder + "/predict.png"  # 預測圖路徑
            # 合併三張圖片
            combineABC.merge_images(output_file_path_down, output_file_path_up, 
                                    self.output_folder + "/combinetwoedge/" + base_name + "down.png", 
                                    predictthree_pic)
            output_file_path_ai = self.output_folder + '/ai_' + base_name + ".png"  # AI生成圖路徑
            # 使用GAN模型生成AI深度圖
            singleimgcolor.apply_gan_model(self.model_folder, predictthree_pic, output_file_path_ai)
            output_stl_path = self.output_folder + '/ai_' + base_name + ".stl"  # STL文件路徑
            self.upper_opacity = 0  # 隱藏上顎
            self.lower_opacity = 1  # 顯示下顎
            self.upper_actor.GetProperty().SetOpacity(self.upper_opacity)
            self.lower_actor.GetProperty().SetOpacity(self.lower_opacity)
            # 使用重建器生成3D模型
            reconstructor = trianglegood.DentalModelReconstructor(output_file_path_ai, self.lower_file, output_stl_path)
            reconstructor.reconstruct()
            smoothed_stl_path = self.output_folder + '/ai_' + base_name + "_smooth.stl"  # 平滑後STL路徑
            self.smooth_stl(output_stl_path, smoothed_stl_path)  # 平滑處理
            readmodel.render_file_in_second_window(render2, smoothed_stl_path)  # 在第二窗口渲染

        elif self.lower_file and self.output_folder and self.model_folder:
            # 僅處理下顎的情況
            self.upper_opacity = 0  # 隱藏上顎（如果存在）
            # 保存深度圖
            output_file_path = self.save_depth_map(renderer)
            output_file_path_ai = self.output_folder + '/ai_' + base_name + ".png"  # AI生成圖路徑
            # 使用GAN模型生成AI深度圖
            singleimgcolor.apply_gan_model(self.model_folder, output_file_path, output_file_path_ai)
            output_stl_path = self.output_folder + '/ai_' + base_name + ".stl"  # STL文件路徑
            self.SaveCurrentRenderWindowAsPLY(renderer, self.lower_file_modify)  # 保存當前渲染為PLY
            # 使用重建器生成3D模型
            reconstructor = trianglegood.DentalModelReconstructor(output_file_path_ai, self.lower_file_modify, output_stl_path)
            reconstructor.reconstruct()
            smoothed_stl_path = self.output_folder + '/ai_' + base_name + "_smooth.stl"  # 平滑後STL路徑
            self.smooth_stl(output_stl_path, smoothed_stl_path)  # 平滑處理
            readmodel.render_file_in_second_window(render2, smoothed_stl_path)  # 在第二窗口渲染

        # self.model_updated.emit()  # 發送信號通知模型已更新
        renderer.GetRenderWindow().SetSize(768, 768)  # 恢復渲染窗口大小
        return True

    # 平滑STL模型
    def smooth_stl(self, input_stl_path, output_stl_path, iterations=20, relaxation_factor=0.2):
        """對 STL 進行平滑處理"""
        reader = vtk.vtkSTLReader()  # STL文件讀取器
        reader.SetFileName(input_stl_path)
        
        smoother = vtk.vtkSmoothPolyDataFilter()  # 平滑過濾器
        smoother.SetInputConnection(reader.GetOutputPort())
        smoother.SetNumberOfIterations(iterations)  # 設定平滑迭代次數
        smoother.SetRelaxationFactor(relaxation_factor)  # 控制平滑強度
        smoother.FeatureEdgeSmoothingOff()  # 關閉邊緣平滑
        smoother.BoundarySmoothingOn()  # 開啟邊界平滑
        smoother.Update()

        writer = vtk.vtkSTLWriter()  # STL文件寫入器
        writer.SetFileName(output_stl_path)
        writer.SetInputConnection(smoother.GetOutputPort())
        writer.Write()

    # 將當前渲染窗口保存為PLY文件
    def SaveCurrentRenderWindowAsPLY(self, renderer, file_path):
        """
        將當前可見模型從渲染窗口保存為PLY文件。
        提取所有可見演員的PolyData並合併為單一文件。
        """
        append_filter = vtk.vtkAppendPolyData()  # 用於合併多個PolyData
        actor_count = 0

        # 遍歷當前場景中的所有演員
        for actor in renderer.GetActors():
            mapper = actor.GetMapper()
            polydata = mapper.GetInput()
            if polydata:
                clean_filter = vtk.vtkCleanPolyData()  # 清理數據，移除重複點
                clean_filter.SetInputData(polydata)
                clean_filter.Update()
                append_filter.AddInputData(clean_filter.GetOutput())
                actor_count += 1

        if actor_count == 0:
            print("沒有可保存的模型。")
            return

        # 合併並保存
        append_filter.Update()
        ply_writer = vtk.vtkPLYWriter()  # PLY文件寫入器
        ply_writer.SetFileName(file_path)
        ply_writer.SetInputData(append_filter.GetOutput())
        ply_writer.Write()
        print(f"已成功將當前場景模型保存為: {file_path}")