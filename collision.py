import vtk
import os

# 載入網格模型，支援 .ply 與 .stl 格式
def load_mesh(file_path):
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.ply':
        reader = vtk.vtkPLYReader()
    elif ext == '.stl':
        reader = vtk.vtkSTLReader()
    else:
        raise ValueError(f"Unsupported file format: {ext}")
    
    reader.SetFileName(file_path)
    reader.Update()

    polydata = reader.GetOutput()
    if not polydata or polydata.GetNumberOfPoints() == 0:
        raise ValueError(f"Failed to load mesh from {file_path}")
    
    return polydata
# 降低網格面數（預設保留 50% 面數）
def simplify_mesh(polydata, reduction=0.5):
    decimate = vtk.vtkDecimatePro()
    decimate.SetInputData(polydata)
    decimate.SetTargetReduction(reduction)  # 例如 0.5 表示保留 50%
    decimate.PreserveTopologyOn()  # 保持拓撲（避免破洞）
    decimate.Update()
    return decimate.GetOutput()

# 使用 VTK 的碰撞偵測模組檢查兩個模型是否發生碰撞
def check_collision(mesh1, mesh2):
    try:
        clean1 = vtk.vtkCleanPolyData()
        clean1.SetInputData(mesh1)
        clean1.Update()

        clean2 = vtk.vtkCleanPolyData()
        clean2.SetInputData(mesh2)
        clean2.Update()

        collision_filter = vtk.vtkCollisionDetectionFilter()
        collision_filter.SetInputData(0, clean1.GetOutput())
        collision_filter.SetTransform(0, vtk.vtkTransform())
        collision_filter.SetInputData(1, clean2.GetOutput())
        collision_filter.SetMatrix(1, vtk.vtkMatrix4x4())
        collision_filter.SetCollisionModeToAllContacts()
        collision_filter.GenerateScalarsOn()
        collision_filter.SetBoxTolerance(0.0)
        collision_filter.SetCellTolerance(0.0)
        collision_filter.SetNumberOfCellsPerNode(2)
        collision_filter.Update()

        num_contacts = collision_filter.GetNumberOfContacts()
        print(f"Number of contacts: {num_contacts}")

        return num_contacts, collision_filter, clean1.GetOutput(), clean2.GetOutput()

    except Exception as e:
        print(f"[Error] Collision detection failed: {e}")
        return 0, None, None, None

# 計算 mesh2 每個點到 mesh1 表面的距離，僅保留內部點（負距離）
def compute_contact_distances(source_mesh, target_mesh):
    dist_calc = vtk.vtkImplicitPolyDataDistance()
    dist_calc.SetInput(target_mesh)

    distances = vtk.vtkFloatArray()
    distances.SetName("ContactDistance")

    for i in range(source_mesh.GetNumberOfPoints()):
        p = source_mesh.GetPoint(i)
        dist = dist_calc.EvaluateFunction(p)  # 帶正負號的距離
        if dist < 0:  # 內部點（負距離）
            distances.InsertNextValue(abs(dist))  # 存儲絕對值以便熱圖顯示
        else:  # 外部點設為 -1
            distances.InsertNextValue(-1.0)

    source_mesh.GetPointData().SetScalars(distances)
    return source_mesh

# 視覺化 mesh1、mesh2（含距離熱圖）
def visualize(mesh1, mesh2_with_distance):
    colors = vtk.vtkNamedColors()

    # Mesh1（作為基準模型）
    mapper1 = vtk.vtkPolyDataMapper()
    mapper1.SetInputData(mesh1)
    actor1 = vtk.vtkActor()
    actor1.SetMapper(mapper1)
    actor1.GetProperty().SetColor(colors.GetColor3d("LightGray"))
    actor1.GetProperty().SetOpacity(0)  # 保持透明

    # Mesh2，含距離資訊（熱圖）
    lut = vtk.vtkLookupTable()
    lut.SetTableRange(0.0, 0.05)  # 熱圖範圍（內部點的絕對值）
    lut.SetHueRange(0.33, 0.0)   # 綠到紅
    lut.SetBelowRangeColor(1.0, 1.0, 0.9, 1.0)  # 外部點（-1.0）設為牙齒顏色（象牙白）
    lut.SetUseBelowRangeColor(True)
    lut.Build()

    mapper2 = vtk.vtkPolyDataMapper()
    mapper2.SetInputData(mesh2_with_distance)
    mapper2.SetLookupTable(lut)
    mapper2.SetScalarRange(0.0, 0.05)  # 包含 -1.0 以映射牙齒顏色
    mapper2.ScalarVisibilityOn()

    actor2 = vtk.vtkActor()
    actor2.SetMapper(mapper2)
    actor2.GetProperty().SetOpacity(1.0)

    # 顯示距離色條
    scalar_bar = vtk.vtkScalarBarActor()
    scalar_bar.SetLookupTable(lut)
    scalar_bar.SetTitle("Internal Distance (mm)")
    scalar_bar.SetNumberOfLabels(6)

    # 建立渲染器
    renderer = vtk.vtkRenderer()
    render_window = vtk.vtkRenderWindow()
    render_window.AddRenderer(renderer)
    interactor = vtk.vtkRenderWindowInteractor()
    interactor.SetRenderWindow(render_window)

    renderer.AddActor(actor1)
    renderer.AddActor(actor2)
    renderer.AddActor2D(scalar_bar)
    renderer.SetBackground(colors.GetColor3d("SlateGray"))
    render_window.SetSize(800, 600)
    interactor.SetInteractorStyle(vtk.vtkInteractorStyleTrackballCamera())

    interactor.Initialize()
    render_window.Render()
    renderer.GetActiveCamera().Azimuth(0)
    renderer.GetActiveCamera().Elevation(0)
    interactor.Start()

# 主程式
if __name__ == "__main__":
    # mesh_path1 = "./Testdata/Up/data0402.ply"
    # mesh_path2 = "./paperdata/compareDAISresult/data0119.ply"
    # mesh_path2 = "./paperdata/compareDAISresult/goicp/ICP_data0402_BB_our_smoothedgo.stl"

    mesh_path1 = "./weipon/Template1-0_upper_Stage1_step0.stl"
    mesh_path2 = "./weipon/Template1-0_lower_Stage1_step0.stl"

    mesh1 = load_mesh(mesh_path1)
    mesh2 = load_mesh(mesh_path2)

    # 降低網格數（例如保留 30%）
    mesh1 = simplify_mesh(mesh1, reduction=0.5)
    mesh2 = simplify_mesh(mesh2, reduction=0.5)
    # #    # 對 mesh1 應用 Z 軸平移 (-1) onlay
    # transform = vtk.vtkTransform()
    # transform.Translate(0, -0.30, -0.3)  # 沿 Z 軸向下平移 1 單位
    # transform_filter = vtk.vtkTransformPolyDataFilter()
    # transform_filter.SetInputData(mesh1)
    # transform_filter.SetTransform(transform)
    # transform_filter.Update()
    # mesh1 = transform_filter.GetOutput()

    
    # # 對 mesh1 應用 Z 軸平移 (-1) crown
    # transform = vtk.vtkTransform()
    # transform.Translate(0, 0.0, -0.2)  
    # transform_filter = vtk.vtkTransformPolyDataFilter()
    # transform_filter.SetInputData(mesh1)
    # transform_filter.SetTransform(transform)
    # transform_filter.Update()
    # mesh1 = transform_filter.GetOutput()

    contacts, collision_filter, out1, out2 = check_collision(mesh1, mesh2)

    # 使用完整 mesh2 計算與 mesh1 的距離分布，顯示內部距離熱圖
    mesh2_with_distance = compute_contact_distances(out1, out2)
    visualize(out1, mesh2_with_distance)