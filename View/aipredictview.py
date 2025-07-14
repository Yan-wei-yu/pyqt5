# 主要目的：此程式碼定義了一個基於 PyQt5 和 VTK 的 `AimodelView` 類，作為圖形用戶界面 (GUI) 視圖，用於 AI 預測功能。它允許用戶選擇上顎和下顎的 3D 缺陷模型、預訓練模型檔案和輸出資料夾，通過下拉選單切換模型（上顎/下顎）以進行高亮顯示，並執行 AI 預測，結果可通過 VTK 渲染器顯示，適用於牙科 3D 模型的 AI 修復場景。

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox  # 導入 PyQt5 的界面元件，用於創建 GUI。
from .baseview import BaseView  # 從當前模組導入 BaseView 基類，AimodelView 繼承自該類。
from PyQt5.QtWidgets import QFileDialog  # 導入 QFileDialog，用於檔案選擇對話框。
import vtk  # 導入 VTK 庫，用於 3D 模型處理和視覺化。
from Selectmodel import forvtkinteractor  # 導入 Selectmodel 模組中的 forvtkinteractor，用於自定義交互樣式。

class AimodelView(BaseView):  # 定義 AimodelView 類，繼承自 BaseView。
    # 初始化函數，設置視圖的基本屬性
    def __init__(self, parent_layout, model, render_widget, renderinput, renderinput2):  # 初始化方法，接收父佈局、模型、渲染窗口部件和兩個渲染輸入。
        # 調用父類的初始化函數
        super().__init__(parent_layout, renderinput, renderinput2)  # 設置父佈局和渲染輸入。
        self.model = model  # 儲存傳入的模型對象，用於處理數據和邏輯。
        self.render_widget = render_widget  # 儲存 VTK 渲染窗口部件，用於交互和顯示。
        # 獲取交互器對象
        self.interactor = self.render_widget.GetRenderWindow().GetInteractor()  # 獲取 VTK 交互器，用於處理用戶交互事件。
        # 當模型更新時觸發視圖更新
        self.model.model_updated.connect(self.update_view)  # 將模型的更新信號連接到 update_view 方法。
        self.area_picker = vtk.vtkAreaPicker()  # 創建 VTK 區域拾取器，用於選擇 3D 模型區域。
        self.render_widget.SetPicker(self.area_picker)  # 將區域拾取器設置到渲染窗口部件。
        # 設置高亮交互樣式
        self.highlight_style = forvtkinteractor.HighlightInteractorStyle(self.interactor, renderinput)  # 創建自定義高亮交互樣式。
        self.interactor.SetInteractorStyle(self.highlight_style)  # 將交互器設置為高亮樣式。

        # 新增模型選擇的下拉選單
        self.model_selector = QComboBox()  # 創建下拉選單，用於選擇上顎或下顎模型。
        self.model_selector.currentIndexChanged.connect(self.switch_model)  # 將選單改變事件連接到 switch_model 方法。

    # 創建AIOBB預測面板
    def create_predict(self, parent_layout, current_panel):  # 創建 AI 預測的 GUI 面板。
        # 如果當前面板存在，則移除
        if current_panel:  # 檢查是否已有當前面板。
            parent_layout.removeWidget(current_panel)  # 移除當前面板以更新界面。

        # 創建帶標題的組框
        panel = QGroupBox("AI預測")  # 創建標題為“AI預測”的 QGroupBox 分組框。
        layout = QVBoxLayout()  # 創建垂直佈局，用於組織 GUI 元件。

        # 模型選擇器佈局
        selector_layout = QHBoxLayout()  # 創建水平佈局，用於模型選擇器。
        selector_label = QLabel("選擇操作模型:")  # 創建標籤“選擇操作模型:”。
        selector_layout.addWidget(selector_label)  # 將標籤添加到佈局。
        selector_layout.addWidget(self.model_selector)  # 將下拉選單添加到佈局。
        layout.addLayout(selector_layout)  # 將模型選擇器佈局添加到主垂直佈局。

        # 創建下顎3D模型文件選擇器
        lower_layout, self.threeddown_file = self.create_file_selector(
            "下顎缺陷3D模型:", panel, "3D Model Files (*.ply *.stl *.obj)", "down"
        )  # 創建下顎缺陷模型檔案選擇器，指定位置類型為“down”。
        # 創建上顎3D模型文件選擇器
        upper_layout, self.threedupper_file = self.create_file_selector(
            "上顎3D模型:", panel, "3D Model Files (*.ply *.stl *.obj)", "up"
        )  # 創建上顎模型檔案選擇器，指定位置類型為“up”。
        layout.addLayout(lower_layout)  # 將下顎選擇佈局添加到主佈局。
        layout.addLayout(upper_layout)  # 將上顎選擇佈局添加到主佈局。

        # 創建預訓練模型文件輸入框
        self.model_file = QLineEdit()  # 創建文本框，用於顯示預訓練模型檔案路徑。
        self.create_file_selection_layout(layout, "預訓練模型:", self.model_file, self.model.set_model_folder)  # 調用基類方法創建預訓練模型檔案選擇佈局。

        # 創建輸出文件夾選擇輸入框
        self.output_folder = QLineEdit()  # 創建文本框，用於顯示輸出資料夾路徑。
        self.create_file_selection_layout(layout, "輸出文件夾:", self.output_folder, self.model.set_output_folder)  # 調用基類方法創建輸出資料夾選擇佈局。

        # 創建並設置保存按鈕
        save_button = QPushButton("AI預測")  # 創建“AI預測”按鈕。
        save_button.clicked.connect(self.save_ai_file)  # 將按鈕點擊事件連接到 save_ai_file 方法。
        layout.addWidget(save_button)  # 將按鈕添加到主佈局。

        panel.setLayout(layout)  # 將佈局設置到分組框。
        parent_layout.addWidget(panel)  # 將分組框添加到父佈局。
        return panel  # 返回創建的面板。

    # 保存AI預測結果
    def save_ai_file(self):  # 保存 AI 預測結果的方法。
        # 調用模型的保存方法並檢查結果
        if self.model.save_ai_file(self.render_input, self.render_input2):  # 調用模型的保存方法，傳遞兩個渲染器。
            print("Depth map saved successfully")  # 如果保存成功，打印成功訊息（訊息可能需調整為“AI prediction saved successfully”）。
        else:
            print("Failed to save depth map")  # 如果保存失敗，打印失敗訊息（同上）。

    # 創建文件選擇器佈局
    def create_file_selector(self, label_text, parent, file_types, position_type):  # 創建檔案選擇器的通用方法。
        layout = QHBoxLayout()  # 創建水平佈局，用於檔案選擇。
        label = QLabel(label_text)  # 創建指定文字的標籤。
        layout.addWidget(label)  # 將標籤添加到佈局。
        file_input = QLineEdit()  # 創建文本框，用於顯示檔案路徑。
        layout.addWidget(file_input)  # 將文本框添加到佈局。
        button = QPushButton("選擇")  # 創建“選擇”按鈕。
        # 綁定按鈕點擊事件到文件選擇函數
        button.clicked.connect(lambda: self.choose_file(file_input, file_types, position_type))  # 將按鈕點擊事件連接到 choose_file 方法，傳遞相關參數。
        layout.addWidget(button)  # 將按鈕添加到佈局。
        return layout, file_input  # 返回佈局和文本框。

    # 更新視圖內容
    def update_view(self):  # 更新 GUI 以反映模型的當前狀態。
        self.render_input.RemoveAllViewProps()  # 清除渲染器中的所有視圖屬性（演員）。
        self.model_file.setText(self.model.model_folder)  # 更新預訓練模型檔案路徑的文本框。
        self.threeddown_file.setText(self.model.lower_file)  # 更新下顎模型檔案路徑的文本框。
        self.threedupper_file.setText(self.model.upper_file)  # 更新上顎模型檔案路徑的文本框。
        self.output_folder.setText(self.model.output_folder)  # 更新輸出資料夾路徑的文本框。
        self.model.render_model(self.render_input)  # 調用模型的渲染方法，顯示模型。
        # 如果下顎文件存在，設置高亮數據
        # 根據當前選擇更新 highlight_style 的 polydata
        self.update_model_selector()  # 更新模型選擇下拉選單。
        if self.model_selector.currentText() == "下顎" and self.model.lower_file != '':  # 如果選擇下顎且檔案存在。
            self.highlight_style.SetPolyData(self.model.model2)  # 設置高亮樣式的 PolyData 為下顎模型。
        elif self.model_selector.currentText() == "上顎" and self.model.upper_file != '':  # 如果選擇上顎且檔案存在。
            self.highlight_style.SetPolyData(self.model.model1)  # 設置高亮樣式的 PolyData 為上顎模型（假設 model1 為上顎）。
        self.render_input.ResetCamera()  # 重置渲染器的攝影機視角。
        self.render_input.GetRenderWindow().Render()  # 重新渲染窗口以顯示更新。

    def update_model_selector(self):  # 動態更新模型選擇下拉選單。
        """動態更新模型選擇選單"""
        self.model_selector.clear()  # 清除下拉選單中的所有選項。
        if self.model.lower_file != '':  # 如果下顎檔案存在。
            self.model_selector.addItem("下顎")  # 添加“下顎”選項。
        if self.model.upper_file != '':  # 如果上顎檔案存在。
            self.model_selector.addItem("上顎")  # 添加“上顎”選項。
        if self.model_selector.count() == 0:  # 如果沒有可選模型。
            self.model_selector.addItem("無模型")  # 添加“無模型”選項。

    def switch_model(self):  # 切換模型時更新高亮顯示。
        """當選擇模型改變時，更新 highlight_style 的 polydata"""
        if self.model_selector.currentText() == "下顎" and self.model.lower_file != '':  # 如果選擇下顎且檔案存在。
            self.highlight_style.SetPolyData(self.model.model2)  # 設置高亮樣式的 PolyData 為下顎模型。
        elif self.model_selector.currentText() == "上顎" and self.model.upper_file != '':  # 如果選擇上顎且檔案存在。
            self.highlight_style.SetPolyData(self.model.model1)  # 設置高亮樣式的 PolyData 為上顎模型（假設 model1 為上顎）。
        self.render_input.GetRenderWindow().Render()  # 重新渲染窗口以顯示更新。

    # 選擇文件並更新模型
    def choose_file(self, line_edit, file_filter, position_type):  # 選擇檔案並更新模型的方法。
        options = QFileDialog.Options()  # 創建 QFileDialog 的選項對象。
        # 打開文件選擇對話框
        file_path, _ = QFileDialog.getOpenFileName(None, "選擇檔案", "", file_filter, options=options)  # 獲取檔案路徑。
        if file_path:  # 如果選擇了有效檔案。
            line_edit.setText(file_path)  # 更新文本框顯示檔案路徑。
            if hasattr(self, 'model'):  # 檢查模型是否存在。
                # 檢查文件是否為支持的3D模型格式
                if any(file_path.lower().endswith(ext) for ext in ['.ply', '.stl', '.obj']):  # 確認檔案格式是否為 .ply、.stl 或 .obj。
                    self.model.set_reference_file(file_path, position_type)  # 調用模型方法設置檔案，根據 position_type（up、down）指定。
        else:  # 如果未選擇有效檔案。
            # 移除下顎演員並重置
            if self.model.lower_actor and position_type == "down":  # 如果是下顎檔案且演員存在。
                self.render_input.RemoveActor(self.model.lower_actor)  # 移除下顎模型的演員。
                self.render_input.ResetCamera()  # 重置攝影機視角。
                self.render_input.GetRenderWindow().Render()  # 重新渲染窗口。
                self.model.lower_file = ""  # 清空下顎檔案路徑。
                self.model.lower_center = None  # 清空下顎模型中心。
                self.model.models_center = None  # 清空模型中心。
            # 移除上顎演員並重置
            if self.model.upper_actor and position_type == "up":  # 如果是上顎檔案且演員存在。
                self.render_input.RemoveActor(self.model.upper_actor)  # 移除上顎模型的演員。
                self.render_input.ResetCamera()  # 重置攝影機視角。
                self.render_input.GetRenderWindow().Render()  # 重新渲染窗口。
                self.model.upper_file = ""  # 清空上顎檔案路徑。
                self.model.upper_center = None  # 清空上顎模型中心。
                self.model.models_center = None  # 清空模型中心。
        self.update_view()  # 更新視圖以反映檔案選擇結果。
        return file_path  # 返回選擇的檔案路徑。