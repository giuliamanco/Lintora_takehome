import duckdb
import matplotlib.pyplot as plt
import seaborn as sns
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score

conn = duckdb.connect()

# =========================================================================
# DATA EXTRACTION & FEATURE ENGINEERING (FIRST 5 DAYS)
# =========================================================================

query = """
WITH start_account AS (
SELECT
    a.account_id,
    DATE_TRUNC('day', a.created_at)::DATE AS day,
    a.acquisition_channel as acquisition_channel,
    a.company_size as company_size
FROM 'product/accounts.csv' a
),
events_5_days AS (
SELECT
    b.account_id,
    SUM(CASE WHEN b.event_name = 'session_start' THEN 1 ELSE 0 END) AS session_start_first_5_days,
    SUM(CASE WHEN b.event_name = 'repo_connected' THEN 1 ELSE 0 END) AS repo_connected_first_5_days,
    SUM(CASE WHEN b.event_name = 'ci_integration_connected' THEN 1 ELSE 0 END) AS ci_integration_connected_first_5_days,
    SUM(CASE WHEN b.event_name = 'ai_fix_accepted' THEN 1 ELSE 0 END) AS ai_fix_accepted_first_5_days,
    SUM(CASE WHEN b.event_name = 'user_invited' THEN 1 ELSE 0 END) AS user_invited_first_5_days,
    COUNT(b.event_id) AS total_events_first_5_days
FROM 'product/events.csv' b
JOIN start_account a ON b.account_id = a.account_id
WHERE b.event_timestamp <= a.day + INTERVAL 5 DAY
GROUP BY b.account_id
)
SELECT
    s.account_id,
    s.acquisition_channel,
    s.company_size,
    COALESCE(e.session_start_first_5_days, 0) as session_start_first_5_days,
    COALESCE(e.repo_connected_first_5_days, 0) as repo_connected_first_5_days,
    COALESCE(e.ci_integration_connected_first_5_days, 0) as ci_integration_connected_first_5_days,
    COALESCE(e.ai_fix_accepted_first_5_days, 0) as ai_fix_accepted_first_5_days,
    COALESCE(e.user_invited_first_5_days, 0) as user_invited_first_5_days,
    COALESCE(e.total_events_first_5_days, 0) as total_events_first_5_days,
    CASE WHEN c.account_id IS NOT NULL THEN 1 ELSE 0 END AS has_subscription
FROM start_account s
LEFT JOIN events_5_days e ON s.account_id = e.account_id
LEFT JOIN 'product/subscriptions.csv' c ON s.account_id = c.account_id
WHERE s.day <= '2026-06-15'
"""

result = conn.sql(query)
df = result.df()

# =========================================================================
# MACHINE LEARNING PIPELINE PREPARATION & TRAINING
# =========================================================================
# Features (X) vs Target Variable (y)
# Random Forest Classifier to predict subscription based on first 5 days events

X = df.drop(columns=['account_id', 'has_subscription'])
y = df['has_subscription']

X_encoded = pd.get_dummies(X, drop_first=True)

# Train/Test Validation Split (80% Train, 20% Evaluation)
X_train, X_test, y_train, y_test = train_test_split(X_encoded, y, test_size=0.2, random_state=42, stratify=y)

# Initialize and Train Random Forest Classifier
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# =========================================================================
# MODEL PERFORMANCE EVALUATION
# =========================================================================
y_pred = model.predict(X_test)
print("\n--- Model Evaluation Summary ---")
print(" Model Accuracy:", accuracy_score(y_test, y_pred)*100)
print("\nClassification Report:")
print(classification_report(y_test, y_pred))

# Print Text Feature Importance
print("\n--- Feature Importance Table ---")
importances = model.feature_importances_
indices = np.argsort(importances)[::-1]
for f in range(X_encoded.shape[1]):
    print(f"{X_encoded.columns[indices[f]]}: {importances[indices[f]]:.4f}")

# =========================================================================
# FEATURE IMPORTANCE PLOT GENERATION
# =========================================================================
feature_data = pd.DataFrame({'Feature': X_encoded.columns,'Importance': model.feature_importances_}).sort_values(by='Importance', ascending=False)
feature_data_top10 = feature_data.head(10)

# Ensure the AI Fix feature is explicitly included in the plot to show its 0.00% weight
if 'ai_fix_accepted_first_5_days' not in feature_data_top10['Feature'].values:
    ai_row = feature_data[feature_data['Feature'] == 'ai_fix_accepted_first_5_days']
    feature_data_top10 = pd.concat([feature_data_top10, ai_row])

plt.figure(figsize=(10, 6))
sns.set_theme(style="whitegrid")
palette = sns.color_palette("Blues_r", n_colors=len(feature_data_top10))
ax = sns.barplot(
    x="Importance",
    y="Feature",
    data=feature_data_top10,
    hue="Feature",
    palette=palette,
    dodge=False,
    legend=False
)
plt.title("Trial Conversion Model - Top Feature Importances", fontsize=14, fontweight='bold', pad=15)
plt.xlabel("Importance Score (Relative Weight)", fontsize=12, labelpad=10)
plt.ylabel("Early Behavioral Features (First 5 Days)", fontsize=12, labelpad=10)

for p in ax.patches:
    width = p.get_width()
    ax.text(width + 0.005, p.get_y() + p.get_height()/2 + 0.05, f'{width:.4f}', 
            ha="left", va="center", fontsize=10, fontweight='bold', color='#333333')

plt.tight_layout()
plt.savefig("figures/plot9_ml_feature_importance.png", dpi=300) # Auto-save
plt.show()           