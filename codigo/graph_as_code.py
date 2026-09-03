"""Implementação didática e autocontida do método Graph-as-Code.

O método Graph-as-Code (GaC) faz um modelo de linguagem (LLM) classificar nós de
um grafo **gerando código** em vez de receber o grafo inteiro descrito no prompt.
O grafo é representado como um ``DataFrame`` do pandas (uma linha por nó) e o LLM
gera expressões pandas para investigá-lo sob demanda::

    LLM gera código  ->  Python executa  ->  resultado volta ao LLM  ->  repete

O laço se repete até o LLM ter evidência suficiente e responder a classe do nó.

Este arquivo reúne, em quatro blocos comentados, tudo que o método precisa:

1. Prompt      -- descreve a tarefa e o formato da tabela ao LLM (Template 3).
2. Executor    -- roda a expressão do LLM num sandbox seguro.
3. Extração    -- lê a resposta do LLM (uma expressão ou a classe final).
4. Classifier  -- orquestra o laço iterativo de classificação.

No final há dois clientes de LLM (API compatível com OpenAI e Ollama local), ambos
com a mesma assinatura, o que permite trocar de provedor sem tocar no método.

Referência do método:
    Finkelshtein et al. (2026). "Actions Speak Louder than Prompts". ICLR.
    Template 3 (Appendix F).

Autor: Luiz Fernando P. Quirino (PPGCC/FACOM/UFMS).
"""

from __future__ import annotations

import ast
import json
import os
import re
import signal
import time
import urllib.request
from collections.abc import Callable, Iterator
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Protocol

import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Tipos auxiliares
# ---------------------------------------------------------------------------

#: Uma mensagem do diálogo com o LLM, no formato {"role": ..., "content": ...}.
Mensagem = dict[str, str]

#: Rótulos das classes possíveis: identificador inteiro -> descrição legível.
Classes = dict[int, str]


@dataclass(frozen=True)
class Uso:
    """Contagem de tokens consumidos numa chamada ao LLM.

    Separar entrada e saída importa porque a economia de tokens do método está
    no tamanho da *entrada*: o LLM consulta o grafo sob demanda em vez de recebê-lo
    inteiro no prompt.

    Attributes:
        prompt: Tokens de entrada (o que foi enviado ao modelo).
        completion: Tokens de saída (o que o modelo gerou).
    """

    prompt: int = 0
    completion: int = 0

    @property
    def total(self) -> int:
        """Total de tokens (entrada + saída)."""
        return self.prompt + self.completion


class ClienteLLM(Protocol):
    """Contrato de um cliente de LLM usado pelo classificador.

    Qualquer função que receba o histórico de mensagens e devolva a resposta do
    modelo mais a contagem de tokens serve como cliente. Isso desacopla o método
    do provedor (OpenAI, Ollama, etc.).
    """

    def __call__(
        self, mensagens: list[Mensagem], *, temperatura: float = 0.0, seed: int = 42
    ) -> tuple[str | None, Uso]:
        """Envia o diálogo ao modelo e devolve ``(resposta, uso)``.

        A resposta é ``None`` quando a chamada falha.
        """
        ...


# ===========================================================================
# 1. PROMPT
# ===========================================================================
# Descreve ao LLM a tarefa e o formato da tabela (o "schema"). É a tradução
# direta do Template 3 do artigo (Appendix F).

_TEMPLATE_SISTEMA = """\
Task: You are solving a node-based reasoning task for node {no}. You have a pandas \
DataFrame df where each row corresponds to a node, indexed by its node id.

Instructions: Always begin with reasoning. You may take as many steps as needed, but \
aim to solve the task efficiently using the fewest necessary actions. Before each \
action, assess what information is available, what's missing, which action is most \
appropriate next, and how many steps likely remain. Then, on a new line, specify your \
chosen action.

Schema structure:
- The DataFrame index is the node id. Access a row by node id with: df.loc[node_id].
- The column features stores each node's textual description: df.loc[node_id, 'features'].
- The column neighbors stores a list of neighbor node IDs: df.loc[node_id, 'neighbors'].
- The column label contains the integer node label if it belongs to the training set; \
otherwise None.

You may query ANY column(s) of df using any valid pandas command that applies to a \
DataFrame named df. You may also use pd.* utilities with df as input. The dataframe can \
be long, so you may want to avoid commands that print the entire table.

Response format:
- For intermediate steps: reason then on the final line output a single valid pandas \
expression.
- To finish: reason then on the final line respond exactly as: Answer [class_id].

Available class labels:
{classes}

Now begin your reasoning."""


def montar_prompt_sistema(no: int, classes: Classes) -> str:
    """Monta o prompt de sistema para classificar um nó.

    Args:
        no: Identificador do nó alvo.
        classes: Mapa de identificador de classe para descrição legível.

    Returns:
        O prompt de sistema já formatado, pronto para enviar ao LLM.
    """
    linhas_classes = "\n".join(
        f"{identificador}: {descricao}"
        for identificador, descricao in sorted(classes.items())
    )
    return _TEMPLATE_SISTEMA.format(no=no, classes=linhas_classes)


# ===========================================================================
# 2. EXECUTOR SEGURO
# ===========================================================================
# Roda a expressão pandas gerada pelo LLM num ambiente restrito. Só permite um
# subconjunto seguro da linguagem (sem import, open, eval...) e um conjunto fixo
# de nomes. Também impõe um tempo limite. É o que garante que o código gerado
# apenas consulta o DataFrame, sem tocar no sistema.

_NOMES_PERMITIDOS: frozenset[str] = frozenset({
    "df", "pd", "np", "len", "sum", "max", "min", "sorted", "list", "set",
    "dict", "str", "int", "float", "bool", "range", "enumerate", "zip",
    "any", "all", "abs", "round", "filter", "map", "tuple", "isinstance",
    "hasattr", "getattr", "True", "False", "None",
})

_FUNCOES_BLOQUEADAS: frozenset[str] = frozenset({
    "eval", "exec", "compile", "__import__", "open", "exit", "quit",
})

_NOS_AST_PERMITIDOS: frozenset[type[ast.AST]] = frozenset({
    ast.Expression, ast.BinOp, ast.UnaryOp, ast.BoolOp, ast.Compare,
    ast.Call, ast.Name, ast.Constant, ast.Load, ast.Store, ast.Del,
    ast.Subscript, ast.Attribute, ast.Slice, ast.List, ast.Tuple,
    ast.Dict, ast.Set, ast.IfExp, ast.ListComp, ast.SetComp,
    ast.DictComp, ast.GeneratorExp, ast.comprehension,
    ast.Starred, ast.keyword, ast.Lambda, ast.arg, ast.arguments,
    ast.JoinedStr, ast.FormattedValue,
    ast.Add, ast.Sub, ast.Mult, ast.Div, ast.Mod, ast.Pow,
    ast.FloorDiv, ast.LShift, ast.RShift, ast.BitOr, ast.BitXor,
    ast.BitAnd, ast.And, ast.Or, ast.Not, ast.Invert, ast.UAdd, ast.USub,
    ast.Eq, ast.NotEq, ast.Lt, ast.LtE, ast.Gt, ast.GtE,
    ast.Is, ast.IsNot, ast.In, ast.NotIn,
})

_LIMITE_TEXTO_RESULTADO = 2000
_LIMITE_LINHAS_TABELA = 50


class ExpressaoInsegura(SyntaxError):
    """Levantada quando a expressão do LLM usa algo fora da lista permitida."""


@contextmanager
def _tempo_limite(segundos: float) -> Iterator[None]:
    """Interrompe o bloco protegido se ele passar de ``segundos``.

    Usa ``SIGALRM``, então funciona apenas na thread principal em sistemas Unix.
    """

    def _disparar(_sinal: int, _quadro: Any) -> None:
        raise TimeoutError(f"Execução passou de {segundos}s")

    anterior = signal.signal(signal.SIGALRM, _disparar)
    signal.alarm(int(segundos))
    try:
        yield
    finally:
        signal.alarm(0)
        signal.signal(signal.SIGALRM, anterior)


class ExecutorSeguro:
    """Executa expressões pandas do LLM num sandbox restrito.

    A validação é feita sobre a árvore sintática (AST) da expressão: nós e nomes
    fora das listas permitidas são recusados antes de qualquer execução.

    Attributes:
        df: O DataFrame que representa o grafo.
        tempo_limite: Tempo máximo, em segundos, para avaliar uma expressão.
    """

    def __init__(self, df: pd.DataFrame, tempo_limite: float = 5.0) -> None:
        self.df = df
        self.tempo_limite = tempo_limite
        self._escopo: dict[str, Any] = {
            "df": df, "pd": pd, "np": np,
            "len": len, "sum": sum, "max": max, "min": min,
            "sorted": sorted, "list": list, "set": set, "dict": dict,
            "str": str, "int": int, "float": float, "bool": bool,
            "range": range, "enumerate": enumerate, "zip": zip,
            "any": any, "all": all, "abs": abs, "round": round,
            "filter": filter, "map": map, "tuple": tuple,
            "isinstance": isinstance, "hasattr": hasattr, "getattr": getattr,
            "True": True, "False": False, "None": None,
        }

    def executar(self, codigo: str) -> tuple[bool, str]:
        """Valida e executa uma expressão pandas.

        Args:
            codigo: A expressão gerada pelo LLM (ex.: ``df.loc[133, 'features']``).

        Returns:
            Uma tupla ``(sucesso, texto)``. Quando ``sucesso`` é ``False``, o texto
            descreve o erro (validação, execução ou tempo limite).
        """
        try:
            arvore = self._validar(codigo)
        except ExpressaoInsegura as erro:
            return False, f"ErroDeValidacao: {erro}"

        programa = compile(arvore, "<sandbox>", "eval")
        try:
            with _tempo_limite(self.tempo_limite):
                resultado = eval(programa, {"__builtins__": {}}, self._escopo)  # noqa: S307
        except TimeoutError as erro:
            return False, str(erro)
        except Exception as erro:  # noqa: BLE001 - devolvemos o erro ao LLM como texto
            return False, f"ErroDeExecucao: {type(erro).__name__}: {erro}"

        return True, self._formatar(resultado)

    def _validar(self, codigo: str) -> ast.Expression:
        """Analisa a AST e recusa nós ou nomes fora das listas permitidas."""
        arvore = ast.parse(codigo.strip(), mode="eval")
        for no in ast.walk(arvore):
            if type(no) not in _NOS_AST_PERMITIDOS:
                raise ExpressaoInsegura(f"construção não permitida: {type(no).__name__}")
            if isinstance(no, ast.Name) and no.id not in _NOMES_PERMITIDOS:
                raise ExpressaoInsegura(f"nome não permitido: {no.id}")
            if (
                isinstance(no, ast.Call)
                and isinstance(no.func, ast.Name)
                and no.func.id in _FUNCOES_BLOQUEADAS
            ):
                raise ExpressaoInsegura(f"função bloqueada: {no.func.id}")
        return arvore

    @staticmethod
    def _formatar(resultado: Any) -> str:
        """Converte o resultado em texto, truncando saídas longas por tipo.

        O truncamento evita que uma consulta ampla (ex.: a tabela inteira) estoure
        o contexto do LLM na próxima rodada.
        """
        if resultado is None:
            return "None"

        if isinstance(resultado, pd.DataFrame):
            if len(resultado) > _LIMITE_LINHAS_TABELA:
                cabecalho = (
                    f"DataFrame: {len(resultado)} linhas, "
                    f"{len(resultado.columns)} colunas\n"
                )
                return cabecalho + resultado.head(5).to_string()
            return resultado.to_string()

        if isinstance(resultado, pd.Series):
            if len(resultado) > _LIMITE_LINHAS_TABELA:
                cabecalho = f"Series: {len(resultado)} itens\n"
                return cabecalho + resultado.head(10).to_string()
            return resultado.to_string()

        texto = str(resultado)
        if len(texto) > _LIMITE_TEXTO_RESULTADO:
            return texto[:_LIMITE_TEXTO_RESULTADO] + "\n... [truncado]"
        return texto


# ===========================================================================
# 3. EXTRAÇÃO
# ===========================================================================
# Lê a resposta em texto do LLM e decide: é a classe final ("Answer [id]") ou
# uma expressão pandas para executar?

_PADRAO_RESPOSTA = re.compile(r"Answer[\s:\[]+(\d+)\]?", re.IGNORECASE)


def extrair_resposta(texto: str) -> int | None:
    """Devolve a classe final se o texto contiver ``Answer [id]``.

    Args:
        texto: A resposta do LLM.

    Returns:
        O identificador da classe, ou ``None`` se ainda não houver resposta final.
    """
    achado = _PADRAO_RESPOSTA.search(texto)
    return int(achado.group(1)) if achado else None


def extrair_codigo(texto: str) -> str | None:
    """Procura, de baixo para cima, a expressão pandas na resposta do LLM.

    A busca é de baixo para cima porque a expressão escolhida costuma ser a última
    linha da resposta (o LLM raciocina antes e age no fim).

    Args:
        texto: A resposta do LLM.

    Returns:
        A expressão encontrada, ou ``None`` se não houver nenhuma.
    """
    linhas = (linha.strip() for linha in reversed(texto.splitlines()) if linha.strip())
    for linha in linhas:
        candidata = linha.strip("`").strip()
        if candidata.startswith(">>>"):
            candidata = candidata[3:].strip()
        if candidata.lower().startswith("answer"):
            continue
        if candidata.startswith(("df.", "pd.")):
            return candidata
        if ("df." in candidata or "pd." in candidata) and any(c in candidata for c in "([="):
            return candidata
    return None


# ===========================================================================
# 4. CLASSIFICADOR
# ===========================================================================
# Orquestra o laço: envia o diálogo ao LLM, executa a expressão que ele gerar,
# devolve o resultado, e repete até o LLM responder a classe (ou esgotar os passos).

_COLUNAS_VISIVEIS_LLM = ["features", "neighbors", "label"]


@dataclass
class Resultado:
    """Desfecho da classificação de um nó.

    Attributes:
        no: Identificador do nó classificado.
        predicao: Classe prevista, ou ``-1`` quando não foi possível classificar.
        passos: Quantas rodadas de interação o LLM usou.
        uso: Tokens consumidos no total.
        latencia_s: Tempo total, em segundos.
        erro: Descrição do erro, quando houver.
    """

    no: int
    predicao: int = -1
    passos: int = 0
    uso: Uso = field(default_factory=Uso)
    latencia_s: float = 0.0
    erro: str | None = None


class ClassificadorGraphAsCode:
    """Classifica nós de um grafo pelo paradigma Graph-as-Code.

    O grafo deve ser um ``DataFrame`` indexado pelo id do nó, com as colunas
    ``features`` (texto), ``neighbors`` (lista de vizinhos) e ``label`` (a classe,
    visível apenas para os nós de treino).

    Exemplo:
        >>> cliente = criar_cliente_openai(modelo="o4-mini")
        >>> classificador = ClassificadorGraphAsCode(cliente, {0: "Real", 1: "Fake"})
        >>> resultado = classificador.classificar(df, no=133)
        >>> resultado.predicao
        1

    Attributes:
        cliente: A função que fala com o LLM.
        classes: Mapa de identificador de classe para descrição.
        max_passos: Número máximo de rodadas antes de forçar uma resposta.
        tempo_limite: Tempo máximo por expressão pandas, em segundos.
    """

    def __init__(
        self,
        cliente: ClienteLLM,
        classes: Classes,
        *,
        max_passos: int = 15,
        tempo_limite: float = 5.0,
    ) -> None:
        self.cliente = cliente
        self.classes = classes
        self.max_passos = max_passos
        self.tempo_limite = tempo_limite

    def classificar(
        self, df: pd.DataFrame, no: int, *, verboso: bool = False
    ) -> Resultado:
        """Classifica um único nó do grafo.

        Args:
            df: O grafo como DataFrame.
            no: O identificador do nó a classificar.
            verboso: Se ``True``, imprime o raciocínio e as expressões a cada passo.

        Returns:
            Um :class:`Resultado` com a predição e as métricas da execução.
        """
        executor = ExecutorSeguro(df, tempo_limite=self.tempo_limite)
        dialogo: list[Mensagem] = [
            {"role": "system", "content": montar_prompt_sistema(no, self.classes)},
            {"role": "user", "content": f"Please classify node {no}."},
        ]

        uso_total = Uso()
        inicio = time.time()

        for passo in range(1, self.max_passos + 1):
            resposta, uso = self.cliente(dialogo)
            uso_total = _somar_uso(uso_total, uso)

            if resposta is None:
                return Resultado(no, -1, passo, uso_total, _decorrido(inicio), "erro_de_api")

            dialogo.append({"role": "assistant", "content": resposta})
            if verboso:
                print(f"\n[Passo {passo}]\n{resposta[:400]}")

            desfecho = self._processar_resposta(resposta, executor, dialogo, verboso)
            if desfecho is not None:
                return Resultado(no, desfecho, passo, uso_total, _decorrido(inicio))

        # Esgotou os passos sem uma resposta: força uma decisão final.
        predicao, uso_final = self._forcar_resposta(dialogo)
        uso_total = _somar_uso(uso_total, uso_final)
        return Resultado(no, predicao, self.max_passos, uso_total, _decorrido(inicio))

    def _processar_resposta(
        self,
        resposta: str,
        executor: ExecutorSeguro,
        dialogo: list[Mensagem],
        verboso: bool,
    ) -> int | None:
        """Trata uma resposta do LLM dentro do laço.

        Returns:
            A classe final, se o LLM respondeu e ela é válida. Caso contrário,
            ``None`` e o diálogo já foi atualizado com o próximo passo (o resultado
            de uma expressão ou um pedido de correção).
        """
        classe = extrair_resposta(resposta)
        if classe is not None:
            if classe in self.classes:
                return classe
            dialogo.append(_pedir(f"Classe inválida {classe}. Válidas: {list(self.classes)}"))
            return None

        codigo = extrair_codigo(resposta)
        if codigo is None:
            dialogo.append(_pedir(
                "Nenhuma expressão pandas encontrada. Escreva uma expressão pandas "
                "ou responda com: Answer [class_id]"
            ))
            return None

        sucesso, texto = executor.executar(codigo)
        if verboso:
            print(f"  [{'ok' if sucesso else 'erro'}] {codigo}\n  -> {texto[:200]}")
        dialogo.append(_pedir(f"Result:\n{texto}"))
        return None

    def _forcar_resposta(self, dialogo: list[Mensagem]) -> tuple[int, Uso]:
        """Pede uma decisão final quando os passos se esgotam."""
        dialogo.append(_pedir(
            f"Maximum steps reached. You MUST answer now. "
            f"Valid classes: {list(self.classes)}. Respond ONLY with: Answer [class_id]"
        ))
        resposta, uso = self.cliente(dialogo)
        if resposta is not None:
            classe = extrair_resposta(resposta)
            if classe is not None:
                return classe, uso
        return -1, uso


# ---------------------------------------------------------------------------
# Funções utilitárias internas (mantêm o laço acima curto e legível)
# ---------------------------------------------------------------------------


def _pedir(conteudo: str) -> Mensagem:
    """Cria uma mensagem de usuário para devolver ao LLM."""
    return {"role": "user", "content": conteudo}


def _somar_uso(acumulado: Uso, novo: Uso) -> Uso:
    """Soma duas contagens de tokens."""
    return Uso(acumulado.prompt + novo.prompt, acumulado.completion + novo.completion)


def _decorrido(inicio: float) -> float:
    """Segundos decorridos desde ``inicio``, arredondados."""
    return round(time.time() - inicio, 2)


# ===========================================================================
# 5. CLIENTES DE LLM
# ===========================================================================
# Dois provedores, a mesma assinatura (o Protocol ClienteLLM). Troque de um para
# o outro sem mexer no método.


def criar_cliente_openai(
    modelo: str = "o4-mini",
    *,
    api_key: str | None = None,
    base_url: str | None = None,
) -> ClienteLLM:
    """Cria um cliente para a API da OpenAI ou qualquer API compatível.

    Serve para OpenAI, OpenRouter, Maritaca e afins, bastando ajustar ``base_url``.

    Args:
        modelo: Nome do modelo (ex.: ``"o4-mini"``).
        api_key: Chave de API. Se ``None``, usa a variável ``OPENAI_API_KEY``.
        base_url: URL base da API. ``None`` usa o padrão da OpenAI.

    Returns:
        Uma função :class:`ClienteLLM` pronta para uso.
    """
    from openai import OpenAI

    cliente = OpenAI(api_key=api_key or os.environ["OPENAI_API_KEY"], base_url=base_url)

    def conversar(
        mensagens: list[Mensagem], *, temperatura: float = 0.0, seed: int = 42
    ) -> tuple[str | None, Uso]:
        try:
            resposta = cliente.chat.completions.create(
                model=modelo, messages=mensagens, temperature=temperatura, seed=seed
            )
        except Exception as erro:  # noqa: BLE001 - falha de rede não deve derrubar o laço
            _avisar_erro("openai", erro)
            return None, Uso()

        texto = resposta.choices[0].message.content or ""
        return texto, _uso_da_openai(resposta.usage)

    return conversar


def criar_cliente_ollama(
    modelo: str = "qwen2.5:14b",
    *,
    base_url: str = "http://localhost:11434",
) -> ClienteLLM:
    """Cria um cliente para modelos locais servidos pelo Ollama (sem custo de API).

    Args:
        modelo: Nome do modelo no Ollama (ex.: ``"qwen2.5:14b"``).
        base_url: Endereço do servidor Ollama.

    Returns:
        Uma função :class:`ClienteLLM` pronta para uso.
    """
    endpoint = f"{base_url}/api/chat"
    tempo_limite = int(os.getenv("OLLAMA_TIMEOUT", "1800"))

    def conversar(
        mensagens: list[Mensagem], *, temperatura: float = 0.0, seed: int = 42
    ) -> tuple[str | None, Uso]:
        corpo = json.dumps({
            "model": modelo,
            "messages": mensagens,
            "stream": False,
            "options": {"temperature": temperatura, "seed": seed},
        }).encode()
        requisicao = urllib.request.Request(
            endpoint, data=corpo, headers={"Content-Type": "application/json"}
        )
        try:
            with urllib.request.urlopen(requisicao, timeout=tempo_limite) as conexao:  # noqa: S310
                dados = json.loads(conexao.read())
        except Exception as erro:  # noqa: BLE001 - falha de rede não deve derrubar o laço
            _avisar_erro("ollama", erro)
            return None, Uso()

        texto = dados.get("message", {}).get("content", "")
        uso = Uso(dados.get("prompt_eval_count", 0), dados.get("eval_count", 0))
        return texto, uso

    return conversar


def _uso_da_openai(usage: Any) -> Uso:
    """Converte o objeto de uso da OpenAI no nosso :class:`Uso`."""
    if usage is None:
        return Uso()
    return Uso(usage.prompt_tokens, usage.completion_tokens)


def _avisar_erro(origem: str, erro: Exception) -> None:
    """Imprime o erro de um cliente de forma discreta e uniforme."""
    print(f"[{origem}] erro: {type(erro).__name__}: {erro}")
