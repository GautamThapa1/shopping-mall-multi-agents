from langchain_core.runnables import RunnableConfig


def get_user_id(config: RunnableConfig) -> str:
    """Read the authenticated user ID from LangChain's runtime config."""
    configurable = config.get("configurable", {})
    user_id = configurable.get("user_id")
    if not isinstance(user_id, str) or not user_id:
        raise ValueError("Runnable config must include a non-empty user_id.")
    return user_id