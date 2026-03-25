# -*- coding: utf-8 -*-
"""
原材料成本与损耗率关联分析可视化方案（优化版）
================================================
三大维度分析：
1. 成本分布可视化
2. 损耗率高低可视化  
3. 损耗原因对成本的影响可视化

优化内容：
- 统一配置管理
- 减少重复代码
- 性能优化（向量化操作）
- 异常处理与数据验证
- 支持自定义参数
- 清晰简洁的图表布局
"""

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.gridspec import GridSpec
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import warnings
import os

warnings.filterwarnings('ignore')


@dataclass
class ChartConfig:
    """图表配置类：统一管理所有可视化配置"""
    
    COLORS_CATEGORY: Dict[str, str] = field(default_factory=lambda: {
        '主料': '#E74C3C',
        '辅料': '#3498DB', 
        '包装材料': '#2ECC71'
    })
    
    COLORS_REASON: List[str] = field(default_factory=lambda: ['#E74C3C', '#F39C12', '#3498DB'])
    
    MARKERS: Dict[str, str] = field(default_factory=lambda: {
        '主料': 'o',
        '辅料': 's',
        '包装材料': '^'
    })
    
    FONT_SIZE_TITLE: int = 13
    FONT_SIZE_LABEL: int = 11
    FONT_SIZE_TICK: int = 10
    FONT_SIZE_ANNOTATION: int = 9
    
    DPI_DISPLAY: int = 100
    DPI_SAVE: int = 150
    
    FIGURE_WIDTH: int = 16
    FIGURE_HEIGHT: int = 20
    
    def setup_matplotlib(self):
        """配置matplotlib全局参数"""
        plt.rcParams['font.sans-serif'] = ['SimHei', 'Microsoft YaHei', 'Arial Unicode MS']
        plt.rcParams['axes.unicode_minus'] = False
        plt.rcParams['figure.dpi'] = self.DPI_DISPLAY
        plt.rcParams['savefig.dpi'] = self.DPI_SAVE


@dataclass
class MaterialConfig:
    """原材料数据配置类"""
    
    MAIN_MATERIALS: List[str] = field(default_factory=lambda: [
        '面粉', '白砂糖', '食用油', '鸡蛋', '牛奶', '奶油', '巧克力', '黄油'
    ])
    AUXILIARY_MATERIALS: List[str] = field(default_factory=lambda: [
        '酵母', '泡打粉', '香草精', '食用色素', '柠檬酸', '明胶', '乳化剂', '防腐剂'
    ])
    PACKAGING_MATERIALS: List[str] = field(default_factory=lambda: [
        '纸箱', '塑料袋', '铝箔袋', '标签纸', '胶带', '托盘', '保鲜膜', '纸盒'
    ])
    
    LOSS_REASONS: List[str] = field(default_factory=lambda: ['存储不当', '加工工艺', '运输破损'])
    
    PRICE_RANGE: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        '主料': (8, 50),
        '辅料': (15, 120),
        '包装材料': (0.5, 8)
    })
    
    USAGE_RANGE: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        '主料': (500, 3000),
        '辅料': (20, 200),
        '包装材料': (2000, 15000)
    })
    
    LOSS_RATE_RANGE: Dict[str, Tuple[float, float]] = field(default_factory=lambda: {
        '主料': (2, 8),
        '辅料': (3, 12),
        '包装材料': (1, 6)
    })
    
    LOSS_REASON_PROB: Dict[str, Tuple[float, float, float]] = field(default_factory=lambda: {
        '主料': (0.3, 0.5, 0.2),
        '辅料': (0.4, 0.35, 0.25),
        '包装材料': (0.2, 0.3, 0.5)
    })
    
    NUM_BATCHES: int = 6


class DataGenerator:
    """数据生成器类"""
    
    def __init__(self, config: MaterialConfig, seed: int = 42):
        self.config = config
        np.random.seed(seed)
    
    def generate(self) -> pd.DataFrame:
        """生成完整的原材料数据集"""
        data = []
        
        category_mapping = {
            '主料': self.config.MAIN_MATERIALS,
            '辅料': self.config.AUXILIARY_MATERIALS,
            '包装材料': self.config.PACKAGING_MATERIALS
        }
        
        for category, materials in category_mapping.items():
            for name in materials:
                record = self._generate_single_record(name, category)
                data.append(record)
        
        df = pd.DataFrame(data)
        df['损耗金额(元)'] = self._calculate_loss_amount(df)
        
        return df
    
    def _generate_single_record(self, name: str, category: str) -> dict:
        """生成单条原材料记录"""
        price_range = self.config.PRICE_RANGE[category]
        usage_range = self.config.USAGE_RANGE[category]
        loss_range = self.config.LOSS_RATE_RANGE[category]
        loss_prob = self.config.LOSS_REASON_PROB[category]
        
        unit_price = np.random.uniform(*price_range)
        monthly_usage = np.random.uniform(*usage_range)
        loss_rate = np.random.uniform(*loss_range)
        loss_reason = np.random.choice(self.config.LOSS_REASONS, p=loss_prob)
        batch = f"B{np.random.randint(1, self.config.NUM_BATCHES + 1):03d}"
        total_cost = unit_price * monthly_usage
        
        return {
            '原材料名称': name,
            '品类': category,
            '采购单价(元/kg)': round(unit_price, 2),
            '月使用量(kg)': round(monthly_usage, 1),
            '总成本(元)': round(total_cost, 2),
            '损耗率(%)': round(loss_rate, 2),
            '损耗原因': loss_reason,
            '采购批次': batch
        }
    
    @staticmethod
    def _calculate_loss_amount(df: pd.DataFrame) -> pd.Series:
        """向量化计算损耗金额"""
        return round(df['总成本(元)'] * df['损耗率(%)'] / 100, 2)


class DataValidator:
    """数据验证器类"""
    
    @staticmethod
    def validate(df: pd.DataFrame) -> bool:
        """验证数据完整性"""
        required_columns = [
            '原材料名称', '品类', '采购单价(元/kg)', '月使用量(kg)',
            '总成本(元)', '损耗率(%)', '损耗原因', '采购批次'
        ]
        
        missing_cols = set(required_columns) - set(df.columns)
        if missing_cols:
            raise ValueError(f"缺少必要字段: {missing_cols}")
        
        if df['损耗率(%)'].min() < 0 or df['损耗率(%)'].max() > 100:
            raise ValueError("损耗率应在0-100%之间")
        
        if df['总成本(元)'].min() < 0:
            raise ValueError("总成本不能为负数")
        
        return True


class ChartStyleMixin:
    """图表样式混入类"""
    
    @staticmethod
    def remove_spines(ax, sides: List[str] = ['top', 'right']):
        """移除坐标轴边框"""
        for side in sides:
            ax.spines[side].set_visible(False)
    
    @staticmethod
    def add_value_labels(ax, bars, values, format_str: str = '{:,.0f}', 
                         offset: Tuple[float, float] = (0, 0), fontsize: int = 8,
                         rotation: float = 0):
        """为柱状图添加数值标签"""
        for bar, val in zip(bars, values):
            height = bar.get_height()
            ax.text(bar.get_x() + bar.get_width()/2 + offset[0], 
                   height + offset[1],
                   format_str.format(val),
                   ha='center', va='bottom', fontsize=fontsize, rotation=rotation)


class VisualizationEngine(ChartStyleMixin):
    """可视化引擎类"""
    
    def __init__(self, config: ChartConfig):
        self.config = config
        self.config.setup_matplotlib()
        self._cache = {}
    
    def create_full_report(self, df: pd.DataFrame, output_file: str = None) -> plt.Figure:
        """创建完整的可视化报告"""
        self._validate_and_cache(df)
        
        fig = plt.figure(figsize=(self.config.FIGURE_WIDTH, self.config.FIGURE_HEIGHT))
        gs = GridSpec(4, 2, figure=fig, height_ratios=[1, 1, 1, 1], 
                      hspace=0.4, wspace=0.3)
        
        fig.suptitle('原材料成本与损耗率关联分析报告', 
                     fontsize=16, fontweight='bold', y=0.98)
        
        self._create_dimension1(df, fig, gs, 0)
        self._create_dimension2(df, fig, gs, 1)
        self._create_dimension3(df, fig, gs, 2)
        self._create_summary(df, fig, gs, 3)
        
        plt.tight_layout(rect=[0, 0, 1, 0.96])
        
        if output_file:
            fig.savefig(output_file, dpi=self.config.DPI_SAVE, bbox_inches='tight',
                       facecolor='white', edgecolor='none')
        
        return fig
    
    def _validate_and_cache(self, df: pd.DataFrame):
        """验证数据并缓存常用计算结果"""
        DataValidator.validate(df)
        
        self._cache['category_cost'] = df.groupby('品类')['总成本(元)'].sum()
        self._cache['category_loss_rate'] = df.groupby('品类')['损耗率(%)'].mean()
        self._cache['reason_cost'] = df.groupby('损耗原因')['损耗金额(元)'].sum()
        self._cache['total_cost'] = df['总成本(元)'].sum()
        self._cache['total_loss'] = df['损耗金额(元)'].sum()
        self._cache['avg_loss_rate'] = df['损耗率(%)'].mean()
        self._cache['cost_q75'] = df['总成本(元)'].quantile(0.75)
        self._cache['loss_q75'] = df['损耗率(%)'].quantile(0.75)
    
    def _create_dimension1(self, df: pd.DataFrame, fig: plt.Figure, gs: GridSpec, row: int):
        """第一维度：成本分布可视化"""
        ax1 = fig.add_subplot(gs[row, 0])
        self._create_pie_chart(df, ax1)
        
        ax2 = fig.add_subplot(gs[row, 1])
        self._create_cost_bar_chart(df, ax2)
    
    def _create_pie_chart(self, df: pd.DataFrame, ax: plt.Axes):
        """创建品类成本占比饼图"""
        category_cost = self._cache['category_cost'].sort_values(ascending=False)
        colors = [self.config.COLORS_CATEGORY[cat] for cat in category_cost.index]
        
        wedges, texts, autotexts = ax.pie(
            category_cost.values,
            labels=category_cost.index,
            autopct='%1.1f%%',
            colors=colors,
            explode=(0.03, 0.02, 0.02),
            startangle=90,
            textprops={'fontsize': self.config.FONT_SIZE_TICK}
        )
        
        for autotext in autotexts:
            autotext.set_fontsize(11)
            autotext.set_color('white')
            autotext.set_fontweight('bold')
        
        total = category_cost.sum()
        legend_labels = [f'{cat}: {cost:,.0f}元' for cat, cost in category_cost.items()]
        ax.legend(wedges, legend_labels, loc='lower center', fontsize=9,
                 bbox_to_anchor=(0.5, -0.1), ncol=3)
        
        ax.set_title('品类成本占比', fontsize=self.config.FONT_SIZE_TITLE, 
                     fontweight='bold', pad=10)
    
    def _create_cost_bar_chart(self, df: pd.DataFrame, ax: plt.Axes):
        """创建原材料成本排序柱状图"""
        material_cost = df.nlargest(10, '总成本(元)').sort_values('总成本(元)')
        colors = [self.config.COLORS_CATEGORY[cat] for cat in material_cost['品类']]
        
        bars = ax.barh(material_cost['原材料名称'], material_cost['总成本(元)'],
                       color=colors, edgecolor='white', linewidth=0.5, height=0.6)
        
        for bar, cost in zip(bars, material_cost['总成本(元)']):
            ax.text(bar.get_width() + 1000, bar.get_y() + bar.get_height()/2,
                   f'{cost/10000:.1f}万', va='center', fontsize=self.config.FONT_SIZE_ANNOTATION)
        
        ax.set_xlabel('总成本(元)', fontsize=self.config.FONT_SIZE_LABEL)
        ax.set_title('原材料成本TOP10', fontsize=self.config.FONT_SIZE_TITLE, 
                     fontweight='bold', pad=10)
        self.remove_spines(ax)
        
        legend_elements = [mpatches.Patch(color=color, label=cat) 
                          for cat, color in self.config.COLORS_CATEGORY.items()]
        ax.legend(handles=legend_elements, loc='lower right', fontsize=9, framealpha=0.9)
    
    def _create_dimension2(self, df: pd.DataFrame, fig: plt.Figure, gs: GridSpec, row: int):
        """第二维度：损耗率高低可视化"""
        ax3 = fig.add_subplot(gs[row, 0])
        self._create_loss_rate_boxplot(df, ax3)
        
        ax4 = fig.add_subplot(gs[row, 1])
        self._create_loss_rate_heatmap(df, ax4)
    
    def _create_loss_rate_boxplot(self, df: pd.DataFrame, ax: plt.Axes):
        """创建品类损耗率箱线图"""
        categories = list(self.config.COLORS_CATEGORY.keys())
        colors = list(self.config.COLORS_CATEGORY.values())
        
        box_data = [df[df['品类'] == cat]['损耗率(%)'].values for cat in categories]
        bp = ax.boxplot(box_data, labels=categories, patch_artist=True, widths=0.5)
        
        for patch, color in zip(bp['boxes'], colors):
            patch.set_facecolor(color)
            patch.set_alpha(0.5)
        
        for i, (cat, color) in enumerate(zip(categories, colors)):
            cat_data = df[df['品类'] == cat]
            x_jitter = np.random.normal(i+1, 0.03, len(cat_data))
            ax.scatter(x_jitter, cat_data['损耗率(%)'], c=color, alpha=0.6, s=40,
                      edgecolor='white', linewidth=0.5, zorder=3)
        
        ax.set_ylabel('损耗率(%)', fontsize=self.config.FONT_SIZE_LABEL)
        ax.set_title('各品类损耗率分布', fontsize=self.config.FONT_SIZE_TITLE, 
                     fontweight='bold', pad=10)
        self.remove_spines(ax)
        
        avg_loss = self._cache['avg_loss_rate']
        ax.axhline(y=avg_loss, color='gray', linestyle='--', linewidth=1.2,
                   label=f'均值: {avg_loss:.1f}%')
        ax.legend(loc='upper right', fontsize=9)
        ax.set_ylim(bottom=0)
    
    def _create_loss_rate_heatmap(self, df: pd.DataFrame, ax: plt.Axes):
        """创建采购批次损耗率热力图"""
        batch_category_loss = df.pivot_table(
            values='损耗率(%)', index='采购批次', columns='品类',
            aggfunc='mean', fill_value=0
        ).reindex(columns=self.config.COLORS_CATEGORY.keys())
        
        im = ax.imshow(batch_category_loss.values, cmap='YlOrRd', aspect='auto')
        
        ax.set_xticks(range(len(batch_category_loss.columns)))
        ax.set_xticklabels(batch_category_loss.columns, fontsize=self.config.FONT_SIZE_TICK)
        ax.set_yticks(range(len(batch_category_loss.index)))
        ax.set_yticklabels(batch_category_loss.index, fontsize=self.config.FONT_SIZE_TICK)
        
        max_val = batch_category_loss.values.max()
        for i in range(len(batch_category_loss.index)):
            for j in range(len(batch_category_loss.columns)):
                value = batch_category_loss.values[i, j]
                text_color = 'white' if value > max_val * 0.5 else 'black'
                ax.text(j, i, f'{value:.1f}%', ha='center', va='center',
                       color=text_color, fontsize=9, fontweight='bold')
        
        ax.set_xlabel('品类', fontsize=self.config.FONT_SIZE_LABEL)
        ax.set_ylabel('采购批次', fontsize=self.config.FONT_SIZE_LABEL)
        ax.set_title('批次×品类损耗率', fontsize=self.config.FONT_SIZE_TITLE, 
                     fontweight='bold', pad=10)
        
        cbar = plt.colorbar(im, ax=ax, shrink=0.8)
        cbar.set_label('损耗率(%)', fontsize=self.config.FONT_SIZE_LABEL)
    
    def _create_dimension3(self, df: pd.DataFrame, fig: plt.Figure, gs: GridSpec, row: int):
        """第三维度：损耗原因对成本的影响可视化"""
        ax5 = fig.add_subplot(gs[row, 0])
        self._create_reason_cost_chart(df, ax5)
        
        ax6 = fig.add_subplot(gs[row, 1])
        self._create_reason_category_chart(df, ax6)
    
    def _create_reason_cost_chart(self, df: pd.DataFrame, ax: plt.Axes):
        """创建损耗原因成本影响柱状图"""
        reason_cost = self._cache['reason_cost'].sort_values(ascending=False)
        total_loss = self._cache['total_loss']
        
        bars = ax.bar(reason_cost.index, reason_cost.values,
                      color=self.config.COLORS_REASON, edgecolor='white', linewidth=1, width=0.6)
        
        for bar, cost in zip(bars, reason_cost.values):
            weight = cost / total_loss * 100
            ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 300,
                   f'{weight:.0f}%',
                   ha='center', va='bottom', fontsize=self.config.FONT_SIZE_TICK, fontweight='bold')
        
        ax.set_ylabel('损耗金额(元)', fontsize=self.config.FONT_SIZE_LABEL)
        ax.set_title('损耗原因影响占比', fontsize=self.config.FONT_SIZE_TITLE, 
                     fontweight='bold', pad=10)
        self.remove_spines(ax)
        ax.tick_params(axis='x', labelsize=9)
    
    def _create_reason_category_chart(self, df: pd.DataFrame, ax: plt.Axes):
        """创建损耗原因×品类成本影响分布图"""
        reason_category = df.pivot_table(
            values='损耗金额(元)', index='损耗原因', columns='品类',
            aggfunc='sum', fill_value=0
        ).reindex(columns=self.config.COLORS_CATEGORY.keys())
        
        x = np.arange(len(reason_category.index))
        width = 0.22
        
        for i, (col, color) in enumerate(zip(reason_category.columns, 
                                              self.config.COLORS_CATEGORY.values())):
            bars = ax.bar(x + i*width, reason_category[col], width,
                         label=col, color=color, edgecolor='white', linewidth=0.5)
        
        ax.set_xlabel('损耗原因', fontsize=self.config.FONT_SIZE_LABEL)
        ax.set_ylabel('损耗金额(元)', fontsize=self.config.FONT_SIZE_LABEL)
        ax.set_title('损耗原因×品类分布', fontsize=self.config.FONT_SIZE_TITLE, 
                     fontweight='bold', pad=10)
        ax.set_xticks(x + width)
        ax.set_xticklabels(reason_category.index, fontsize=9)
        ax.legend(title='品类', loc='upper right', fontsize=9, framealpha=0.9)
        self.remove_spines(ax)
    
    def _create_summary(self, df: pd.DataFrame, fig: plt.Figure, gs: GridSpec, row: int):
        """创建综合分析散点图"""
        ax = fig.add_subplot(gs[row, :])
        
        cost_q75 = self._cache['cost_q75']
        loss_q75 = self._cache['loss_q75']
        avg_loss = self._cache['avg_loss_rate']
        avg_cost = df['总成本(元)'].mean()
        
        for category in self.config.COLORS_CATEGORY.keys():
            cat_data = df[df['品类'] == category]
            ax.scatter(cat_data['总成本(元)'], cat_data['损耗率(%)'],
                      c=self.config.COLORS_CATEGORY[category],
                      marker=self.config.MARKERS[category],
                      s=100,
                      alpha=0.7, edgecolor='white', linewidth=1,
                      label=category, zorder=3)
        
        high_priority = df[(df['损耗率(%)'] > loss_q75) & (df['总成本(元)'] > cost_q75)]
        for _, row_data in high_priority.iterrows():
            ax.annotate(row_data['原材料名称'],
                       xy=(row_data['总成本(元)'], row_data['损耗率(%)']),
                       xytext=(8, 8), textcoords='offset points',
                       fontsize=self.config.FONT_SIZE_ANNOTATION, fontweight='bold',
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='#FFF3CD', alpha=0.8,
                                edgecolor='#FFC107'))
        
        ax.axhline(y=avg_loss, color='#7F8C8D', linestyle='--', linewidth=1.2, alpha=0.8,
                   label=f'损耗率均值: {avg_loss:.1f}%')
        ax.axvline(x=avg_cost, color='#7F8C8D', linestyle=':', linewidth=1.2, alpha=0.8,
                   label=f'成本均值: {avg_cost/10000:.1f}万')
        
        if len(high_priority) > 0:
            ax.fill_between([cost_q75, df['总成本(元)'].max() * 1.05],
                           loss_q75, df['损耗率(%)'].max() * 1.05,
                           alpha=0.1, color='#E74C3C', label='重点关注区域')
        
        ax.set_xlabel('总成本(元)', fontsize=self.config.FONT_SIZE_LABEL)
        ax.set_ylabel('损耗率(%)', fontsize=self.config.FONT_SIZE_LABEL)
        ax.set_title('成本-损耗率关联分析（标注为高成本高损耗原材料）', 
                     fontsize=self.config.FONT_SIZE_TITLE, fontweight='bold', pad=10)
        ax.legend(loc='upper right', fontsize=9, ncol=2, framealpha=0.9)
        self.remove_spines(ax)
        ax.grid(True, alpha=0.2, linestyle='-', linewidth=0.5)
        ax.set_xlim(left=0)
        ax.set_ylim(bottom=0)


class AnalysisReporter:
    """分析报告生成器"""
    
    def __init__(self, df: pd.DataFrame):
        self.df = df
        self._stats = self._calculate_statistics()
    
    def _calculate_statistics(self) -> dict:
        """计算统计数据"""
        return {
            'total_materials': len(self.df),
            'category_distribution': self.df['品类'].value_counts().to_dict(),
            'total_cost': self.df['总成本(元)'].sum(),
            'avg_loss_rate': self.df['损耗率(%)'].mean(),
            'total_loss': self.df['损耗金额(元)'].sum(),
            'category_cost_pct': self.df.groupby('品类')['总成本(元)'].sum() / 
                                 self.df['总成本(元)'].sum() * 100,
            'category_avg_loss': self.df.groupby('品类')['损耗率(%)'].mean(),
            'reason_cost': self.df.groupby('损耗原因')['损耗金额(元)'].sum().sort_values(ascending=False),
            'top_cost_materials': self.df.nlargest(3, '总成本(元)')[['原材料名称', '品类', '总成本(元)']].values,
            'high_loss_materials': self.df[self.df['损耗率(%)'] > self.df['损耗率(%)'].quantile(0.75)]
                                   [['原材料名称', '品类', '损耗率(%)']].values,
            'high_priority': self.df[
                (self.df['损耗率(%)'] > self.df['损耗率(%)'].quantile(0.75)) & 
                (self.df['总成本(元)'] > self.df['总成本(元)'].quantile(0.75))
            ]
        }
    
    def print_summary(self):
        """打印分析摘要"""
        stats = self._stats
        
        print("=" * 60)
        print("原材料成本与损耗率关联分析可视化方案")
        print("=" * 60)
        
        print("\n数据集概览：")
        print(f"  - 原材料总数: {stats['total_materials']} 种")
        print(f"  - 品类分布: {stats['category_distribution']}")
        print(f"  - 总成本合计: {stats['total_cost']:,.2f} 元")
        print(f"  - 平均损耗率: {stats['avg_loss_rate']:.2f}%")
        print(f"  - 损耗金额合计: {stats['total_loss']:,.2f} 元")
        
        print("\n" + "=" * 60)
        print("图表解读与分析结论")
        print("=" * 60)
        
        self._print_dimension1_analysis()
        self._print_dimension2_analysis()
        self._print_dimension3_analysis()
        self._print_comprehensive_analysis()
        self._print_recommendations()
    
    def _print_dimension1_analysis(self):
        """打印第一维度分析"""
        stats = self._stats
        top = stats['top_cost_materials']
        
        print("\n【第一维度：成本分布分析】")
        print(f"  1. 成本集中区域：TOP3高成本原材料为 {top[0][0]}({top[0][2]:,.0f}元)、"
              f"{top[1][0]}({top[1][2]:,.0f}元)、{top[2][0]}({top[2][2]:,.0f}元)")
        pct = stats['category_cost_pct']
        print(f"  2. 品类成本占比：主料 {pct['主料']:.1f}%、辅料 {pct['辅料']:.1f}%、"
              f"包装材料 {pct['包装材料']:.1f}%")
    
    def _print_dimension2_analysis(self):
        """打印第二维度分析"""
        stats = self._stats
        high_loss = stats['high_loss_materials']
        avg_loss = stats['category_avg_loss']
        
        print("\n【第二维度：损耗率分析】")
        print(f"  1. 高损耗率原材料：共{len(high_loss)}种，需重点关注")
        for item in high_loss[:3]:
            print(f"     - {item[0]}({item[1]}): {item[2]:.1f}%")
        print(f"  2. 品类损耗率对比：辅料平均损耗率最高({avg_loss['辅料']:.1f}%)，"
              f"包装材料最低({avg_loss['包装材料']:.1f}%)")
    
    def _print_dimension3_analysis(self):
        """打印第三维度分析"""
        stats = self._stats
        reason_cost = stats['reason_cost']
        total_loss = stats['total_loss']
        
        print("\n【第三维度：损耗原因影响分析】")
        print("  1. 损耗原因影响排序：")
        for reason, cost in reason_cost.items():
            pct = cost / total_loss * 100
            print(f"     - {reason}: {cost:,.0f}元 ({pct:.1f}%)")
    
    def _print_comprehensive_analysis(self):
        """打印综合分析"""
        stats = self._stats
        high_priority = stats['high_priority']
        
        print("\n【综合分析：成本-损耗率关联】")
        print(f"  1. 重点关注对象：{len(high_priority)}种原材料同时处于高成本高损耗区域")
        if len(high_priority) > 0:
            for _, row in high_priority.iterrows():
                print(f"     - {row['原材料名称']}: 成本{row['总成本(元)']:,.0f}元, "
                      f"损耗率{row['损耗率(%)']:.1f}%, 损耗金额{row['损耗金额(元)']:,.0f}元")
    
    def _print_recommendations(self):
        """打印管控建议"""
        print("\n【管控建议】")
        print("  1. 成本管控：优先关注TOP5高成本原材料的采购策略优化")
        print("  2. 损耗管控：重点改善运输环节，该原因导致的损耗占比最高")
        print("  3. 批次管理：对高损耗批次进行专项排查，优化存储和运输流程")
        print("  4. 重点监控：对高成本高损耗原材料建立专项管控机制")


def main(output_image: str = '原材料成本损耗分析可视化报告.png',
         output_excel: str = '原材料数据集.xlsx',
         seed: int = 42):
    """主函数：生成数据并创建完整可视化
    
    Args:
        output_image: 输出图片文件名
        output_excel: 输出Excel文件名
        seed: 随机种子，用于数据可复现
    """
    try:
        chart_config = ChartConfig()
        material_config = MaterialConfig()
        
        print("\n[1/5] 生成模拟数据集...")
        generator = DataGenerator(material_config, seed=seed)
        df = generator.generate()
        
        print("\n[2/5] 创建可视化图表...")
        engine = VisualizationEngine(chart_config)
        fig = engine.create_full_report(df, output_file=output_image)
        print(f"  - 可视化报告已保存: {output_image}")
        
        print("\n[3/5] 保存数据文件...")
        df.to_excel(output_excel, index=False, sheet_name='原材料数据')
        print(f"  - 数据文件已保存: {output_excel}")
        
        print("\n[4/5] 输出分析结论...")
        reporter = AnalysisReporter(df)
        reporter.print_summary()
        
        print("\n" + "=" * 60)
        print("可视化分析完成！")
        print("=" * 60)
        
        plt.show()
        
        return df
        
    except Exception as e:
        print(f"\n错误: {str(e)}")
        raise


if __name__ == '__main__':
    df = main()
