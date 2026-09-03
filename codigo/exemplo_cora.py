"""Demonstração do Graph-as-Code classificando nós do dataset Cora.

O Cora é o benchmark clássico de classificação de nós: cada nó é um artigo
científico, cada aresta é uma citação, e a tarefa é prever a área do artigo entre
sete classes. É o mesmo dataset usado no artigo original do método, então serve de
verificação de sanidade.

O script sorteia alguns nós de teste (aqueles com rótulo oculto), pede ao LLM que os
classifique mostrando o raciocínio passo a passo, e ao final reporta a acurácia.

Como rodar:

    # Com uma API compatível com OpenAI:
    export OPENAI_API_KEY=sk-...
    python exemplo_cora.py --n 5 --modelo o4-mini

    # Com um modelo local via Ollama (sem custo):
    python exemplo_cora.py --n 5 --provedor ollama --modelo qwen2.5:14b

Observação: com poucos nós (n=5) a acurácia oscila bastante; isto é uma demonstração
do mecanismo, não uma medida confiável. Ver a pasta ``resultados/`` para números de
uma reprodução séria.
"""

from __future__ import annotations

import argparse
import json
import random
from pathlib import Path

import pandas as pd

from graph_as_code import (
    Classes,
    ClassificadorGraphAsCode,
    ClienteLLM,
    criar_cliente_ollama,
    criar_cliente_openai,
)

PASTA_DADOS = Path(__file__).resolve().parent / "dados-exemplo"


def carregar_cora() -> tuple[pd.DataFrame, Classes, dict[int, int]]:
    """Carrega o grafo Cora, o mapa de classes e o gabarito.

    Returns:
        Uma tupla ``(df, classes, gabarito)``, em que ``df`` é o grafo no formato
        do método, ``classes`` mapeia id para nome da classe e ``gabarito`` mapeia
        id do nó para a classe verdadeira.
    """
    df = pd.read_pickle(PASTA_DADOS / "cora_gac.pkl")
    classes = {
        int(k): v
        for k, v in json.loads((PASTA_DADOS / "cora_classes.json").read_text()).items()
    }
    gabarito = {
        int(k): int(v)
        for k, v in json.loads((PASTA_DADOS / "cora_truth.json").read_text()).items()
    }
    return df, classes, gabarito


def sortear_nos_de_teste(df: pd.DataFrame, quantidade: int, seed: int) -> list[int]:
    """Sorteia nós de teste (aqueles cujo rótulo está oculto no DataFrame).

    Args:
        df: O grafo Cora.
        quantidade: Quantos nós sortear.
        seed: Semente para tornar o sorteio reprodutível.

    Returns:
        A lista de identificadores de nós sorteados.
    """
    nos_de_teste = [no for no in df.index if pd.isna(df.loc[no, "label"])]
    quantidade = min(quantidade, len(nos_de_teste))
    return random.Random(seed).sample(nos_de_teste, quantidade)


def criar_cliente(provedor: str, modelo: str) -> ClienteLLM:
    """Cria o cliente de LLM conforme o provedor escolhido."""
    if provedor == "openai":
        return criar_cliente_openai(modelo)
    if provedor == "ollama":
        return criar_cliente_ollama(modelo)
    raise ValueError(f"Provedor desconhecido: {provedor!r}")


def classificar_nos(
    classificador: ClassificadorGraphAsCode,
    df: pd.DataFrame,
    nos: list[int],
    classes: Classes,
    gabarito: dict[int, int],
    *,
    verboso: bool,
) -> int:
    """Classifica cada nó, imprime o desfecho e conta os acertos.

    Returns:
        O número de nós classificados corretamente.
    """
    grafo_para_llm = df[["features", "neighbors", "label"]]
    acertos = 0

    for indice, no in enumerate(nos, start=1):
        classe_real = gabarito[no]
        print("=" * 70)
        print(f"[{indice}/{len(nos)}] Nó {no}  |  "
              f"classe real: {classe_real} ({classes[classe_real]})")
        print("=" * 70)

        resultado = classificador.classificar(grafo_para_llm, no, verboso=verboso)

        acertou = resultado.predicao == classe_real
        acertos += int(acertou)
        nome_previsto = classes.get(resultado.predicao, "(inválida)")
        print(f"\n  -> Predição: {resultado.predicao} ({nome_previsto})  "
              f"{'ACERTOU' if acertou else 'errou'}")
        print(f"     passos={resultado.passos}  tokens={resultado.uso.total}  "
              f"latência={resultado.latencia_s}s\n")

    return acertos


def analisar_argumentos() -> argparse.Namespace:
    """Lê e valida os argumentos da linha de comando."""
    parser = argparse.ArgumentParser(description="Demonstração do Graph-as-Code no Cora")
    parser.add_argument("--n", type=int, default=5, help="quantos nós classificar")
    parser.add_argument("--seed", type=int, default=42, help="semente do sorteio")
    parser.add_argument("--provedor", choices=["openai", "ollama"], default="openai")
    parser.add_argument("--modelo", default="o4-mini", help="ex.: o4-mini, qwen2.5:14b")
    parser.add_argument("--max-passos", type=int, default=15)
    parser.add_argument("--silencioso", action="store_true",
                        help="não mostra o raciocínio passo a passo")
    return parser.parse_args()


def main() -> None:
    """Ponto de entrada: carrega os dados, classifica e resume."""
    args = analisar_argumentos()

    df, classes, gabarito = carregar_cora()
    print(f"Cora: {len(df)} nós, {len(classes)} classes")
    print("Classes:", classes)

    nos = sortear_nos_de_teste(df, args.n, args.seed)
    print(f"\nClassificando {len(nos)} nós de teste (seed={args.seed}): {nos}\n")

    classificador = ClassificadorGraphAsCode(
        criar_cliente(args.provedor, args.modelo),
        classes,
        max_passos=args.max_passos,
    )
    acertos = classificar_nos(
        classificador, df, nos, classes, gabarito, verboso=not args.silencioso
    )

    print("#" * 70)
    print(f"RESUMO: {acertos}/{len(nos)} corretos "
          f"({100 * acertos / len(nos):.0f}% de acurácia nesta amostra)")
    print("#" * 70)


if __name__ == "__main__":
    main()
