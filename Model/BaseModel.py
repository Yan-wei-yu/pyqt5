# 此檔案實作 BaseModel 類別，作為牙科數位建模系統的基底類別，主要功能包含：

# ✔ 管理上顎與下顎 STL 模型檔案（載入、渲染、旋轉）
# ✔ 設定輸出資料夾並產生深度圖（包括咬合面或單顎）
# ✔ 控制 PyQt 與 VTK 的渲染同步，支援 UI 即時更新
# ✔ 進行前處理（例如填充白色背景、影像邊界處理）
# ✔ 重置模型狀態（方便切換病例或重新處理）
from PyQt5.QtCore import QObject
import os
from Otherfunction import readmodel, pictureedgblack, fillwhite, trianglegoodobbox  # 匯入外部模組

class BaseModel(QObject):
    """
    BaseModel 是牙科數位化應用中的核心基底類別，提供以下功能：
    1. 載入上下顎模型並渲染至 VTK 視窗。
    2. 支援模型旋轉、透明度調整。
    3. 將場景輸出為深度圖 (256x256)。
    4. 提供輸出資料夾設定與模型重置。
    """

    def __init__(self):
        super().__init__()  # 初始化 QObject，支援 PyQt 訊號

    # ------------------------------
    # 資料夾與檔案設定
    # ------------------------------
    def set_upper_folder(self, folder_path):
        """設定上顎 STL 模型資料夾，並取得檔案清單"""
        self.upper_folder = folder_path
        if os.path.isdir(folder_path):
            self.upper_files = self._get_files_in_folder(folder_path)
            self.model_updated.emit()  # 通知 UI 更新
            return True
        return False

    def set_lower_folder(self, folder_path):
        """設定下顎 STL 模型資料夾，並取得檔案清單"""
        self.lower_folder = folder_path
        if os.path.isdir(folder_path):
            self.lower_files = self._get_files_in_folder(folder_path)
            self.model_updated.emit()
            return True
        return False

    def _get_files_in_folder(self, folder_path):
        """回傳資料夾內的檔案清單"""
        return [f for f in os.listdir(folder_path) if os.path.isfile(os.path.join(folder_path, f))]

    # ------------------------------
    # 模型旋轉
    # ------------------------------
    def set_model_angle(self, angle):
        """
        設定模型旋轉角度：
        - 若有上下顎，兩者同步旋轉。
        - 若僅有下顎，單獨旋轉。
        """
        self.angle = angle
        if not hasattr(self, 'lower_actor'):
            self.model_updated.emit()
            return

        if hasattr(self, 'upper_actor') and self.lower_actor:
            # 同時旋轉上下顎
            readmodel.rotate_actor(self.upper_actor, self.models_center, self.angle)
            readmodel.rotate_actor(self.lower_actor, self.models_center, self.angle)
        else:
            # 僅旋轉下顎
            self.lower_center = readmodel.calculate_center(self.lower_actor)
            readmodel.rotate_actor(self.lower_actor, self.lower_center, self.angle)
            self.lower_center = readmodel.calculate_center(self.lower_actor)
        self.model_updated.emit()

    # ------------------------------
    # 模型渲染
    # ------------------------------
    def render_model(self, renderer):
        """將已載入的模型渲染至 VTK 視窗"""
        renderer.RemoveAllViewProps()

        # 渲染上顎
        if hasattr(self, 'upper_file') and self.upper_file != '':
            self.model1 = readmodel.load_3d_model(self.upper_file)
            self.upper_actor = readmodel.create_actor(self.model1, (0.98, 0.98, 0.92))
            self._apply_actor_style(self.upper_actor, self.upper_opacity)
            self.upper_center = readmodel.calculate_center(self.upper_actor)
            renderer.AddActor(self.upper_actor)

        # 渲染下顎
        if hasattr(self, 'lower_file') and self.lower_file:
            self.model2 = readmodel.load_3d_model(self.lower_file)
            self.lower_actor = readmodel.create_actor(self.model2, (0.98, 0.98, 0.92))
            self._apply_actor_style(self.lower_actor, self.lower_opacity)
            renderer.AddActor(self.lower_actor)

        # 如果同時載入上下顎，計算模型中心
        if hasattr(self, 'lower_actor') and hasattr(self, 'upper_actor'):
            self.models_center = readmodel.twomodel_bound(
                self.lower_actor.GetBounds(),
                self.upper_actor.GetBounds()
            )

        renderer.ResetCamera()
        renderer.GetRenderWindow().Render()

    def _apply_actor_style(self, actor, opacity):
        """統一設定模型材質與光照效果"""
        prop = actor.GetProperty()
        prop.SetOpacity(opacity)
        prop.SetSpecular(0.5)  # 高光
        prop.SetSpecularPower(20)
        prop.SetDiffuse(0.6)
        prop.SetAmbient(0.3)

    # ------------------------------
    # 輸出深度圖
    # ------------------------------
    def save_depth_map(self, renderer):
        """將當前模型場景輸出為 256x256 深度圖"""
        renderer.GetRenderWindow().SetSize(256, 256)

        if self.lower_actor and self.output_folder:
            upper_file_cleaned = self.lower_file.strip("' ").strip()
            base_name = os.path.splitext(os.path.basename(upper_file_cleaned))[0]
            output_file_path = self.output_folder + '/' + base_name + ".png"

            # 根據透明度決定處理方式
            if self.upper_opacity == 0:  # 只顯示下顎
                if hasattr(self, 'upper_actor'):
                    self.upper_actor.GetProperty().SetOpacity(self.upper_opacity)
                scale_filter = readmodel.setup_camera(renderer, renderer.GetRenderWindow(),
                                                      None, self.lower_actor, self.upper_opacity, self.angle)
                readmodel.save_depth_image(output_file_path, scale_filter)
                bound_image = pictureedgblack.get_image_bound(output_file_path)
                fillwhite.process_image_pair(bound_image, output_file_path, output_file_path)

            elif self.upper_opacity == 1:  # 顯示上下顎
                self.upper_actor.GetProperty().SetOpacity(self.upper_opacity)
                self.lower_actor.GetProperty().SetOpacity(self.lower_opacity)
                scale_filter = readmodel.setup_camera(renderer, renderer.GetRenderWindow(),
                                                      self.upper_center, self.lower_actor, self.upper_opacity, self.angle)
                readmodel.save_depth_image(output_file_path, scale_filter)

            renderer.GetRenderWindow().SetSize(768, 768)
            return output_file_path
        else:
            print("Output folder not set")
        return None

    def combine_three_depth(self, renderer, base_name):
        """輸出多張深度圖，包含上下顎或單顎"""
        renderer.GetRenderWindow().SetSize(256, 256)
        if self.upper_opacity == 1:
            output_file_path = f"{self.output_folder}/{base_name}.png"
            self.upper_center = readmodel.calculate_center(self.upper_actor)
            scale_filter = readmodel.setup_camera(renderer, renderer.GetRenderWindow(),
                                                  self.upper_center, self.lower_actor, self.upper_opacity, self.angle)
        else:
            output_file_path = f"{self.output_folder}/{base_name}down.png"
            scale_filter = readmodel.setup_camera(renderer, renderer.GetRenderWindow(),
                                                  None, self.lower_actor, self.upper_opacity, self.angle)

        readmodel.save_depth_image(output_file_path, scale_filter)
        bound_image = pictureedgblack.get_image_bound(output_file_path)
        fillwhite.process_image_pair(bound_image, output_file_path, output_file_path)
        return output_file_path

    def set_output_folder(self, folder_path):
        """設定輸出結果的資料夾"""
        if os.path.isdir(folder_path):
            self.output_folder = folder_path
            self.model_updated.emit()
            return True
        return False

    def reset(self, renderer):
        """重置模型與相機狀態"""
        self.upper_file = ""
        self.lower_file = ""
        self.upper_center = None
        self.lower_center = None
        self.models_center = None

        if hasattr(self, 'upper_actor'):
            del self.upper_actor
        if hasattr(self, 'lower_actor'):
            del self.lower_actor

        # 重置相機
        camera = renderer.GetActiveCamera()
        camera.SetPosition(0, 0, 1)
        camera.SetFocalPoint(0, 0, 0)
        camera.SetViewUp(0, 1, 0)

        self.model_updated.emit()
