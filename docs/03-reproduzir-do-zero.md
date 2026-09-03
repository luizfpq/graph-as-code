# 3. Reproduzir do zero

> Um guia para rodar o método na sua máquina, mesmo que você nunca tenha mexido nisso.

---

## O que você vai precisar

- Python 3.10 ou mais novo.
- Uma forma de acesso a um LLM:
  - uma chave do **OpenRouter** (provedor padrão do projeto), ou
  - uma chave da própria OpenAI, ou
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

### Opção A: OpenRouter (padrão do projeto)

O OpenRouter é uma API compatível com a da OpenAI que dá acesso a vários modelos com
uma única chave. Crie a chave em https://openrouter.ai e defina no ambiente:

```bash
export OPENROUTER_API_KEY=sua-chave-aqui
```

Os nomes de modelo levam o prefixo do provedor de origem, por exemplo
`openai/o4-mini` ou `deepseek/deepseek-chat`.

### Opção B: API da própria OpenAI

Se preferir usar a OpenAI diretamente:

```bash
export OPENAI_API_KEY=sk-sua-chave-aqui
```

Nesse caso, rode com `--provedor openai` e um nome de modelo sem prefixo (ex.: `o4-mini`).

### Opção C: modelo local com Ollama (sem custo)

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
# Opção A (OpenRouter, padrão):
python exemplo_cora.py --n 5 --modelo openai/o4-mini

# Opção B (OpenAI):
python exemplo_cora.py --n 5 --provedor openai --modelo o4-mini

# Opção C (local):
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

Os dados em `dados-exemplo/` são um recorte pequeno, incluído só para mostrar como se
monta e se consome o DataFrame. Não têm tamanho suficiente para representar cenários
reais: a acurácia mostrada aqui é ilustrativa, não uma medida do método. Números com
significância estão em [`../resultados/reproducao-o4mini.md`](../resultados/reproducao-o4mini.md).

---

## Argumentos disponíveis

| Argumento | Padrão | Para que serve |
|-----------|--------|----------------|
| `--n` | 5 | quantos nós classificar |
| `--seed` | 42 | semente do sorteio (reprodutível) |
| `--provedor` | openrouter | `openrouter`, `openai` ou `ollama` |
| `--modelo` | openai/o4-mini | nome do modelo (com prefixo no OpenRouter) |
| `--max-passos` | 15 | limite de rodadas antes de forçar resposta |
| `--silencioso` | desligado | esconde o raciocínio passo a passo |

---

## Problemas comuns

| Sintoma | Causa provável | Solução |
|---------|----------------|---------|
| `KeyError: 'OPENROUTER_API_KEY'` | chave não definida | rode o `export` do passo 2 |
| `KeyError: 'OPENAI_API_KEY'` | usou `--provedor openai` sem a chave | defina `OPENAI_API_KEY` |
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
