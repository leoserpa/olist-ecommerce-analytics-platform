"""
ETL Pipeline — Olist Brazilian E-Commerce
==========================================
Pipeline de produção para ingestão, limpeza, enriquecimento e validação
do dataset público Olist. Gera um Parquet analítico e um relatório de
qualidade em HTML.

Autor : Pipeline automatizado
Stack : Python 3.11 · DuckDB · pandas · pyarrow
"""

import duckdb
import logging
import os
import sys
import traceback
from datetime import datetime
from pathlib import Path

import pandas as pd
import numpy as np

# ─────────────────────────────────────────────────────────────────────
# CONSTANTES
# ─────────────────────────────────────────────────────────────────────
RAW_DIR = Path("data/raw")
RECEITA_PARQUET = Path("data/olist_receita.parquet")
COMPLETO_PARQUET = Path("data/olist_completo.parquet")
OUTPUT_REPORT = Path("reports/relatorio_qualidade.html")
LOG_DIR = Path("logs")

TIMESTAMP_RUN = datetime.now().strftime("%Y%m%d_%H%M%S")
LOG_FILE = LOG_DIR / f"etl_{TIMESTAMP_RUN}.log"

REQUIRED_TABLES = [
    "orders", "customers", "order_items",
    "order_payments", "order_reviews", "products",
    "product_category_name_translation",
]

REQUIRED_COLS_NO_NULL = ["order_id", "order_purchase_timestamp", "customer_state"]

MIN_PEDIDOS_MES = 100

FAIXA_ENTREGA_BINS = [
    (0, 7, "rapido"),
    (8, 15, "normal"),
    (16, 30, "lento"),
    (31, float("inf"), "muito lento"),
]


# ─────────────────────────────────────────────────────────────────────
# LOGGING
# ─────────────────────────────────────────────────────────────────────
class EmojiFilter(logging.Filter):
    """Remove emojis dos registros destinados ao arquivo de log."""
    import re
    _EMOJI_RE = re.compile(
        "["
        "\U0001F300-\U0001F9FF"
        "\U00002702-\U000027B0"
        "\U0000FE00-\U0000FE0F"
        "\U0000200D"
        "\U000025A0-\U000025FF"
        "\U00002600-\U000026FF"
        "]+",
        flags=re.UNICODE,
    )

    def filter(self, record):
        record.msg = self._EMOJI_RE.sub("", str(record.msg)).strip()
        return True


def setup_logging() -> logging.Logger:
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    logger = logging.getLogger("olist_etl")
    logger.setLevel(logging.DEBUG)

    # Handler: terminal (INFO, com emojis)
    # Forcar UTF-8 no stdout para evitar crash com emojis no Windows (cp1252)
    utf8_stdout = open(sys.stdout.fileno(), mode="w", encoding="utf-8", closefd=False)
    console_handler = logging.StreamHandler(utf8_stdout)
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter("%(message)s")
    console_handler.setFormatter(console_fmt)

    # Handler: arquivo (DEBUG, sem emojis)
    file_handler = logging.FileHandler(LOG_FILE, encoding="utf-8")
    file_handler.setLevel(logging.DEBUG)
    file_handler.addFilter(EmojiFilter())
    file_fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
    )
    file_handler.setFormatter(file_fmt)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    return logger


# ─────────────────────────────────────────────────────────────────────
# ETAPAS DO PIPELINE
# ─────────────────────────────────────────────────────────────────────

def etapa_carregar_csvs(con: duckdb.DuckDBPyConnection, log: logging.Logger) -> dict:
    """Carrega todos os CSVs em tabelas DuckDB. Retorna mapa {nome: linhas}."""
    log.info("📁 [1/8] Carregando CSVs para DuckDB...")
    csv_files = sorted(RAW_DIR.glob("*.csv"))

    if not csv_files:
        raise FileNotFoundError(f"Nenhum CSV encontrado em {RAW_DIR}")

    tabelas = {}
    for fp in csv_files:
        name = fp.stem.replace("olist_", "").replace("_dataset", "")
        con.execute(
            f"CREATE TABLE {name} AS SELECT * FROM read_csv_auto('{fp.as_posix()}')"
        )
        rows = con.execute(f"SELECT COUNT(*) FROM {name}").fetchone()[0]
        tabelas[name] = rows
        log.debug(f"  Tabela '{name}' criada — {rows:,} linhas")

    for req in REQUIRED_TABLES:
        if req not in tabelas:
            raise ValueError(f"Tabela obrigatória ausente: {req}")

    log.info(f"✅ {len(tabelas)} tabelas carregadas: {list(tabelas.keys())}")
    return tabelas


def etapa_dedup_reviews(con: duckdb.DuckDBPyConnection, log: logging.Logger) -> int:
    """Deduplica reviews mantendo a mais recente por order_id."""
    log.info("🔎 [2/8] Deduplicando reviews antes do JOIN...")

    total_antes = con.execute("SELECT COUNT(*) FROM order_reviews").fetchone()[0]
    dupes = con.execute("""
        SELECT COUNT(*) FROM (
            SELECT order_id, COUNT(*) AS cnt 
            FROM order_reviews GROUP BY order_id HAVING cnt > 1
        )
    """).fetchone()[0]

    log.info(f"   Reviews totais: {total_antes:,} | Pedidos com múltiplas reviews: {dupes:,}")

    if dupes > 0:
        con.execute("""
            CREATE OR REPLACE TABLE order_reviews AS
            SELECT * FROM (
                SELECT *,
                    ROW_NUMBER() OVER (
                        PARTITION BY order_id
                        ORDER BY TRY_CAST(review_creation_date AS TIMESTAMP) DESC NULLS LAST
                    ) AS rn
                FROM order_reviews
            ) WHERE rn = 1
        """)
        # Remover coluna auxiliar rn
        con.execute("""
            CREATE OR REPLACE TABLE order_reviews AS
            SELECT * EXCLUDE (rn) FROM order_reviews
        """)
        total_depois = con.execute("SELECT COUNT(*) FROM order_reviews").fetchone()[0]
        removidos = total_antes - total_depois
        log.info(f"   ✅ {removidos:,} reviews duplicadas removidas. Reviews finais: {total_depois:,}")
        return removidos
    else:
        log.info("   ✅ Nenhuma duplicata encontrada em reviews.")
        return 0


def etapa_join(con: duckdb.DuckDBPyConnection, log: logging.Logger) -> pd.DataFrame:
    """Executa o JOIN principal e retorna o DataFrame base."""
    log.info("🔗 [3/8] Executando JOINs entre tabelas...")

    query = """
        SELECT
            o.order_id,
            o.customer_id,
            c.customer_unique_id,
            TRY_CAST(o.order_purchase_timestamp AS TIMESTAMP)       AS order_purchase_timestamp,
            TRY_CAST(o.order_approved_at AS TIMESTAMP)              AS order_approved_at,
            TRY_CAST(o.order_delivered_carrier_date AS TIMESTAMP)    AS order_delivered_carrier_date,
            TRY_CAST(o.order_delivered_customer_date AS TIMESTAMP)   AS order_delivered_customer_date,
            TRY_CAST(o.order_estimated_delivery_date AS TIMESTAMP)   AS order_estimated_delivery_date,
            o.order_status,
            c.customer_state,
            c.customer_city,
            oi.order_item_id,
            oi.price,
            oi.freight_value,
            oi.seller_id,
            s.seller_city,
            s.seller_state,
            p.product_weight_g,
            rev.review_score,
            TRY_CAST(rev.review_creation_date AS TIMESTAMP)         AS review_creation_date,
            pt.product_category_name_english                        AS product_category,
            pay.payment_type
        FROM orders o
        LEFT JOIN customers c       ON o.customer_id = c.customer_id
        LEFT JOIN order_items oi    ON o.order_id    = oi.order_id
        LEFT JOIN sellers s         ON oi.seller_id  = s.seller_id
        LEFT JOIN order_reviews rev ON o.order_id    = rev.order_id
        LEFT JOIN products p        ON oi.product_id = p.product_id
        LEFT JOIN product_category_name_translation pt
            ON p.product_category_name = pt.product_category_name
        LEFT JOIN (
            SELECT order_id, payment_type,
                   ROW_NUMBER() OVER (PARTITION BY order_id ORDER BY payment_value DESC) AS rn
            FROM order_payments
        ) pay ON o.order_id = pay.order_id AND pay.rn = 1
    """
    df = con.execute(query).df()
    log.info(f"   ✅ Shape pós-JOIN: {df.shape[0]:,} linhas × {df.shape[1]} colunas")
    return df


def _logar_nulos(df: pd.DataFrame, log: logging.Logger, titulo: str):
    """Loga detalhes de nulos por coluna."""
    nulos = df.isnull().sum()
    nulos = nulos[nulos > 0]
    if nulos.empty:
        log.debug(f"  [{titulo}] Nenhum nulo encontrado.")
        return
    for col, cnt in nulos.items():
        pct = cnt / len(df) * 100
        log.debug(f"  [{titulo}] {col}: {cnt:,} nulos ({pct:.2f}%)")


def etapa_investigar_nulos(df: pd.DataFrame, log: logging.Logger) -> dict:
    """Investiga contexto de cada grupo de nulos ANTES de tratar.
    Retorna dict com relatórios para o HTML."""
    log.info("🔍 [4/8] Investigando contexto dos nulos...")
    relatorio = {}

    # ── order_item_id / price / freight_value nulos ──
    mask_item_null = df["order_item_id"].isnull()
    cnt = mask_item_null.sum()
    if cnt > 0:
        dist = df.loc[mask_item_null, "order_status"].value_counts().to_dict()
        log.info(f"   order_item_id/price/freight nulos: {cnt:,}")
        log.info(f"   Distribuição por order_status: {dist}")

        # Verificar anomalias (status delivered sem item)
        delivered_sem_item = dist.get("delivered", 0)
        if delivered_sem_item > 0:
            log.warning(
                f"   ⚠️ ANOMALIA: {delivered_sem_item} pedidos 'delivered' sem itens — "
                f"logar para investigação separada"
            )
        relatorio["item_nulos"] = {"total": cnt, "distribuicao_status": dist}
    else:
        relatorio["item_nulos"] = {"total": 0, "distribuicao_status": {}}

    # ── order_delivered_customer_date / tempo_entrega nulos ──
    mask_date_null = df["order_delivered_customer_date"].isnull()
    cnt_date = mask_date_null.sum()
    if cnt_date > 0:
        dist_date = df.loc[mask_date_null, "order_status"].value_counts().to_dict()
        log.info(f"   order_delivered_customer_date nulos: {cnt_date:,}")
        log.info(f"   Distribuição por order_status: {dist_date}")

        delivered_sem_data = dist_date.get("delivered", 0)
        if delivered_sem_data > 0:
            log.warning(
                f"   ⚠️ ANOMALIA GRAVE: {delivered_sem_data} pedidos 'delivered' sem data de entrega — "
                f"serão REMOVIDOS"
            )
        relatorio["entrega_nulos"] = {
            "total": cnt_date,
            "distribuicao_status": dist_date,
            "delivered_sem_data": delivered_sem_data,
        }
    else:
        relatorio["entrega_nulos"] = {"total": 0, "distribuicao_status": {}, "delivered_sem_data": 0}

    # ── review_score nulos ──
    mask_rev_null = df["review_score"].isnull()
    cnt_rev = mask_rev_null.sum()
    log.info(f"   review_score nulos: {cnt_rev:,} ({cnt_rev / len(df) * 100:.2f}%) — "
             f"Decisão: criar coluna 'tem_avaliacao', preencher nulos com 0")
    relatorio["review_nulos"] = cnt_rev

    # ── product_category nulos ──
    mask_cat_null = df["product_category"].isnull()
    cnt_cat = mask_cat_null.sum()
    log.info(f"   product_category nulos: {cnt_cat:,} ({cnt_cat / len(df) * 100:.2f}%) — "
             f"Decisão: preencher com 'sem categoria'")
    relatorio["categoria_nulos"] = cnt_cat

    return relatorio


def etapa_tratar_nulos(df: pd.DataFrame, log: logging.Logger) -> pd.DataFrame:
    """Aplica tratamento de nulos conforme regras de negócio."""
    log.info("🧹 [5/8] Tratando valores nulos com regras de negócio...")
    shape_antes = df.shape[0]

    # 1. Pedidos 'delivered' sem data de entrega → anomalia grave → remover
    mask_anomalia = (
        (df["order_status"] == "delivered") &
        (df["order_delivered_customer_date"].isnull())
    )
    n_anomalias = mask_anomalia.sum()
    if n_anomalias > 0:
        log.warning(f"   ❌ Removendo {n_anomalias:,} linhas — pedidos 'delivered' sem data de entrega")
        df = df[~mask_anomalia].copy()

    # 2. order_item_id / price / freight nulos → preencher com 0 (pedidos sem itens válidos)
    for col in ["order_item_id", "price", "freight_value"]:
        n = df[col].isnull().sum()
        if n > 0:
            df[col] = df[col].fillna(0)
            log.debug(f"   {col}: {n:,} nulos preenchidos com 0")

    # 3. review_score → criar flag ANTES de preencher
    df["tem_avaliacao"] = df["review_score"].notna()
    n_rev = df["review_score"].isnull().sum()
    df["review_score"] = df["review_score"].fillna(0)
    log.debug(f"   review_score: {n_rev:,} nulos preenchidos com 0 (coluna 'tem_avaliacao' criada)")

    # 4. product_category → preencher com 'sem categoria'
    n_cat = df["product_category"].isnull().sum()
    df["product_category"] = df["product_category"].fillna("sem categoria")
    log.debug(f"   product_category: {n_cat:,} nulos preenchidos com 'sem categoria'")

    # 5. Data entrega e tempo de entrega: manter como NaT/NaN (não preencher)
    log.debug("   order_delivered_customer_date: nulos em não-delivered mantidos como NaT")

    shape_depois = df.shape[0]
    log.info(f"   ✅ Shape: {shape_antes:,} → {shape_depois:,} (removidas {shape_antes - shape_depois:,} anomalias)")
    return df


def etapa_anomalias(df: pd.DataFrame, log: logging.Logger) -> dict:
    """Detecta e trata anomalias nos dados. Retorna relatório."""
    log.info("🚨 [6/8] Detectando anomalias...")
    relatorio = {}
    shape_antes = df.shape[0]

    # 1. price ou freight_value negativos
    mask_neg_price = df["price"] < 0
    mask_neg_freight = df["freight_value"] < 0
    n_neg = (mask_neg_price | mask_neg_freight).sum()
    if n_neg > 0:
        log.warning(f"   ❌ {n_neg:,} linhas com price ou freight negativos — REMOVIDAS")
        df = df[~(mask_neg_price | mask_neg_freight)].copy()
    else:
        log.info("   ✅ Nenhum preço/frete negativo encontrado")
    relatorio["negativos"] = n_neg

    # 2. tempo_entrega_dias negativo em pedidos delivered
    df["tempo_entrega_dias"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.days
    mask_tempo_neg = (df["order_status"] == "delivered") & (df["tempo_entrega_dias"] < 0)
    n_tempo_neg = mask_tempo_neg.sum()
    if n_tempo_neg > 0:
        log.warning(f"   ❌ ANOMALIA CRÍTICA: {n_tempo_neg:,} pedidos 'delivered' com tempo de entrega negativo — REMOVIDOS")
        df = df[~mask_tempo_neg].copy()
    else:
        log.info("   ✅ Nenhum tempo de entrega negativo em pedidos delivered")
    relatorio["tempo_negativo"] = n_tempo_neg

    # 3. review_score fora do intervalo 0-5 (0 = sem avaliação)
    mask_score_inv = ~df["review_score"].isin([0, 1, 2, 3, 4, 5])
    n_score_inv = mask_score_inv.sum()
    if n_score_inv > 0:
        log.warning(f"   ⚠️ {n_score_inv:,} review_score fora de [0-5] — corrigidos para 0")
        df.loc[mask_score_inv, "review_score"] = 0
    else:
        log.info("   ✅ Todos review_score dentro de [0-5]")
    relatorio["score_invalido"] = n_score_inv

    # 4. Datas futuras (além da data máxima natural do dataset)
    max_date = df["order_purchase_timestamp"].max()
    # A data máxima legítima do Olist é em torno de 2018-10. Vamos usar
    # a data máxima + 1 dia como limiar, caso o user tenha dados extras.
    mask_futuro = df["order_purchase_timestamp"] > max_date
    n_futuro = mask_futuro.sum()
    # Como usamos max_date do próprio dataset, nenhuma linha pode ser maior
    # que ela mesma. Isso serve como guarda: se injetarem dados, detecta.
    log.info(f"   ✅ Data máxima do dataset: {max_date}. Registros futuros: {n_futuro}")
    relatorio["datas_futuras"] = n_futuro

    # 5. Duplicatas por (order_id, order_item_id)
    # Excluir registros com order_item_id == 0 (pedidos sem itens originais)
    df_check = df[df["order_item_id"] > 0]
    dupes = df_check.duplicated(subset=["order_id", "order_item_id"], keep="first")
    n_dupes = dupes.sum()
    if n_dupes > 0:
        log.warning(f"   ⚠️ {n_dupes:,} duplicatas por (order_id, order_item_id) — mantendo primeira ocorrência")
        idx_to_remove = df_check[dupes].index
        df = df.drop(idx_to_remove).copy()
    else:
        log.info("   ✅ Nenhuma duplicata por (order_id, order_item_id)")
    relatorio["duplicatas"] = n_dupes

    shape_depois = df.shape[0]
    log.info(f"   Shape após anomalias: {shape_antes:,} → {shape_depois:,}")
    relatorio["removidas_total"] = shape_antes - shape_depois
    return df, relatorio


def etapa_colunas_derivadas(df: pd.DataFrame, log: logging.Logger) -> pd.DataFrame:
    """Cria colunas analíticas derivadas."""
    log.info("🧮 [7/8] Criando colunas derivadas...")

    # ano_mes
    df["ano_mes"] = df["order_purchase_timestamp"].dt.strftime("%Y-%m")

    # tempo_entrega_dias (já recalculado na etapa de anomalias, mas garantir coerência)
    df["tempo_entrega_dias"] = (
        df["order_delivered_customer_date"] - df["order_purchase_timestamp"]
    ).dt.days

    # faixa_entrega
    def classificar_entrega(dias):
        if pd.isna(dias):
            return "nao entregue"
        dias = int(dias)
        for lo, hi, label in FAIXA_ENTREGA_BINS:
            if lo <= dias <= hi:
                return label
        return "nao entregue"

    df["faixa_entrega"] = df["tempo_entrega_dias"].apply(classificar_entrega)

    # faixa_preco (quartis do price > 0)
    mask_preco = df["price"] > 0
    df["faixa_preco"] = "N/A"
    if mask_preco.sum() > 0:
        quartis = pd.qcut(df.loc[mask_preco, "price"], q=4, labels=["baixo", "medio", "alto", "premium"])
        df.loc[mask_preco, "faixa_preco"] = quartis.astype(str)

    # pedido_item_seq — numera cada item dentro do pedido (1, 2, 3...)
    # USE: filtre pedido_item_seq == 1 para métricas por PEDIDO (ex: review, status)
    #      use TODAS as linhas para métricas por ITEM (ex: receita, frete, categoria)
    df["pedido_item_seq"] = df.groupby("order_id").cumcount() + 1

    n_pedidos = df["order_id"].nunique()
    n_multi_item = (df.groupby("order_id").size() > 1).sum()
    n_avaliados = df.loc[df["pedido_item_seq"] == 1, "tem_avaliacao"].sum()
    pct_avaliados = (n_avaliados / n_pedidos * 100) if n_pedidos > 0 else 0
    log.info(f"   📊 Pedidos unicos: {n_pedidos:,} | Multi-item: {n_multi_item:,} | Avaliados: {pct_avaliados:.1f}%")

    # atraso_entrega_dias — Diferenca entre entrega real e estimada
    # Positivo = atrasou, Negativo = adiantou, NaN = nao entregue
    df["atraso_entrega_dias"] = (
        df["order_delivered_customer_date"] - df["order_estimated_delivery_date"]
    ).dt.days

    # --- COLUNAS DE DIAGNOSTICO ---
    # dias_para_postar: Responsabilidade do Vendedor (Aprovado ate Transportadora)
    df["dias_para_postar"] = (
        df["order_delivered_carrier_date"] - df["order_approved_at"]
    ).dt.days

    # dias_vencimento_sla: Quao fora do prazo o pedido foi entregue
    df["dias_vencimento_sla"] = df["atraso_entrega_dias"]

    # pct_frete — Peso do frete no valor total pago pelo cliente
    total_item = df["price"] + df["freight_value"]
    df["pct_frete"] = np.where(total_item > 0, (df["freight_value"] / total_item * 100).round(2), 0)

    # hora_compra — Hora da compra para analise de comportamento
    df["hora_compra"] = df["order_purchase_timestamp"].dt.hour

    # Remover coluna auxiliar review_creation_date (usada no DuckDB)
    if "review_creation_date" in df.columns:
        df = df.drop(columns=["review_creation_date"])

    # Logs de resumo das novas colunas
    mask_entregues = df["atraso_entrega_dias"].notna()
    if mask_entregues.any():
        media_atraso = df.loc[mask_entregues, "atraso_entrega_dias"].mean()
        media_postagem = df.loc[df["dias_para_postar"].notna(), "dias_para_postar"].mean()
        log.info(f"   📦 Atraso médio: {media_atraso:.1f} dias | Tempo médio postagem seller: {media_postagem:.1f} dias")

    log.info(f"   ✅ Colunas de Diagnostico criadas: dias_para_postar, dias_vencimento_sla")
    log.info(f"   Shape final: {df.shape[0]:,} linhas × {df.shape[1]} colunas")
    return df


def etapa_filtrar_meses_truncados(df: pd.DataFrame, log: logging.Logger) -> tuple:
    """Remove meses com volume insuficiente de pedidos (truncados).
    Retorna (df_filtrado, relatorio_meses)."""
    log.info("📅 [EXTRA] Filtrando meses truncados por volume insuficiente...")
    shape_antes = df.shape[0]

    # Calcular pedidos unicos por ano_mes
    vol = df.groupby("ano_mes")["order_id"].nunique().reset_index()
    vol.columns = ["ano_mes", "pedidos_unicos"]
    vol = vol.sort_values("ano_mes")

    # Identificar meses truncados (menos de MIN_PEDIDOS_MES pedidos)
    meses_truncados = vol[vol["pedidos_unicos"] < MIN_PEDIDOS_MES].copy()
    relatorio = {"meses_removidos": [], "periodo_final": ("", ""), "total_meses_validos": 0}

    if meses_truncados.empty:
        log.info(f"   ✅ Nenhum mes truncado encontrado (todos >= {MIN_PEDIDOS_MES} pedidos)")
        meses_validos = vol.sort_values("ano_mes")
        relatorio["periodo_final"] = (meses_validos["ano_mes"].iloc[0], meses_validos["ano_mes"].iloc[-1])
        relatorio["total_meses_validos"] = len(meses_validos)
        return df, relatorio

    # Logar detalhes de cada mes truncado
    log.warning(f"   ⚠️ {len(meses_truncados)} meses com menos de {MIN_PEDIDOS_MES} pedidos detectados:")
    for _, row in meses_truncados.iterrows():
        log.warning(f"      - {row['ano_mes']}: {row['pedidos_unicos']} pedidos (REMOVIDO)")
        relatorio["meses_removidos"].append({
            "mes": row["ano_mes"],
            "pedidos": int(row["pedidos_unicos"]),
            "motivo": f"Volume abaixo do minimo ({MIN_PEDIDOS_MES} pedidos)"
        })

    # Filtrar
    meses_para_remover = set(meses_truncados["ano_mes"].tolist())
    df = df[~df["ano_mes"].isin(meses_para_remover)].copy()

    shape_depois = df.shape[0]
    log.info(f"   Shape: {shape_antes:,} → {shape_depois:,} (removidas {shape_antes - shape_depois:,} linhas)")

    # Validar resultado
    vol_pos = df.groupby("ano_mes")["order_id"].nunique()
    abaixo = vol_pos[vol_pos < MIN_PEDIDOS_MES]
    if not abaixo.empty:
        log.error(f"   ❌ Ainda existem meses abaixo de {MIN_PEDIDOS_MES} apos filtragem: {abaixo.to_dict()}")
    else:
        log.info(f"   ✅ Validado: todos os {len(vol_pos)} meses restantes >= {MIN_PEDIDOS_MES} pedidos")

    meses_sorted = sorted(df["ano_mes"].unique())
    mes_ini, mes_fim = meses_sorted[0], meses_sorted[-1]
    log.info(f"   Periodo final: {mes_ini} ate {mes_fim} ({len(meses_sorted)} meses)")

    relatorio["periodo_final"] = (mes_ini, mes_fim)
    relatorio["total_meses_validos"] = len(meses_sorted)

    return df, relatorio


def etapa_salvar_e_validar(df: pd.DataFrame, log: logging.Logger):
    """Salva o Parquet Completo e executa validações rigorosas."""
    log.info("💾 [8/8] Salvando Parquet e validando...")

    COMPLETO_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df.to_parquet(COMPLETO_PARQUET, engine="pyarrow", index=False)
    log.info(f"   Arquivo salvo: {COMPLETO_PARQUET}")

    # Reabrir e validar
    df_val = pd.read_parquet(COMPLETO_PARQUET)
    log.info(f"   Validando arquivo reaberture — Shape: {df_val.shape}")

    erros = []

    # Validação 1: Shape confere
    if df_val.shape != df.shape:
        erros.append(f"Shape diverge: esperado {df.shape}, obtido {df_val.shape}")

    # Validação 2: Colunas obrigatórias sem nulos
    for col in REQUIRED_COLS_NO_NULL:
        n = df_val[col].isnull().sum()
        if n > 0:
            erros.append(f"Coluna obrigatória '{col}' tem {n:,} nulos")

    # Validação 3: review_score no range [0, 5]
    score_fora = (~df_val["review_score"].isin([0, 1, 2, 3, 4, 5])).sum()
    if score_fora > 0:
        erros.append(f"review_score fora de [0-5]: {score_fora:,} registros")

    # Validação 4: Duplicatas por (order_id, order_item_id) onde order_item_id > 0
    df_dup_check = df_val[df_val["order_item_id"] > 0]
    dupes = df_dup_check.duplicated(subset=["order_id", "order_item_id"]).sum()
    if dupes > 0:
        erros.append(f"Duplicatas (order_id, order_item_id): {dupes:,}")

    # Validação 5: Granularidade de reviews (max 1 review_score distinto por order_id)
    rev_por_pedido = df_val.groupby("order_id")["review_score"].nunique()
    multi_rev = (rev_por_pedido > 1).sum()
    if multi_rev > 0:
        erros.append(f"Pedidos com review_scores conflitantes: {multi_rev:,}")

    if erros:
        for e in erros:
            log.error(f"   ❌ VALIDAÇÃO FALHOU: {e}")
        # Deletar arquivo corrompido
        COMPLETO_PARQUET.unlink(missing_ok=True)
        log.error(f"   Arquivo {COMPLETO_PARQUET} DELETADO por falha na validação")
        raise ValueError(f"Validação final falhou: {'; '.join(erros)}")

    log.info("   ✅ Todas as validações passaram")
    log.info(f"\n📊 Shape final: {df_val.shape[0]:,} linhas × {df_val.shape[1]} colunas")
    pd.set_option("display.max_columns", None)
    log.info(f"\n👀 Primeiras 3 linhas:\n{df_val.head(3)}")


def etapa_gerar_parquets_derivados(df: pd.DataFrame, log: logging.Logger) -> dict:
    """Gera parquets derivados: receita (apenas transações reais) e completo."""
    log.info("📦 [EXTRA] Gerando parquets derivados...")

    # ── olist_receita.parquet ──
    status_receita = ['delivered', 'shipped', 'invoiced', 'processing', 'approved']
    mask_receita = (df['order_status'].isin(status_receita)) & (df['price'] > 0)
    df_receita = df[mask_receita].copy()

    RECEITA_PARQUET.parent.mkdir(parents=True, exist_ok=True)
    df_receita.to_parquet(RECEITA_PARQUET, engine="pyarrow", index=False)
    log.info(f"   ✅ olist_receita.parquet salvo — {df_receita.shape[0]:,} linhas (apenas pedidos com valor real)")

    # ── Detalhar exclusões ──
    df_excluidos = df[~mask_receita]
    n_excluidos = len(df_excluidos)
    log.warning(f"   ⚠️ Registros excluídos do dataset de receita: {n_excluidos:,}")

    detalhes_exclusao = {}
    if n_excluidos > 0:
        # Agrupar por order_status
        mask_unavailable = df_excluidos['order_status'] == 'unavailable'
        mask_canceled_0 = (df_excluidos['order_status'] == 'canceled') & (df_excluidos['price'] == 0)
        mask_canceled_price = (df_excluidos['order_status'] == 'canceled') & (df_excluidos['price'] > 0)
        mask_created = df_excluidos['order_status'] == 'created'

        categorias = [
            ('unavailable', mask_unavailable.sum()),
            ('canceled com price=0', mask_canceled_0.sum()),
            ('canceled com price>0 (status fora da lista)', mask_canceled_price.sum()),
            ('created', mask_created.sum()),
        ]

        outros = n_excluidos - sum(c[1] for c in categorias)
        categorias.append(('outros', outros))

        for nome, qtd in categorias:
            if qtd > 0:
                log.warning(f"      - {nome}: {qtd:,}")
                detalhes_exclusao[nome] = int(qtd)

    relatorio = {
        'receita_linhas': df_receita.shape[0],
        'completo_linhas': df.shape[0],
        'excluidos_total': n_excluidos,
        'excluidos_detalhe': detalhes_exclusao,
    }

    return relatorio


# ─────────────────────────────────────────────────────────────────────
# RELATÓRIO HTML
# ─────────────────────────────────────────────────────────────────────

def gerar_relatorio_html(
    df: pd.DataFrame,
    nulos_antes: pd.Series,
    nulos_depois: pd.Series,
    shape_antes: tuple,
    shape_depois: tuple,
    relatorio_nulos: dict,
    relatorio_anomalias: dict,
    relatorio_meses: dict,
    relatorio_datasets: dict,
    log: logging.Logger,
):
    """Gera relatório de qualidade em HTML com CSS inline."""
    log.info("📄 Gerando relatório de qualidade em HTML...")

    # Calcular metricas granulares para o relatorio
    pedidos_unicos = df["order_id"].nunique()
    avaliados = df.loc[df["pedido_item_seq"] == 1, "tem_avaliacao"].sum()
    pct_avaliados = (avaliados / pedidos_unicos * 100) if pedidos_unicos > 0 else 0

    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Tabela comparativa de nulos
    all_cols = sorted(set(nulos_antes.index) | set(nulos_depois.index))
    nulos_rows = ""
    for col in all_cols:
        antes_val = int(nulos_antes.get(col, 0))
        depois_val = int(nulos_depois.get(col, 0))
        antes_pct = f"{antes_val / shape_antes[0] * 100:.2f}%" if shape_antes[0] > 0 else "0%"
        depois_pct = f"{depois_val / shape_depois[0] * 100:.2f}%" if shape_depois[0] > 0 else "0%"
        cor = ' style="background-color:#ffe0e0;"' if depois_val > 0 else ""
        nulos_rows += f"<tr{cor}><td>{col}</td><td>{antes_val:,}</td><td>{antes_pct}</td><td>{depois_val:,}</td><td>{depois_pct}</td></tr>\n"

    # Decisões tomadas
    decisoes = [
        ("order_item_id / price / freight_value",
         "Cruzamento com order_status: nulos predominantemente em canceled/unavailable. "
         "Registros mantidos, valores preenchidos com 0.",
         f"Distribuicao: {relatorio_nulos.get('item_nulos', {}).get('distribuicao_status', {})}"),
        ("order_delivered_customer_date",
         "Nulos em pedidos 'delivered' sao anomalias graves e foram REMOVIDOS. "
         "Nulos em outros status sao esperados (pedido nao entregue) e mantidos como NaT.",
         f"Delivered sem data removidos: {relatorio_nulos.get('entrega_nulos', {}).get('delivered_sem_data', 0)}"),
        ("review_score",
         "Coluna booleana 'tem_avaliacao' criada ANTES do fillna. "
         "Nulos preenchidos com 0 para representar 'sem avaliacao'.",
         f"Total de nulos originais: {relatorio_nulos.get('review_nulos', 0):,}"),
        ("product_category",
         "Preenchidos com 'sem categoria'. Nenhum registro removido.",
         f"Total de nulos preenchidos: {relatorio_nulos.get('categoria_nulos', 0):,}"),
    ]
    decisoes_rows = ""
    for col, decisao, detalhe in decisoes:
        decisoes_rows += f"<tr><td>{col}</td><td>{decisao}</td><td>{detalhe}</td></tr>\n"

    # Anomalias detectadas
    anomalias_rows = ""
    anomalia_items = [
        ("Precos/fretes negativos", relatorio_anomalias.get("negativos", 0)),
        ("Tempo entrega negativo (delivered)", relatorio_anomalias.get("tempo_negativo", 0)),
        ("Review score fora de [0-5]", relatorio_anomalias.get("score_invalido", 0)),
        ("Datas futuras", relatorio_anomalias.get("datas_futuras", 0)),
        ("Duplicatas (order_id + order_item_id)", relatorio_anomalias.get("duplicatas", 0)),
    ]
    for nome, qtd in anomalia_items:
        cor = ' style="background-color:#ffe0e0;"' if qtd > 0 else ""
        anomalias_rows += f"<tr{cor}><td>{nome}</td><td>{qtd:,}</td></tr>\n"

    # Distribuição de status nos nulos de order_item_id
    dist_status = relatorio_nulos.get("item_nulos", {}).get("distribuicao_status", {})
    dist_rows = ""
    for status, cnt in sorted(dist_status.items(), key=lambda x: -x[1]):
        dist_rows += f"<tr><td>{status}</td><td>{cnt:,}</td></tr>\n"

    # Primeiras 5 linhas
    df_head = df.head(5)
    head_headers = "".join(f"<th>{c}</th>" for c in df_head.columns)
    head_rows = ""
    for _, row in df_head.iterrows():
        cells = "".join(f"<td>{v}</td>" for v in row.values)
        head_rows += f"<tr>{cells}</tr>\n"

    # Estatísticas descritivas
    num_cols = ["price", "freight_value", "review_score", "tempo_entrega_dias", "product_weight_g"]
    num_cols_exist = [c for c in num_cols if c in df.columns]
    desc = df[num_cols_exist].describe().round(2)
    desc_headers = "<th>Estatistica</th>" + "".join(f"<th>{c}</th>" for c in desc.columns)
    desc_rows = ""
    for stat in desc.index:
        cells = f"<td><strong>{stat}</strong></td>" + "".join(f"<td>{desc.loc[stat, c]}</td>" for c in desc.columns)
        desc_rows += f"<tr>{cells}</tr>\n"

    # --- ENRIQUECIMENTO ESTRATÉGICO ---
    # Distribuição de Pagamentos
    pagamento_rows = ""
    if "payment_type" in df.columns:
        pay_dist = df[df['pedido_item_seq'] == 1]['payment_type'].value_counts()
        pay_total = pay_dist.sum()
        for tipo, qtd in pay_dist.items():
            pct = qtd / pay_total * 100
            pagamento_rows += f"<tr><td>{tipo}</td><td>{qtd:,}</td><td>{pct:.1f}%</td></tr>\n"

    # Taxa de Recorrência
    recorrencia_html = ""
    if "customer_unique_id" in df.columns:
        clientes_unicos = df['customer_unique_id'].nunique()
        compras_por_cliente = df[df['pedido_item_seq'] == 1].groupby('customer_unique_id')['order_id'].nunique()
        clientes_recorrentes = (compras_por_cliente > 1).sum()
        pct_recorrencia = (clientes_recorrentes / clientes_unicos * 100) if clientes_unicos > 0 else 0
        recorrencia_html = f"""
        <div class="summary-box">
            Clientes Unicos<br>
            <strong>{clientes_unicos:,}</strong>
        </div>
        <div class="summary-box">
            Clientes Recorrentes<br>
            <strong>{clientes_recorrentes:,} ({pct_recorrencia:.1f}%)</strong>
        </div>
        """

    # Estatísticas de Peso
    peso_html = ""
    if "product_weight_g" in df.columns:
        peso_valido = df['product_weight_g'].dropna()
        if len(peso_valido) > 0:
            peso_medio = peso_valido.mean()
            peso_mediana = peso_valido.median()
            peso_max = peso_valido.max()
            peso_html = f"""
            <div class="summary-box">
                Peso Medio (g)<br>
                <strong>{peso_medio:,.0f}g</strong>
            </div>
            <div class="summary-box">
                Peso Mediana (g)<br>
                <strong>{peso_mediana:,.0f}g</strong>
            </div>
            <div class="summary-box">
                Peso Maximo (g)<br>
                <strong>{peso_max:,.0f}g</strong>
            </div>
            """

    html = f"""<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <title>Relatorio de Qualidade — Olist ETL</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', Arial, sans-serif;
            background: #ffffff;
            color: #222;
            padding: 40px 60px;
            line-height: 1.6;
        }}
        h1 {{
            font-size: 28px;
            border-bottom: 3px solid #2c3e50;
            padding-bottom: 10px;
            margin-bottom: 8px;
            color: #2c3e50;
        }}
        .timestamp {{
            font-size: 13px;
            color: #888;
            margin-bottom: 30px;
        }}
        h2 {{
            font-size: 20px;
            color: #34495e;
            margin-top: 35px;
            margin-bottom: 12px;
            border-left: 4px solid #3498db;
            padding-left: 12px;
        }}
        table {{
            border-collapse: collapse;
            width: 100%;
            margin-bottom: 25px;
            font-size: 14px;
        }}
        th {{
            background: #2c3e50;
            color: #fff;
            padding: 10px 14px;
            text-align: left;
            font-weight: 600;
        }}
        td {{
            padding: 8px 14px;
            border-bottom: 1px solid #ddd;
        }}
        tr:nth-child(even) {{ background: #f8f9fa; }}
        tr:hover {{ background: #eef2f7; }}
        .summary-box {{
            display: inline-block;
            background: #f0f4f8;
            border: 1px solid #d0d7de;
            border-radius: 6px;
            padding: 14px 22px;
            margin: 6px 12px 6px 0;
            font-size: 14px;
        }}
        .summary-box strong {{
            display: block;
            font-size: 22px;
            color: #2c3e50;
        }}
        .badge-ok {{
            display: inline-block;
            background: #d4edda;
            color: #155724;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
        .badge-warn {{
            display: inline-block;
            background: #fff3cd;
            color: #856404;
            padding: 2px 8px;
            border-radius: 4px;
            font-size: 12px;
        }}
    </style>
</head>
<body>
    <h1>Relatorio de Qualidade — Olist ETL</h1>
    <p class="timestamp">Gerado em: {ts}</p>

    <div>
        <div class="summary-box">
            Shape Antes<br>
            <strong>{shape_antes[0]:,} x {shape_antes[1]}</strong>
        </div>
        <div class="summary-box">
            Shape Depois<br>
            <strong>{shape_depois[0]:,} x {shape_depois[1]}</strong>
        </div>
        <div class="summary-box">
            Registros Removidos<br>
            <strong>{shape_antes[0] - shape_depois[0]:,}</strong>
        </div>
        <div class="summary-box">
            Pedidos unicos<br>
            <strong>{pedidos_unicos:,}</strong>
        </div>
        <div class="summary-box">
            Pedidos Avaliados<br>
            <strong>{pct_avaliados:.1f}%</strong>
        </div>
    </div>

    <h2>Comparativo de Nulos: Antes vs Depois</h2>
    <table>
        <tr><th>Coluna</th><th>Nulos Antes</th><th>% Antes</th><th>Nulos Depois</th><th>% Depois</th></tr>
        {nulos_rows}
    </table>

    <h2>Decisoes de Tratamento (com Justificativa)</h2>
    <table>
        <tr><th>Coluna(s)</th><th>Decisao</th><th>Detalhe</th></tr>
        {decisoes_rows}
    </table>

    <h2>Anomalias Detectadas</h2>
    <table>
        <tr><th>Tipo de Anomalia</th><th>Quantidade</th></tr>
        {anomalias_rows}
    </table>

    <h2>Distribuicao de order_status nos Nulos de order_item_id</h2>
    <table>
        <tr><th>order_status</th><th>Quantidade</th></tr>
        {dist_rows}
    </table>

    <h2>Primeiras 5 Linhas do DataFrame Final</h2>
    <div style="overflow-x:auto;">
    <table>
        <tr>{head_headers}</tr>
        {head_rows}
    </table>
    </div>

    <h2>Meses Removidos por Volume Insuficiente</h2>
    {{meses_section}}

    <h2>Estatisticas Descritivas</h2>
    <table>
        <tr>{desc_headers}</tr>
        {desc_rows}
    </table>

    <h2>Enriquecimento Estrategico: Novas Dimensoes</h2>

    <h3 style="color:#34495e; margin-top:20px;">Distribuicao de Metodos de Pagamento</h3>
    <table>
        <tr><th>Metodo</th><th>Pedidos</th><th>%</th></tr>
        {pagamento_rows}
    </table>

    <h3 style="color:#34495e; margin-top:20px;">Taxa de Fidelizacao (Recorrencia)</h3>
    <div>{recorrencia_html}</div>

    <h3 style="color:#34495e; margin-top:20px;">Perfil Fisico dos Produtos</h3>
    <div>{peso_html}</div>

    <h2>Guia de Granularidade (Anti-Erro)</h2>
    <div style="background: #eef2f7; border-left: 4px solid #2980b9; padding: 15px; margin-bottom: 20px;">
        <p><strong>Atenção:</strong> O Olist possui a seguinte hierarquia: Um pedido pode ter vários itens. O dataset atual possui <strong>uma linha por ITEM</strong>, o que significa que o mesmo pedido (e sua avaliacão) pode se repetir várias vezes.</p>
        <p>Para evitar somar as mesmas avaliacoes multiplas vezes (passando de 100%), use a coluna <code>pedido_item_seq</code> criada neste ETL:</p>
        <ul>
            <li><strong>Métricas por Pedido (Satisfacao, Status):</strong> Filtre usando <code>df[df['pedido_item_seq'] == 1]</code> para considerar apenas 1 linha por pedido.</li>
            <li><strong>Métricas por Item (Receita, Categorias, Frete):</strong> Nao faca nenhum filtro, use <code>df</code> completo. O preco de cada item deve ser somado.</li>
        </ul>
    </div>

    <h2>Datasets Gerados</h2>
    {{datasets_section}}

</body>
</html>"""

    # Gerar secao de meses truncados
    meses_removidos = relatorio_meses.get("meses_removidos", [])
    periodo = relatorio_meses.get("periodo_final", ("", ""))
    total_meses = relatorio_meses.get("total_meses_validos", 0)

    if meses_removidos:
        meses_table_rows = ""
        for m in meses_removidos:
            meses_table_rows += f'<tr style="background-color:#ffe0e0;"><td>{m["mes"]}</td><td>{m["pedidos"]}</td><td>{m["motivo"]}</td></tr>\n'
        meses_section = f"""
    <table>
        <tr><th>Mes</th><th>Pedidos Unicos</th><th>Motivo da Remocao</th></tr>
        {meses_table_rows}
    </table>
    <p><strong>Periodo final de analise:</strong> {periodo[0]} ate {periodo[1]} ({total_meses} meses validos)</p>
"""
    else:
        meses_section = f'<p>Nenhum mes removido. Todos os meses possuem volume suficiente.</p>\n<p><strong>Periodo:</strong> {periodo[0]} ate {periodo[1]} ({total_meses} meses)</p>'

    html = html.replace("{meses_section}", meses_section)

    # Gerar secao de datasets gerados
    rec_linhas = relatorio_datasets.get('receita_linhas', 0)
    comp_linhas = relatorio_datasets.get('completo_linhas', 0)
    datasets_section = f"""
    <table>
        <tr><th>Arquivo</th><th>Linhas</th><th>Descricao / Regra de Uso</th></tr>
        <tr><td><code>olist_receita.parquet</code></td><td>{rec_linhas:,}</td><td>
            <strong>Pedidos com valor monetario real.</strong><br>
            Remove Cancelados e problemas de estoque que nao geraram receita. <br>
            <em>Use para: Faturamento, crescimentos mensais, ticket medio.</em>
        </td></tr>
        <tr><td><code>olist_completo.parquet</code></td><td>{comp_linhas:,}</td><td>
            <strong>Analise operacional e logistica completa.</strong><br>
            Mantem todos os registros originais. <br>
            <em>Use para: Analise de churn, funil de status, logistica das entregas.</em>
        </td></tr>
        <tr><td><code>olist_processado.parquet</code></td><td>{comp_linhas:,}</td><td>Dataset compatibilidade antiga.</em></td></tr>
    </table>
"""
    html = html.replace("{datasets_section}", datasets_section)

    OUTPUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_REPORT, "w", encoding="utf-8") as f:
        f.write(html)
    log.info(f"   ✅ Relatorio salvo em: {OUTPUT_REPORT}")


# ─────────────────────────────────────────────────────────────────────
# MAIN
# ─────────────────────────────────────────────────────────────────────

def main():
    log = setup_logging()
    log.info("=" * 70)
    log.info(f"🚀 OLIST ETL — Inicio da execucao: {TIMESTAMP_RUN}")
    log.info("=" * 70)

    con = None
    try:
        if not RAW_DIR.exists():
            raise FileNotFoundError(f"Diretorio de dados nao encontrado: {RAW_DIR}")

        con = duckdb.connect(database=":memory:")
        log.info("✅ DuckDB conectado (in-memory)")

        # Etapa 1 — Carregar CSVs
        tabelas = etapa_carregar_csvs(con, log)

        # Etapa 2 — Deduplicar reviews
        etapa_dedup_reviews(con, log)

        # Etapa 3 — JOIN
        df = etapa_join(con, log)
        shape_original = df.shape
        nulos_antes = df.isnull().sum()

        # Etapa 4 — Investigar nulos (sem alterar dados)
        relatorio_nulos = etapa_investigar_nulos(df, log)

        # Etapa 5 — Tratar nulos
        df = etapa_tratar_nulos(df, log)

        # Etapa 6 — Anomalias
        df, relatorio_anomalias = etapa_anomalias(df, log)

        # Etapa 7 — Colunas derivadas
        df = etapa_colunas_derivadas(df, log)

        # Etapa 7.5 — Filtrar meses truncados
        df, relatorio_meses = etapa_filtrar_meses_truncados(df, log)

        nulos_depois = df.isnull().sum()
        shape_final = df.shape

        # Etapa 8 — Salvar e validar
        etapa_salvar_e_validar(df, log)

        # Etapa 9 — Gerar parquets derivados
        relatorio_datasets = etapa_gerar_parquets_derivados(df, log)

        # Relatório HTML
        gerar_relatorio_html(
            df=df,
            nulos_antes=nulos_antes,
            nulos_depois=nulos_depois,
            shape_antes=shape_original,
            shape_depois=shape_final,
            relatorio_nulos=relatorio_nulos,
            relatorio_anomalias=relatorio_anomalias,
            relatorio_meses=relatorio_meses,
            relatorio_datasets=relatorio_datasets,
            log=log,
        )

        log.info("\n" + "=" * 70)
        log.info("🎉 ETL FINALIZADO COM SUCESSO")
        log.info("=" * 70)

    except Exception:
        log.error(f"\n❌ ERRO FATAL NO PIPELINE ETL")
        log.error(traceback.format_exc())
        sys.exit(1)

    finally:
        if con:
            try:
                con.close()
            except Exception:
                pass


if __name__ == "__main__":
    main()
