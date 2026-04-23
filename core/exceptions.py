class SonificationError(Exception):
    """Базовый класс ошибок"""
    pass

class EmptyCanvasError(SonificationError):
    """Пустой холст"""
    pass