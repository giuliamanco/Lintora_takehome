import duckdb
import pandas as pd
import matplotlib.pyplot as plt

# Global configuration flag
SHOW_PLOTS = True  # Set to False if you want to run the script without pop-up windows

conn = duckdb.connect()

# ==================================================================================================================================
# 1  TRIAL TO SUBSCRIPTION CONVERSION
# ===============================================================================================

# Check the rate of accounts conversion to subscriptions over time
query1 = """
SELECT
    (DATE_TRUNC('month', created_at)+ INTERVAL 1 MONTH - INTERVAL 1 DAY)::DATE AS month,
    COUNT(DISTINCT a.account_id) AS account_started,
    COUNT(DISTINCT s.account_id) AS subscription_started,
    COUNT(s.account_id) * 100.0 /COUNT(a.account_id) AS ratio
FROM 'product/accounts.csv' a
LEFT JOIN 'product/subscriptions.csv' s ON a.account_id = s.account_id
GROUP BY month 
ORDER BY month ASC
""" 

result1 = conn.sql(query1)
df1 = result1.df()

df1['month'] = pd.to_datetime(df1['month']).dt.strftime('%b %Y')

#Plot 1: Conversion Rate Trend
plt.figure(figsize=(12, 6))
plt.plot(df1['month'], df1['ratio'], label='Trial of Conversion Rate', marker='o', linestyle='-')
plt.xlabel('Month')
plt.ylabel('Conversion Rate (%)')
plt.title('Account to Subscription Conversion')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig('figures/plot1_conversion_rate.png', dpi=300) # Auto-save

#Plot2 Account Trials and Subscription Started Over Time
plt.figure(figsize=(12, 6))
plt.plot(df1['month'], df1['account_started'], label='Trial Started', marker='o', linestyle='-')
plt.plot(df1['month'], df1['subscription_started'], label='Subscription Started', marker='o', linestyle='-')
plt.xlabel('Month')
plt.ylabel('Count')
plt.title('Account Trials vs Subscription Started')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig('figures/plot2_trial_subscription.png', dpi=300) # Auto-save

# ==================================================================================================================================
# 2  INVESTIGATION OF PAID SOCIAL CHANNEL BUDGET CUT AND IMPACT ON CONVERSION
# ===============================================================================================

# Check the rate of accounts conversion to subscriptions over time for paid social channel
query2 = """
SELECT
    (DATE_TRUNC('month', created_at)+ INTERVAL 1 MONTH - INTERVAL 1 DAY)::DATE AS month,
    COUNT(DISTINCT a.account_id) AS account_started_social,
    COUNT(DISTINCT s.account_id) AS subscription_started_social,
    subscription_started_social * 100.0 /account_started_social AS conversion_rate_social
FROM 'product/accounts.csv' a
LEFT JOIN 'product/subscriptions.csv' s ON a.account_id = s.account_id 
WHERE a.acquisition_channel = 'paid_social'
GROUP BY month 
ORDER BY month ASC
""" 

result2 = conn.sql(query2)
df2 = result2.df()

df2['month'] = pd.to_datetime(df2['month']).dt.strftime('%b %Y')

#Plot 3: Paid Social Conversion Rate Trend 
plt.figure(figsize=(12, 6))
plt.plot(df2['month'], df2['conversion_rate_social'], label='Paid Social Conversion', marker='o', linestyle='-')
plt.xlabel('Month')
plt.ylabel('Paid Social Conversion Rate (%)')
plt.title('Account to Subscription Conversion')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig('figures/plot3_paid_social_conversion.png', dpi=300) # Auto-save

#Plot 4: Account and Subscription Started Over Time for Paid Social Channel
plt.figure(figsize=(12, 6))
plt.plot(df2['month'], df2['account_started_social'], label='Accounts by social paid', marker='o', linestyle='-')
plt.plot(df2['month'], df2['subscription_started_social'], label='Subscriptions by social paid', marker='o', linestyle='-')
plt.xlabel('Month')
plt.ylabel('Count')
plt.title('Paid Social Account and Subscription Started Over Time')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig('figures/plot4_paid_social_accounts_sub.png', dpi=300) # Auto-save

# =========================================================================
# SECTION 3: MARKETING BUDGET CORRELATION ANALYSIS
# =========================================================================

#Check a budget cut around March 2026
query3 = """
SELECT
    month,
    ANY_VALUE(spend_usd) AS budget_spent_social
FROM 'product/marketing_spend_monthly.csv' 
WHERE channel = 'paid_social'
GROUP BY month 
ORDER BY month ASC
""" 

# Calculate the drop between March 2026 (index 14) and April 2026 (index 15)
result3 = conn.sql(query3)
df3 = result3.df()

decrease = (df3['budget_spent_social'][14] - df3['budget_spent_social'][15])/(df3['budget_spent_social'][14])
print(f"{round(decrease * 100, 2)}% decrease in paid social budget from March to April")

#Plot 5: Marketing Spend on Paid Social
plt.figure(figsize=(12, 6))
plt.plot(df3['month'], df3['budget_spent_social'], label='Budget Spent on Paid Social', marker='o', linestyle='-')
plt.xlabel('Month')
plt.ylabel('Budget Spent (USD)')
plt.title('Marketing Spend: Paid Social')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig('figures/plot5_marketing_spend.png', dpi=300) # Auto-save

# =========================================================================
# SECTION 4: SOFTWARE VERSION QUALITY
# =========================================================================

query4 = """
SELECT
    DATE_TRUNC('month', a.week_start)::DATE AS month, 
    SUM(a.issues_dismissed_false_positive) AS false_positive,
    SUM(a.issues_raised) AS issues_raised,
    SUM(a.issues_fixed) AS fixed_issues,
    
    SUM(a.issues_dismissed_false_positive) / SUM(a.issues_raised) AS false_positive_normalized,
    SUM(a.issues_fixed) / SUM(a.issues_raised) AS fixed_issues_normalized
    
FROM 'product/issue_activity_weekly.csv' a
WHERE a.week_start >= '2025-02-01'
GROUP BY month
ORDER BY month ASC
"""

result4 = conn.sql(query4)
df4 = result4.df()

# Plot 6: False Positive Trend
plt.figure(figsize=(12, 6))
plt.plot(df4['month'], df4['false_positive_normalized'], label='False Positive Rate (%)', marker='o', linestyle='-')
plt.xlabel('Month')
plt.ylabel('Normalized Rate (%)')
plt.title('False Positive Rate Trend')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig('figures/plot6_false_positives.png', dpi=300) # Auto-save

# Plot 7: Fixed Issues Trend
plt.figure(figsize=(12, 6))
plt.plot(df4['month'], df4['fixed_issues_normalized'], label='Fixed Issue Rate (%)', marker='o', linestyle='-')
plt.xlabel('Month')
plt.ylabel('Normalized Rate (%)')
plt.title('Fixed Issues Rate Trend')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig('figures/plot7_fixed_issues.png', dpi=300) # Auto-save


# =========================================================================
# SECTION 5: COHORT SUBSCRIPTION CHURN & AI FEATURE ADOPTION
# =========================================================================

query5 = """
WITH ai_users AS (
SELECT
    DATE_TRUNC('month', event_timestamp)::DATE AS month, 
    a.account_id 
FROM 'product/events.csv' a
WHERE a.event_timestamp >= '2025-06-01' AND a.event_name = 'ai_fix_accepted'
)

SELECT 
    DATE_TRUNC('month', s.start_date)::DATE AS month,
    COUNT(DISTINCT CASE WHEN s.status = 'active' THEN s.account_id END) AS total_active_accounts,
    COUNT(DISTINCT CASE WHEN s.status = 'active' THEN  ai.account_id END) AS ai_active_users,
    
    -- Adoption rate: percentage of active accounts that have adopted AI features
    ROUND( COUNT(DISTINCT CASE WHEN s.status = 'active' THEN ai.account_id END) * 100.0 / NULLIF(COUNT(DISTINCT CASE WHEN s.status = 'active' THEN  s.account_id END), 0), 2) AS adoption_rate,

    COUNT(DISTINCT CASE WHEN s.status = 'canceled' THEN s.account_id END) AS total_canceled_accounts,
    COUNT(DISTINCT CASE WHEN s.status = 'canceled' THEN  ai.account_id END) AS ai_canceled_users,
    
    -- Churn rate: percentage of active accounts that have canceled their subscription for AI ,
    ROUND( COUNT(DISTINCT CASE WHEN s.status = 'canceled' THEN ai.account_id END) *100.0 / NULLIF(COUNT(DISTINCT ai.account_id), 0), 2) AS churn_ai_rate,
    -- Churn rate: percentage of active accounts that have canceled their subscription for non-AI,
    ROUND( (COUNT(DISTINCT CASE WHEN s.status = 'canceled' THEN s.account_id END) - COUNT(DISTINCT CASE WHEN s.status = 'canceled' THEN ai.account_id END))* 100.0 / NULLIF(COUNT(DISTINCT CASE WHEN s.status = 'active' THEN  s.account_id END), 0), 2) AS churn_no_ai_rate    
FROM 'product/subscriptions.csv' s
LEFT JOIN ai_users ai ON s.account_id = ai.account_id AND DATE_TRUNC('month', s.start_date)::DATE = ai.month 
WHERE s.start_date >= '2025-06-01'
GROUP BY  DATE_TRUNC('month', s.start_date)::DATE
ORDER BY  DATE_TRUNC('month', s.start_date)::DATE ASC
"""

result5 = conn.sql(query5)
df5 = result5.df()

# Plot 8: AI Feature Adoption vs Churn Segmentation
plt.figure(figsize=(12, 6))
plt.plot(df5['month'], df5['adoption_rate'], label='Adoption Rate', marker='o', linestyle='-')
plt.plot(df5['month'], df5['churn_ai_rate'], label='Churn Rate (AI)', marker='s', linestyle='--')
plt.plot(df5['month'], df5['churn_no_ai_rate'], label='Churn Rate (Non-AI)', marker='^', linestyle='-.')
plt.xlabel('Cohort Subscription Month')
plt.ylabel('Percentage (%)')
plt.title('')
plt.xticks(rotation=45)
plt.legend()
plt.tight_layout()
plt.savefig('figures/plot8_ai_churn_cohorts.png', dpi=300) # Auto-save

print("\nAll plots have been automatically saved as PNG images in the /figures directory.")
# =========================================================================
# PLOT SHOW
# =========================================================================
if SHOW_PLOTS:
    print("Plot visualization...")
    plt.show()
else:
    print("Skipping pop-up windows (SHOW_PLOTS = False).")
    plt.close('all')
