# DonyanUtils/task_runner.py
import concurrent.futures
import time
import threading

class ProgressTracker:
    """并发任务的简单进度跟踪器。"""
    def __init__(self, total_tasks):
        self.total_tasks = total_tasks
        self.completed_tasks = 0
        self.failed_tasks = 0
        self.lock = threading.Lock()
        self.start_time = time.monotonic()

    def task_done(self, success=True):
        with self.lock:
            if success:
                self.completed_tasks += 1
            else:
                self.failed_tasks += 1
            
            processed = self.completed_tasks + self.failed_tasks
            elapsed_time = time.monotonic() - self.start_time
            progress_percent = (processed / self.total_tasks) * 100 if self.total_tasks > 0 else 0
            
            print(
                f"\rProgress: {processed}/{self.total_tasks} ({progress_percent:.2f}%) | "
                f"Success: {self.completed_tasks} | Failed: {self.failed_tasks} | "
                f"时间: {elapsed_time:.2f}s",
                end=""
            )
            if processed == self.total_tasks:
                print() # 在结尾添加换行符

    def get_summary(self):
        elapsed_time = time.monotonic() - self.start_time
        return (f"总计: {self.total_tasks}, 成功: {self.completed_tasks}, 失败: {self.failed_tasks}, "
                f"耗时: {elapsed_time:.2f}s")


def run_concurrently(tasks_data, task_function, max_workers=None, use_processes=False, show_progress=True):
    """
    在任务数据列表上并发运行给定的任务函数。

    Args:
        tasks_data (list): 数据项列表，每个项都将作为参数传递给task_function。
                           如果task_function需要多个参数，tasks_data中的每个项
                           应该是一个元组或字典以便解包。
        task_function (callable): 为每个任务执行的函数。
        max_workers (int, optional): 最大线程/进程数。默认为None（Python的默认值）。
        use_processes (bool, optional): 如果为True，使用ProcessPoolExecutor，否则使用ThreadPoolExecutor。默认为False。
        show_progress (bool, optional): 如果为True，显示进度。默认为True。

    Returns:
        list: 来自task_function的结果列表，按tasks_data的顺序排列。
              如果任务失败，其结果将是异常对象。
    """
    if not tasks_data:
        return []

    results = [None] * len(tasks_data)
    progress_tracker = ProgressTracker(len(tasks_data)) if show_progress else None

    Executor = concurrent.futures.ProcessPoolExecutor if use_processes else concurrent.futures.ThreadPoolExecutor

    with Executor(max_workers=max_workers) as executor:
        future_to_index = {}
        for i, task_args in enumerate(tasks_data):
            if isinstance(task_args, tuple):
                future = executor.submit(task_function, *task_args)
            elif isinstance(task_args, dict):
                future = executor.submit(task_function, **task_args)
            else: # 单个参数
                future = executor.submit(task_function, task_args)
            future_to_index[future] = i

        for future in concurrent.futures.as_completed(future_to_index):
            index = future_to_index[future]
            try:
                result = future.result()
                results[index] = result
                if progress_tracker:
                    progress_tracker.task_done(success=True)
            except Exception as e:
                print(f"\n任务 {index} 失败: {e}")
                results[index] = e # 将异常存储为失败任务的结果
                if progress_tracker:
                    progress_tracker.task_done(success=False)
    
    if progress_tracker:
        print(f"\n并发执行完成。摘要: {progress_tracker.get_summary()}")
    return results