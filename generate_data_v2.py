"""
优化版：原材料数据生成器
使用配置管理，确保数据一致性
"""
import pandas as pd
import numpy as np
import random
from utils import COLOR_CONFIG

# 设置随机种子保证可复现
np.random.seed(42)
random.seed(42)

# 定义原材料数据 - 可通过配置文件扩展
MATERIALS_CONFIG = {
    '主料': [
        ('牛肉', 60, 5.8, 800), ('猪肉', 35, 4.2, 1200), ('鸡肉', 20, 3.5, 1500),
        ('鱼肉', 45, 4.8, 600), ('虾', 70, 6.2, 400), ('面粉', 8, 2.1, 2000),
        ('大米', 6, 1.8, 1800), ('大豆油', 12, 3.2, 1000)
    ],
    '辅料': [
        ('盐', 3, 0.8, 500), ('糖', 5, 1.2, 600), ('酱油', 15, 2.5, 400),
        ('醋', 10, 2.2, 300), ('料酒', 12, 2.8, 350), ('香料', 50, 5.5, 150),
        ('味精', 20, 3.8, 200), ('淀粉', 7, 1.5, 450)
    ],
    '包装材料': [
        ('纸箱', 5, 1.2, 1000), ('塑料袋', 0.5, 0.3, 5000), ('标签', 0.2, 0.05, 10000),
        ('保鲜膜', 2, 0.8, 2000), ('缓冲泡沫', 3, 1.0, 1500), ('胶带', 1, 0.4, 3000)
    ]
}

# 损耗原因配置
LOSS_REASONS = list(COLOR_CONFIG['reason_colors'].keys())  # 与颜色配置保持一致
LOSS_REASON_WEIGHTS = [0.3, 0.35, 0.2, 0.1, 0.05]  # 损耗原因概率分布

# 批次配置
BATCH_NUMBERS = ['B001', 'B002', 'B003', 'B004', 'B005']

# 波动参数配置 - 可根据实际业务调整
VARIATION_CONFIG = {
    'price': {'loc': 1, 'scale': 0.08},       # 价格波动 (loc=mean, scale=std)
    'usage': {'loc': 1, 'scale': 0.12},       # 使用量波动 (loc=mean, scale=std)
    'loss_rate': {'loc': 1, 'scale': 0.25}    # 损耗率波动 (loc=mean, scale=std)
}

# 损耗率限制
LOSS_RATE_LIMITS = {'min': 0.5, 'max': 15}


def generate_material_data():
    """
    生成原材料数据
    
    返回:
        pd.DataFrame: 生成的数据集
    """
    data = []
    
    for category, items in MATERIALS_CONFIG.items():
        for name, base_price, base_loss_rate, base_usage in items:
            for batch in BATCH_NUMBERS:
                # 添加随机波动
                price_variation = np.random.normal(**VARIATION_CONFIG['price'])
                usage_variation = np.random.normal(**VARIATION_CONFIG['usage'])
                loss_rate_variation = np.random.normal(**VARIATION_CONFIG['loss_rate'])
                
                # 计算各项指标，确保在合理范围内
                price = round(base_price * price_variation, 2)
                usage = int(max(1, base_usage * usage_variation))  # 使用量不能为0
                total_cost = round(price * usage, 2)
                
                # 限制损耗率在合理范围
                loss_rate = base_loss_rate * loss_rate_variation
                loss_rate = round(
                    max(LOSS_RATE_LIMITS['min'],
                        min(loss_rate, LOSS_RATE_LIMITS['max'])),
                    2
                )
                
                # 按概率分配损耗原因
                loss_reason = random.choices(LOSS_REASONS, weights=LOSS_REASON_WEIGHTS)[0]
                
                data.append({
                    '原材料名称': name,
                    '品类': category,
                    '采购单价': price,
                    '月使用量': usage,
                    '总成本': total_cost,
                    '损耗率(%)': loss_rate,
                    '损耗原因': loss_reason,
                    '采购批次': batch
                })
    
    # 创建DataFrame
    df = pd.DataFrame(data)
    
    # 添加损耗金额字段
    df['损耗金额'] = round(df['总成本'] * df['损耗率(%)'] / 100, 2)
    
    # 按原材料名称和批次排序
    df = df.sort_values(['原材料名称', '采购批次']).reset_index(drop=True)
    
    return df


def validate_data(df):
    """
    验证生成的数据是否符合预期
    
    参数:
        df (pd.DataFrame): 要验证的数据集
    
    返回:
        bool: 验证是否通过
    """
    # 检查必要列
    required_columns = ['原材料名称', '品类', '采购单价', '月使用量', '总成本', '损耗率(%)', '损耗原因', '采购批次']
    if not all(col in df.columns for col in required_columns):
        print("❌ 数据缺少必要列！")
        return False
    
    # 检查数值范围
    if (df['采购单价'] <= 0).any():
        print("❌ 采购单价存在非正值！")
        return False
    
    if (df['月使用量'] <= 0).any():
        print("❌ 月使用量存在非正值！")
        return False
    
    if (df['损耗率(%)'] < LOSS_RATE_LIMITS['min']).any() or \
       (df['损耗率(%)'] > LOSS_RATE_LIMITS['max']).any():
        print("❌ 损耗率超出合理范围！")
        return False
    
    # 检查品类完整性
    if not all(cat in MATERIALS_CONFIG.keys() for cat in df['品类'].unique()):
        print("❌ 存在未定义的品类！")
        return False
    
    # 检查损耗原因完整性
    if not all(reason in LOSS_REASONS for reason in df['损耗原因'].unique()):
        print("❌ 存在未定义的损耗原因！")
        return False
    
    print("✅ 数据验证通过！")
    return True


def main():
    """主函数"""
    print("开始生成原材料数据...")
    
    # 生成数据
    df = generate_material_data()
    
    # 验证数据
    if validate_data(df):
        # 保存到CSV
        output_path = '原材料数据.csv'
        df.to_csv(output_path, index=False, encoding='utf-8-sig')
        
        print(f"\n数据生成完成！共生成 {len(df)} 条记录")
        print(f"数据已保存至: {output_path}")
        
        # 显示基本统计
        print("\n" + "="*60)
        print("数据基本统计信息")
        print("="*60)
        print(df.describe().round(2))
        print("="*60)
        
        # 显示数据预览
        print("\n数据预览:")
        print(df[['原材料名称', '品类', '采购单价', '月使用量', '总成本', '损耗率(%)', '损耗原因', '采购批次']].head(10))
        
        return df
    else:
        print("❌ 数据验证失败！")
        return None


if __name__ == '__main__':
    main()
