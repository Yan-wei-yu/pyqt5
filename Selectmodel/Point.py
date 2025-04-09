import vtk

class TrimVisualize:
    def __init__(self, renderer):
        self.renderer = renderer
        self.projected_points = vtk.vtkPoints()
        self.poly_data_trim = vtk.vtkPolyData()
        self.trim_mapper = vtk.vtkPolyDataMapper()
        self.trim_actor = vtk.vtkActor()

    def connect_point_to_line(self, point_list):
        for point in point_list:
            self.projected_points.InsertNextPoint(point)
        lines = vtk.vtkCellArray()
        for i in range(len(point_list) - 1):
            line = vtk.vtkLine()
            line.GetPointIds().SetId(0, i)
            line.GetPointIds().SetId(1, i + 1)
            lines.InsertNextCell(line)
        self.poly_data_trim.SetPoints(self.projected_points)
        self.poly_data_trim.SetLines(lines)
        self.trim_mapper.SetInputData(self.poly_data_trim)
        self.trim_actor.SetMapper(self.trim_mapper)
        self.trim_actor.GetProperty().SetLineWidth(3)
        self.trim_actor.GetProperty().SetColor(0.0, 1.0, 0.0)
        self.renderer.AddActor(self.trim_actor)

    def removeLine(self):
        self.renderer.RemoveActor(self.trim_actor)
        self.projected_points.Initialize()
        self.poly_data_trim.Initialize()
        self.trim_mapper = vtk.vtkPolyDataMapper()
        self.trim_actor = vtk.vtkActor()

class PointInteractor(vtk.vtkInteractorStyleTrackballCamera):
    def __init__(self, poly_data):
        super().__init__()
        self.poly_data = poly_data
        self.dijkstra = vtk.vtkDijkstraGraphGeodesicPath()
        self.selectionPoints = vtk.vtkPoints()
        self.dijkstra.SetInputData(self.poly_data)
        self.sphereActors = []
        self.lineActors = []
        self.pathList = []
        self.meshNumList = []
        self.pick3DCoord = vtk.vtkCellPicker()

        self.loop = vtk.vtkImplicitSelectionLoop()
        self.total_length = 0
        # 新增功能：支援 undo 和 redo
        self.redoSphereActors = []
        self.redoLineActors = []
        self.redoPathList = []
        self.redoMeshNumList = []
        self.total_path_point = vtk.vtkPoints()  # 用於儲存所有投影點
        self.AddObserver("LeftButtonPressEvent", self.onLeftButtonDown)

    def onLeftButtonDown(self, obj, event, interactor, renderer):
        self.renderer = renderer
        self.interactor = interactor
        clickPos = interactor.GetEventPosition()
        picker = vtk.vtkCellPicker()
        # 選取位置轉成3D座標
        picker.Pick(clickPos[0],clickPos[1],0,renderer)
        # 給予pick3DCoord資料
        self.pick3DCoord.Pick(clickPos[0],clickPos[1],0,renderer)
        self.clickPath = vtk.vtkPoints()
        print(f"point coord: {self.poly_data.GetPoint(picker.GetPointId())}")
        # 選取輸入物件
        if(picker.GetCellId() != -1):
            
            # pathList存放使用者實際點選的點，並且賦予他們id
            self.pathList.append(picker.GetPointId())
            # 點選位置座標
            point_position = self.poly_data.GetPoint(picker.GetPointId())
            # 實體化球體
            sphereSource = vtk.vtkSphereSource()
            # 球體中心位置設定點選座標
            sphereSource.SetCenter(point_position)
            # 半徑設定0.02
            sphereSource.SetRadius(0.02)
            # 將圓形立體資料轉換成平面圖形資料
            sphereMapper = vtk.vtkPolyDataMapper()
            # SetInputConnection()動態傳遞點選的球體；GetOutputPort()取得球體
            sphereMapper.SetInputConnection(sphereSource.GetOutputPort())
            # 將球體資料轉換成視覺化物件
            self.sphereActor = vtk.vtkActor()
            # actor放入mapper，轉換成適合渲染的物件
            self.sphereActor.SetMapper(sphereMapper)
            # 設定球體顏色為紅色
            self.sphereActor.GetProperty().SetColor(1.0, 0.0, 0.0)
            # 將actor放入渲染器
            renderer.AddActor(self.sphereActor)
            # undo、消除的列表
            self.sphereActors.append(self.sphereActor)
            print(f"pathList: {self.pathList}")
            for i in range(len(self.pathList)):
                self.total_path_point.InsertNextPoint(self.poly_data.GetPoint(self.pathList[i]))
                self.clickPath.InsertNextPoint(self.poly_data.GetPoint(self.pathList[i]))
            # 求最小路徑，至少一個點以上才能求最短路徑
            
            for i in range(len(self.pathList)-1):
                
                # 投影每個取樣點
                self.project_line_to_surface(self.poly_data.GetPoint(self.pathList[i]),self.poly_data.GetPoint(self.pathList[i+1]))       

    def project_line_to_surface(self, pt1, pt2, num_samples=100):
        line_points = []
        for i in range(num_samples):
            t = i / (num_samples - 1)
            x = pt1[0] + t * (pt2[0] - pt1[0])
            y = pt1[1] + t * (pt2[1] - pt1[1])
            z = pt1[2] + t * (pt2[2] - pt1[2])
            line_points.append((x, y, z))

        locator = vtk.vtkCellLocator()
        locator.SetDataSet(self.poly_data)
        locator.BuildLocator()
        projected_points = []
        for point in line_points:
            closest_point = [0.0, 0.0, 0.0]
            cell_id = vtk.reference(0)
            sub_id = vtk.reference(0)
            dist2 = vtk.reference(0.0)
            locator.FindClosestPoint(point, closest_point, cell_id, sub_id, dist2)
            projected_points.append(closest_point)
            self.total_path_point.InsertNextPoint(closest_point)
                # 初始化Trim
        create_line = TrimVisualize(self.renderer)
        # 連接點與線段
        create_line.connect_point_to_line(projected_points)
        # 儲存視覺化線段
        self.lineActors.append(create_line.trim_actor)
        # 互動器更新
        self.interactor.GetRenderWindow().Render()

    def closeArea(self,interactor,renderer):
        # 最後一段：補 D → A
        pt1 = self.poly_data.GetPoint(self.pathList[-1])
        pt2 = self.poly_data.GetPoint(self.pathList[0])
        self.project_line_to_surface(pt1, pt2)
        # print(f"num of total points: {self.total_path_point.GetNumberOfPoints()}")
        self.loop.SetLoop(self.total_path_point)

        # 封閉選取範圍
        self.loop.SetLoop(self.total_path_point)
        clip = vtk.vtkClipPolyData()
        clip.SetInputData(self.poly_data)
        clip.SetClipFunction(self.loop)
        clip.InsideOutOn()
        clip.Update()

        clipMapper = vtk.vtkPolyDataMapper()
        clipMapper.SetInputConnection(clip.GetOutputPort())
        clipActor = vtk.vtkActor()
        clipActor.SetMapper(clipMapper)
        clipActor.GetProperty().SetColor(1.0, 0.0, 0.0)
        renderer.AddActor(clipActor)
        interactor.GetRenderWindow().Render()

    def unRenderAllSelectors(self, renderer, interactor):
        for actor in self.sphereActors:
            renderer.RemoveActor(actor)
        for actor in self.lineActors:
            renderer.RemoveActor(actor)
        self.sphereActors.clear()
        self.lineActors.clear()
        self.pathList.clear()
        self.meshNumList.clear()
        self.redoSphereActors.clear()
        self.redoLineActors.clear()
        self.redoPathList.clear()
        self.redoMeshNumList.clear()
        self.total_path_point.Reset()
        interactor.GetRenderWindow().Render()

     # 取消上一步選取；先回收視覺化點->最短路徑實際線段->最短路徑視覺化線段->再清除存放實際線段的列表
    def undo(self):
        # undo上一步點的視覺化
        last_sphere = self.sphereActors.pop()
        # 清除視覺化點
        self.renderer.RemoveActor(last_sphere)
        # 存放undo視覺化點
        self.redoSphereActors.append(last_sphere)
        # undo儲存實際點選列表
        last_path_point = self.pathList.pop()
        # 存放undo點選列表
        self.redoPathList.append(last_path_point)
        # 因為要更新點undo的畫面，這裡重新渲染畫面
        self.interactor.GetRenderWindow().Render()
        # undo儲存實際線段數量，沒有實際線段，不做事情
        if len(self.meshNumList) == 0:
            return
        # 一段段回收最短路徑的線段，避免有落單的沒有放到redo
        for i in range(self.meshNumList[-1]):
            # 避免實際線段超出範圍
            if i == self.meshNumList[-1] - 1:
                break
            # undo視覺化線段
            last_line = self.lineActors.pop()
            # 清除視覺化線段
            self.renderer.RemoveActor(last_line)
            # 把undo線段放回redo
            self.redoLineActors.append(last_line)
        # 抽出最短路徑實際線段儲存的資料
        last_mesh_num = self.meshNumList.pop()
        # 存放undo實際線段數量
        self.redoMeshNumList.append(last_mesh_num)
        # 更新畫面
        self.interactor.GetRenderWindow().Render()

    # 還原選取；先回收視覺化點->最短路徑實際線段->最短路徑視覺化線段->再清除存放實際線段的列表
    def redo(self):
        # redo視覺化點
        redo_sphere = self.redoSphereActors.pop()
        # 渲染器放入視覺化點
        self.renderer.AddActor(redo_sphere)
        # 把視覺化點放回原本的列表
        self.sphereActors.append(redo_sphere)
        # redo儲存實際點選列表
        redo_path_point = self.redoPathList.pop()
        # 把undo點選列表放回原本的列表
        self.pathList.append(redo_path_point)
        # 重新更新畫面，因為要還原視覺化點
        self.interactor.GetRenderWindow().Render()
        # redo儲存實際線段數量
        if len(self.redoMeshNumList) == 0:
            return
        # 迭代每一筆最短路徑的資料
        for i in range(self.redoMeshNumList[-1]):
            if i == self.redoMeshNumList[-1] - 1:
                break
            # redo視覺化線段
            redo_line = self.redoLineActors.pop()
            # 重新渲染視覺化線段資料
            self.renderer.AddActor(redo_line)
            # 添加回原本的列表
            self.lineActors.append(redo_line)
        # redo實際線段數量
        redo_mesh_num = self.redoMeshNumList.pop()
        # 添加回原本的列表
        self.meshNumList.append(redo_mesh_num)
        # 重新更新畫面
        self.interactor.GetRenderWindow().Render()
    # 穿透選取模式