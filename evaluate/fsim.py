# 主要目的：此程式碼實現了 PyTorch 版本的 FSIM（Feature SIMilarity）和 FSIMc（彩色版本），用於評估兩張圖像的結構相似度，適用於牙科圖像品質評估（例如比較 GAN 修復圖像與參考圖像）。FSIM 基於相位一致性（Phase Congruency）和梯度相似度，FSIMc 額外考慮色彩通道（YIQ 空間的 I 和 Q 分量）。程式碼包括基礎類 `FSIM_base` 以及兩個衍生類 `FSIM`（灰階）和 `FSIMc`（彩色），支援 CUDA 加速，並與 `DentalModelReconstructor`、邊界檢測和 GAN 模組整合，用於牙科圖像處理和 3D 重建流程中的品質控制。

import torch as pt  # 導入 PyTorch 庫，用於張量操作和神經網絡。
import torch.nn as nn  # 導入 PyTorch 的神經網絡模組。
import torch.nn.functional as FUN  # 導入 PyTorch 的功能模組，包含卷積等操作。
import numpy as np  # 導入 NumPy 庫，用於數值運算。
import math  # 導入 math 模組，用於數學計算（如 pi）。

'''
這段程式碼是 PyTorch 版本的 FSIM（Feature SIMilarity）實現，
原始 MATLAB 版本由 Lin ZHANG 等人提出。
FSIM 用於評估兩張圖片的結構相似度，通常應用於圖像品質評估。
原始演算法請參考：
https://www4.comp.polyu.edu.hk/~cslzhang/IQA/FSIM/FSIM.htm
'''

class FSIM_base(nn.Module):  # 定義 FSIM 的基礎類，繼承自 nn.Module。
    def __init__(self):  # 初始化方法。
        nn.Module.__init__(self)  # 調用父類的初始化方法。
        # 是否使用 CUDA 加速
        self.cuda_computation = False  # 預設不使用 CUDA。

        # 小波濾波器參數
        self.nscale = 4  # 尺度數（小波分解層數）。
        self.norient = 4  # 方向數（濾波方向數量）。
        self.k = 2.0  # 噪聲抑制門檻參數。
        self.epsilon = .0001  # 避免除零的小值。
        self.pi = math.pi  # 圓周率 π。

        # Log-Gabor 濾波器參數
        minWaveLength = 6  # 最小尺度濾波器的波長。
        mult = 2  # 尺度之間的倍率。
        sigmaOnf = 0.55  # Log-Gabor 濾波器頻率域標準差。
        dThetaOnSigma = 1.2  # 控制方向濾波器的角度擴散。

        # 計算角度高斯函數的標準差
        self.thetaSigma = self.pi / self.norient / dThetaOnSigma  # 角度標準差。

        # 濾波器中心頻率（4 個尺度）
        self.fo = (1.0 / (minWaveLength * pt.pow(mult, pt.arange(0, self.nscale, dtype=pt.float64)))).unsqueeze(0)  # 計算各尺度的中心頻率。
        self.den = 2 * (math.log(sigmaOnf)) ** 2  # Log-Gabor 濾波器的分母項。

        # Sobel-like 梯度卷積核（水平與垂直方向）
        self.dx = -pt.tensor([[[[3, 0, -3], [10, 0, -10], [3, 0, -3]]]]) / 16.0  # 水平方向梯度核。
        self.dy = -pt.tensor([[[[3, 10, 3], [0, 0, 0], [-3, -10, -3]]]]) / 16.0  # 垂直方向梯度核。

        # FSIM 常數，用於相似度公式
        self.T1 = 0.85  # 相位一致性相似度常數。
        self.T2 = 160  # 梯度相似度常數。
        self.T3 = 200  # I 通道相似度常數。
        self.T4 = 200  # Q 通道相似度常數。
        self.lambdac = 0.03  # FSIMc 中色彩通道權重。

    def set_arrays_to_cuda(self):  # 將內部張量移至 CUDA。
        """將內部張量移至 CUDA"""
        self.cuda_computation = True  # 啟用 CUDA 計算。
        self.fo = self.fo.cuda()  # 將中心頻率張量移至 CUDA。
        self.dx = self.dx.cuda()  # 將水平梯度核移至 CUDA。
        self.dy = self.dy.cuda()  # 將垂直梯度核移至 CUDA。

    def forward_gradloss(self, imgr, imgd):  # 計算梯度相似度損失。
        """
        計算梯度相似度損失，用於梯度一致性學習
        imgr: 參考圖像（批次張量，形狀為 [batch, channels, height, width]）
        imgd: 待評估圖像（同上）
        """
        # 將圖像轉換至 YIQ 色彩空間，提取亮度 Y
        I1, Q1, Y1 = self.process_image_channels(imgr)  # 處理參考圖像，提取 YIQ 分量。
        I2, Q2, Y2 = self.process_image_channels(imgd)  # 處理待評估圖像，提取 YIQ 分量。

        # 計算梯度圖
        gradientMap1 = self.calculate_gradient_map(Y1)  # 計算參考圖像的梯度圖。
        gradientMap2 = self.calculate_gradient_map(Y2)  # 計算待評估圖像的梯度圖。

        # 計算梯度相似度矩陣
        gradientSimMatrix = self.calculate_gradient_sim(gradientMap1, gradientMap2)  # 計算梯度相似度。

        # 計算總梯度損失
        gradloss = pt.sum(pt.sum(pt.sum(gradientSimMatrix, 1), 1))  # 對相似度矩陣求和，得到總梯度損失。
        return gradloss

    def calculate_fsim(self, gradientSimMatrix, PCSimMatrix, PCm):  # 計算 FSIM 分數。
        """
        FSIM 計算公式：
        FSIM = Σ( Gsim * PCsim * PCm ) / Σ( PCm )
        """
        SimMatrix = gradientSimMatrix * PCSimMatrix * PCm  # 結合梯度相似度和相位一致性。
        FSIM = pt.sum(pt.sum(SimMatrix, 1), 1) / pt.sum(pt.sum(PCm, 1), 1)  # 計算 FSIM 分數。
        return FSIM

    def calculate_fsimc(self, I1, Q1, I2, Q2, gradientSimMatrix, PCSimMatrix, PCm):  # 計算 FSIMc 分數。
        """
        FSIMc：彩色版本的 FSIM，額外考慮 I、Q 色彩通道相似度
        """
        ISimMatrix = (2 * I1 * I2 + self.T3) / (pt.pow(I1, 2) + pt.pow(I2, 2) + self.T3)  # 計算 I 通道相似度。
        QSimMatrix = (2 * Q1 * Q2 + self.T4) / (pt.pow(Q1, 2) + pt.pow(Q2, 2) + self.T4)  # 計算 Q 通道相似度。
        SimMatrixC = gradientSimMatrix * PCSimMatrix * (pt.pow(pt.abs(ISimMatrix * QSimMatrix), self.lambdac)) * PCm  # 結合所有相似度分量。
        FSIMc = pt.sum(pt.sum(SimMatrixC, 1), 1) / pt.sum(pt.sum(PCm, 1), 1)  # 計算 FSIMc 分數。
        return FSIMc

    def lowpassfilter(self, rows, cols):  # 建立低通濾波器。
        """
        建立低通濾波器，用於抑制高頻雜訊
        """
        cutoff = .45  # 低通濾波器截止頻率。
        n = 15  # 濾波器階數。
        x, y = self.create_meshgrid(cols, rows)  # 生成網格座標。
        radius = pt.sqrt(pt.pow(x, 2) + pt.pow(y, 2)).unsqueeze(0)  # 計算頻率域半徑。
        f = self.ifftshift2d(1 / (1.0 + pt.pow(pt.div(radius, cutoff), 2 * n)))  # 計算低通濾波器。
        return f

    def calculate_gradient_sim(self, gradientMap1, gradientMap2):  # 計算梯度相似度。
        """
        計算梯度相似度：
        Gsim = (2*g1*g2 + T2) / (g1^2 + g2^2 + T2)
        """
        gradientSimMatrix = (2 * gradientMap1 * gradientMap2 + self.T2) / (pt.pow(gradientMap1, 2) + pt.pow(gradientMap2, 2) + self.T2)  # 計算梯度相似度矩陣。
        return gradientSimMatrix

    def calculate_gradient_map(self, Y):  # 計算梯度圖。
        """
        使用 Sobel-like 卷積計算梯度強度
        """
        IxY = FUN.conv2d(Y, self.dx, padding=1)  # 水平方向梯度。
        IyY = FUN.conv2d(Y, self.dy, padding=1)  # 垂直方向梯度。
        gradientMap1 = pt.sqrt(pt.pow(IxY, 2) + pt.pow(IyY, 2))  # 計算梯度強度。
        return gradientMap1

    def calculate_phase_score(self, PC1, PC2):  # 計算相位一致性相似度。
        """
        計算相位一致性相似度：
        PCsim = (2*PC1*PC2 + T1) / (PC1^2 + PC2^2 + T1)
        PCm = max(PC1, PC2)
        """
        PCSimMatrix = (2 * PC1 * PC2 + self.T1) / (pt.pow(PC1, 2) + pt.pow(PC2, 2) + self.T1)  # 計算相位一致性相似度。
        PCm = pt.where(PC1 > PC2, PC1, PC2)  # 取相位一致性的最大值。
        return PCSimMatrix, PCm

    def roll_1(self, x, n):  # 張量循環平移。
        """
        將張量沿著某一維度循環平移 n 個元素
        """
        return pt.cat((x[:, -n:, :, :, :], x[:, :-n, :, :, :]), dim=1)  # 沿指定維度平移。

    def ifftshift(self, tens, var_axis):  # 調整頻率中心位置。
        """
        用於調整頻率中心位置
        """
        len11 = int(tens.size()[var_axis] / 2)  # 計算平移長度。
        len12 = tens.size()[var_axis] - len11  # 計算剩餘長度。
        return pt.cat((tens.narrow(var_axis, len11, len12), tens.narrow(var_axis, 0, len11)), axis=var_axis)  # 執行平移。

    def ifftshift2d(self, tens):  # 對 2D 資料進行 ifftshift。
        """
        對 2D 資料進行 ifftshift
        """
        return self.ifftshift(self.ifftshift(tens, 1), 2)  # 對兩個維度依次平移。

    def create_meshgrid(self, cols, rows):  # 生成網格座標。
        """
        生成網格座標，用於頻率域濾波器
        """
        if cols % 2:  # 若列數為奇數。
            xrange = pt.arange(start=-(cols - 1) / 2, end=(cols - 1) / 2 + 1, step=1, requires_grad=False) / (cols - 1)  # 計算 x 範圍。
        else:  # 若列數為偶數。
            xrange = pt.arange(-(cols) / 2, (cols) / 2, step=1, requires_grad=False) / (cols)  # 計算 x 範圍。

        if rows % 2:  # 若行數為奇數。
            yrange = pt.arange(-(rows - 1) / 2, (rows - 1) / 2 + 1, step=1, requires_grad=False) / (rows - 1)  # 計算 y 範圍。
        else:  # 若行數為偶數。
            yrange = pt.arange(-(rows) / 2, (rows) / 2, step=1, requires_grad=False) / (rows)  # 計算 y 範圍。

        x, y = pt.meshgrid([xrange, yrange])  # 生成網格座標。

        if self.cuda_computation:  # 若啟用 CUDA。
            x, y = x.cuda(), y.cuda()  # 將座標移至 CUDA。

        return x.T, y.T  # 返回轉置後的座標。

    def process_image_channels(self, img):  # 處理圖像通道，轉換為 YIQ。
        """
        將輸入 RGB 轉換成 YIQ 色彩空間，提取亮度 Y、I、Q 分量
        並進行下採樣（根據輸入尺寸）
        """
        batch, rows, cols = img.shape[0], img.shape[2], img.shape[3]  # 獲取批次、行數和列數。

        minDimension = min(rows, cols)  # 獲取最小尺寸。

        # RGB → YIQ 轉換係數
        Ycoef = pt.tensor([[0.299, 0.587, 0.114]])  # Y 分量（亮度）轉換係數。
        Icoef = pt.tensor([[0.596, -0.274, -0.322]])  # I 分量（色度）轉換係數。
        Qcoef = pt.tensor([[0.211, -0.523, 0.312]])  # Q 分量（色度）轉換係數。

        if self.cuda_computation:  # 若啟用 CUDA。
            Ycoef, Icoef, Qcoef = Ycoef.cuda(), Icoef.cuda(), Qcoef.cuda()  # 將係數移至 CUDA。

        Yfilt = pt.cat(batch * [pt.cat(rows * cols * [Ycoef.unsqueeze(2)], dim=2).view(1, 3, rows, cols)], 0)  # 構建 Y 分量濾波器。
        Ifilt = pt.cat(batch * [pt.cat(rows * cols * [Icoef.unsqueeze(2)], dim=2).view(1, 3, rows, cols)], 0)  # 構建 I 分量濾波器。
        Qfilt = pt.cat(batch * [pt.cat(rows * cols * [Qcoef.unsqueeze(2)], dim=2).view(1, 3, rows, cols)], 0)  # 構建 Q 分量濾波器。

        # 如果輸入是 RGB
        if img.size()[1] == 3:  # 若輸入為 RGB 圖像（3 通道）。
            Y = pt.sum(Yfilt * img, 1).unsqueeze(1)  # 計算 Y 分量。
            I = pt.sum(Ifilt * img, 1).unsqueeze(1)  # 計算 I 分量。
            Q = pt.sum(Qfilt * img, 1).unsqueeze(1)  # 計算 Q 分量。
        else:  # 若輸入為灰階圖像（1 通道）。
            Y = pt.mean(img, 1).unsqueeze(1)  # 取平均值作為 Y 分量。
            I = pt.ones(Y.size(), dtype=pt.float64)  # I 分量設為全 1。
            Q = pt.ones(Y.size(), dtype=pt.float64)  # Q 分量設為全 1。

        # 下採樣比例
        F = max(1, round(minDimension / 256))  # 根據最小尺寸計算下採樣比例。

        # 均值池化
        aveKernel = nn.AvgPool2d(kernel_size=F, stride=F, padding=0)  # 創建平均池化層。
        if self.cuda_computation:  # 若啟用 CUDA。
            aveKernel = aveKernel.cuda()  # 將池化層移至 CUDA。

        # 輸出 Y、I、Q
        I = aveKernel(I)  # 下採樣 I 分量。
        Q = aveKernel(Q)  # 下採樣 Q 分量。
        Y = aveKernel(Y)  # 下採樣 Y 分量。
        return I, Q, Y  # 返回 YIQ 分量。

    def phasecong2(self, img):  # 計算相位一致性。
        """
        計算圖像的相位一致性（Phase Congruency），基於 Log-Gabor 濾波器。
        濾波器由徑向分量（控制頻率帶）和角度分量（控制方向）組成。
        """
        batch, rows, cols = img.shape[0], img.shape[2], img.shape[3]  # 獲取批次、行數和列數。

        imagefft = pt.rfft(img, signal_ndim=2, onesided=False)  # 對圖像進行 2D 快速傅里葉變換。

        x, y = self.create_meshgrid(cols, rows)  # 生成網格座標。

        radius = pt.cat(batch * [pt.sqrt(pt.pow(x, 2) + pt.pow(y, 2)).unsqueeze(0)], 0)  # 計算頻率域半徑。
        theta = pt.cat(batch * [pt.atan2(-y, x).unsqueeze(0)], 0)  # 計算頻率域角度。

        radius = self.ifftshift2d(radius)  # 將半徑張量進行 ifftshift。
        theta = self.ifftshift2d(theta)  # 將角度張量進行 ifftshift。

        radius[:, 0, 0] = 1  # 設置中心頻率點為 1（避免除零）。

        sintheta = pt.sin(theta)  # 計算角度的正弦值。
        costheta = pt.cos(theta)  # 計算角度的餘弦值。

        lp = self.lowpassfilter(rows, cols)  # 創建低通濾波器。
        lp = pt.cat(batch * [lp.unsqueeze(0)], 0)  # 將低通濾波器擴展到批次。

        term1 = pt.cat(rows * cols * [self.fo.unsqueeze(2)], dim=2).view(-1, self.nscale, rows, cols)  # 構建中心頻率項。
        term1 = pt.cat(batch * [term1.unsqueeze(0)], 0).view(-1, self.nscale, rows, cols)  # 擴展到批次。

        term2 = pt.log(pt.cat(self.nscale * [radius.unsqueeze(1)], 1) / term1)  # 計算 Log-Gabor 濾波器的徑向分量。
        logGabor = pt.exp(-pt.pow(term2, 2) / self.den)  # 計算 Log-Gabor 濾波器。
        logGabor = logGabor * lp  # 應用低通濾波器。
        logGabor[:, :, 0, 0] = 0  # 設置中心頻率點為 0。

        # 構建角度濾波器分量
        angl = pt.arange(0, self.norient, dtype=pt.float64) / self.norient * self.pi  # 計算方向角度。

        if self.cuda_computation:  # 若啟用 CUDA。
            angl = angl.cuda()  # 將角度移至 CUDA。

        ds_t1 = pt.cat(self.norient * [sintheta.unsqueeze(1)], 1) * pt.cos(angl).view(-1, self.norient, 1, 1)  # 正弦差分項 1。
        ds_t2 = pt.cat(self.norient * [costheta.unsqueeze(1)], 1) * pt.sin(angl).view(-1, self.norient, 1, 1)  # 正弦差分項 2。
        dc_t1 = pt.cat(self.norient * [costheta.unsqueeze(1)], 1) * pt.cos(angl).view(-1, self.norient, 1, 1)  # 餘弦差分項 1。
        dc_t2 = pt.cat(self.norient * [sintheta.unsqueeze(1)], 1) * pt.sin(angl).view(-1, self.norient, 1, 1)  # 餘弦差分項 2。
        ds = ds_t1 - ds_t2  # 正弦差分。
        dc = dc_t1 + dc_t2  # 餘弦差分。
        dtheta = pt.abs(pt.atan2(ds, dc))  # 計算角度距離。
        spread = pt.exp(-pt.pow(dtheta, 2) / (2 * self.thetaSigma ** 2))  # 計算角度濾波器分量。

        logGabor_rep = pt.repeat_interleave(logGabor, self.norient, 1).view(-1, self.nscale, self.norient, rows, cols)  # 重複 Log-Gabor 濾波器。

        spread_rep = pt.cat(self.nscale * [spread]).view(-1, self.nscale, self.norient, rows, cols)  # 重複角度濾波器。
        filter_log_spread = logGabor_rep * spread_rep  # 結合徑向和角度濾波器。
        array_of_zeros = pt.zeros(filter_log_spread.unsqueeze(5).size(), dtype=pt.float64)  # 創建零張量。
        if self.cuda_computation:  # 若啟用 CUDA。
            array_of_zeros = array_of_zeros.cuda()  # 將零張量移至 CUDA。
        filter_log_spread_zero = pt.cat((filter_log_spread.unsqueeze(5), array_of_zeros), dim=5)  # 添加零通道。
        ifftFilterArray = pt.ifft(filter_log_spread_zero, signal_ndim=2).select(5, 0) * math.sqrt(rows * cols)  # 計算濾波器的逆傅里葉變換。

        imagefft_repeat = pt.cat(self.nscale * self.norient * [imagefft], dim=1).view(-1, self.nscale, self.norient, rows, cols, 2)  # 重複圖像傅里葉變換。
        filter_log_spread_repeat = pt.cat(2 * [filter_log_spread.unsqueeze(5)], dim=5)  # 重複濾波器。
        EO = pt.ifft(filter_log_spread_repeat * imagefft_repeat, signal_ndim=2)  # 卷積操作（頻率域）。

        E = EO.select(5, 0)  # 提取偶數濾波結果。
        O = EO.select(5, 1)  # 提取奇數濾波結果。
        An = pt.sqrt(pt.pow(E, 2) + pt.pow(O, 2))  # 計算響應幅度。
        sumAn_ThisOrient = pt.sum(An, 1)  # 按尺度求和。
        sumE_ThisOrient = pt.sum(E, 1)  # 偶數濾波結果求和。
        sumO_ThisOrient = pt.sum(O, 1)  # 奇數濾波結果求和。

        XEnergy = pt.sqrt(pt.pow(sumE_ThisOrient, 2) + pt.pow(sumO_ThisOrient, 2)) + self.epsilon  # 計算加權平均能量。
        MeanE = sumE_ThisOrient / XEnergy  # 計算加權平均偶數響應。
        MeanO = sumO_ThisOrient / XEnergy  # 計算加權平均奇數響應。

        MeanO = pt.cat(self.nscale * [MeanO.unsqueeze(1)], 1)  # 擴展奇數響應。
        MeanE = pt.cat(self.nscale * [MeanE.unsqueeze(1)], 1)  # 擴展偶數響應。

        # 計算能量（相位一致性乘以幅度）
        Energy = pt.sum(E * MeanE + O * MeanO - pt.abs(E * MeanO - O * MeanE), 1)  # 計算能量。
        abs_EO = pt.sqrt(pt.pow(E, 2) + pt.pow(O, 2))  # 計算濾波響應幅度。

        # 估計噪聲功率
        medianE2n = pt.pow(abs_EO.select(1, 0), 2).view(-1, self.norient, rows * cols).median(2).values  # 計算最小尺度的中位能量。
        EM_n = pt.sum(pt.sum(pt.pow(filter_log_spread.select(1, 0), 2), 3), 2)  # 計算濾波器能量。
        noisePower = -(medianE2n / math.log(0.5)) / EM_n  # 估計噪聲功率。

        # 估計總噪聲能量
        EstSumAn2 = pt.sum(pt.pow(ifftFilterArray, 2), 1)  # 計算濾波器響應平方和。
        sumEstSumAn2 = pt.sum(pt.sum(EstSumAn2, 2), 2)  # 求和。
        roll_t1 = ifftFilterArray * self.roll_1(ifftFilterArray, 1)  # 計算滾動濾波器乘積。
        roll_t2 = ifftFilterArray * self.roll_1(ifftFilterArray, 2)  # 計算滾動濾波器乘積。
        roll_t3 = ifftFilterArray * self.roll_1(ifftFilterArray, 3)  # 計算滾動濾波器乘積。
        rolling_mult = roll_t1 + roll_t2 + roll_t3  # 結合滾動濾波器。
        EstSumAiAj = pt.sum(rolling_mult, 1) / 2  # 計算濾波器間交互項。
        sumEstSumAiAj = pt.sum(pt.sum(EstSumAiAj, 2), 2)  # 求和。

        EstNoiseEnergy2 = 2 * noisePower * sumEstSumAn2 + 4 * noisePower * sumEstSumAiAj  # 估計噪聲能量平方。
        tau = pt.sqrt(EstNoiseEnergy2 / 2)  # 計算噪聲閾值參數。
        EstNoiseEnergy = tau * math.sqrt(self.pi / 2)  # 估計噪聲能量。
        EstNoiseEnergySigma = pt.sqrt((2 - self.pi / 2) * pt.pow(tau, 2))  # 估計噪聲標準差。

        T = (EstNoiseEnergy + self.k * EstNoiseEnergySigma) / 1.7  # 計算噪聲閾值（經驗調整）。
        T_exp = pt.cat(rows * cols * [T.unsqueeze(2)], dim=2).view(-1, self.norient, rows, cols)  # 擴展閾值。
        AnAll = pt.sum(sumAn_ThisOrient, 1)  # 總幅度。
        array_of_zeros_energy = pt.zeros(Energy.size(), dtype=pt.float64)  # 創建零張量。
        if self.cuda_computation:  # 若啟用 CUDA。
            array_of_zeros_energy = array_of_zeros_energy.cuda()  # 將零張量移至 CUDA。

        EnergyAll = pt.sum(pt.where((Energy - T_exp) < 0.0, array_of_zeros_energy, Energy - T_exp), 1)  # 計算最終能量。
        ResultPC = EnergyAll / AnAll  # 計算相位一致性。

        return ResultPC

class FSIM(FSIM_base):  # 定義 FSIM 類（灰階版本）。
    """
    Note, the input is expected to be from 0 to 255
    """
    def __init__(self):  # 初始化方法。
        super().__init__()  # 調用父類初始化。

    def forward(self, imgr, imgd):  # 前向傳播。
        if imgr.is_cuda:  # 若輸入在 CUDA 上。
            self.set_arrays_to_cuda()  # 將內部張量移至 CUDA。

        I1, Q1, Y1 = self.process_image_channels(imgr)  # 處理參考圖像，提取 YIQ。
        I2, Q2, Y2 = self.process_image_channels(imgd)  # 處理待評估圖像，提取 YIQ。
        PC1 = self.phasecong2(Y1)  # 計算參考圖像的相位一致性。
        PC2 = self.phasecong2(Y2)  # 計算待評估圖像的相位一致性。

        PCSimMatrix, PCm = self.calculate_phase_score(PC1, PC2)  # 計算相位一致性相似度。
        gradientMap1 = self.calculate_gradient_map(Y1)  # 計算參考圖像梯度圖。
        gradientMap2 = self.calculate_gradient_map(Y2)  # 計算待評估圖像梯度圖。

        gradientSimMatrix = self.calculate_gradient_sim(gradientMap1, gradientMap2)  # 計算梯度相似度。
        gradientSimMatrix = gradientSimMatrix.view(PCSimMatrix.size())  # 調整形狀。
        FSIM = self.calculate_fsim(gradientSimMatrix, PCSimMatrix, PCm)  # 計算 FSIM 分數。

        return FSIM.mean()  # 返回平均 FSIM 分數。

class FSIMc(FSIM_base, nn.Module):  # 定義 FSIMc 類（彩色版本）。
    """
    Note, the input is expected to be from 0 to 255
    """
    def __init__(self):  # 初始化方法。
        super().__init__()  # 調用父類初始化。

    def forward(self, imgr, imgd):  # 前向傳播。
        if imgr.is_cuda:  # 若輸入在 CUDA 上。
            self.set_arrays_to_cuda()  # 將內部張量移至 CUDA。

        I1, Q1, Y1 = self.process_image_channels(imgr)  # 處理參考圖像，提取 YIQ。
        I2, Q2, Y2 = self.process_image_channels(imgd)  # 處理待評估圖像，提取 YIQ。
        PC1 = self.phasecong2(Y1)  # 計算參考圖像的相位一致性。
        PC2 = self.phasecong2(Y2)  # 計算待評估圖像的相位一致性。

        PCSimMatrix, PCm = self.calculate_phase_score(PC1, PC2)  # 計算相位一致性相似度。
        gradientMap1 = self.calculate_gradient_map(Y1)  # 計算參考圖像梯度圖。
        gradientMap2 = self.calculate_gradient_map(Y2)  # 計算待評估圖像梯度圖。

        gradientSimMatrix = self.calculate_gradient_sim(gradientMap1, gradientMap2)  # 計算梯度相似度。
        gradientSimMatrix = gradientSimMatrix.view(PCSimMatrix.size())  # 調整形狀。
        FSIMc = self.calculate_fsimc(I1.squeeze(), Q1.squeeze(), I2.squeeze(), Q2.squeeze(), gradientSimMatrix, PCSimMatrix, PCm)  # 計算 FSIMc 分數。

        return FSIMc.mean()  # 返回平均 FSIMc 分數。