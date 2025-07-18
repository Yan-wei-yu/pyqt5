# 主要目的：此程式碼定義了一組函數，用於計算兩張圖像之間的多項圖像品質評估指標，包括 PSNR（峰值信噪比）、SSIM（結構相似性）、FSIM（特徵相似性）和 RMSE（均方根誤差）。主函數 `cal_all` 批量處理指定資料夾中的圖像對（修復圖像與真實圖像），支援根據遮罩裁剪圖像，並將結果保存到文本文件。此程式碼適用於牙科圖像處理流程，例如評估 GAN 修復圖像（來自 `apply_gan_model`）與真實圖像的品質，或比較不同視角的深度圖像（來自 `DentalModelReconstructor`），並與邊界檢測（`get_image_bound` 或 `mark_boundary_points`）和遮罩裁剪（`crop_to_mask`）模組整合。

import numpy as np  # 導入 NumPy 庫，用於數值運算和陣列處理。
from skimage.metrics import structural_similarity as mssim  # 導入 SSIM 函數，用於結構相似性計算。
from skimage.metrics import peak_signal_noise_ratio as psnr  # 導入 PSNR 函數，用於峰值信噪比計算。
import os  # 導入 os 模組，用於文件和路徑操作。
import torch  # 導入 PyTorch 庫，用於 FSIM 計算的張量操作。
# import matplotlib.pyplot as plt  # 繪圖庫（已註解，暫未使用）。
import cv2  # 導入 OpenCV 庫，用於圖像讀取和處理。
from .fsim import FSIM, FSIMc  # 導入自定義 FSIM 和 FSIMc 模組，用於特徵相似性計算。
# import Niqe  # NIQE 模組（已註解，暫未使用）。
from sklearn.metrics import mean_squared_error  # 導入均方根誤差 (RMSE) 計算函數。
from .forSSIM.crop import crop_to_mask  # 導入自定義裁剪模組，用於根據遮罩裁剪圖像。

# 計算 SSIM 和 PSNR
def cal_ssim_psnr(img1, img2):  # 定義計算 PSNR 和 SSIM 的函數。
    """
    計算兩張圖像的 PSNR 和 SSIM。
    參數:
        img1: 第一張圖像 (修復圖像，NumPy 陣列，RGB 格式)
        img2: 第二張圖像 (真實圖像，NumPy 陣列，RGB 格式)
    返回:
        PSNR 和 SSIM 的平均值
    """
    cal_psnr = []  # 初始化 PSNR 列表。
    cal_ssim = []  # 初始化 SSIM 列表。

    cal_psnr.append(psnr(img1, img2))  # 計算 PSNR 值並添加到列表。
    cal_ssim.append(mssim(img1, img2, multichannel=True, win_size=None))  # 計算 SSIM 值（多通道模式）並添加到列表。
    return np.array(cal_psnr).mean(), np.array(cal_ssim).mean()  # 返回 PSNR 和 SSIM 的平均值。

# 計算 FSIM（特徵相似性指標）
def cal_fsim(img1, img2):  # 定義計算 FSIM 的函數。
    """
    計算兩張圖像的 FSIM。
    參數:
        img1: 第一張圖像 (修復圖像，NumPy 陣列，RGB 格式)
        img2: 第二張圖像 (真實圖像，NumPy 陣列，RGB 格式)
    返回:
        FSIM 的平均值
    """
    cal_fsim = []  # 初始化 FSIM 列表。
    batch_size = 1  # 批次大小設為 1（單張圖像處理）。

    # 將圖像轉換為 PyTorch 張量並調整維度
    img1 = torch.from_numpy(np.asarray(img1))  # 將 NumPy 陣列轉為 PyTorch 張量。
    img1 = img1.permute(2, 0, 1)  # 調整維度為 [通道, 高度, 寬度]。
    img1 = img1.unsqueeze(0).type(torch.FloatTensor)  # 添加批次維度並轉為浮點型。
    img2 = torch.from_numpy(np.asarray(img2))  # 同上，處理第二張圖像。
    img2 = img2.permute(2, 0, 1)
    img2 = img2.unsqueeze(0).type(torch.FloatTensor)

    # 創建假批次（測試用）
    img1b = torch.cat(batch_size * [img1], 0)  # 重複圖像形成批次。
    img2b = torch.cat(batch_size * [img2], 0)  # 同上，處理第二張圖像。

    # 如果有 GPU 可用，則將數據移至 GPU
    if torch.cuda.is_available():  # 檢查是否可用 CUDA。
        img1b = img1b.cuda()  # 將第一張圖像移至 GPU。
        img2b = img2b.cuda()  # 將第二張圖像移至 GPU。

    # 創建 FSIM 損失函數並計算
    FSIM_loss = FSIM()  # 實例化 FSIM 類（灰階版本）。
    loss = FSIM_loss(img1b, img2b)  # 計算 FSIM 分數。
    cal_fsim.append(loss.cpu().detach().numpy())  # 將結果轉回 CPU 並添加到列表。
    return np.array(cal_fsim).mean()  # 返回 FSIM 的平均值。

# 計算 RMSE（均方根誤差）
def cal_rmse(img1, img2):  # 定義計算 RMSE 的函數。
    """
    計算兩張圖像的 RMSE。
    參數:
        img1: 第一張圖像 (修復圖像，NumPy 陣列，RGB 格式)
        img2: 第二張圖像 (真實圖像，NumPy 陣列，RGB 格式)
    返回:
        RMSE 的平均值
    """
    cal_rmse = []  # 初始化 RMSE 列表。
    img1_flat = img1.reshape(-1, 3)  # 將圖像展平為一維陣列（每個像素有 3 個通道）。
    img2_flat = img2.reshape(-1, 3)  # 同上，處理第二張圖像。
    rms = mean_squared_error(img1_flat, img2_flat, squared=False)  # 計算 RMSE（不取平方）。
    cal_rmse.append(rms)  # 添加 RMSE 值。
    return np.array(cal_rmse).mean()  # 返回 RMSE 的平均值。

# 計算所有指標並保存結果
def cal_all(path_high, path, txt_path, mask_path=None):  # 定義批量計算所有指標的函數。
    """
    計算指定資料夾中所有圖像的 PSNR、SSIM、FSIM 和 RMSE，並將結果保存到文本文件。
    參數:
        path_high: 真實圖像資料夾路徑
        path: 修復圖像資料夾路徑
        txt_path: 結果保存的文本文件路徑
        mask_path: 遮罩圖像資料夾路徑（可選）
    """
    print('computing...')  # 提示計算開始。
    file = open(txt_path, 'w', encoding='utf-8')  # 打開文本文件以寫入結果（使用 UTF-8 編碼）。
    file_list = os.listdir(path)  # 獲取修復圖像資料夾中的文件列表。
    c_psnr = []  # 初始化 PSNR 列表。
    c_ssim = []  # 初始化 SSIM 列表。
    c_fsim = []  # 初始化 FSIM 列表。
    c_rmse = []  # 初始化 RMSE 列表。

    # 保存原始的真實圖像路徑
    original_path_high = path_high  # 複製真實圖像資料夾路徑。

    # 遍歷修復圖像文件
    for i in file_list:  # 迭代資料夾中的每個文件。
        gt_image_path = os.path.join(original_path_high, i)  # 構建真實圖像路徑。
        test_image_path = os.path.join(path, i)  # 構建修復圖像路徑。

        # 如果提供了遮罩路徑，則根據遮罩裁剪圖像
        if mask_path:  # 檢查是否提供遮罩路徑。
            mask_file = os.path.join(mask_path, i.replace(".jpg", ".png"))  # 假設遮罩文件為 PNG 格式。
            if os.path.exists(mask_file):  # 檢查遮罩文件是否存在。
                cropped_gt, marked_gt = crop_to_mask(gt_image_path, mask_file)  # 裁剪真實圖像。
                cropped_test, marked_test = crop_to_mask(test_image_path, mask_file)  # 裁剪修復圖像。
            else:
                print()  # 如果遮罩文件不存在，打印空行並跳過。
                continue
        else:
            # 如果沒有遮罩，直接讀取圖像
            cropped_gt = cv2.imread(gt_image_path)  # 讀取真實圖像（BGR 格式）。
            cropped_test = cv2.imread(test_image_path)  # 讀取修復圖像（BGR 格式）。

        # 計算各項指標
        a, b = cal_ssim_psnr(cropped_test, cropped_gt)  # 計算 PSNR 和 SSIM。
        c = cal_fsim(cropped_test, cropped_gt)  # 計算 FSIM。
        f = cal_rmse(cropped_test, cropped_gt)  # 計算 RMSE。

        # 將結果添加到列表
        c_psnr.append(a)  # 添加 PSNR 值。
        c_ssim.append(b)  # 添加 SSIM 值。
        c_fsim.append(c)  # 添加 FSIM 值。
        c_rmse.append(f)  # 添加 RMSE 值。

        # 格式化並寫入單張圖像的結果
        result_str = (f"{i} - PSNR: {a:.4f}, SSIM: {b:.4f}, "
                      f"FSIM: {c:.4f}, RMSE: {f:.4f}\n")  # 格式化結果字符串。
        file.write(result_str)  # 寫入文件。
        print(result_str)  # 同時打印到控制台。

    # 如果有成功處理的數據，計算並保存平均值
    if len(c_psnr) > 0:  # 檢查是否有有效數據。
        avg_psnr = np.mean(c_psnr)  # 計算平均 PSNR。
        avg_ssim = np.mean(c_ssim)  # 計算平均 SSIM。
        avg_fsim = np.mean(c_fsim)  # 計算平均 FSIM。
        avg_rmse = np.mean(c_rmse)  # 計算平均 RMSE。

        # 格式化並寫入平均值
        avg_str = (f"\nAverages:\nPSNR: {avg_psnr:.4f}\nMS-SSIM: {avg_ssim:.4f}\n"
                   f"FSIM: {avg_fsim:.4f}\nRMSE: {avg_rmse:.4f}")  # 格式化平均值字符串。
        file.write(avg_str)  # 寫入文件。
        print(avg_str)  # 打印到控制台。

    file.close()  # 關閉文件。
    print('Computation completed')  # 提示計算完成。