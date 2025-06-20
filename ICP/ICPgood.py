import open3d as o3d  # Open3D 庫，用於 3D 數據處理和點雲配準
import numpy as np  # NumPy 庫，用於數學運算和陣列處理

class MultiwayRegistration:
    # 初始化函數，設置點雲配準參數
    def __init__(self, voxel_size=0.0002, max_corr_dist_coarse=30, max_corr_dist_fine=0.05):
        self.voxel_size = voxel_size  # 體素降採樣大小，控制點雲密度
        self.max_corr_dist_coarse = max_corr_dist_coarse  # 粗配準的最大對應距離
        self.max_corr_dist_fine = max_corr_dist_fine  # 精細配準的最大對應距離

    # 加載並降採樣點雲
    def load_point_clouds(self, pointlist):
        """
        將點雲列表降採樣並返回。
        參數:
            pointlist: 點雲對象列表
        返回:
            降採樣後的點雲列表
        """
        pcds = []
        for point in pointlist:
            pcd_down = point.voxel_down_sample(voxel_size=self.voxel_size)  # 降採樣點雲
            pcds.append(pcd_down)
        return pcds

    # 成對點雲配準（使用 ICP 算法）
    def pairwise_registration(self, source, target):
        """
        對源點雲和目標點雲進行點到平面的 ICP 配準。
        參數:
            source: 源點雲
            target: 目標點雲
        返回:
            轉換矩陣和信息矩陣
        """
        print("Apply point-to-plane ICP")  # 提示執行點到平面 ICP
        # 粗配準
        icp_coarse = o3d.pipelines.registration.registration_icp(
            source, target, self.max_corr_dist_coarse, np.identity(4),  # 初始單位矩陣
            o3d.pipelines.registration.TransformationEstimationPointToPlane())
        # 精細配準，使用粗配準結果作為初始值
        icp_fine = o3d.pipelines.registration.registration_icp(
            source, target, self.max_corr_dist_fine, icp_coarse.transformation,
            o3d.pipelines.registration.TransformationEstimationPointToPlane())
        transformation_icp = icp_fine.transformation  # 最終轉換矩陣
        # 獲取信息矩陣，用於後續優化
        information_icp = o3d.pipelines.registration.get_information_matrix_from_point_clouds(
            source, target, self.max_corr_dist_fine, icp_fine.transformation)
        return transformation_icp, information_icp

    # 完整配準，構建姿態圖
    def full_registration(self, pcds):
        """
        對多個點雲進行配準，構建姿態圖。
        參數:
            pcds: 點雲列表
        返回:
            姿態圖對象
        """
        pose_graph = o3d.pipelines.registration.PoseGraph()  # 創建姿態圖
        odometry = np.identity(4)  # 初始里程計為單位矩陣
        pose_graph.nodes.append(o3d.pipelines.registration.PoseGraphNode(odometry))  # 添加初始節點
        n_pcds = len(pcds)
        # 遍歷所有點雲對進行配準
        for source_id in range(n_pcds):
            for target_id in range(source_id + 1, n_pcds):
                transformation_icp, information_icp = self.pairwise_registration(
                    pcds[source_id], pcds[target_id])  # 成對配準
                print("Build PoseGraph")  # 提示構建姿態圖
                if target_id == source_id + 1:  # 如果是連續點雲
                    odometry = np.dot(transformation_icp, odometry)  # 更新里程計
                    pose_graph.nodes.append(
                        o3d.pipelines.registration.PoseGraphNode(np.linalg.inv(odometry)))  # 添加新節點
                    pose_graph.edges.append(
                        o3d.pipelines.registration.PoseGraphEdge(source_id, target_id,
                                                                 transformation_icp, information_icp,
                                                                 uncertain=False))  # 添加確定邊
                else:  # 非連續點雲
                    pose_graph.edges.append(
                        o3d.pipelines.registration.PoseGraphEdge(source_id, target_id,
                                                                 transformation_icp, information_icp,
                                                                 uncertain=True))  # 添加不確定邊
        return pose_graph

    # 繞 Y 軸旋轉點雲
    def rotate_around_y_axis(self, pcd, rotation_angle):
        """
        繞 Y 軸旋轉點雲。
        參數:
            pcd: 點雲對象
            rotation_angle: 旋轉角度（弧度）
        返回:
            旋轉後的點雲
        """
        center = np.mean(np.asarray(pcd.points), axis=0)  # 計算點雲中心
        pcd.translate(-center)  # 平移至原點
        axis = np.array([0, 1, 0])  # Y 軸方向
        rotation_vector = axis * rotation_angle  # 旋轉向量
        rotation_matrix = o3d.geometry.get_rotation_matrix_from_axis_angle(rotation_vector)  # 旋轉矩陣
        pcd.rotate(rotation_matrix, center=(0, 0, 0))  # 執行旋轉
        return pcd

    # 執行多路配準
    def run_registration(self, mesh_target, mesh_source, mesh_third):
        """
        執行三個網格的多路配準。
        參數:
            mesh_target: 目標網格文件路徑
            mesh_source: 源網格文件路徑
            mesh_third: 第三個網格文件路徑
        返回:
            合併後的點雲
        """
        # 讀取三個網格並設定顏色
        mesh1 = o3d.io.read_triangle_mesh(mesh_target)  # 目標網格
        mesh2 = o3d.io.read_triangle_mesh(mesh_source)  # 源網格
        mesh3 = o3d.io.read_triangle_mesh(mesh_third)  # 第三個網格
        mesh1.paint_uniform_color([1, 0.706, 0])  # 橙色
        mesh2.paint_uniform_color([0, 0.706, 1])  # 青色
        mesh3.paint_uniform_color([0, 1, 0])      # 綠色

        # 轉換為點雲並提取頂點
        source = o3d.geometry.PointCloud()
        target = o3d.geometry.PointCloud()
        third = o3d.geometry.PointCloud()
        target.points = o3d.utility.Vector3dVector(np.array(mesh1.vertices))
        source.points = o3d.utility.Vector3dVector(np.array(mesh2.vertices))
        third.points = o3d.utility.Vector3dVector(np.array(mesh3.vertices))

        # 旋轉點雲
        rotation_angle = -np.pi / 2  # 旋轉 -90 度
        source = self.rotate_around_y_axis(source, rotation_angle)  # 源點雲旋轉
        third = self.rotate_around_y_axis(third, -rotation_angle)   # 第三點雲旋轉 90 度

        # 平移調整
        target.translate(-np.mean(np.asarray(target.points), axis=0))  # 目標點雲移至原點
        source.translate(np.array([-5, 0, -2]))  # 源點雲平移
        third.translate(np.array([5, 0, -2]))    # 第三點雲平移

        # 估計法向量
        search_param = o3d.geometry.KDTreeSearchParamHybrid(radius=20, max_nn=40)  # 搜索參數
        source.estimate_normals(search_param=search_param)
        target.estimate_normals(search_param=search_param)
        third.estimate_normals(search_param=search_param)

        # 設定點雲顏色
        target.paint_uniform_color([0, 1, 0])  # 綠色
        source.paint_uniform_color([1, 0, 0])  # 紅色
        third.paint_uniform_color([0, 0, 1])   # 藍色

        # 第一次配準（source 與 target）
        pcds_down = self.load_point_clouds([source, target])  # 降採樣點雲
        with o3d.utility.VerbosityContextManager(o3d.utility.VerbosityLevel.Debug):  # 啟用調試信息
            pose_graph = self.full_registration(pcds_down)  # 構建姿態圖

        print("Optimizing PoseGraph ...")  # 提示優化姿態圖
        option = o3d.pipelines.registration.GlobalOptimizationOption(
            max_correspondence_distance=self.max_corr_dist_fine,
            edge_prune_threshold=0.1,
            reference_node=0)  # 全局優化選項
        with o3d.utility.VerbosityContextManager(o3d.utility.VerbosityLevel.Debug):
            o3d.pipelines.registration.global_optimization(
                pose_graph,
                o3d.pipelines.registration.GlobalOptimizationLevenbergMarquardt(),  # 優化方法
                o3d.pipelines.registration.GlobalOptimizationConvergenceCriteria(),  # 收斂標準
                option)

        # 轉換並合併點雲
        pcds = self.load_point_clouds([source, target])
        pcd_combined = o3d.geometry.PointCloud()
        for point_id in range(len(pcds)):
            pcds[point_id].transform(pose_graph.nodes[point_id].pose)  # 應用轉換
            pcd_combined += pcds[point_id]  # 合併點雲
        pcd_combined.translate(-np.mean(np.asarray(pcd_combined.points), axis=0))  # 移至原點
        pcd_combined.estimate_normals(search_param=search_param)  # 估計法向量

        # 第二次配準（third 與 pcd_combined）
        pcds_down1 = self.load_point_clouds([third, pcd_combined])
        with o3d.utility.VerbosityContextManager(o3d.utility.VerbosityLevel.Debug):
            pose_graph1 = self.full_registration(pcds_down1)

        print("Optimizing PoseGraph1 ...")
        option1 = o3d.pipelines.registration.GlobalOptimizationOption(
            max_correspondence_distance=self.max_corr_dist_fine,
            edge_prune_threshold=0.1,
            reference_node=0)
        with o3d.utility.VerbosityContextManager(o3d.utility.VerbosityLevel.Debug):
            o3d.pipelines.registration.global_optimization(
                pose_graph1,
                o3d.pipelines.registration.GlobalOptimizationLevenbergMarquardt(),
                o3d.pipelines.registration.GlobalOptimizationConvergenceCriteria(),
                option1)

        # 最終合併
        pcds1 = self.load_point_clouds([third, pcd_combined])
        pcd_combined1 = o3d.geometry.PointCloud()
        for point_id in range(len(pcds1)):
            pcds1[point_id].transform(pose_graph1.nodes[point_id].pose)
            pcd_combined1 += pcds1[point_id]

        return pcd_combined1  # 返回最終合併的點雲
    def run_registration_sec(self, mesh_target, mesh_source):
        """
        執行三個網格的多路配準。
        參數:
            mesh_target: 目標網格文件路徑
            mesh_source: 源網格文件路徑
            mesh_third: 第三個網格文件路徑
        返回:
            合併後的點雲
        """
        # 讀取三個網格並設定顏色
        mesh1 = o3d.io.read_triangle_mesh(mesh_target)  # 目標網格
        mesh2 = o3d.io.read_triangle_mesh(mesh_source)  # 源網格
        mesh1.paint_uniform_color([1, 0.706, 0])  # 橙色
        mesh2.paint_uniform_color([0, 0.706, 1])  # 青色

        # 轉換為點雲並提取頂點
        source = o3d.geometry.PointCloud()
        target = o3d.geometry.PointCloud()
        target.points = o3d.utility.Vector3dVector(np.array(mesh1.vertices))
        source.points = o3d.utility.Vector3dVector(np.array(mesh2.vertices))

        # 旋轉點雲
        rotation_angle = -np.pi / 2  # 旋轉 -90 度
        source = self.rotate_around_y_axis(source, -rotation_angle)  # 源點雲旋轉

        # 平移調整
        target.translate(-np.mean(np.asarray(target.points), axis=0))  # 目標點雲移至原點
        source.translate(np.array([5, 0, 0]))  # 源點雲平移
        # third.translate(np.array([5, 0, -2]))    # 第三點雲平移

        # 估計法向量
        search_param = o3d.geometry.KDTreeSearchParamHybrid(radius=20, max_nn=40)  # 搜索參數
        source.estimate_normals(search_param=search_param)
        target.estimate_normals(search_param=search_param)

        # 設定點雲顏色
        target.paint_uniform_color([0, 1, 0])  # 綠色
        source.paint_uniform_color([1, 0, 0])  # 紅色

        # 第一次配準（source 與 target）
        pcds_down = self.load_point_clouds([source, target])  # 降採樣點雲
        with o3d.utility.VerbosityContextManager(o3d.utility.VerbosityLevel.Debug):  # 啟用調試信息
            pose_graph = self.full_registration(pcds_down)  # 構建姿態圖

        print("Optimizing PoseGraph ...")  # 提示優化姿態圖
        option = o3d.pipelines.registration.GlobalOptimizationOption(
            max_correspondence_distance=self.max_corr_dist_fine,
            edge_prune_threshold=0.1,
            reference_node=0)  # 全局優化選項
        with o3d.utility.VerbosityContextManager(o3d.utility.VerbosityLevel.Debug):
            o3d.pipelines.registration.global_optimization(
                pose_graph,
                o3d.pipelines.registration.GlobalOptimizationLevenbergMarquardt(),  # 優化方法
                o3d.pipelines.registration.GlobalOptimizationConvergenceCriteria(),  # 收斂標準
                option)

        # 轉換並合併點雲
        pcds = self.load_point_clouds([source, target])
        pcd_combined = o3d.geometry.PointCloud()
        for point_id in range(len(pcds)):
            pcds[point_id].transform(pose_graph.nodes[point_id].pose)  # 應用轉換
            pcd_combined += pcds[point_id]  # 合併點雲
        pcd_combined.translate(-np.mean(np.asarray(pcd_combined.points), axis=0))  # 移至原點
        pcd_combined.estimate_normals(search_param=search_param)  # 估計法向量


        return pcd_combined  # 返回最終合併的點雲


# # 使用範例：
# if __name__ == "__main__":
#     # 替換成你實際的 STL 檔案路徑
#     mesh_paths = [
#         "./0005/rebbox/redata0005bbox.stl",
#         "./0005/rebbox/redata0005bbox-90.stl",
#         "./0005/rebbox/redata0005bbox--90.stl"
#     ]
#     reg = MultiwayRegistration()
#     result = reg.run_registration(mesh_paths[0], mesh_paths[1], mesh_paths[2])
