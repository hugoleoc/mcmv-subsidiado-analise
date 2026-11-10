"""Preparação compartilhada da base MCMV-Subsidiado.

Usada pelos notebooks de análise territorial e de empresas, para que
as duas partes partam sempre da mesma base limpa.
"""
from pathlib import Path
import pandas as pd

# Caminho relativo à raiz do projeto (o módulo está em src/)
RAIZ = Path(__file__).resolve().parent.parent
CAMINHO_SUBSIDIADO = RAIZ / "dados" / "brutos" / "mcmv_subsidiado_20260630.csv"

# Identificadores lidos como texto, para não perder zeros e não usar notação científica
COLUNAS_TEXTO = ["cod_ibge", "cod_operacao", "txt_cnpj_construtora_entidade", "txt_cep"]

# Mapa de padronização da modalidade (caixa e acentos)
MAPA_MODALIDADE = {"RURAL": "Rural", "Oferta Publica": "Oferta Pública"}

# Modalidades presentes na legenda do dicionário de dados
MODALIDADES_DICIONARIO = {"FAR", "Entidades", "Oferta Pública", "Rural"}


def carregar_subsidiado(caminho=CAMINHO_SUBSIDIADO):
    """Lê o CSV bruto com os tipos corretos para o MCMV-Subsidiado."""
    return pd.read_csv(
        caminho,
        sep=";",
        encoding="utf-8",
        decimal=",",
        thousands=".",
        dtype={c: str for c in COLUNAS_TEXTO},
    )


def padronizar_modalidade(df):
    """Padroniza a modalidade e cria a classificação com/sem legenda do dicionário."""
    df = df.copy()
    df["txt_modalidade"] = df["txt_modalidade"].replace(MAPA_MODALIDADE)
    df["classificacao_modalidade"] = df["txt_modalidade"].apply(
        lambda m: "Com classificação" if m in MODALIDADES_DICIONARIO else "Sem classificação"
    )
    return df


def remover_duplicatas_exatas(df):
    """Remove linhas idênticas, mantendo a primeira ocorrência. Devolve a base e o total removido."""
    antes = len(df)
    df_limpo = df.drop_duplicates(keep="first").reset_index(drop=True)
    return df_limpo, antes - len(df_limpo)


def preparar_datas(df):
    """Converte dt_assinatura em data e cria trimestre e semestre."""
    df = df.copy()
    df["dt_assinatura"] = pd.to_datetime(df["dt_assinatura"], format="%d/%m/%Y", errors="coerce")
    df["trimestre"] = df["dt_assinatura"].dt.to_period("Q")
    df["semestre"] = (
        df["dt_assinatura"].dt.year.astype(str)
        + "S"
        + ((df["dt_assinatura"].dt.month > 6) + 1).astype(str)
    )
    return df


def preparar_sem_codigo(df):
    """Seleciona os registros sem cod_operacao e cria a chave nome + CNPJ + município."""
    sem = df[df["cod_operacao"].isna()].copy()
    sem["nome_padrao"] = (
        sem["txt_nome_empreendimento"]
        .str.strip().str.upper()
        .str.replace(r"\s+", " ", regex=True)
    )
    sem["cnpj_nulo"] = sem["txt_cnpj_construtora_entidade"].isna()
    sem["cnpj_chave"] = sem["txt_cnpj_construtora_entidade"].fillna("CNPJ NULO")
    return sem


def carregar_base_limpa():
    """Pipeline completo: leitura, modalidade, duplicatas e datas. Devolve a base pronta para análise."""
    df = carregar_subsidiado()
    df = padronizar_modalidade(df)
    df, _ = remover_duplicatas_exatas(df)
    df = preparar_datas(df)
    return df