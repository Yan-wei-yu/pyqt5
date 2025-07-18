# 主要目的：此程式碼定義了一個函數 `compare_image_folders`，用於比較兩個資料夾中相同名稱的圖像，計算它們的像素級絕對差異（absdiff），並將差異圖像保存到指定的輸出資料夾。圖像會被調整為統一大小（預設 256x256），並轉為灰階進行比較。此程式碼適用於牙科圖像處理流程，例如比較 GAN 模型修復的圖像（來自 `apply_gan_model`）與標準答案圖像（來自 `DentalModelReconstructor` 或 `setup_camera_with_obb`），或檢查邊界檢測結果（來自 `get_image_bound` 或 `mark_boundary_points`）的差異，支援 PNG、JPG、JPEG、BMP 和 TIFF 格式。

import os  # 導入 os 模組，用於文件和目錄操作（遍歷文件夾、創建目錄等）。
import cv2  # 導入 OpenCV 庫，用於圖像讀取、調整大小、像素差異計算和保存。

def compare_image_folders(folder1, folder2, output_folder, image_size=(256, 256)):  # 定義比較圖像資料夾的函數。
    """
    比較兩個資料夾中的相同圖片，計算像素差異並輸出到指定資料夾。
    
    :param folder1: 第一個圖片資料夾 (標準答案，字串路徑)
    :param folder2: 第二個圖片資料夾 (測試結果，字串路徑)
    :param output_folder: 差異圖片輸出資料夾 (字串路徑)
    :param image_size: 重新調整的圖片大小 (預設為 256x256，元組)
    """
    os.makedirs(output_folder, exist_ok=True)  # 創建輸出資料夾，若已存在則不報錯。

    # 過濾有效的圖片副檔名
    valid_extensions = {'.png', '.jpg', '.jpeg', '.bmp', '.tiff'}  # 定義支援的圖像格式副檔名集合。
    images1 = {f for f in os.listdir(folder1) if os.path.splitext(f)[1].lower() in valid_extensions}  # 獲取第一個資料夾中有效圖像文件名集合。
    images2 = {f for f in os.listdir(folder2) if os.path.splitext(f)[1].lower() in valid_extensions}  # 獲取第二個資料夾中有效圖像文件名集合。

    # 找到共同的圖片
    common_images = images1.intersection(images2)  # 計算兩個資料夾中相同文件名的交集。

    if not common_images:  # 檢查是否有共同圖像。
        print("沒有找到相同的圖片檔案。")  # 若無共同圖像，打印提示並退出。
        return

    for image_name in common_images:  # 遍歷共同圖像文件名。
        img1_path = os.path.join(folder1, image_name)  # 構建第一個資料夾中圖像的完整路徑。
        img2_path = os.path.join(folder2, image_name)  # 構建第二個資料夾中圖像的完整路徑。

        img1 = cv2.imread(img1_path, cv2.IMREAD_GRAYSCALE)  # 以灰階模式讀取第一張圖像。
        img2 = cv2.imread(img2_path, cv2.IMREAD_GRAYSCALE)  # 以灰階模式讀取第二張圖像。

        if img1 is None or img2 is None:  # 檢查圖像是否成功讀取。
            print(f"讀取失敗: {image_name}")  # 若任一圖像讀取失敗，打印提示並跳過。
            continue

        # 調整圖片大小
        img1 = cv2.resize(img1, image_size)  # 將第一張圖像調整為指定大小（預設 256x256）。
        img2 = cv2.resize(img2, image_size)  # 將第二張圖像調整為指定大小（預設 256x256）。

        # 計算像素差異
        diff = cv2.absdiff(img1, img2)  # 計算兩張圖像的像素級絕對差異。

        # 儲存差異圖片
        diff_path = os.path.join(output_folder, f"diff_{image_name}")  # 構建差異圖像的輸出路徑（添加 "diff_" 前綴）。
        cv2.imwrite(diff_path, diff)  # 將差異圖像保存到輸出路徑。

        print(f"已儲存差異圖: {diff_path}")  # 打印保存的差異圖像路徑。

    print("比對完成！")  # 提示比較完成。

# # 使用範例
# folder1 = 'D:/Users/user/Desktop/weiyundontdelete/GANdata/trainingdepth/DAISdepth/alldata/prdeictdata/evaluted_testdata_answer/'
# folder2 = 'D:/Users/user/Desktop/weiyundontdelete/GANdata/trainingdepth/DAISdepth/alldata/prdeictdata/Ablation_Study_Test2/'
# output_folder = 'D:/Users/user/Desktop/weiyundontdelete/GANdata/trainingdepth/DAISdepth/alldata/compare_pixel/Ablation_Study_Test2'

# compare_image_folders(folder1, folder2, output_folder)