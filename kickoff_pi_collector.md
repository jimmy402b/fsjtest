# New Session Kickoff Prompt — Pi Zero 2W 实验室数据采集器

复制以下内容到新会话（工作目录 `Z:\Code_in_raspi`）：

---

我正在开始一个新项目：**树莓派 Zero 2W 上的实验室数据采集器**。

## 背景

这是一个考古 3D 测量系统的数据采集端。Pi Zero 2W 作为手持设备的采集核心，在实验室环境下（无 GNSS 信号）采集激光测距、相机照片和 Vive Tracker 位姿数据，存储到 SD 卡，事后手动导入 PC 供 Archaeo3D（`Z:\GameDev`，一个 C++/Qt5 3D 可视化系统）消费。

## 硬件

| 模块 | 连接方式 | 说明 |
|------|----------|------|
| 树莓派 Zero 2W | — | UPS 电池通过 GPIO 供电（已验证OK），刚刷好系统 |
| MyAntenna L1s-40 激光测距模块 | UART TTL 3.3V，接 GPIO14/15，EN→GPIO17 | 量程 0.03~40m，精度±1mm，38400bps |
| CSI 相机 | 22-pin mini CSI 软排线 | — |
| Vive Tracker | micro-USB 接入 OTG 口 | libsurvive 已验证可在 Zero 2W 上运行 |

## L1s 激光模块协议

手册位于 `C22467668_传感器模块_L1S-40_规格书_WJ1189103.PDF`（25 页）。

- 通信协议：ASCII（默认），支持 Modbus RTU / Custom HEX
- 单次测距：发送 `iSM\r\n` → 响应 `D=Xm,N#\r\n`（距离米, 回光量）
- 连续测距：`iACM\r\n` / `iFACM\r\n`
- 错误响应：`E=Y\r\n`（错误码见附录）

## 数据流

```
Pi Zero 2W 采集循环:
  ├─ 触发激光测距 → 解析距离值
  ├─ 触发相机拍照 → 保存 JPG
  └─ 读取 Tracker 位姿 → 6-DOF (x,y,z,qw,qx,qy,qz)
         ↓
   写入 SQLite + 照片文件 → SD 卡
         ↓ 手动搬运到 PC
   Archaeo3D 导入消费
```

## 关键约束

- **Zero 2W 性能受限**（512MB RAM），只做采集和存储，不做重计算
- **不涉及 GNSS/RTK/PPK** — 这是实验室环境，没有 Reach M+
- **不需要 lhgeo**（`Z:\location`）— 那是 GNSS 标定管线，和这里无关
- Pi 端的依赖尽量轻：Python stdlib（`serial`、`sqlite3`）+ Picamera2 + libsurvive Python 绑定
- 采集的数据最终要能被 Archaeo3D 消费：Archaeo3D 的数据模型见 `Z:\GameDev\src\core\data_model.h`（ExcavationUnit、Artifact、LighthousePose）

## 你现在的任务

1. 先读取 `C22467668_传感器模块_L1S-40_规格书_WJ1189103.PDF` 完整理解 L1s 协议
2. 浏览 `Z:\GameDev\src\core\data_model.h` 和 `Z:\GameDev\src\camera\lighthouse_pose_loader.cpp` 了解 Archaeo3D 期望的数据格式
3. 用 brainstorming 技能设计这个新项目的架构，然后实现

注意：`Z:\location` 下的 `.claude` 记忆文件中有两个相关项目的上下文，可以忽略——这是全新项目，不要受 lhgeo 的设计约束。
