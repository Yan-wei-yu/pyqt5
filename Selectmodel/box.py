# 主要目的：此程式碼定義了一個基於 VTK 的 `BoxInteractor` 類，繼承自 `vtkInteractorStyleRubberBand3D`，用於在牙科 3D 模型處理場景中實現矩形框選功能。它允許用戶通過滑鼠左鍵拖曳選擇 3D 模型的區域，生成選取範圍的幾何數據並以紅色高亮顯示，支援與 `HighlightInteractorStyle` 和 `AimodelView` 結合使用，提供交互式模型編輯功能。

from vtkmodules.vtkInteractionStyle import vtkInteractorStyleRubberBand3D  # 導入 VTK 的橡皮筋 3D 交互樣式，作為基類。
import vtk  # 導入 VTK 庫，用於 3D 模型處理和視覺化。

class BoxInteractor(vtkInteractorStyleRubberBand3D):  # 定義 BoxInteractor 類，繼承自橡皮筋 3D 交互樣式。
    def __init__(self, poly_data, renderer):  # 初始化方法，接收 PolyData 和渲染器。
        super().__init__()  # 調用父類的初始化方法。
        self.renderer = renderer  # 儲存傳入的 VTK 渲染器（來自 AimodelView）。
        self.poly_data = poly_data  # 儲存傳入的 PolyData（3D 模型數據，例如上顎或下顎模型）。
        self.selection_frustum = None  # 初始化選取範圍的錐體（frustum），用於定義框選區域。
        self.extract_geometry = None  # 初始化幾何提取器，用於提取選取範圍的數據。
        self.selected_poly_data = None  # 初始化選取的 PolyData，儲存框選結果。
        self.end_position = [0, 0]  # 初始化框選結束位置（螢幕坐標）。
        self.start_position = [0, 0]  # 初始化框選起始位置（螢幕坐標）。
        self.boxArea = vtk.vtkAreaPicker()  # 創建 VTK 區域拾取器，用於框選區域。
        self.colorActors = []  # 初始化演員列表，儲存高亮顯示的演員。
        # 移除父類的默認事件監聽器
        self.RemoveObservers("LeftButtonPressEvent")  # 移除左鍵按下事件監聽。
        self.RemoveObservers("LeftButtonUpEvent")  # 移除左鍵釋放事件監聽。
        self.RemoveObservers("RightButtonPressEvent")  # 移除右鍵按下事件監聽。
        self.RemoveObservers("RightButtonReleaseEvent")  # 移除右鍵釋放事件監聽。
        self.RemoveObservers("MiddleButtonPressEvent")  # 移除中鍵按下事件監聽。
        self.RemoveObservers("MiddleButtonReleaseEvent")  # 移除中鍵釋放事件監聽。
        self.RemoveObservers("MiddleButtonForwardEvent")  # 移除中鍵前滾事件監聽（應為 MouseWheelForwardEvent）。
        self.RemoveObservers("MiddleButtonBackwardEvent")  # 移除中鍵後滾事件監聽（應為 MouseWheelBackwardEvent）。
        # 添加自定義事件監聽器
        self.AddObserver("LeftButtonPressEvent", self.onLeftButtonPress)  # 綁定左鍵按下事件。
        self.AddObserver("LeftButtonReleaseEvent", self.onLeftButtonUp)  # 綁定左鍵釋放事件。
        self.AddObserver("RightButtonPressEvent", self.onRightButtonPress)  # 綁定右鍵按下事件。
        self.AddObserver("RightButtonReleaseEvent", self.onRightButtonUp)  # 綁定右鍵釋放事件。
        self.AddObserver("MiddleButtonPressEvent", self.onMiddleButtonDown)  # 綁定中鍵按下事件。
        self.AddObserver("MiddleButtonReleaseEvent", self.onMiddleButtonUp)  # 綁定中鍵釋放事件。
        self.AddObserver("MiddleButtonForwardEvent", self.onMiddleButtonForward)  # 綁定中鍵前滾事件（應為鼠標滾輪）。
        self.AddObserver("MiddleButtonBackwardEvent", self.onMiddleButtonBackward)  # 綁定中鍵後滾事件（應為鼠標滾輪）。

    def onMiddleButtonDown(self, obj, event):  # 處理中鍵按下事件。
        return  # 空實現，待補充。

    def onMiddleButtonUp(self, obj, event):  # 處理中鍵釋放事件。
        return  # 空實現，待補充。

    def onMiddleButtonForward(self, obj, event):  # 處理中鍵前滾事件（應為鼠標滾輪前滾）。
        return  # 空實現，待補充。

    def onMiddleButtonBackward(self, obj, event):  # 處理中鍵後滾事件（應為鼠標滾輪後滾）。
        return  # 空實現，待補充。

    def onRightButtonPress(self, obj, event):  # 處理右鍵按下事件。
        return  # 空實現，待補充。

    def onRightButtonUp(self, obj, event):  # 處理右鍵釋放事件。
        return  # 空實現，待補充。

    def onLeftButtonPress(self, obj, event):  # 處理左鍵按下事件。
        start_coord = self.GetInteractor().GetEventPosition()  # 獲取滑鼠事件的位置（螢幕坐標）。
        self.start_position = [start_coord[0], start_coord[1]]  # 記錄框選起始位置。
        super().OnLeftButtonDown()  # 調用父類的左鍵按下處理，啟動橡皮筋框選。
        return

    def onLeftButtonUp(self, obj, event):  # 處理左鍵釋放事件。
        end_coord = self.GetInteractor().GetEventPosition()  # 獲取滑鼠事件的位置（螢幕坐標）。
        self.end_position = [end_coord[0], end_coord[1]]  # 記錄框選結束位置。
        super().OnLeftButtonUp()  # 調用父類的左鍵釋放處理，結束橡皮筋框選。
        return

    def boxSelectArea(self):  # 執行矩形框選並提取選取區域的幾何數據。
        self.boxArea.AreaPick(self.start_position[0], self.start_position[1], 
                              self.end_position[0], self.end_position[1], self.renderer)  # 使用區域拾取器選擇框選範圍。
        self.selection_frustum = self.boxArea.GetFrustum()  # 獲取框選範圍的錐體（frustum）。
        self.extract_geometry = vtk.vtkExtractGeometry()  # 創建幾何提取器。
        self.extract_geometry.SetInputData(self.poly_data)  # 設置輸入 PolyData（3D 模型數據）。
        self.extract_geometry.SetImplicitFunction(self.selection_frustum)  # 設置框選錐體作為提取函數。
        self.extract_geometry.Update()  # 更新幾何提取器。
        self.selected_poly_data = self.extract_geometry.GetOutput()  # 獲取提取的 PolyData。
        self.geometry_filter = vtk.vtkGeometryFilter()  # 創建幾何過濾器，確保輸出為 PolyData。
        self.geometry_filter.SetInputData(self.selected_poly_data)  # 設置輸入為提取的 PolyData。
        self.geometry_filter.Update()  # 更新幾何過濾器。
        return self.geometry_filter.GetOutput()  # 返回框選區域的 PolyData。

    def show_all_area(self, input_model):  # 高亮顯示框選區域。
        mapper = vtk.vtkPolyDataMapper()  # 創建 VTK 映射器。
        actor = vtk.vtkActor()  # 創建 VTK 演員。
        mapper.SetInputData(input_model)  # 設置映射器的輸入為框選的 PolyData。
        actor.SetMapper(mapper)  # 設置演員的映射器。
        actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # 設置演員顏色為紅色（RGB: 1, 0, 0）。
        self.colorActors.append(actor)  # 將演員添加到高亮演員列表。
        self.renderer.AddActor(actor)  # 將演員添加到渲染器。
        self.GetInteractor().GetRenderWindow().Render()  # 重新渲染窗口以顯示高亮區域。

    def unRenderAllSelectors(self):  # 移除所有高亮演員。
        for colorActor in self.colorActors:  # 迭代高亮演員列表。
            self.renderer.RemoveActor(colorActor)  # 移除每個高亮演員。
        self.GetInteractor().GetRenderWindow().Render()  # 重新渲染窗口以更新顯示。

    def interactorSetter(self, interactor):  # 設置交互器。
        self.SetInteractor(interactor)  # 將傳入的交互器設置為當前交互器，避免在建構子中直接初始化。