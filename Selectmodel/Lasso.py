# 主要目的：此程式碼定義了兩個基於 VTK 的類：`LassoInteractor` 和 `LassoAreaColor`，用於在牙科 3D 模型處理場景中實現套索（lasso）選取功能。`LassoInteractor` 繼承自 `vtk.vtkInteractorStyle`，允許用戶通過滑鼠左鍵拖曳繪製多邊形選取範圍，生成 2D 遮罩並映射到 3D 模型點；`LassoAreaColor` 負責將選取的點以紅色高亮顯示，支援與 `HighlightInteractorStyle` 和 `AimodelView` 結合，提供交互式模型編輯功能。

import numpy as np  # 導入 NumPy 庫，用於數值運算和陣列處理。
import vtkmodules.all as vtk  # 導入 VTK 庫，用於 3D 模型處理和視覺化。
from vtkmodules.util import numpy_support as nps  # 導入 VTK NumPy 支援模組，用於 VTK 和 NumPy 陣列轉換。
from vtkmodules.vtkCommonCore import vtkCommand  # 導入 VTK 命令模組，用於事件處理。
import cv2  # 導入 OpenCV 庫，用於 2D 遮罩處理。

class LassoInteractor(vtk.vtkInteractorStyle):  # 定義 LassoInteractor 類，繼承 VTK 交互樣式。
    class vtkInternal(object):  # 內部類，模擬 C++ 的私有變數，用於儲存和管理多邊形點。
        def __init__(self, parent=None):  # 初始化方法。
            super().__init__()  # 調用父類的初始化方法（儘管無父類，保留兼容性）。
            self._points = []  # 初始化點列表，儲存多邊形頂點的螢幕坐標。
        
        @property
        def points(self):  # 定義 points 屬性，返回點列表。
            return np.array(self._points)  # 將點列表轉為 NumPy 陣列。
        
        def AddPoint(self, x, y):  # 添加點到列表。
            self._points.append([x, y])  # 將螢幕坐標 [x, y] 添加到點列表。
        
        def GetPoint(self, index):  # 獲取指定索引的點。
            if index < 0 or index > len(self._points) - 1:  # 檢查索引是否有效。
                return  # 若無效，返回 None。
            return np.array(self._points[index])  # 返回指定索引的點（轉為 NumPy 陣列）。
        
        def GetNumberOfPoints(self):  # 獲取點數量。
            return len(self._points)  # 返回點列表的長度。
        
        def Clear(self):  # 清除點列表。
            self._points = []  # 重置點列表。
        
        def DrawPixels(self, StartPos, EndPos, pixels, size):  # 繪製線段像素到像素陣列。
            length = int(round(np.linalg.norm(StartPos - EndPos)))  # 計算起始點和結束點的歐幾里得距離。
            if length == 0:  # 如果距離為 0，不繪製。
                return
            x1, y1 = StartPos  # 獲取起始點的 x, y 坐標。
            x2, y2 = EndPos  # 獲取結束點的 x, y 坐標。
            x = [int(round(v)) for v in np.linspace(x1, x2, length)]  # 生成線性插值的 x 坐標。
            y = [int(round(v)) for v in np.linspace(y1, y2, length)]  # 生成線性插值的 y 坐標。
            indices = np.array([row * size[0] + col for col, row in zip(x, y)])  # 計算像素索引（行優先）。
            pixels[indices] = 255 ^ pixels[indices]  # 將對應像素值取反（模擬繪製效果）。

    def __init__(self, poly_data, renderer):  # 初始化方法，接收 PolyData 和渲染器。
        super().__init__()  # 調用父類的初始化方法。
        self.renderer = renderer  # 儲存傳入的 VTK 渲染器。
        self.poly_data = poly_data  # 儲存傳入的 PolyData（3D 模型數據，例如牙齒模型）。
        self.colorActors = []  # 初始化高亮演員列表，儲存選取區域的可視化演員。
        self.setup()  # 調用設置方法，初始化內部變數。
        self.AddObserver("MouseMoveEvent", self.onMouseMove)  # 綁定滑鼠移動事件。
        self.AddObserver("LeftButtonPressEvent", self.onLeftButtonDown)  # 綁定左鍵按下事件。
        self.AddObserver("LeftButtonReleaseEvent", self.onLeftButtonUp)  # 綁定左鍵釋放事件。

    def setup(self):  # 初始化內部變數，保持與 C++ 風格一致（PascalCase）。
        self.Internal = self.vtkInternal()  # 創建內部類實例，管理多邊形點。
        self.Moving = False  # 初始化移動狀態為 False，表示未在繪製。
        self.StartPosition = np.zeros(2, dtype=np.int32)  # 初始化起始位置（螢幕坐標）。
        self.EndPosition = np.zeros(2, dtype=np.int32)  # 初始化結束位置（螢幕坐標）。
        self.PixelArray = vtk.vtkUnsignedCharArray()  # 初始化像素數據陣列（RGB）。
        self.DrawPolygonPixels = True  # 初始化為繪製多邊形像素。

    def interactorSetter(self, interactor):  # 設置交互器。
        self.SetInteractor(interactor)  # 動態設置 VTK 交互器，避免建構子直接初始化。

    def DrawPolygon(self):  # 繪製多邊形到渲染窗口。
        tmpPixelArray = vtk.vtkUnsignedCharArray()  # 創建臨時像素數據陣列。
        tmpPixelArray.DeepCopy(self.PixelArray)  # 深拷貝當前像素數據。
        pixels = nps.vtk_to_numpy(tmpPixelArray)  # 將像素數據轉為 NumPy 陣列。
        renWin = self.GetInteractor().GetRenderWindow()  # 獲取渲染窗口。
        size = renWin.GetSize()  # 獲取渲染窗口的尺寸（寬、高）。
        for i in range(self.Internal.GetNumberOfPoints() - 1):  # 迭代多邊形的邊。
            StartPos = self.Internal.GetPoint(i)  # 獲取起始點。
            EndPos = self.Internal.GetPoint(i + 1)  # 獲取結束點。
            self.Internal.DrawPixels(StartPos, EndPos, pixels, size)  # 繪製邊的像素。
        if self.Internal.GetNumberOfPoints() >= 3:  # 如果點數 >= 3，封閉多邊形。
            StartPos = self.Internal.GetPoint(0)  # 獲取第一個點。
            EndPos = self.Internal.GetPoint(self.Internal.GetNumberOfPoints() - 1)  # 獲取最後一個點。
            self.Internal.DrawPixels(StartPos, EndPos, pixels, size)  # 繪製封閉邊。
        renWin.SetPixelData(0, 0, size[0] - 1, size[1] - 1, pixels.flatten(), 0, 0)  # 更新渲染窗口的像素數據。
        renWin.Frame()  # 刷新渲染窗口。

    def DrawPolygonPixelsOn(self):  # 啟用多邊形像素繪製。
        self.DrawPolygonPixels = True  # 設置繪製多邊形像素狀態為 True。

    def DrawPolygonPixelsOff(self):  # 禁用多邊形像素繪製。
        self.DrawPolygonPixels = False  # 設置繪製多邊形像素狀態為 False。

    def GetPolygonPoints(self):  # 獲取多邊形點。
        return self.Internal.points  # 返回多邊形點的 NumPy 陣列。

    def onLeftButtonDown(self, obj, event):  # 處理左鍵按下事件。
        if self.GetInteractor() is None:  # 如果交互器未設置，直接返回。
            return
        self.Moving = True  # 設置移動狀態為 True，表示開始繪製。
        renWin = self.GetInteractor().GetRenderWindow()  # 獲取渲染窗口。
        eventPos = self.GetInteractor().GetEventPosition()  # 獲取滑鼠點擊位置（螢幕坐標）。
        self.StartPosition[0], self.StartPosition[1] = eventPos[0], eventPos[1]  # 設置起始位置。
        self.EndPosition = self.StartPosition  # 初始結束位置等於起始位置。
        self.PixelArray.Initialize()  # 初始化像素數據陣列。
        self.PixelArray.SetNumberOfComponents(3)  # 設置像素數據為 RGB（3 分量）。
        size = renWin.GetSize()  # 獲取渲染窗口尺寸。
        self.PixelArray.SetNumberOfTuples(size[0] * size[1])  # 設置像素數據大小（寬 * 高）。
        self.pixels = None  # 初始化像素數據變數（未使用，可能是遺留代碼）。
        renWin.GetPixelData(0, 0, size[0] - 1, size[1] - 1, 1, self.PixelArray, 0)  # 獲取當前窗口的像素數據。
        self.Internal.Clear()  # 清除多邊形點列表。
        self.Internal.AddPoint(self.StartPosition[0], self.StartPosition[1])  # 添加起始點。
        self.InvokeEvent(vtk.vtkCommand.StartInteractionEvent)  # 觸發開始交互事件。
        super().OnLeftButtonDown()  # 調用父類的左鍵按下處理。

    def onLeftButtonUp(self, obj, event):  # 處理左鍵釋放事件。
        if self.GetInteractor() is None or not self.Moving:  # 如果交互器未設置或未在繪製，直接返回。
            return
        if self.DrawPolygonPixels:  # 如果啟用了多邊形像素繪製。
            renWin = self.GetInteractor().GetRenderWindow()  # 獲取渲染窗口。
            size = renWin.GetSize()  # 獲取渲染窗口尺寸。
            pixels = nps.vtk_to_numpy(self.PixelArray)  # 將像素數據轉為 NumPy 陣列。
            renWin.SetPixelData(0, 0, size[0] - 1, size[1] - 1, pixels.flatten(), 0, 0)  # 更新渲染窗口像素數據。
            renWin.Frame()  # 刷新渲染窗口。
        self.Moving = False  # 設置移動狀態為 False，表示結束繪製。
        self.InvokeEvent(vtkCommand.SelectionChangedEvent)  # 觸發選取變更事件。
        self.InvokeEvent(vtkCommand.EndPickEvent)  # 觸發結束拾取事件。
        self.InvokeEvent(vtkCommand.EndInteractionEvent)  # 觸發結束交互事件。
        self.getSelectArea(self.GetPolygonPoints())  # 處理選取的多邊形區域。
        super().OnLeftButtonUp()  # 調用父類的左鍵釋放處理。

    def onMouseMove(self, obj, event):  # 處理滑鼠移動事件。
        if self.GetInteractor() is None or not self.Moving:  # 如果交互器未設置或未在繪製，直接返回。
            return
        eventPos = self.GetInteractor().GetEventPosition()  # 獲取滑鼠當前位置。
        self.EndPosition[0], self.EndPosition[1] = eventPos[0], eventPos[1]  # 更新結束位置。
        size = self.GetInteractor().GetRenderWindow().GetSize()  # 獲取渲染窗口尺寸。
        if self.EndPosition[0] > size[0] - 1:  # 限制 x 坐標不超過窗口寬度。
            self.EndPosition[0] = size[0] - 1
        if self.EndPosition[0] < 0:  # 限制 x 坐標不小於 0。
            self.EndPosition[0] = 0
        if self.EndPosition[1] > size[1] - 1:  # 限制 y 坐標不超過窗口高度。
            self.EndPosition[1] = size[1] - 1
        if self.EndPosition[1] < 0:  # 限制 y 坐標不小於 0。
            self.EndPosition[1] = 0
        lastPoint = self.Internal.GetPoint(self.Internal.GetNumberOfPoints() - 1)  # 獲取最後一個點。
        newPoint = self.EndPosition  # 獲取當前滑鼠位置。
        if np.linalg.norm(lastPoint - newPoint) > 10:  # 如果新點與最後一點距離大於 10 像素。
            self.Internal.AddPoint(*newPoint)  # 添加新點到多邊形點列表。
            if self.DrawPolygonPixels:  # 如果啟用了多邊形像素繪製。
                self.DrawPolygon()  # 繪製多邊形。
        super().OnMouseMove()  # 調用父類的滑鼠移動處理。

    def SetDrawPolygonPixels(self, drawPolygonPixels):  # 設置是否繪製多邊形像素。
        self.DrawPolygonPixels = drawPolygonPixels  # 更新繪製多邊形像素狀態。

    def getSelectArea(self, select_point):  # 處理選取的多邊形區域。
        w, h = self.renderer.GetRenderWindow().GetSize()  # 獲取渲染窗口尺寸。
        mask = np.zeros((h, w), dtype=np.uint8)  # 創建全黑的 2D 遮罩（高 x 寬）。
        cv2.fillPoly(mask, [np.array(select_point, dtype=np.int32)], 255)  # 在遮罩上繪製多邊形（白色填充）。
        coord = vtk.vtkCoordinate()  # 創建 VTK 坐標轉換物件。
        coord.SetCoordinateSystemToWorld()  # 設置坐標系統為世界坐標。
        selected_ids = vtk.vtkIdTypeArray()  # 創建 VTK ID 陣列，儲存選取的點 ID。
        selected_ids.SetNumberOfComponents(1)  # 設置 ID 陣列為單分量。
        for ptId in range(self.poly_data.GetNumberOfPoints()):  # 迭代模型的所有點。
            world_point = self.poly_data.GetPoint(ptId)  # 獲取點的世界坐標。
            coord.SetValue(world_point)  # 設置坐標值為世界坐標。
            display_point = coord.GetComputedDisplayValue(self.renderer)  # 將世界坐標轉為螢幕坐標。
            x, y = int(display_point[0]), int(display_point[1])  # 轉為整數坐標。
            if 0 <= x < w and 0 <= y < h and mask[y, x] == 255:  # 如果點在遮罩範圍內且為白色。
                selected_ids.InsertNextValue(ptId)  # 將點 ID 添加到選取列表。
        self.setClipRange(selected_ids)  # 設置選取範圍的點 ID。

    def setClipRange(self, selected_ids):  # 設置選取範圍的點 ID。
        self.selected_ids = selected_ids  # 儲存選取的點 ID 陣列。

    def getClip(self):  # 獲取選取範圍的點 ID。
        return self.selected_ids  # 返回選取的點 ID 陣列。

class LassoAreaColor:  # 定義 LassoAreaColor 類，用於高亮顯示選取點。
    def __init__(self, poly_data, renderer, interactor):  # 初始化方法，接收 PolyData、渲染器和交互器。
        self.poly_data = poly_data  # 儲存傳入的 PolyData。
        self.renderer = renderer  # 儲存傳入的渲染器。
        self.interactor = interactor  # 儲存傳入的交互器。
        self.colorActors = []  # 初始化高亮演員列表。

    def show_all_area(self, select_ids):  # 高亮顯示選取的點。
        points = vtk.vtkPoints()  # 創建 VTK 點集。
        for i in range(select_ids.GetNumberOfTuples()):  # 迭代選取的點 ID。
            try:
                point_id = select_ids.GetValue(i)  # 獲取點 ID。
                x, y, z = self.poly_data.GetPoint(point_id)  # 獲取點的世界坐標。
                points.InsertNextPoint(x, y, z)  # 將點添加到點集。
            except Exception as e:
                print(f"[ERROR] point_id={point_id}: {e}")  # 打印錯誤訊息。
        poly_data = vtk.vtkPolyData()  # 創建 VTK PolyData。
        poly_data.SetPoints(points)  # 設置點集。
        vertex_filter = vtk.vtkVertexGlyphFilter()  # 創建頂點過濾器，將點轉為可視化圖元。
        vertex_filter.SetInputData(poly_data)  # 設置輸入 PolyData。
        vertex_filter.Update()  # 更新過濾器。
        mapper = vtk.vtkPolyDataMapper()  # 創建 VTK 映射器。
        mapper.SetInputConnection(vertex_filter.GetOutputPort())  # 設置輸入為過濾器輸出。
        actor = vtk.vtkActor()  # 創建 VTK 演員。
        actor.SetMapper(mapper)  # 設置演員的映射器。
        actor.GetProperty().SetColor(1.0, 0.0, 0.0)  # 設置顏色為紅色（RGB: 1, 0, 0）。
        actor.GetProperty().SetPointSize(5)  # 設置點大小為 5 像素。
        self.colorActors.append(actor)  # 將演員添加到高亮演員列表。
        self.renderer.AddActor(actor)  # 將演員添加到渲染器。
        self.renderer.GetRenderWindow().Render()  # 渲染窗口。
        if self.interactor is not None:  # 如果交互器存在，再次渲染（可能為兼容性）。
            self.interactor.GetRenderWindow().Render()

    def unRenderAllSelectors(self):  # 移除所有高亮演員。
        for colorActor in self.colorActors:  # 迭代高亮演員列表。
            self.renderer.RemoveActor(colorActor)  # 移除每個演員。
        if self.interactor:  # 如果交互器存在，重新渲染。
            self.interactor.GetRenderWindow().Render()