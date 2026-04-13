import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.compose import ColumnTransformer
import xgboost as xgb
import joblib
import json
import os

# Biblioteca de encoders profissionais
try:
    from category_encoders import TargetEncoder
except ImportError:
    # Caso rode localmente sem o pacote (no Colab instalamos no código que te mandarei no chat)
    print("⚠️ category_encoders não encontrado. Instale com 'pip install category-encoders'")

def train_professional_pipeline():
    # 1. Carregar Dados
    print("📂 Carregando dados...")
    df = pd.read_parquet('data/olist_completo.parquet')

    # 2. Pré-processamento e Target
    # Limpeza básica (só quem avaliou)
    df_ml = df[df['review_score'] > 0].copy()
    df_ml['is_detrator'] = (df_ml['review_score'] <= 2).astype(int)

    # Engenharia de Features de Tempo
    # No ETL a coluna já é datetime, mas garantimos a extração aqui
    df_ml['dia_semana'] = df_ml['order_purchase_timestamp'].dt.day_name()
    df_ml['is_weekend'] = df_ml['order_purchase_timestamp'].dt.weekday.isin([5, 6]).astype(int)

    # Colunas para o modelo
    num_features = [
        'price', 'freight_value', 'tempo_entrega_dias', 
        'atraso_entrega_dias', 'pct_frete', 'product_weight_g', 'hora_compra'
    ]
    cat_features = ['customer_state', 'product_category', 'payment_type', 'dia_semana']
    
    features = num_features + cat_features
    X = df_ml[features]
    y = df_ml['is_detrator']

    # 3. Split Estratificado
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42, stratify=y)

    # 4. Construção do Pipeline Profissional com ColumnTransformer
    # Separamos o que é número do que é texto para não dar erro de "mediana em string"
    numeric_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='median'))
    ])

    categorical_transformer = Pipeline(steps=[
        ('imputer', SimpleImputer(strategy='constant', fill_value='missing')),
        ('encoder', TargetEncoder())
    ])

    preprocessor = ColumnTransformer(
        transformers=[
            ('num', numeric_transformer, num_features),
            ('cat', categorical_transformer, cat_features)
        ])

    pipeline = Pipeline(steps=[
        ('preprocessor', preprocessor),
        ('xgb', xgb.XGBClassifier(
            n_estimators=300,
            max_depth=6,
            learning_rate=0.05,
            scale_pos_weight=(y_train == 0).sum() / (y_train == 1).sum(),
            random_state=42,
            use_label_encoder=False,
            eval_metric='logloss'
        ))
    ])

    print("🚀 Treinando Pipeline Profissional...")
    pipeline.fit(X_train, y_train)

    # 5. Avaliação e Exportação de Métricas (O "Boletim")
    y_pred = pipeline.predict(X_test)
    report = classification_report(y_test, y_pred, output_dict=True)
    cm = confusion_matrix(y_test, y_pred).tolist()

    # Prepara métricas para o Dashboard
    metrics = {
        "accuracy": report["accuracy"],
        "detrator_recall": report["1"]["recall"],
        "detrator_precision": report["1"]["precision"],
        "f1_score": report["1"]["f1-score"],
        "confusion_matrix": cm,
        "feature_importance": dict(zip(features, pipeline.named_steps['xgb'].feature_importances_.tolist()))
    }

    # Criar pasta de relatórios se não existir
    os.makedirs('ml/reports', exist_ok=True)
    os.makedirs('ml/models', exist_ok=True)

    with open('ml/reports/ml_metrics.json', 'w') as f:
        json.dump(metrics, f)

    # 6. Salvar o Pipeline Robusto
    joblib.dump(pipeline, 'ml/models/satisfaction_pipeline.pkl')
    
    print("\n✅ Pipeline e Métricas Salvos!")
    print(f"📊 Performance - Recall Detrator: {metrics['detrator_recall']:.2f}")

if __name__ == "__main__":
    train_professional_pipeline()
