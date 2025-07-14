# 主要目的：此程式碼定義了一個基於 PyQt5 的 `ImageedgeView` 類
# 作為圖形用戶界面 (GUI) 視圖，用於批次創建牙齒邊界線。
# 它允許用戶選擇上顎和下顎圖檔（通常為深度圖或相關影像）、設置輸出資料夾，並執行邊界線生成與保存，結果可通過 VTK 渲染器顯示，適用於牙科影像處理場景。

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton  # 導入 PyQt5 的界面元件，用於創建 GUI。
from .baseview import BaseView  # 從當前模組導入 BaseView 基類，ImageedgeView 繼承自該類。

class ImageedgeView(BaseView):  # 定義 ImageedgeView 類，繼承自 BaseView。
    def __init__(self, parent_layout, model, renderinput, renderinput2):  # 初始化方法，接收父佈局、模型和兩個渲染輸入。
        super().__init__(parent_layout, renderinput, renderinput2)  # 調用基類的初始化方法，設置父佈局和渲染輸入。
        self.model = model  # 儲存傳入的模型對象，用於處理數據和邏輯。

    def create_edge(self, parent_layout, current_panel):  # 創建批次創建牙齒邊界線的 GUI 面板。
        if current_panel:  # 如果當前面板存在。
            parent_layout.removeWidget(current_panel)  # 移除當前面板以更新界面。

        panel = QGroupBox("批次創建牙齒邊界線")  # 創建標題為“批次創建牙齒邊界線”的 QGroupBox 分組框。
        layout = QVBoxLayout()  # 創建垂直佈局，用於組織 GUI 元件。

        # 上顎模型檔案選擇
        self.upper_file = QLineEdit()  # 創建文本框，用於顯示上顎圖檔路徑。
        self.create_file_selection_layout(layout, "上顎圖檔:", self.upper_file, self.model.set_upper_folder)  # 調用基類方法創建上顎圖檔選擇佈局。

        # 下顎模型檔案選擇
        self.lower_file = QLineEdit()  # 創建文本框，用於顯示下顎圖檔路徑。
        self.create_file_selection_layout(layout, "下顎圖檔:", self.lower_file, self.model.set_lower_folder)  # 調用基類方法創建下顎圖檔選擇佈局。

        # 輸出深度圖文件夾選擇
        self.output_layout = QHBoxLayout()  # 創建水平佈局，用於輸出資料夾選擇。
        self.output_folder = QLineEdit()  # 創建文本框，用於顯示輸出資料夾路徑。
        self.create_file_selection_layout(layout, "輸出文件夾:", self.output_folder, self.model.set_output_folder)  # 調用基類方法創建輸出資料夾選擇佈局。

        # 保存按鈕
        save_button = QPushButton("保存邊界線圖")  # 創建“保存邊界線圖”按鈕。
        save_button.clicked.connect(self.save_edge_file)  # 將按鈕點擊事件連接到 save_edge_file 方法。
        layout.addWidget(save_button)  # 將按鈕添加到主佈局。

        panel.setLayout(layout)  # 將佈局設置到分組框。
        parent_layout.addWidget(panel)  # 將分組框添加到父佈局。
        return panel  # 返回創建的面板。

    def update_view(self):  # 更新 GUI 以反映模型的當前狀態。
        self.upper_file.setText(self.model.upper_folder)  # 更新上顎圖檔路徑的文本框。
        self.lower_file.setText(self.model.lower_folder)  # 更新下顎圖檔路徑的文本框。
        self.output_folder.setText(self.model.output_folder)  # 更新輸出資料夾路徑的文本框。

    def save_edge_file(self):  # 保存牙齒邊界線圖的方法。
        if self.model.save_edge_button(self.render_input, self.render_input2):  # 調用模型的保存方法，傳遞兩個渲染器。
            print("Depth map saved successfully")  # 如果保存成功，打印成功訊息。
        else:
            print("Failed to save depth map")  # 如果保存失敗，打印失敗訊息。