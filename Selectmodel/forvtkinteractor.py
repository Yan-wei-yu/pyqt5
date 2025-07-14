# 主要目的：此程式碼定義了一個基於 VTK 的 `HighlightInteractorStyle` 類，繼承自 `vtk.vtkInteractorStyleTrackballCamera`，用於在牙科 3D 模型處理場景中實現交互式選取功能。它支援三種選取模式（矩形框 box、點選 point、套索 lasso），並提供刪除選取區域、穿透模式切換和模型高亮顯示的功能，適用於 `AimodelView` 等視圖的交互式 3D 模型編輯。

import vtk  # 導入 VTK 庫，用於 3D 模型處理和視覺化。
from .Point import PointInteractor  # 導入 PointInteractor 類，用於點選交互。
from .Lasso import LassoInteractor, LassoAreaColor  # 導入 LassoInteractor 和 LassoAreaColor 類，用於套索選取和高亮顯示。
from .box import BoxInteractor  # 導入 BoxInteractor 類，用於矩形框選取。

class HighlightInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):  # 定義 HighlightInteractorStyle 類，繼承 VTK 的軌跡球攝影機交互樣式。
    def __init__(self, interactor, renderer):  # 初始化方法，接收交互器和渲染器。
        super().__init__()  # 調用父類的初始化方法。
        self.interactor = interactor  # 儲存傳入的交互器（來自 AimodelView 的 VTK 交互器）。
        self.renderer = renderer  # 儲存左視圖的渲染器（VTK 渲染器）。
        # 選取模式開關
        self.modes = {
            "box": False,  # 矩形框選模式，預設關閉。
            "point": False,  # 點選模式，預設關閉。
            "lasso": False  # 套索選取模式，預設關閉。
        }
        self.throughBtnMode = False  # 穿透模式，預設關閉。
        self.box_func = None  # 矩形框選物件，初始為 None。
        self.lasso_func = None  # 套索選取物件，初始為 None。
        self.lassoareacolor = None  # 套索選取區域高亮物件，初始為 None。
        self.start_position = None  # 矩形選取的起始位置，初始為 None。
        self.end_position = None  # 矩形選取的結束位置，初始為 None。
        self.mapper = vtk.vtkPolyDataMapper()  # 創建 VTK 映射器，用於渲染 PolyData。
        self.actor = vtk.vtkActor()  # 創建 VTK 演員，用於顯示模型。

        # 選取模式監聽器
        self.AddObserver("KeyPressEvent", self.modeSltKeyPress)  # 綁定鍵盤按鍵事件。
        self.AddObserver("LeftButtonPressEvent", self.onLeftButtonDown)  # 綁定左鍵按下事件。
        self.AddObserver("LeftButtonReleaseEvent", self.onLeftButtonUp)  # 綁定左鍵釋放事件。
        self.AddObserver("RightButtonPressEvent", self.onRightButtonDown)  # 綁定右鍵按下事件。
        self.AddObserver("RightButtonReleaseEvent", self.onRightButtonUp)  # 綁定右鍵釋放事件。
        self.AddObserver("MiddleButtonPressEvent", self.onMiddleButtonPressEvent)  # 綁定中鍵按下事件。
        self.AddObserver("MiddleButtonReleaseEvent", self.onMiddleButtonReleaseEvent)  # 綁定中鍵釋放事件。
        self.AddObserver("MouseWheelForwardEvent", self.onMouseWheelForwardEvent)  # 綁定鼠標滾輪前滾事件。
        self.AddObserver("MouseWheelBackwardEvent", self.onMouseWheelBackwardEvent)  # 綁定鼠標滾輪後滾事件。

    def SetPolyData(self, polydata):  # 設置 PolyData（來自 AimodelView 的上顎或下顎模型數據）。
        self.polydata = polydata  # 儲存傳入的 PolyData。
        self.point_func = PointInteractor(self.polydata)  # 初始化點選交互物件，傳入 PolyData。

    def toggleMode(self, mode):  # 切換選取模式的通用方法。
        if self.modes[mode]:  # 如果當前模式已啟用。
            self.modes[mode] = False  # 關閉該模式。
        else:  # 如果當前模式未啟用。
            for key in self.modes:  # 遍歷所有模式。
                self.modes[key] = False  # 關閉所有其他模式。
            self.modes[mode] = True  # 啟用當前模式。

    '''因應直接切換至矩形、套索選取模式'''
    def _activate_box(self):  # 啟用矩形框選模式。
        if self.lasso_func:  # 如果套索模式已啟用。
            self._deactivate_lasso()  # 清除套索相關物件和渲染數據。
        if self.box_func:  # 如果矩形框選物件已存在。
            return  # 防止重複創建，直接返回。
        self.box_func = BoxInteractor(self.polydata, self.renderer)  # 創建矩形框選物件。
        self.box_func.interactorSetter(self.interactor)  # 設置框選物件的交互器。
        self.toggleMode("box")  # 切換到矩形框選模式。

    def _deactivate_box(self):  # 停用矩形框選模式。
        self.box_func.unRenderAllSelectors()  # 移除所有框選的高亮區域。
        self.box_func.interactorSetter(None)  # 清除框選物件的交互器。
        self.box_func = None  # 清空框選物件。

    def _activate_point(self):  # 啟用點選模式（目前未實現）。
        return  # 空實現，待補充。

    def _deactivate_point(self):  # 停用點選模式（目前未實現）。
        return  # 空實現，待補充。

    def _activate_lasso(self):  # 啟用套索選取模式。
        if self.box_func:  # 如果矩形框選模式已啟用。
            self._deactivate_box()  # 清除框選相關物件和渲染數據。
        if self.lasso_func:  # 如果套索選取物件已存在。
            return  # 防止重複創建，直接返回。
        self.lasso_func = LassoInteractor(self.polydata, self.renderer)  # 創建套索選取物件。
        self.lassoareacolor = LassoAreaColor(self.polydata, self.renderer, self.interactor)  # 創建套索區域高亮物件。
        self.lasso_func.interactorSetter(self.interactor)  # 設置套索物件的交互器。
        self.toggleMode("lasso")  # 切換到套索選取模式。

    def _deactivate_lasso(self):  # 停用套索選取模式。
        self.lassoareacolor.unRenderAllSelectors()  # 移除所有套索選取的高亮區域。
        self.lasso_func.interactorSetter(None)  # 清除套索物件的交互器。
        self.lasso_func = None  # 清空套索物件。

    '''鍵盤事件'''
    def modeSltKeyPress(self, obj, event):  # 處理鍵盤按鍵事件。
        self.key = self.GetInteractor().GetKeySym()  # 獲取按下的鍵符號。
        
        # 切換選取模式
        if self.key in ["c", "C"]:  # 按下 'c' 或 'C' 鍵。
            self._activate_box()  # 啟用矩形框選模式。
        elif self.key in ["p", "P"]:  # 按下 'p' 或 'P' 鍵。
            return  # 點選模式未實現，無操作。
        elif self.key in ["l", "L"]:  # 按下 'l' 或 'L' 鍵。
            self._activate_lasso()  # 啟用套索選取模式。
            
        # 刪除範圍
        elif self.key == "Delete":  # 按下 'Delete' 鍵。
            if self.modes["box"]:  # 如果處於矩形框選模式。
                self.boxRemove(self.box_func.selection_frustum)  # 刪除框選區域的內容。
                self.box_func.unRenderAllSelectors()  # 移除框選高亮區域。
            elif self.modes["point"]:  # 如果處於點選模式。
                self.keep_select_area(self.point_func.total_path_point)  # 保留點選區域。
                self.point_func.unRenderAllSelectors(self.renderer, self.GetInteractor())  # 移除點選高亮區域。
            elif self.modes["lasso"]:  # 如果處於套索選取模式。
                self.lassoRemove(self.polydata, self.actor, self.lasso_func.selected_ids)  # 刪除套索選取區域的內容。
                self.lassoareacolor.unRenderAllSelectors()  # 移除套索高亮區域。

        # 點選取範圍封閉
        elif self.key == "Return" and self.modes["point"]:  # 按下 'Return' 鍵且處於點選模式。
            self.point_func.closeArea(self.interactor, self.renderer)  # 封閉點選區域。

        # 穿透模式切換
        elif self.key in ["t", "T"]:  # 按下 't' 或 'T' 鍵。
            self.throughBtnMode = not self.throughBtnMode  # 切換穿透模式開關。
            print(f"Through mode: {self.throughBtnMode}")  # 打印穿透模式狀態。

    def boxRemove(self, selection_frustum):  # 刪除矩形框選區域的內容。
        if not isinstance(selection_frustum, vtk.vtkImplicitFunction):  # 檢查選取區域是否為 VTK 隱式函數。
            return  # 若不是，則直接返回。
        clipper = vtk.vtkClipPolyData()  # 創建 VTK 裁切器。
        clipper.SetInputData(self.polydata)  # 設置輸入 PolyData（來自 AimodelView）。
        clipper.SetClipFunction(selection_frustum)  # 設置裁切函數為框選區域。
        clipper.GenerateClippedOutputOff()  # 不生成裁切後的輸出。
        clipper.Update()  # 更新裁切器。
        new_poly_data = clipper.GetOutput()  # 獲取裁切後的 PolyData。
        if new_poly_data.GetNumberOfCells() == 0:  # 如果裁切後無內容。
            return  # 直接返回。
        self.polydata.DeepCopy(new_poly_data)  # 深拷貝裁切後的 PolyData，避免影響原始數據。
        self.renderer.RemoveActor(self.actor)  # 移除之前的演員。
        self.mapper.ScalarVisibilityOff()  # 關閉標量可視化，避免使用選取顏色渲染。
        self.mapper.SetInputData(self.polydata)  # 設置映射器的輸入為新的 PolyData。
        self.GetInteractor().GetRenderWindow().Render()  # 重新渲染窗口。

    def keep_select_area(self, loop_points):  # 保留點選封閉區域的內容。
        if loop_points.GetNumberOfPoints() < 3:  # 如果點數少於 3，無法形成封閉區域。
            return  # 直接返回。
        # 使用 SelectPolyData 建立封閉區域選取
        select = vtk.vtkSelectPolyData()  # 創建 VTK 選取器。
        select.SetInputData(self.polydata)  # 設置輸入 PolyData。
        select.SetLoop(loop_points)  # 設置封閉路徑點。
        select.GenerateSelectionScalarsOn()  # 啟用選取標量生成。
        select.SetSelectionModeToSmallestRegion()  # 選擇最小區域。
        select.Update()  # 更新選取器。
        # 用 ClipPolyData 裁切選取區域
        clip = vtk.vtkClipPolyData()  # 創建 VTK 裁切器。
        clip.SetInputConnection(select.GetOutputPort())  # 設置輸入為選取器的輸出。
        clip.InsideOutOn()  # 保留選取區域內的內容。
        clip.Update()  # 更新裁切器。
        # 轉為 PolyData
        geometry = vtk.vtkGeometryFilter()  # 創建幾何過濾器。
        geometry.SetInputConnection(clip.GetOutputPort())  # 設置輸入為裁切器的輸出。
        geometry.Update()  # 更新幾何過濾器。
        new_poly_data = geometry.GetOutput()  # 獲取新的 PolyData。
        if new_poly_data.GetNumberOfCells() == 0:  # 如果無內容。
            return  # 直接返回。
        self.renderer.RemoveActor(self.actor)  # 移除之前的演員。
        self.mapper.SetInputData(new_poly_data)  # 設置映射器的輸入為新的 PolyData。
        self.mapper.ScalarVisibilityOff()  # 關閉標量可視化。
        self.actor.SetMapper(self.mapper)  # 設置演員的映射器。
        self.renderer.AddActor(self.actor)  # 將演員添加到渲染器。
        self.polydata.DeepCopy(new_poly_data)  # 深拷貝新的 PolyData。
        self.GetInteractor().GetRenderWindow().Render()  # 重新渲染窗口。

    def lassoRemove(self, poly_data, actor, selected_ids):  # 刪除套索選取區域的內容。
        poly_data.BuildLinks()  # 構建 PolyData 的連結，支援頂點到單元的反向查詢。
        points = vtk.vtkPoints()  # 創建 VTK 點集，用於儲存選取的點。
        cell_ids = vtk.vtkIdList()  # 創建 VTK ID 列表，用於儲存單元 ID。
        cells_to_delete = set()  # 創建集合，儲存需要刪除的單元 ID。
        for i in range(selected_ids.GetNumberOfTuples()):  # 迭代所有選取的點 ID。
            try:  # 嘗試處理每個點 ID。
                point_id = selected_ids.GetValue(i)  # 獲取點的 ID。
                x, y, z = poly_data.GetPoint(point_id)  # 獲取點的座標。
                points.InsertNextPoint(x, y, z)  # 將點添加到點集。
                poly_data.GetPointCells(point_id, cell_ids)  # 獲取與該點關聯的單元 ID。
                for j in range(cell_ids.GetNumberOfIds()):  # 迭代所有關聯單元 ID。
                    cells_to_delete.add(cell_ids.GetId(j))  # 將單元 ID 添加到刪除集合。
            except Exception as e:  # 捕獲異常（例如無效點 ID）。
                print(f"[ERROR] point_id={point_id}: {e}")  # 打印錯誤訊息。
        new_cells = vtk.vtkCellArray()  # 創建新的單元陣列，用於儲存保留的單元。
        id_list = vtk.vtkIdList()  # 創建 VTK ID 列表，用於儲存單元中的點 ID。
        for cid in range(poly_data.GetNumberOfCells()):  # 迭代所有單元 ID。
            if cid in cells_to_delete:  # 如果單元 ID 在刪除集合中。
                continue  # 跳過該單元。
            poly_data.GetCellPoints(cid, id_list)  # 獲取單元的點 ID。
            new_cells.InsertNextCell(id_list)  # 將單元添加到新的單元陣列。
        poly_data.SetPolys(new_cells)  # 設置 PolyData 的新單元陣列。
        poly_data.Modified()  # 標記 PolyData 已修改。
        self.mapper.ScalarVisibilityOff()  # 關閉標量可視化，避免使用選取顏色渲染。
        self.mapper.SetInputData(poly_data)  # 設置映射器的輸入為更新後的 PolyData。
        self.actor.SetMapper(self.mapper)  # 設置演員的映射器。
        self.actor.GetProperty().SetColor(1.0, 1.0, 1.0)  # 設置演員顏色為白色。
        self.renderer.AddActor(self.actor)  # 將演員添加到渲染器。
        self.GetInteractor().GetRenderWindow().Render()  # 重新渲染窗口。

    '''繼承父類別'''
    def onMiddleButtonPressEvent(self, obj, event):  # 處理中鍵按下事件。
        super().OnMiddleButtonDown()  # 調用父類的中鍵按下處理。

    def onMiddleButtonReleaseEvent(self, obj, event):  # 處理中鍵釋放事件。
        super().OnMiddleButtonUp()  # 調用父類的中鍵釋放處理。

    def onMouseWheelForwardEvent(self, obj, event):  # 處理鼠標滾輪前滾事件。
        super().OnMouseWheelForward()  # 調用父類的滾輪前滾處理。

    def onMouseWheelBackwardEvent(self, obj, event):  # 處理鼠標滾輪後滾事件。
        super().OnMouseWheelBackward()  # 調用父類的滾輪後滾處理。

    def onRightButtonDown(self, obj, event):  # 處理右鍵按下事件。
        super().OnLeftButtonDown()  # 將右鍵按下轉為左鍵旋轉事件，保持標準交互行為。

    def onRightButtonUp(self, obj, event):  # 處理右鍵釋放事件。
        super().OnLeftButtonUp()  # 將右鍵釋放轉為左鍵旋轉事件，保持標準交互行為。

    def onLeftButtonDown(self, obj, event):  # 處理左鍵按下事件。
        if self.modes["box"]:  # 如果處於矩形框選模式。
            self.box_func.unRenderAllSelectors()  # 移除所有框選高亮區域。
            self.box_func.onLeftButtonPress(obj, event)  # 記錄框選起始位置。
        elif self.modes["point"]:  # 如果處於點選模式。
            self.point_func.onLeftButtonDown(obj, event, self.GetInteractor(), self.renderer)  # 處理點選事件。
        elif self.modes["lasso"]:  # 如果處於套索選取模式。
            self.lassoareacolor.unRenderAllSelectors()  # 移除所有套索高亮區域。
            self.lasso_func.interactorSetter(self.interactor)  # 設置套索物件的交互器。
            self.lasso_func.onLeftButtonDown(obj, event)  # 記錄套索選取起始位置。
            self.lasso_func.onMouseMove(obj, event)  # 處理滑鼠移動以繪製套索路徑。

    def onLeftButtonUp(self, obj, event):  # 處理左鍵釋放事件。
        if self.modes["box"]:  # 如果處於矩形框選模式。
            self.box_func.onLeftButtonUp(obj, event)  # 記錄框選結束位置。
            select_area = self.box_func.boxSelectArea()  # 繪製框選區域。
            self.box_func.show_all_area(select_area)  # 顯示框選高亮區域。
        elif self.modes["lasso"]:  # 如果處於套索選取模式。
            self.lasso_func.interactorSetter(self.interactor)  # 設置套索物件的交互器。
            self.lasso_func.onLeftButtonUp(obj, event)  # 記錄套索選取結束位置。
            self.lassoareacolor.show_all_area(self.lasso_func.selected_ids)  # 顯示套索選取高亮區域。
