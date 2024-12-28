import pandas as pd
import matplotlib.pyplot as plt

# 读取数据函数
def read_wns_file(filename):
    try:
        df = pd.read_csv(filename, 
                        delimiter='\s+',
                        header=None, 
                        names=['group', 'wns', 'tns'],
                        error_bad_lines=False,
                        warn_bad_lines=True)
        
        df = df.dropna()
        df = df[df['wns'] < 0]  # 只保留负的WNS值
        return df
    except Exception as e:
        print(f"读取文件 {filename} 时发生错误: {str(e)}")
        return None

try:
    # 读取三个文件
    files = ['wms1.txt', 'wms2.txt', 'wms3.txt']
    colors = ['blue', 'red', 'green']
    labels = ['Sample 1', 'Sample 2', 'Sample 3']
    
    # 创建图表
    plt.figure(figsize=(15, 8))
    
    # 绘制每个文件的WNS数据
    min_wns = float('inf')  # 用于记录最小WNS值
    for file, color, label in zip(files, colors, labels):
        df = read_wns_file(file)
        if df is not None:
            plt.plot(df['wns'], marker='o', color=color, linewidth=2, 
                    markersize=4, label=label)
            min_wns = min(min_wns, df['wns'].min())
    
    # 设置图表样式
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.title('Negative WNS Distribution Comparison', fontsize=14)
    plt.ylabel('WNS', fontsize=12)
    plt.legend(fontsize=10)
    
    # 隐藏x轴标签
    plt.xticks([])
    
    # 添加水平线标记0点
    plt.axhline(y=0, color='black', linestyle='--', alpha=0.5)
    
    # 设置y轴范围，0在底部，最小值在顶部
    plt.ylim(0, min_wns * 1.1)  # 稍微扩展一下范围
    
    # 调整布局
    plt.tight_layout()
    
    # 保存图表
    plt.savefig('wns_comparison_plot.png', dpi=300, bbox_inches='tight')
    plt.show()

except Exception as e:
    print(f"发生错误: {str(e)}")
    print("请检查数据文件格式是否正确") 