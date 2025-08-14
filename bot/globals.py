"""
Глобальное состояние приложения
"""

# Глобальная переменная для хранения монитора
_monitor_instance = None


def set_monitor_instance(monitor):
    """Устанавливает глобальный экземпляр монитора"""
    global _monitor_instance
    _monitor_instance = monitor


def get_monitor_instance():
    """Получает глобальный экземпляр монитора"""
    return _monitor_instance
