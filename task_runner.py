# DonyanUtils/task_runner.py
import concurrent.futures
import time
import threading

class ProgressTracker:
    """Simple progress tracker for concurrent tasks."""
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
                f"Time: {elapsed_time:.2f}s",
                end=""
            )
            if processed == self.total_tasks:
                print() # Newline at the end

    def get_summary(self):
        elapsed_time = time.monotonic() - self.start_time
        return (f"Total: {self.total_tasks}, Success: {self.completed_tasks}, Failed: {self.failed_tasks}, "
                f"Duration: {elapsed_time:.2f}s")


def run_concurrently(tasks_data, task_function, max_workers=None, use_processes=False, show_progress=True):
    """
    Runs a given task_function concurrently over a list of tasks_data.

    Args:
        tasks_data (list): A list of data items, each will be passed as an argument to task_function.
                           If task_function expects multiple arguments, each item in tasks_data
                           should be a tuple or dict to be unpacked.
        task_function (callable): The function to execute for each task.
        max_workers (int, optional): Maximum number of threads/processes. Defaults to None (Python's default).
        use_processes (bool, optional): If True, use ProcessPoolExecutor, else ThreadPoolExecutor. Defaults to False.
        show_progress (bool, optional): If True, display progress. Defaults to True.

    Returns:
        list: A list of results from a_function, in the order of tasks_data.
              If a task fails, its result will be the exception object.
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
            else: # Single argument
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
                print(f"\nTask {index} failed: {e}")
                results[index] = e # Store exception as result for failed tasks
                if progress_tracker:
                    progress_tracker.task_done(success=False)
    
    if progress_tracker:
        print(f"\nConcurrent execution finished. Summary: {progress_tracker.get_summary()}")
    return results