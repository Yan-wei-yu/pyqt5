# 主要目的：此程式碼用於批量處理指定資料夾中的 PNG 圖像，將其縮放至指定尺寸（預設 730x730），並裁剪出中心區域（預設 256x256），保存到輸出資料夾。支援命令行參數配置輸入和輸出路徑，適用於牙科圖像預處理，例如準備 GAN 模型訓練數據（與 `apply_gan_model` 整合）或深度圖像處理（與 `DentalModelReconstructor` 配合）。程式碼與邊界檢測（`get_image_bound` 或 `mark_boundary_points`）和遮罩裁剪（`crop_to_mask`）模組間接關聯，用於生成標準化輸入數據。

from PIL import Image  # 導入 PIL 庫，用於圖像處理（打開、縮放、裁剪、保存圖像）。
import os  # 導入 os 模組，用於文件和目錄操作（遍歷文件夾、創建目錄等）。
import argparse  # 導入 argparse 模組，用於解析命令行參數。

# 命令行參數設置
parser = argparse.ArgumentParser()  # 創建 ArgumentParser 物件，用於解析命令行參數。
parser.add_argument("--input_dir", default="D:/Users/user/Desktop/weiyundontdelete/GANdata/trainingdepth/DAISdepth/alldata/foranswer/", 
                    help="輸入 PNG 圖像文件夾")  # 定義輸入文件夾參數，預設為指定路徑。
parser.add_argument("--output_dir", default="D:/Users/user/Desktop/weiyundontdelete/GANdata/trainingdepth/DAISdepth/alldata/foranswercrop/", 
                    help="輸出 PNG 圖像文件夾")  # 定義輸出文件夾參數，預設為指定路徑。
args = parser.parse_args()  # 解析命令行參數，儲存到 args 物件。

def crop_and_resize_image(input_file, output_file, scale_size=730, crop_size=256):  # 定義單張圖像裁剪和縮放函數。
    """
    裁剪並調整圖片大小，保存到指定位置。
    參數:
        input_file: 輸入圖片文件路徑（字串）
        output_file: 輸出圖片文件路徑（字串）
        scale_size: 縮放到的尺寸（預設為730，寬高均為此值）
        crop_size: 裁剪區域的大小（預設為256，裁剪出正方形區域）
    """
    img = Image.open(input_file)  # 使用 PIL 打開輸入圖像文件。

    # 計算偏移量（根據縮放比例調整）
    offset_height = int(95 * (scale_size / crop_size))  # 計算高度偏移量，根據縮放比例縮放原始偏移 95。
    offset_width = int(80 * (scale_size / crop_size))   # 計算寬度偏移量，根據縮放比例縮放原始偏移 80。

    # 調整圖片大小至 [scale_size, scale_size]，使用抗鋸齒濾波
    img = img.resize((scale_size, scale_size), Image.ANTIALIAS)  # 縮放圖像至指定尺寸，使用抗鋸齒濾波提高品質。

    # 設置裁剪區域 (left, upper, right, lower)
    left = offset_width  # 左邊界，根據偏移量設置。
    top = offset_height  # 上邊界，根據偏移量設置。
    right = offset_width + crop_size  # 右邊界，左邊界加裁剪尺寸。
    bottom = offset_height + crop_size  # 下邊界，上邊界加裁剪尺寸。

    # 裁剪圖片
    img = img.crop((left, top, right, bottom))  # 根據指定區域裁剪圖像。

    # 保存裁剪後的圖片為 PNG 格式
    img.save(output_file, format="PNG")  # 將裁剪後的圖像保存為 PNG 格式。

def process_folder(input_dir, output_dir, scale_size=730, crop_size=256):  # 定義批量處理文件夾的函數。
    """
    遍歷文件夾，裁剪並保存圖片。
    參數:
        input_dir: 輸入文件夾路徑（字串）
        output_dir: 輸出文件夾路徑（字串）
        scale_size: 縮放到的尺寸（預設為730）
        crop_size: 裁剪區域的大小（預設為256）
    """
    # 如果輸出文件夾不存在，則創建
    if not os.path.exists(output_dir):  # 檢查輸出資料夾是否存在。
        os.makedirs(output_dir)  # 若不存在，創建資料夾。

    # 遍歷輸入文件夾中的所有文件
    for filename in os.listdir(input_dir):  # 迭代輸入資料夾中的所有文件。
        input_file = os.path.join(input_dir, filename)  # 構建輸入文件的完整路徑。
        output_file = os.path.join(output_dir, filename)  # 構建輸出文件的完整路徑。

        # 檢查是否為文件且為 PNG 格式
        if os.path.isfile(input_file) and input_file.lower().endswith('.png'):  # 確認文件是 PNG 格式。
            print(f"Processing file: {input_file}")  # 打印正在處理的文件路徑。
            crop_and_resize_image(input_file, output_file, scale_size, crop_size)  # 對圖像進行裁剪和縮放。
            print(f"Saved to: {output_file}")  # 打印保存的輸出文件路徑。

if __name__ == "__main__":  # 主程式入口。
    # 從命令行參數獲取輸入和輸出文件夾路徑
    input_dir = args.input_dir  # 獲取輸入資料夾路徑。
    output_dir = args.output_dir  # 獲取輸出資料夾路徑。

    # 執行文件夾處理
    process_folder(input_dir, output_dir)  # 調用批量處理函數，處理所有 PNG 圖像。