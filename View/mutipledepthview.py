from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSlider
from PyQt5.QtCore import Qt
from .baseview import BaseView


class MutipleDepthView(BaseView): 
    """
    MutipleDepthView 負責處理多次創建深度圖的 UI 介面，允許使用者選擇檔案、調整旋轉角度和透明度，
    並最終保存深度圖。

    繼承自 BaseView，並使用 model 來存儲狀態，確保 UI 變更時能即時反映到資料模型中。
    """

    def __init__(self, parent_layout, model, renderinput, renderinput2):
        """
        初始化 MutipleDepthView 類別。

        Args:
            parent_layout (QLayout): PyQt 的父佈局，將 UI 元件添加到此佈局中。
            model (object): 儲存 UI 狀態的數據模型，並處理與深度圖生成相關的邏輯。
            renderinput (vtkRenderer): VTK 渲染器，負責顯示 3D 模型。
            renderinput2 (vtkRenderer): 第二個 VTK 渲染器，可能用於對比或額外顯示數據。
        """
        super().__init__(parent_layout, renderinput, renderinput2)
        self.model = model
        model.model_updated.connect(self.update_view)  # 監聽 model 變更事件，更新 UI

    def create_depth(self, parent_layout, current_panel):
        """
        創建並顯示「多次創建深度圖」的 UI 面板。

        Args:
            parent_layout (QLayout): UI 父佈局。
            current_panel (QWidget or None): 當前面板，若已存在則先移除。
        
        Returns:
            panel (QGroupBox): 創建的 UI 面板。
        """
        # 若當前已有面板，則先移除
        if current_panel:
            parent_layout.removeWidget(current_panel)

        # 根據 self.model 的類別名稱動態設定 QGroupBox 的標題
        model_class_name = self.model.__class__.__name__
        if "OBB" in model_class_name:
            panel_title = "多次OBB創建深度圖"
        else:
            panel_title = "多次創建深度圖"

        # 創建分組框並設定標題
        panel = QGroupBox(panel_title)  # 創建分組框
        layout = QVBoxLayout()  # 設定主佈局為垂直排列

        # 上顎模型檔案選擇
        self.upper_file = QLineEdit()  # 創建文字輸入框
        self.create_file_selection_layout(layout, "上顎檔案:", self.upper_file, self.model.set_upper_folder)

        # 下顎模型檔案選擇
        self.lower_file = QLineEdit()
        self.create_file_selection_layout(layout, "下顎檔案:", self.lower_file, self.model.set_lower_folder)

        # 旋轉角度輸入
        angle_layout = QHBoxLayout()
        angle_layout.addWidget(QLabel("旋轉角度:"))  # 加入標籤
        self.angle_input = QLineEdit()
        self.angle_input.setText("0")  # 預設旋轉角度為 0
        self.angle_input.textChanged.connect(self.update_angle)  # 綁定更新函式
        angle_layout.addWidget(self.angle_input)
        layout.addLayout(angle_layout)

        # 上顎透明度滑桿
        upper_opacity_layout = QHBoxLayout()
        upper_opacity_layout.addWidget(QLabel("上顎透明度:"))
        self.upper_opacity = QSlider(Qt.Horizontal)
        self.upper_opacity.setRange(0, 1)  # 設定範圍 0~1
        self.upper_opacity.setValue(1)  # 預設值為 1（完全不透明）
        self.upper_opacity.valueChanged.connect(self.update_upper_opacity)
        upper_opacity_layout.addWidget(self.upper_opacity)
        layout.addLayout(upper_opacity_layout)

        # 下顎透明度滑桿
        lower_opacity_layout = QHBoxLayout()
        lower_opacity_layout.addWidget(QLabel("下顎透明度:"))
        self.lower_opacity = QSlider(Qt.Horizontal)
        self.lower_opacity.setRange(0, 1)
        self.lower_opacity.setValue(1)
        self.lower_opacity.valueChanged.connect(self.update_lower_opacity)
        lower_opacity_layout.addWidget(self.lower_opacity)
        layout.addLayout(lower_opacity_layout)

        # 輸出深度圖文件夾選擇
        self.output_folder = QLineEdit()
        self.create_file_selection_layout(layout, "輸出文件夾:", self.output_folder, self.model.set_output_folder)

        # 保存按鈕
        save_button = QPushButton("保存深度圖")
        save_button.clicked.connect(self.save_depth_maps)
        layout.addWidget(save_button)

        # 設定面板佈局並加入父佈局
        panel.setLayout(layout)
        parent_layout.addWidget(panel)
        return panel

    def update_view(self):
        """
        更新 UI，確保界面數據與 model 保持同步。
        """
        self.upper_file.setText(self.model.upper_folder)
        self.lower_file.setText(self.model.lower_folder)
        self.angle_input.setText(str(self.model.angle))
        self.output_folder.setText(self.model.output_folder)

        # 由於透明度滑塊的值應為整數，這裡先轉換
        self.upper_opacity.setValue(int(self.model.upper_opacity))
        self.lower_opacity.setValue(int(self.model.lower_opacity))

        # 更新 VTK 渲染器，重新整理畫面
        self.render_input.ResetCamera()
        self.render_input.GetRenderWindow().Render()

    def update_upper_opacity(self):
        """
        更新上顎模型的透明度，並同步到 model。
        """
        opacity = self.upper_opacity.value()
        self.model.set_upper_opacity(opacity)

    def update_lower_opacity(self):
        """
        更新下顎模型的透明度，並同步到 model。
        """
        opacity = self.lower_opacity.value()
        self.model.set_lower_opacity(opacity)

    def save_depth_maps(self):
        """
        觸發 model 來保存深度圖，並在終端顯示結果。
        """
        if self.model.save_depth_map_button(self.render_input, self.render_input2):
            print("Depth map saved successfully")  # 成功儲存
        else:
            print("Failed to save depth map")  # 失敗
