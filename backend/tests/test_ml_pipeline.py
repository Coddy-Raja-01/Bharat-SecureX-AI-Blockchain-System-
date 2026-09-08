import os
import sys
import joblib
import pandas as pd
import numpy as np
import networkx as nx

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal
from ml.train import load_data, build_networkx_graph, compute_structural_features

def test_ml_feature_computation():
    nodes_df, edges_df, gt_df = load_data()
    assert not nodes_df.empty, "Nodes dataframe should not be empty"
    assert not edges_df.empty, "Edges dataframe should not be empty"
    
    G = build_networkx_graph(nodes_df, edges_df)
    assert G.number_of_nodes() > 0, "NetworkX graph should have nodes"
    
    struct_features_df = compute_structural_features(G)
    assert 'degree_centrality' in struct_features_df.columns
    assert 'pagerank' in struct_features_df.columns
    assert len(struct_features_df) == len(nodes_df), "Features must be computed for all nodes"

def test_saved_model_artifacts():
    models_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'models')
    
    risk_model_path = os.path.join(models_dir, 'risk_model.joblib')
    link_model_path = os.path.join(models_dir, 'link_model.joblib')
    anomaly_model_path = os.path.join(models_dir, 'anomaly_model.joblib')
    
    assert os.path.exists(risk_model_path), "Risk model artifact must exist"
    assert os.path.exists(link_model_path), "Link model artifact must exist"
    assert os.path.exists(anomaly_model_path), "Anomaly model artifact must exist"
    
    # Load and check
    risk_data = joblib.load(risk_model_path)
    assert 'model' in risk_data
    assert 'feature_cols' in risk_data
    assert 'explainer' in risk_data
    
    link_data = joblib.load(link_model_path)
    assert 'model' in link_data
    assert 'feature_cols' in link_data
    
    anomaly_data = joblib.load(anomaly_model_path)
    assert 'model' in anomaly_data
