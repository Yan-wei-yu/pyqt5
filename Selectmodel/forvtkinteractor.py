import vtk
from .Point import PointInteractor
from .Lasso import LassoInteractor,LassoAreaColor
from .box import BoxInteractor


class HighlightInteractorStyle(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self,interactor,renderer): #接收class AimodelView的互動器；左視圖的渲染器
        super().__init__()
        self.interactor = interactor # 指派class AimodelView的互動器給self
        self.renderer = renderer # 指派左視圖的渲染器給self
        # 選取模式開關
        self.modes = {
            "box": False,
            "point": False,
            "lasso": False
        }
        self.throughBtnMode = False  # 穿透模式

        self.box_func = None # 繪製box的物件
        self.lasso_func = None # 繪製lasso的物件
        self.lassoareacolor = None #塗上lasso選取範圍的顏色的物件

        self.start_position = None # 矩形選取的起始位置
        self.end_position = None # 矩形選取的結束位置
        self.mapper = vtk.vtkPolyDataMapper()
        self.actor = vtk.vtkActor()

        # 選取模式監聽器
        self.AddObserver("KeyPressEvent", self.modeSltKeyPress)
        self.AddObserver("LeftButtonPressEvent", self.onLeftButtonDown)
        self.AddObserver("LeftButtonReleaseEvent", self.onLeftButtonUp)
        self.AddObserver("RightButtonPressEvent", self.onRightButtonDown)
        self.AddObserver("RightButtonReleaseEvent", self.onRightButtonUp)
        self.AddObserver("MiddleButtonPressEvent", self.onMiddleButtonPressEvent)
        self.AddObserver("MiddleButtonReleaseEvent", self.onMiddleButtonReleaseEvent)
        self.AddObserver("MouseWheelForwardEvent", self.onMouseWheelForwardEvent)
        self.AddObserver("MouseWheelBackwardEvent", self.onMouseWheelBackwardEvent)

    def SetPolyData(self, polydata): #polydata接收class AimodelView的polydata
        self.polydata = polydata
        self.point_func = PointInteractor(self.polydata)

    def toggleMode(self, mode):
        if self.modes[mode]: # 如果當前模式已經啟用，則關閉它
            self.modes[mode] = False # 關閉當前模式
        else: # 如果當前模式未啟用，則關閉所有其他模式並啟用當前模式
            for key in self.modes: # 遍歷所有模式
                self.modes[key] = False # 關閉所有模式
            self.modes[mode] = True # 啟用當前模式
    '''因應直接切換至矩形、套索選取模式'''
    def _activate_box(self): 
        if self.lasso_func:
            self._deactivate_lasso() # 如果由l直接切換到c，清除lasso物件、渲染資料、互動器
        if self.box_func:
            return # 防止重複按下，創建新的box物件

        self.box_func = BoxInteractor(self.polydata, self.renderer) # 繪製box的物件
        self.box_func.interactorSetter(self.interactor) # 設定box物件的互動器
        self.toggleMode("box") # 切換成box模式
    def _deactivate_box(self):
        self.box_func.unRenderAllSelectors() # 消除染色的區塊
        self.box_func.interactorSetter(None) # 關掉box物件的互動器
        self.box_func = None # 關閉box物件
    def _activate_point(self):
        return
    def _deactivate_point(self):
        return
    def _activate_lasso(self):
        if self.box_func: 
            self._deactivate_box() # 如果由c直接切換到l，清除box物件、渲染資料、互動器
        if self.lasso_func:
            return # 防止重複按下，創建新的lasso物件

        self.lasso_func = LassoInteractor(self.polydata, self.renderer) # 繪製lasso的物件
        self.lassoareacolor = LassoAreaColor(self.polydata, self.renderer,self.interactor) # 塗上lasso選取範圍的物件
        self.lasso_func.interactorSetter(self.interactor) # 設定lasso物件的互動器
        self.toggleMode("lasso") # 切換成lasso模式
    def _deactivate_lasso(self):
        self.lassoareacolor.unRenderAllSelectors() #消除染色的區塊
        self.lasso_func.interactorSetter(None) # 關掉lasso物件的互動器
        self.lasso_func = None # 關閉lasso物件
    
    '''鍵盤事件'''
    def modeSltKeyPress(self, obj, event):
        self.key = self.GetInteractor().GetKeySym() # 取得按下的鍵
        
        # 切換選取模式
        if self.key in ["c", "C"]:
            self._activate_box() # 切換成box模式
        elif self.key in ["p", "P"]:
            return
        elif self.key in ["l", "L"]:
            self._activate_lasso() # 切換成lasso模式

            
        # 刪除範圍
        elif self.key == "Delete":
            if self.modes["box"]:
                self.boxRemove(self.box_func.selection_frustum) # 刪除box選取的範圍
                self.box_func.unRenderAllSelectors() # 消除染色的區塊
            elif self.modes["point"]:
                self.keep_select_area(self.point_func.total_path_point)
                self.point_func.unRenderAllSelectors(self.renderer, self.GetInteractor())
            elif self.modes["lasso"]:
                self.lassoRemove(self.polydata, self.actor, self.lasso_func.selected_ids) # 刪除lasso選取的範圍
                self.lassoareacolor.unRenderAllSelectors() # 消除染色的區塊

        # 點選取範圍封閉
        elif self.key == "Return" and self.modes["point"]:
            self.point_func.closeArea(self.interactor, self.renderer)


        # 穿透模式切換
        elif self.key in ["t", "T"]:
            self.throughBtnMode = not self.throughBtnMode
            print(f"Through mode: {self.throughBtnMode}")

    def boxRemove(self, selection_frustum):
        if not isinstance(selection_frustum, vtk.vtkImplicitFunction): # 如果不是 vtkImplicitFunction，則返回
            return

        clipper = vtk.vtkClipPolyData() # 創建裁切器
        clipper.SetInputData(self.polydata) # 輸入資料為class AimodelView的polydata
        clipper.SetClipFunction(selection_frustum) # 設定裁切函數為選取的區域
        clipper.GenerateClippedOutputOff() # 不生成裁切後的輸出
        clipper.Update() # 更新裁切器

        new_poly_data = clipper.GetOutput() # 獲取裁切後的輸出
        if new_poly_data.GetNumberOfCells() == 0: # 如果沒有裁切後的輸出，則返回
            return

        self.polydata.DeepCopy(new_poly_data) # 拷貝裁切後的輸出，避免讓整個畫面被選染成上一個選取的資料
        self.renderer.RemoveActor(self.actor) # 移除上一個選取的範圍
        self.mapper.ScalarVisibilityOff() # 避免根據vtk選取的顏色來渲染
        self.mapper.SetInputData(self.polydata) # 設定映射器的輸入資料
        self.GetInteractor().GetRenderWindow().Render() # 渲染視窗

    def keep_select_area(self, loop_points):
        if loop_points.GetNumberOfPoints() < 3:
            return

        # 使用 SelectPolyData 建立封閉區域選取
        select = vtk.vtkSelectPolyData()
        select.SetInputData(self.polydata)
        select.SetLoop(loop_points)
        select.GenerateSelectionScalarsOn()
        select.SetSelectionModeToSmallestRegion()
        select.Update()

        # 用 ClipPolyData 裁切選取區域
        clip = vtk.vtkClipPolyData()
        clip.SetInputConnection(select.GetOutputPort())
        clip.InsideOutOn()
        clip.Update()

        # 轉為 PolyData
        geometry = vtk.vtkGeometryFilter()
        geometry.SetInputConnection(clip.GetOutputPort())
        geometry.Update()

        new_poly_data = geometry.GetOutput()
        if new_poly_data.GetNumberOfCells() == 0:
            return

        self.renderer.RemoveActor(self.actor)
        self.mapper.SetInputData(new_poly_data)
        self.mapper.ScalarVisibilityOff()
        self.actor.SetMapper(self.mapper)
        self.renderer.AddActor(self.actor)
        self.polydata.DeepCopy(new_poly_data)
        self.GetInteractor().GetRenderWindow().Render()
    
    def lassoRemove(self,poly_data,actor, selected_ids):
        poly_data.BuildLinks()#反查頂點連接的面
        points = vtk.vtkPoints() # 創建一個 vtkPoints 對象來儲存選取的點
        cell_ids = vtk.vtkIdList() # 儲存連接的cell id
        cells_to_delete = set() # 儲存要刪除的cell id
        for i in range(selected_ids.GetNumberOfTuples()): # 迭代所有選取的點
            try: # 確認是否有點
                point_id = selected_ids.GetValue(i) # 取得點的id
                x, y, z = poly_data.GetPoint(point_id) # 取得點的座標
                points.InsertNextPoint(x, y, z) # 將點加入vtkPoints

                poly_data.GetPointCells(point_id, cell_ids) # 取得連接的cell id
                for j in range(cell_ids.GetNumberOfIds()): # 迭代所有cell id
                    cells_to_delete.add(cell_ids.GetId(j)) # 將cell id加入刪除列表
            except Exception as e: # 如果沒有點，擲回錯誤訊息
                print(f"[ERROR] point_id={point_id}: {e}")
        new_cells = vtk.vtkCellArray() # 創建一個新的cell array來儲存新的cell

        id_list = vtk.vtkIdList() # 創建一個vtkIdList來儲存cell的id
        for cid in range(poly_data.GetNumberOfCells()): # 迭代所有cell id
            if cid in cells_to_delete: # 如果cell id在刪除列表中，則跳過
                continue #  跳過這個cell id
            poly_data.GetCellPoints(cid, id_list) # 取得cell的點
            new_cells.InsertNextCell(id_list) # 將cell的點加入新的cell array
        poly_data.SetPolys(new_cells) # 設定新的cell array為poly_data的cell array
        poly_data.Modified() # 更新poly_data

        self.mapper.ScalarVisibilityOff() # 避免根據vtk選取的顏色來渲染
        self.mapper.SetInputData(poly_data) # 設定映射器的輸入資料
        self.actor.SetMapper(self.mapper) # 設定Actor的映射器
        self.actor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.renderer.AddActor(self.actor) # 將Actor加入渲染器   
        self.GetInteractor().GetRenderWindow().Render() # 渲染視窗
    '''繼承父類別'''
    def onMiddleButtonPressEvent(self, obj, event):
        super().OnMiddleButtonDown()
    def onMiddleButtonReleaseEvent(self, obj, event):
        super().OnMiddleButtonUp()
    def onMouseWheelForwardEvent(self, obj, event):
        super().OnMouseWheelForward()
    def onMouseWheelBackwardEvent(self, obj, event):
        super().OnMouseWheelBackward()
    def onRightButtonDown(self, obj, event):
        super().OnLeftButtonDown() # 將右鍵事件轉換為左鍵旋轉事件，因為選取模式都是使用左鍵做選取
    def onRightButtonUp(self, obj, event):
        super().OnLeftButtonUp() # 將右鍵事件轉換為左鍵旋轉事件，因為選取模式都是使用左鍵做選取

    def onLeftButtonDown(self, obj, event):
        if self.modes["box"]:
            self.box_func.unRenderAllSelectors() # 消除染色的區塊
            self.box_func.onLeftButtonPress(obj,event) # 按下左鍵進入box模式，先紀錄起始位置
        elif self.modes["point"]:
            self.point_func.onLeftButtonDown(obj, event, self.GetInteractor(), self.renderer)
        elif self.modes["lasso"]:
            self.lassoareacolor.unRenderAllSelectors() # 消除染色的區塊
            self.lasso_func.interactorSetter(self.interactor) # 設定lasso物件的互動器
            self.lasso_func.onLeftButtonDown(obj, event) 
            self.lasso_func.onMouseMove(obj,event)

    def onLeftButtonUp(self, obj, event):
        if self.modes["box"]:
            self.box_func.onLeftButtonUp(obj,event) # 按下左鍵進入box模式，紀錄結束位置
            select_area = self.box_func.boxSelectArea() # 繪製box選取的區域
            self.box_func.show_all_area(select_area) # 顯示box選取的區域
        elif self.modes["lasso"]:
            self.lasso_func.interactorSetter(self.interactor) # 設定lasso物件的互動器
            self.lasso_func.onLeftButtonUp(obj, event) # 紀錄結束位置
            self.lassoareacolor.show_all_area(self.lasso_func.selected_ids) # 顯示lasso選取的區域
        
    