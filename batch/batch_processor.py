import threading
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import List, Callable, Any, Dict, Optional

from api.ark_api_utils import RateLimiter
from .config import BatchConfig


class ProgressTracker:
    """进度跟踪器"""
    def __init__(self, total_tasks: int):
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.lock = threading.Lock()
        self.start_time = time.time()
    
    def update_progress(self, success: bool = True):
        """更新进度"""
        with self.lock:
            if success:
                self.completed_tasks += 1
            else:
                self.failed_tasks += 1
            
            total_finished = self.completed_tasks + self.failed_tasks
            progress = (total_finished / self.total_tasks) * 100
            elapsed_time = time.time() - self.start_time
            
            if total_finished > 0:
                avg_time_per_task = elapsed_time / total_finished
                remaining_tasks = self.total_tasks - total_finished
                estimated_remaining_time = avg_time_per_task * remaining_tasks
                
                print(f"📊 进度: {total_finished}/{self.total_tasks} ({progress:.1f}%) "
                      f"✅成功: {self.completed_tasks} | ❌失败: {self.failed_tasks} "
                      f"⏱️预计剩余: {estimated_remaining_time:.1f}秒")
    
    def get_stats(self) -> Dict[str, Any]:
        """获取统计信息"""
        elapsed_time = time.time() - self.start_time
        return {
            'total_tasks': self.total_tasks,
            'completed_tasks': self.completed_tasks,
            'failed_tasks': self.failed_tasks,
            'success_rate': (self.completed_tasks / self.total_tasks * 100) if self.total_tasks > 0 else 0,
            'elapsed_time': elapsed_time,
            'tasks_per_second': self.completed_tasks / elapsed_time if elapsed_time > 0 else 0
        }


def execute_single_task_with_retry(
    task_func: Callable,
    task_data: Any,
    config: BatchConfig,
    rate_limiter: RateLimiter,
    progress_tracker: ProgressTracker
) -> Dict[str, Any]:
    """
    执行单个任务（带重试机制）
    
    Args:
        task_func: 要执行的任务函数
        task_data: 传递给任务函数的数据
        config: 批量处理配置
        rate_limiter: 速率限制器
        progress_tracker: 进度跟踪器
    
    Returns:
        任务执行结果字典
    """
    result = {
        'success': False,
        'data': None,
        'error': None,
        'attempts': 0,
        'task_data': task_data
    }
    
    for attempt in range(config.max_retries):
        try:
            result['attempts'] = attempt + 1
            
            # 速率限制检查
            rate_limiter.wait_if_needed()
            
            # 执行任务（带超时）
            start_time = time.time()
            task_result = task_func(task_data)
            execution_time = time.time() - start_time
            
            # 检查超时
            if execution_time > config.timeout:
                raise TimeoutError(f"任务执行超时: {execution_time:.2f}秒 > {config.timeout}秒")
            
            result['success'] = True
            result['data'] = task_result
            result['execution_time'] = execution_time
            
            progress_tracker.update_progress(success=True)
            return result
            
        except Exception as e:
            result['error'] = str(e)
            
            if attempt < config.max_retries - 1:
                print(f"⚠️ 任务第{attempt + 1}次尝试失败，准备重试: {e}")
                time.sleep(config.retry_delay)
            else:
                print(f"❌ 任务重试{config.max_retries}次后仍失败: {e}")
    
    progress_tracker.update_progress(success=False)
    return result


def parallel_batch_processor(
    tasks: List[Any],
    task_func: Callable[[Any], Any],
    config: Optional[BatchConfig] = None,
    show_progress: bool = True
) -> Dict[str, Any]:
    """
    并行批量处理器
    
    这是一个通用的并行批量处理工具，可以处理任何类型的任务。
    
    Args:
        tasks: 任务列表，每个元素将作为参数传递给task_func
        task_func: 任务处理函数，接收单个任务数据作为参数
        config: 批量处理配置，如果为None则使用默认配置
        show_progress: 是否显示进度信息
    
    Returns:
        包含处理结果和统计信息的字典:
        {
            'results': List[Dict],  # 每个任务的详细结果
            'stats': Dict,          # 统计信息
            'successful_results': List,  # 成功任务的结果数据
            'failed_tasks': List    # 失败任务的信息
        }
    
    Example:
        # 示例1: 批量HTTP请求
        def http_request(url):
            import requests
            response = requests.get(url, timeout=10)
            return response.json()
        
        urls = ['http://api1.com', 'http://api2.com', 'http://api3.com']
        config = BatchConfig(max_workers=5, rate_limit_per_minute=120)
        result = parallel_batch_processor(urls, http_request, config)
        
        # 示例2: 批量文件处理
        def process_file(filepath):
            with open(filepath, 'r') as f:
                return len(f.read())
        
        files = ['file1.txt', 'file2.txt', 'file3.txt']
        result = parallel_batch_processor(files, process_file)
        
        # 示例3: 批量数据转换
        def transform_data(item):
            return item * 2 + 1
        
        numbers = list(range(100))
        result = parallel_batch_processor(numbers, transform_data)
    """
    
    if config is None:
        config = BatchConfig()
    
    if not tasks:
        return {
            'results': [],
            'stats': {'total_tasks': 0, 'completed_tasks': 0, 'failed_tasks': 0},
            'successful_results': [],
            'failed_tasks': []
        }
    
    if show_progress:
        print(f"🚀 开始并行批量处理，任务数: {len(tasks)}")
        print(f"⚡ 配置: 最大并发{config.max_workers} | 速率限制{config.rate_limit_per_minute}/分钟 | 最大重试{config.max_retries}次")
        print("=" * 60)
    
    # 创建进度跟踪器和速率限制器
    progress_tracker = ProgressTracker(len(tasks))
    rate_limiter = RateLimiter(max_requests=config.rate_limit_per_minute, window_seconds=config.rate_limit_window)
    
    all_results = []
    
    # 使用线程池并发执行任务
    with ThreadPoolExecutor(max_workers=config.max_workers) as executor:
        # 提交所有任务
        future_to_task = {}
        for i, task_data in enumerate(tasks):
            # 添加请求延迟，避免过于密集的API调用
            if i > 0 and config.request_delay > 0:
                time.sleep(config.request_delay / config.max_workers)
            
            future = executor.submit(
                execute_single_task_with_retry,
                task_func,
                task_data,
                config,
                rate_limiter,
                progress_tracker
            )
            future_to_task[future] = task_data
        
        # 等待所有任务完成
        for future in as_completed(future_to_task):
            try:
                result = future.result()
                all_results.append(result)
            except Exception as e:
                # 处理未捕获的异常
                task_data = future_to_task[future]
                error_result = {
                    'success': False,
                    'data': None,
                    'error': f"未捕获异常: {str(e)}",
                    'attempts': 0,
                    'task_data': task_data
                }
                all_results.append(error_result)
                progress_tracker.update_progress(success=False)
    
    # 生成最终统计和结果
    stats = progress_tracker.get_stats()
    successful_results = [r['data'] for r in all_results if r['success']]
    failed_tasks = [r for r in all_results if not r['success']]
    
    if show_progress:
        print("=" * 60)
        print(f"🎉 批量处理完成!")
        print(f"📊 统计: 总任务{stats['total_tasks']}个 | ✅成功{stats['completed_tasks']}个 | ❌失败{stats['failed_tasks']}个")
        print(f"📈 成功率: {stats['success_rate']:.1f}%")
        print(f"⏱️ 总耗时: {stats['elapsed_time']:.1f}秒")
        print(f"⚡ 处理速度: {stats['tasks_per_second']:.2f}个/秒")
        print(f"📞 总API调用: {rate_limiter.total_api_calls}次")
        
        if failed_tasks:
            print(f"❌ 失败任务详情:")
            for i, failed_task in enumerate(failed_tasks[:5], 1):  # 只显示前5个失败任务
                print(f"   {i}. 任务: {failed_task['task_data']} | 错误: {failed_task['error']}")
            if len(failed_tasks) > 5:
                print(f"   ... 还有 {len(failed_tasks) - 5} 个失败任务")
    
    return {
        'results': all_results,
        'stats': stats,
        'successful_results': successful_results,
        'failed_tasks': failed_tasks
    }


def simple_parallel_map(tasks: List[Any], task_func: Callable[[Any], Any], max_workers: int = 10) -> List[Any]:
    """
    简化版并行处理器 - 类似于内置map函数的并行版本
    
    Args:
        tasks: 任务列表
        task_func: 处理函数
        max_workers: 最大并发数
    
    Returns:
        处理结果列表（保持与输入相同的顺序）
    
    Example:
        # 简单的并行处理
        numbers = list(range(10))
        results = simple_parallel_map(numbers, lambda x: x ** 2, max_workers=4)
        print(results)  # [0, 1, 4, 9, 16, 25, 36, 49, 64, 81]
    """
    config = BatchConfig(max_workers=max_workers, max_retries=1, rate_limit_per_minute=max_workers * 60)
    result = parallel_batch_processor(tasks, task_func, config, show_progress=False)
    
    # 创建一个从任务数据到结果的映射
    task_map = {str(res['task_data']): res for res in result['results']}

    # 按原始任务顺序构建结果列表
    ordered_results = []
    for task_data in tasks:
        task_result = task_map.get(str(task_data))
        if task_result and task_result['success']:
            ordered_results.append(task_result['data'])
        else:
            ordered_results.append(None)
            
    return ordered_results 