"""
原材料成本与损耗率关联分析可视化方案
核心维度：
1. 成本分布可视化
2. 损耗率高低可视化
3. 损耗原因对成本的影响可视化
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Rectangle
import warnings
warnings.filterwarnings('ignore')

# 设置中文字体 - 使用系统可用字体
import matplotlib.font_manager as fm

# 尝试查找可用的中文字体
available_fonts = [f.name for f in fm.fontManager.ttflist]
chinese_fonts = ['DengXian', 'Microsoft YaHei', 'SimHei', 'SimSun', 'NSimSun', 'FangSong', 'KaiTi', 'Arial Unicode MS', 'WenQuanYi Micro Hei']
selected_font = None

for font in chinese_fonts:
    if font in available_fonts:
        selected_font = font
        break

if selected_font:
    plt.rcParams['font.sans-serif'] = [selected_font, 'DejaVu Sans']
    print(f"使用中文字体: {selected_font}")
else:
    # 如果没有找到中文字体，使用默认字体并打印警告
    print("警告: 未找到中文字体，图表中的中文可能显示为乱码")

plt.rcParams['axes.unicode_minus'] = False

# 设置样式
sns.set_style("whitegrid")
plt.style.use('seaborn-v0_8-whitegrid')

# ============================================
# 第一部分：生成原材料数据集
# ============================================
def generate_material_data():
    """生成原材料数据集"""
    np.random.seed(42)
    
    # 定义原材料基础数据
    materials_data = {
        '主料': [
            ('优质牛肉', 85, 1200),
            ('进口猪肉', 45, 2500),
            ('新鲜鸡肉', 28, 3200),
            ('深海鱼片', 120, 600),
            ('特级面粉', 6, 5000),
            ('东北大米', 8, 4500),
            ('有机蔬菜', 15, 2800),
            ('特级食用油', 45, 1500),
        ],
        '辅料': [
            ('食用盐', 3, 800),
            ('白砂糖', 8, 600),
            ('酿造酱油', 25, 400),
            ('香醋', 18, 350),
            ('料酒', 20, 300),
            ('味精', 35, 200),
            ('五香粉', 80, 150),
            ('生姜大蒜', 12, 500),
        ],
        '包装材料': [
            ('食品级塑料袋', 0.5, 10000),
            ('纸箱包装', 2.5, 3000),
            ('真空包装袋', 1.2, 5000),
            ('标签贴纸', 0.1, 20000),
            ('保鲜膜', 3, 2500),
            ('铝箔袋', 4, 1800),
        ]
    }
    
    # 损耗原因及其概率权重
    loss_reasons = ['存储不当', '加工工艺', '运输破损', '过期报废', '质量问题']
    loss_weights = [0.25, 0.30, 0.20, 0.15, 0.10]
    
    # 生成数据
    data = []
    batch_id = 1
    
    for category, materials in materials_data.items():
        for material_name, unit_price, monthly_usage in materials:
            # 生成3-5个采购批次
            num_batches = np.random.randint(3, 6)
            
            for _ in range(num_batches):
                # 基础损耗率根据品类不同
                if category == '主料':
                    base_loss_rate = np.random.uniform(2, 8)
                elif category == '辅料':
                    base_loss_rate = np.random.uniform(1, 5)
                else:  # 包装材料
                    base_loss_rate = np.random.uniform(0.5, 4)
                
                # 添加随机波动
                loss_rate = max(0.1, min(15, base_loss_rate + np.random.normal(0, 1)))
                loss_rate = round(loss_rate, 2)
                
                # 计算总成本和损耗成本
                batch_usage = monthly_usage // num_batches + np.random.randint(-50, 50)
                batch_usage = max(10, batch_usage)
                total_cost = round(unit_price * batch_usage, 2)
                loss_cost = round(total_cost * loss_rate / 100, 2)
                
                # 随机选择损耗原因
                loss_reason = np.random.choice(loss_reasons, p=loss_weights)
                
                data.append({
                    '原材料名称': material_name,
                    '品类': category,
                    '采购单价': unit_price,
                    '月使用量': batch_usage,
                    '总成本': total_cost,
                    '损耗率(%)': loss_rate,
                    '损耗原因': loss_reason,
                    '采购批次': f'BATCH-{batch_id:04d}',
                    '损耗金额': loss_cost
                })
                batch_id += 1
    
    return pd.DataFrame(data)

# 生成数据
df = generate_material_data()
print("=" * 80)
print("原材料数据集概览")
print("=" * 80)
print(f"数据条数: {len(df)}")
print(f"\n数据字段: {list(df.columns)}")
print(f"\n数据前10行:")
print(df.head(10).to_string())
print(f"\n数据统计摘要:")
print(df.describe())

# 保存数据到CSV
df.to_csv('material_data.csv', index=False, encoding='utf-8-sig')
print("\n数据已保存到 material_data.csv")

# ============================================
# 第二部分：成本分布可视化
# ============================================

def plot_cost_distribution(df):
    """成本分布可视化 - 饼图+柱状图组合"""
    fig = plt.figure(figsize=(18, 10))
    
    # 创建子图布局
    gs = fig.add_gridspec(2, 3, hspace=0.3, wspace=0.3)
    
    # 1. 品类成本占比饼图
    ax1 = fig.add_subplot(gs[0, 0])
    category_cost = df.groupby('品类')['总成本'].sum().sort_values(ascending=False)
    colors_pie = ['#FF6B6B', '#4ECDC4', '#45B7D1']
    
    wedges, texts, autotexts = ax1.pie(
        category_cost.values, 
        labels=category_cost.index,
        autopct='%1.1f%%',
        colors=colors_pie,
        explode=[0.02, 0.02, 0.02],
        shadow=True,
        startangle=90
    )
    ax1.set_title('各品类总成本占比分布', fontsize=14, fontweight='bold', pad=15)
    
    # 添加金额标注
    total_cost = category_cost.sum()
    for i, (cat, cost) in enumerate(category_cost.items()):
        percentage = cost / total_cost * 100
        print(f"  {cat}: ¥{cost:,.2f} ({percentage:.1f}%)")
    
    # 2. 各品类成本柱状图
    ax2 = fig.add_subplot(gs[0, 1:])
    bars = ax2.bar(category_cost.index, category_cost.values, color=colors_pie, 
                   edgecolor='white', linewidth=2)
    ax2.set_ylabel('总成本 (元)', fontsize=12)
    ax2.set_title('各品类总成本对比', fontsize=14, fontweight='bold', pad=15)
    ax2.set_ylim(0, max(category_cost.values) * 1.15)
    
    # 添加数值标签
    for bar, cost in zip(bars, category_cost.values):
        height = bar.get_height()
        ax2.annotate(f'¥{cost:,.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # 3. TOP10高成本原材料横向柱状图
    ax3 = fig.add_subplot(gs[1, :])
    material_cost = df.groupby('原材料名称').agg({
        '总成本': 'sum',
        '品类': 'first'
    }).sort_values('总成本', ascending=True).tail(10)
    
    # 根据品类设置颜色
    color_map = {'主料': '#FF6B6B', '辅料': '#4ECDC4', '包装材料': '#45B7D1'}
    bar_colors = [color_map[cat] for cat in material_cost['品类']]
    
    bars = ax3.barh(material_cost.index, material_cost['总成本'], color=bar_colors, 
                    edgecolor='white', linewidth=1.5)
    ax3.set_xlabel('总成本 (元)', fontsize=12)
    ax3.set_title('TOP10 高成本原材料排名', fontsize=14, fontweight='bold', pad=15)
    
    # 添加数值标签
    for bar, cost in zip(bars, material_cost['总成本']):
        width = bar.get_width()
        ax3.annotate(f'¥{cost:,.0f}',
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0),
                    textcoords="offset points",
                    ha='left', va='center', fontsize=10, fontweight='bold')
    
    # 添加图例
    from matplotlib.patches import Patch
    legend_elements = [Patch(facecolor=color_map[cat], label=cat) for cat in color_map]
    ax3.legend(handles=legend_elements, loc='lower right', fontsize=10)
    
    plt.suptitle('第一维度：成本分布可视化分析', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig('cost_distribution.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    
    return category_cost, material_cost

print("\n" + "=" * 80)
print("正在生成成本分布可视化...")
print("=" * 80)
category_cost, material_cost = plot_cost_distribution(df)

# ============================================
# 第三部分：损耗率高低可视化
# ============================================

def plot_loss_rate_analysis(df):
    """损耗率高低可视化 - 柱状图+箱线图+散点图"""
    fig = plt.figure(figsize=(18, 12))
    gs = fig.add_gridspec(2, 3, hspace=0.35, wspace=0.3)
    
    color_map = {'主料': '#FF6B6B', '辅料': '#4ECDC4', '包装材料': '#45B7D1'}
    
    # 1. 各品类平均损耗率对比（柱状图）
    ax1 = fig.add_subplot(gs[0, 0])
    category_loss = df.groupby('品类')['损耗率(%)'].mean().sort_values(ascending=False)
    bars = ax1.bar(category_loss.index, category_loss.values, 
                   color=[color_map[cat] for cat in category_loss.index],
                   edgecolor='white', linewidth=2)
    ax1.set_ylabel('平均损耗率 (%)', fontsize=12)
    ax1.set_title('各品类平均损耗率对比', fontsize=14, fontweight='bold', pad=15)
    ax1.set_ylim(0, max(category_loss.values) * 1.2)
    
    # 添加数值标签和警戒线
    for bar, rate in zip(bars, category_loss.values):
        height = bar.get_height()
        ax1.annotate(f'{rate:.2f}%',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=11, fontweight='bold')
    
    # 添加警戒线（5%）
    ax1.axhline(y=5, color='red', linestyle='--', linewidth=2, alpha=0.7, label='警戒线(5%)')
    ax1.legend(loc='upper right')
    
    # 2. 各品类损耗率分布箱线图
    ax2 = fig.add_subplot(gs[0, 1:])
    categories = df['品类'].unique()
    box_data = [df[df['品类'] == cat]['损耗率(%)'].values for cat in categories]
    box_colors = [color_map[cat] for cat in categories]
    
    bp = ax2.boxplot(box_data, labels=categories, patch_artist=True)
    for patch, color in zip(bp['boxes'], box_colors):
        patch.set_facecolor(color)
        patch.set_alpha(0.7)
    
    ax2.set_ylabel('损耗率 (%)', fontsize=12)
    ax2.set_title('各品类损耗率分布箱线图', fontsize=14, fontweight='bold', pad=15)
    ax2.axhline(y=5, color='red', linestyle='--', linewidth=2, alpha=0.7, label='警戒线(5%)')
    ax2.legend(loc='upper right')
    
    # 添加统计信息
    for i, cat in enumerate(categories):
        cat_data = df[df['品类'] == cat]['损耗率(%)']
        median = cat_data.median()
        ax2.annotate(f'中位数: {median:.2f}%',
                    xy=(i+1, median),
                    xytext=(10, 10),
                    textcoords="offset points",
                    fontsize=9, color='darkblue')
    
    # 3. 高损耗率原材料TOP10
    ax3 = fig.add_subplot(gs[1, :2])
    material_loss = df.groupby('原材料名称').agg({
        '损耗率(%)': 'mean',
        '品类': 'first'
    }).sort_values('损耗率(%)', ascending=True).tail(10)
    
    bar_colors = [color_map[cat] for cat in material_loss['品类']]
    bars = ax3.barh(material_loss.index, material_loss['损耗率(%)'], 
                    color=bar_colors, edgecolor='white', linewidth=1.5)
    ax3.set_xlabel('平均损耗率 (%)', fontsize=12)
    ax3.set_title('TOP10 高损耗率原材料', fontsize=14, fontweight='bold', pad=15)
    ax3.axvline(x=5, color='red', linestyle='--', linewidth=2, alpha=0.7, label='警戒线(5%)')
    
    # 添加数值标签
    for bar, rate in zip(bars, material_loss['损耗率(%)']):
        width = bar.get_width()
        ax3.annotate(f'{rate:.2f}%',
                    xy=(width, bar.get_y() + bar.get_height() / 2),
                    xytext=(5, 0),
                    textcoords="offset points",
                    ha='left', va='center', fontsize=10, fontweight='bold',
                    color='red' if rate > 5 else 'black')
    
    # 4. 损耗率分布直方图
    ax4 = fig.add_subplot(gs[1, 2])
    ax4.hist(df['损耗率(%)'], bins=15, color='#95E1D3', edgecolor='white', alpha=0.8)
    ax4.axvline(x=df['损耗率(%)'].mean(), color='red', linestyle='--', linewidth=2, 
                label=f'平均值: {df["损耗率(%)"].mean():.2f}%')
    ax4.axvline(x=5, color='orange', linestyle='--', linewidth=2, label='警戒线: 5%')
    ax4.set_xlabel('损耗率 (%)', fontsize=12)
    ax4.set_ylabel('频次', fontsize=12)
    ax4.set_title('损耗率分布直方图', fontsize=14, fontweight='bold', pad=15)
    ax4.legend(loc='upper right')
    
    plt.suptitle('第二维度：损耗率高低可视化分析', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig('loss_rate_analysis.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    
    # 输出高损耗预警
    print("\n高损耗预警 (>5%):")
    high_loss = df[df['损耗率(%)'] > 5].groupby('原材料名称').agg({
        '损耗率(%)': 'mean',
        '品类': 'first'
    }).sort_values('损耗率(%)', ascending=False)
    for material, row in high_loss.head(5).iterrows():
        print(f"  ⚠️ {material} ({row['品类']}): {row['损耗率(%)']:.2f}%")
    
    return category_loss, material_loss

print("\n" + "=" * 80)
print("正在生成损耗率高低可视化...")
print("=" * 80)
category_loss, material_loss = plot_loss_rate_analysis(df)

# ============================================
# 第四部分：损耗原因对成本的影响可视化
# ============================================

def plot_loss_reason_analysis(df):
    """损耗原因对成本的影响可视化 - 热力图+瀑布图+散点图"""
    fig = plt.figure(figsize=(20, 14))
    gs = fig.add_gridspec(3, 3, hspace=0.4, wspace=0.35)
    
    color_map = {'主料': '#FF6B6B', '辅料': '#4ECDC4', '包装材料': '#45B7D1'}
    
    # 1. 各损耗原因的成本损失金额（柱状图）
    ax1 = fig.add_subplot(gs[0, :2])
    reason_cost = df.groupby('损耗原因')['损耗金额'].sum().sort_values(ascending=False)
    colors_reason = ['#E74C3C', '#E67E22', '#F39C12', '#27AE60', '#3498DB']
    
    bars = ax1.bar(reason_cost.index, reason_cost.values, color=colors_reason,
                   edgecolor='white', linewidth=2)
    ax1.set_ylabel('损耗金额 (元)', fontsize=12)
    ax1.set_title('各损耗原因导致的成本损失金额', fontsize=14, fontweight='bold', pad=15)
    ax1.set_ylim(0, max(reason_cost.values) * 1.15)
    
    # 添加数值标签和占比
    total_loss = reason_cost.sum()
    for bar, cost in zip(bars, reason_cost.values):
        height = bar.get_height()
        percentage = cost / total_loss * 100
        ax1.annotate(f'¥{cost:,.0f}\n({percentage:.1f}%)',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 5),
                    textcoords="offset points",
                    ha='center', va='bottom', fontsize=10, fontweight='bold')
    
    # 2. 损耗原因占比饼图
    ax2 = fig.add_subplot(gs[0, 2])
    wedges, texts, autotexts = ax2.pie(
        reason_cost.values,
        labels=reason_cost.index,
        autopct='%1.1f%%',
        colors=colors_reason,
        explode=[0.03] * len(reason_cost),
        shadow=True,
        startangle=90
    )
    ax2.set_title('损耗原因成本占比', fontsize=14, fontweight='bold', pad=15)
    
    # 3. 品类×损耗原因 热力图
    ax3 = fig.add_subplot(gs[1, :])
    pivot_table = df.pivot_table(
        values='损耗金额',
        index='损耗原因',
        columns='品类',
        aggfunc='sum'
    ).fillna(0)
    
    # 使用seaborn绘制热力图
    sns.heatmap(pivot_table, annot=True, fmt='.0f', cmap='YlOrRd',
                cbar_kws={'label': '损耗金额 (元)'}, ax=ax3, linewidths=1,
                linecolor='white')
    ax3.set_title('品类 × 损耗原因 热力图（损耗金额）', fontsize=14, fontweight='bold', pad=15)
    ax3.set_xlabel('品类', fontsize=12)
    ax3.set_ylabel('损耗原因', fontsize=12)
    
    # 4. 成本-损耗率散点图（气泡大小表示损耗金额）
    ax4 = fig.add_subplot(gs[2, :2])
    
    for category in df['品类'].unique():
        cat_data = df[df['品类'] == category]
        scatter = ax4.scatter(
            cat_data['总成本'],
            cat_data['损耗率(%)'],
            s=cat_data['损耗金额'] / 10,  # 气泡大小
            c=color_map[category],
            alpha=0.6,
            edgecolors='white',
            linewidth=1,
            label=category
        )
    
    ax4.set_xlabel('总成本 (元)', fontsize=12)
    ax4.set_ylabel('损耗率 (%)', fontsize=12)
    ax4.set_title('成本-损耗率关联散点图（气泡大小=损耗金额）', fontsize=14, fontweight='bold', pad=15)
    ax4.legend(title='品类', loc='upper right')
    ax4.axhline(y=5, color='red', linestyle='--', linewidth=1.5, alpha=0.5)
    ax4.axvline(x=df['总成本'].median(), color='blue', linestyle='--', linewidth=1.5, alpha=0.5)
    
    # 添加象限标注
    ax4.text(0.95, 0.95, '高成本\n高损耗', transform=ax4.transAxes, 
             ha='right', va='top', fontsize=10, color='red',
             bbox=dict(boxstyle='round', facecolor='white', alpha=0.7))
    
    # 5. 各品类损耗成本瀑布图（简化版）
    ax5 = fig.add_subplot(gs[2, 2])
    category_loss_cost = df.groupby('品类')['损耗金额'].sum().sort_values(ascending=False)
    
    # 计算累计值用于瀑布图效果
    cumulative = 0
    for i, (cat, cost) in enumerate(category_loss_cost.items()):
        ax5.bar(i, cost, bottom=cumulative, color=color_map[cat], 
                edgecolor='white', linewidth=2)
        ax5.annotate(f'¥{cost:,.0f}',
                    xy=(i, cumulative + cost / 2),
                    ha='center', va='center', fontsize=10, fontweight='bold')
        cumulative += cost
    
    ax5.set_xticks(range(len(category_loss_cost)))
    ax5.set_xticklabels(category_loss_cost.index, rotation=45, ha='right')
    ax5.set_ylabel('累计损耗金额 (元)', fontsize=12)
    ax5.set_title('各品类累计损耗成本', fontsize=14, fontweight='bold', pad=15)
    
    plt.suptitle('第三维度：损耗原因对成本的影响可视化分析', fontsize=16, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig('loss_reason_analysis.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()
    
    # 输出关键洞察
    print("\n损耗原因成本影响分析:")
    print(f"  总损耗金额: ¥{df['损耗金额'].sum():,.2f}")
    print(f"  平均损耗率: {df['损耗率(%)'].mean():.2f}%")
    print("\n  各损耗原因影响排名:")
    for i, (reason, cost) in enumerate(reason_cost.items(), 1):
        percentage = cost / total_loss * 100
        print(f"    {i}. {reason}: ¥{cost:,.2f} ({percentage:.1f}%)")
    
    return reason_cost, pivot_table

print("\n" + "=" * 80)
print("正在生成损耗原因对成本影响可视化...")
print("=" * 80)
reason_cost, pivot_table = plot_loss_reason_analysis(df)

# ============================================
# 第五部分：综合仪表盘与关键指标分析
# ============================================

def create_dashboard(df):
    """创建综合仪表盘"""
    fig = plt.figure(figsize=(20, 16))
    gs = fig.add_gridspec(3, 4, hspace=0.4, wspace=0.35)
    
    color_map = {'主料': '#FF6B6B', '辅料': '#4ECDC4', '包装材料': '#45B7D1'}
    
    # 计算关键指标
    total_cost = df['总成本'].sum()
    total_loss_cost = df['损耗金额'].sum()
    avg_loss_rate = df['损耗率(%)'].mean()
    high_loss_materials = len(df[df['损耗率(%)'] > 5]['原材料名称'].unique())
    
    # 1. KPI卡片 - 总成本
    ax1 = fig.add_subplot(gs[0, 0])
    ax1.text(0.5, 0.7, '总采购成本', ha='center', va='center', 
             fontsize=14, transform=ax1.transAxes)
    ax1.text(0.5, 0.4, f'¥{total_cost:,.0f}', ha='center', va='center', 
             fontsize=24, fontweight='bold', color='#2C3E50', transform=ax1.transAxes)
    ax1.set_xlim(0, 1)
    ax1.set_ylim(0, 1)
    ax1.axis('off')
    ax1.add_patch(Rectangle((0.05, 0.05), 0.9, 0.9, fill=False, 
                            edgecolor='#3498DB', linewidth=3, transform=ax1.transAxes))
    
    # 2. KPI卡片 - 总损耗金额
    ax2 = fig.add_subplot(gs[0, 1])
    ax2.text(0.5, 0.7, '总损耗金额', ha='center', va='center', 
             fontsize=14, transform=ax2.transAxes)
    ax2.text(0.5, 0.4, f'¥{total_loss_cost:,.0f}', ha='center', va='center', 
             fontsize=24, fontweight='bold', color='#E74C3C', transform=ax2.transAxes)
    loss_ratio = total_loss_cost / total_cost * 100
    ax2.text(0.5, 0.2, f'占成本比例: {loss_ratio:.2f}%', ha='center', va='center', 
             fontsize=11, color='#7F8C8D', transform=ax2.transAxes)
    ax2.set_xlim(0, 1)
    ax2.set_ylim(0, 1)
    ax2.axis('off')
    ax2.add_patch(Rectangle((0.05, 0.05), 0.9, 0.9, fill=False, 
                            edgecolor='#E74C3C', linewidth=3, transform=ax2.transAxes))
    
    # 3. KPI卡片 - 平均损耗率
    ax3 = fig.add_subplot(gs[0, 2])
    ax3.text(0.5, 0.7, '平均损耗率', ha='center', va='center', 
             fontsize=14, transform=ax3.transAxes)
    color = '#E74C3C' if avg_loss_rate > 5 else '#27AE60'
    ax3.text(0.5, 0.4, f'{avg_loss_rate:.2f}%', ha='center', va='center', 
             fontsize=24, fontweight='bold', color=color, transform=ax3.transAxes)
    status = '⚠️ 超标' if avg_loss_rate > 5 else '✓ 正常'
    ax3.text(0.5, 0.2, f'状态: {status}', ha='center', va='center', 
             fontsize=11, color=color, transform=ax3.transAxes)
    ax3.set_xlim(0, 1)
    ax3.set_ylim(0, 1)
    ax3.axis('off')
    ax3.add_patch(Rectangle((0.05, 0.05), 0.9, 0.9, fill=False, 
                            edgecolor=color, linewidth=3, transform=ax3.transAxes))
    
    # 4. KPI卡片 - 高损耗原材料数
    ax4 = fig.add_subplot(gs[0, 3])
    ax4.text(0.5, 0.7, '高损耗原材料数', ha='center', va='center', 
             fontsize=14, transform=ax4.transAxes)
    ax4.text(0.5, 0.4, f'{high_loss_materials}', ha='center', va='center', 
             fontsize=24, fontweight='bold', color='#E67E22', transform=ax4.transAxes)
    ax4.text(0.5, 0.2, f'损耗率>5%的原材料', ha='center', va='center', 
             fontsize=11, color='#7F8C8D', transform=ax4.transAxes)
    ax4.set_xlim(0, 1)
    ax4.set_ylim(0, 1)
    ax4.axis('off')
    ax4.add_patch(Rectangle((0.05, 0.05), 0.9, 0.9, fill=False, 
                            edgecolor='#E67E22', linewidth=3, transform=ax4.transAxes))
    
    # 5. 品类成本与损耗对比（双轴图）
    ax5 = fig.add_subplot(gs[1, :2])
    category_stats = df.groupby('品类').agg({
        '总成本': 'sum',
        '损耗金额': 'sum'
    }).sort_values('总成本', ascending=False)
    
    x = np.arange(len(category_stats))
    width = 0.35
    
    bars1 = ax5.bar(x - width/2, category_stats['总成本'], width, 
                    label='总成本', color='#3498DB', alpha=0.8)
    bars2 = ax5.bar(x + width/2, category_stats['损耗金额'], width,
                    label='损耗金额', color='#E74C3C', alpha=0.8)
    
    ax5.set_ylabel('金额 (元)', fontsize=12)
    ax5.set_title('各品类成本与损耗金额对比', fontsize=14, fontweight='bold', pad=15)
    ax5.set_xticks(x)
    ax5.set_xticklabels(category_stats.index)
    ax5.legend()
    
    # 添加数值标签
    for bar in bars1:
        height = bar.get_height()
        ax5.annotate(f'¥{height:,.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)
    for bar in bars2:
        height = bar.get_height()
        ax5.annotate(f'¥{height:,.0f}',
                    xy=(bar.get_x() + bar.get_width() / 2, height),
                    xytext=(0, 3), textcoords="offset points",
                    ha='center', va='bottom', fontsize=9)
    
    # 6. 损耗率趋势（按采购批次）
    ax6 = fig.add_subplot(gs[1, 2:])
    df_sorted = df.sort_values('采购批次')
    for category in df['品类'].unique():
        cat_data = df_sorted[df_sorted['品类'] == category]
        ax6.plot(range(len(cat_data)), cat_data['损耗率(%)'], 
                marker='o', label=category, color=color_map[category], linewidth=2)
    
    ax6.axhline(y=5, color='red', linestyle='--', linewidth=2, alpha=0.7, label='警戒线')
    ax6.set_xlabel('采购批次序号', fontsize=12)
    ax6.set_ylabel('损耗率 (%)', fontsize=12)
    ax6.set_title('损耗率趋势分析', fontsize=14, fontweight='bold', pad=15)
    ax6.legend(loc='upper left')
    ax6.grid(True, alpha=0.3)
    
    # 7. 高成本高损耗风险矩阵
    ax7 = fig.add_subplot(gs[2, :2])
    material_risk = df.groupby('原材料名称').agg({
        '总成本': 'sum',
        '损耗率(%)': 'mean',
        '品类': 'first'
    })
    
    for category in material_risk['品类'].unique():
        cat_data = material_risk[material_risk['品类'] == category]
        ax7.scatter(cat_data['总成本'], cat_data['损耗率(%)'], 
                   s=200, c=color_map[category], alpha=0.7, 
                   edgecolors='white', linewidth=2, label=category)
    
    # 添加风险区域划分
    ax7.axhline(y=5, color='red', linestyle='--', linewidth=2, alpha=0.5)
    ax7.axvline(x=material_risk['总成本'].median(), color='blue', linestyle='--', linewidth=2, alpha=0.5)
    
    # 标注高风险点
    high_risk = material_risk[(material_risk['损耗率(%)'] > 5) & 
                              (material_risk['总成本'] > material_risk['总成本'].median())]
    for name, row in high_risk.iterrows():
        ax7.annotate(name, (row['总成本'], row['损耗率(%)']),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=9, color='red', fontweight='bold')
    
    ax7.set_xlabel('总成本 (元)', fontsize=12)
    ax7.set_ylabel('损耗率 (%)', fontsize=12)
    ax7.set_title('成本-损耗风险矩阵（右上=高风险区）', fontsize=14, fontweight='bold', pad=15)
    ax7.legend(title='品类', loc='upper right')
    
    # 8. 优化建议清单
    ax8 = fig.add_subplot(gs[2, 2:])
    ax8.axis('off')
    
    # 生成优化建议
    suggestions = []
    
    # 建议1: 高损耗原材料
    top_loss = df.groupby('原材料名称')['损耗率(%)'].mean().sort_values(ascending=False).head(3)
    for material, rate in top_loss.items():
        category = df[df['原材料名称'] == material]['品类'].iloc[0]
        suggestions.append(f"⚠️ 优先处理: {material}({category}) - 损耗率{rate:.2f}%")
    
    # 建议2: 高成本损耗
    top_cost_loss = df.groupby('损耗原因')['损耗金额'].sum().sort_values(ascending=False).head(2)
    for reason, cost in top_cost_loss.items():
        suggestions.append(f"💰 重点管控: {reason} - 损失¥{cost:,.0f}")
    
    # 建议3: 品类建议
    category_loss_rate = df.groupby('品类')['损耗率(%)'].mean().sort_values(ascending=False)
    worst_category = category_loss_rate.index[0]
    suggestions.append(f"📊 品类优化: {worst_category}品类平均损耗率最高({category_loss_rate.iloc[0]:.2f}%)")
    
    # 显示建议
    ax8.text(0.05, 0.95, '📋 优化建议清单', fontsize=16, fontweight='bold', 
             transform=ax8.transAxes, va='top')
    
    y_pos = 0.80
    for i, suggestion in enumerate(suggestions, 1):
        ax8.text(0.05, y_pos, f'{i}. {suggestion}', fontsize=11, 
                transform=ax8.transAxes, va='top')
        y_pos -= 0.15
    
    # 添加边框
    ax8.add_patch(Rectangle((0.02, 0.1), 0.96, 0.85, fill=False, 
                            edgecolor='#34495E', linewidth=2, transform=ax8.transAxes))
    
    plt.suptitle('原材料成本与损耗率综合仪表盘', fontsize=18, fontweight='bold', y=0.98)
    plt.tight_layout()
    plt.savefig('dashboard.png', dpi=150, bbox_inches='tight', facecolor='white')
    plt.show()

print("\n" + "=" * 80)
print("正在生成综合仪表盘...")
print("=" * 80)
create_dashboard(df)

# ============================================
# 输出完整分析报告
# ============================================
print("\n" + "=" * 80)
print("完整分析报告")
print("=" * 80)

print("\n【一、成本分布分析】")
print(f"  • 总采购成本: ¥{df['总成本'].sum():,.2f}")
for cat, cost in df.groupby('品类')['总成本'].sum().sort_values(ascending=False).items():
    pct = cost / df['总成本'].sum() * 100
    print(f"  • {cat}: ¥{cost:,.2f} ({pct:.1f}%)")

print("\n【二、损耗率分析】")
print(f"  • 平均损耗率: {df['损耗率(%)'].mean():.2f}%")
print(f"  • 最高损耗率: {df['损耗率(%)'].max():.2f}%")
print(f"  • 高损耗原材料数(>5%): {len(df[df['损耗率(%)'] > 5]['原材料名称'].unique())}个")

print("\n【三、损耗原因分析】")
for reason, cost in df.groupby('损耗原因')['损耗金额'].sum().sort_values(ascending=False).items():
    pct = cost / df['损耗金额'].sum() * 100
    print(f"  • {reason}: ¥{cost:,.2f} ({pct:.1f}%)")

print("\n【四、核心发现】")
# 高成本高损耗
high_cost_high_loss = df.groupby('原材料名称').agg({
    '总成本': 'sum',
    '损耗率(%)': 'mean'
})
high_risk = high_cost_high_loss[
    (high_cost_high_loss['总成本'] > high_cost_high_loss['总成本'].median()) &
    (high_cost_high_loss['损耗率(%)'] > 5)
]
print(f"  • 高成本高损耗风险原材料: {len(high_risk)}个")
for name, row in high_risk.head(3).iterrows():
    print(f"    - {name}: 成本¥{row['总成本']:,.0f}, 损耗率{row['损耗率(%)']:.2f}%")

print("\n" + "=" * 80)
print("可视化图表已生成:")
print("  1. cost_distribution.png - 成本分布可视化")
print("  2. loss_rate_analysis.png - 损耗率高低可视化")
print("  3. loss_reason_analysis.png - 损耗原因影响可视化")
print("  4. dashboard.png - 综合仪表盘")
print("  5. material_data.csv - 原始数据")
print("=" * 80)
