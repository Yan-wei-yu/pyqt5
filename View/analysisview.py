# 主要目的：此程式碼定義了一個基於 PyQt5 的 `AnalysisView` 類
# 作為圖形用戶界面 (GUI) 視圖，用於遮罩贋復區域分析。
# 它允許用戶選擇真實圖檔、修復圖檔和遮罩圖檔的資料夾，設置輸出資料夾，並執行分析數值的生成與保存，結果可通過 VTK 渲染器顯示，適用於牙科影像處理場景中的修復效果分析。

from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLineEdit, QPushButton  # 導入 PyQt5 的界面元件，用於創建 GUI。
from .baseview import BaseView  # 從當前模組導入 BaseView 基類，AnalysisView 繼承自該類。

class AnalysisView(BaseView):  # 定義 AnalysisView 類，繼承自 BaseView。
    # 初始化函數，設置視圖的基本屬性
    def __init__(self, parent_layout, model, renderinput, renderinput2):  # 初始化方法，接收父佈局、模型和兩個渲染輸入。
        super().__init__(parent_layout, renderinput, renderinput2)  # 調用基類的初始化方法，設置父佈局和渲染輸入。
        self.model = model  # 儲存傳入的模型對象，用於處理數據和邏輯。

    # 創建遮罩贋復區域分析面板
    def create_edge(self, parent_layout, current_panel):  # 創建遮罩贋復區域分析的 GUI 面板。
        # 如果當前面板存在，則移除
        if current_panel:  # 檢查是否已有當前面板。
            parent_layout.removeWidget(current_panel)  # 移除當前面板以更新界面。

        # 創建帶標題的組框，標題為"遮罩贋復區域分析"
        panel = QGroupBox("遮罩贋復區域分析")  # 創建標題為“遮罩贋復區域分析”的 QGroupBox 分組框。
        layout = QVBoxLayout()  # 創建垂直佈局，用於組織 GUI 元件。

        # 真實圖檔資料夾選擇
        self.groudtruth_file = QLineEdit()  # 創建文本框，用於顯示真實圖檔資料夾路徑。
        self.create_file_selection_layout(layout, "真實圖檔資料夾:", self.groudtruth_file,
                                         self.model.set_groudtruth_folder)  # 調用基類方法創建真實圖檔資料夾選擇佈局。

        # 修復圖檔資料夾選擇
        self.result_file = QLineEdit()  # 創建文本框，用於顯示修復圖檔資料夾路徑。
        self.create_file_selection_layout(layout, "修復圖檔資料夾:", self.result_file,
                                         self.model.set_result_folder)  # 調用基類方法創建修復圖檔資料夾選擇佈局。

        # 遮罩圖檔資料夾選擇
        self.mask_file = QLineEdit()  # 創建文本框，用於顯示遮罩圖檔資料夾路徑。
        self.create_file_selection_layout(layout, "遮罩圖檔資料夾:", self.mask_file,
                                         self.model.set_mask_folder)  # 調用基類方法創建遮罩圖檔資料夾選擇佈局。

        # 輸出文件夾選擇
        self.output_layout = QHBoxLayout()  # 創建水平佈局（未實際使用，可能是遺留代碼）。
        self.output_folder = QLineEdit()  # 創建文本框，用於顯示輸出資料夾路徑。
        self.create_file_selection_layout(layout, "輸出文件夾:", self.output_folder,
                                         self.model.set_output_folder)  # 調用基類方法創建輸出資料夾選擇佈局。

        # 創建並設置保存按鈕
        save_button = QPushButton("保存分析數值")  # 創建“保存分析數值”按鈕。
        save_button.clicked.connect(self.save_value_file)  # 將按鈕點擊事件連接到 save_value_file 方法。
        layout.addWidget(save_button)  # 將按鈕添加到主佈局。

        panel.setLayout(layout)  # 將佈局設置到分組框。
        parent_layout.addWidget(panel)  # 將分組框添加到父佈局。
        return panel  # 返回創建的面板。

    # 更新視圖內容
    def update_view(self):  # 更新 GUI 以反映模型的當前狀態。
        # 根據模型的當前狀態更新視圖
        self.groudtruth_file.setText(self.model.groudtruth_file)  # 更新真實圖檔資料夾路徑的文本框。
        self.result_file.setText(self.model.result_file)  # 更新修復圖檔資料夾路徑的文本框。
        self.mask_file.setText(self.model.mask_file)  # 更新遮罩圖檔資料夾路徑的文本框。
        self.output_folder.setText(self.model.output_folder)  # 更新輸出資料夾路徑的文本框。

    # 保存分析數值
    def save_value_file(self):  # 保存分析數值的方法。
        # 調用模型的保存方法並檢查結果
        if self.model.save_value_button(self.render_input, self.render_input2):  # 調用模型的保存方法，傳遞兩個渲染器。
            print("Depth map saved successfully")  # 如果保存成功，打印成功訊息（訊息可能需調整為“Analysis values saved successfully”）。
        else:
            print("Failed to save depth map")  # 如果保存失敗，打印失敗訊息（同上，建議調整為更精確的訊息）。