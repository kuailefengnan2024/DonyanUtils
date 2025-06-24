import sys
import os
import time

# 将项目根目录添加到Python路径中
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from donyan_utils.config import BatchConfig
from donyan_utils.batch_processor import parallel_batch_processor, simple_parallel_map

# 使用示例和测试代码
if __name__ == "__main__":
    # 示例1: 模拟API调用
    def mock_api_call(task_id):
        import random
        time.sleep(random.uniform(0.1, 0.5))  # 模拟网络延迟
        
        # 模拟10%的失败率
        if random.random() < 0.1:
            raise Exception(f"API调用失败 - 任务{task_id}")
        
        return f"任务{task_id}完成，结果: {task_id * 100}"
    
    print("🧪 测试示例1: 模拟API批量调用")
    tasks = list(range(1, 21))  # 20个任务
    config = BatchConfig(
        max_workers=5,
        rate_limit_per_minute=300,
        max_retries=3
    )
    
    result = parallel_batch_processor(tasks, mock_api_call, config)
    print(f"成功结果数量: {len(result['successful_results'])}")
    print(f"失败任务数量: {len(result['failed_tasks'])}")
    
    print("\n" + "="*60)
    
    # 示例2: 简单的数学计算
    def square_number(n):
        return n ** 2
    
    print("🧪 测试示例2: 简单并行计算")
    numbers = list(range(10))
    squared_results = simple_parallel_map(numbers, square_number, max_workers=4)
    print(f"原始数字: {numbers}")
    print(f"平方结果: {squared_results}") 