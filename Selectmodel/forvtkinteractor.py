import vtk
from .Point import PointInteractor
from .Lasso import LassoInteractor

class HighlightInteractorStyle(vtk.vtkInteractorStyleRubberBand3D):
    def __init__(self,interactor,renderer):
        super().__init__()
        self.interactor = interactor
        self.renderer = renderer
        # 選取模式開關
        self.modes = {
            "box": False,
            "point": False,
            "lasso": False
        }
        self.throughBtnMode = False  # 穿透模式

        self.start_position = None
        self.end_position = None
        self.geometry_filter = None
        self.selected_poly_data = None
        self.extract_geometry = None
        self.mapper = vtk.vtkPolyDataMapper()
        self.actor = vtk.vtkActor()
        self.boxArea = vtk.vtkAreaPicker()

        # 選取模式監聽器
        self.AddObserver("KeyPressEvent", self.modeSltKeyPress)
        self.AddObserver("LeftButtonReleaseEvent", self.onLeftButtonUp)
        self.AddObserver("LeftButtonPressEvent", self.onLeftButtonDown)

    def SetPolyData(self, polydata):
        self.polydata = polydata
        self.point_func = PointInteractor(self.polydata)

    def toggleMode(self, mode):
        if self.modes[mode]:
            self.modes[mode] = False
        else:
            for key in self.modes:
                self.modes[key] = False
            self.modes[mode] = True

    def modeSltKeyPress(self, obj, event):
        self.key = self.GetInteractor().GetKeySym()

        # 模式切換
        if self.key in ["c", "C"]:
            self.toggleMode("box")
        elif self.key in ["p", "P"]:
            was_on = self.modes.get("point", False) #確認是否在預設關閉
            self.toggleMode("point") # 切換成point模式
            if not was_on and self.modes["point"]: #確認point模式是否開啟
                self.point_func = PointInteractor(self.polydata,self.interactor,self.renderer) # 創建point物件
            elif was_on and not self.modes["point"]: # 確認point模式是否關閉
                self.point_func.interactor = None # 關point物件的互動器
        elif self.key in ["l", "L"]:
            was_on = self.modes.get("lasso", False) #確認是否在預設關閉
            self.toggleMode("lasso") # 切換成lasso模式
            if not was_on and self.modes["lasso"]: #確認lasso模式是否開啟
                self.lasso_func = LassoInteractor(self.polydata,self.interactor,self.renderer) # 創建lasso物件
            elif was_on and not self.modes["lasso"]: # 確認lasso模式是否關閉
                self.lasso_func.interactorSetter(None) # 關lasso物件的互動器

        # 刪除範圍
        elif self.key == "Delete":
            if self.modes["box"]:
                self.removeCells(self.boxArea.GetFrustum())
            elif self.modes["point"]:
                self.keep_select_area(self.point_func.total_path_point)
                self.point_func.unRenderAllSelectors(self.renderer, self.GetInteractor())
            elif self.modes["lasso"]:
                self.lassoClip(self.polydata, self.actor, self.lasso_func.selected_ids)

        # 點選取範圍封閉
        elif self.key == "Return" and self.modes["point"]:
            self.point_func.closeArea(self.interactor, self.renderer)


        # 穿透模式切換
        elif self.key in ["t", "T"]:
            self.throughBtnMode = not self.throughBtnMode
            print(f"Through mode: {self.throughBtnMode}")

    def removeCells(self, selection_frustum):
        if not isinstance(selection_frustum, vtk.vtkImplicitFunction):
            return

        clipper = vtk.vtkClipPolyData()
        clipper.SetInputData(self.polydata)
        clipper.SetClipFunction(selection_frustum)
        clipper.GenerateClippedOutputOff()
        clipper.Update()

        new_poly_data = clipper.GetOutput()
        if new_poly_data.GetNumberOfCells() == 0:
            return

        self.polydata.DeepCopy(new_poly_data)
        self.renderer.RemoveActor(self.actor)
        self.mapper.ScalarVisibilityOff()
        self.mapper.SetInputData(self.polydata)
        self.GetInteractor().GetRenderWindow().Render()

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
    
    def lassoClip(self,poly_data,actor, selected_ids):
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

        self.mapper.ScalarVisibilityOff()
        self.mapper.SetInputData(poly_data) # 設定映射器的輸入資料
        self.actor.SetMapper(self.mapper) # 設定Actor的映射器
        self.actor.GetProperty().SetColor(1.0, 1.0, 1.0)
        self.renderer.AddActor(self.actor) # 將Actor加入渲染器   
        self.GetInteractor().GetRenderWindow().Render() # 渲染視窗

    def onLeftButtonDown(self, obj, event):
        if self.modes["box"]:
            self.start_position = self.GetInteractor().GetEventPosition()
        elif self.modes["point"]:
            self.point_func.onLeftButtonDown(obj, event, self.GetInteractor(), self.renderer)
        elif self.modes["lasso"]:
            self.lasso_func.interactorSetter(self.interactor)
            self.lasso_func.onLeftButtonDown(obj, event)
            self.lasso_func.onMouseMove(obj,event)

    def onLeftButtonUp(self, obj, event):
        if self.modes["box"]:
            self.end_position = self.GetInteractor().GetEventPosition()
            self.boxArea.AreaPick(self.start_position[0], self.start_position[1],
                                  self.end_position[0], self.end_position[1], self.renderer)
            self.selection_frustum = self.boxArea.GetFrustum()

            self.extract = vtk.vtkExtractGeometry()
            self.extract.SetInputData(self.polydata)
            self.extract.SetImplicitFunction(self.selection_frustum)
            if self.throughBtnMode:
                self.extract.ExtractInsideOn()
            else:
                self.extract.ExtractBoundaryCellsOff()
            self.extract.Update()
            self.selected = self.extract.GetOutput()

            if self.selected.GetNumberOfCells() > 0:
                self.geometry_filter = vtk.vtkGeometryFilter()
                self.geometry_filter.SetInputData(self.selected)
                self.geometry_filter.Update()
                self.mapper.SetInputData(self.geometry_filter.GetOutput())
                self.actor.SetMapper(self.mapper)
                self.actor.GetProperty().SetColor(0.0, 1.0, 1.0)
                self.renderer.AddActor(self.actor)
            self.OnLeftButtonUp()
            self.GetInteractor().GetRenderWindow().Render()
        elif self.modes["lasso"]:
            self.lasso_func.interactorSetter( self.interactor)
            self.lasso_func.onLeftButtonUp(obj, event)