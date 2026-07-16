from __future__ import annotations

from typing import Any, Callable

from app.scoring import evaluate_job


TOOL_DEFINITIONS = [
    {
        "type": "function",
        "function": {
            "name": "calcular_risco_vaga",
            "description": (
                "Calcula score, veredito e evidências por regras auditáveis. "
                "Deve ser chamada exatamente uma vez e seu veredito não pode ser alterado pelo modelo."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "vaga": {
                        "type": "object",
                        "description": "Campos da vaga exatamente como recebidos da aplicação.",
                        "properties": {
                            "title": {"type": "string"},
                            "description": {"type": "string"},
                            "company_profile": {"type": "string"},
                            "salary_range": {"type": "string"},
                            "required_education": {"type": "string"},
                            "required_experience": {"type": "string"},
                            "function": {"type": "string"},
                            "canal_contato": {"type": "string"},
                            "has_company_logo": {"type": "boolean"},
                            "has_questions": {"type": "boolean"},
                            "texto_bruto": {"type": "string"},
                        },
                        "required": ["title", "description"],
                    }
                },
                "required": ["vaga"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "consultar_casos_locais",
            "description": (
                "Busca no histórico local análises com texto ou título semelhante. "
                "Serve apenas como contexto; não confirma que a vaga atual é fraude."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "termo": {
                        "type": "string",
                        "description": "Termo curto e observável da vaga, como cargo ou domínio de contato.",
                        "minLength": 3,
                        "maxLength": 80,
                    },
                    "limite": {
                        "type": "integer",
                        "description": "Quantidade máxima de casos retornados.",
                        "minimum": 1,
                        "maximum": 5,
                        "default": 3,
                    },
                },
                "required": ["termo"],
            },
        },
    },
]


class ToolExecutionError(ValueError):
    pass


def _calculate(arguments: dict[str, Any]) -> dict[str, Any]:
    job = arguments.get("vaga")
    if not isinstance(job, dict):
        raise ToolExecutionError("O parâmetro 'vaga' deve ser um objeto.")
    return evaluate_job(job)


def _search(arguments: dict[str, Any]) -> dict[str, Any]:
    term = str(arguments.get("termo", "")).strip()
    if len(term) < 3:
        raise ToolExecutionError("O termo deve ter pelo menos 3 caracteres.")
    try:
        limit = max(1, min(5, int(arguments.get("limite", 3))))
    except (TypeError, ValueError) as exc:
        raise ToolExecutionError("O limite deve ser um número inteiro.") from exc

    from app.database import search_local_cases

    return {
        "aviso": "Histórico local é contexto, não confirmação de fraude.",
        "casos": search_local_cases(term[:80], limit),
    }


TOOL_HANDLERS: dict[str, Callable[[dict[str, Any]], dict[str, Any]]] = {
    "calcular_risco_vaga": _calculate,
    "consultar_casos_locais": _search,
}


def execute_tool(name: str, arguments: dict[str, Any]) -> dict[str, Any]:
    handler = TOOL_HANDLERS.get(name)
    if handler is None:
        raise ToolExecutionError(f"Ferramenta desconhecida: {name}")
    try:
        return handler(arguments)
    except ToolExecutionError:
        raise
    except Exception as exc:
        raise ToolExecutionError(f"Falha ao executar {name}: {exc}") from exc
