from rest_framework.exceptions import APIException
from rest_framework.views import exception_handler


class Conflict(APIException):
    status_code = 409
    default_detail = "A operação conflita com o estado atual do recurso."
    default_code = "conflito"


def api_exception_handler(exc, context):
    response = exception_handler(exc, context)
    if response is None:
        return response
    messages = {
        400: ("DADOS_INVALIDOS", "Os dados informados são inválidos."),
        401: ("NAO_AUTENTICADO", "Autenticação necessária ou token expirado."),
        403: ("PERMISSAO_NEGADA", "Você não tem permissão para acessar este recurso."),
        404: ("NAO_ENCONTRADO", "Recurso não encontrado."),
        409: ("CONFLITO", "A operação conflita com o estado atual do recurso."),
        429: ("LIMITE_EXCEDIDO", "Muitas tentativas. Tente novamente mais tarde."),
    }
    code, message = messages.get(response.status_code, ("ERRO", "Não foi possível processar a solicitação."))
    response.data = {"erro": {"codigo": code, "mensagem": message, "detalhes": response.data}}
    return response
