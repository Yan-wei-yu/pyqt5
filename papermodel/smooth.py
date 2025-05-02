import vtk

def smooth_stl( input_stl_path, output_stl_path, iterations=20, relaxation_factor=0.2):
    """對 STL 進行平滑處理"""
    reader = vtk.vtkSTLReader()  # STL文件讀取器
    reader.SetFileName(input_stl_path)
    
    smoother = vtk.vtkSmoothPolyDataFilter()  # 平滑過濾器
    smoother.SetInputConnection(reader.GetOutputPort())
    smoother.SetNumberOfIterations(iterations)  # 設定平滑迭代次數
    smoother.SetRelaxationFactor(relaxation_factor)  # 控制平滑強度
    smoother.FeatureEdgeSmoothingOff()  # 關閉邊緣平滑
    smoother.BoundarySmoothingOn()  # 開啟邊界平滑
    smoother.Update()

    writer = vtk.vtkSTLWriter()  # STL文件寫入器
    writer.SetFileName(output_stl_path)
    writer.SetInputConnection(smoother.GetOutputPort())
    writer.Write()


if __name__ == "__main__":
    input_stl_path = "data0007_BB_咬合面_pix2pixfour.stl"  # 輸入 STL 文件路徑
    output_stl_path = "data0007_BB_咬合面_pix2pixfour_smooth.stl"  # 輸出 STL 文件路徑
    smooth_stl(input_stl_path, output_stl_path)


