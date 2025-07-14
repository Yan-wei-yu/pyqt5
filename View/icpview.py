# 主要目的：此程式碼定義了一個基於 PyQt5 和 VTK 的 `ICPView` 類，作為圖形用戶界面 (GUI) 視圖，用於執行 3D 模型的 ICP（迭代最近點）定位操作。它允許用戶選擇咬合面、左側和右側的 3D 模型檔案，設置輸出資料夾，並執行 ICP 定位，最終將結果渲染到 VTK 窗口並保存。

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton  # 導入 PyQt5 的界面元件，用於創建 GUI。
from .baseview import BaseView  # 從當前模組導入 BaseView 基類，ICPView 繼承自該類。
from PyQt5.QtWidgets import QFileDialog  # 導入 QFileDialog，用於檔案選擇對話框。
import vtk  # 導入 VTK 庫，用於 3D 模型處理和視覺化。

class ICPView(BaseView):  # 定義 ICPView 類，繼承自 BaseView。
    def __init__(self, parent_layout, model, render_widget, renderinput, renderinput2):  # 初始化方法，接收父佈局、模型、渲染窗口部件和兩個渲染輸入。
        super().__init__(parent_layout, renderinput, renderinput2)  # 調用基類的初始化方法，設置父佈局和渲染輸入。
        self.model = model  # 儲存傳入的模型對象，用於處理數據和邏輯。
        self.render_widget = render_widget  # 儲存 VTK 渲染窗口部件，用於交互和顯示。
        self.interactor = self.render_widget.GetRenderWindow().GetInteractor()  # 獲取 VTK 交互器，用於處理用戶交互事件。
        model.model_updated.connect(self.update_view)  # 將模型的更新信號連接到 update_view 方法，確保 UI 隨模型更新。
        self.area_picker = vtk.vtkAreaPicker()  # 創建 VTK 區域拾取器，用於選擇 3D 模型區域。
        self.render_widget.SetPicker(self.area_picker)  # 將區域拾取器設置到渲染窗口部件。

    def create_predict(self, parent_layout, current_panel):  # 創建 ICP 定位的 GUI 面板。
        if current_panel:  # 如果當前面板存在。
            parent_layout.removeWidget(current_panel)  # 移除當前面板以更新界面。

        panel = QGroupBox("ICP定位")  # 創建標題為“ICP定位”的 QGroupBox 分組框。
        layout = QVBoxLayout()  # 創建垂直佈局，用於組織 GUI 元件。

        # 咬合面 3D 模型檔案選擇
        front_layout, self.threefront_file = self.create_file_selector(
            "咬合面3D模型:", panel, "3D Model Files (*.ply *.stl *.obj)", "front"
        )  # 創建咬合面模型檔案選擇器，傳遞標籤、面板、檔案類型和位置類型（front）。
        layout.addLayout(front_layout)  # 將咬合面選擇佈局添加到主垂直佈局。

        # 左側 3D 模型檔案選擇
        left_layout, self.threeleft_file = self.create_file_selector(
            "左側3D模型:", panel, "3D Model Files (*.ply *.stl *.obj)", "left"
        )  # 創建左側模型檔案選擇器。

        # 右側 3D 模型檔案選擇
        right_layout, self.threeright_file = self.create_file_selector(
            "右側3D模型:", panel, "3D Model Files (*.ply *.stl *.obj)", "right"
        )  # 創建右側模型檔案選擇器。
        layout.addLayout(front_layout)  # 將咬合面選擇佈局添加到主佈局（重複添加，可能是程式碼錯誤）。
        layout.addLayout(left_layout)  # 將左側選擇佈局添加到主佈局。
        layout.addLayout(right_layout)  # 將右側選擇佈局添加到主佈局。

        # 輸出深度圖文件夾選擇
        self.output_folder = QLineEdit()  # 創建文本框，用於顯示輸出資料夾路徑。
        self.create_file_selection_layout(layout, "輸出文件夾:", self.output_folder, self.model.set_output_folder)  # 調用基類方法創建輸出資料夾選擇佈局。

        # 保存按鈕
        save_button = QPushButton("ICP定位")  # 創建“ICP定位”按鈕。
        save_button.clicked.connect(self.save_icp_file)  # 將按鈕點擊事件連接到 save_icp_file 方法。
        layout.addWidget(save_button)  # 將按鈕添加到主佈局。

        panel.setLayout(layout)  # 將佈局設置到分組框。
        parent_layout.addWidget(panel)  # 將分組框添加到父佈局。
        return panel  # 返回創建的面板。

    def save_icp_file(self):  # 保存 ICP 定位結果的方法。
        if self.model.save_icp_file(self.render_input, self.render_input2):  # 調用模型的保存方法，傳遞兩個渲染器。
            print("ICP successfully")  # 如果保存成功，打印成功訊息。
        else:
            print("Failed to save ICP")  # 如果保存失敗，打印失敗訊息。

    def create_file_selector(self, label_text, parent, file_types, position_type):  # 創建檔案選擇器的通用方法。
        layout = QHBoxLayout()  # 創建水平佈局，用於檔案選擇。
        label = QLabel(label_text)  # 創建指定文字的標籤。
        layout.addWidget(label)  # 將標籤添加到佈局。
        file_input = QLineEdit()  # 創建文本框，用於顯示檔案路徑。
        layout.addWidget(file_input)  # 將文本框添加到佈局。
        button = QPushButton("選擇")  # 創建“選擇”按鈕。
        button.clicked.connect(lambda: self.choose_file(file_input, file_types, position_type))  # 將按鈕點擊事件連接到 choose_file 方法，傳遞相關參數。
        layout.addWidget(button)  # 將按鈕添加到佈局。
        return layout, file_input  # 返回佈局和文本框。

    def update_view(self):  # 更新 GUI 以反映模型的當前狀態。
        self.render_input.RemoveAllViewProps()  # 清除渲染器中的所有視圖屬性（演員）。
        self.threefront_file.setText(self.model.front_file)  # 更新咬合面模型檔案路徑的文本框。
        self.threeleft_file.setText(self.model.left_file)  # 更新左側模型檔案路徑的文本框。
        self.threeright_file.setText(self.model.right_file)  # 更新右側模型檔案路徑的文本框。
        self.output_folder.setText(self.model.output_folder)  # 更新輸出資料夾路徑的文本框。
        self.model.render_model_icp(self.render_input)  # 調用模型的渲染方法，顯示 ICP 定位的模型。
        self.render_input.ResetCamera()  # 重置渲染器的攝影機視角。
        self.render_input.GetRenderWindow().Render()  # 重新渲染窗口以顯示更新。

    def choose_file(self, line_edit, file_filter, position_type):  # 選擇檔案的方法，根據位置類型設置模型檔案。
        options = QFileDialog.Options()  # 創建 QFileDialog 的選項對象。
        file_path, _ = QFileDialog.getOpenFileName(None, "選擇檔案", "", file_filter, options=options)  # 打開檔案選擇對話框，獲取檔案路徑。
        if file_path:  # 如果選擇了有效檔案。
            line_edit.setText(file_path)  # 更新文本框顯示檔案路徑。
            if hasattr(self, 'model'):  # 檢查模型是否存在。
                if any(file_path.lower().endswith(ext) for ext in ['.ply', '.stl', '.obj']):  # 確認檔案格式是否為 .ply、.stl 或 .obj。
                    self.model.set_reference_file(file_path, position_type)  # 調用模型方法設置檔案，根據 position_type（front、left、right）指定。
        else:  # 如果未選擇有效檔案。
            if hasattr(self.model, 'front_file') and self.model.front_file and position_type == "front":  # 如果是咬合面檔案且存在。
                self.render_input.RemoveActor(self.model.front_actor)  # 移除咬合面模型的演員。
                self.render_input.ResetCamera()  # 重置攝影機視角。
                self.render_input.GetRenderWindow().Render()  # 重新渲染窗口。
                self.model.front_file = ""  # 清空模型的咬合面檔案路徑。
            elif hasattr(self.model, 'left_file') and self.model.left_file and position_type == "left":  # 如果是左側檔案且存在。
                self.render_input.RemoveActor(self.model.left_actor)  # 移除左側模型的演員。
                self.render_input.ResetCamera()  # 重置攝影機視角。
                self.render_input.GetRenderWindow().Render()  # 重新渲染窗口。
                self.model.left_file = ""  # 清空模型的左側檔案路徑。
            elif hasattr(self.model, 'right_file') and self.model.right_file and position_type == "right":  # 如果是右側檔案且存在。
                self.render_input.RemoveActor(self.model.right_actor)  # 移除右側模型的演員。
                self.render_input.ResetCamera()  # 重置攝影機視角。
                self.render_input.GetRenderWindow().Render()  # 重新渲染窗口。
                self.model.right_file = ""  # 清空模型的右側檔案路徑。
        self.update_view()  # 更新視圖以反映檔案選擇結果。
        return file_path  # 返回選擇的檔案路徑。