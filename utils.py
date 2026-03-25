"""
公共工具模块
包含数据读取、配置管理、通用绘图工具等功能
"""
import pandas as pd
import matplotlib as mpl
import matplotlib.pyplot as plt
from matplotlib.patches import Patch
import numpy as np

# ==================== 配置统一管理 ====================
# 颜色配置 - 全局统一管理
COLOR_CONFIG = {
    # 品类颜色映射
    'category_colors': {
        '主料': '#FF6B6B',
        '辅料': '#4ECDC4',
        '包装材料': '#45B7D1'
    },
    # 损耗原因颜色映射
    'reason_colors': {
        '存储不当': '#FF6B6B',
        '加工工艺': '#4ECDC4',
        '运输破损': '#45B7D1',
        '自然损耗': '#96CEB4',
        '其他': '#FFEAA7'
    },
    # 批次颜色
    'batch_colors': ['#95E1D3', '#F38181', '#AA96DA', '#FCBAD3', '#A8D8EA'],
    # 热力图配色
    'heatmap_cmap': 'YlOrRd'
}

# 字体配置
FONT_CONFIG = {
    'title_size': 14,
    'label_size': 12,
    'tick_size': 10,
    'annotation_size': 9,
    'super_title_size': 20
}

# 阈值配置
THRESHOLD_CONFIG = {
    'warning_loss_rate': 3,    # 警戒阈值
    'danger_loss_rate': 5,     # 危险阈值
    'strong_correlation': 0.7  # 强相关系数阈值
}

# ==================== 中文字体设置 ====================
def setup_chinese_font():
    """
    设置Matplotlib中文字体支持
    """
    mpl.rcParams['font.sans-serif'] = ['SimHei', 'DejaVu Sans', 'Microsoft YaHei']
    mpl.rcParams['axes.unicode_minus'] = False

# ==================== 数据读取 ====================
def load_data(file_path='原材料数据.csv', encoding='utf-8-sig'):
    """
    读取并验证原材料数据
    
    参数:
        file_path (str): 文件路径
        encoding (str): 文件编码
    
    返回:
        pd.DataFrame: 验证后的数据集
    
    异常:
        FileNotFoundError: 文件不存在时抛出
        ValueError: 数据验证失败时抛出
    """
    try:
        df = pd.read_csv(file_path, encoding=encoding)
    except FileNotFoundError:
        raise FileNotFoundError(f"数据文件 {file_path} 不存在，请先运行generate_data.py生成数据")
    
    # 验证必要的列是否存在
    required_columns = ['原材料名称', '品类', '采购单价', '月使用量', '总成本', '损耗率(%)', '损耗原因', '采购批次']
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        raise ValueError(f"数据缺少必要的列: {', '.join(missing_columns)}")
    
    # 验证数据类型
    numeric_columns = ['采购单价', '月使用量', '总成本', '损耗率(%)']
    for col in numeric_columns:
        if not pd.api.types.is_numeric_dtype(df[col]):
            raise ValueError(f"列 {col} 应为数值类型")
    
    # 如果缺少损耗金额列，自动计算
    if '损耗金额' not in df.columns:
        df['损耗金额'] = df['总成本'] * df['损耗率(%)'] / 100
        print("提示：自动计算损耗金额列")
    
    return df

# ==================== 通用绘图工具 ====================
def add_bar_labels(ax, fmt='{:,.0f}', fontsize=11, offset=0, va='bottom'):
    """
    为柱状图添加数据标签
    
    参数:
        ax (matplotlib.axes.Axes): 坐标轴对象
        fmt (str): 格式化字符串
        fontsize (int): 字体大小
        offset (float): 标签偏移量
        va (str): 垂直对齐方式
    """
    for bar in ax.patches:
        height = bar.get_height()
        if height > 0:  # 只在高度大于0时显示标签
            ax.text(
                bar.get_x() + bar.get_width() / 2.,
                height + offset,
                fmt.format(height),
                ha='center',
                va=va,
                fontsize=fontsize
            )

def add_bar_labels_percent(ax, fontsize=11, offset=0):
    """为柱状图添加百分比数据标签"""
    add_bar_labels(ax, fmt='{:.2f}%', fontsize=fontsize, offset=offset)

def add_bar_labels_currency(ax, fontsize=11, offset=0):
    """为柱状图添加货币数据标签（带¥符号）"""
    add_bar_labels(ax, fmt='¥{:,.0f}', fontsize=fontsize, offset=offset)

def create_category_legend(ax, loc='upper right', fontsize=12):
    """
    创建品类图例
    
    参数:
        ax (matplotlib.axes.Axes): 坐标轴对象
        loc (str): 图例位置
        fontsize (int): 字体大小
    """
    legend_elements = [
        Patch(facecolor=color, edgecolor='black', label=category)
        for category, color in COLOR_CONFIG['category_colors'].items()
    ]
    ax.legend(handles=legend_elements, loc=loc, fontsize=fontsize)

def add_text_box(ax, text, x=0.02, y=0.95, facecolor='yellow', alpha=0.8, fontsize=11):
    """
    添加文本框注释
    
    参数:
        ax (matplotlib.axes.Axes): 坐标轴对象
        text (str): 文本内容
        x (float): x位置（轴坐标）
        y (float): y位置（轴坐标）
        facecolor (str): 背景颜色
        alpha (float): 透明度
        fontsize (int): 字体大小
    """
    ax.text(
        x, y, text,
        transform=ax.transAxes,
        bbox=dict(facecolor=facecolor, alpha=alpha, pad=10),
        fontsize=fontsize,
        verticalalignment='top'
    )

# ==================== 数据聚合函数 ====================
def aggregate_by_category(df):
    """
    按品类聚合数据
    
    参数:
        df (pd.DataFrame): 原始数据集
    
    返回:
        pd.DataFrame: 按品类聚合的统计数据
    """
    return df.groupby('品类').agg({
        '总成本': 'sum',
        '采购单价': 'mean',
        '月使用量': 'sum',
        '损耗率(%)': 'mean',
        '损耗金额': 'sum'
    }).reset_index()

def aggregate_by_material(df):
    """
    按原材料聚合数据
    
    参数:
        df (pd.DataFrame): 原始数据集
    
    返回:
        pd.DataFrame: 按原材料聚合的统计数据
    """
    result = df.groupby(['原材料名称', '品类']).agg({
        '总成本': 'mean',
        '采购单价': 'mean',
        '月使用量': 'mean',
        '损耗率(%)': ['mean', 'std'],
        '损耗金额': 'mean'
    }).reset_index()
    
    # 展平列名
    result.columns = [
        '原材料名称', '品类', '平均总成本', '平均采购单价', '平均月使用量',
        '平均损耗率(%)', '损耗率标准差', '平均损耗金额'
    ]
    return result

def aggregate_by_batch(df):
    """
    按采购批次聚合数据
    
    参数:
        df (pd.DataFrame): 原始数据集
    
    返回:
        pd.DataFrame: 按批次聚合的统计数据
    """
    return df.groupby('采购批次').agg({
        '损耗率(%)': 'mean',
        '损耗金额': 'sum',
        '总成本': 'sum'
    }).reset_index()

def aggregate_by_reason(df):
    """
    按损耗原因聚合数据
    
    参数:
        df (pd.DataFrame): 原始数据集
    
    返回:
        pd.DataFrame: 按损耗原因聚合的统计数据
    """
    result = df.groupby('损耗原因').agg({
        '损耗金额': 'sum',
        '总成本': 'sum',
        '损耗率(%)': 'mean',
        '原材料名称': 'count'
    }).reset_index()
    
    result = result.rename(columns={'原材料名称': '记录数'})
    result['损耗金额占比(%)'] = result['损耗金额'] / result['损耗金额'].sum() * 100
    return result

def aggregate_category_reason(df):
    """
    按品类和损耗原因交叉聚合
    
    参数:
        df (pd.DataFrame): 原始数据集
    
    返回:
        pd.DataFrame: 品类-损耗原因交叉聚合数据
    """
    return df.groupby(['品类', '损耗原因']).agg({
        '损耗金额': 'sum'
    }).reset_index()

# ==================== 格式化函数 ====================
def format_currency(value):
    """格式化货币值"""
    return f'¥{value:,.2f}'

def format_percent(value):
    """格式化百分比"""
    return f'{value:.2f}%'

# ==================== 分析函数 ====================
def calculate_concentration(df, top_n=3):
    """
    计算成本集中度
    
    参数:
        df (pd.DataFrame): 按原材料聚合的数据
        top_n (int): Top N原材料
    
    返回:
        float: 集中度百分比
    """
    sorted_df = df.sort_values('平均总成本', ascending=False)
    top_cost = sorted_df.head(top_n)['平均总成本'].sum()
    total_cost = sorted_df['平均总成本'].sum()
    return (top_cost / total_cost) * 100 if total_cost > 0 else 0

def identify_high_loss_materials(df, threshold=5):
    """
    识别高损耗原材料
    
    参数:
        df (pd.DataFrame): 按原材料聚合的数据
        threshold (float): 损耗率阈值
    
    返回:
        pd.DataFrame: 高损耗原材料数据
    """
    return df[df['平均损耗率(%)'] > threshold].sort_values('平均损耗率(%)', ascending=False)

# ==================== 主执行函数（用于测试） ====================
if __name__ == '__main__':
    # 初始化字体
    setup_chinese_font()
    
    # 测试数据读取
    try:
        df = load_data()
        print("数据读取成功！")
        print(f"数据形状: {df.shape}")
        print(f"原材料种类: {df['原材料名称'].nunique()}")
        
        # 测试聚合函数
        cat_summary = aggregate_by_category(df)
        print("\n品类汇总:")
        print(cat_summary[['品类', '总成本', '损耗金额']])
        
    except Exception as e:
        print(f"错误: {e}")
