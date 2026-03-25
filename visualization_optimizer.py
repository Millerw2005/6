"""
优化版：原材料成本与损耗率关联分析可视化
模块化设计，消除代码重复
"""
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np

# 导入公共工具模块
from utils import (
    setup_chinese_font, load_data,
    aggregate_by_category, aggregate_by_material,
    aggregate_by_batch, aggregate_by_reason,
    aggregate_category_reason,
    add_bar_labels, add_bar_labels_percent, add_bar_labels_currency,
    create_category_legend, add_text_box,
    calculate_concentration, identify_high_loss_materials,
    COLOR_CONFIG, FONT_CONFIG, THRESHOLD_CONFIG
)

class MaterialCostLossAnalyzer:
    """
    原材料成本与损耗分析器类
    统一管理三个维度的可视化
    """
    
    def __init__(self, data_path='原材料数据.csv'):
        """
        初始化分析器
        
        参数:
            data_path (str): 数据文件路径
        """
        # 设置字体
        setup_chinese_font()
        
        # 加载数据
        self.df = load_data(data_path)
        
        # 预聚合数据
        self._aggregate_data()
        
        print(f"分析器初始化完成，共加载 {len(self.df)} 条记录")
    
    def _aggregate_data(self):
        """预聚合各类数据"""
        self.category_summary = aggregate_by_category(self.df)
        self.material_summary = aggregate_by_material(self.df)
        self.batch_summary = aggregate_by_batch(self.df)
        self.reason_summary = aggregate_by_reason(self.df)
        self.category_reason = aggregate_category_reason(self.df)
        
        # 获取Top 10高损耗原材料用于热力图
        self.top_materials_by_loss = (
            self.df.groupby('原材料名称')['损耗金额']
            .sum()
            .sort_values(ascending=False)
            .head(10)
            .index
        )
    
    def plot_cost_distribution(self, save_path='1_成本分布可视化.png', show=True):
        """
        第一维度：成本分布可视化
        
        参数:
            save_path (str): 图片保存路径
            show (bool): 是否显示图表
        """
        fig = plt.figure(figsize=(20, 12))
        fig.suptitle(
            '第一维度：成本分布可视化',
            fontsize=FONT_CONFIG['super_title_size'],
            fontweight='bold',
            y=0.98
        )
        
        # 获取品类颜色列表
        cat_colors = [COLOR_CONFIG['category_colors'][cat] for cat in self.category_summary['品类']]
        
        # 1. 饼图：品类成本占比
        ax1 = plt.subplot(2, 2, 1)
        wedges, texts, autotexts = ax1.pie(
            self.category_summary['总成本'],
            labels=self.category_summary['品类'],
            colors=cat_colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': FONT_CONFIG['label_size']}
        )
        ax1.set_title('图1-1：各品类总成本占比', fontsize=FONT_CONFIG['title_size'], pad=20)
        plt.setp(autotexts, size=FONT_CONFIG['label_size'], weight='bold')
        
        # 添加数据表格
        total_cost = self.category_summary['总成本'].sum()
        table_data = [
            [row['品类'], f"¥{row['总成本']:,.2f}", f"{row['总成本']/total_cost*100:.1f}%"]
            for _, row in self.category_summary.iterrows()
        ]
        
        table = ax1.table(
            cellText=table_data,
            colLabels=['品类', '总成本', '占比'],
            loc='bottom',
            cellLoc='center',
            bbox=[0, -0.4, 1, 0.3]
        )
        table.auto_set_font_size(False)
        table.set_fontsize(11)
        
        # 2. 柱状图：各品类总成本对比
        ax2 = plt.subplot(2, 2, 2)
        bars = ax2.bar(
            self.category_summary['品类'],
            self.category_summary['总成本'],
            color=cat_colors,
            edgecolor='black',
            alpha=0.8
        )
        ax2.set_title('图1-2：各品类总成本对比', fontsize=FONT_CONFIG['title_size'], pad=20)
        ax2.set_ylabel('总成本（元）', fontsize=FONT_CONFIG['label_size'])
        ax2.tick_params(axis='x', labelsize=FONT_CONFIG['label_size'])
        add_bar_labels_currency(ax2, fontsize=11)
        
        # 3. 柱状图：单种原材料成本排序
        ax3 = plt.subplot(2, 1, 2)
        material_sorted = self.material_summary.sort_values('平均总成本', ascending=False).reset_index(drop=True)
        bar_colors = [COLOR_CONFIG['category_colors'][cat] for cat in material_sorted['品类']]
        
        bars = ax3.bar(
            material_sorted['原材料名称'],
            material_sorted['平均总成本'],
            color=bar_colors,
            edgecolor='black',
            alpha=0.8
        )
        ax3.set_title('图1-3：单种原材料平均月成本排序', fontsize=FONT_CONFIG['title_size'], pad=20)
        ax3.set_ylabel('平均月总成本（元）', fontsize=FONT_CONFIG['label_size'])
        ax3.tick_params(axis='x', rotation=45, labelsize=FONT_CONFIG['tick_size'])
        add_bar_labels_currency(ax3, fontsize=9)
        
        # 添加品类图例
        create_category_legend(ax3)
        
        # 添加成本集中度分析
        concentration = calculate_concentration(self.material_summary)
        add_text_box(
            ax3,
            f'成本集中度分析：\nTop 3原材料占总成本的 {concentration:.1f}%',
            facecolor='yellow'
        )
        
        # 调整布局
        plt.tight_layout(rect=[0, 0, 1, 0.95])
        
        # 保存图片
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"第一维度可视化图表已保存：{save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
    
    def plot_loss_rate_analysis(self, save_path='2_损耗率高低可视化.png', show=True):
        """
        第二维度：损耗率高低可视化
        
        参数:
            save_path (str): 图片保存路径
            show (bool): 是否显示图表
        """
        fig = plt.figure(figsize=(24, 18))
        fig.suptitle(
            '第二维度：损耗率高低可视化',
            fontsize=FONT_CONFIG['super_title_size'],
            fontweight='bold',
            y=0.95
        )
        
        # 1. 柱状图：各品类平均损耗率对比
        ax1 = plt.subplot(3, 2, 1)
        cat_colors = [COLOR_CONFIG['category_colors'][cat] for cat in self.category_summary['品类']]
        bars = ax1.bar(
            self.category_summary['品类'],
            self.category_summary['损耗率(%)'],
            color=cat_colors,
            edgecolor='black',
            alpha=0.8
        )
        ax1.set_title('图2-1：各品类平均损耗率对比', fontsize=FONT_CONFIG['title_size'], pad=20)
        ax1.set_ylabel('平均损耗率(%)', fontsize=FONT_CONFIG['label_size'])
        ax1.set_ylim(0, self.category_summary['损耗率(%)'].max() * 1.2)
        add_bar_labels_percent(ax1, fontsize=12)
        
        # 2. 箱线图：各品类损耗率分布区间
        ax2 = plt.subplot(3, 2, 2)
        box_data = []
        box_labels = []
        for category in self.df['品类'].unique():
            box_data.append(self.df[self.df['品类'] == category]['损耗率(%)'].values)
            box_labels.append(category)
        
        bp = ax2.boxplot(
            box_data,
            tick_labels=box_labels,  # 使用新的参数名避免警告
            patch_artist=True,
            medianprops={'color': 'red', 'linewidth': 2},
            flierprops={'marker': 'o', 'markerfacecolor': 'red', 'markersize': 8}
        )
        
        # 设置箱体颜色
        for patch, color in zip(bp['boxes'], [COLOR_CONFIG['category_colors'][cat] for cat in box_labels]):
            patch.set_facecolor(color)
            patch.set_alpha(0.7)
        
        ax2.set_title('图2-2：各品类损耗率分布区间', fontsize=FONT_CONFIG['title_size'], pad=20)
        ax2.set_ylabel('损耗率(%)', fontsize=FONT_CONFIG['label_size'])
        ax2.grid(axis='y', linestyle='--', alpha=0.7)
        
        # 3. 柱状图：各采购批次平均损耗率
        ax3 = plt.subplot(3, 2, 3)
        bars = ax3.bar(
            self.batch_summary['采购批次'],
            self.batch_summary['损耗率(%)'],
            color=COLOR_CONFIG['batch_colors'],
            edgecolor='black',
            alpha=0.8
        )
        ax3.set_title('图2-3：各采购批次平均损耗率', fontsize=FONT_CONFIG['title_size'], pad=20)
        ax3.set_ylabel('平均损耗率(%)', fontsize=FONT_CONFIG['label_size'])
        ax3.set_xlabel('采购批次', fontsize=FONT_CONFIG['label_size'])
        ax3.set_ylim(0, self.batch_summary['损耗率(%)'].max() * 1.2)
        add_bar_labels_percent(ax3, fontsize=11)
        
        # 4. 散点图：损耗率与损耗金额的关系
        ax4 = plt.subplot(3, 2, 4)
        for category in self.df['品类'].unique():
            cat_data = self.material_summary[self.material_summary['品类'] == category]
            ax4.scatter(
                cat_data['平均损耗率(%)'],
                cat_data['平均损耗金额'],
                color=COLOR_CONFIG['category_colors'][category],
                s=150,
                alpha=0.7,
                edgecolor='black',
                label=category
            )
        ax4.set_title('图2-4：损耗率与损耗金额的关系', fontsize=FONT_CONFIG['title_size'], pad=20)
        ax4.set_xlabel('平均损耗率(%)', fontsize=FONT_CONFIG['label_size'])
        ax4.set_ylabel('平均月损耗金额（元）', fontsize=FONT_CONFIG['label_size'])
        ax4.legend(fontsize=FONT_CONFIG['label_size'])
        ax4.grid(True, linestyle='--', alpha=0.7)
        
        # 5. 柱状图：高损耗率原材料Top15
        ax5 = plt.subplot(3, 1, 3)
        loss_sorted = self.material_summary.sort_values('平均损耗率(%)', ascending=False).head(15).reset_index(drop=True)
        bar_colors = [COLOR_CONFIG['category_colors'][cat] for cat in loss_sorted['品类']]
        
        bars = ax5.bar(
            loss_sorted['原材料名称'],
            loss_sorted['平均损耗率(%)'],
            color=bar_colors,
            edgecolor='black',
            alpha=0.8
        )
        ax5.set_title('图2-5：高损耗率原材料Top15', fontsize=FONT_CONFIG['title_size'], pad=20)
        ax5.set_ylabel('平均损耗率(%)', fontsize=FONT_CONFIG['label_size'])
        ax5.tick_params(axis='x', rotation=45, labelsize=FONT_CONFIG['tick_size'])
        
        # 添加数据标签和异常标注
        for i, bar in enumerate(bars):
            height = bar.get_height()
            ax5.text(
                bar.get_x() + bar.get_width()/2.,
                height,
                f'{height:.2f}%',
                ha='center',
                va='bottom',
                fontsize=FONT_CONFIG['tick_size']
            )
            
            # 标注高损耗异常
            if height > THRESHOLD_CONFIG['danger_loss_rate']:
                ax5.text(
                    bar.get_x() + bar.get_width()/2.,
                    height + 0.3,
                    '高损耗',  # 使用文字替代emoji避免字体问题
                    ha='center',
                    va='bottom',
                    fontsize=9,
                    color='red',
                    fontweight='bold'
                )
        
        # 添加品类图例
        create_category_legend(ax5)
        
        # 添加损耗率基准线
        ax5.axhline(
            y=THRESHOLD_CONFIG['warning_loss_rate'],
            color='orange',
            linestyle='--',
            alpha=0.7,
            label=f'警戒阈值({THRESHOLD_CONFIG["warning_loss_rate"]}%)'
        )
        ax5.axhline(
            y=THRESHOLD_CONFIG['danger_loss_rate'],
            color='red',
            linestyle='--',
            alpha=0.7,
            label=f'危险阈值({THRESHOLD_CONFIG["danger_loss_rate"]}%)'
        )
        
        # 添加损耗管控重点提示
        add_text_box(
            ax5,
            f'损耗管控重点提示：\n- 损耗率 > {THRESHOLD_CONFIG["warning_loss_rate"]}% 需要关注\n'
            f'- 损耗率 > {THRESHOLD_CONFIG["danger_loss_rate"]}% 需要立即整改',
            facecolor='yellow'
        )
        
        # 调整布局
        plt.tight_layout(rect=[0, 0, 1, 0.93])
        
        # 保存图片
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"第二维度可视化图表已保存：{save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
    
    def plot_loss_reason_analysis(self, save_path='3_损耗原因影响可视化.png', show=True):
        """
        第三维度：损耗原因对成本的影响可视化
        
        参数:
            save_path (str): 图片保存路径
            show (bool): 是否显示图表
        """
        fig = plt.figure(figsize=(24, 20))
        fig.suptitle(
            '第三维度：损耗原因对成本的影响可视化',
            fontsize=FONT_CONFIG['super_title_size'],
            fontweight='bold',
            y=0.95
        )
        
        # 1. 饼图：各损耗原因的损耗金额占比
        ax1 = plt.subplot(3, 2, 1)
        colors = [COLOR_CONFIG['reason_colors'][reason] for reason in self.reason_summary['损耗原因']]
        wedges, texts, autotexts = ax1.pie(
            self.reason_summary['损耗金额'],
            labels=self.reason_summary['损耗原因'],
            colors=colors,
            autopct='%1.1f%%',
            startangle=90,
            textprops={'fontsize': 11}
        )
        ax1.set_title('图3-1：各损耗原因损耗金额占比', fontsize=FONT_CONFIG['title_size'], pad=20)
        plt.setp(autotexts, size=11, weight='bold')
        
        # 2. 柱状图：各损耗原因对应的总损耗金额
        ax2 = plt.subplot(3, 2, 2)
        bars = ax2.bar(
            self.reason_summary['损耗原因'],
            self.reason_summary['损耗金额'],
            color=colors,
            edgecolor='black',
            alpha=0.8
        )
        ax2.set_title('图3-2：各损耗原因总损耗金额', fontsize=FONT_CONFIG['title_size'], pad=20)
        ax2.set_ylabel('总损耗金额（元）', fontsize=FONT_CONFIG['label_size'])
        ax2.tick_params(axis='x', rotation=30)
        add_bar_labels_currency(ax2, fontsize=11)
        
        # 3. 堆叠柱状图：各品类下不同损耗原因的损耗金额
        ax3 = plt.subplot(3, 2, 3)
        categories = self.df['品类'].unique()
        reasons = self.reason_summary['损耗原因'].tolist()
        stack_data = np.zeros((len(categories), len(reasons)))
        
        for i, cat in enumerate(categories):
            for j, reason in enumerate(reasons):
                mask = (self.category_reason['品类'] == cat) & (self.category_reason['损耗原因'] == reason)
                if mask.any():
                    stack_data[i, j] = self.category_reason[mask]['损耗金额'].values[0]
        
        bottom = np.zeros(len(categories))
        for j, reason in enumerate(reasons):
            ax3.bar(
                categories,
                stack_data[:, j],
                bottom=bottom,
                color=COLOR_CONFIG['reason_colors'][reason],
                edgecolor='black',
                alpha=0.8,
                label=reason
            )
            bottom += stack_data[:, j]
        
        ax3.set_title('图3-3：各品类下不同损耗原因的损耗金额', fontsize=FONT_CONFIG['title_size'], pad=20)
        ax3.set_ylabel('损耗金额（元）', fontsize=FONT_CONFIG['label_size'])
        ax3.legend(title='损耗原因', bbox_to_anchor=(1.05, 1), loc='upper left')
        
        # 添加总数标签
        for i, cat in enumerate(categories):
            total = stack_data[i, :].sum()
            ax3.text(
                i,
                total,
                f'¥{total:,.0f}',
                ha='center',
                va='bottom',
                fontsize=11,
                fontweight='bold'
            )
        
        # 4. 热力图：损耗原因与原材料的关联
        ax4 = plt.subplot(3, 2, 4)
        material_reason = (
            self.df[self.df['原材料名称'].isin(self.top_materials_by_loss)]
            .groupby(['原材料名称', '损耗原因'])
            .agg({'损耗金额': 'sum'})
            .reset_index()
        )
        
        # 准备热力图数据
        heatmap_data = material_reason.pivot(
            index='原材料名称',
            columns='损耗原因',
            values='损耗金额'
        ).fillna(0)
        
        # 按总损耗金额排序
        heatmap_data = heatmap_data.loc[heatmap_data.sum(axis=1).sort_values(ascending=False).index]
        
        sns.heatmap(
            heatmap_data,
            annot=True,
            fmt=',.0f',
            cmap=COLOR_CONFIG['heatmap_cmap'],
            ax=ax4,
            cbar_kws={'label': '损耗金额（元）'},
            annot_kws={'size': FONT_CONFIG['annotation_size']}
        )
        ax4.set_title('图3-4：高损耗原材料与损耗原因关联热力图', fontsize=FONT_CONFIG['title_size'], pad=20)
        ax4.set_xlabel('损耗原因', fontsize=FONT_CONFIG['label_size'])
        ax4.set_ylabel('原材料名称', fontsize=FONT_CONFIG['label_size'])
        ax4.tick_params(axis='x', rotation=45)
        
        # 5. 散点图：成本与损耗金额的关联
        ax5 = plt.subplot(3, 1, 3)
        for reason in reasons:
            reason_data = self.df[self.df['损耗原因'] == reason]
            ax5.scatter(
                reason_data['总成本'],
                reason_data['损耗金额'],
                color=COLOR_CONFIG['reason_colors'][reason],
                s=100,
                alpha=0.6,
                edgecolor='black',
                label=reason
            )
        
        # 添加趋势线
        z = np.polyfit(self.df['总成本'], self.df['损耗金额'], 1)
        p = np.poly1d(z)
        x_trend = np.linspace(self.df['总成本'].min(), self.df['总成本'].max(), 100)
        ax5.plot(
            x_trend,
            p(x_trend),
            "r--",
            alpha=0.8,
            label=f'趋势线 (y={z[0]:.3f}x+{z[1]:.0f})'
        )
        
        ax5.set_title('图3-5：总成本与损耗金额关联分析', fontsize=FONT_CONFIG['title_size'], pad=20)
        ax5.set_xlabel('总成本（元）', fontsize=FONT_CONFIG['label_size'])
        ax5.set_ylabel('损耗金额（元）', fontsize=FONT_CONFIG['label_size'])
        ax5.legend(title='损耗原因', bbox_to_anchor=(1.02, 1), loc='upper left', fontsize=11)
        ax5.grid(True, linestyle='--', alpha=0.7)
        
        # 添加相关性分析
        corr = self.df['总成本'].corr(self.df['损耗金额'])
        add_text_box(
            ax5,
            f'相关性分析：\n总成本与损耗金额的相关系数: {corr:.3f}\n'
            f'（系数>{THRESHOLD_CONFIG["strong_correlation"]}表示强正相关）',
            y=0.98,
            facecolor='lightblue'
        )
        
        # 添加影响权重总结
        reason_weight_text = '损耗原因影响权重总结：\n' + '\n'.join(
            [f'- {row["损耗原因"]}: {row["损耗金额占比(%)"]:.1f}%'
             for _, row in self.reason_summary.iterrows()]
        )
        add_text_box(
            ax5,
            reason_weight_text,
            y=0.78,
            facecolor='lightgreen',
            fontsize=10
        )
        
        # 调整布局
        plt.tight_layout(rect=[0, 0, 0.92, 0.93])
        
        # 保存图片
        plt.savefig(save_path, dpi=300, bbox_inches='tight')
        print(f"第三维度可视化图表已保存：{save_path}")
        
        if show:
            plt.show()
        else:
            plt.close()
    
    def generate_all_visualizations(self, show=False):
        """
        生成所有可视化图表
        
        参数:
            show (bool): 是否显示图表
        """
        print("\n开始生成可视化图表...")
        self.plot_cost_distribution(show=show)
        self.plot_loss_rate_analysis(show=show)
        self.plot_loss_reason_analysis(show=show)
        print("\n所有可视化图表生成完成！")
    
    def generate_summary_report(self):
        """生成分析摘要报告"""
        print("\n" + "="*60)
        print("原材料成本与损耗分析摘要报告")
        print("="*60)
        
        # 基本统计
        print(f"\n📊 数据概览:")
        print(f"  - 原材料种类: {self.df['原材料名称'].nunique()} 种")
        print(f"  - 采购批次: {self.df['采购批次'].nunique()} 个")
        print(f"  - 总记录数: {len(self.df)} 条")
        
        # 成本分析
        total_cost = self.category_summary['总成本'].sum()
        print(f"\n💰 成本分析:")
        print(f"  - 月总成本: ¥{total_cost:,.2f}")
        for _, row in self.category_summary.iterrows():
            print(f"  - {row['品类']}: ¥{row['总成本']:,.2f} ({row['总成本']/total_cost*100:.1f}%)")
        
        # 损耗分析
        total_loss = self.reason_summary['损耗金额'].sum()
        avg_loss_rate = self.df['损耗率(%)'].mean()
        print(f"\n📉 损耗分析:")
        print(f"  - 月总损耗金额: ¥{total_loss:,.2f}")
        print(f"  - 平均损耗率: {avg_loss_rate:.2f}%")
        print(f"  - 损耗率范围: {self.df['损耗率(%)'].min():.2f}% ~ {self.df['损耗率(%)'].max():.2f}%")
        
        # 损耗原因
        print(f"\n🔍 损耗原因分布:")
        for _, row in self.reason_summary.iterrows():
            print(f"  - {row['损耗原因']}: ¥{row['损耗金额']:,.2f} ({row['损耗金额占比(%)']:.1f}%)")
        
        # 高损耗预警
        high_loss_materials = identify_high_loss_materials(
            self.material_summary,
            THRESHOLD_CONFIG['danger_loss_rate']
        )
        if not high_loss_materials.empty:
            print(f"\n⚠️  高损耗预警 (损耗率 > {THRESHOLD_CONFIG['danger_loss_rate']}%):")
            for _, row in high_loss_materials.iterrows():
                print(f"  - {row['原材料名称']} ({row['品类']}): {row['平均损耗率(%)']:.2f}%")
        
        # 成本集中度
        concentration = calculate_concentration(self.material_summary)
        print(f"\n📈 成本集中度:")
        print(f"  - Top 3原材料占总成本的 {concentration:.1f}%")
        
        # 相关性
        corr = self.df['总成本'].corr(self.df['损耗金额'])
        corr_desc = "强正相关" if corr > THRESHOLD_CONFIG['strong_correlation'] else "中等相关" if corr > 0.5 else "弱相关"
        print(f"\n🔗 相关性分析:")
        print(f"  - 总成本与损耗金额的相关系数: {corr:.3f} ({corr_desc})")
        
        print("\n" + "="*60)
        print("报告生成完毕")
        print("="*60 + "\n")


def main():
    """主函数"""
    try:
        # 创建分析器实例
        analyzer = MaterialCostLossAnalyzer()
        
        # 生成摘要报告
        analyzer.generate_summary_report()
        
        # 生成所有可视化图表
        analyzer.generate_all_visualizations(show=False)
        
    except Exception as e:
        print(f"❌ 错误: {e}")
        raise


if __name__ == '__main__':
    main()
