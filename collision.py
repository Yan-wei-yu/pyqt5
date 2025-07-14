# 主要目的：此程式碼使用 VTK 庫載入並處理 3D 網格模型（支援 .ply 和 .stl 格式），執行網格簡化、碰撞檢測，並計算網格間的距離，生成包含距離熱圖的視覺化結果。

import vtk  # 導入 VTK 庫，用於 3D 圖形處理和視覺化。
import os  # 導入 os 模組，用於處理文件路徑和擴展名。

# 載入網格模型，支援 .ply 與 .stl 格式
def load_mesh(file_path):
    ext = os.path.splitext(file_path)[1].lower()  # 獲取文件擴展名並轉為小寫。
    if ext == '.ply':  # 如果文件是 .ply 格式。
        reader = vtk.vtkPLYReader()  # 創建 PLY 格式的讀取器。
    elif ext == '.stl':  # 如果文件是 .stl 格式。
        reader = vtk.vtkSTLReader()  # 創建 STL 格式的讀取器。
    else:  # 如果文件格式不受支援。
        raise ValueError(f"Unsupported file format: {ext}")  # 拋出錯誤，顯示不受支援的格式。
    
    reader.SetFileName(file_path)  # 設置讀取器的文件路徑。
    reader.Update()  # 更新讀取器以載入網格數據。

    polydata = reader.GetOutput()  # 獲取讀取器輸出的網格數據（PolyData）。
    if not polydata or polydata.GetNumberOfPoints() == 0:  # 檢查網格是否有效或包含點。
        raise ValueError(f"Failed to load mesh from {file_path}")  # 如果載入失敗，拋出錯誤。
    
    return polydata  # 返回載入的網格數據。

# 降低網格面數（預設保留 50% 面數）
def simplify_mesh(polydata, reduction=0.5):
    decimate = vtk.vtkDecimatePro()  # 創建網格簡化濾波器（DecimatePro）。
    decimate.SetInputData(polydata)  # 設置輸入網格數據。
    decimate.SetTargetReduction(reduction)  # 設置簡化目標（例如 0.5 表示保留 50% 面數）。
    decimate.PreserveTopologyOn()  # 啟用拓撲保持，防止簡化過程中出現破洞。
    decimate.Update()  # 更新濾波器以執行簡化。
    return decimate.GetOutput()  # 返回簡化後的網格數據。

# 使用 VTK 的碰撞偵測模組檢查兩個模型是否發生碰撞
def check_collision(mesh1, mesh2):
    try:
        clean1 = vtk.vtkCleanPolyData()  # 創建用於清理網格的濾波器（移除重複點等）。
        clean1.SetInputData(mesh1)  # 設置第一個網格作為輸入。
        clean1.Update()  # 更新濾波器以清理網格。

        clean2 = vtk.vtkCleanPolyData()  # 創建用於清理第二個網格的濾波器。
        clean2.SetInputData(mesh2)  # 設置第二個網格作為輸入。
        clean2.Update()  # 更新濾波器以清理網格。

        collision_filter = vtk.vtkCollisionDetectionFilter()  # 創建碰撞檢測濾波器。
        collision_filter.SetInputData(0, clean1.GetOutput())  # 設置第一個清理後的網格作為輸入 0。
        collision_filter.SetTransform(0, vtk.vtkTransform())  # 設置第一個網格的變換（無變換）。
        collision_filter.SetInputData(1, clean2.GetOutput())  # 設置第二個清理後的網格作為輸入 1。
        collision_filter.SetMatrix(1, vtk.vtkMatrix4x4())  # 設置第二個網格的變換矩陣（無變換）。
        collision_filter.SetCollisionModeToAllContacts()  # 設置碰撞模式為檢測所有接觸點。
        collision_filter.GenerateScalarsOn()  # 啟用標量生成（用於存儲碰撞資訊）。
        collision_filter.SetBoxTolerance(0.0)  # 設置邊界框容差為 0（高精度）。
        collision_filter.SetCellTolerance(0.0)  # 設置單元容差為 0（高精度）。
        collision_filter.SetNumberOfCellsPerNode(2)  # 設置每個節點的單元數量為 2。
        collision_filter.Update()  # 更新濾波器以執行碰撞檢測。

        num_contacts = collision_filter.GetNumberOfContacts()  # 獲取碰撞接觸點的數量。
        print(f"Number of contacts: {num_contacts}")  # 打印接觸點數量。

        return num_contacts, collision_filter, clean1.GetOutput(), clean2.GetOutput()  # 返回接觸點數量、碰撞濾波器及清理後的網格。

    except Exception as e:  # 捕獲可能發生的錯誤。
        print(f"[Error] Collision detection failed: {e}")  # 打印錯誤訊息。
        return 0, None, None, None  # 返回空值表示碰撞檢測失敗。

# 計算 mesh2 每個點到 mesh1 表面的距離，僅保留內部點（負距離）
def compute_contact_distances(source_mesh, target_mesh):
    dist_calc = vtk.vtkImplicitPolyDataDistance()  # 創建距離計算濾波器。
    dist_calc.SetInput(target_mesh)  # 設置目標網格（mesh1）作為距離計算的參考。

    distances = vtk.vtkFloatArray()  # 創建浮點數陣列用於存儲距離值。
    distances.SetName("ContactDistance")  # 設置陣列名稱為 "ContactDistance"。

    for i in range(source_mesh.GetNumberOfPoints()):  # 遍歷 source_mesh（mesh2）的每個點。
        p = source_mesh.GetPoint(i)  # 獲取當前點的座標。
        dist = dist_calc.EvaluateFunction(p)  # 計算該點到 target_mesh 的簽署距離（正負號表示內外）。
        if dist < 0:  # 如果是內部點（負距離）。
            distances.InsertNextValue(abs(dist))  # 存儲距離的絕對值（用於熱圖顯示）。
        else:  # 如果是外部點。
            distances.InsertNextValue(-1.0)  # 設置為 -1.0，表示外部點。

    source_mesh.GetPointData().SetScalars(distances)  # 將距離陣列附加到 source_mesh 的點數據。
    return source_mesh  # 返回包含距離資訊的網格。

# 視覺化 mesh1、mesh2（含距離熱圖）
def visualize(mesh1, mesh2_with_distance):
    colors = vtk.vtkNamedColors()  # 創建 VTK 命名顏色對象，用於設置顏色。

    # Mesh1（作為基準模型）
    mapper1 = vtk.vtkPolyDataMapper()  # 創建用於 mesh1 的映射器，將網格數據轉換為可視化形式。
    mapper1.SetInputData(mesh1)  # 設置 mesh1 作為輸入數據。
    actor1 = vtk.vtkActor()  # 創建用於 mesh1 的演員（可視化對象）。
    actor1.SetMapper(mapper1)  # 將映射器關聯到演員。
    actor1.GetProperty().SetColor(colors.GetColor3d("LightGray"))  # 設置 mesh1 的顏色為淺灰色。
    actor1.GetProperty().SetOpacity(0)  # 設置 mesh1 的透明度為 0（完全透明）。

    # Mesh2，含距離資訊（熱圖）
    lut = vtk.vtkLookupTable()  # 創建顏色查找表，用於熱圖顯示。
    lut.SetTableRange(0.0, 0.05)  # 設置熱圖的距離範圍（0 到 0.05 毫米）。
    lut.SetHueRange(0.33, 0.0)  # 設置色調範圍（綠色到紅色）。
    lut.SetBelowRangeColor(1.0, 1.0, 0.9, 1.0)  # 外部點（-1.0）設置為牙齒顏色（象牙白）。
    lut.SetUseBelowRangeColor(True)  # 啟用低於範圍的顏色設置。
    lut.Build()  # 構建顏色查找表。

    mapper2 = vtk.vtkPolyDataMapper()  # 創建用於 mesh2 的映射器。
    mapper2.SetInputData(mesh2_with_distance)  # 設置帶距離資訊的 mesh2 作為輸入。
    mapper2.SetLookupTable(lut)  # 設置顏色查找表。
    mapper2.SetScalarRange(0.0, 0.05)  # 設置標量範圍（包含 -1.0 以映射牙齒顏色）。
    mapper2.ScalarVisibilityOn()  # 啟用標量可視化（顯示熱圖）。

    actor2 = vtk.vtkActor()  # 創建用於 mesh2 的演員。
    actor2.SetMapper(mapper2)  # 將映射器關聯到演員。
    actor2.GetProperty().SetOpacity(1.0)  # 設置 mesh2 的透明度為 1（不透明）。

    # 顯示距離色條
    scalar_bar = vtk.vtkScalarBarActor()  # 創建色條演員，用於顯示距離熱圖的圖例。
    scalar_bar.SetLookupTable(lut)  # 設置色條的顏色查找表。
    scalar_bar.SetTitle("Internal Distance (mm)")  # 設置色條標題為 "內部距離（毫米）"。
    scalar_bar.SetNumberOfLabels(6)  # 設置色條上的標籤數量為 6。

    # 建立渲染器
    renderer = vtk.vtkRenderer()  # 創建渲染器，用於管理場景中的可視化對象。
    render_window = vtk.vtkRenderWindow()  # 創建渲染窗口，用於顯示渲染結果。
    render_window.AddRenderer(renderer)  # 將渲染器添加到渲染窗口。
    interactor = vtk.vtkRenderWindowInteractor()  # 創建交互器，用於處理用戶交互。
    interactor.SetRenderWindow(render_window)  # 將渲染窗口關聯到交互器。

    renderer.AddActor(actor1)  # 將 mesh1 的演員添加到渲染器。
    renderer.AddActor(actor2)  # 將 mesh2 的演員添加到渲染器。
    renderer.AddActor2D(scalar_bar)  # 將色條添加到渲染器（2D 對象）。
    renderer.SetBackground(colors.GetColor3d("SlateGray"))  # 設置渲染器背景顏色為石板灰。
    render_window.SetSize(800, 600)  # 設置渲染窗口大小為 800x600 像素。
    interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())  # 設置交互樣式為軌跡球相機模式。

    interactor.Initialize()  # 初始化交互器。
    render_window.Render()  # 執行渲染以顯示場景。
    renderer.GetActiveCamera().Azimuth(0)  # 設置攝影機的方位角為 0。
    renderer.GetActiveCamera().Elevation(0)  # 設置攝影機的仰角為 0。
    interactor.Start()  # 啟動交互器，進入交互模式。

# 主程式
if __name__ == "__main__":  # 檢查腳本是否直接運行（而非作為模組導入）。
    # mesh_path1 = "./Testdata/Up/data0402.ply"  # 註解掉的測試網格文件路徑 1。
    # mesh_path2 = "./paperdata/compareDAISresult/data0119.ply"  # 註解掉的測試網格文件路徑 2。
    # mesh_path2 = "./paperdata/compareDAISresult/goicp/ICP_data0402_BB_our_smoothedgo.stl"  # 註解掉的另一測試網格文件路徑。

    mesh_path1 = "./weipon/Template1-0_upper_Stage1_step0.stl"  # 第一個網格文件的路徑（上顎模型）。
    mesh_path2 = "./weipon/Template1-0_lower_Stage1_step0.stl"  # 第二個網格文件的路徑（下顎模型）。

    mesh1 = load_mesh(mesh_path1)  # 載入第一個網格模型。
    mesh2 = load_mesh(mesh_path2)  # 載入第二個網格模型。

    # 降低網格數（例如保留 30%）
    mesh1 = simplify_mesh(mesh1, reduction=0.5)  # 簡化第一個網格，保留 50% 面數。
    mesh2 = simplify_mesh(mesh2, reduction=0.5)  # 簡化第二個網格，保留 50% 面數。

    # 以下為註解掉的代碼，用於對 mesh1 應用 Z 軸平移（僅適用於特定場景）
    # transform = vtk.vtkTransform()  # 創建變換對象。
    # transform.Translate(0, -0.30, -0.3)  # 沿 Z 軸向下平移 0.3 單位。
    # transform_filter = vtk.vtkTransformPolyDataFilter()  # 創建變換濾波器。
    # transform_filter.SetInputData(mesh1)  # 設置輸入網格。
    # transform_filter.SetTransform(transform)  # 設置變換。
    # transform_filter.Update()  # 更新濾波器。
    # mesh1 = transform_filter.GetOutput()  # 更新 mesh1 為變換後的網格。

    contacts, collision_filter, out1, out2 = check_collision(mesh1, mesh2)  # 執行碰撞檢測，返回接觸點數量及清理後的網格。

    # 使用完整 mesh2 計算與 mesh1 的距離分布，顯示內部距離熱圖
    mesh2_with_distance = compute_contact_distances(out1, out2)  # 計算 mesh2 每個點到 mesh1 的距離。
    visualize(out1, mesh2_with_distance)  # 視覺化 mesh1 和帶距離熱圖的 mesh2。