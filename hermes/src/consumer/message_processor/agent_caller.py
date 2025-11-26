import time
import traceback
from src.utils.logger import HermesLogger

logger = HermesLogger("agent_caller")

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
                    logger.error("All retry attempts failed", func=func.__name__, error=str(e))
                    raise e

                delay = min(base_delay * (2**attempt), max_delay)
                logger.warning(
                    "Agent call failed, retrying",
                    func=func.__name__,
                    attempt=f"{attempt + 1}/{max_attempts}",
                    retry_delay_s=delay,
                    error=str(e)
                )
                time.sleep(delay)

        raise Exception(f"All {max_attempts} attempts failed for {func.__name__}")

    @staticmethod
    def safe_agent_call(agent_func, *args, **kwargs):
        try:
            return agent_func(*args, **kwargs)
        except Exception as e:
            logger.error("Agent call failed", func=agent_func.__name__, error=str(e))
            raise e
