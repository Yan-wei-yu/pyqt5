# 進行多視角牙科 3D 模型的點雲配準 (ICP) + 重建 (Poisson Surface Reconstruction)，並輸出平滑化 STL 檔案。
import os
from .ICPgood import MultiwayRegistration   # 匯入 ICP 模組，用於多視角點雲配準
from .remesh import PointCloudReconstruction  # 匯入重建模組，用於點雲表面重建

def process_and_reconstruct(mesh_path1, mesh_path2, mesh_path3, output_dir="."):
    """
    功能：
    執行多視角模型的點雲 ICP 配準，並進行 Poisson 表面重建，最後輸出 STL 檔案。
    
    參數：
    mesh_path1: str -> 第一個 3D 模型檔案路徑（通常為正面）
    mesh_path2: str -> 第二個 3D 模型檔案路徑（通常為左側）
    mesh_path3: str -> 第三個 3D 模型檔案路徑（通常為右側，當前未使用）
    output_dir: str -> 輸出 STL 檔案的資料夾路徑，預設為當前目錄
    
    回傳：
    str -> 最終重建後的 STL 檔案路徑
    """

    # -------------------- [1] 執行點雲配準 (ICP) --------------------
    reg = MultiwayRegistration()  # 建立多視角 ICP 配準物件
    # 執行配準，目前僅使用 mesh_path1 和 mesh_path2
    # 如果需要使用第三個模型，可以改成 run_registration(mesh_path1, mesh_path2, mesh_path3)
    # pcd_combined = reg.run_registration_sec(mesh_path1, mesh_path2)
    pcd_combined = reg.run_registration(mesh_path1, mesh_path2, mesh_path3)  # 執行配準，將三個模型合併為一個點雲


    # -------------------- [2] 進行 Poisson 表面重建 --------------------
    reconstructor = PointCloudReconstruction(pcd_combined)  # 初始化重建器，傳入合併後的點雲
    reconstructor.estimate_normals()            # 計算法向量，Poisson 重建需要法向資訊
    reconstructor.poisson_reconstruction(depth=8)  # 執行 Poisson 表面重建，depth=8 表示八叉樹深度，數值越大細節越高

    # -------------------- [3] 網格後處理 --------------------
    reconstructor.filter_low_density(quantile=0.032)  # 過濾低密度點（刪除雜點），quantile 控制保留比例
    reconstructor.smooth_mesh(iterations=5)           # 平滑處理網格，預設迭代 5 次
    reconstructor.compute_normals_and_color(color=[1, 0.706, 0])  # 重新計算法向並給模型上色（黃色）

    # -------------------- [4] 儲存結果 STL 檔 --------------------
    base_name = os.path.basename(mesh_path1)               # 取得第一個輸入檔案名稱（含副檔名）
    name_without_ext = os.path.splitext(base_name)[0]      # 去掉副檔名，僅保留檔名
    output_filename1 = os.path.join(output_dir, f"ICP_{name_without_ext}.stl")  # 輸出檔案路徑（增加前綴 ICP_）
    
    reconstructor.save_mesh(output_filename1)  # 將重建後的網格儲存為 STL 檔
    reconstructor.visualize()  # （註解掉）如需視覺化，可解除註解呼叫此方法

    # 回傳輸出的 STL 檔案路徑
    return output_filename1


# # 執行函式
# process_and_reconstruct( "./0002/rebbox/redata0002bbox.stl","./0002/rebbox/redata0002bbox-90.stl","./0002/rebbox/redata0002bbox--90.stl")
