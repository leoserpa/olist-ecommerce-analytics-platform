"""
RFM Clustering Trainer - Olist Brazilian E-Commerce
==================================================
Script profissional para segmentação de clientes utilizando RFM + K-Means.
Gera modelos persistentes (.pkl) e relatório de métricas (.json).

Uso no Colab: Copie todo este conteúdo para uma célula e execute.
"""

# 🚀 COPIE DAQUI PARA O COLAB
# !pip install pandas==2.3.2 numpy==2.3.2 scikit-learn==1.7.2 yellowbrick==1.5 joblib==1.5.2 -U

import pandas as pd
import numpy as np
import os
import json
import joblib
from datetime import datetime
from sklearn.preprocessing import StandardScaler
from sklearn.cluster import KMeans
from sklearn.metrics import silhouette_score

def train_rfm_clustering():
    # 1. Configurar caminhos robustos
    # No Colab o arquivo pode estar na raiz ou em 'data/'
    data_path = 'data/olist_receita.parquet'
    if not os.path.exists(data_path):
        data_path = 'olist_receita.parquet'
        
    if not os.path.exists(data_path):
        print(f"❌ Erro: Arquivo '{data_path}' não encontrado. Faça o upload do dataset!")
        return

    # Criar pastas para exportação
    os.makedirs('ml/models', exist_ok=True)
    os.makedirs('ml/reports', exist_ok=True)

    # 2. Carregar Dados
    print("📂 Carregando dados para RFM...")
    df = pd.read_parquet(data_path)

    # 3. Engenharia de Features (RFM)
    print("🧮 Calculando métricas RFM...")
    snapshot_date = df['order_purchase_timestamp'].max() + pd.Timedelta(days=1)
    
    rfm = df.groupby('customer_unique_id').agg({
        'order_purchase_timestamp': lambda x: (snapshot_date - x.max()).days,
        'order_id': 'nunique',
        'price': lambda x: (x + df.loc[x.index, 'freight_value']).sum()
    }).rename(columns={
        'order_purchase_timestamp': 'Recency',
        'order_id': 'Frequency',
        'price': 'Monetary'
    })

    # 4. Pré-processamento Profissional
    print("🧹 Pré-processando (Log + Scaling)...")
    # Log Transformation para remover assimetria (skewness)
    rfm_log = np.log1p(rfm) # Log(x+1)
    
    # Scaling
    scaler = StandardScaler()
    rfm_scaled = scaler.fit_transform(rfm_log)

    # 5. Treinamento do Modelo (K-Means)
    # defini o K=5 como um bom equilíbrio entre 
    # granularidade e interpretabilidade para o Olist, mas o script pode ser adaptado.
    k_ideal = 5 
    print(f"🚀 Treinando K-Means com K={k_ideal}...")
    kmeans = KMeans(n_clusters=k_ideal, random_state=42, n_init=10)
    clusters = kmeans.fit_predict(rfm_scaled)
    
    rfm['Cluster'] = clusters

    # 6. Cálculo de Métricas de Performance
    print("📊 Gerando métricas de validação...")
    sil_score = silhouette_score(rfm_scaled, clusters)
    
    # Perfil dos Clusters (Médias)
    profiling = rfm.groupby('Cluster').agg({
        'Recency': 'mean',
        'Frequency': 'mean',
        'Monetary': 'mean',
        'Cluster': 'count'
    }).rename(columns={'Cluster': 'Customer_Count'}).to_dict('index')

    # Preparar JSON de métricas
    metrics = {
        "algorithm": "K-Means",
        "n_clusters": k_ideal,
        "silhouette_score": float(sil_score),
        "timestamp": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "cluster_profiles": profiling
    }

    # 7. Persistência de Artefatos
    print("💾 Salvando modelos e relatórios...")
    
    # Salvar modelos
    joblib.dump(scaler, 'ml/models/rfm_scaler.pkl')
    joblib.dump(kmeans, 'ml/models/rfm_kmeans.pkl')
    
    # Salvar métricas
    with open('ml/reports/rfm_metrics.json', 'w') as f:
        json.dump(metrics, f, indent=4)

    print("\n✅ Treinamento RFM Concluído!")
    print(f"📌 Modelos em: ml/models/")
    print(f"📌 Métricas em: ml/reports/rfm_metrics.json")
    print(f"📊 Silhouette Score: {sil_score:.4f}")

if __name__ == "__main__":
    train_rfm_clustering()
