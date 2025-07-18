# 主要目的：此程式碼定義了一個函數 `get_all_filenames`，用於獲取指定資料夾中所有檔案的路徑物件（Path 物件）清單。該函數使用 `pathlib.Path` 模組，支援跨平台路徑處理，僅返回檔案（非資料夾）的路徑。此程式碼適用於牙科圖像處理流程，例如遍歷 GAN 模型輸出圖像（來自 `apply_gan_model`）或深度圖像（來自 `DentalModelReconstructor` 或 `setup_camera_with_obb`）的資料夾，與邊界檢測（`get_image_bound` 或 `mark_boundary_points`）或遮罩裁剪（`crop_to_mask`）模組整合，用於後續圖像處理或品質評估。

from pathlib import Path  # 導入 Path 類，用於跨平台的文件路徑處理。

def get_all_filenames(folder_path):  # 定義獲取資料夾中所有檔案路徑的函數。
    # 確認路徑是否存在
    path = Path(folder_path)  # 將輸入路徑轉換為 Path 物件。
    if not path.exists():  # 檢查資料夾路徑是否存在。
        print(f"資料夾路徑 {folder_path} 不存在。")  # 若不存在，打印提示訊息。
        return []  # 返回空列表。

    # 獲取資料夾中的所有檔案名稱，返回其中裝著Path物件的list
    filenames = [file for file in path.glob('*') if file.is_file()]  # 使用 glob 遍歷資料夾，僅保留檔案（非資料夾）的 Path 物件。
    
    return filenames  # 返回包含所有檔案路徑物件的列表。


# # 使用範例
# if __name__ == "__main__": # 只有直接執行此檔案時為True
#     folder_path = r'C:\Users\upup5\Desktop\research\DGTS-Inpainting\data\teeth_seem_inlay\test'
#     filenames = get_all_filenames(folder_path)

#     print(f"路徑 ({folder_path}) 中共有{len(filenames)}個檔案")
#     # 列出所有檔案名稱(含後綴)
#     for filename in filenames:
#         print(filename.name)