# Flow-GUI

Flow-GUI 是一个基于 PyQt5 的图形界面工具，用于监控和管理 XMeta 工作流运行状态。

## 功能特点

- **运行状态监控**
  - 实时显示所有 target 的运行状态
  - 使用颜色编码直观展示不同状态（完成/失败/运行中等）
  - 支持按层级查看 target 依赖关系

- **多 Run 管理**
  - 支持在同一界面管理多个 run
  - 提供所有 run 的状态概览
  - 方便切换不同的 run 目录

- **操作便捷**
  - 右键菜单快速访问常用功能
    - Terminal：打开终端
    - csh：查看 shell 脚本
    - Log：查看日志文件
    - cmd：查看命令文件
    - Trace Up/Down：查看依赖关系

- **状态控制**
  - run/stop：运行/停止 target
  - skip/unskip：跳过/取消跳过 target
  - invalid：设置 target 为无效

## 使用要求

- Python 3.x
- PyQt5
- XMeta 环境

## 安装

1. 克隆仓库：
```bash
git clone https://github.com/a6987985/Flow-GUI.git
```

2. 安装依赖：
```bash
pip install PyQt5
```

## 使用方法

1. 在 XMeta 环境下运行：
```bash
python monitor.py
```

2. 界面说明：
   - 顶部下拉框：选择要监控的 run
   - 过滤框：快速查找特定 target
   - 按钮组：执行各种操作（run/stop/skip 等）
   - 树形视图：显示 target 状态和依赖关系

## 主要特性

- 实时状态更新
- 多 tab 页面管理
- 状态颜色编码
- 右键快捷操作
- target 依赖追踪
- 运行状态概览

## 贡献

欢迎提交 Issue 和 Pull Request。

## 许可

[MIT License](LICENSE)