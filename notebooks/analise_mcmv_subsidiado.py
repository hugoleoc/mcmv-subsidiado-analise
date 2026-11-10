# %% [markdown]
# # Projeto Habitação MCMV: análise territorial do MCMV-Subsidiado
#
# **Objetivo:** analisar a contratação de empreendimentos do Programa Minha Casa, Minha Vida (MCMV), modalidade subsidiada, por tempo, região, UF e município.
#
# **Fonte:** Ministério das Cidades, Secretaria Nacional de Habitação (SNH).
# Página de bases: https://www.gov.br/cidades/pt-br/acesso-a-informacao/acoes-e-programas/habitacao/programa-minha-casa-minha-vida/bases-de-dados-do-programa-minha-casa-minha-vida
#
# **Dicionário de dados:** *Dicionários de Dados SNH*, versão 2.4, de 09/10/2025 (página 2, tabela MCMV-Subsidiado).
#
# **Decisões de método**
# 1. **Data de análise:** `dt_assinatura` (data de contratação). `data_referencia` é só a data de extração.
# 2. **Calendário:** trimestres completos entre a menor e a maior data, com zero onde não houve contratação.
# 3. **Trimestre parcial:** 2026T2 (dados até 23/06/2026) é sinalizado nos gráficos.
# 4. **Formato de valores:** R$ em bilhões nos gráficos; os cálculos usam valores originais.
# 5. **Unidades habitacionais:** cada linha é um empreendimento; `qtd_uh` é o total contratado nele, e as demais colunas de unidades são a distribuição por situação.
# 6. **Preparação da base:** feita em `src/preparacao.py`, compartilhada com a análise de empresas.

# %% [markdown]
# ## 1. Ambiente e importações
#
# Ambiente virtual `.venv` na raiz do projeto. O kernel deve ser o `.venv` (`mcmv\.venv\Scripts\python.exe`).
#
# - `pandas`: leitura e manipulação de tabelas.
# - `numpy`: posições numéricas das barras nos gráficos.
# - `matplotlib.pyplot`: gráficos.
# - `src.preparacao`: módulo compartilhado de preparação da base.

# %%
import sys
from pathlib import Path

# Sobe a partir da pasta atual até encontrar src/preparacao.py (raiz do projeto)
RAIZ = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "src" / "preparacao.py").is_file())
sys.path.insert(0, str(RAIZ))

from IPython.display import display
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

from src.preparacao import carregar_base_limpa, MODALIDADES_DICIONARIO

# %% [markdown]
# ## 2. Carregamento e preparação
#
# A base é lida, padronizada e limpa pelo módulo `src/preparacao.py`: leitura com tipos corretos,
# padronização de modalidade, remoção de duplicatas exatas e preparação de datas, trimestre e semestre.
# %%
df_sub = carregar_base_limpa()

print(len(df_sub), df_sub["val_contratado_total"].sum(), df_sub["qtd_uh"].sum())
print("Linhas na base limpa:", len(df_sub))
print("Datas inválidas:", df_sub["dt_assinatura"].isna().sum())
print("Menor data:", df_sub["dt_assinatura"].min(), "| Maior data:", df_sub["dt_assinatura"].max())

# Período formatado para os títulos dos gráficos
data_min = df_sub["dt_assinatura"].min()
data_max = df_sub["dt_assinatura"].max()
periodo_inicio = data_min.strftime("%d/%m/%Y")
periodo_fim = data_max.strftime("%d/%m/%Y")

# Calendário completo de trimestres, do primeiro ao último
trimestres = pd.period_range(start=data_min.to_period("Q"), end=data_max.to_period("Q"), freq="Q")

# %% [markdown]
# ## 3. Conferência com o dicionário de dados
#
# Compara as colunas lidas com a lista do dicionário. Deve sair vazio nos dois casos.
# A conferência usa a lista de colunas do próprio dicionário, transcrita abaixo.

# %%
colunas_dicionario = [
    "data_referencia", "cod_ibge", "txt_nome_municipio", "txt_sigla_uf", "txt_regiao",
    "dt_assinatura", "cod_operacao", "txt_nome_empreendimento", "txt_nome_agente_financeiro",
    "txt_modalidade", "txt_situacao_empreendimento", "qtd_uh", "qtd_uh_entregues",
    "qtd_uh_vigentes", "qtd_uh_distratadas", "val_contratado_total", "val_desembolsado",
    "txt_cnpj_construtora_entidade", "txt_nome_construtora_entidade", "txt_endereco", "txt_cep",
]
print("No dicionário e ausentes na base:", set(colunas_dicionario) - set(df_sub.columns))
print("Na base e fora do dicionário:", set(df_sub.columns) - set(colunas_dicionario))

# %%
# Conferência por modalidade: a soma das linhas deve ser igual ao total da base
contagem_modalidade = df_sub["txt_modalidade"].value_counts()
display(contagem_modalidade.to_frame("linhas"))
print("Conferência:", "OK" if contagem_modalidade.sum() == len(df_sub) else "DIVERGE")

# %% [markdown]
# ## 4. Séries trimestrais de valor
#
# Séries por trimestre: geral, por região, por UF e por município (cod_ibge).
# Base de cálculo para os gráficos da seção 6.

# %%
serie_geral = (
    df_sub.groupby("trimestre")["val_contratado_total"].sum()
    .reindex(trimestres, fill_value=0)
)

serie_regiao = pd.pivot_table(
    df_sub, index="trimestre", columns="txt_regiao",
    values="val_contratado_total", aggfunc="sum", fill_value=0,
).reindex(trimestres, fill_value=0)

serie_uf = pd.pivot_table(
    df_sub, index="trimestre", columns="txt_sigla_uf",
    values="val_contratado_total", aggfunc="sum", fill_value=0,
).reindex(trimestres, fill_value=0)

serie_municipio = pd.pivot_table(
    df_sub, index="trimestre", columns="cod_ibge",
    values="val_contratado_total", aggfunc="sum", fill_value=0,
).reindex(trimestres, fill_value=0)

print("Diferença (deve ser ~0):", round(serie_geral.sum() - df_sub["val_contratado_total"].sum(), 2))

# %%
# Formatação para exibição em R$ bilhões (apenas visual; os cálculos usam valores originais)
def formatar_bi(valor):
    return f"R$ {valor / 1e9:,.2f} bi".replace(",", "X").replace(".", ",").replace("X", ".")

# %% [markdown]
# ## 4.1 Classificação de modalidades
#
# "Com classificação": modalidades da legenda do dicionário (FAR, Entidades, Oferta Pública, Rural).
# "Sem classificação": FNHIS e FAR - Compra Assistida. A classificação já vem pronta do módulo.

# %%
print(df_sub.groupby(["classificacao_modalidade", "txt_modalidade"])
      .agg(empreendimentos=("cod_operacao", "count"),
           unidades=("qtd_uh", "sum"),
           valor_total=("val_contratado_total", "sum")))
print(df_sub.groupby("classificacao_modalidade")["val_contratado_total"].sum())

# %% [markdown]
# ## 4.2 Checagens de duplicidade e consistência
#
# Confirma a base limpa: sem linhas duplicadas exatas, sem `cod_operacao` repetido e com `qtd_uh`
# igual à soma das situações.

# %%
print("Linhas duplicadas exatas:", int(df_sub.duplicated().sum()))
print("cod_operacao repetidos:", int(df_sub["cod_operacao"].dropna().duplicated().sum()))
soma_situacoes = (
    df_sub["qtd_uh_entregues"] + df_sub["qtd_uh_vigentes"] + df_sub["qtd_uh_distratadas"].fillna(0)
)
print("Linhas em que qtd_uh difere da soma:", int((df_sub["qtd_uh"] != soma_situacoes).sum()))


# %% [markdown]
# ## 7. Gráficos
#
# Padrões usados em todos os gráficos:
# - Eixo x: trimestre, com um rótulo por ano (exceto o gráfico 7.3 e o 7.4, que usam região e modalidade).
# - Valores monetários: R$ bilhões, com uma casa decimal no eixo e duas nos rótulos. Unidades habitacionais: número inteiro com separador de milhar.
# - Trimestre parcial: 2026T2 é sinalizado com cor clara (barras) ou trecho tracejado (linhas), com nota no gráfico.
# - Cores de região fixas em `cores_regiao` (paleta Okabe-Ito) e cores de modalidade em `cores_modalidade`.

# ### Padrões compartilhados pelos gráficos
plt.style.use("seaborn-v0_8-whitegrid")

regioes = ["Norte", "Nordeste", "Centro-Oeste", "Sudeste", "Sul"]

# %%
# Paleta Okabe-Ito, segura para daltonismo, com uma cor por região
cores_regiao = {
    "Norte": "#009E73",          # verde-azulado
    "Nordeste": "#E69F00",       # laranja
    "Centro-Oeste": "#D55E00",   # vermelho-alaranjado (quente)
    "Sudeste": "#CC79A7",        # rosa (frio)
    "Sul": "#0072B2",            # azul

}

formato_milhar = plt.FuncFormatter(lambda v, _: f"{v:,.0f}".replace(",", "."))

# %%
# 7.1 Valor total por trimestre (barras), em R$ bilhões
rotulos = [f"{p.year}T{p.quarter}" for p in serie_geral.index]
posicoes = np.arange(len(rotulos))

# Valores numéricos em bilhões: o matplotlib precisa de números, não de texto
valores_bi = serie_geral.values / 1e9

# Barras da paleta Okabe-Ito; o último trimestre (parcial) recebe azul claro
cores = ["#0072B2"] * len(rotulos)
cores[-1] = "#56B4E9"

fig, ax = plt.subplots(figsize=(16, 6))
barras = ax.bar(posicoes, valores_bi, color=cores)

ax.set_title("Valor contratado no MCMV-Subsidiado, por trimestre", fontsize=14, pad=12)
ax.set_xlabel("Trimestre da contratação")
ax.set_ylabel("Total contratado (R$ bilhões)")
ax.set_xticks(posicoes[::4])
ax.set_xticklabels(rotulos[::4], rotation=45, ha="right")

# Eixo y com duas casas decimais e vírgula brasileira, coerente com formatar_bi
ax.yaxis.set_major_formatter(
    plt.FuncFormatter(lambda v, _: f"{v:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))
)

# Rótulo com o valor formatado (saída de formatar_bi) no topo de cada barra
serie_formatada = serie_geral.map(formatar_bi).values
for barra, texto in zip(barras, serie_formatada):
    if barra.get_height() > 0:
        ax.text(barra.get_x() + barra.get_width() / 2, barra.get_height(),
                texto, ha="center", va="bottom", rotation=90, fontsize=7)

ax.set_ylim(0, valores_bi.max() * 1.25)
ax.grid(axis="y", linestyle="--", alpha=0.5)
ax.set_axisbelow(True)
ax.text(0.99, 0.95, "Barra clara: 2026T2 (trimestre incompleto)",
        transform=ax.transAxes, ha="right", fontsize=9, color="#555555")

plt.tight_layout()
plt.show()

# %%
# 7.2 Curva trimestral por região (linhas), em R$ bilhões
rotulos = [f"{p.year}T{p.quarter}" for p in serie_regiao.index]
posicoes = np.arange(len(rotulos))

fig, ax = plt.subplots(figsize=(16, 6))
for regiao in regioes:
    valores_bi = serie_regiao[regiao].values / 1e9
    # Linha principal: todos os trimestres, exceto os dois últimos (2026T2 parcial)
    ax.plot(posicoes[:-1], valores_bi[:-1], marker="o", linewidth=2,
            color=cores_regiao[regiao], label=regiao)
    # Trecho do trimestre parcial: tracejado, com marcador vazado
    ax.plot(posicoes[-2:], valores_bi[-2:], linestyle="--", marker="o",
            markerfacecolor="white", linewidth=2, color=cores_regiao[regiao])

ax.set_title("Evolução do valor contratado no MCMV-Subsidiado, por região e trimestre", fontsize=14, pad=12)
ax.set_xlabel("Trimestre da contratação")
ax.set_ylabel("Total contratado (R$ bilhões)")
ax.set_xticks(posicoes[::4])
ax.set_xticklabels(rotulos[::4], rotation=45, ha="right")
ax.yaxis.set_major_formatter(
    plt.FuncFormatter(lambda v, _: f"{v:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))
)
ax.legend(title="Região")
ax.text(0.99, 0.95, "Trecho tracejado: 2026T2 (trimestre incompleto)",
        transform=ax.transAxes, ha="right", fontsize=9, color="#555555")
plt.tight_layout()
plt.show()

# %%
# 7.3 Modalidades por região (barras horizontais), com participação dentro de cada região
valor_mod_regiao = (
    df_sub.groupby(["txt_modalidade", "txt_regiao"])["val_contratado_total"]
    .sum()
    .unstack(fill_value=0)
    .reindex(columns=regioes, fill_value=0)
)

# Ordena as modalidades pelo valor total (a maior fica no topo do gráfico)
ordem_modalidades = valor_mod_regiao.sum(axis=1).sort_values(ascending=True).index
valor_mod_regiao = valor_mod_regiao.loc[ordem_modalidades]

# Participação de cada modalidade dentro do total da própria região (em %)
participacao_regiao = valor_mod_regiao / valor_mod_regiao.sum(axis=0) * 100

cores_modalidade = {
    "FAR": "#0072B2",
    "Entidades": "#E69F00",
    "Oferta Pública": "#009E73",
    "Rural": "#CC79A7",
    "FNHIS": "#56B4E9",
    "FAR - Compra Assistida": "#999999",
}

# sharey=True: as modalidades ficam alinhadas entre os painéis
fig, eixos = plt.subplots(1, len(regioes), figsize=(22, 6), sharey=False, sharex=True)

# Maior valor entre todas as regiões, para usar a mesma escala em todos os painéis
limite_x = valor_mod_regiao.values.max() / 1e9 * 1.9

for i, (ax, regiao) in enumerate(zip(eixos, regioes)):
    valores_bi = valor_mod_regiao[regiao].values / 1e9
    pct = participacao_regiao[regiao].values
    modalidades = valor_mod_regiao.index
    cores_barras = [cores_modalidade.get(m, "#444444") for m in modalidades]

    barras = ax.barh(modalidades, valores_bi, color=cores_barras)
    ax.set_title(regiao, color=cores_regiao[regiao], fontweight="bold")
    ax.set_xlabel("R$ bilhões")
    ax.set_xlim(0, limite_x)
    ax.grid(axis="x", linestyle="--", alpha=0.5)
    ax.set_axisbelow(True)

    # Nomes das modalidades só no primeiro painel (Norte); nos demais, o eixo é o mesmo
    if i > 0:
        ax.tick_params(labelleft=False)

    # Rótulo com valor e percentual, no fim de cada barra
    for barra, v, p in zip(barras, valores_bi, pct):
        if v > 0:
            texto = f"R$ {v:,.2f} bi ({p:.1f}%)".replace(",", "X").replace(".", ",").replace("X", ".")
            ax.text(barra.get_width() + limite_x * 0.01, barra.get_y() + barra.get_height() / 2,
                    texto, va="center", fontsize=8)

eixos[0].set_ylabel("Modalidade")
fig.suptitle("Valor contratado por modalidade em cada região (MCMV-Subsidiado)",
             fontsize=14, y=1.02)
plt.tight_layout()
plt.show()

# %%
# 7.4 Total por região no período (barras, com participação), em R$ bilhões
total_regiao = df_sub.groupby("txt_regiao")["val_contratado_total"].sum().reindex(regioes)
participacao = total_regiao / total_regiao.sum() * 100
valores_bi = total_regiao.values / 1e9

# Datas de início e fim do período, formatadas como dd/mm/aaaa
periodo_inicio = data_min.strftime("%d/%m/%Y")
periodo_fim = data_max.strftime("%d/%m/%Y")

fig, ax = plt.subplots(figsize=(10, 6))
barras = ax.bar(regioes, valores_bi, color=[cores_regiao[r] for r in regioes])

ax.set_title(
    f"Valor total contratado no MCMV-Subsidiado, por região.\n"
    f"Período: {periodo_inicio} a {periodo_fim}",
    fontsize=14, pad=12,
)
ax.set_xlabel("Região")
ax.set_ylabel("Total contratado (R$ bilhões)")
ax.yaxis.set_major_formatter(
    plt.FuncFormatter(lambda v, _: f"{v:,.1f}".replace(",", "X").replace(".", ",").replace("X", "."))
)
ax.grid(axis="y", linestyle="--", alpha=0.5)
ax.set_axisbelow(True)

# Rótulo com valor em bilhões e participação percentual no topo de cada barra
for barra, valor, pct in zip(barras, valores_bi, participacao.values):
    texto = f"R$ {valor:,.2f} bi\n({pct:.1f}%)".replace(",", "X").replace(".", ",").replace("X", ".")
    ax.text(barra.get_x() + barra.get_width() / 2, barra.get_height(),
            texto, ha="center", va="bottom", fontsize=9)

ax.set_ylim(0, valores_bi.max() * 1.15)
plt.tight_layout()
plt.show()

# %%
# 7.5 Total de unidades habitacionais por região no período (barras, com participação)
total_uh_regiao = df_sub.groupby("txt_regiao")["qtd_uh"].sum().reindex(regioes)
participacao_uh = total_uh_regiao / total_uh_regiao.sum() * 100

fig, ax = plt.subplots(figsize=(10, 6))
barras = ax.bar(regioes, total_uh_regiao.values, color=[cores_regiao[r] for r in regioes])

ax.set_title(
    f"Unidades habitacionais contratadas no MCMV-Subsidiado, por região.\n"
    f"Período: {periodo_inicio} a {periodo_fim}",
    fontsize=14, pad=12,
)
ax.set_xlabel("Região")
ax.set_ylabel("Unidades habitacionais contratadas")
ax.yaxis.set_major_formatter(formato_milhar)
ax.grid(axis="y", linestyle="--", alpha=0.5)
ax.set_axisbelow(True)

# Rótulo com o total de unidades e a participação percentual no topo de cada barra
for barra, total, pct in zip(barras, total_uh_regiao.values, participacao_uh.values):
    texto = f"{total:,.0f} UH\n({pct:.1f}%)".replace(",", ".")
    ax.text(barra.get_x() + barra.get_width() / 2, barra.get_height(),
            texto, ha="center", va="bottom", fontsize=9)

ax.set_ylim(0, total_uh_regiao.max() * 1.15)
plt.tight_layout()
plt.show()
# %%
# %%
# 7.6 Total de unidades habitacionais entregues por região no período (barras, com participação)
total_uhe_regiao = df_sub.groupby("txt_regiao")["qtd_uh_entregues"].sum().reindex(regioes)
participacao_uhe = total_uhe_regiao / total_uhe_regiao.sum() * 100

fig, ax = plt.subplots(figsize=(10, 6))
barras = ax.bar(regioes, total_uhe_regiao.values, color=[cores_regiao[r] for r in regioes])

ax.set_title(
    f"Unidades habitacionais entregues no MCMV-Subsidiado, por região.\n"
    f"Período: {periodo_inicio} a {periodo_fim}",
    fontsize=14, pad=12,
)
ax.set_xlabel("Região")
ax.set_ylabel("Unidades habitacionais entregues")
ax.yaxis.set_major_formatter(formato_milhar)
ax.grid(axis="y", linestyle="--", alpha=0.5)
ax.set_axisbelow(True)

# Rótulo com o total de unidades entregues e a participação percentual no topo de cada barra
for barra, total, pct in zip(barras, total_uhe_regiao.values, participacao_uhe.values):
    texto = f"{total:,.0f} UH\n({pct:.1f}%)".replace(",", ".")
    ax.text(barra.get_x() + barra.get_width() / 2, barra.get_height(),
            texto, ha="center", va="bottom", fontsize=9)

ax.set_ylim(0, total_uhe_regiao.max() * 1.15)
plt.tight_layout()
plt.show()


# %%
# %%
# 7.7 Unidades habitacionais vigentes por região no período (barras, com participação)
total_uhv_regiao = df_sub.groupby("txt_regiao")["qtd_uh_vigentes"].sum().reindex(regioes)
participacao_uhv = total_uhv_regiao / total_uhv_regiao.sum() * 100

fig, ax = plt.subplots(figsize=(10, 6))
barras = ax.bar(regioes, total_uhv_regiao.values, color=[cores_regiao[r] for r in regioes])

ax.set_title(
    f"Unidades habitacionais vigentes (não entregues) no MCMV-Subsidiado, por região.\n"
    f"Período: {periodo_inicio} a {periodo_fim}",
    fontsize=14, pad=12,
)
ax.set_xlabel("Região")
ax.set_ylabel("Unidades habitacionais vigentes")
ax.yaxis.set_major_formatter(formato_milhar)
ax.grid(axis="y", linestyle="--", alpha=0.5)
ax.set_axisbelow(True)

for barra, total, pct in zip(barras, total_uhv_regiao.values, participacao_uhv.values):
    texto = f"{total:,.0f} UH\n({pct:.1f}%)".replace(",", ".")
    ax.text(barra.get_x() + barra.get_width() / 2, barra.get_height(),
            texto, ha="center", va="bottom", fontsize=9)

ax.set_ylim(0, total_uhv_regiao.max() * 1.15)
plt.tight_layout()
plt.show()

# %%
# 7.8 Unidades habitacionais distratadas por região no período (barras, com participação)
total_uhd_regiao = df_sub.groupby("txt_regiao")["qtd_uh_distratadas"].sum().reindex(regioes)
participacao_uhd = total_uhd_regiao / total_uhd_regiao.sum() * 100

fig, ax = plt.subplots(figsize=(10, 6))
barras = ax.bar(regioes, total_uhd_regiao.values, color=[cores_regiao[r] for r in regioes])

ax.set_title(
    f"Unidades habitacionais distratadas no MCMV-Subsidiado, por região.\n"
    f"Período: {periodo_inicio} a {periodo_fim}",
    fontsize=14, pad=12,
)
ax.set_xlabel("Região")
ax.set_ylabel("Unidades habitacionais distratadas")
ax.yaxis.set_major_formatter(formato_milhar)
ax.grid(axis="y", linestyle="--", alpha=0.5)
ax.set_axisbelow(True)

for barra, total, pct in zip(barras, total_uhd_regiao.values, participacao_uhd.values):
    texto = f"{total:,.0f} UH\n({pct:.1f}%)".replace(",", ".")
    ax.text(barra.get_x() + barra.get_width() / 2, barra.get_height(),
            texto, ha="center", va="bottom", fontsize=9)

ax.set_ylim(0, total_uhd_regiao.max() * 1.15)
plt.tight_layout()
plt.show()
# %%
# Confirmação final sobre a base limpa
print("Linhas duplicadas exatas:", df_sub.duplicated().sum())
print("cod_operacao repetidos (não nulos):", df_sub["cod_operacao"].dropna().duplicated().sum())
print("Empreendimentos com cod_operacao nulo:", df_sub["cod_operacao"].isna().sum())

# %%
# %%
# 7.9 Composição das unidades contratadas por região (barras horizontais empilhadas a 100%)
composicao = (
    df_sub.groupby("txt_regiao")[["qtd_uh_entregues", "qtd_uh_vigentes", "qtd_uh_distratadas"]]
    .sum()
    .reindex(regioes)
)

# Converte cada parcela em percentual do total contratado da região
composicao_pct = composicao.div(composicao.sum(axis=1), axis=0) * 100

rotulos_situacao = ["Entregues", "Vigentes (não entregues)", "Distratadas"]
colunas_situacao = ["qtd_uh_entregues", "qtd_uh_vigentes", "qtd_uh_distratadas"]
cores_situacao = ["#0072B2", "#E69F00", "#CC79A7"]

fig, ax = plt.subplots(figsize=(14, 6))

# Empilhamento: cada parcela começa onde a anterior terminou
esquerda = np.zeros(len(regioes))
for coluna, rotulo, cor in zip(colunas_situacao, rotulos_situacao, cores_situacao):
    valores = composicao_pct[coluna].values
    barras = ax.barh(regioes, valores, left=esquerda, color=cor, label=rotulo, edgecolor="white")

    # Rótulo com o percentual dentro da fatia, só quando há espaço suficiente
    for barra, v in zip(barras, valores):
        if v >= 3:
            ax.text(barra.get_x() + barra.get_width() / 2,
                    barra.get_y() + barra.get_height() / 2,
                    f"{v:.1f}%".replace(".", ","),
                    ha="center", va="center", fontsize=9, color="white")
    esquerda += valores

ax.set_title(
    f"Composição das unidades habitacionais contratadas, por região (MCMV-Subsidiado)\n"
    f"Período: {periodo_inicio} a {periodo_fim}",
    fontsize=14, pad=12,
)
ax.set_xlabel("Participação nas unidades contratadas da região (%)")
ax.set_xlim(0, 100)
ax.invert_yaxis()  # Norte no topo, na ordem fixa das regiões
ax.legend(title="Situação", loc="upper center", bbox_to_anchor=(0.5, -0.15), ncol=3, frameon=False)
ax.grid(axis="x", linestyle="--", alpha=0.5)
ax.set_axisbelow(True)

plt.tight_layout()
plt.show()
