# 這是打單一深度圖的視圖模組
from PyQt5.QtWidgets import QGroupBox, QVBoxLayout, QHBoxLayout, QLabel, QLineEdit, QPushButton, QSlider  # 從 PyQt5 導入必要的 UI 組件
from PyQt5.QtCore import Qt  # 從 PyQt5 導入核心功能，例如 Qt.Horizontal
from .baseview import BaseView  # 從當前目錄下的 baseview 模組導入 BaseView 類
from Otherfunction import readmodel  # 從 Otherfunction 模組導入 readmodel 函數

class SingleDepthView(BaseView):  # 定義 SingleDepthView 類，繼承自 BaseView
    def __init__(self, parent_layout, model, renderinput, renderinput2):  # 初始化函數，接收父佈局、模型和兩個渲染輸入
        super().__init__(parent_layout, renderinput, renderinput2)  # 調用父類 BaseView 的初始化方法
        self.model = model  # 將傳入的模型存儲為實例變數
        model.model_updated.connect(self.update_view)  # 將模型的更新信號連接到 update_view 方法

    def create_depth(self, parent_layout, current_panel):  # 定義創建深度圖面板的方法，接收父佈局和當前面板
        if current_panel:  # 如果存在當前面板
            parent_layout.removeWidget(current_panel)  # 從父佈局中移除當前面板

        panel = QGroupBox("單次創建深度圖")  # 創建一個標題為 "單次創建深度圖" 的組框
        layout = QVBoxLayout()  # 創建一個垂直佈局用於組框內部

        # 上顎模型檔案選擇
        upper_layout = QHBoxLayout()  # 創建一個水平佈局用於上顎檔案選擇
        upper_layout.addWidget(QLabel("上顎檔案:"))  # 添加標籤 "上顎檔案:"
        self.upper_file = QLineEdit()  # 創建一個用於輸入上顎檔案路徑的文本框
        upper_layout.addWidget(self.upper_file)  # 將文本框添加到上顎佈局
        upper_button = QPushButton("選擇")  # 創建一個標籤為 "選擇" 的按鈕
        upper_button.clicked.connect(self.choose_upper_file)  # 將按鈕點擊事件連接到 choose_upper_file 方法
        upper_layout.addWidget(upper_button)  # 將按鈕添加到上顎佈局
        layout.addLayout(upper_layout)  # 將上顎佈局添加到主垂直佈局

        # 下顎模型檔案選擇
        lower_layout = QHBoxLayout()  # 創建一個水平佈局用於下顎檔案選擇
        lower_layout.addWidget(QLabel("下顎檔案:"))  # 添加標籤 "下顎檔案:"
        self.lower_file = QLineEdit()  # 創建一個用於輸入下顎檔案路徑的文本框
        lower_layout.addWidget(self.lower_file)  # 將文本框添加到下顎佈局
        lower_button = QPushButton("選擇")  # 創建一個標籤為 "選擇" 的按鈕
        lower_button.clicked.connect(self.choose_lower_file)  # 將按鈕點擊事件連接到 choose_lower_file 方法
        lower_layout.addWidget(lower_button)  # 將按鈕添加到下顎佈局
        layout.addLayout(lower_layout)  # 將下顎佈局添加到主垂直佈局

        # 旋轉角度輸入框
        angle_layout = QHBoxLayout()  # 創建一個水平佈局用於旋轉角度輸入
        angle_layout.addWidget(QLabel("旋轉角度:"))  # 添加標籤 "旋轉角度:"
        self.angle_input = QLineEdit()  # 創建一個用於輸入旋轉角度的文本框
        self.angle_input.setText("0")  # 設定旋轉角度的初始值為 "0"
        self.angle_input.editingFinished.connect(self.update_angle)  # 將編輯完成事件連接到 update_angle 方法
        angle_layout.addWidget(self.angle_input)  # 將角度輸入框添加到角度佈局
        layout.addLayout(angle_layout)  # 將角度佈局添加到主垂直佈局

        # 上顎透明度調整滑塊
        upper_opacity_layout = QHBoxLayout()  # 創建一個水平佈局用於上顎透明度調整
        upper_opacity_layout.addWidget(QLabel("上顎透明度:"))  # 添加標籤 "上顎透明度:"
        self.upper_opacity = QSlider(Qt.Horizontal)  # 創建一個水平滑塊用於調整上顎透明度
        self.upper_opacity.setRange(0, 1)  # 設定滑塊範圍為 0 到 1
        self.upper_opacity.setValue(1)  # 設定滑塊初始值為 1（完全不透明）
        self.upper_opacity.valueChanged.connect(self.update_upper_opacity)  # 將滑塊值變化事件連接到 update_upper_opacity 方法
        upper_opacity_layout.addWidget(self.upper_opacity)  # 將滑塊添加到上顎透明度佈局
        layout.addLayout(upper_opacity_layout)  # 將上顎透明度佈局添加到主垂直佈局

        # 下顎透明度調整滑塊
        lower_opacity_layout = QHBoxLayout()  # 創建一個水平佈局用於下顎透明度調整
        lower_opacity_layout.addWidget(QLabel("下顎透明度:"))  # 添加標籤 "下顎透明度:"
        self.lower_opacity = QSlider(Qt.Horizontal)  # 創建一個水平滑塊用於調整下顎透明度
        self.lower_opacity.setRange(0, 1)  # 設定滑塊範圍為 0 到 1
        self.lower_opacity.setValue(1)  # 設定滑塊初始值為 1（完全不透明）
        self.lower_opacity.valueChanged.connect(self.update_lower_opacity)  # 將滑塊值變化事件連接到 update_lower_opacity 方法
        lower_opacity_layout.addWidget(self.lower_opacity)  # 將滑塊添加到下顎透明度佈局
        layout.addLayout(lower_opacity_layout)  # 將下顎透明度佈局添加到主垂直佈局

        # 輸出深度圖文件夾選擇
        self.output_layout = QHBoxLayout()  # 創建一個水平佈局用於輸出文件夾選擇
        self.output_folder = QLineEdit()  # 創建一個用於輸入輸出文件夾路徑的文本框
        self.create_file_selection_layout(layout, "輸出文件夾:", self.output_folder, self.model.set_output_folder)  # 調用方法創建文件選擇佈局

        # 保存深度圖按鈕
        save_button = QPushButton("保存深度圖")  # 創建一個標籤為 "保存深度圖" 的按鈕
        save_button.clicked.connect(self.save_depth_single_map)  # 將按鈕點擊事件連接到 save_depth_single_map 方法
        layout.addWidget(save_button)  # 將保存按鈕添加到主垂直佈局

        panel.setLayout(layout)  # 將佈局設置到組框中
        parent_layout.addWidget(panel)  # 將組框添加到父佈局
        return panel  # 返回創建的面板

    def choose_upper_file(self):  # 定義選擇上顎檔案的方法
        file_path = self.choose_file(self.upper_file, "3D Model Files (*.ply *.stl *.obj)")  # 調用選擇文件方法，支持指定格式
        if file_path and self.model.set_upper_file(file_path):  # 如果選擇了有效文件且模型成功設置
            self.model.render_model(self.render_input)  # 渲染上顎模型
        else:  # 如果文件無效
            # 若無效則移除上顎模型
            if hasattr(self.model, 'upper_actor') and self.model.upper_actor:  # 檢查模型是否有 upper_actor 屬性且不為空
                self.render_input.RemoveActor(self.model.upper_actor)  # 從渲染輸入中移除上顎模型
                self.render_input.ResetCamera()  # 重置攝影機視角
                self.render_input.GetRenderWindow().Render()  # 重新渲染窗口
            self.model.upper_file = ""  # 清空上顎文件路徑
            self.model.upper_center = None  # 清空上顎中心
            self.model.models_center = None  # 清空模型中心

    def choose_lower_file(self):  # 定義選擇下顎檔案的方法
        file_path = self.choose_file(self.lower_file, "3D Model Files (*.ply *.stl *.obj)")  # 調用選擇文件方法，支持指定格式
        if file_path and self.model.set_lower_file(file_path):  # 如果選擇了有效文件且模型成功設置
            self.model.render_model(self.render_input)  # 渲染下顎模型
        else:  # 如果文件無效
            # 若無效則移除下顎模型
            if hasattr(self.model, 'lower_actor') and self.model.lower_actor:  # 檢查模型是否有 lower_actor 屬性且不為空
                self.render_input.RemoveActor(self.model.lower_actor)  # 從渲染輸入中移除下顎模型
                self.render_input.ResetCamera()  # 重置攝影機視角
                self.render_input.GetRenderWindow().Render()  # 重新渲染窗口
            self.model.lower_file = ""  # 清空下顎文件路徑
            self.model.lower_center = None  # 清空下顎中心
            self.model.models_center = None  # 清空模型中心

    def update_upper_opacity(self):  # 定義更新上顎透明度的方法
        opacity = self.upper_opacity.value()  # 獲取滑塊當前值作為透明度
        self.model.set_upper_opacity(opacity)  # 將透明度設置到模型中

    def update_lower_opacity(self):  # 定義更新下顎透明度的方法
        opacity = self.lower_opacity.value()  # 獲取滑塊當前值作為透明度
        self.model.set_lower_opacity(opacity)  # 將透明度設置到模型中

    def save_depth_single_map(self):  # 定義保存單次深度圖的方法
        output_file_path = self.model.save_depth_map(self.render_input)  # 調用模型方法保存深度圖並獲取文件路徑
        readmodel.render_file_in_second_window(self.render_input2, output_file_path)  # 在第二窗口渲染保存的深度圖文件
        print("Depth map saved successfully")  # 輸出保存成功的消息

    def update_view(self):  # 定義更新視圖的方法
        # 更新 UI 以反映模型的當前狀態
        self.upper_file.setText(self.model.upper_file)  # 更新上顎文件路徑文本框
        self.lower_file.setText(self.model.lower_file)  # 更新下顎文件路徑文本框
        self.angle_input.setText(str(self.model.angle))  # 更新旋轉角度文本框
        self.output_folder.setText(self.model.output_folder)  # 更新輸出文件夾路徑文本框
        self.upper_opacity.setValue(int(self.model.upper_opacity))  # 更新上顎透明度滑塊
        self.lower_opacity.setValue(int(self.model.lower_opacity))  # 更新下顎透明度滑塊
        self.render_input.ResetCamera()  # 重置渲染輸入的攝影機視角
        self.render_input.GetRenderWindow().Render()  # 重新渲染窗口