# piper_tabletop_sim

独立的 Gazebo Harmonic 桌面抓取场景：**一条 AgileX PiPER 六轴臂 + 官方 70 mm 平行夹爪 + 一个 Intel RealSense D435i RGB-D 相机 + 一张桌面 + 一个 4 cm 木质方块**。

它**不依赖** `real_piper_yolo_graspnet`，也**不依赖** `ag_robot_description`；网格和参数是复制/裁剪进来的，可以单独 `colcon build`、单独运行。

## 1. 包含与不包含

包含：

- 1 条 PiPER 臂（官方质量/惯量/关节限位）
- 官方 70 mm 小夹爪（虚拟总开口关节 `gripper` 0..0.07 m，joint7/joint8 为 mimic 指爪）
- 1 个 D435i RGB-D 相机（848×480，官方深度内参）
- 1 张 0.82 × 0.68 m 桌面，顶面与机械臂基座同平面
- 1 个 0.04 m 木质立方体
- Gazebo Harmonic + `gz_ros2_control` + `joint_trajectory_controller`
- 最小 MoveIt 配置（arm / gripper 两组，OMPL + KDL）
- 抓取所需 RGB / Depth / CameraInfo 的 ROS 桥接（兼容话题和点云可选）

不包含：

- 底盘、轮子、升降、第二条臂、VLP-16、头盔
- YOLO / GraspNet / 真机 `grasp_executor` / `piper_sdk` 替身
- detachable joint / 自动吸附抓取
- 额外物体（只有那个 4 cm 木块）

## 2. 依赖与前置

本机已验证：Ubuntu 22.04、ROS 2 Humble、Gazebo Harmonic 8.15、`ros_gz_sim`/`ros_gz_bridge` 0.244.12、MoveIt Humble、ros2_control。

`gz_ros2_control` 可由系统包或源码 overlay 提供。若使用源码 overlay，运行前先加载其环境：

```bash
source /opt/ros/humble/setup.bash
source /path/to/gz_ros2_control_ws/install/setup.bash
```

否则 Gazebo 里模型能出现，但 `gz_ros2_control-system` 插件加载失败，控制器全部起不来（表现为没有 `/joint_states`）。

如果该 overlay 将来失效，可以安装 apt 包（需要 sudo）：

```bash
sudo apt install ros-humble-gz-ros2-control
```

## 3. 构建

```bash
source /opt/ros/humble/setup.bash
source /path/to/gz_ros2_control_ws/install/setup.bash  # 仅源码 overlay 需要
cd /path/to/piper_tabletop_sim_ws
colcon build --symlink-install
source install/setup.bash
```

## 4. 运行

只开仿真（Gazebo + 控制器 + 相机桥接）：

```bash
ros2 launch piper_tabletop_sim sim.launch.py
```

无界面：

```bash
ros2 launch piper_tabletop_sim sim.launch.py gazebo_gui:=false
```

仿真 + MoveIt + RViz：

```bash
ros2 launch piper_tabletop_sim bringup.launch.py
```

只开 MoveIt：

```bash
ros2 launch piper_tabletop_sim move_group.launch.py
```

关键 launch 参数：

| 参数 | 默认 | 含义 |
|---|---|---|
| `gazebo_gui` | `true` | `false` 时只跑 `gz sim -s` |
| `camera_pitch_offset` | `1.047197551` | D435i 下俯 60°；设为 `0.0` 恢复 ag_robot 原始水平姿态 |
| `start_rviz` | `true` | MoveIt 是否打开 RViz |
| `camera_update_rate` | `10` | RGB-D 相机更新频率，单位 Hz |
| `legacy_camera_topics` | `false` | 桥接旧版相机话题 |
| `bridge_point_cloud` | `false` | 桥接 ROS 点云 |

## 5. 场景与坐标系

- 世界根：`world`，固定。
- `base_footprint`：世界原点。
- `base_frame_link`：`z=0.2184858 m`，yaw `+90°`（AG 机器人底盘坐标）。
- 左臂安装：`base_frame_link` 下 `(0.187732, -0.249047, 0.332000)`，yaw `-90°`。
- 臂基座 `base_link` 的 z ≈ `0.5504858 m`。
- 桌面顶面：`z=0.5504858 m`，与臂基座同平面。
- 木块：`(0.62, 0.10, 0.5704858)`，边长 0.04 m，yaw 0.28 rad。
- 相机：`base_frame_link` 下 `(0.006445351, -0.211853207, 0.991065428)`，yaw `-90°`，默认再下俯 60°。

> 相机说明：ag_robot_description 的 D435i 在头部，是**水平导航视角**，无法看到与臂基座同高度的桌面。本包保留它的**位置、模型和内参**，把俯仰做成参数并默认 60° 下俯。设 `camera_pitch_offset:=0.0` 可以还原 ag_robot 的原始姿态，但那种姿态看不到桌面。

## 6. 官方机械臂与夹爪参数

PiPER 官方参数（AgileX PiPER 用户手册/产品页）：

| 项目 | 值 |
|---|---|
| 自由度 | 6 DOF |
| 额定负载 | 1.5 kg |
| 臂展/工作半径 | 626.75 mm |
| 臂重 | 4.2 kg |
| 重复定位精度 | ±0.1 mm |
| 夹爪开口 | 0–70 mm |
| 夹爪重量 | 500 g |
| 夹爪额定/最大夹持力 | 40 N / 50 N |

URDF 里的 link 质量/惯量/关节限位来自官方 `piper_description`（与 `ag_robot_description`、`agx_arm_urdf/piper` 同一组数值）。夹爪按官方 **70 mm 小夹爪**建模：

- `gripper`：虚拟总开口关节，prismatic，`0..0.07 m`，由控制器直接命令；
- `joint7`：prismatic，`0..0.035 m`，`mimic gripper × +0.5`；
- `joint8`：prismatic，`-0.035..0 m`，`mimic gripper × -0.5`；
- 总开口 = `gripper` 值 = `2 × joint7 = 0.07 m`；
- TCP：`link6` 沿 +Z `0.1358 m`（与真机项目常量一致）。

指爪保留官方视觉网格；Gazebo 和 MoveIt 的接触碰撞使用两块简化平面指垫（每块 20 × 40 × 12 mm），避免三角网格边角接触导致木块被横向弹开。Gazebo 为指垫设置 `mu=1.0`、木块表面设置 `mu=0.9`，桌面维持 `mu=0.4`；这些是仿真接触参数，并非真机夹持力测量。

> 为什么用虚拟 `gripper` 主关节：Gazebo 的 mimic 约束需要一个“主动关节”带动从关节。直接用 joint7 作为主动关节时，bullet-featherstone 下位置控制器无法让 joint7 动起来（实测 joint7 保持 0）；改成 `gripper` 主关节 + joint7/joint8 两个 mimic 指爪后，`gripper=0.07` 能稳定得到 `joint7=0.035`、`joint8=-0.035`。

木块质量 0.0416 kg，远低于 1.5 kg 额定负载。

## 7. 木块与桌面材质参数

网上工程均值（不是精确材料常数）：

| 参数 | 取值 | 说明 |
|---|---|---|
| 木材密度 | 650 kg/m³ | 常见木材约 600–700 kg/m³（12–15% 含水率） |
| 木块质量 | 0.0416 kg | `650 × 0.04³` |
| 木块惯量 | 1.11e-5 kg·m² | 均质立方体 `m·a²/6` |
| 木-木静摩擦 μ | 0.4 | 常见范围 0.3–0.5，取中值 |
| 木-木恢复系数 e | 0.4 | 常见范围 0.4–0.6，取偏保守值 |
| 桌面摩擦 μ | 0.4 | 层压板/木桌面近似 |
| 桌面恢复系数 e | 0.2 | 桌面吸能 |

参考来源：

- 木材密度分级（12–15% 含水率）：<https://mzv.gov.cz/public/fe/a3/68/134859_14884_ALLWOOD_Presentation_EN.pdf>
- 木-木摩擦系数表：<https://literature.hpcalc.org/community/sliderule-calculator-metrification.pdf>
- 木-木恢复系数实验数据：<https://garuda.kemdiktisaintek.go.id/documents/detail/1279122>
- PiPER 官方参数：<https://static.generation-robots.com/media/agilex-piper-user-manual.pdf>

## 8. 相机

- 型号：Intel RealSense D435i（单 RGBD 传感器，RGB 与 Depth 像素对齐）。
- 分辨率：848×480，默认 10 Hz（可用 `camera_update_rate` 调整）。
- 深度内参（来自 ag_robot_description 的 librealsense 参考设备）：
  - `fx=fy=418.2646789550781`
  - `cx=424.1576232910156`
  - `cy=238.23983764648438`
  - HFOV `1.5844149256643074 rad`
  - clip `0.28..10.0 m`

默认 ROS 话题（供抓取链使用）：

```text
/camera/camera/color/image_raw
/camera/camera/aligned_depth_to_color/image_raw
/camera/camera/color/camera_info
```

设置 `legacy_camera_topics:=true` 后还会提供旧版相机话题：

```text
/camera/color/image_raw
/camera/depth/image_raw
/camera/color/camera_info
/camera/depth/camera_info
```

设置 `bridge_point_cloud:=true` 后会提供 `/camera/depth/points`。

注意：仿真里 RGB 和 Depth 共用同一个 RGBD 传感器，因此 RGB 的视场/内参与真实 D435i 的彩色相机（约 70° HFOV）不同，深度内参是官方值。这样做的目的是保证 RGB-D 像素严格对齐，便于抓取感知。

## 9. 控制器与 MoveIt

Gazebo 控制器（`config/ros2_controllers.yaml`）：

- `joint_state_broadcaster`
- `arm_controller`：joint1..6
- `gripper_controller`：`gripper`（joint7/joint8 只做状态，由 mimic 驱动）

MoveIt（`config/piper.srdf`）：

- `arm`：`base_link → link6`
- `gripper`：单关节组 `gripper`（虚拟总开口关节）
- group_state：`zero`、`open`（gripper=0.07）、`close`（gripper=0）、`ready`

MoveIt 参数：

- `joint_limits.yaml` 沿用真机项目的 joint6 ±1.7453 rad（线缆保护），其余关节官方限位。
- KDL 运动学，OMPL RRTConnect。
- `moveit_manage_controllers: false`，控制器由 launch 自己 spawn。

## 10. 验证

```bash
# 终端 A
source /opt/ros/humble/setup.bash
source /path/to/gz_ros2_control_ws/install/setup.bash  # 仅源码 overlay 需要
source /path/to/piper_tabletop_sim_ws/install/setup.bash
ros2 launch piper_tabletop_sim sim.launch.py gazebo_gui:=false
```

```bash
# 终端 B
ros2 topic list | grep -E "joint_states|camera"
ros2 topic echo /joint_states --once
ros2 topic hz /camera/camera/color/image_raw
ros2 topic hz /camera/camera/aligned_depth_to_color/image_raw
ros2 control list_controllers
```

预期：

- `/joint_states` 含 `joint1..joint6`、`gripper`、`joint7`、`joint8`；
- `/camera/color/image_raw`、`/camera/depth/image_raw`、`/camera/depth/points` 有数据；
- `joint_state_broadcaster`、`arm_controller`、`gripper_controller` 都是 `active`。

已实测（2026-10-25，headless）：

- 三个控制器均 `active`。
- 夹爪命令 `gripper=0.07` → `joint7=0.035`、`joint8=-0.035`；`gripper=0` → 两指回到 0。
- 彩色/深度/点云都有数据；深度图有效距离约 `0.63..2.08 m`，画面中能看到桌面和 4 cm 木块。
- MoveIt 的 `/move_action`、`/compute_fk`、`/compute_ik`、`/compute_cartesian_path` 均可用。
- 对木块做**侧向接近**的抓取位姿（tool +Z 水平/略下俯 15°）`/compute_ik` 有解，plan-only 返回
  `error_code=1` 且 `planned_trajectory` 非空。
- **正上方垂直下抓**（tool +Z 竖直向下）在当前臂基座/桌面布局下 `compute_ik` 返回
  `-31 (NO_IK_SOLUTION)`，换 yaw、换高度、换种子都不行。原因见第 11 节。

> 手动发夹爪命令时注意发现时序：刚启动就 `ros2 topic pub --once` 可能还没匹配到订阅者，
> 消息会丢。建议发 2–3 次，或用 action：
>
> ```bash
> ros2 topic pub --times 3 --rate 2 /gripper_controller/joint_trajectory \
>   trajectory_msgs/msg/JointTrajectory \
>   "{joint_names: [gripper], points: [{positions: [0.07], time_from_start: {sec: 2, nanosec: 0}}]}"
> ```
>
> 也可以用 `/gripper_controller/follow_joint_trajectory` action。

MoveIt：

```bash
ros2 launch piper_tabletop_sim move_group.launch.py
```

检查 `/move_action`、`/compute_fk`、`/compute_cartesian_path`，在 RViz 里对木块做 plan-only。当前建议用侧向/15° 下俯的候选，不要用纯垂直下抓。

## 11. 已知限制

- 仿真通过 `real_piper_yolo_graspnet` 的 YOLO、GraspNet 与 `grasp_executor` 接入抓取链；夹爪由 `gripper_controller` 控制。
- 相机俯仰 60° 是桌面演示覆盖，不是 ag_robot 原始导航姿态。
- 桌面顶面高度为 0.5504858 m；改变桌面高度需同步核对相机、手眼与 MoveIt 碰撞体。
- **垂直下抓不可达**：当前臂基座与桌面同平面、木块只比基座高 2.25 cm，PiPER 的腕部在
  “tool +Z 竖直向下”时无法到达木块上方（`compute_ik` 返回 -31）。实测**水平或下俯 15°
  的侧向接近**有解。若必须垂直下抓，需要把臂基座抬高（例如加一个 10–20 cm 的安装柱）
  或把桌面/木块相对臂基座降低，然后重新验证可达性。
- 木块摩擦/恢复系数是工程均值，仿真里是否完全按 bullet-featherstone 的接触模型生效需要实际观察。
- 没有做真实 D435i 的 Color→Depth 15 mm 基线；仿真 RGBD 是像素对齐的简化模型。
- 相机支架是 visual-only（无碰撞），因为机械臂零位会折到桌后，实体支架会挡住腕部。

## 12. 许可证与归属

- 本包代码/配置：Apache-2.0。
- 机械臂网格与官方参数来自 AgileX `agx_arm_urdf/piper`，并经 `ag_robot_description`（MIT）转引。
- Gazebo 场景、launch 结构参考 `piper_lightweight_sim`（Apache-2.0）。
- D435i 网格与内外参来自 `ag_robot_description`（MIT）。

详见 `NOTICE`。

## 13. 木块 YOLO 模型

仓库根目录的 `models/wood_block_yolov8s_seg.onnx` 是 Agent 抓取链使用的木块识别模型。
训练数据、训练脚本和 PyTorch 权重不属于仿真运行包，未纳入本仓库。
实际推理节点由外部的 `real_piper_yolo_graspnet` 工作区提供。
