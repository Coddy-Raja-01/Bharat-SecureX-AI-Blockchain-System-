import os
import sys
import pytest

sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import SessionLocal, Node, Edge, GroundTruth
from ml.generate_data import generate_synthetic_data, clear_database

def test_data_generation():
    db = SessionLocal()
    try:
        # Clear and generate
        clear_database(db)
        generate_synthetic_data(db)
        
        # Verify node counts
        num_nodes = db.query(Node).count()
        num_edges = db.query(Edge).count()
        num_gt = db.query(GroundTruth).count()
        
        print(f"Test generated: {num_nodes} nodes, {num_edges} edges")
        
        assert num_nodes > 500, "Should generate a baseline count of nodes"
        assert num_edges > 1000, "Should generate a baseline count of edges"
        assert num_gt == num_nodes, "Ground truth count must match node count"
        
        # Verify cell criminals exist
        criminals = db.query(GroundTruth).filter(GroundTruth.is_criminal == True).all()
        assert len(criminals) > 10, "Should have criminal cell members embedded"
        
        # Verify kingpin exists
        kingpins = db.query(GroundTruth).filter(GroundTruth.role == "kingpin").all()
        assert len(kingpins) > 0, "Should have at least one kingpin node"
        
    finally:
        db.close()
