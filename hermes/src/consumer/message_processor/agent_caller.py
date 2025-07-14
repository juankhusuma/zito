import time
import traceback

class AgentCaller:
    @staticmethod
    def retry_with_exponential_backoff(
        func,
        max_attempts=3,
        base_delay=1,
        max_delay=10,
        *args,
        **kwargs,
    ):
        for attempt in range(max_attempts):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                if attempt == max_attempts - 1:
                    print(f"Final attempt failed for {func.__name__}: {str(e)}")
                    raise e

                delay = min(base_delay * (2**attempt), max_delay)
                print(
                    f"Attempt {attempt + 1} failed for {func.__name__}: {str(e)}. Retrying in {delay}s..."
                )
                time.sleep(delay)

        raise Exception(f"All {max_attempts} attempts failed for {func.__name__}")

    @staticmethod
    def safe_agent_call(agent_func, *args, **kwargs):
        try:
            return agent_func(*args, **kwargs)
        except Exception as e:
            print(f"{agent_func.__name__} error: {str(e)}")
            print(f"Traceback: {traceback.format_exc()}")
            raise e
