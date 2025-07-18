# 主要目的：此程式碼定義了一個函數 `calculate_image_difference`，用於計算兩張灰階圖像的像素值差異，生成一張新的灰階圖像，其中每個像素值表示兩張輸入圖像對應像素的絕對差異。該函數適用於牙科圖像處理流程，例如比較 GAN 模型生成的修復圖像與原始圖像的差異，或比較不同視角的深度圖像。結果圖像可選擇保存到指定路徑，並與 `DentalModelReconstructor` 和邊界檢測模組整合，用於可視化牙科模型的差異分析。

from PIL import Image  # 導入 PIL 庫，用於圖像處理和操作。

def calculate_image_difference(image1, image2, output_image_path=None):  # 定義計算圖像差異的函數。
    """
    計算兩張灰階圖像的像素值絕對差異，生成差異圖像。

    參數:
        image1: 字串或 PIL.Image，第一張輸入圖像的路徑或圖像物件。
        image2: 字串或 PIL.Image，第二張輸入圖像的路徑或圖像物件。
        output_image_path: 字串，可選，輸出差異圖像的保存路徑。

    返回:
        PIL.Image: 包含像素值絕對差異的新圖像（灰階）。
    """
    image1 = Image.open(image1)  # 打開第一張圖像（假設為灰階圖像）。
    image2 = Image.open(image2)  # 打開第二張圖像（假設為灰階圖像）。

    # 將圖像數據轉換為像素列表
    pixels1 = list(image1.getdata())  # 獲取第一張圖像的像素值列表（展平為一維）。
    pixels2 = list(image2.getdata())  # 獲取第二張圖像的像素值列表（展平為一維）。

    new_data = []  # 初始化差異像素值列表。

    # 計算像素差異
    for i in range(len(pixels1)):  # 迭代所有像素。
        new = abs(pixels2[i] - pixels1[i])  # 計算對應像素值的絕對差異。
        new_data.append(new)  # 將差異值添加到列表。

    # 創建新圖像並填充差異數據
    new_image = Image.new(image1.mode, image1.size)  # 創建與第一張圖像相同模式和尺寸的新圖像。
    new_image.putdata(new_data)  # 將差異像素值填充到新圖像。

    # 如果指定了輸出路徑，則保存圖像
    if output_image_path:  # 檢查是否提供了輸出路徑。
        new_image.save(output_image_path)  # 保存差異圖像到指定路徑。

    return new_image  # 返回生成的差異圖像。
# # 資料夾路徑
# folder_path1 = "D:/Users/user/Desktop/weiyundontdelete/GANdata/trainingdepth/DAISdepth/alldata/depthfordifferentr/DCPRdepth/r=0/Prepfill/"
# folder_path2 = "D:/Users/user/Desktop/weiyundontdelete/GANdata/trainingdepth/DAISdepth/alldata/depthfordifferentr/DCPRdepth/r=0/up/"

# # 輸出資料夾
# output_folder =  "D:/Users/user/Desktop/weiyundontdelete/GANdata/trainingdepth/DAISdepth/alldata/depthfordifferentr/DCPRdepth/r=0/combineimage1"

# # 確保輸出資料夾存在
# if not os.path.exists(output_folder):
#     os.makedirs(output_folder)

# # 取得資料夾中所有檔案名稱
# files1 = os.listdir(folder_path1)
# files2 = os.listdir(folder_path2)

# # 遍歷第一個資料夾
# for filename1 in files1:
#     if filename1 in files2:
#         image1 = Image.open(os.path.join(folder_path2, filename1))
#         image2 = Image.open(os.path.join(folder_path1, filename1))

#         pixels1 = list(image1.getdata())
#         pixels2 = list(image2.getdata())

#         new_data = []

#         for i in range(len(pixels1)):
#             new = abs(pixels2[i] - pixels1[i])
#             new_data.append(new)

#         new_image = Image.new(image1.mode, image1.size)
#         new_image.putdata(new_data)

#         # 生成輸出檔案名稱
#         output_filename = os.path.join(output_folder, filename1)

#         new_image.save(output_filename)

# print("處理完成。結果已儲存在output資料夾中。")
