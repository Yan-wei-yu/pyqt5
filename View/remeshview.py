# 主要目的：作為 3D 重建視圖模組，負責處理 3D 模型重建的圖形用戶界面 (GUI)。
# 它允許用戶選擇 2D 圖檔（深度圖）、3D 參考模型和輸出資料夾，選擇重建模式（BB 或 OBB）和面（咬合面、舌側、頰側），並執行 3D 重建操作
# 最後將結果渲染到 VTK 窗口並保存。
from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QComboBox  # 導入 PyQt5 的界面元件，用於創建 GUI。
from PyQt5.QtCore import Qt  # 導入 PyQt5 的核心模組，用於設置界面屬性。
from .baseview import BaseView  # 從當前模組導入 BaseView 基類，RemeshView 繼承自該類。
from Otherfunction import readmodel  # 導入 Otherfunction 模組中的 readmodel，用於渲染文件。

class RemeshView(BaseView):  # 定義 RemeshView 類，繼承自 BaseView。
    # 初始化函數，設置視圖的基本屬性
    def __init__(self, parent_layout, model, renderinput, renderinput2):  # 初始化方法，接收父佈局、模型和兩個渲染輸入。
        super().__init__(parent_layout, renderinput, renderinput2)  # 調用基類的初始化方法，設置父佈局和渲染輸入。
        self.model = model  # 儲存傳入的模型對象，用於處理數據和邏輯。
        model.model_updated.connect(self.update_view)  # 將模型的更新信號連接到 update_view 方法，確保視圖隨模型更新。

    # 創建3D重建面板
    def create_remesh(self, parent_layout, current_panel):  # 創建 3D 重建的 GUI 面板。
        # 如果當前面板存在，則移除
        if current_panel:  # 檢查是否已有當前面板。
            parent_layout.removeWidget(current_panel)  # 移除當前面板以更新界面。

        # 創建帶標題的組框，標題為"3D重建"
        panel = QGroupBox("3D重建")  # 創建標題為“3D重建”的 QGroupBox 分組框。
        layout = QVBoxLayout()  # 創建垂直佈局，用於組織 GUI 元件。

        # 上顎模型檔案選擇（這裡實際上是2D圖檔）
        image_layout = QHBoxLayout()  # 創建水平佈局，用於 2D 圖檔選擇。
        image_layout.addWidget(QLabel("2D圖檔"))  # 添加標籤“2D圖檔”。
        self.image_file = QLineEdit()  # 創建文本框，用於顯示 2D 圖檔路徑。
        image_layout.addWidget(self.image_file)  # 將文本框添加到佈局。
        image_button = QPushButton("選擇")  # 創建“選擇”按鈕。
        image_button.clicked.connect(self.choose_image_file)  # 將按鈕點擊事件連接到選擇 2D 圖檔方法。
        image_layout.addWidget(image_button)  # 將按鈕添加到佈局。
        layout.addLayout(image_layout)  # 將 2D 圖檔選擇佈局添加到主垂直佈局。

        # 下顎模型檔案選擇（3D參考模型）
        lower_layout = QHBoxLayout()  # 創建水平佈局，用於 3D 參考模型檔案選擇。
        lower_layout.addWidget(QLabel("3D參考"))  # 添加標籤“3D參考”。
        self.lower_file = QLineEdit()  # 創建文本框，用於顯示 3D 參考模型檔案路徑。
        lower_layout.addWidget(self.lower_file)  # 將文本框添加到佈局。
        lower_button = QPushButton("選擇")  # 創建“選擇”按鈕。
        lower_button.clicked.connect(self.choose_lower_file)  # 將按鈕點擊事件連接到選擇 3D 參考模型方法。
        lower_layout.addWidget(lower_button)  # 將按鈕添加到佈局。
        layout.addLayout(lower_layout)  # 將 3D 參考模型選擇佈局添加到主垂直佈局。

        # 輸出文件夾選擇
        self.output_layout = QHBoxLayout()  # 創建水平佈局，用於輸出資料夾選擇。
        self.output_folder = QLineEdit()  # 創建文本框，用於顯示輸出資料夾路徑。
        self.create_file_selection_layout(layout, "輸出文件夾:", self.output_folder, self.model.set_output_folder)  # 調用基類方法創建檔案選擇佈局。

        # 第一排：選擇模式 (BB 或 OBB)
        mode_layout = QHBoxLayout()  # 創建水平佈局，用於模式選擇。
        mode_layout.addWidget(QLabel("模式選擇:"))  # 添加標籤“模式選擇:”。
        self.mode_combo = QComboBox()  # 創建下拉選單，用於選擇重建模式。
        self.mode_combo.addItems(["", "BB", "OBB"])  # 添加選項：空、BB（Bounding Box）、OBB（Oriented Bounding Box）。
        self.mode_combo.currentTextChanged.connect(self.on_mode_changed)  # 將模式改變事件連接到 on_mode_changed 方法。
        mode_layout.addWidget(self.mode_combo)  # 將下拉選單添加到佈局。
        layout.addLayout(mode_layout)  # 將模式選擇佈局添加到主垂直佈局。

        # 第二排：選擇面 (咬合面、舌側、頰側)
        face_layout = QHBoxLayout()  # 創建水平佈局，用於面選擇。
        face_layout.addWidget(QLabel("面選擇:"))  # 添加標籤“面選擇:”。
        self.face_combo = QComboBox()  # 創建下拉選單，用於選擇牙冠面。
        self.face_combo.addItems(["", "咬合面", "舌側", "頰側"])  # 添加選項：空、咬合面、舌側、頰側。
        self.face_combo.setEnabled(False)  # 初始禁用面選擇下拉選單。
        self.face_combo.currentTextChanged.connect(self.on_face_changed)  # 將面改變事件連接到 on_face_changed 方法。
        face_layout.addWidget(self.face_combo)  # 將下拉選單添加到佈局。
        layout.addLayout(face_layout)  # 將面選擇佈局添加到主垂直佈局。

        # 創建並設置保存按鈕
        save_button = QPushButton("3D重建")  # 創建“3D重建”按鈕。
        save_button.clicked.connect(self.save_remesh_file)  # 將按鈕點擊事件連接到保存 3D 重建結果方法。
        layout.addWidget(save_button)  # 將按鈕添加到主佈局。

        panel.setLayout(layout)  # 將佈局設置到分組框。
        parent_layout.addWidget(panel)  # 將分組框添加到父佈局。
        return panel  # 返回創建的面板。

    # 選擇下顎3D參考文件
    def choose_lower_file(self):  # 選擇 3D 參考模型檔案的方法。
        file_path = self.choose_file(self.lower_file, "3D Model Files (*.ply *.stl *.obj)")  # 調用基類方法選擇檔案，支援 .ply、.stl、.obj 格式。
        if file_path:  # 如果選擇了有效檔案。
            self.model.set_reference_file(file_path)  # 調用模型方法設置 3D 參考檔案。
        else:  # 如果未選擇有效檔案。
            self.model.reference_file = ""  # 清空模型的 3D 參考檔案路徑。

    # 選擇2D圖檔
    def choose_image_file(self):  # 選擇 2D 圖檔（深度圖）的方法。
        file_path = self.choose_image(self.image_file)  # 調用基類方法選擇圖檔（假設支援圖像格式）。
        if file_path:  # 如果選擇了有效檔案。
            self.model.set_image_file(file_path)  # 調用模型方法設置 2D 圖檔。
        else:  # 如果未選擇有效檔案。
            self.model.image_file = ""  # 清空模型的 2D 圖檔路徑。

    # 當模式改變時觸發
    def on_mode_changed(self, mode):  # 處理模式下拉選單改變事件。
        if mode:  # 如果選擇了有效模式（非空）。
            self.model.set_mode(mode)  # 調用模型方法設置模式（BB 或 OBB）。
            self.face_combo.setEnabled(True)  # 啟用面選擇下拉選單。
        else:  # 如果選擇了空模式。
            self.model.mode = None  # 清空模型的模式。
            self.face_combo.setEnabled(False)  # 禁用面選擇下拉選單。
            self.face_combo.setCurrentText("")  # 重置面選擇為空。

    # 當面改變時觸發
    def on_face_changed(self, face):  # 處理面下拉選單改變事件。
        if face:  # 如果選擇了有效面（非空）。
            self.model.set_face(face)  # 調用模型方法設置面（咬合面、舌側、頰側）。
        else:  # 如果選擇了空面。
            self.model.face = None  # 清空模型的面選擇。

    # 保存3D重建結果
    def save_remesh_file(self):  # 保存 3D 重建結果的方法。
        if self.model.save_remesh_file(self.render_input, self.render_input2):  # 調用模型的保存方法，傳遞兩個渲染器。
            print("Depth map saved successfully")  # 如果保存成功，打印成功訊息。
        else:
            print("Failed to save depth map")  # 如果保存失敗，打印失敗訊息。

    # 更新視圖內容
    def update_view(self):  # 更新 GUI 以反映模型的當前狀態。
        self.image_file.setText(self.model.image_file)  # 更新 2D 圖檔路徑的文本框。
        self.lower_file.setText(self.model.reference_file)  # 更新 3D 參考模型檔案路徑的文本框。
        self.output_folder.setText(self.model.output_folder)  # 更新輸出資料夾路徑的文本框。
        self.render_input.RemoveAllViewProps()  # 清除渲染器中的所有視圖屬性（演員）。
        if self.model.image_file:  # 如果存在 2D 圖檔。
            readmodel.render_file_in_second_window(self.render_input, self.model.image_file)  # 在渲染器中渲染 2D 圖檔。
        # 更新模式和面的顯示
        self.mode_combo.setCurrentText(self.model.mode if self.model.mode else "")  # 更新模式下拉選單，顯示當前模式或空。
        self.face_combo.setCurrentText(self.model.face if self.model.face else "")  # 更新面下拉選單，顯示當前面或空。
        self.face_combo.setEnabled(bool(self.model.mode))  # 根據是否選擇模式啟用或禁用面選項。