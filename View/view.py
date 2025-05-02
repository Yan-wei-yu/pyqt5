from PyQt5.QtWidgets import (QMainWindow, QVBoxLayout, QHBoxLayout, QPushButton, QWidget, QSpacerItem, 
                             QSizePolicy, QDesktopWidget)  # 引入 PyQt5 中的 GUI 元件
from vtkmodules.qt.QVTKRenderWindowInteractor import QVTKRenderWindowInteractor  # 引入 VTK 在 Qt 內嵌的窗口
import vtkmodules.all as vtk  # 匯入所有 VTK 模組
from . import (singledepthview, mutipledepthview, aipredictview,  # 匯入不同的視圖模組
               edgeview, remeshview, stitchview, analysisview, icpview,aipredictobbview,stitchview)
from Model import Singledepthmodel, Mutipledepthmodel, Edgemodel, Aipredictmodel, Remeshmodel, Analysismodel, ICPmodel,MutipleOBBdepthmodel,Aipredictobbmodel,Stitchmodel  # 匯入不同的模型

class View(QMainWindow):  # 定義主視圖類別，繼承自 QMainWindow
    def __init__(self, parent=None):
        super().__init__(parent)  # 呼叫父類別的建構子
        self.setWindowTitle('AI牙冠平台')  # 設定視窗標題
        self.setup_ui()  # 設定 UI 佈局
        self.setup_vtk()  # 設定 VTK 渲染窗口
        self.connect_signals()  # 連接按鈕信號與對應的處理函數
        self.current_panel = None  # 初始化當前面板變數
        self.center()  # 使視窗置中
        self.showMaximized()  # 視窗最大化顯示

    def setup_ui(self):  # 設定 UI 介面
        self.centralWidget = QWidget()  # 創建主控件
        self.setCentralWidget(self.centralWidget)  # 設定為中央控件
        self.mainLayout = QHBoxLayout(self.centralWidget)  # 創建水平佈局
        self.setup_button_panel()  # 設定按鈕面板
        self.setup_vtk_widgets()  # 設定 VTK 顯示區域

    def setup_button_panel(self):  # 設定左側的按鈕面板
        self.buttonPanel = QVBoxLayout()  # 建立垂直佈局
        self.buttonPanel.addSpacerItem(QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding))  # 增加間隔

        # 定義按鈕對應的功能名稱
        self.buttons = {
            "depthButton": "單次創建深度圖",
            "mutiple_depthButton": "多次創建深度圖",
            "mutiple_obb_depthButton": "多次obb創建深度圖",
            "edgeButton": "獲得牙齒邊界線圖",
            "predictButton": "AI預測",
            "predictobbButton": "AIOBB預測",
            "icpButton": "ICP模型對齊",
            "reconstructButton": "3D模型重建",
            "stitchButton": "3D縫合網格",
            "analysisButton": "2D圖像遮罩區域分析",
        }
        
        buttonStyle = "font-size: 26px; font-family: '標楷體', 'Times New Roman'; font-weight: bold;"  # 設定按鈕樣式
        
        for attr, text in self.buttons.items():  # 迴圈建立按鈕
            button = QPushButton(text)  # 創建按鈕
            button.setStyleSheet(buttonStyle)  # 設定樣式
            setattr(self, attr, button)  # 使用 setattr 動態將每個按鈕以名稱註冊為類別屬性，之後可用 self.<名稱> 直接操作
            self.buttonPanel.addWidget(button)  # 新增按鈕至面板
            self.buttonPanel.addSpacing(20)  # 增加間距
        
        self.buttonPanel.addStretch(1)  # 讓按鈕面板填滿剩餘空間
        self.mainLayout.addLayout(self.buttonPanel, 1)  # 將按鈕面板加入主佈局

    def setup_vtk_widgets(self):  # 設定 VTK 視圖元件
        self.vtkWidget1 = QVTKRenderWindowInteractor(self.centralWidget)  # 創建第一個 VTK 窗口
        self.vtkWidget2 = QVTKRenderWindowInteractor(self.centralWidget)  # 創建第二個 VTK 窗口
        self.mainLayout.addWidget(self.vtkWidget1, stretch=1)  # 添加到主佈局
        self.mainLayout.addWidget(self.vtkWidget2, stretch=1)  # 添加到主佈局

    def setup_vtk(self):  # 設定 VTK 渲染器
        self.vtk_renderer1 = vtk.vtkRenderer()  # 創建第一個渲染器
        self.vtkWidget1.GetRenderWindow().AddRenderer(self.vtk_renderer1)  # 綁定渲染器
        self.iren1 = self.vtkWidget1.GetRenderWindow().GetInteractor()  # 獲取交互器
        self.iren1.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())  # 設定交互方式
        self.iren1.RemoveObservers('TimerEvent')  # 防止自動旋轉
        self.vtk_renderer1.SetBackground(0.1, 0.2, 0.4)  # 設定背景顏色
        self.vtkWidget1.setFixedSize(768, 768)  # 設定窗口大小
        self.iren1.Initialize()  # 初始化交互器

        self.vtk_renderer2 = vtk.vtkRenderer()  # 創建第二個渲染器
        self.vtkWidget2.GetRenderWindow().SetSharedRenderWindow(self.vtkWidget1.GetRenderWindow())  # 共用同一個渲染窗口
        self.vtkWidget2.GetRenderWindow().AddRenderer(self.vtk_renderer2)  # 綁定渲染器
        self.iren2 = self.vtkWidget2.GetRenderWindow().GetInteractor()  # 獲取交互器
        self.iren2.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())  # 設定交互方式
        self.iren2.RemoveObservers('TimerEvent')  # 防止自動旋轉
        self.vtk_renderer2.SetBackground(0.1, 0.4, 0.2)  # 設定背景顏色
        self.vtkWidget2.setFixedSize(768, 768)  # 設定窗口大小
        self.iren2.Initialize()  # 初始化交互器

    def connect_signals(self):  # 連接按鈕信號與對應函數
        self.depthButton.clicked.connect(lambda: self.create_depth_panel())
        self.mutiple_depthButton.clicked.connect(lambda: self.create_multiple_depth_panel())
        self.mutiple_obb_depthButton.clicked.connect(lambda: self.create_obb_multiple_depth_panel())
        self.edgeButton.clicked.connect(lambda: self.create_edge_panel())
        self.predictButton.clicked.connect(lambda: self.create_predict_panel())
        self.predictobbButton.clicked.connect(lambda: self.create_predictobb_panel())
        self.icpButton.clicked.connect(lambda: self.create_icp_panel())
        self.reconstructButton.clicked.connect(lambda: self.create_reconstruct_panel())
        self.stitchButton.clicked.connect(lambda: self.create_stitch_panel())
        self.analysisButton.clicked.connect(lambda: self.create_analysis_panel())


    def create_depth_panel(self):
        """創建單個深度視圖面板"""
        self.clear_renderers()  # 清空渲染器內容
        self.function_view = singledepthview.SingleDepthView(
            self.buttonPanel, Singledepthmodel.SingleDepthModel(), self.vtk_renderer1, self.vtk_renderer2
        )
        self.current_panel = self.function_view.create_depth(self.buttonPanel, self.current_panel)

    def create_multiple_depth_panel(self):
        """創建多個深度視圖面板"""
        self.clear_renderers()
        self.function_view = mutipledepthview.MutipleDepthView(
            self.buttonPanel, Mutipledepthmodel.BatchDepthModel(), self.vtk_renderer1, self.vtk_renderer2
        )
        self.current_panel = self.function_view.create_depth(self.buttonPanel, self.current_panel)

    def create_obb_multiple_depth_panel(self):
            """創建OBB多個深度視圖面板"""
            self.clear_renderers()
            self.function_view = mutipledepthview.MutipleDepthView(
                self.buttonPanel, MutipleOBBdepthmodel.OBBBatchDepthModel(), self.vtk_renderer1, self.vtk_renderer2
            )
            self.current_panel = self.function_view.create_depth(self.buttonPanel, self.current_panel)

    def create_edge_panel(self):
        """創建邊緣檢測視圖面板"""
        self.clear_renderers()
        self.function_view = edgeview.ImageedgeView(
            self.buttonPanel, Edgemodel.EdgeModel(), self.vtk_renderer1, self.vtk_renderer2
        )
        self.current_panel = self.function_view.create_edge(self.buttonPanel, self.current_panel)

    def create_predict_panel(self):
        """創建 AI 預測視圖面板"""
        self.clear_renderers()
        self.function_view = aipredictview.AimodelView(
            self.buttonPanel, Aipredictmodel.AipredictModel(), self.vtkWidget1, self.vtk_renderer1, self.vtk_renderer2
        )
        self.current_panel = self.function_view.create_predict(self.buttonPanel, self.current_panel)

    def create_predictobb_panel(self):
        """創建 AI obb預測視圖面板"""
        self.clear_renderers()
        self.function_view = aipredictobbview.AimodelOBBView(
            self.buttonPanel, Aipredictobbmodel.AipredictOBBModel(), self.vtkWidget1, self.vtk_renderer1, self.vtk_renderer2
        )
        self.current_panel = self.function_view.create_predict(self.buttonPanel, self.current_panel)
    
    def create_icp_panel(self):
        """創建 ICP（Iterative Closest Point）模型對齊視圖面板"""
        self.clear_renderers()
        self.function_view = icpview.ICPView(
            self.buttonPanel, ICPmodel.ICPModel(), self.vtkWidget1, self.vtk_renderer1, self.vtk_renderer2
        )
        self.current_panel = self.function_view.create_predict(self.buttonPanel, self.current_panel)
    
    def create_reconstruct_panel(self):
        """創建重建視圖面板"""
        self.clear_renderers()
        self.function_view = remeshview.RemeshView(
            self.buttonPanel, Remeshmodel.RemeshModel(), self.vtk_renderer1, self.vtk_renderer2
        )
        self.current_panel = self.function_view.create_remesh(self.buttonPanel, self.current_panel)

    def create_stitch_panel(self):
        """創建未來分割+縫合視圖面板"""
        self.clear_renderers()
        self.function_view = stitchview.StitchView(
            self.buttonPanel, Stitchmodel.StitchModel(), self.vtk_renderer1, self.vtk_renderer2
        )
        self.current_panel = self.function_view.create_stitch(self.buttonPanel, self.current_panel)

    def create_analysis_panel(self):
        """創建分析視圖面板"""
        self.clear_renderers()
        self.function_view = analysisview.AnalysisView(
            self.buttonPanel, Analysismodel.AnalysisModel(), self.vtk_renderer1, self.vtk_renderer2
        )
        self.current_panel = self.function_view.create_edge(self.buttonPanel, self.current_panel)

    def clear_renderers(self):
        """清空所有 VTK 渲染器內的內容"""
        self.vtk_renderer1.RemoveAllViewProps()  # 移除第一個渲染器的所有物件
        self.vtk_renderer2.RemoveAllViewProps()  # 移除第二個渲染器的所有物件
        self.vtk_renderer1.GetRenderWindow().Render()
        self.vtk_renderer2.GetRenderWindow().Render()

    def closeEvent(self, event):
        """處理視窗關閉事件，進行清理"""
        self.cleanup()
        event.accept()

    def cleanup(self):
        """清理所有 VTK 相關資源"""
        for iren in [self.iren1, self.iren2]:
            if iren:
                iren.GetRenderWindow().Finalize()
                iren.TerminateApp()

        # 釋放 VTK 和 UI 元件
        for attr in ['vtkWidget1', 'vtkWidget2', 'vtk_renderer1', 'vtk_renderer2', 'iren1', 'iren2']:
            setattr(self, attr, None)

    def center(self):
        """將視窗置中"""
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().topLeft()
        qr.moveCenter(cp)
        self.move(qr.center())