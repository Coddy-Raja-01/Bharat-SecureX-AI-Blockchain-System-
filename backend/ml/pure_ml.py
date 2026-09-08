import random
import math

def pure_train_test_split(X, y, test_size=0.2, random_state=42):
    random.seed(random_state)
    indices = list(range(len(X)))
    random.shuffle(indices)
    split_idx = int(len(X) * (1 - test_size))
    
    train_indices = indices[:split_idx]
    test_indices = indices[split_idx:]
    
    X_train = [X[i] for i in train_indices]
    y_train = [y[i] for i in train_indices]
    X_test = [X[i] for i in test_indices]
    y_test = [y[i] for i in test_indices]
    
    return X_train, X_test, y_train, y_test

class PureDecisionTree:
    def __init__(self, max_depth=5, min_samples_split=2):
        self.max_depth = max_depth
        self.min_samples_split = min_samples_split
        self.root = None

    class Node:
        def __init__(self, feature=None, threshold=None, left=None, right=None, *, value=None):
            self.feature = feature       # Index of feature to split on
            self.threshold = threshold   # Threshold value for split
            self.left = left             # Left child node
            self.right = right           # Right child node
            self.value = value           # Expected value / probability of class 1 at this node

    def fit(self, X, y):
        # X: list of lists
        # y: list of binary targets
        self.root = self._build_tree(X, y, depth=0)

    def _gini(self, y):
        n = len(y)
        if n == 0:
            return 0.0
        p1 = sum(y) / n
        p0 = 1.0 - p1
        return 1.0 - (p0**2 + p1**2)

    def _split(self, X, y, feat_idx, threshold):
        left_idx = [i for i, row in enumerate(X) if row[feat_idx] <= threshold]
        right_idx = [i for i, row in enumerate(X) if row[feat_idx] > threshold]
        return left_idx, right_idx

    def _best_split(self, X, y):
        best_gini = 999.0
        best_feat = None
        best_thresh = None
        
        n_samples = len(X)
        if n_samples <= self.min_samples_split:
            return None, None
            
        n_features = len(X[0])
        
        for feat_idx in range(n_features):
            values = sorted(list(set(row[feat_idx] for row in X)))
            if len(values) <= 1:
                continue
                
            for i in range(len(values) - 1):
                thresh = (values[i] + values[i+1]) / 2.0
                left_idx, right_idx = self._split(X, y, feat_idx, thresh)
                
                if len(left_idx) == 0 or len(right_idx) == 0:
                    continue
                    
                gini_left = self._gini([y[idx] for idx in left_idx])
                gini_right = self._gini([y[idx] for idx in right_idx])
                
                weighted_gini = (len(left_idx) / n_samples) * gini_left + (len(right_idx) / n_samples) * gini_right
                
                if weighted_gini < best_gini:
                    best_gini = weighted_gini
                    best_feat = feat_idx
                    best_thresh = thresh
                    
        return best_feat, best_thresh

    def _build_tree(self, X, y, depth):
        n_samples = len(X)
        if n_samples == 0:
            return self.Node(value=0.0)
            
        p1 = sum(y) / n_samples
        
        if p1 == 0.0 or p1 == 1.0 or depth >= self.max_depth or n_samples < self.min_samples_split:
            return self.Node(value=p1)
            
        feat, thresh = self._best_split(X, y)
        if feat is None:
            return self.Node(value=p1)
            
        left_idx, right_idx = self._split(X, y, feat, thresh)
        
        left_node = self._build_tree([X[i] for i in left_idx], [y[i] for i in left_idx], depth + 1)
        right_node = self._build_tree([X[i] for i in right_idx], [y[i] for i in right_idx], depth + 1)
        
        return self.Node(feature=feat, threshold=thresh, left=left_node, right=right_node, value=p1)

    def predict_proba(self, X_sample):
        node = self.root
        while node.left is not None:
            if X_sample[node.feature] <= node.threshold:
                node = node.left
            else:
                node = node.right
        # Return probability of class 1
        return node.value

    def explain(self, X_sample, feature_names):
        # Calculate local TreeSHAP-like feature contributions
        explanation = {}
        node = self.root
        
        while node.left is not None:
            feat_idx = node.feature
            feat_name = feature_names[feat_idx]
            
            # Predict before split
            base_val = node.value
            
            # Traversal
            if X_sample[feat_idx] <= node.threshold:
                next_node = node.left
            else:
                next_node = node.right
                
            # Contribution of this node split
            diff = next_node.value - base_val
            
            # Aggregate contributions
            explanation[feat_name] = explanation.get(feat_name, 0.0) + diff
            node = next_node
            
        return [{"feature": k, "shap_value": v} for k, v in explanation.items() if abs(v) > 0.0001]

class PureAnomalyDetector:
    def __init__(self, contamination=0.03):
        self.contamination = contamination
        self.means = {}
        self.stds = {}
        self.threshold = 0.0

    def fit(self, X):
        # X: list of lists
        if not X:
            return
            
        n_samples = len(X)
        n_features = len(X[0])
        
        # Calculate mean & std for each feature
        for j in range(n_features):
            vals = [row[j] for row in X]
            mean = sum(vals) / n_samples
            self.means[j] = mean
            
            variance = sum((x - mean) ** 2 for x in vals) / (n_samples - 1 if n_samples > 1 else 1)
            self.stds[j] = variance ** 0.5 if variance > 0 else 1.0
            
        # Calculate anomaly scores for threshold boundary
        scores = []
        for row in X:
            scores.append(self.score(row))
            
        scores.sort(reverse=True)
        idx = int(n_samples * self.contamination)
        self.threshold = scores[idx] if idx < len(scores) else scores[-1]

    def score(self, row):
        # Sum of squared Z-scores (Mahalanobis distance proxy)
        score = 0.0
        for j, val in enumerate(row):
            if j in self.means:
                z = (val - self.means[j]) / self.stds[j]
                score += z ** 2
        return score

    def predict(self, row):
        val = self.score(row)
        # Returns -1 for anomaly, 1 for normal
        return -1 if val >= self.threshold else 1

def pure_auc_roc(y_true, y_prob):
    sorted_pairs = sorted(zip(y_prob, y_true), reverse=True)
    n_pos = sum(y_true)
    n_neg = len(y_true) - n_pos
    if n_pos == 0 or n_neg == 0:
        return 0.5
        
    tp = 0
    fp = 0
    auc = 0.0
    last_fp = 0
    
    for _, label in sorted_pairs:
        if label == 1:
            tp += 1
        else:
            fp += 1
            auc += tp * (fp - last_fp)
            last_fp = fp
            
    return auc / (n_pos * n_neg)

def pure_precision_recall_f1(y_true, y_pred):
    tp = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 1)
    fp = sum(1 for t, p in zip(y_true, y_pred) if t == 0 and p == 1)
    fn = sum(1 for t, p in zip(y_true, y_pred) if t == 1 and p == 0)
    
    prec = tp / (tp + fp) if (tp + fp) > 0 else 0.0
    rec = tp / (tp + fn) if (tp + fn) > 0 else 0.0
    f1 = 2.0 * prec * rec / (prec + rec) if (prec + rec) > 0 else 0.0
    
    return prec, rec, f1

def pure_adjusted_rand_index(labels_true, labels_pred):
    from collections import Counter
    n = len(labels_true)
    if n <= 1:
        return 1.0
        
    contingency = Counter(zip(labels_true, labels_pred))
    sum_nij = sum(nij * (nij - 1) / 2 for nij in contingency.values())
    
    a_counts = Counter(labels_true)
    b_counts = Counter(labels_pred)
    
    sum_ai = sum(a * (a - 1) / 2 for a in a_counts.values())
    sum_bj = sum(b * (b - 1) / 2 for b in b_counts.values())
    
    expected = (sum_ai * sum_bj) / (n * (n - 1) / 2)
    max_index = (sum_ai + sum_bj) / 2.0
    
    if max_index == expected:
        return 0.0
        
    return (sum_nij - expected) / (max_index - expected)
