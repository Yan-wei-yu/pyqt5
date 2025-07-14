# 主要目的：此程式碼定義了一個基於 PyQt5 的 `MutipleDepthView` 類，作為多次創建深度圖的圖形用戶界面 (GUI)。它允許用戶選擇上顎和下顎模型檔案、調整旋轉角度和透明度、設置輸出資料夾，並執行深度圖的生成與保存，適用於牙科 3D 模型處理場景。

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSlider  # 導入 PyQt5 的界面元件，用於創建 GUI。
from PyQt5.QtCore import Qt  # 導入 PyQt5 核心模組，用於設置界面屬性（如滑桿方向）。
from .baseview import BaseView  # 從當前模組導入 BaseView 基類，MutipleDepthView 繼承自該類。

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
        super().__init__(parent_layout, renderinput, renderinput2)  # 調用基類的初始化方法，設置父佈局和渲染輸入。
        self.model = model  # 儲存傳入的模型對象，用於處理數據和邏輯。
        model.model_updated.connect(self.update_view)  # 將模型的更新信號連接到 update_view 方法，確保 UI 隨模型更新。

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
        if current_panel:  # 檢查是否已有當前面板。
            parent_layout.removeWidget(current_panel)  # 移除當前面板以更新界面。

        # 根據 self.model 的類別名稱動態設定 QGroupBox 的標題
        model_class_name = self.model.__class__.__name__  # 獲取模型的類名稱。
        if "OBB" in model_class_name:  # 如果模型名稱包含 "OBB"。
            panel_title = "多次OBB創建深度圖"  # 設置標題為“多次OBB創建深度圖”。
        else:
            panel_title = "多次創建深度圖"  # 否則設置標題為“多次創建深度圖”。

        # 創建分組框並設定標題
        panel = QGroupBox(panel_title)  # 創建標題為 panel_title 的 QGroupBox 分組框。
        layout = QVBoxLayout()  # 創建垂直佈局，用於組織 GUI 元件。

        # 上顎模型檔案選擇
        self.upper_file = QLineEdit()  # 創建文本框，用於顯示上顎模型檔案路徑。
        self.create_file_selection_layout(layout, "上顎檔案:", self.upper_file, self.model.set_upper_folder)  # 調用基類方法創建上顎檔案選擇佈局。

        # 下顎模型檔案選擇
        self.lower_file = QLineEdit()  # 創建文本框，用於顯示下顎模型檔案路徑。
        self.create_file_selection_layout(layout, "下顎檔案:", self.lower_file, self.model.set_lower_folder)  # 調用基類方法創建下顎檔案選擇佈局。

        # 旋轉角度輸入
        angle_layout = QHBoxLayout()  # 創建水平佈局，用於旋轉角度輸入。
        angle_layout.addWidget(QLabel("旋轉角度:"))  # 添加標籤“旋轉角度:”。
        self.angle_input = QLineEdit()  # 創建文本框，用於輸入旋轉角度。
        self.angle_input.setText("0")  # 設置預設旋轉角度為 0。
        self.angle_input.textChanged.connect(self.update_angle)  # 將文本改變事件連接到 update_angle 方法。
        angle_layout.addWidget(self.angle_input)  # 將文本框添加到佈局。
        layout.addLayout(angle_layout)  # 將旋轉角度佈局添加到主垂直佈局。

        # 上顎透明度滑桿
        upper_opacity_layout = QHBoxLayout()  # 創建水平佈局，用於上顎透明度設置。
        upper_opacity_layout.addWidget(QLabel("上顎透明度:"))  # 添加標籤“上顎透明度:”。
        self.upper_opacity = QSlider(Qt.Horizontal)  # 創建水平滑桿，用於調整上顎透明度。
        self.upper_opacity.setRange(0, 1)  # 設置滑桿範圍為 0 到 1。
        self.upper_opacity.setValue(1)  # 設置預設值為 1（完全不透明）。
        self.upper_opacity.valueChanged.connect(self.update_upper_opacity)  # 將滑桿值改變事件連接到 update_upper_opacity 方法。
        upper_opacity_layout.addWidget(self.upper_opacity)  # 將滑桿添加到佈局。
        layout.addLayout(upper_opacity_layout)  # 將上顎透明度佈局添加到主垂直佈局。

        # 下顎透明度滑桿
        lower_opacity_layout = QHBoxLayout()  # 創建水平佈局，用於下顎透明度設置。
        lower_opacity_layout.addWidget(QLabel("下顎透明度:"))  # 添加標籤“下顎透明度:”。
        self.lower_opacity = QSlider(Qt.Horizontal)  # 創建水平滑桿，用於調整下顎透明度。
        self.lower_opacity.setRange(0, 1)  # 設置滑桿範圍為 0 到 1。
        self.lower_opacity.setValue(1)  # 設置預設值為 1（完全不透明）。
        self.lower_opacity.valueChanged.connect(self.update_lower_opacity)  # 將滑桿值改變事件連接到 update_lower_opacity 方法。
        lower_opacity_layout.addWidget(self.lower_opacity)  # 將滑桿添加到佈局。
        layout.addLayout(lower_opacity_layout)  # 將下顎透明度佈局添加到主垂直佈局。

        # 輸出深度圖文件夾選擇
        self.output_folder = QLineEdit()  # 創建文本框，用於顯示輸出資料夾路徑。
        self.create_file_selection_layout(layout, "輸出文件夾:", self.output_folder, self.model.set_output_folder)  # 調用基類方法創建輸出資料夾選擇佈局。

        # 保存按鈕
        save_button = QPushButton("保存深度圖")  # 創建“保存深度圖”按鈕。
        save_button.clicked.connect(self.save_depth_maps)  # 將按鈕點擊事件連接到 save_depth_maps 方法。
        layout.addWidget(save_button)  # 將按鈕添加到主佈局。

        # 設定面板佈局並加入父佈局
        panel.setLayout(layout)  # 將佈局設置到分組框。
        parent_layout.addWidget(panel)  # 將分組框添加到父佈局。
        return panel  # 返回創建的面板。

    def update_view(self):
        """
        更新 UI，確保界面數據與 model 保持同步。
        """
        self.upper_file.setText(self.model.upper_folder)  # 更新上顎模型檔案路徑的文本框。
        self.lower_file.setText(self.model.lower_folder)  # 更新下顎模型檔案路徑的文本框。
        self.angle_input.setText(str(self.model.angle))  # 更新旋轉角度文本框，確保與模型同步。
        self.output_folder.setText(self.model.output_folder)  # 更新輸出資料夾路徑的文本框。

        # 由於透明度滑塊的值應為整數，這裡先轉換
        self.upper_opacity.setValue(int(self.model.upper_opacity))  # 更新上顎透明度滑桿值。
        self.lower_opacity.setValue(int(self.model.lower_opacity))  # 更新下顎透明度滑桿值。

        # 更新 VTK 渲染器，重新整理畫面
        self.render_input.ResetCamera()  # 重置渲染器的攝影機視角。
        self.render_input.GetRenderWindow().Render()  # 重新渲染窗口以顯示更新。

    def update_upper_opacity(self):
        """
        更新上顎模型的透明度，並同步到 model。
        """
        opacity = self.upper_opacity.value()  # 獲取上顎透明度滑桿的值。
        self.model.set_upper_opacity(opacity)  # 調用模型方法設置上顎透明度。

    def update_lower_opacity(self):
        """
        更新下顎模型的透明度，並同步到 model。
        """
        opacity = self.lower_opacity.value()  # 獲取下顎透明度滑桿的值。
        self.model.set_lower_opacity(opacity)  # 調用模型方法設置下顎透明度。

    def save_depth_maps(self):
        """
        觸發 model 來保存深度圖，並在終端顯示結果。
        """
        if self.model.save_depth_map_button(self.render_input, self.render_input2):  # 調用模型的保存方法，傳遞兩個渲染器。
            print("Depth map saved successfully")  # 如果保存成功，打印成功訊息。
        else:
            print("Failed to save depth map")  # 如果保存失敗，打印失敗訊息。