# PiPER 桌面抓取仿真工作区

本仓库保存可独立启动的 ROS 2 / Gazebo Harmonic 桌面仿真包，以及 Agent 抓取流程所需的仿真辅助文件。仿真包位于 [`src/piper_tabletop_sim`](src/piper_tabletop_sim)，场景包含一条 PiPER 臂、70 mm 夹爪、D435i RGB-D 相机、桌子和 40 mm 木块。

## 提交内容

| 路径 | 用途 |
| --- | --- |
| `src/piper_tabletop_sim/` | Gazebo 场景、机器人 URDF、网格、控制器和 MoveIt 配置 |
| `sim_support/` | MoveIt 桌面碰撞体和关节反馈中继；Agent 使用这两个脚本 |
| `config/handeye_sim.yaml` | 仿真相机到机械臂基座的变换；仅用于仿真 |
| `models/wood_block_yolov8s_seg.onnx` | 木块识别模型，约 45 MiB；Gazebo 本身不需要它，Agent 抓取需要 |

`build/`、`install/`、`log/`、训练运行记录、数据集和 PyTorch 权重不纳入版本库。ONNX 模型的 SHA-256 为 `42899816f98d63d71067aff9d3bd910b144b08c212a3e452f3306478a9209186`。

## 构建和启动

环境：Ubuntu 22.04、ROS 2 Humble、Gazebo Harmonic、`ros_gz_sim`、`ros_gz_bridge`、`gz_ros2_control`、MoveIt 2 和 colcon。`gz_ros2_control` 可由系统包或已构建的 overlay 提供。

```bash
source /opt/ros/humble/setup.bash
# 如果 gz_ros2_control 来自源码 overlay，先 source 它的 install/setup.bash
cd /path/to/piper_tabletop_sim_ws
colcon build --symlink-install
source install/setup.bash
export ROS_DOMAIN_ID=67 GZ_PARTITION=tabletop67
ros2 launch piper_tabletop_sim sim.launch.py gazebo_gui:=true
```

另一个终端可启动 MoveIt：

```bash
source /opt/ros/humble/setup.bash
source /path/to/piper_tabletop_sim_ws/install/setup.bash
export ROS_DOMAIN_ID=67 GZ_PARTITION=tabletop67
ros2 launch piper_tabletop_sim move_group.launch.py start_rviz:=false
```

默认相机为 848×480、10 Hz。抓取流程使用 `/camera/camera/color/image_raw` 和 `/camera/camera/aligned_depth_to_color/image_raw`。若旧程序需要其他相机话题，可设置 `legacy_camera_topics:=true`；需要 ROS 点云时设置 `bridge_point_cloud:=true`。完整场景参数、坐标系和已知限制见[仿真包说明](src/piper_tabletop_sim/README.md)。

## Agent 抓取集成边界

本仓库提供仿真环境与木块模型。完整的 Agent 控制抓取还依赖**另两个工作区**：`real_piper_yolo_graspnet` 提供 YOLO 桥接、GraspNet Docker 推理及抓取执行器；`ag_robot_agent` 提供任务编排、候选筛选和仿真专用参数。克隆本仓库后需分别配置这两个工作区，并根据本机目录修改 Agent 配置。仅构建本仓库不会启动 Agent 或 GraspNet。

当前仿真使用已知木块尺寸、朝向及仿真手眼参数。它能验证软件闭环，不代表真机成功率。网格和派生材料的归属见 [`NOTICE`](src/piper_tabletop_sim/NOTICE)。
