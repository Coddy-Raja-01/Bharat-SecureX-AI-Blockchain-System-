import os
import sys
import random
from datetime import datetime, timedelta
from faker import Faker

# Add parent directory to path so we can import app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.database import engine, SessionLocal, init_db, Node, Edge, GroundTruth, Base

fake = Faker('en_IN')  # Use Indian locale for realistic names and data

def clear_database(db):
    print("Clearing database...")
    db.query(GroundTruth).delete()
    db.query(Edge).delete()
    db.query(Node).delete()
    db.commit()

def generate_synthetic_data(db):
    print("Generating synthetic criminal network data...")
    
    # 1. Configuration parameters
    NUM_NORMAL_PEOPLE = 800
    NUM_CELLS = 3
    CELL_SIZES = [12, 10, 8]  # Sizes of criminal cells
    
    # Trackers
    all_nodes = []
    all_edges = []
    ground_truth_records = []
    
    # Helper to track node categories
    normal_people_ids = []
    criminal_people_ids = []
    
    # Pre-generate address clusters
    address_clusters = [f"Cluster_{i}" for i in range(10)]
    occupations = ["Engineer", "Teacher", "Doctor", "Business Owner", "Laborer", "Clerk", "Student", "Unemployed", "Driver", "Contractor"]
    age_bands = ["18-25", "26-35", "36-50", "50+"]
    
    # Keep track of phone/account maps for edge creation
    person_phones = {}
    person_accounts = {}
    person_attributes = {}
    
    # -------------------------------------------------------------
    # 2. Generate Legitimate (Normal) Network
    # -------------------------------------------------------------
    print(f"Generating {NUM_NORMAL_PEOPLE} legitimate entities...")
    for i in range(NUM_NORMAL_PEOPLE):
        p_id = f"person_normal_{i}"
        normal_people_ids.append(p_id)
        
        # Profile attributes
        occupation = random.choice(occupations) if random.random() > 0.1 else "Unknown"
        age_band = random.choices(age_bands, weights=[0.25, 0.4, 0.25, 0.1])[0]
        prior_cases = random.choices([0, 1, 2], weights=[0.96, 0.03, 0.01])[0]
        address_cluster = random.choice(address_clusters)
        
        # Person Node
        p_node = Node(
            id=p_id,
            type="Person",
            label=fake.name(),
            attributes={
                "occupation": occupation,
                "age_band": age_band,
                "prior_cases": prior_cases,
                "address_cluster": address_cluster
            }
        )
        all_nodes.append(p_node)
        person_attributes[p_id] = p_node.attributes
        
        # Ground Truth (Normal)
        gt = GroundTruth(
            node_id=p_id,
            is_criminal=False,
            role="normal",
            cell_id=None
        )
        ground_truth_records.append(gt)
        
        # Phone Nodes (1 or 2 per person)
        phones = []
        for ph_idx in range(random.choices([1, 2], weights=[0.85, 0.15])[0]):
            ph_id = f"phone_normal_{i}_{ph_idx}"
            ph_node = Node(
                id=ph_id,
                type="Phone",
                label=fake.phone_number().replace(" ", "").replace("-", "")[:10],
                attributes={"status": "active"}
            )
            all_nodes.append(ph_node)
            phones.append(ph_id)
            # Edge linking person to phone
            all_edges.append(Edge(
                source=p_id,
                target=ph_id,
                type="OWNED_PHONE",
                attributes={"primary": ph_idx == 0}
            ))
            
            # Ground truth for phone
            ground_truth_records.append(GroundTruth(
                node_id=ph_id,
                is_criminal=False,
                role="normal",
                cell_id=None
            ))
        person_phones[p_id] = phones
        
        # BankAccount Nodes (1 per person)
        acc_id = f"account_normal_{i}"
        acc_node = Node(
            id=acc_id,
            type="BankAccount",
            label=fake.iban()[:12],
            attributes={"bank_name": random.choice(["SBI", "HDFC", "ICICI", "PNB", "Axis"])}
        )
        all_nodes.append(acc_node)
        person_accounts[p_id] = acc_id
        # Edge linking person to account
        all_edges.append(Edge(
            source=p_id,
            target=acc_id,
            type="OWNED_ACCOUNT",
            attributes={}
        ))
        
        # Ground truth for account
        ground_truth_records.append(GroundTruth(
            node_id=acc_id,
            is_criminal=False,
            role="normal",
            cell_id=None
        ))
        
        # Address Node
        addr_id = f"address_normal_{i}"
        addr_node = Node(
            id=addr_id,
            type="Address",
            label=fake.address().replace("\n", ", "),
            attributes={"cluster": address_cluster}
        )
        all_nodes.append(addr_node)
        all_edges.append(Edge(
            source=p_id,
            target=addr_id,
            type="SHARED_ADDRESS",
            attributes={}
        ))
        ground_truth_records.append(GroundTruth(
            node_id=addr_id,
            is_criminal=False,
            role="normal",
            cell_id=None
        ))
        
        # Vehicle Node (50% chance)
        if random.random() > 0.5:
            veh_id = f"vehicle_normal_{i}"
            veh_node = Node(
                id=veh_id,
                type="Vehicle",
                label=f"DL {random.randint(1, 9)}C {chr(random.randint(65, 90))}{chr(random.randint(65, 90))} {random.randint(1000, 9999)}",
                attributes={"model": random.choice(["Maruti Swift", "Hyundai i20", "Honda City", "Royal Enfield", "Hero Splendor"])}
            )
            all_nodes.append(veh_node)
            all_edges.append(Edge(
                source=p_id,
                target=veh_id,
                type="SHARED_VEHICLE",
                attributes={}
            ))
            ground_truth_records.append(GroundTruth(
                node_id=veh_id,
                is_criminal=False,
                role="normal",
                cell_id=None
            ))

    # -------------------------------------------------------------
    # 3. Generate Embedded Criminal Network Cells
    # -------------------------------------------------------------
    print(f"Generating {NUM_CELLS} structured criminal cells...")
    for cell_idx, cell_size in enumerate(CELL_SIZES):
        print(f"  Building Cell {cell_idx} with {cell_size} members...")
        cell_members = []
        
        # We designate:
        # - Member 0: Kingpin
        # - Member 1-2: Lieutenants/Financiers
        # - Rest: Associates/Mules
        for j in range(cell_size):
            p_id = f"person_criminal_c{cell_idx}_{j}"
            cell_members.append(p_id)
            criminal_people_ids.append(p_id)
            
            # Assign roles
            if j == 0:
                role = "kingpin"
                prior_cases = random.randint(2, 6)
                occupation = "Business Owner"  # front business
                age_band = random.choice(["36-50", "50+"])
            elif j in [1, 2] and cell_size > 2:
                role = "financier"
                prior_cases = random.randint(1, 3)
                occupation = random.choice(["Clerk", "Broker", "Unemployed"])
                age_band = random.choice(["26-35", "36-50"])
            else:
                role = "associate"
                prior_cases = random.choices([0, 1, 2], weights=[0.6, 0.3, 0.1])[0]
                occupation = random.choice(["Driver", "Laborer", "Unemployed", "Unknown"])
                age_band = random.choice(["18-25", "26-35"])
            
            # Person Node
            p_node = Node(
                id=p_id,
                type="Person",
                label=fake.name(),
                attributes={
                    "occupation": occupation,
                    "age_band": age_band,
                    "prior_cases": prior_cases,
                    "address_cluster": f"Cluster_Crim_{cell_idx}"
                }
            )
            all_nodes.append(p_node)
            person_attributes[p_id] = p_node.attributes
            
            # Ground Truth (Criminal)
            gt = GroundTruth(
                node_id=p_id,
                is_criminal=True,
                role=role,
                cell_id=cell_idx
            )
            ground_truth_records.append(gt)
            
            # Phones (Criminals often use burner phones, we give them 1-3)
            phones = []
            for ph_idx in range(random.randint(1, 3)):
                ph_id = f"phone_criminal_c{cell_idx}_{j}_{ph_idx}"
                ph_node = Node(
                    id=ph_id,
                    type="Phone",
                    label=fake.phone_number().replace(" ", "").replace("-", "")[:10],
                    attributes={"status": "prepaid", "is_burner": True}
                )
                all_nodes.append(ph_node)
                phones.append(ph_id)
                all_edges.append(Edge(
                    source=p_id,
                    target=ph_id,
                    type="OWNED_PHONE",
                    attributes={"burner": True}
                ))
                
                # Ground truth for phone (marked as criminal because owned by criminal cell)
                ground_truth_records.append(GroundTruth(
                    node_id=ph_id,
                    is_criminal=True,
                    role=role,
                    cell_id=cell_idx
                ))
            person_phones[p_id] = phones
            
            # Bank accounts (Multiple for kingpins/financiers, 1 for mules)
            acc_id = f"account_criminal_c{cell_idx}_{j}"
            acc_node = Node(
                id=acc_id,
                type="BankAccount",
                label=fake.iban()[:12],
                attributes={"bank_name": random.choice(["SBI", "HDFC", "ICICI"])}
            )
            all_nodes.append(acc_node)
            person_accounts[p_id] = acc_id
            all_edges.append(Edge(
                source=p_id,
                target=acc_id,
                type="OWNED_ACCOUNT",
                attributes={}
            ))
            ground_truth_records.append(GroundTruth(
                node_id=acc_id,
                is_criminal=True,
                role=role,
                cell_id=cell_idx
            ))
            
            # Shared addresses & vehicles (creates internal cell correlation)
            addr_id = f"address_criminal_c{cell_idx}_{j}"
            addr_node = Node(
                id=addr_id,
                type="Address",
                label=fake.address().replace("\n", ", "),
                attributes={"cluster": f"Cluster_Crim_{cell_idx}"}
            )
            all_nodes.append(addr_node)
            all_edges.append(Edge(
                source=p_id,
                target=addr_id,
                type="SHARED_ADDRESS",
                attributes={}
            ))
            ground_truth_records.append(GroundTruth(
                node_id=addr_id,
                is_criminal=True,
                role=role,
                cell_id=cell_idx
            ))
            
            if random.random() > 0.4:
                veh_id = f"vehicle_criminal_c{cell_idx}_{j}"
                veh_node = Node(
                    id=veh_id,
                    type="Vehicle",
                    label=f"DL {random.randint(1, 9)}C {chr(random.randint(65, 90))}{chr(random.randint(65, 90))} {random.randint(1000, 9999)}",
                    attributes={"model": random.choice(["Mahindra Scorpio", "Toyota Fortuner", "Maruti Swift"])}
                )
                all_nodes.append(veh_node)
                all_edges.append(Edge(
                    source=p_id,
                    target=veh_id,
                    type="SHARED_VEHICLE",
                    attributes={}
                ))
                ground_truth_records.append(GroundTruth(
                    node_id=veh_id,
                    is_criminal=True,
                    role=role,
                    cell_id=cell_idx
                ))
                
        # Connect the Cell internally:
        # A. FIR Co-Accused Links
        # Link Kingpin + Lieutenant + some Mules in common FIRs
        fir_case_ids = [f"FIR/2026/{cell_idx*10 + k}" for k in range(3)]
        for case_id in fir_case_ids:
            # Pick a subset of 3-5 members of this cell to be co-accused
            num_co_accused = min(random.randint(3, 5), cell_size)
            co_accused = random.sample(cell_members, num_co_accused)
            # Make sure Kingpin or Lieutenant is always involved
            if cell_members[0] not in co_accused and random.random() > 0.3:
                co_accused[0] = cell_members[0]
            
            # Create co-accused links pairwise
            for m_a in co_accused:
                for m_b in co_accused:
                    if m_a < m_b:  # Avoid self-loops and duplicate edges
                        all_edges.append(Edge(
                            source=m_a,
                            target=m_b,
                            type="CO_ACCUSED",
                            attributes={"case_id": case_id},
                            timestamp=datetime.utcnow() - timedelta(days=random.randint(30, 365))
                        ))
        
        # B. Internal Calls (Frequent & recent between phones)
        # Kingpin calls Lieutenants, Lieutenants call Mules
        kingpin = cell_members[0]
        lieutenants = cell_members[1:3] if cell_size > 2 else [cell_members[1]]
        mules = cell_members[3:] if cell_size > 3 else []
        
        # Calls: Kingpin <-> Lieutenants
        for lt in lieutenants:
            kp_phone = random.choice(person_phones[kingpin])
            lt_phone = random.choice(person_phones[lt])
            all_edges.append(Edge(
                source=kp_phone,
                target=lt_phone,
                type="CALL",
                attributes={"frequency": random.randint(30, 100), "duration_avg": random.randint(120, 400), "recency_days": random.randint(0, 3)},
                timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 48))
            ))
            
        # Calls: Lieutenants <-> Mules
        for m in mules:
            lt = random.choice(lieutenants)
            lt_phone = random.choice(person_phones[lt])
            m_phone = random.choice(person_phones[m])
            all_edges.append(Edge(
                source=lt_phone,
                target=m_phone,
                type="CALL",
                attributes={"frequency": random.randint(20, 60), "duration_avg": random.randint(60, 200), "recency_days": random.randint(0, 5)},
                timestamp=datetime.utcnow() - timedelta(hours=random.randint(1, 96))
            ))
            
        # C. Internal Transactions (High-Value flow)
        # Kingpin -> Financier -> Mules (Money laundering flow)
        kp_acc = person_accounts[kingpin]
        for lt in lieutenants:
            lt_acc = person_accounts[lt]
            # Multiple high value transactions
            for _ in range(random.randint(2, 5)):
                all_edges.append(Edge(
                    source=kp_acc,
                    target=lt_acc,
                    type="TRANSACTION",
                    attributes={"amount": float(random.randint(100000, 500000)), "purpose": "commercial"},
                    timestamp=datetime.utcnow() - timedelta(days=random.randint(1, 15))
                ))
                
        for m in mules:
            lt = random.choice(lieutenants)
            lt_acc = person_accounts[lt]
            m_acc = person_accounts[m]
            # Transaction Lieutenant -> Mule
            for _ in range(random.randint(1, 3)):
                all_edges.append(Edge(
                    source=lt_acc,
                    target=m_acc,
                    type="TRANSACTION",
                    attributes={"amount": float(random.randint(20000, 80000)), "purpose": "personal"},
                    timestamp=datetime.utcnow() - timedelta(days=random.randint(1, 10))
                ))
                
        # D. Shared Resources within the Cell
        # E.g., sharing a vehicle between 2-3 members
        if len(mules) >= 2:
            shared_veh = f"vehicle_shared_c{cell_idx}"
            veh_node = Node(
                id=shared_veh,
                type="Vehicle",
                label=f"DL {random.randint(1, 9)}C {chr(random.randint(65, 90))}{chr(random.randint(65, 90))} {random.randint(1000, 9999)}",
                attributes={"model": "Mahindra Scorpio", "color": "Black"}
            )
            all_nodes.append(veh_node)
            ground_truth_records.append(GroundTruth(
                node_id=shared_veh,
                is_criminal=True,
                role="associate",
                cell_id=cell_idx
            ))
            # Link to multiple people in the cell
            for p in random.sample(cell_members, 3):
                all_edges.append(Edge(
                    source=p,
                    target=shared_veh,
                    type="SHARED_VEHICLE",
                    attributes={"shared": True}
                ))

    # -------------------------------------------------------------
    # 4. Generate Interaction Edges (Calls, Transactions) in Background Legitimate Graph
    # -------------------------------------------------------------
    print("Generating background interactions (Calls & Transactions) for normal nodes...")
    
    # Legit Calls
    for _ in range(3500):
        # Pick two random normal people
        p1 = random.choice(normal_people_ids)
        p2 = random.choice(normal_people_ids)
        if p1 == p2:
            continue
        
        # Higher chance to call if they share address cluster
        cluster1 = person_attributes[p1]["address_cluster"]
        cluster2 = person_attributes[p2]["address_cluster"]
        if cluster1 != cluster2 and random.random() > 0.15:
            continue  # Prefer intra-cluster calls
            
        ph1 = random.choice(person_phones[p1])
        ph2 = random.choice(person_phones[p2])
        
        # Standard call frequency (1 to 10) and duration
        all_edges.append(Edge(
            source=ph1,
            target=ph2,
            type="CALL",
            attributes={"frequency": random.randint(1, 8), "duration_avg": random.randint(30, 180), "recency_days": random.randint(5, 50)},
            timestamp=datetime.utcnow() - timedelta(days=random.randint(2, 50))
        ))

    # Legit Transactions
    for _ in range(2000):
        p1 = random.choice(normal_people_ids)
        p2 = random.choice(normal_people_ids)
        if p1 == p2:
            continue
        
        acc1 = person_accounts[p1]
        acc2 = person_accounts[p2]
        
        # Standard normal transfers: smaller amounts (100 to 5000)
        all_edges.append(Edge(
            source=acc1,
            target=acc2,
            type="TRANSACTION",
            attributes={"amount": float(random.randint(200, 6000))},
            timestamp=datetime.utcnow() - timedelta(days=random.randint(1, 30))
        ))
        
    # Associate / Family links (legitimate)
    for _ in range(400):
        p1 = random.choice(normal_people_ids)
        p2 = random.choice(normal_people_ids)
        if p1 != p2:
            all_edges.append(Edge(
                source=p1,
                target=p2,
                type="ASSOCIATE",
                attributes={"relationship": random.choice(["family", "relative", "colleague"])}
            ))

    # -------------------------------------------------------------
    # 5. Sparse Links: Connect Criminal Cells slightly to Background (Noise)
    # -------------------------------------------------------------
    print("Connecting criminal cells sparsely to the background network (noise)...")
    for cell_idx, cell_size in enumerate(CELL_SIZES):
        cell_members = [p_id for p_id in criminal_people_ids if f"c{cell_idx}_" in p_id]
        
        # Make a few cell associates call or transact with normal people
        for _ in range(3):
            crim_person = random.choice(cell_members)
            norm_person = random.choice(normal_people_ids)
            
            crim_phone = random.choice(person_phones[crim_person])
            norm_phone = random.choice(person_phones[norm_person])
            
            all_edges.append(Edge(
                source=crim_phone,
                target=norm_phone,
                type="CALL",
                attributes={"frequency": random.randint(1, 3), "duration_avg": random.randint(20, 100), "recency_days": random.randint(10, 40)},
                timestamp=datetime.utcnow() - timedelta(days=random.randint(10, 40))
            ))
            
        for _ in range(2):
            crim_person = random.choice(cell_members)
            norm_person = random.choice(normal_people_ids)
            
            crim_acc = person_accounts[crim_person]
            norm_acc = person_accounts[norm_person]
            
            all_edges.append(Edge(
                source=crim_acc,
                target=norm_acc,
                type="TRANSACTION",
                attributes={"amount": float(random.randint(500, 4000))},
                timestamp=datetime.utcnow() - timedelta(days=random.randint(5, 25))
            ))

    # Write everything to DB
    print(f"Seeding DB: {len(all_nodes)} nodes, {len(all_edges)} edges, {len(ground_truth_records)} ground truth records...")
    
    # Bulk save to speed up execution
    db.add_all(all_nodes)
    db.commit()
    
    db.add_all(all_edges)
    db.commit()
    
    db.add_all(ground_truth_records)
    db.commit()
    
    print("Database seeding completed successfully.")

if __name__ == "__main__":
    db = SessionLocal()
    try:
        init_db()
        clear_database(db)
        generate_synthetic_data(db)
    finally:
        db.close()
