import vtk
import os
import math
from . import trianglegoodobbox

# 載入 3D 模型並根據檔案格式選擇對應的讀取器
def load_3d_model(filename):
    _, extension = os.path.splitext(filename)  # 取得檔案副檔名
    extension = extension.lower()  # 轉為小寫字母

    # 根據檔案副檔名選擇對應的讀取器
    if extension == '.ply':
        reader = vtk.vtkPLYReader()
    elif extension == '.stl':
        reader = vtk.vtkSTLReader()
    elif extension == '.obj':
        reader = vtk.vtkOBJReader()
    else:
        raise ValueError(f"Unsupported file format: {extension}")  # 不支援的檔案格式，拋出錯誤

    reader.SetFileName(filename)  # 設定檔案名稱
    reader.Update()  # 更新讀取器
    return reader.GetOutput()  # 返回讀取的資料

# 根據 polydata 生成 actor 並設定顏色
def create_actor(polydata, color):
    mapper = vtk.vtkPolyDataMapper()  # 創建資料映射器
    mapper.SetInputData(polydata)  # 設定資料

    actor = vtk.vtkActor()  # 創建 actor
    actor.SetMapper(mapper)  # 設定資料映射器
    prop = actor.GetProperty()
    prop.SetColor(color)           # 設定顏色（淺灰）
    
    # ✨ 加入 shading 設定（類似 GeoMagic）

    prop.ShadingOn()               # 開啟 shading 模式（使用 Phong）
    return actor
# def add_lighting(renderer):
#     light = vtk.vtkLight()
#     light.SetLightTypeToSceneLight()
#     light.SetPosition(1, 1, 1)
#     light.SetFocalPoint(0, 0, 0)
#     light.SetIntensity(0.8)
#     renderer.AddLight(light)

# 計算 actor 的幾何中心
def calculate_center(actor):
    bounds = actor.GetBounds()  # 取得 actor 的邊界
    center = [
        (bounds[1] + bounds[0]) * 0.5,  # x 軸中心
        (bounds[3] + bounds[2]) * 0.5,  # y 軸中心
        (bounds[5] + bounds[4]) * 0.5   # z 軸中心
    ]
    return center

# 合併上下模型的邊界
def twomodel_bound(upper_bounds, lower_bounds):
    combined_bounds = [
        min(upper_bounds[0], lower_bounds[0]),  # x_min
        max(upper_bounds[1], lower_bounds[1]),  # x_max
        min(upper_bounds[2], lower_bounds[2]),  # y_min
        max(upper_bounds[3], lower_bounds[3]),  # y_max
        min(upper_bounds[4], lower_bounds[4]),  # z_min
        max(upper_bounds[5], lower_bounds[5])   # z_max
    ]
    return combined_bounds

# 旋轉 actor 至指定角度
def rotate_actor(actor, center, angle):
    transform = vtk.vtkTransform()
    transform.Translate(-center[0], -center[1], -center[2])
    transform.RotateY(angle) 
    transform.Translate(center[0], center[1], center[2])
    actor.SetUserTransform(transform)

def setup_camera_with_obb(renderer, render_window,upper_actor, center2=None, lower_actor=None, upper_opacity=None, angle=0):
    """
    使用 OBB 邊界設置相機進行深度圖像渲染。

    參數:
        renderer: vtkRenderer 對象。
        render_window: vtkRenderWindow 對象。
        center2: 可選，第二個焦點。
        lower_actor: 可選，較低層次的 actor。
        upper_opacity: 可選，上層透明度。
        angle: 可選，相機額外調整角度。

    返回:
        vtkImageShiftScale: 調整過的深度圖像。
    """

    cam1 = renderer.GetActiveCamera()  # 獲取當前的相機

    # 設置相機的初始位置與剪裁範圍
    cam_position = [0.0, 0.0, 0.0]
    polydata = lower_actor.GetMapper().GetInput()  # 取得模型資料
    if  upper_actor is not None:
        up_polydata = upper_actor.GetMapper().GetInput()  # 取得模型資料
        obb_bounds  = trianglegoodobbox.DentalModelReconstructor.compute_obb_aligned_bounds(polydata,up_polydata)  # 計算 OBB 邊界
    else:
        obb_bounds  = trianglegoodobbox.DentalModelReconstructor.compute_obb_aligned_bounds(polydata,None,angle)  # 計算 OBB 邊界
        
    center1 =  (
        (obb_bounds[0] + obb_bounds[1]) / 2.0,
        (obb_bounds[2] + obb_bounds[3]) / 2.0,
        (obb_bounds[4] + obb_bounds[5]) / 2.0,
    )

    cam1.SetFocalPoint(center1)  # 設定焦點
    cam1.SetParallelProjection(True)  # 啟用平行投影
    cam_position=cam1.GetPosition()

    # 計算相機與模型中心的距離
    distance_cam_to_bb = math.sqrt(
        (cam_position[0] - center1[0])**2 +
        (cam_position[1] - center1[1])**2 +
        (cam_position[2] - center1[2])**2
    )

    # 計算近平面與遠平面的範圍
    near = distance_cam_to_bb - ((obb_bounds[5] -  obb_bounds[4]) * 0.5)
    far = distance_cam_to_bb + ((obb_bounds[5] -  obb_bounds[4]) * 0.5)

    # 設定相機的平行比例
    cam1.SetParallelScale((obb_bounds[3] - obb_bounds[2]) * 0.5)

    # 根據角度或其他條件設置剪裁範圍
    if angle != 0:
        cam1.SetClippingRange(near, far - ((far - near) * 0.5))
    elif upper_opacity is not None and center2 is not None:
        distance_cam_to_bb_up = math.sqrt(
            (cam_position[0] - center2[0])**2 +
            (cam_position[1] - center2[1])**2 +
            (cam_position[2] - center2[2])**2
        )
        gap_and_down = distance_cam_to_bb - distance_cam_to_bb_up

        cam1.SetClippingRange(near - gap_and_down, far)
    else:
        cam1.SetClippingRange(near-2, far)

    renderer.SetActiveCamera(cam1)  # 設定活動相機

    # 創建 vtkWindowToImageFilter 獲取深度圖像
    depth_image_filter = vtk.vtkWindowToImageFilter()
    depth_image_filter.SetInput(render_window)
    depth_image_filter.SetInputBufferTypeToZBuffer()  # 使用 Z 緩衝區

    # 創建 vtkImageShiftScale 將深度值映射至 0-255 範圍
    scale_filter = vtk.vtkImageShiftScale()
    scale_filter.SetInputConnection(depth_image_filter.GetOutputPort())
    scale_filter.SetOutputScalarTypeToUnsignedChar()
    scale_filter.SetShift(-1)
    scale_filter.SetScale(-255)

    return scale_filter  # 返回深度圖像的縮放過濾器

# 設定普通相機進行深度圖像渲染
def setup_camera(renderer, render_window, center2=None, lower_actor=None, upper_opacity=None, angle=0):
    cam1 = renderer.GetActiveCamera()  # 獲取當前的相機

    # 計算並設置相機焦點與其他參數
    cam_position = [0.0, 0.0, 0.0]
    center1 = calculate_center(lower_actor)
    lower_bound = lower_actor.GetBounds()
    cam1.SetFocalPoint(center1)
    cam1.SetParallelProjection(True)
    cam_position=cam1.GetPosition()
    # 計算相機與模型中心的距離
    distance_cam_to_bb = math.sqrt(
        (cam_position[0] - center1[0])**2 +
        (cam_position[1] - center1[1])**2 +
        (cam_position[2] - center1[2])**2
    )

    # 計算近平面與遠平面的範圍
    near = distance_cam_to_bb - ((lower_bound[5] - lower_bound[4]) * 0.5)
    far = distance_cam_to_bb + ((lower_bound[5] - lower_bound[4]) * 0.5)

    # 設定相機的平行比例
    cam1.SetParallelScale((lower_bound[3] - lower_bound[2]) * 0.5)

    # 根據角度或其他條件設置剪裁範圍
    if angle != 0:
        cam1.SetClippingRange(near, far - ((far - near) * 0.5))
    elif upper_opacity != 0 and center2 is not None:
        distance_cam_to_bb_up = math.sqrt(
            (cam_position[0] - center2[0])**2 +
            (cam_position[1] - center2[1])**2 +
            (cam_position[2] - center2[2])**2
        )
        gap_and_down = distance_cam_to_bb - distance_cam_to_bb_up

        cam1.SetClippingRange(near - gap_and_down, far)
    else:
        cam1.SetClippingRange(near-2.0, far)

    renderer.SetActiveCamera(cam1)  # 設定活動相機

    # 創建 vtkWindowToImageFilter 獲取深度圖像
    depth_image_filter = vtk.vtkWindowToImageFilter()
    depth_image_filter.SetInput(render_window)
    depth_image_filter.SetInputBufferTypeToZBuffer()  # 使用 Z 緩衝區

    # 創建 vtkImageShiftScale 將深度值映射至 0-255 範圍
    scale_filter = vtk.vtkImageShiftScale()
    scale_filter.SetInputConnection(depth_image_filter.GetOutputPort())
    scale_filter.SetOutputScalarTypeToUnsignedChar()
    scale_filter.SetShift(-1)
    scale_filter.SetScale(-255)

    return scale_filter  # 返回深度圖像的縮放過濾器


def save_depth_image(output_file_path, scale_filter):
    # 創建 vtkPNGWriter 以儲存深度圖像
    depth_image_writer = vtk.vtkPNGWriter()

    # 設定輸出的檔案路徑
    depth_image_writer.SetFileName(output_file_path)

    # 將寫入器與縮放過濾器的輸出連接（假設該過濾器已經有有效的輸出）
    depth_image_writer.SetInputConnection(scale_filter.GetOutputPort())

    # 將深度圖像寫入指定的檔案
    depth_image_writer.Write()

    # 管線已經設置完成，您現在可以執行過濾器並處理輸出的圖像。



def render_file_in_second_window(render2, file_path):
    """
    在第二個 VTK 渲染窗口 (render2) 中渲染 STL 3D 模型或 PNG 圖像。

    Args:
        render2 (vtkRenderer): VTK 渲染器，負責在第二個視窗中顯示內容。
        file_path (str): 需要渲染的檔案路徑，格式可以是 PNG 圖像或 STL 3D 模型。
    """

    # 確保檔案存在，若檔案不存在則輸出錯誤訊息並返回
    if not os.path.exists(file_path):
        print(f"File not found: {file_path}")
        return

    # 獲取檔案的副檔名來判斷是影像 (PNG) 還是 3D 模型 (STL)
    file_extension = os.path.splitext(file_path)[1].lower()

    if file_extension == ".png":
        # 若為 PNG 檔案，使用 vtkPNGReader 來讀取影像
        reader = vtk.vtkPNGReader()
    elif file_extension == ".stl":
        # 若為 STL 檔案，使用 vtkSTLReader 來讀取 3D 模型
        reader = vtk.vtkSTLReader()
    else:
        # 若檔案格式不支援，則輸出錯誤訊息並返回
        print(f"Unsupported file format: {file_extension}")
        return

    # 設定檔案名稱並更新 reader
    reader.SetFileName(file_path)
    reader.Update()

    # 根據檔案類型建立適當的 actor 來進行渲染
    if file_extension == ".png":
        # 若是 PNG 影像，則使用 vtkImageActor 來顯示
        actor = vtk.vtkImageActor()
        actor.GetMapper().SetInputConnection(reader.GetOutputPort())
    elif file_extension == ".stl":
        # 若是 STL 3D 模型，則建立 vtkPolyDataMapper 來映射 3D 幾何數據
        mapper = vtk.vtkPolyDataMapper()
        mapper.SetInputConnection(reader.GetOutputPort())

        # 創建 vtkActor 來管理模型的外觀
        actor = vtk.vtkActor()
        actor.SetMapper(mapper)

        # 設定 STL 3D 模型的顏色與材質屬性，讓模型更具真實感
        actor.GetProperty().SetColor((0.98, 0.98, 0.92))  # 設定模型顏色 (接近象牙白)
        actor.GetProperty().SetSpecular(0.5)  # 設定反射高光 (越高越亮)
        actor.GetProperty().SetSpecularPower(10)  # 設定高光強度 (數值越高，光澤越集中)
        actor.GetProperty().SetDiffuse(0.6)  # 設定漫反射程度 (影響光線散射)
        actor.GetProperty().SetAmbient(0.1)  # 設定環境光影響 (控制陰影範圍)

    # 清除第二個渲染視窗的所有先前渲染的內容
    render2.RemoveAllViewProps()

    # 將新建立的 actor (影像或 3D 模型) 加入到渲染器中
    render2.AddActor(actor)

    # 重置相機，使模型或影像自動適配到視窗大小
    render2.ResetCamera()

    # 觸發重新渲染，使新內容顯示在視窗中
    render2.GetRenderWindow().Render()
