# 主要目的：此程式碼定義了兩個基於 VTK 的類：`TrimVisualize` 和 `PointInteractor`，用於牙科 3D 模型處理場景中的交互式點選和線段可視化。`TrimVisualize` 負責將點連接到線段並以綠色線條顯示；`PointInteractor` 繼承自 `vtk.vtkInteractorStyleTrackballCamera`，允許用戶通過左鍵點選 3D 模型表面上的點，計算最短路徑並投影到表面，支援封閉區域選擇、撤銷（undo）和重做（redo）功能，適用於 `HighlightInteractorStyle` 和 `AimodelView` 的交互式模型編輯。

import vtk  # 導入 VTK 庫，用於 3D 模型處理和視覺化。

class TrimVisualize:
    def __init__(self, renderer):  # 初始化方法，接收 VTK 渲染器。
        self.renderer = renderer  # 儲存傳入的渲染器。
        self.projected_points = vtk.vtkPoints()  # 初始化 VTK 點集，用於儲存投影點。
        self.poly_data_trim = vtk.vtkPolyData()  # 初始化 VTK PolyData，用於儲存線段數據。
        self.trim_mapper = vtk.vtkPolyDataMapper()  # 初始化 VTK 映射器，用於渲染線段。
        self.trim_actor = vtk.vtkActor()  # 初始化 VTK 演員，用於顯示線段。

    def connect_point_to_line(self, point_list):  # 將點連接到線段並可視化。
        for point in point_list:  # 迭代輸入的點列表。
            self.projected_points.InsertNextPoint(point)  # 將每個點添加到 VTK 點集。
        lines = vtk.vtkCellArray()  # 創建 VTK 單元陣列，用於儲存線段。
        for i in range(len(point_list) - 1):  # 迭代點列表，創建連續線段。
            line = vtk.vtkLine()  # 創建 VTK 線段對象。
            line.GetPointIds().SetId(0, i)  # 設置線段的第一個點 ID。
            line.GetPointIds().SetId(1, i + 1)  # 設置線段的第二個點 ID。
            lines.InsertNextCell(line)  # 將線段添加到單元陣列。
        self.poly_data_trim.SetPoints(self.projected_points)  # 設置 PolyData 的點集。
        self.poly_data_trim.SetLines(lines)  # 設置 PolyData 的線段。
        self.trim_mapper.SetInputData(self.poly_data_trim)  # 設置映射器的輸入為 PolyData。
        self.trim_actor.SetMapper(self.trim_mapper)  # 設置演員的映射器。
        self.trim_actor.GetProperty().SetLineWidth(3)  # 設置線段寬度為 3 像素。
        self.trim_actor.GetProperty().SetColor(0.0, 1.0, 0.0)  # 設置線段顏色為綠色（RGB: 0, 1, 0）。
        self.renderer.AddActor(self.trim_actor)  # 將演員添加到渲染器。

    def removeLine(self):  # 移除線段可視化。
        self.renderer.RemoveActor(self.trim_actor)  # 從渲染器中移除線段演員。
        self.projected_points.Initialize()  # 重置點集。
        self.poly_data_trim.Initialize()  # 重置 PolyData。
        self.trim_mapper = vtk.vtkPolyDataMapper()  # 重置映射器。
        self.trim_actor = vtk.vtkActor()  # 重置演員。

class PointInteractor(vtk.vtkInteractorStyleTrackballCamera):  # 定義 PointInteractor 類，繼承 VTK 軌跡球攝影機交互樣式。
    def __init__(self, poly_data):  # 初始化方法，接收 PolyData（3D 模型數據）。
        super().__init__()  # 調用父類的初始化方法。
        self.poly_data = poly_data  # 儲存傳入的 PolyData（例如上顎或下顎模型）。
        self.dijkstra = vtk.vtkDijkstraGraphGeodesicPath()  # 初始化 Dijkstra 測地路徑計算器。
        self.selectionPoints = vtk.vtkPoints()  # 初始化 VTK 點集，用於儲存選取點。
        self.dijkstra.SetInputData(self.poly_data)  # 設置 Dijkstra 計算器的輸入 PolyData。
        self.sphereActors = []  # 初始化球體演員列表，用於顯示選取點。
        self.lineActors = []  # 初始化線段演員列表，用於顯示最短路徑。
        self.pathList = []  # 初始化選取點 ID 列表。
        self.meshNumList = []  # 初始化網格數量列表（用於記錄線段數）。
        self.pick3DCoord = vtk.vtkCellPicker()  # 初始化 VTK 單元拾取器，用於 3D 點選。
        self.loop = vtk.vtkImplicitSelectionLoop()  # 初始化 VTK 隱式選擇迴圈，用於封閉區域。
        self.total_length = 0  # 初始化總路徑長度（未使用，可能是遺留代碼）。
        # 新增功能：支援 undo 和 redo
        self.redoSphereActors = []  # 初始化 redo 球體演員列表。
        self.redoLineActors = []  # 初始化 redo 線段演員列表。
        self.redoPathList = []  # 初始化 redo 選取點 ID 列表。
        self.redoMeshNumList = []  # 初始化 redo 網格數量列表。
        self.total_path_point = vtk.vtkPoints()  # 初始化 VTK 點集，用於儲存所有投影點。
        self.AddObserver("LeftButtonPressEvent", self.onLeftButtonDown)  # 綁定左鍵按下事件。

    def onLeftButtonDown(self, obj, event, interactor, renderer):  # 處理左鍵按下事件。
        self.renderer = renderer  # 儲存傳入的渲染器。
        self.interactor = interactor  # 儲存傳入的交互器。
        clickPos = interactor.GetEventPosition()  # 獲取滑鼠點擊位置（螢幕坐標）。
        picker = vtk.vtkCellPicker()  # 創建 VTK 單元拾取器。
        picker.Pick(clickPos[0], clickPos[1], 0, renderer)  # 在點擊位置進行 3D 拾取。
        self.pick3DCoord.Pick(clickPos[0], clickPos[1], 0, renderer)  # 更新 3D 拾取器。
        self.clickPath = vtk.vtkPoints()  # 初始化點選路徑點集。
        print(f"point coord: {self.poly_data.GetPoint(picker.GetPointId())}")  # 打印拾取點的 3D 座標。
        if picker.GetCellId() != -1:  # 如果拾取到有效單元。
            self.pathList.append(picker.GetPointId())  # 將拾取點 ID 添加到路徑列表。
            point_position = self.poly_data.GetPoint(picker.GetPointId())  # 獲取拾取點的 3D 座標。
            sphereSource = vtk.vtkSphereSource()  # 創建 VTK 球體源。
            sphereSource.SetCenter(point_position)  # 設置球體中心為拾取點座標。
            sphereSource.SetRadius(0.02)  # 設置球體半徑為 0.02。
            sphereMapper = vtk.vtkPolyDataMapper()  # 創建 VTK 映射器。
            sphereMapper.SetInputConnection(sphereSource.GetOutputPort())  # 設置球體源的輸出。
            self.sphereActor = vtk.vtkActor()  # 創建球體演員。
            self.sphereActor.SetMapper(sphereMapper)  # 設置演員的映射器。
            self.sphereActor.GetProperty().SetColor(1.0, 0.0, 0.0)  # 設置球體顏色為紅色（RGB: 1, 0, 0）。
            renderer.AddActor(self.sphereActor)  # 將球體演員添加到渲染器。
            self.sphereActors.append(self.sphereActor)  # 將球體演員添加到列表。
            print(f"pathList: {self.pathList}")  # 打印當前路徑點 ID 列表。
            for i in range(len(self.pathList)):  # 迭代路徑點，更新點選路徑。
                self.total_path_point.InsertNextPoint(self.poly_data.GetPoint(self.pathList[i]))  # 將點添加到總路徑點集。
                self.clickPath.InsertNextPoint(self.poly_data.GetPoint(self.pathList[i]))  # 將點添加到當前點選路徑。
            for i in range(len(self.pathList) - 1):  # 迭代路徑點，計算相鄰點間的最短路徑。
                self.project_line_to_surface(self.poly_data.GetPoint(self.pathList[i]), 
                                             self.poly_data.GetPoint(self.pathList[i + 1]))  # 投影線段到表面。

    def project_line_to_surface(self, pt1, pt2, num_samples=100):  # 將兩點間的線段投影到模型表面。
        line_points = []  # 初始化線段點列表。
        for i in range(num_samples):  # 生成 100 個均勻分佈的線段點。
            t = i / (num_samples - 1)  # 計算插值參數 t。
            x = pt1[0] + t * (pt2[0] - pt1[0])  # 插值計算 x 座標。
            y = pt1[1] + t * (pt2[1] - pt1[1])  # 插值計算 y 座標。
            z = pt1[2] + t * (pt2[2] - pt1[2])  # 插值計算 z 座標。
            line_points.append((x, y, z))  # 添加插值點到列表。
        locator = vtk.vtkCellLocator()  # 創建 VTK 單元定位器。
        locator.SetDataSet(self.poly_data)  # 設置定位器的輸入 PolyData。
        locator.BuildLocator()  # 構建定位器以加速查找。
        projected_points = []  # 初始化投影點列表。
        for point in line_points:  # 迭代線段點。
            closest_point = [0.0, 0.0, 0.0]  # 初始化最近點座標。
            cell_id = vtk.reference(0)  # 初始化單元 ID。
            sub_id = vtk.reference(0)  # 初始化子單元 ID。
            dist2 = vtk.reference(0.0)  # 初始化距離平方。
            locator.FindClosestPoint(point, closest_point, cell_id, sub_id, dist2)  # 查找最近的表面點。
            projected_points.append(closest_point)  # 添加投影點到列表。
            self.total_path_point.InsertNextPoint(closest_point)  # 將投影點添加到總路徑點集。
        create_line = TrimVisualize(self.renderer)  # 創建 TrimVisualize 實例。
        create_line.connect_point_to_line(projected_points)  # 將投影點連接到線段並可視化。
        self.lineActors.append(create_line.trim_actor)  # 將線段演員添加到列表。
        self.interactor.GetRenderWindow().Render()  # 重新渲染窗口。

    def closeArea(self, interactor, renderer):  # 封閉選取區域並可視化。
        pt1 = self.poly_data.GetPoint(self.pathList[-1])  # 獲取最後一個點的座標。
        pt2 = self.poly_data.GetPoint(self.pathList[0])  # 獲取第一個點的座標。
        self.project_line_to_surface(pt1, pt2)  # 將最後一點與第一點連接到表面。
        self.loop.SetLoop(self.total_path_point)  # 設置隱式選擇迴圈的點集。
        clip = vtk.vtkClipPolyData()  # 創建 VTK 裁切器。
        clip.SetInputData(self.poly_data)  # 設置輸入 PolyData。
        clip.SetClipFunction(self.loop)  # 設置裁切函數為隱式選擇迴圈。
        clip.InsideOutOn()  # 保留迴圈內的區域。
        clip.Update()  # 更新裁切器。
        clipMapper = vtk.vtkPolyDataMapper()  # 創建 VTK 映射器。
        clipMapper.SetInputConnection(clip.GetOutputPort())  # 設置輸入為裁切器的輸出。
        clipActor = vtk.vtkActor()  # 創建 VTK 演員。
        clipActor.SetMapper(clipMapper)  # 設置演員的映射器。
        clipActor.GetProperty().SetColor(1.0, 0.0, 0.0)  # 設置封閉區域顏色為紅色（RGB: 1, 0, 0）。
        renderer.AddActor(clipActor)  # 將演員添加到渲染器。
        interactor.GetRenderWindow().Render()  # 重新渲染窗口。

    def unRenderAllSelectors(self, renderer, interactor):  # 移除所有選取點和線段的可視化。
        for actor in self.sphereActors:  # 迭代球體演員列表。
            renderer.RemoveActor(actor)  # 移除每個球體演員。
        for actor in self.lineActors:  # 迭代線段演員列表。
            renderer.RemoveActor(actor)  # 移除每個線段演員。
        self.sphereActors.clear()  # 清空球體演員列表。
        self.lineActors.clear()  # 清空線段演員列表。
        self.pathList.clear()  # 清空選取點 ID 列表。
        self.meshNumList.clear()  # 清空網格數量列表。
        self.redoSphereActors.clear()  # 清空 redo 球體演員列表。
        self.redoLineActors.clear()  # 清空 redo 線段演員列表。
        self.redoPathList.clear()  # 清空 redo 選取點 ID 列表。
        self.redoMeshNumList.clear()  # 清空 redo 網格數量列表。
        self.total_path_point.Reset()  # 重置總路徑點集。
        interactor.GetRenderWindow().Render()  # 重新渲染窗口。

    def undo(self):  # 撤銷上一步選取操作。
        last_sphere = self.sphereActors.pop()  # 移除最後一個球體演員。
        self.renderer.RemoveActor(last_sphere)  # 從渲染器中移除球體演員。
        self.redoSphereActors.append(last_sphere)  # 將球體演員添加到 redo 列表。
        last_path_point = self.pathList.pop()  # 移除最後一個選取點 ID。
        self.redoPathList.append(last_path_point)  # 將選取點 ID 添加到 redo 列表。
        self.interactor.GetRenderWindow().Render()  # 重新渲染窗口以更新畫面。
        if len(self.meshNumList) == 0:  # 如果網格數量列表為空。
            return  # 直接返回。
        for i in range(self.meshNumList[-1]):  # 迭代最後一組線段數量。
            if i == self.meshNumList[-1] - 1:  # 避免超出範圍。
                break
            last_line = self.lineActors.pop()  # 移除最後一個線段演員。
            self.renderer.RemoveActor(last_line)  # 從渲染器中移除線段演員。
            self.redoLineActors.append(last_line)  # 將線段演員添加到 redo 列表。
        last_mesh_num = self.meshNumList.pop()  # 移除最後一個網格數量。
        self.redoMeshNumList.append(last_mesh_num)  # 將網格數量添加到 redo 列表。
        self.interactor.GetRenderWindow().Render()  # 重新渲染窗口。

    def redo(self):  # 重做上一步撤銷的操作。
        redo_sphere = self.redoSphereActors.pop()  # 移除 redo 列表中的球體演員。
        self.renderer.AddActor(redo_sphere)  # 將球體演員添加到渲染器。
        self.sphereActors.append(redo_sphere)  # 將球體演員添加到球體演員列表。
        redo_path_point = self.redoPathList.pop()  # 移除 redo 列表中的選取點 ID。
        self.pathList.append(redo_path_point)  # 將選取點 ID 添加到路徑列表。
        self.interactor.GetRenderWindow().Render()  # 重新渲染窗口以更新畫面。
        if len(self.redoMeshNumList) == 0:  # 如果 redo 網格數量列表為空。
            return  # 直接返回。
        for i in range(self.redoMeshNumList[-1]):  # 迭代 redo 網格數量。
            if i == self.redoMeshNumList[-1] - 1:  # 避免超出範圍。
                break
            redo_line = self.redoLineActors.pop()  # 移除 redo 列表中的線段演員。
            self.renderer.AddActor(redo_line)  # 將線段演員添加到渲染器。
            self.lineActors.append(redo_line)  # 將線段演員添加到線段演員列表。
        redo_mesh_num = self.redoMeshNumList.pop()  # 移除 redo 列表中的網格數量。
        self.meshNumList.append(redo_mesh_num)  # 將網格數量添加到網格數量列表。
        self.interactor.GetRenderWindow().Render()  # 重新渲染窗口。