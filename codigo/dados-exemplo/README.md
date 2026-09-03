# dados-exemplo

Recorte pequeno do dataset Cora, já no formato que o método consome (um DataFrame com
as colunas `features`, `neighbors` e `label`), mais o mapa de classes e o gabarito.

| Arquivo | Conteúdo |
|---------|----------|
| `cora_gac.pkl` | o grafo como DataFrame pandas (uma linha por nó) |
| `cora_classes.json` | mapa id da classe para nome (7 áreas de ML) |
| `cora_truth.json` | gabarito: id do nó para classe verdadeira |

---

## Para que servem (e para que NÃO servem)

Estes dados existem **apenas para demonstrar como se monta e se consome o DataFrame**
do método, com um exemplo que roda de verdade. São material didático.

Eles **não têm tamanho nem representatividade suficientes** para medir desempenho ou
representar cenários reais. Os percentuais obtidos rodando o exemplo sobre este recorte
não são uma avaliação do método: com poucos nós, um acerto a mais ou a menos muda muito
o resultado.

Para números com significância estatística (amostras grandes, várias sementes, datasets
completos), veja [`../../resultados/reproducao-o4mini.md`](../../resultados/reproducao-o4mini.md).

A fonte original do Cora e a citação estão em [`../../CITATION.md`](../../CITATION.md).
