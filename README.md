# Flow-GUI

一个用于物理设计PR流程的图形界面工具。

## 功能特点

- 实时监控PR运行状态
- 支持多目标并行显示
- 树形结构展示依赖关系
- 支持搜索和过滤功能
- 支持目标状态追踪
- 集成终端操作功能

## 系统要求

- Python 3.6+
- PyQt5
- Unix/Linux操作系统

## 安装说明

1. 克隆仓库:
```bash
git clone https://github.com/a6987985/Flow-GUI.git
cd Flow-GUI
```

2. 安装依赖:
```bash
pip install -r requirements.txt
```

## 使用方法

运行主程序:
```bash
python main.py
```

## 主要功能

### 目标监控
- 实时显示目标运行状态
- 支持状态颜色标记
- 自动更新运行时间

### 搜索功能
- 支持目标名称搜索
- 支持状态过滤
- 支持正则表达式

### 上下文菜单
- 打开终端
- 查看日志
- 追踪依赖关系

## 项目结构

```
Flow-GUI/
├── config/         # 配置文件
├── events/         # 事件处理
├── models/         # 数据模型
├── ui/             # 用户界面
│   └── widgets/    # 界面组件
└── utils/          # 工具函数
```

## 贡献指南

欢迎提交问题和功能建议。如果您想贡献代码:

1. Fork 项目
2. 创建特性分支 (`git checkout -b feature/AmazingFeature`)
3. 提交更改 (`git commit -m 'Add some AmazingFeature'`)
4. 推送到分支 (`git push origin feature/AmazingFeature`)
5. 开启 Pull Request

## 许可证

本项目采用 MIT 许可证 - 详见 [LICENSE](LICENSE) 文件

## 联系方式

如有问题或建议，请通过以下方式联系：

- GitHub Issues: [https://github.com/a6987985/Flow-GUI/issues](https://github.com/a6987985/Flow-GUI/issues) 