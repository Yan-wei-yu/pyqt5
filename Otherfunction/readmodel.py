# 主要目的：此程式碼提供了一組工具函數，用於載入和渲染 3D 模型（支援 PLY、STL、OBJ 格式）以及生成深度圖像，適用於牙科 3D 模型的可視化和處理。它使用 VTK 進行模型載入、相機設置和深度圖像生成，支援單模型和上下模型的邊界計算，並提供 OBB（定向邊界框）對齊的相機設置功能。此外，還包含一個函數用於在第二個渲染窗口中顯示 STL 模型或 PNG 圖像，支援交互式視圖更新。此程式碼與 `DentalModelReconstructor` 和 `LassoInteractor` 等模組結合，適用於牙科模型的 AI 修復和交互式編輯流程。

import vtk  # 導入 VTK 庫，用於 3D 模型處理和可視化。
import os  # 導入 os 模組，用於檔案路徑操作。
import math  # 導入 math 模組，用於數學計算（如距離計算）。
from . import trianglegoodobbox  # 導入自定義模組，包含 `DentalModelReconstructor` 類，用於 OBB 計算。

# 載入 3D 模型並根據檔案格式選擇對應的讀取器
def load_3d_model(filename):  # 定義載入 3D 模型的函數。
    _, extension = os.path.splitext(filename)  # 獲取檔案副檔名（例如 .ply、.stl）。
    extension = extension.lower()  # 將副檔名轉為小寫。

    # 根據檔案副檔名選擇對應的 VTK 讀取器
    if extension == '.ply':  # 如果是 PLY 格式。
        reader = vtk.vtkPLYReader()
    elif extension == '.stl':  # 如果是 STL 格式。
        reader = vtk.vtkSTLReader()
    elif extension == '.obj':  # 如果是 OBJ 格式。
        reader = vtk.vtkOBJReader()
    else:
        raise ValueError(f"Unsupported file format: {extension}")  # 不支援的格式，拋出錯誤。

    reader.SetFileName(filename)  # 設置檔案路徑。
    reader.Update()  # 更新讀取器以載入檔案。
    return reader.GetOutput()  # 返回讀取的 PolyData 物件。

# 根據 polydata 生成 actor 並設定顏色
def create_actor(polydata, color):  # 定義創建 VTK Actor 的函數。
    mapper = vtk.vtkPolyDataMapper()  # 創建 PolyData 映射器，用於將幾何數據映射到渲染。
    mapper.SetInputData(polydata)  # 設置輸入 PolyData。

    actor = vtk.vtkActor()  # 創建 Actor，用於管理可視化屬性。
    actor.SetMapper(mapper)  # 將映射器綁定到 Actor。
    prop = actor.GetProperty()  # 獲取 Actor 的屬性物件。
    prop.SetColor(color)  # 設置 Actor 的顏色（傳入 RGB 元組，如 (0.8, 0.8, 0.8) 表示淺灰）。

    # ✨ 加入 shading 設定（類似 GeoMagic）
    prop.ShadingOn()  # 啟用 Phong 光照模型，增強模型的視覺效果。
    return actor  # 返回配置好的 Actor。

# 計算 actor 的幾何中心
def calculate_center(actor):  # 定義計算 Actor 幾何中心的函數。
    bounds = actor.GetBounds()  # 獲取 Actor 的邊界框 (xmin, xmax, ymin, ymax, zmin, zmax)。
    center = [
        (bounds[1] + bounds[0]) * 0.5,  # 計算 X 軸中心。
        (bounds[3] + bounds[2]) * 0.5,  # 計算 Y 軸中心。
        (bounds[5] + bounds[4]) * 0.5   # 計算 Z 軸中心。
    ]
    return center  # 返回中心點坐標 (x, y, z)。

# 合併上下模型的邊界
def twomodel_bound(upper_bounds, lower_bounds):  # 定義合併上下模型邊界框的函數。
    combined_bounds = [
        min(upper_bounds[0], lower_bounds[0]),  # 合併 X 軸最小值。
        max(upper_bounds[1], lower_bounds[1]),  # 合併 X 軸最大值。
        min(upper_bounds[2], lower_bounds[2]),  # 合併 Y 軸最小值。
        max(upper_bounds[3], lower_bounds[3]),  # 合併 Y 軸最大值。
        min(upper_bounds[4], lower_bounds[4]),  # 合併 Z 軸最小值。
        max(upper_bounds[5], lower_bounds[5])   # 合併 Z 軸最大值。
    ]
    return combined_bounds  # 返回合併後的邊界框。

# 旋轉 actor 至指定角度
def rotate_actor(actor, center, angle):  # 定義旋轉 Actor 的函數。
    transform = vtk.vtkTransform()  # 創建 VTK 變換物件。
    transform.Translate(-center[0], -center[1], -center[2])  # 平移到原點（以中心為基準）。
    transform.RotateY(angle)  # 沿 Y 軸旋轉指定角度（單位：度）。
    transform.Translate(center[0], center[1], center[2])  # 平移回原始位置。
    actor.SetUserTransform(transform)  # 應用變換到 Actor。

def setup_camera_with_obb(renderer, render_window, upper_actor, center2=None, lower_actor=None, upper_opacity=None, angle=0):
    """
    使用 OBB 邊界設置相機進行深度圖像渲染。

    參數:
        renderer: vtkRenderer 對象，用於渲染場景。
        render_window: vtkRenderWindow 對象，用於顯示渲染結果。
        upper_actor: 上層模型的 Actor（必須提供）。
        center2: 可選，第二個焦點（用於上下模型場景）。
        lower_actor: 可選，下層模型的 Actor。
        upper_opacity: 可選，上層模型的透明度。
        angle: 可選，相機額外調整角度（單位：度）。

    返回:
        vtkImageShiftScale: 調整過的深度圖像過濾器。
    """
    cam1 = renderer.GetActiveCamera()  # 獲取渲染器的當前相機。

    # 設置相機的初始位置與剪裁範圍
    cam_position = [0.0, 0.0, 0.0]  # 初始化相機位置（將由 VTK 自動設置）。
    polydata = lower_actor.GetMapper().GetInput() if lower_actor else upper_actor.GetMapper().GetInput()  # 獲取模型的 PolyData。
    if upper_actor is not None:  # 如果提供了上層 Actor。
        up_polydata = upper_actor.GetMapper().GetInput()  # 獲取上層模型的 PolyData。
        obb_bounds = trianglegoodobbox.DentalModelReconstructor.compute_obb_aligned_bounds(polydata, up_polydata)  # 計算 OBB 邊界（考慮上下模型）。
    else:
        obb_bounds = trianglegoodobbox.DentalModelReconstructor.compute_obb_aligned_bounds(polydata, None, angle)  # 僅計算單模型的 OBB 邊界。

    center1 = (
        (obb_bounds[0] + obb_bounds[1]) / 2.0,  # 計算 OBB 邊界框的 X 中心。
        (obb_bounds[2] + obb_bounds[3]) / 2.0,  # 計算 OBB 邊界框的 Y 中心。
        (obb_bounds[4] + obb_bounds[5]) / 2.0,  # 計算 OBB 邊界框的 Z 中心。
    )

    cam1.SetFocalPoint(center1)  # 設置相機焦點為 OBB 中心。
    cam1.SetParallelProjection(True)  # 啟用平行投影（適合深度圖生成）。
    cam_position = cam1.GetPosition()  # 獲取相機當前位置。

    # 計算相機與模型中心的距離
    distance_cam_to_bb = math.sqrt(
        (cam_position[0] - center1[0])**2 +
        (cam_position[1] - center1[1])**2 +
        (cam_position[2] - center1[2])**2
    )

    # 計算近平面與遠平面的範圍
    near = distance_cam_to_bb - ((obb_bounds[5] - obb_bounds[4]) * 0.5)  # 近平面距離（Z 軸範圍的一半）。
    far = distance_cam_to_bb + ((obb_bounds[5] - obb_bounds[4]) * 0.5)  # 遠平面距離。

    # 設置相機的平行投影比例
    cam1.SetParallelScale((obb_bounds[3] - obb_bounds[2]) * 0.5)  # 根據 Y 軸範圍設置縮放比例。

    # 根據角度或其他條件設置剪裁範圍
    if angle != 0:  # 如果指定了非零角度（例如舌側或頰側視角）。
        cam1.SetClippingRange(near, far - ((far - near) * 0.5))  # 壓縮遠平面範圍（聚焦上半部分）。
    elif upper_opacity is not None and center2 is not None:  # 如果有上層透明度和第二焦點。
        distance_cam_to_bb_up = math.sqrt(
            (cam_position[0] - center2[0])**2 +
            (cam_position[1] - center2[1])**2 +
            (cam_position[2] - center2[2])**2
        )  # 計算相機到第二焦點的距離。
        gap_and_down = distance_cam_to_bb - distance_cam_to_bb_up  # 計算上下模型的距離差。
        cam1.SetClippingRange(near - gap_and_down, far)  # 調整剪裁範圍以包含上下模型。
    else:
        cam1.SetClippingRange(near - 2, far)  # 默認剪裁範圍，略微擴展近平面。

    renderer.SetActiveCamera(cam1)  # 將配置好的相機設置為渲染器的活動相機。

    # 創建深度圖像過濾器
    depth_image_filter = vtk.vtkWindowToImageFilter()  # 創建窗口到圖像的過濾器。
    depth_image_filter.SetInput(render_window)  # 設置輸入為渲染窗口。
    depth_image_filter.SetInputBufferTypeToZBuffer()  # 使用 Z 緩衝區生成深度圖。

    # 創建縮放過濾器將深度值映射到 0-255
    scale_filter = vtk.vtkImageShiftScale()  # 創建縮放過濾器。
    scale_filter.SetInputConnection(depth_image_filter.GetOutputPort())  # 連接深度圖過濾器。
    scale_filter.SetOutputScalarTypeToUnsignedChar()  # 設置輸出為 8 位無符號整數（0-255）。
    scale_filter.SetShift(-1)  # 將深度值平移（Z 緩衝區範圍 [-1, 1]）。
    scale_filter.SetScale(-255)  # 縮放深度值到 0-255（反轉以匹配灰階圖）。

    return scale_filter  # 返回深度圖像的縮放過濾器。

# 設定普通相機進行深度圖像渲染
def setup_camera(renderer, render_window, center2=None, lower_actor=None, upper_opacity=None, angle=0):  # 定義普通相機設置函數。
    cam1 = renderer.GetActiveCamera()  # 獲取渲染器的當前相機。

    # 計算並設置相機焦點與其他參數
    cam_position = [0.0, 0.0, 0.0]  # 初始化相機位置（將由 VTK 自動設置）。
    center1 = calculate_center(lower_actor)  # 計算下層 Actor 的幾何中心。
    lower_bound = lower_actor.GetBounds()  # 獲取下層 Actor 的邊界框。
    cam1.SetFocalPoint(center1)  # 設置相機焦點為模型中心。
    cam1.SetParallelProjection(True)  # 啟用平行投影。
    cam_position = cam1.GetPosition()  # 獲取相機當前位置。

    # 計算相機與模型中心的距離
    distance_cam_to_bb = math.sqrt(
        (cam_position[0] - center1[0])**2 +
        (cam_position[1] - center1[1])**2 +
        (cam_position[2] - center1[2])**2
    )

    # 計算近平面與遠平面的範圍
    near = distance_cam_to_bb - ((lower_bound[5] - lower_bound[4]) * 0.5)  # 近平面距離。
    far = distance_cam_to_bb + ((lower_bound[5] - lower_bound[4]) * 0.5)  # 遠平面距離。

    # 設置相機的平行投影比例
    cam1.SetParallelScale((lower_bound[3] - lower_bound[2]) * 0.5)  # 根據 Y 軸範圍設置縮放比例。

    # 根據角度或其他條件設置剪裁範圍
    if angle != 0:  # 如果指定了非零角度。
        cam1.SetClippingRange(near, far - ((far - near) * 0.5))  # 壓縮遠平面範圍。
    elif upper_opacity != 0 and center2 is not None:  # 如果有上層透明度和第二焦點。
        distance_cam_to_bb_up = math.sqrt(
            (cam_position[0] - center2[0])**2 +
            (cam_position[1] - center2[1])**2 +
            (cam_position[2] - center2[2])**2
        )  # 計算相機到第二焦點的距離。
        gap_and_down = distance_cam_to_bb - distance_cam_to_bb_up  # 計算上下模型的距離差。
        cam1.SetClippingRange(near - gap_and_down, far)  # 調整剪裁範圍。
    else:
        cam1.SetClippingRange(near - 2.0, far)  # 默認剪裁範圍。

    renderer.SetActiveCamera(cam1)  # 將配置好的相機設置為渲染器的活動相機。

    # 創建深度圖像過濾器
    depth_image_filter = vtk.vtkWindowToImageFilter()  # 創建窗口到圖像的過濾器。
    depth_image_filter.SetInput(render_window)  # 設置輸入為渲染窗口。
    depth_image_filter.SetInputBufferTypeToZBuffer()  # 使用 Z 緩衝區生成深度圖。

    # 創建縮放過濾器將深度值映射到 0-255
    scale_filter = vtk.vtkImageShiftScale()  # 創建縮放過濾器。
    scale_filter.SetInputConnection(depth_image_filter.GetOutputPort())  # 連接深度圖過濾器。
    scale_filter.SetOutputScalarTypeToUnsignedChar()  # 設置輸出為 8 位無符號整數。
    scale_filter.SetShift(-1)  # 將深度值平移。
    scale_filter.SetScale(-255)  # 縮放深度值到 0-255。

    return scale_filter  # 返回深度圖像的縮放過濾器。

def save_depth_image(output_file_path, scale_filter):  # 定義保存深度圖像的函數。
    # 創建 vtkPNGWriter 以儲存深度圖像
    depth_image_writer = vtk.vtkPNGWriter()  # 創建 PNG 寫入器。

    # 設定輸出的檔案路徑
    depth_image_writer.SetFileName(output_file_path)  # 設置輸出檔案路徑。

    # 將寫入器與縮放過濾器的輸出連接
    depth_image_writer.SetInputConnection(scale_filter.GetOutputPort())  # 連接縮放過濾器。

    # 將深度圖像寫入指定的檔案
    depth_image_writer.Write()  # 執行寫入操作。

def render_file_in_second_window(render2, file_path):  # 定義在第二渲染窗口中渲染檔案的函數。
    """
    在第二個 VTK 渲染窗口 (render2) 中渲染 STL 3D 模型或 PNG 圖像。

    Args:
        render2 (vtkRenderer): VTK 渲染器，負責在第二個視窗中顯示內容。
        file_path (str): 需要渲染的檔案路徑，格式可以是 PNG 圖像或 STL 3D 模型。
    """
    # 確保檔案存在，若檔案不存在則輸出錯誤訊息並返回
    if not os.path.exists(file_path):  # 檢查檔案是否存在。
        print(f"File not found: {file_path}")  # 打印錯誤訊息。
        return

    # 獲取檔案的副檔名來判斷是影像 (PNG) 還是 3D 模型 (STL)
    file_extension = os.path.splitext(file_path)[1].lower()  # 獲取副檔名並轉為小寫。

    if file_extension == ".png":  # 如果是 PNG 檔案。
        reader = vtk.vtkPNGReader()  # 創建 PNG 讀取器。
    elif file_extension == ".stl":  # 如果是 STL 檔案。
        reader = vtk.vtkSTLReader()  # 創建 STL 讀取器。
    else:
        print(f"Unsupported file format: {file_extension}")  # 不支援的格式，打印錯誤訊息。
        return

    # 設定檔案名稱並更新 reader
    reader.SetFileName(file_path)  # 設置檔案路徑。
    reader.Update()  # 更新讀取器以載入檔案。

    # 根據檔案類型建立適當的 actor 來進行渲染
    if file_extension == ".png":  # 如果是 PNG 圖像。
        actor = vtk.vtkImageActor()  # 創建圖像 Actor。
        actor.GetMapper().SetInputConnection(reader.GetOutputPort())  # 設置圖像數據。
    elif file_extension == ".stl":  # 如果是 STL 模型。
        mapper = vtk.vtkPolyDataMapper()  # 創建 PolyData 映射器。
        mapper.SetInputConnection(reader.GetOutputPort())  # 設置 STL 數據。

        actor = vtk.vtkActor()  # 創建 3D 模型 Actor。
        actor.SetMapper(mapper)  # 綁定映射器。

        # 設定 STL 3D 模型的顏色與材質屬性
        actor.GetProperty().SetColor((0.98, 0.98, 0.92))  # 設置顏色為接近象牙白。
        actor.GetProperty().SetSpecular(0.5)  # 設置高光反射（控制光澤）。
        actor.GetProperty().SetSpecularPower(10)  # 設置高光強度（集中光澤）。
        actor.GetProperty().SetDiffuse(0.6)  # 設置漫反射（控制光線散射）。
        actor.GetProperty().SetAmbient(0.1)  # 設置環境光（控制陰影效果）。

    # 清除第二個渲染視窗的所有先前渲染的內容
    render2.RemoveAllViewProps()  # 移除渲染器中的所有 Actor。

    # 將新建立的 actor (影像或 3D 模型) 加入到渲染器中
    render2.AddActor(actor)  # 添加 Actor 到渲染器。

    # 重置相機，使模型或影像自動適配到視窗大小
    render2.ResetCamera()  # 自動調整相機以適應內容。

    # 觸發重新渲染，使新內容顯示在視窗中
    render2.GetRenderWindow().Render()  # 執行渲染。