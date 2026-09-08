import os
import sys
import joblib
import pandas as pd
import numpy as np
import networkx as nx
import random

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, Node, Edge, GroundTruth
from ml.pure_ml import (
    pure_train_test_split, 
    PureDecisionTree, 
    PureAnomalyDetector, 
    pure_auc_roc, 
    pure_precision_recall_f1, 
    pure_adjusted_rand_index
)

def load_data():
    db = SessionLocal()
    try:
        nodes = db.query(Node).all()
        edges = db.query(Edge).all()
        ground_truth = db.query(GroundTruth).all()
        
        # Convert to dataframes
        nodes_df = pd.DataFrame([{
            "id": n.id,
            "type": n.type,
            "label": n.label,
            **n.attributes
        } for n in nodes])
        
        edges_df = pd.DataFrame([{
            "id": e.id,
            "source": e.source,
            "target": e.target,
            "type": e.type,
            "timestamp": e.timestamp,
            **e.attributes
        } for e in edges])
        
        gt_df = pd.DataFrame([{
            "node_id": gt.node_id,
            "is_criminal": gt.is_criminal,
            "role": gt.role,
            "cell_id": gt.cell_id
        } for gt in ground_truth])
        
        return nodes_df, edges_df, gt_df
    finally:
        db.close()

def build_networkx_graph(nodes_df, edges_df):
    G = nx.Graph()
    # Add all nodes
    for _, row in nodes_df.iterrows():
        G.add_node(row['id'], type=row['type'], label=row['label'])
    # Add all edges (undirected simple representation for centrality)
    for _, row in edges_df.iterrows():
        if G.has_edge(row['source'], row['target']):
            G[row['source']][row['target']]['weight'] = G[row['source']][row['target']].get('weight', 1.0) + 1.0
        else:
            G.add_edge(row['source'], row['target'], weight=1.0)
    return G

def compute_structural_features(G):
    print("Computing graph centrality metrics...")
    
    # Degree centrality
    deg_cent = nx.degree_centrality(G)
    
    # PageRank
    try:
        pagerank = nx.pagerank(G, alpha=0.85)
    except Exception as e:
        print(f"PageRank failed, using degree centrality as fallback: {e}")
        pagerank = deg_cent
        
    # Betweenness centrality
    bet_cent = nx.betweenness_centrality(G)
    
    # Closeness centrality
    cl_cent = nx.closeness_centrality(G)
    
    # Eigenvector centrality (with error handling)
    try:
        eig_cent = nx.eigenvector_centrality(G, max_iter=2000, tol=1e-05)
    except Exception as e:
        print(f"Eigenvector centrality failed, falling back to 0.0: {e}")
        eig_cent = {node: 0.0 for node in G.nodes()}
        
    # Clustering coefficient
    clust_coeff = nx.clustering(G)
    
    # k-core number
    G_simple = G.copy()
    G_simple.remove_edges_from(nx.selfloop_edges(G_simple))
    k_core = nx.core_number(G_simple)
    
    features = {}
    for node in G.nodes():
        features[node] = {
            "degree_centrality": deg_cent.get(node, 0.0),
            "pagerank": pagerank.get(node, 0.0),
            "betweenness_centrality": bet_cent.get(node, 0.0),
            "closeness_centrality": cl_cent.get(node, 0.0),
            "eigenvector_centrality": eig_cent.get(node, 0.0),
            "clustering_coefficient": clust_coeff.get(node, 0.0),
            "k_core_number": k_core.get(node, 0)
        }
    return pd.DataFrame.from_dict(features, orient='index').reset_index().rename(columns={'index': 'id'})

def train_risk_scoring_model(nodes_df, gt_df, struct_features_df, output_dir):
    print("\n--- Training Risk-Scoring Model (Node Classification) ---")
    
    # Merge structural features and ground truth
    df = nodes_df.merge(struct_features_df, on='id').merge(gt_df, left_on='id', right_on='node_id')
    
    # Handle NaNs in entity attributes (like occupation, age_band for non-persons)
    df['occupation'] = df['occupation'].fillna('N/A')
    df['age_band'] = df['age_band'].fillna('N/A')
    df['prior_cases'] = df['prior_cases'].fillna(0)
    
    # One-hot encode categoricals
    df_encoded = pd.get_dummies(df, columns=['type', 'occupation', 'age_band'], drop_first=False, dtype=float)
    
    # Drop unused ID columns and target columns
    cols_to_drop = ['id', 'label', 'node_id', 'is_criminal', 'role', 'cell_id', 'address_cluster']
    
    # Select only numeric columns to avoid string columns (like status, bank_name, cluster, model)
    numeric_df = df_encoded.select_dtypes(include=[np.number])
    feature_cols = [c for c in numeric_df.columns if c not in cols_to_drop]
    
    # Extract numerical arrays/lists
    X = df_encoded[feature_cols].values.tolist()
    y = df_encoded['is_criminal'].astype(int).tolist()
    
    # Pure Python split
    X_train, X_test, y_train, y_test = pure_train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train Pure Python Decision Tree
    tree = PureDecisionTree(max_depth=5)
    tree.fit(X_train, y_train)
    
    # Evaluate
    y_prob = [tree.predict_proba(row) for row in X_test]
    y_pred = [1 if prob >= 0.5 else 0 for prob in y_prob]
    
    auc = pure_auc_roc(y_test, y_prob)
    precision, recall, f1 = pure_precision_recall_f1(y_test, y_pred)
    
    print(f"Risk Scoring Metrics on Held-out Set (Pure Python DT):")
    print(f"  AUC-ROC:   {auc:.4f}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    
    # Save artifacts
    model_path = os.path.join(output_dir, 'risk_model.joblib')
    joblib.dump({
        'model': tree,
        'feature_cols': feature_cols,
        'explainer': tree
    }, model_path)
    print(f"Saved risk scoring model to {model_path}")
    
    return tree, feature_cols

def compute_node_pair_features(G, u, v, node_features_dict):
    cn = list(nx.common_neighbors(G, u, v))
    num_cn = len(cn)
    
    union_size = len(set(G.neighbors(u)).union(set(G.neighbors(v))))
    jaccard = num_cn / union_size if union_size > 0 else 0.0
    
    pref_attach = G.degree(u) * G.degree(v)
    
    adamic_adar = 0.0
    for w in cn:
        deg = G.degree(w)
        if deg > 1:
            adamic_adar += 1.0 / np.log(deg)
            
    u_feat = node_features_dict.get(u, {})
    v_feat = node_features_dict.get(v, {})
    
    pair_feat = {
        "common_neighbors": num_cn,
        "jaccard_coefficient": jaccard,
        "preferential_attachment": pref_attach,
        "adamic_adar_index": adamic_adar,
    }
    
    for key in ["degree_centrality", "pagerank", "betweenness_centrality", "closeness_centrality", "eigenvector_centrality", "clustering_coefficient", "k_core_number"]:
        pair_feat[f"src_{key}"] = u_feat.get(key, 0.0)
        pair_feat[f"dst_{key}"] = v_feat.get(key, 0.0)
        
    return pair_feat

def train_link_prediction_model(G, nodes_df, edges_df, gt_df, struct_features_df, output_dir):
    print("\n--- Training Link Prediction Model (Edge Classification) ---")
    
    node_feat_df = nodes_df.merge(struct_features_df, on='id')
    node_features_dict = node_feat_df.set_index('id').to_dict(orient='index')
    
    target_edge_types = ["CALL", "TRANSACTION", "CO_ACCUSED", "ASSOCIATE"]
    filtered_edges = edges_df[edges_df['type'].isin(target_edge_types)]
    
    pos_pairs = list(zip(filtered_edges['source'], filtered_edges['target']))
    pos_pairs = list(set([tuple(sorted(p)) for p in pos_pairs]))
    
    neg_pairs = []
    node_ids = list(G.nodes())
    attempts = 0
    while len(neg_pairs) < len(pos_pairs) and attempts < len(pos_pairs) * 5:
        attempts += 1
        u = random.choice(node_ids)
        v = random.choice(node_ids)
        if u == v:
            continue
        u_sorted, v_sorted = sorted([u, v])
        if not G.has_edge(u_sorted, v_sorted) and (u_sorted, v_sorted) not in neg_pairs:
            neg_pairs.append((u_sorted, v_sorted))
            
    print(f"Formed dataset: {len(pos_pairs)} positive edges, {len(neg_pairs)} negative edges")
    
    dataset = []
    for u, v in pos_pairs:
        feats = compute_node_pair_features(G, u, v, node_features_dict)
        feats['label'] = 1
        dataset.append(feats)
        
    for u, v in neg_pairs:
        feats = compute_node_pair_features(G, u, v, node_features_dict)
        feats['label'] = 0
        dataset.append(feats)
        
    df_link = pd.DataFrame(dataset)
    
    X_df = df_link.drop(columns=['label'])
    numeric_cols = X_df.select_dtypes(include=[np.number]).columns.tolist()
    
    X = X_df[numeric_cols].astype(float).values.tolist()
    y = df_link['label'].astype(int).tolist()
    
    X_train, X_test, y_train, y_test = pure_train_test_split(X, y, test_size=0.2, random_state=42)
    
    # Train Pure Python Decision Tree
    tree_link = PureDecisionTree(max_depth=5)
    tree_link.fit(X_train, y_train)
    
    # Evaluate
    y_prob = [tree_link.predict_proba(row) for row in X_test]
    y_pred = [1 if prob >= 0.5 else 0 for prob in y_prob]
    
    auc = pure_auc_roc(y_test, y_prob)
    precision, recall, f1 = pure_precision_recall_f1(y_test, y_pred)
    
    print(f"Link Prediction Metrics on Held-out Set (Pure Python DT):")
    print(f"  AUC-ROC:   {auc:.4f}")
    print(f"  Precision: {precision:.4f}")
    print(f"  Recall:    {recall:.4f}")
    print(f"  F1 Score:  {f1:.4f}")
    
    # Save artifacts
    model_path = os.path.join(output_dir, 'link_model.joblib')
    joblib.dump({
        'model': tree_link,
        'feature_cols': numeric_cols
    }, model_path)
    print(f"Saved link prediction model to {model_path}")
    
    return tree_link, numeric_cols

def train_anomaly_detection(edges_df, output_dir):
    print("\n--- Training Transaction/Communication Anomaly Detection ---")
    
    records = []
    for _, row in edges_df.iterrows():
        freq = float(row.get('frequency', 1.0))
        dur = float(row.get('duration_avg', 0.0))
        amt = float(row.get('amount', 0.0))
        
        is_trans = 1.0 if row['type'] == 'TRANSACTION' else 0.0
        is_call = 1.0 if row['type'] == 'CALL' else 0.0
        is_coaccused = 1.0 if row['type'] == 'CO_ACCUSED' else 0.0
        
        records.append({
            "frequency": freq,
            "duration": dur,
            "amount": amt,
            "is_transaction": is_trans,
            "is_call": is_call,
            "is_coaccused": is_coaccused
        })
        
    df_anomaly = pd.DataFrame(records)
    feature_cols = [c for c in df_anomaly.columns]
    
    X = df_anomaly[feature_cols].astype(float).values.tolist()
    
    # Train Pure Python Anomaly Detector
    anomaly_detector = PureAnomalyDetector(contamination=0.03)
    anomaly_detector.fit(X)
    
    preds = [anomaly_detector.predict(row) for row in X]
    
    num_anomalies = sum(1 for p in preds if p == -1)
    print(f"Pure Python Anomaly Detector flagged {num_anomalies} anomalies out of {len(X)} edges.")
    
    # Save model artifact
    model_path = os.path.join(output_dir, 'anomaly_model.joblib')
    joblib.dump({
        'model': anomaly_detector,
        'feature_cols': feature_cols
    }, model_path)
    print(f"Saved anomaly detection model to {model_path}")

def evaluate_communities(G, gt_df):
    print("\n--- Running and Evaluating Community Detection ---")
    
    # Run Louvain
    communities = nx.community.louvain_communities(G, weight='weight', seed=42)
    
    detected_partition = {}
    for comm_idx, node_set in enumerate(communities):
        for node in node_set:
            detected_partition[node] = comm_idx
            
    modularity = nx.community.modularity(G, communities, weight='weight')
    print(f"Louvain Community Detection Modularity: {modularity:.4f}")
    
    gt_filtered = gt_df[gt_df['node_id'].isin(G.nodes())].copy()
    
    gt_labels = []
    pred_labels = []
    
    counter = 100
    for _, row in gt_filtered.iterrows():
        node_id = row['node_id']
        cell_id = row['cell_id']
        
        if pd.isna(cell_id):
            gt_labels.append(counter)
            counter += 1
        else:
            gt_labels.append(int(cell_id))
            
        pred_labels.append(detected_partition.get(node_id, -1))
        
    ari = pure_adjusted_rand_index(gt_labels, pred_labels)
    print(f"Adjusted Rand Index (ARI) compared to Ground Truth cells: {ari:.4f}")

if __name__ == "__main__":
    output_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
    os.makedirs(output_dir, exist_ok=True)
    
    random.seed(42)
    np.random.seed(42)
    
    nodes_df, edges_df, gt_df = load_data()
    G = build_networkx_graph(nodes_df, edges_df)
    
    struct_features_df = compute_structural_features(G)
    train_risk_scoring_model(nodes_df, gt_df, struct_features_df, output_dir)
    train_link_prediction_model(G, nodes_df, edges_df, gt_df, struct_features_df, output_dir)
    train_anomaly_detection(edges_df, output_dir)
    evaluate_communities(G, gt_df)
    
    print("\nModel training pipeline finished successfully!")
