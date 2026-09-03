# 3. Reproduzir do zero

> Um guia para rodar o método na sua máquina, mesmo que você nunca tenha mexido nisso.

---

## O que você vai precisar

- Python 3.10 ou mais novo.
- Uma de duas formas de acesso a um LLM:
  - uma chave de API compatível com OpenAI (paga), ou
  - o Ollama instalado, para rodar um modelo local de graça.

---

## Passo 1: preparar o ambiente

Recomendo um ambiente virtual para não misturar dependências:

```bash
cd codigo
python -m venv .venv
source .venv/bin/activate        # no Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

---

## Passo 2: escolher como acessar o LLM

### Opção A: API compatível com OpenAI

Defina a chave no ambiente:

```bash
export OPENAI_API_KEY=sk-sua-chave-aqui
```

Isso vale para a OpenAI e para serviços compatíveis (OpenRouter, Maritaca), ajustando
a `base_url` no cliente se precisar.

### Opção B: modelo local com Ollama (sem custo)

Instale o Ollama (https://ollama.com), baixe um modelo e deixe o servidor no ar:

```bash
ollama pull qwen2.5:14b
ollama serve        # normalmente já sobe sozinho após a instalação
```

O modelo roda na sua máquina. É mais lento (pode usar CPU), mas não custa nada e não
manda dados para fora.

---

## Passo 3: rodar a demonstração

```bash
# Opção A (API):
python exemplo_cora.py --n 5 --modelo o4-mini

# Opção B (local):
python exemplo_cora.py --n 5 --provedor ollama --modelo qwen2.5:14b
```

Você verá, para cada nó, o raciocínio do LLM e cada expressão pandas que ele gera, até
a classe final. No fim, um resumo com a acurácia da amostra.

Para ver só o resultado, sem o passo a passo, use `--silencioso`.

---

## O que o script faz por dentro

1. Carrega o Cora já no formato do método (`dados-exemplo/cora_gac.pkl`).
2. Sorteia alguns nós de teste (aqueles cujo rótulo está oculto).
3. Para cada nó, chama o `ClassificadorGraphAsCode`, que roda o laço de investigação.
4. Compara a predição com o gabarito e reporta a acurácia.

---

## Argumentos disponíveis

| Argumento | Padrão | Para que serve |
|-----------|--------|----------------|
| `--n` | 5 | quantos nós classificar |
| `--seed` | 42 | semente do sorteio (reprodutível) |
| `--provedor` | openai | `openai` ou `ollama` |
| `--modelo` | o4-mini | nome do modelo |
| `--max-passos` | 15 | limite de rodadas antes de forçar resposta |
| `--silencioso` | desligado | esconde o raciocínio passo a passo |

---

## Problemas comuns

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| `KeyError: 'OPENAI_API_KEY'` | chave não definida | rode o `export` do passo 2 |
| erro de conexão com o Ollama | servidor não está no ar | rode `ollama serve` |
| acurácia baixa com poucos nós | amostra pequena | aumente `--n` (a acurácia estabiliza) |
| muito lento no Ollama | modelo grande em CPU | use um modelo menor (ex.: `llama3.1:8b`) |

---

## Quer números sérios?

A demonstração com poucos nós serve para ver o mecanismo. Para uma reprodução com
significância estatística (100 nós, várias sementes), veja
[`../resultados/reproducao-o4mini.md`](../resultados/reproducao-o4mini.md).

---

## Próximo passo

Entenda de onde o método veio em [`04-genealogia-do-metodo.md`](04-genealogia-do-metodo.md).
