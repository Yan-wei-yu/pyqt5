# 主要目的：此程式碼定義了一個基於 PyQt5 和 VTK 的 `StitchView` 類，用於實現 3D 模型縫合功能。它提供了一個圖形用戶界面 (GUI)，允許用戶選擇缺陷模型和 AI 平滑模型，設置輸出資料夾，執行 ICP 配準、裁剪模型、點選交互，並視覺化裁剪結果，最終保存縫合模型。

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton  # 導入 PyQt5 的界面元件，用於創建 GUI。
from .baseview import BaseView  # 從當前模組導入 BaseView 基類，StitchView 繼承自該類。
import vtk  # 導入 VTK 庫，用於 3D 模型處理和視覺化。

class StitchView(BaseView):  # 定義 StitchView 類，繼承自 BaseView。
    def __init__(self, parent_layout, model, renderinput, renderinput2, interactor):  # 初始化方法，接收父佈局、模型、兩個渲染輸入和交互器。
        super().__init__(parent_layout, renderinput, renderinput2)  # 調用基類的初始化方法，設置父佈局和渲染輸入。
        self.model = model  # 儲存傳入的模型對象，用於處理數據和邏輯。
        self.model.model_updated.connect(self.update_view)  # 將模型的更新信號連接到 update_view 方法，與 SingleDepthView 保持一致。
        self.interactor = interactor  # 儲存 VTK 交互器，用於處理用戶交互事件。
        self.render_input = renderinput  # 儲存第一個渲染輸入（VTK 渲染器）。
        self.collect_point = []  # 初始化列表，用於儲存用戶點選的 3D 點座標。
        self.spheres_actor = []  # 初始化列表，用於儲存點選位置的球體演員（VTK Actor）。

    def create_stitch(self, parent_layout, current_panel):  # 創建縫合模型的 GUI 面板。
        if current_panel:  # 如果當前面板存在。
            parent_layout.removeWidget(current_panel)  # 移除當前面板以更新界面。

        panel = QGroupBox("縫合模型")  # 創建標題為“縫合模型”的 QGroupBox 分組框。
        layout = QVBoxLayout()  # 創建垂直佈局，用於組織 GUI 元件。

        # 缺陷模型檔案選擇
        prepare_layout = QHBoxLayout()  # 創建水平佈局，用於缺陷模型檔案選擇。
        prepare_layout.addWidget(QLabel("缺陷模型:"))  # 添加標籤“缺陷模型:”。
        self.prepare_file = QLineEdit()  # 創建文本框，用於顯示缺陷模型檔案路徑。
        prepare_layout.addWidget(self.prepare_file)  # 將文本框添加到佈局。
        prepare_button = QPushButton("選擇")  # 創建“選擇”按鈕。
        prepare_button.clicked.connect(self.choose_prepare_file)  # 將按鈕點擊事件連接到選擇檔案方法。
        prepare_layout.addWidget(prepare_button)  # 將按鈕添加到佈局。
        layout.addLayout(prepare_layout)  # 將水平佈局添加到主垂直佈局。

        # AIsmooth 模型檔案選擇
        smooth_layout = QHBoxLayout()  # 創建水平佈局，用於 AI 平滑模型檔案選擇。
        smooth_layout.addWidget(QLabel("AIsmooth模型:"))  # 添加標籤“AIsmooth模型:”。
        self.smooth_ai_file = QLineEdit()  # 創建文本框，用於顯示 AI 平滑模型檔案路徑。
        smooth_layout.addWidget(self.smooth_ai_file)  # 將文本框添加到佈局。
        smooth_button = QPushButton("選擇")  # 創建“選擇”按鈕。
        smooth_button.clicked.connect(self.choose_smooth_ai_file)  # 將按鈕點擊事件連接到選擇檔案方法。
        smooth_layout.addWidget(smooth_button)  # 將按鈕添加到佈局。
        layout.addLayout(smooth_layout)  # 將水平佈局添加到主垂直佈局。

        # 輸出資料夾選擇
        self.output_layout = QHBoxLayout()  # 創建水平佈局，用於輸出資料夾選擇。
        self.output_folder = QLineEdit()  # 創建文本框，用於顯示輸出資料夾路徑。
        self.create_file_selection_layout(layout, "輸出文件夾:", self.output_folder, self.model.set_output_folder)  # 調用基類方法創建檔案選擇佈局。

        # icp按鈕
        icp_button = QPushButton("執行ICP")  # 創建“執行ICP”按鈕。
        icp_button.clicked.connect(self.run_icp)  # 將按鈕點擊事件連接到執行 ICP 的方法。
        layout.addWidget(icp_button)  # 將按鈕添加到主佈局。

        # 裁剪按鈕
        crop_button = QPushButton("裁剪模型")  # 創建“裁剪模型”按鈕。
        crop_button.clicked.connect(self.crop_controller)  # 將按鈕點擊事件連接到裁剪模型方法。
        layout.addWidget(crop_button)  # 將按鈕添加到主佈局。

        # 剪取完成按鈕
        crop_done_button = QPushButton("裁剪完成")  # 創建“裁剪完成”按鈕。
        crop_done_button.clicked.connect(self.crop_complete)  # 將按鈕點擊事件連接到完成裁剪方法。
        layout.addWidget(crop_done_button)  # 將按鈕添加到主佈局。

        # 保存按鈕
        save_button = QPushButton("保存縫合結果")  # 創建“保存縫合結果”按鈕。
        save_button.clicked.connect(self.save_stitch_model)  # 將按鈕點擊事件連接到保存縫合結果方法。
        layout.addWidget(save_button)  # 將按鈕添加到主佈局。

        panel.setLayout(layout)  # 將佈局設置到分組框。
        parent_layout.addWidget(panel)  # 將分組框添加到父佈局。
        return panel  # 返回創建的面板。

    def choose_prepare_file(self):  # 選擇缺陷模型檔案的方法。
        file_path = self.choose_file(self.prepare_file, "3D Model Files (*.ply *.stl *.obj)")  # 調用基類方法選擇檔案，支援 .ply、.stl、.obj 格式。
        if file_path and self.model.set_prepare_file(file_path):  # 如果選擇了有效檔案且模型成功設置檔案。
            self.model.render_model(self.render_input)  # 調用模型的渲染方法在渲染器中顯示模型。
        else:  # 如果檔案無效或設置失敗。
            if hasattr(self.model, 'prepare_actor') and self.model.prepare_actor:  # 檢查模型是否有 prepare_actor 且不為空。
                self.render_input.RemoveActor(self.model.prepare_actor)  # 移除缺陷模型的演員。
                self.render_input.ResetCamera()  # 重置攝影機視角。
                self.render_input.GetRenderWindow().Render()  # 重新渲染窗口。
            self.model.prepare_file = ""  # 清空模型的檔案路徑。
            self.prepare_file.setText("")  # 清空文本框內容。

    def choose_smooth_ai_file(self):  # 選擇 AI 平滑模型檔案的方法。
        file_path = self.choose_file(self.smooth_ai_file, "3D Model Files (*.ply *.stl *.obj)")  # 調用基類方法選擇檔案，支援 .ply、.stl、.obj 格式。
        if file_path and self.model.set_smooth_ai_file(file_path):  # 如果選擇了有效檔案且模型成功設置檔案。
            self.model.render_model(self.render_input)  # 調用模型的渲染方法在渲染器中顯示模型。
        else:  # 如果檔案無效或設置失敗。
            if hasattr(self.model, 'smooth_ai_actor') and self.model.smooth_ai_actor:  # 檢查模型是否有 smooth_ai_actor 且不為空。
                self.render_input.RemoveActor(self.model.smooth_ai_actor)  # 移除 AI 平滑模型的演員。
                self.render_input.ResetCamera()  # 重置攝影機視角。
                self.render_input.GetRenderWindow().Render()  # 重新渲染窗口。
            self.model.smooth_ai_file = ""  # 清空模型的檔案路徑。
            self.smooth_ai_file.setText("")  # 清空文本框內容。

    def update_view(self):  # 更新 GUI 以反映模型的當前狀態。
        self.prepare_file.setText(self.model.prepare_file)  # 更新缺陷模型檔案路徑的文本框。
        self.smooth_ai_file.setText(self.model.smooth_ai_file)  # 更新 AI 平滑模型檔案路徑的文本框。
        self.output_folder.setText(self.model.output_folder)  # 更新輸出資料夾路徑的文本框。

    def save_stitch_model(self):  # 保存縫合結果的方法。
        if self.model.save_stitch_button(self.render_input, self.render_input2):  # 調用模型的保存方法，傳遞兩個渲染器。
            print("Stitch saved successfully")  # 如果保存成功，打印成功訊息。
        else:
            print("Failed to save depth map")  # 如果保存失敗，打印失敗訊息。

    def run_icp(self):  # 執行 ICP（迭代最近點）配準的方法。
        if self.model.run_icp_button(self.render_input):  # 調用模型的 ICP 方法，傳遞渲染器。
            print("ICP executed successfully")  # 如果執行成功，打印成功訊息。
        else:
            print("Failed to execute ICP")  # 如果執行失敗，打印失敗訊息。

    def crop_controller(self):  # 啟動裁剪模型的控制器方法。
        self.enable_point_selection(self.model.target_output_actor)  # 啟用點選功能，指定目標演員。

    def crop_complete(self):  # 完成裁剪操作的方法。
        if self.model.crop_complete(self.collect_point):  # 調用模型的裁剪完成方法，傳遞收集的點。
            print("Cropping completed successfully")  # 如果裁剪成功，打印成功訊息。
            self.clean()  # 清除已選取的點和球體。
        else:
            print("Failed to complete cropping")  # 如果裁剪失敗，打印失敗訊息。

    def enable_point_selection(self, actor_to_pick=None):  # 啟用點選交互功能。
        self.interactive_actor = actor_to_pick  # 設置可交互的演員（VTK Actor）。
        self.interactor.AddObserver("RightButtonPressEvent", self._on_left_click)  # 添加右鍵點擊事件監聽器，連接到 _on_left_click 方法。

    def compute_curvature_and_visualize(self):  # 計算曲率並視覺化選取點的連線。
        points = vtk.vtkPoints()  # 創建 VTK 點集合。
        for point in self.collect_point:  # 遍歷收集的點。
            points.InsertNextPoint(point)  # 將點添加到 VTK 點集合。
        polyData = vtk.vtkPolyData()  # 創建 VTK PolyData 對象。
        polyData.SetPoints(points)  # 設置點集合到 PolyData。

        # 線段
        line = vtk.vtkCellArray()  # 創建 VTK 單元陣列，用於儲存線段。
        polyline = vtk.vtkPolyLine()  # 創建 VTK 折線對象。
        polyline.GetPointIds().SetNumberOfIds(points.GetNumberOfPoints())  # 設置折線的點數量。
        for i in range(points.GetNumberOfPoints()):  # 遍歷點集合。
            polyline.GetPointIds().SetId(i, i)  # 將點索引添加到折線。
        line.InsertNextCell(polyline)  # 將折線添加到單元陣列。
        polyData.SetLines(line)  # 設置 PolyData 的線段。

        # 平滑線段
        spline_filter = vtk.vtkSplineFilter()  # 創建 VTK 樣條濾波器，用於平滑線段。
        spline_filter.SetInputData(polyData)  # 設置輸入 PolyData。
        spline_filter.SetSubdivideToLength()  # 設置細分模式為按長度細分。
        spline_filter.SetLength(0.01)  # 設置細分長度為 0.01。
        spline_filter.Update()  # 更新濾波器以生成平滑線段。
        output_polydata = spline_filter.GetOutput()  # 獲取平滑後的 PolyData。

        # 視覺化
        spline_mapper = vtk.vtkPolyDataMapper()  # 創建 VTK 映射器，將 PolyData 轉換為可視化形式。
        spline_mapper.SetInputData(output_polydata)  # 設置平滑後的 PolyData 作為輸入。
        spline_actor = vtk.vtkActor()  # 創建 VTK 演員。
        spline_actor.SetMapper(spline_mapper)  # 將映射器關聯到演員。
        spline_actor.GetProperty().SetColor(0, 1, 0)  # 設置演員顏色為綠色（RGB: 0, 1, 0）。
        self.render_input.AddActor(spline_actor)  # 將演員添加到渲染器。

    def _on_left_click(self, obj, event):  # 處理左鍵點擊事件（儘管名稱為 _on_left_click，但實際監聽右鍵事件）。
        click_pos = self.interactor.GetEventPosition()  # 獲取點擊位置的螢幕座標。
        picker = vtk.vtkPropPicker()  # 創建 VTK 拾取器，用於拾取點擊的對象。
        picker.Pick(click_pos[0], click_pos[1], 0, self.render_input)  # 在點擊位置執行拾取。
        picked_actor = picker.GetActor()  # 獲取拾取到的演員。

        if hasattr(self, 'interactive_actor') and picked_actor != self.interactive_actor:  # 檢查是否拾取到指定的交互演員。
            return  # 如果拾取到的演員不匹配，則退出。

        world_point = picker.GetPickPosition()  # 獲取拾取點的世界座標。

        sphere = vtk.vtkSphereSource()  # 創建 VTK 球體源，用於標記點選位置。
        sphere.SetCenter(world_point)  # 設置球體中心為拾取點。
        sphere.SetRadius(0.01)  # 設置球體半徑為 0.01。
        sphere.Update()  # 更新球體源。
        sphere_mapper = vtk.vtkPolyDataMapper()  # 創建映射器，將球體數據轉換為可視化形式。
        sphere_mapper.SetInputConnection(sphere.GetOutputPort())  # 設置球體數據作為輸入。
        sphere_actor = vtk.vtkActor()  # 創建球體演員。
        self.spheres_actor.append(sphere_actor)  # 將球體演員添加到列表。
        sphere_actor.SetMapper(sphere_mapper)  # 將映射器關聯到球體演員。
        sphere_actor.GetProperty().SetColor(1, 0, 0)  # 設置球體顏色為紅色（RGB: 1, 0, 0）。
        self.render_input.AddActor(sphere_actor)  # 將球體演員添加到渲染器。

        self.collect_point.append(world_point)  # 將拾取點的世界座標添加到收集點列表。

        self.compute_curvature_and_visualize()  # 調用方法計算曲率並視覺化連線。

        self.render_input.GetRenderWindow().Render()  # 重新渲染窗口以顯示更新。

    def clean(self):  # 清除點選的球體和收集的點。
        for sphere_actor in self.spheres_actor:  # 遍歷球體演員列表。
            self.render_input.RemoveActor(sphere_actor)  # 從渲染器中移除每個球體演員。
        self.spheres_actor.clear()  # 清空球體演員列表。
        self.collect_point.clear()  # 清空收集點列表。