from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton
from .baseview import BaseView  
from Otherfunction import readmodel
import numpy as np
import vtk
class StitchView(BaseView):
    def __init__(self, parent_layout, model, renderinput, renderinput2,interactor):
        super().__init__(parent_layout, renderinput, renderinput2)
        self.model = model
        self.model.model_updated.connect(self.update_view)  # 連接到模型的更新信號，與 SingleDepthView 一致
        self.interactor = interactor  # 初始化互動器
        self.render_input = renderinput  # 儲存渲染輸入
        self.collect_point = []
        self.spheres_actor = []  # 儲存點選的球體

    def create_stitch(self, parent_layout, current_panel):
        if current_panel:
            parent_layout.removeWidget(current_panel)

        panel = QGroupBox("縫合模型")
        layout = QVBoxLayout()

        # 缺陷模型檔案選擇
        prepare_layout = QHBoxLayout()  # 創建水平佈局
        prepare_layout.addWidget(QLabel("缺陷模型:"))  # 添加標籤
        self.prepare_file = QLineEdit()  # 創建文本框
        prepare_layout.addWidget(self.prepare_file)  # 添加文本框到佈局
        prepare_button = QPushButton("選擇")  # 創建選擇按鈕
        prepare_button.clicked.connect(self.choose_prepare_file)  # 連接到選擇檔案方法
        prepare_layout.addWidget(prepare_button)  # 添加按鈕到佈局
        layout.addLayout(prepare_layout)  # 添加佈局到主佈局

        # AIsmooth 模型檔案選擇
        smooth_layout = QHBoxLayout()  # 創建水平佈局
        smooth_layout.addWidget(QLabel("AIsmooth模型:"))  # 添加標籤
        self.smooth_ai_file = QLineEdit()  # 創建文本框
        smooth_layout.addWidget(self.smooth_ai_file)  # 添加文本框到佈局
        smooth_button = QPushButton("選擇")  # 創建選擇按鈕
        smooth_button.clicked.connect(self.choose_smooth_ai_file)  # 連接到選擇檔案方法
        smooth_layout.addWidget(smooth_button)  # 添加按鈕到佈局
        layout.addLayout(smooth_layout)  # 添加佈局到主佈局

        # 輸出資料夾選擇
        self.output_layout = QHBoxLayout()  # 創建一個水平佈局用於輸出文件夾選擇
        self.output_folder = QLineEdit()  # 創建一個用於輸入輸出文件夾路徑的文本框
        self.create_file_selection_layout(layout, "輸出文件夾:", self.output_folder, self.model.set_output_folder)  # 調用方法創建文件選擇佈局

        # icp按鈕
        icp_button = QPushButton("執行ICP")
        icp_button.clicked.connect(self.run_icp)  # 連接到執行ICP方法
        layout.addWidget(icp_button)

        # 裁剪按鈕
        crop_button = QPushButton("裁剪模型")
        crop_button.clicked.connect(self.crop_controller) # 連接到裁剪模型方法
        layout.addWidget(crop_button)

        # 剪取完成按鈕
        crop_done_button = QPushButton("裁剪完成")
        crop_done_button.clicked.connect(self.crop_complete)  # 連接到完成裁剪方法
        layout.addWidget(crop_done_button)

        # 保存按鈕
        save_button = QPushButton("保存縫合結果")
        save_button.clicked.connect(self.save_stitch_model)  # 連接到保存縫合結果方法
        layout.addWidget(save_button)  # 添加保存按鈕到佈局

        panel.setLayout(layout)
        parent_layout.addWidget(panel)
        return panel

    def choose_prepare_file(self):
        file_path = self.choose_file(self.prepare_file, "3D Model Files (*.ply *.stl *.obj)")  # 使用與 SingleDepthView 相同的檔案格式
        if file_path and self.model.set_prepare_file(file_path):  # 假設模型有 set_prepare_file 方法
            self.model.render_model(self.render_input)  # 渲染模型
        else:
            # 若無效則移除缺陷模型
            if hasattr(self.model, 'prepare_actor') and self.model.prepare_actor:
                self.render_input.RemoveActor(self.model.prepare_actor)
                self.render_input.ResetCamera()
                self.render_input.GetRenderWindow().Render()
            self.model.prepare_file = ""
            self.prepare_file.setText("")  # 清空文本框

    def choose_smooth_ai_file(self):
        file_path = self.choose_file(self.smooth_ai_file, "3D Model Files (*.ply *.stl *.obj)")  # 使用與 SingleDepthView 相同的檔案格式
        if file_path and self.model.set_smooth_ai_file(file_path):  # 假設模型有 set_smooth_ai_file 方法
            self.model.render_model(self.render_input)  # 渲染模型
        else:
            # 若無效則移除 AIsmooth 模型
            if hasattr(self.model, 'smooth_ai_actor') and self.model.smooth_ai_actor:
                self.render_input.RemoveActor(self.model.smooth_ai_actor)
                self.render_input.ResetCamera()
                self.render_input.GetRenderWindow().Render()
            self.model.smooth_ai_file = ""
            self.smooth_ai_file.setText("")  # 清空文本框


    def update_view(self):
        # 更新 UI 以反映模型的當前狀態
        self.prepare_file.setText(self.model.prepare_file)
        self.smooth_ai_file.setText(self.model.smooth_ai_file)
        self.output_folder.setText(self.model.output_folder)

    def save_stitch_model(self):
        if self.model.save_stitch_button(self.render_input, self.render_input2):
            print("Stitch saved successfully")
        else:
            print("Failed to save depth map")
    def run_icp(self):
        if self.model.run_icp_button(self.render_input):
            print("ICP executed successfully")
        else:
            print("Failed to execute ICP")
    def crop_controller(self):
        self.enable_point_selection(self.model.target_output_actor)  # 啟用點選監聽，指定可互動的 actor
    def crop_complete(self):
        """完成裁剪操作"""
        if self.model.crop_complete(self.collect_point):
            print("Cropping completed successfully")
            self.clean()  # 清除已選取的點和球體
        else:
            print("Failed to complete cropping")
    def enable_point_selection(self, actor_to_pick=None):
        """指定可互動的 actor，並啟用點選監聽"""
        self.interactive_actor = actor_to_pick
        self.interactor.AddObserver("RightButtonPressEvent", self._on_left_click)
    def compute_curvature_and_visualize(self):
        # 取得collect_point的點
        points = vtk.vtkPoints()
        for point in self.collect_point:
            points.InsertNextPoint(point)
        polyData = vtk.vtkPolyData()
        polyData.SetPoints(points)
        # 線段
        line = vtk.vtkCellArray()
        polyline = vtk.vtkPolyLine()
        polyline.GetPointIds().SetNumberOfIds(points.GetNumberOfPoints())
        for i in range(points.GetNumberOfPoints()):
            polyline.GetPointIds().SetId(i, i)
        line.InsertNextCell(polyline)
        polyData.SetLines(line)
        # 平滑線段
        spline_filter = vtk.vtkSplineFilter()
        spline_filter.SetInputData(polyData)
        spline_filter.SetSubdivideToLength()
        spline_filter.SetLength(0.01)
        spline_filter.Update()
        output_polydata = spline_filter.GetOutput()

        # 視覺化
        spline_mapper = vtk.vtkPolyDataMapper()
        spline_mapper.SetInputData(output_polydata)
        spline_actor = vtk.vtkActor()
        spline_actor.SetMapper(spline_mapper)
        spline_actor.GetProperty().SetColor(0, 1, 0)
        self.render_input.AddActor(spline_actor)


    def _on_left_click(self, obj, event):
        click_pos = self.interactor.GetEventPosition()
        picker = vtk.vtkPropPicker()
        picker.Pick(click_pos[0], click_pos[1], 0, self.render_input)
        picked_actor = picker.GetActor()

        if hasattr(self, 'interactive_actor') and picked_actor != self.interactive_actor:
            return

        world_point = picker.GetPickPosition()

        sphere = vtk.vtkSphereSource()
        sphere.SetCenter(world_point)
        sphere.SetRadius(0.01)
        sphere.Update()
        sphere_mapper = vtk.vtkPolyDataMapper()
        sphere_mapper.SetInputConnection(sphere.GetOutputPort())
        sphere_actor = vtk.vtkActor()
        self.spheres_actor.append(sphere_actor)
        sphere_actor.SetMapper(sphere_mapper)
        sphere_actor.GetProperty().SetColor(1, 0, 0)
        self.render_input.AddActor(sphere_actor)

        self.collect_point.append(world_point)

        self.compute_curvature_and_visualize()

        self.render_input.GetRenderWindow().Render()
    def clean(self):
        for sphere_actor in self.spheres_actor:
            self.render_input.RemoveActor(sphere_actor)
        self.spheres_actor.clear()
        self.collect_point.clear()
