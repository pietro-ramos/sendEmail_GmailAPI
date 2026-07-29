from app.comunicado_config import ComunicadoConfig


def executar_comunicado(*args, **kwargs):
    from app.comunicado_runner import executar_comunicado as _executar_comunicado

    return _executar_comunicado(*args, **kwargs)

__all__ = ["ComunicadoConfig", "executar_comunicado"]
