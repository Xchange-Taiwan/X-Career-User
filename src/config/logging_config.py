import logging

def init_logging():
    """
    初始化全域 logging 設定

    - 設定 root logger 層級為 INFO
    - 打印初始化訊息
    """

    root_logger = logging.getLogger()
    
    root_logger.setLevel(logging.INFO)

    root_logger.info("Logging initialized (root level=INFO)")