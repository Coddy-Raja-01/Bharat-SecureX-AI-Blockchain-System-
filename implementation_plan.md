# Implementation Plan — AI-Powered Criminal Network Analysis System

This plan details the design and implementation of the **AI-Powered Criminal Network Analysis System (SIH26189)** prototype for the Smart India Hackathon 2026. The system consists of a FastAPI backend (with NetworkX for graph computation and scikit-learn/XGBoost for AI models) and a React + TypeScript + Tailwind CSS frontend for interactive visual analysis. All services are containerized using Docker Compose.

---

## Technical Stack & Architecture

### Backend Component
- **Language**: Python 3.11 (inside Docker to avoid compatibility issues with ML dependencies on host)
- **Framework**: FastAPI
- **Database**: PostgreSQL (persisting entities, relationships, cases, and ground truth)
- **Graph Processing**: NetworkX (in-memory representations synced with database)
- **Machine Learning**: 
  - `xgboost` / `scikit-learn` for Risk Scoring (Node Classification) and Link Prediction (Edge Classification)
  - `shap` for explainability on node risk scoring
  - `IsolationForest` (scikit-learn) for transactional/interaction anomaly detection
  - Louvain Community Detection (NetworkX) for clustering nodes into criminal cells
- **Serialization**: `joblib` for persisting trained models

### Frontend Component
- **Language/Framework**: React (TypeScript) + Vite
- **Styling**: Tailwind CSS (supporting Dark Mode by default)
- **Icons**: `lucide-react`
- **Visualization**: `react-force-graph-2d` (HTML5 Canvas-based graph rendering for high performance, smooth zoom/pan, node dragging, and custom styling)
- **State Management & Layout**: Flex layout with transition shifts from single data view to split-panel inspection.

---

## User Review Required

> [!IMPORTANT]
> - **Synthetic Data**: The backend contains a custom Faker generator (`generate_data.py`) to create a realistic mock criminal network (dense subgraphs for criminal cells, sparse background relationships). In production, this would be connected to actual restricted databases (CCTNS, CDR logs, bank APIs).
> - **GNN vs XGBoost**: XGBoost on graph structural features (centralities) + entity features is chosen as the primary backend for its explainability (via SHAP) and fast training. GNN (GraphSAGE) is documented in the README as a production scalability path.
> - **Graph Engine**: NetworkX is used for in-memory graph processing for this prototype scale (thousands of nodes). The README describes transitioning to Neo4j for scale.

---

## Open Questions

- **Gemini Chat Integration**: Would you like to include a Gemini-powered chat interface to enable natural language queries against your network data (e.g., "Find the main facilitator connecting Cell A and Cell B")? If yes, we can add a chat panel to the frontend and expose a query endpoint in FastAPI. Let us know and we will update the plan.

---

## Proposed Changes

We will create a structured project inside the workspace `d:\Development (Projects)\SIH Project 1`.

### Backend Implementation

#### [NEW] [generate_data.py](file:///d:/Development%20(Projects)/SIH%20Project%201/backend/ml/generate_data.py)
A script to generate synthetic data with embedded criminal cells:
- **Entities**:
  - `Person`: ID, Name, Age Band, Address Cluster, Occupation, Prior Cases.
  - `Phone`: ID, Phone Number.
  - `BankAccount`: ID, Account Number, Bank Name.
  - `Vehicle`: ID, License Plate.
  - `Address`: ID, Location Name.
- **Relationships (Edges)**:
  - `CALL`: Phone $\leftrightarrow$ Phone (frequency, duration, recency).
  - `TRANSACTION`: BankAccount $\rightarrow$ BankAccount (amount, timestamp).
  - `CO_ACCUSED`: Person $\leftrightarrow$ Person (FIR case ID, timestamp).
  - `ASSOCIATE`: Person $\leftrightarrow$ Person (type, recency).
  - `SHARED_ADDRESS`: Person $\leftrightarrow$ Address.
  - `SHARED_VEHICLE`: Person $\leftrightarrow$ Vehicle.
- **Embedded Ground Truth**:
  - Deliberately inject 3 distinct criminal cells.
  - Cell structure: 1 Kingpin (high centrality, financier), 2 Lieutenants (organizers), 5-8 Mules (low centrality but high transaction/call frequencies).
  - Dense relationships inside cells; sparse background relationships to normal nodes.
  - Write these entities, edges, and ground-truth labels directly to the PostgreSQL database.

#### [NEW] [train.py](file:///d:/Development%20(Projects)/SIH%20Project%201/backend/ml/train.py)
A pipeline script to load data, compute features, train models, evaluate, and save artifacts:
1. **Feature Engineering**:
   - Construct a NetworkX graph from database edges.
   - Node-level structural features: degree, betweenness centrality, closeness centrality, PageRank, eigenvector centrality, clustering coefficient, k-core number.
   - Entity features: age band (one-hot), occupation (one-hot), prior cases.
   - Edge-level features: interaction frequency, recency, transaction amount, relation type.
2. **Risk-Scoring Model (Node Classification)**:
   - Target: `is_criminal` (from ground-truth table).
   - Algorithm: Random Forest or XGBoost Classifier.
   - Split: Train/Val/Test (stratified).
   - Evaluation: AUC-ROC, Precision, Recall, F1. Log values to console.
   - Save `risk_model.joblib` and train SHAP explainer for node analysis.
3. **Link Prediction Model (Edge Classification)**:
   - Formulate as predicting missing edges.
   - Positive samples: actual criminal/associate relationships.
   - Negative samples: random node pairs not connected.
   - Features: common neighbors, Adamic-Adar index, preferential attachment, Jaccard coefficient, source/target risk scores, source/target centralities.
   - Algorithm: XGBoost Classifier.
   - Evaluation: AUC-ROC, Average Precision.
   - Save `link_model.joblib`.
4. **Community Detection**:
   - Algorithm: Louvain Community Detection.
   - Evaluation: Modularity score, and Adjusted Rand Index (ARI) compared to ground-truth cells.
5. **Anomaly Detection**:
   - Algorithm: Isolation Forest trained on transaction/call feature vectors.
   - Flag top 2% of anomalous interactions.
   - Save model artifact `anomaly_model.joblib`.

#### [NEW] [database.py](file:///d:/Development%20(Projects)/SIH%20Project%201/backend/app/database.py)
SQLAlchemy configuration, database connection, and schema definitions for tables:
- `nodes` (id, label, type, attributes)
- `edges` (id, source, target, type, attributes, timestamp)
- `ground_truth` (node_id, is_criminal, role, cell_id)
- `cases` (case_id, description, date_created)

#### [NEW] [graph.py](file:///d:/Development%20(Projects)/SIH%20Project%201/backend/app/graph.py)
A state manager for NetworkX inside FastAPI:
- Loads the database nodes and edges into memory at startup.
- Keeps an in-memory NetworkX MultiDiGraph representation.
- Provides functions to compute features dynamically for the whole graph or for updated sections.
- Houses the prediction functions which load the `.joblib` models and evaluate active nodes/edges.
- Evaluates updated nodes/edges in real-time when new cases are submitted (using the loaded model objects).

#### [NEW] [main.py](file:///d:/Development%20(Projects)/SIH%20Project%201/backend/app/main.py)
FastAPI routes and server setup:
- `GET /network` — Returns node list (with risk scores, communities, and types) and edge list for rendering.
- `GET /entity/{id}` — Returns profile details, risk score, connected relationships, and SHAP explainability values (feature importances/contributions).
- `GET /communities` — Returns Louvain community structures, member profiles, and modularity stats.
- `GET /predicted-links` — Returns top $N$ predicted hidden links with their confidence scores.
- `GET /anomalies` — Returns interactions flagged as anomalous by the Isolation Forest.
- `POST /case` — Ingests a batch of new nodes and edges, persists them to Postgres, dynamically inserts them into the in-memory NetworkX graph, computes features, evaluates their risk scores/link probabilities using the trained models, and returns the live updated values.

#### [NEW] [requirements.txt](file:///d:/Development%20(Projects)/SIH%20Project%201/backend/requirements.txt)
Python package specifications including `fastapi`, `uvicorn`, `sqlalchemy`, `psycopg2-binary`, `networkx`, `xgboost`, `shap`, `scikit-learn`, `pandas`, `numpy`, `faker`, `joblib`, `pytest`.

#### [NEW] [Dockerfile](file:///d:/Development%20(Projects)/SIH%20Project%201/backend/Dockerfile)
Multi-stage build using a standard `python:3.11-slim` base image to compile and serve the FastAPI application.

---

### Frontend Implementation

#### [NEW] [package.json](file:///d:/Development%20(Projects)/SIH%20Project%201/frontend/package.json)
Vite, React, TypeScript, Tailwind CSS, `lucide-react`, `axios`, and `react-force-graph-2d` dependencies.

#### [NEW] [vite.config.ts](file:///d:/Development%20(Projects)/SIH%20Project%201/frontend/vite.config.ts)
Vite setup with proxying configured for backend API calls (`/api/` routing).

#### [NEW] [tailwind.config.js](file:///d:/Development%20(Projects)/SIH%20Project%201/frontend/tailwind.config.js)
Tailwind configuration setting up the default dark theme (`class: 'dark'`) and customization for the zinc-styled layout.

#### [NEW] [index.css](file:///d:/Development%20(Projects)/SIH%20Project%201/frontend/src/index.css)
Tailwind imports and custom utility styles for glassmorphism, scrollbars, and graph containers.

#### [NEW] [App.tsx](file:///d:/Development%20(Projects)/SIH%20Project%201/frontend/src/App.tsx)
The main layout of the criminal analysis platform. Contains:
1. **Header Row**: Left-aligned Title (SIH26189 - AI Criminal Network Analyser), Status indicator (Connected to live backend), and Dark/Light Mode switch.
2. **KPI Cards Row**: High-level network metrics: Total Inspected Entities, Identified High-Risk Hubs, Modularity Score, Flagged Anomalies.
3. **Split layout**:
   - **Left Panel (Graph & Visualizer)**: Integrates `react-force-graph-2d`. Nodes colored by risk score (Red=High, Orange=Medium, Green/Blue=Low) and sized by PageRank/degree centrality. Hovering displays simple profile. Clicking selects the node and slides open the right inspection panel.
   - **Right Panel (Details & Intelligence Panel)**: Responsive panel that slides in/out. Displays:
     - Entity profile & active metrics.
     - SHAP Explanation: A horizontal bar chart showing the structural and demographic factors driving their risk rating (e.g. "Degree centrality (+15%)", "Co-accused associations (+25%)").
     - Timeline of relations/edges.
     - List of predicted hidden links specifically involving this node.
4. **Bottom Tabs Layout**: For accessing supplementary intelligence views:
   - *Detected Cells / Communities*: List of Louvain-partitioned cells, sorted by aggregate risk, showing member rosters.
   - *Link Predictor*: Global list of top predicted hidden links with explanation labels.
   - *Anomaly Radar*: List of isolation forest flagged transaction/communication events.
   - *Add Case Data*: Live form inputting custom JSON case details (entities and relationships), calling the live re-scoring engine, and instantly updating the network visuals.

#### [NEW] [Dockerfile](file:///d:/Development%20(Projects)/SIH%20Project%201/frontend/Dockerfile)
Vite build and static server configurations using Nginx.

---

### Orchestration & Seed Script

#### [NEW] [docker-compose.yml](file:///d:/Development%20(Projects)/SIH%20Project%201/docker-compose.yml)
Coordinates three services:
1. `db`: PostgreSQL database.
2. `backend`: FastAPI server. Depends on `db`.
3. `frontend`: Nginx serving the static React app. Connects to `backend`.

#### [NEW] [setup.sh](file:///d:/Development%20(Projects)/SIH%20Project%201/setup.sh)
A setup script that:
1. Runs `docker compose down -v` to clear existing states.
2. Builds the containers.
3. Starts the database.
4. Runs the database migration, generates synthetic data, seeds PostgreSQL, runs `train.py` to compile and store joblib models, and starts the FastAPI/Vite servers.

---

## Verification Plan

### Automated Tests
We will add basic unit tests inside a `backend/tests` folder to assert model functionality:
- `test_data_generator.py`: Verify generated entity structures and ground truth count.
- `test_models.py`: Verify that training outputs `risk_model.joblib` and `link_model.joblib`, models have non-zero feature importances, and evaluation metrics beat a random baseline.
- `test_api.py`: Verify that FastAPI endpoints return valid schemas and respond correctly to inputs.
- Execute via: `pytest` inside the backend container.

### Manual Verification
1. Run `./setup.sh` and inspect the terminal output to ensure data generator runs, PostgreSQL seeds, models train, evaluation metrics (AUC-ROC, Modularity, etc.) are computed and logged, and FastAPI launches successfully.
2. Launch the frontend in the browser.
3. Interact with the Force-Directed Graph: zoom, pan, click nodes. Confirm the side panel slides in and displays correct details, risk scores, and SHAP bar charts.
4. Select the "Add Case Data" form, input a new connection (e.g. a link between a normal node and a kingpin node), and submit. Confirm the graph live-reloads and the target node's risk score increases immediately.
5. Inspect the "Predicted Links" list and confirm the links look logical.
6. Verify the dark mode toggle successfully swaps the page theme and colors.
