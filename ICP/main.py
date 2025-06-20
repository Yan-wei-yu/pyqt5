import os
from .ICPgood import MultiwayRegistration
from .remesh import PointCloudReconstruction

def process_and_reconstruct(mesh_path1, mesh_path2, mesh_path3, output_dir="."):


    # 執行點雲配準
    reg = MultiwayRegistration()
    pcd_combined = reg.run_registration(mesh_path1, mesh_path2, mesh_path3)
    # pcd_combined = reg.run_registration_sec(mesh_path1, mesh_path2)


    # 進行泊松表面重建
    reconstructor = PointCloudReconstruction(pcd_combined)
    reconstructor.estimate_normals()
    reconstructor.poisson_reconstruction(depth=8)
    reconstructor.filter_low_density(quantile=0.032)
    reconstructor.smooth_mesh(iterations=5)
    reconstructor.compute_normals_and_color(color=[1, 0.706, 0])
    
    # 根據 mesh_path1 命名輸出檔案
    base_name = os.path.basename(mesh_path1)  # 獲取檔案名稱
    name_without_ext = os.path.splitext(base_name)[0]  # 去掉副檔名
    output_filename1 = os.path.join(output_dir, f"ICP_{name_without_ext}.stl")  # 第一個輸出檔案
    # 儲存並顯示結果
    reconstructor.save_mesh(output_filename1)
    # reconstructor.visualize()
    
    return output_filename1

# 執行函式
# process_and_reconstruct( "./0002/bbox/redata0006bbox.stl","./0002/bbox/redata0006bbox-90.stl","./0002/bbox/redata0006bbox--90.stl")
