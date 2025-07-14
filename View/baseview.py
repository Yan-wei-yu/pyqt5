# 主要目的：此程式碼定義了一個基於 PyQt5 的 `BaseView` 類
# 作為其他視圖類的基類，提供通用的檔案和資料夾選擇功能
# 以及旋轉角度更新邏輯。它支援檔案選擇（包括圖片檔案）、資料夾選擇，並提供用於創建檔案選擇佈局的通用方法
# 適用於牙科 3D 模型或影像處理的 GUI 應用。

from PyQt5.QtWidgets import QFileDialog  # 導入 QFileDialog，用於檔案和資料夾選擇對話框。
from PyQt5.QtWidgets import QHBoxLayout, QLabel, QPushButton  # 導入 PyQt5 的佈局和界面元件，用於創建 GUI。

class BaseView:  # 定義 BaseView 類，作為其他視圖類的基類。
    def __init__(self, parent_layout, renderinput, renderinput2):  # 初始化方法，接收父佈局和兩個渲染輸入。
        """初始化 BaseView，負責 UI 佈局與檔案選擇功能"""
        self.parent_layout = parent_layout  # 儲存父佈局，用於添加 UI 元件。
        self.render_input = renderinput  # 儲存第一個 VTK 渲染輸入（通常為 vtkRenderer）。
        self.render_input2 = renderinput2  # 儲存第二個 VTK 渲染輸入，用於對比或額外顯示。

    def choose_file(self, line_edit, file_filter):  # 選擇單個檔案的方法。
        """選擇單個檔案，並將其路徑顯示在 line_edit 中"""
        options = QFileDialog.Options()  # 創建 QFileDialog 的選項對象。
        file_path, _ = QFileDialog.getOpenFileName(None, "選擇檔案", "", file_filter, options=options)  # 打開檔案選擇對話框，獲取檔案路徑。
        if file_path:  # 如果選擇了有效檔案。
            line_edit.setText(file_path)  # 將檔案路徑設置到指定的 QLineEdit 輸入框。
        else:
            line_edit.setText("")  # 若未選擇檔案，清空輸入框。
        return file_path  # 返回選擇的檔案路徑。

    def choose_image(self, line_edit):  # 選擇圖片檔案的方法。
        """選擇圖片檔案（僅限 PNG、JPG、JPEG），並將其路徑顯示在 line_edit 中"""
        options = QFileDialog.Options()  # 創建 QFileDialog 的選項對象。
        file_filter = " Image (*.png *.jpg *.jpeg)"  # 設置圖片檔案篩選條件，僅允許 .png、.jpg、.jpeg 格式。
        file_path, _ = QFileDialog.getOpenFileName(None, "選擇檔案", "", file_filter, options=options)  # 打開檔案選擇對話框，獲取圖片路徑。
        if file_path:  # 如果選擇了有效圖片檔案。
            line_edit.setText(file_path)  # 將圖片路徑設置到指定的 QLineEdit 輸入框。
        else:
            line_edit.setText(None)  # 若未選擇圖片，清空輸入框（設置為 None）。
        return file_path  # 返回選擇的圖片路徑。

    def update_angle(self):  # 更新模型旋轉角度的方法。
        """更新模型旋轉角度"""
        try:
            angle = float(self.angle_input.text())  # 嘗試將輸入框的文字轉換為浮點數，表示旋轉角度。
            self.model.set_model_angle(angle)  # 調用模型的 set_model_angle 方法，設置旋轉角度。
        except ValueError:  # 如果輸入無效（例如非數字）。
            print("Invalid angle input")  # 打印錯誤訊息，提示輸入無效。

    def choose_folder(self, line_edit, set_model_callback):  # 選擇資料夾的方法。
        """選擇文件夾，並將其路徑傳遞給回呼函式（callback），顯示於 line_edit"""
        folder_path = QFileDialog.getExistingDirectory(None, "選擇文件夾")  # 打開資料夾選擇對話框，獲取資料夾路徑。
        if folder_path:  # 如果選擇了有效資料夾。
            set_model_callback(folder_path)  # 調用傳入的回呼函式，更新模型的資料夾路徑。
            line_edit.setText(folder_path)  # 將資料夾路徑設置到指定的 QLineEdit 輸入框。
            return folder_path  # 返回選擇的資料夾路徑。
        else:
            set_model_callback(folder_path)  # 若未選擇資料夾，傳遞空路徑給回呼函式。
            line_edit.setText(None)  # 清空輸入框（設置為 None）。
            return None  # 返回 None。

    def create_file_selection_layout(self, parent_layout, label_text, line_edit, set_model):  # 創建通用資料夾選擇佈局的方法。
        """創建通用文件夾選擇佈局，包含標籤、輸入框與選擇按鈕"""
        file_layout = QHBoxLayout()  # 創建水平佈局，用於組織檔案選擇相關元件。
        file_layout.addWidget(QLabel(label_text))  # 添加指定文字的標籤。
        file_layout.addWidget(line_edit)  # 添加傳入的 QLineEdit 輸入框。
        button = QPushButton("選擇")  # 創建“選擇”按鈕。
        button.clicked.connect(lambda: self.choose_folder(line_edit, set_model))  # 將按鈕點擊事件連接到 choose_folder 方法，傳遞輸入框和模型設置函式。
        file_layout.addWidget(button)  # 將按鈕添加到佈局。
        parent_layout.addLayout(file_layout)  # 將檔案選擇佈局添加到父佈局。