from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox
from .baseview import BaseView  
from PyQt5.QtWidgets import QFileDialog
import vtk
from Selectmodel import forvtkinteractor

class AimodelOBBView(BaseView):
    # 初始化函數，設置視圖的基本屬性
    def __init__(self, parent_layout, model, render_widget, renderinput, renderinput2):
        super().__init__(parent_layout, renderinput, renderinput2)  # 調用父類的初始化函數
        self.model = model  # 儲存模型對象
        self.render_widget = render_widget  # 儲存渲染窗口部件
        # 獲取交互器對象
        self.interactor = self.render_widget.GetRenderWindow().GetInteractor()
        # 當模型更新時觸發視圖更新
        self.model.model_updated.connect(self.update_view)
        self.area_picker = vtk.vtkAreaPicker()  # 創建區域選擇器
        self.render_widget.SetPicker(self.area_picker)  # 設置選擇器到渲染窗口
        # 設置高亮交互樣式
        self.highlight_style = forvtkinteractor.HighlightInteractorStyle(self.interactor,renderinput)
        self.interactor.SetInteractorStyle(self.highlight_style)

        # 新增模型選擇的下拉選單
        self.model_selector = QComboBox()
        self.model_selector.currentIndexChanged.connect(self.switch_model)

    # 創建AIOBB預測面板
    def create_predict(self, parent_layout, current_panel):
        # 如果當前面板存在，則移除
        if current_panel:
            parent_layout.removeWidget(current_panel)

        # 創建帶標題的組框，標題為"AIOBB預測"
        panel = QGroupBox("AIOBB預測")
        layout = QVBoxLayout()  # 創建垂直佈局

        # 模型選擇器佈局
        selector_layout = QHBoxLayout()
        selector_label = QLabel("選擇操作模型:")
        selector_layout.addWidget(selector_label)
        selector_layout.addWidget(self.model_selector)
        layout.addLayout(selector_layout)  # 添加模型選擇器佈局到主佈局

        # 創建下顎3D模型文件選擇器
        lower_layout, self.threeddown_file = self.create_file_selector(
            "下顎缺陷3D模型:", panel, "3D Model Files (*.ply *.stl *.obj)", "down"
        )
        # 創建上顎3D模型文件選擇器
        upper_layout, self.threedupper_file = self.create_file_selector(
            "上顎3D模型:", panel, "3D Model Files (*.ply *.stl *.obj)", "up"
        )
        layout.addLayout(lower_layout)  # 添加下顎佈局到主佈局
        layout.addLayout(upper_layout)  # 添加上顎佈局到主佈局

        # 創建預訓練模型文件輸入框
        self.model_file = QLineEdit()
        self.create_file_selection_layout(layout, "預訓練模型:", self.model_file, self.model.set_model_folder)

        # 創建輸出文件夾選擇輸入框
        self.output_folder = QLineEdit()
        self.create_file_selection_layout(layout, "輸出文件夾:", self.output_folder, self.model.set_output_folder)

        # 創建並設置保存按鈕
        save_button = QPushButton("AIOBB預測")
        save_button.clicked.connect(self.save_ai_file)  # 綁定點擊事件到保存函數
        layout.addWidget(save_button)  # 添加按鈕到佈局

        panel.setLayout(layout)  # 設置面板的佈局
        parent_layout.addWidget(panel)  # 添加面板到父佈局
        return panel  # 返回創建的面板

    # 保存AI預測結果
    def save_ai_file(self):
        # 調用模型的保存方法並檢查結果
        if self.model.save_ai_file(self.render_input, self.render_input2):
            print("Depth map saved successfully")  # 成功保存深度圖
        else:
            print("Failed to save depth map")  # 保存失敗

    # 創建文件選擇器佈局
    def create_file_selector(self, label_text, parent, file_types, position_type):
        layout = QHBoxLayout()  # 創建水平佈局
        label = QLabel(label_text)  # 創建標籤
        layout.addWidget(label)  # 添加標籤到佈局
        file_input = QLineEdit()  # 創建文件輸入框
        layout.addWidget(file_input)  # 添加輸入框到佈局
        button = QPushButton("選擇")  # 創建選擇按鈕
        # 綁定按鈕點擊事件到文件選擇函數
        button.clicked.connect(lambda: self.choose_file(file_input, file_types, position_type))
        layout.addWidget(button)  # 添加按鈕到佈局
        return layout, file_input  # 返回佈局和輸入框

    # 更新視圖內容
    def update_view(self):
        self.render_input.RemoveAllViewProps()  # 清除所有視圖中的演員（actors）
        self.model_file.setText(self.model.model_folder)  # 更新模型文件路徑顯示
        self.threeddown_file.setText(self.model.lower_file)  # 更新下顎文件路徑顯示
        self.threedupper_file.setText(self.model.upper_file)  # 更新上顎文件路徑顯示
        self.output_folder.setText(self.model.output_folder)  # 更新輸出文件夾路徑顯示
        self.model.render_model(self.render_input)  # 渲染模型到視圖
        # 如果下顎文件存在，設置高亮數據
        # 根據當前選擇更新 highlight_style 的 polydata
        self.update_model_selector()
        if self.model_selector.currentText() == "下顎" and self.model.lower_file != '':
            self.highlight_style.SetPolyData(self.model.model2)  # 下顎模型
        elif self.model_selector.currentText() == "上顎" and self.model.upper_file != '':
            self.highlight_style.SetPolyData(self.model.model1)  # 上顎模型 (假設 model1 是上顎)
        self.render_input.ResetCamera()  # 重置攝像機
        self.render_input.GetRenderWindow().Render()  # 渲染窗口

    def update_model_selector(self):
            """動態更新模型選擇選單"""
            self.model_selector.clear()
            if self.model.lower_file != '':
                self.model_selector.addItem("下顎")
            if self.model.upper_file != '':
                self.model_selector.addItem("上顎")
            if self.model_selector.count() == 0:
                self.model_selector.addItem("無模型")

    def switch_model(self):
            """當選擇模型改變時，更新 highlight_style 的 polydata"""
            if self.model_selector.currentText() == "下顎" and self.model.lower_file != '':
                self.highlight_style.SetPolyData(self.model.model2)
            elif self.model_selector.currentText() == "上顎" and self.model.upper_file != '':
                self.highlight_style.SetPolyData(self.model.model1)  # 假設 model1 是上顎模型
            self.render_input.GetRenderWindow().Render()
    # 選擇文件並更新模型
    def choose_file(self, line_edit, file_filter, position_type):
        options = QFileDialog.Options()  # 文件對話框選項
        # 打開文件選擇對話框
        file_path, _ = QFileDialog.getOpenFileName(None, "選擇檔案", "", file_filter, options=options)
        if file_path:  # 如果選擇了文件
            line_edit.setText(file_path)  # 更新輸入框文本
            if hasattr(self, 'model'):  # 檢查模型是否存在
                # 檢查文件是否為支持的3D模型格式
                if any(file_path.lower().endswith(ext) for ext in ['.ply', '.stl', '.obj']):
                    self.model.set_reference_file(file_path, position_type)  # 設置參考文件
        else:  # 如果未選擇文件（取消選擇）
            # 移除下顎演員並重置
            if hasattr(self, 'model.lower_actor'):
                if self.model.lower_actor:
                    self.render_input.RemoveActor(self.model.lower_actor)
                    self.render_input.ResetCamera()
                    self.render_input.GetRenderWindow().Render()
                    self.model.lower_file = ""  # 清空下顎文件路徑
                    self.model.lower_center = None  # 清空下顎中心
                    self.model.models_center = None  # 清空模型中心
                # 移除上顎演員並重置
                if self.model.upper_actor:
                    self.render_input.RemoveActor(self.model.upper_actor)
                    self.render_input.ResetCamera()
                    self.render_input.GetRenderWindow().Render()
                    self.model.upper_file = ""  # 清空上顎文件路徑
                    self.model.upper_center = None  # 清空上顎中心
                    self.model.models_center = None  # 清空模型中心
        self.update_view()  # 更新視圖
        return file_path  # 返回選擇的文件路徑