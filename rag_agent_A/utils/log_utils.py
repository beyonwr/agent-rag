import logging
import os

APP_NAME = "rag_agent"
LOG_DIR_BASE = f"./artifacts/{APP_NAME}"


def get_user_session_logger(
    user_id: str, session_id: str, specified_name: str = ""
) -> logging.Logger:

    logger = logging.getLogger(
        f"{specified_name}{'_' if specified_name else ''}{session_id}"
    )
    logging.debug(f"new logger {logger.handlers=}")

    if not logger.handlers:

        logger.setLevel(logging.DEBUG)

        log_dir = f"{LOG_DIR_BASE}/{user_id}/{session_id}"
        os.makedirs(log_dir, exist_ok=True)
        logger.debug(
            f"Start logging into file for user {user_id} session {session_id}. Dir: {log_dir}"
        )
        # Create the file handler
        log_file_path = os.path.join(log_dir, f"{session_id}.log")
        file_handler = logging.FileHandler(log_file_path)

        # Create a formatter
        formatter = logging.Formatter(
            "%(asctime)s - **%(name)s** - %(levelname)s - %(message)s"
        )
        file_handler.setFormatter(formatter)

        # Add the handler to the logger
        logger.addHandler(file_handler)

        # Prevent logs from propagating to the root logger
        logger.propagate = False

    return logger
