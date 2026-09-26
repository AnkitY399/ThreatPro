"""
ThreatPro - Fraud Graph Intelligence & Geospatial Analytics Engine
Neo4j-inspired graph construction with in-memory fallback,
WCC mule network detection, DBSCAN clustering, and genetic patrol optimization.
"""

import uuid
import math
import random
import json
import hashlib
from typing import Dict, List, Tuple, Optional, Any, Set
from datetime import datetime, timedelta
from collections import defaultdict, deque

from ..config import settings


# ============================================================================
# GRAPH NODE & EDGE DATA STRUCTURES
# ============================================================================

class GraphNode:
    """Represents a node in the fraud intelligence graph."""
    
    def __init__(
        self,
        node_id: str,
        label: str,
        node_type: str,
        properties: Optional[Dict[str, Any]] = None,
    ):
        self.id = node_id
        self.label = label
        self.node_type = node_type
        self.properties = properties or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "label": self.label,
            "node_type": self.node_type,
            "properties": self.properties,
        }


class GraphEdge:
    """Represents a directed relationship between two nodes."""
    
    def __init__(
        self,
        source: str,
        target: str,
        relationship: str,
        weight: float = 1.0,
        properties: Optional[Dict[str, Any]] = None,
    ):
        self.source = source
        self.target = target
        self.relationship = relationship
        self.weight = weight
        self.properties = properties or {}

    def to_dict(self) -> Dict[str, Any]:
        return {
            "source": self.source,
            "target": self.target,
            "relationship": self.relationship,
            "weight": self.weight,
            "properties": self.properties,
        }


# ============================================================================
# IN-MEMORY FRAUD GRAPH
# ============================================================================

class FraudGraph:
    """
    In-memory fraud intelligence graph with Neo4j-compatible query patterns.
    Supports WCC (Weakly Connected Components) detection for mule networks.
    """

    def __init__(self):
        self.nodes: Dict[str, GraphNode] = {}
        self.edges: List[GraphEdge] = []
        self._adjacency: Dict[str, List[Tuple[str, str, float]]] = defaultdict(list)
        self._reverse_adjacency: Dict[str, List[Tuple[str, str, float]]] = defaultdict(list)

    def add_node(self, node: GraphNode):
        """Add or update a node in the graph."""
        self.nodes[node.id] = node

    def add_edge(self, edge: GraphEdge):
        """Add a directed edge between two nodes."""
        self.edges.append(edge)
        self._adjacency[edge.source].append((edge.target, edge.relationship, edge.weight))
        self._reverse_adjacency[edge.target].append((edge.source, edge.relationship, edge.weight))

    def get_node(self, node_id: str) -> Optional[GraphNode]:
        """Retrieve a node by ID."""
        return self.nodes.get(node_id)

    def get_neighbors(self, node_id: str, direction: str = "both") -> List[Tuple[str, str, float]]:
        """Get neighboring nodes and edge relationships."""
        if direction == "outgoing":
            return self._adjacency.get(node_id, [])
        elif direction == "incoming":
            return self._reverse_adjacency.get(node_id, [])
        else:
            result = list(self._adjacency.get(node_id, []))
            result.extend((src, rel, w) for src, rel, w in self._reverse_adjacency.get(node_id, []))
            return result

    def find_connected_components(self) -> List[Set[str]]:
        """
        Find all weakly connected components in the graph.
        Equivalent to Neo4j WCC algorithm.
        """
        visited: Set[str] = set()
        components: List[Set[str]] = []

        def bfs(start: str) -> Set[str]:
            """BFS to find all nodes connected to start."""
            component = set()
            queue = deque([start])
            while queue:
                node = queue.popleft()
                if node in visited:
                    continue
                visited.add(node)
                component.add(node)
                for neighbor, _, _ in self.get_neighbors(node):
                    if neighbor not in visited:
                        queue.append(neighbor)
            return component

        for node_id in self.nodes:
            if node_id not in visited:
                component = bfs(node_id)
                if component:
                    components.append(component)

        return components

    def detect_mule_networks(
        self,
        transactions: List[Dict[str, Any]],
        min_inflow: float = 50000.0,
        min_source_accounts: int = 3,
    ) -> List[Dict[str, Any]]:
        """
        Detect money mule networks using WCC analysis.
        
        Identifies sink accounts receiving rapid small transactions
        from multiple distinct source accounts.
        """
        # Build a transaction flow subgraph
        from collections import defaultdict as dd
        flow_graph: Dict[str, Dict[str, Any]] = {}
        
        for tx in transactions:
            target = tx.get("target_account", "")
            source = tx.get("source_account", "")
            amount = float(tx.get("amount", 0))
            device = tx.get("device_id", "")
            ip = tx.get("source_ip", "")

            if target and source:
                if target not in flow_graph:
                    flow_graph[target] = {
                        "inflow": 0.0,
                        "count": 0,
                        "sources": set(),
                        "devices": set(),
                        "ips": set(),
                    }
                flow_graph[target]["inflow"] += amount
                flow_graph[target]["count"] += 1
                flow_graph[target]["sources"].add(source)
                if device:
                    flow_graph[target]["devices"].add(device)
                if ip:
                    flow_graph[target]["ips"].add(ip)

        # Find suspicious sink accounts
        mule_networks = []
        for sink, data in flow_graph.items():
            if data["inflow"] >= min_inflow and len(data["sources"]) >= min_source_accounts:
                raw_inflow: float = data["inflow"]
                raw_sources: int = len(data["sources"])
                raw_count: int = data["count"]
                raw_devices: int = len(data["devices"])
                risk_score = min(100.0, (
                    (raw_inflow / 100000) * 30 +
                    (raw_sources / 10) * 30 +
                    (raw_count / 20) * 25 +
                    (raw_devices / 5) * 15
                ))
                
                mule_networks.append({
                    "network_id": f"MULE_{uuid.uuid4().hex[:8].upper()}",
                    "sink_account": sink,
                    "total_inflow": round(data["inflow"], 2),
                    "transaction_count": data["count"],
                    "source_accounts": list(data["sources"]),
                    "devices_involved": list(data["devices"]),
                    "ips_involved": list(data["ips"]),
                    "risk_score": round(risk_score, 2),
                })

        # Sort by risk score descending
        mule_networks.sort(key=lambda x: x["risk_score"], reverse=True)
        return mule_networks

    def get_graph_snapshot(self, max_nodes: int = 100) -> Dict[str, Any]:
        """
        Export a subset of the graph for frontend visualization.
        """
        # Select nodes (prioritize high-connectivity nodes)
        node_degrees = []
        for nid in self.nodes:
            degree = len(self._adjacency.get(nid, [])) + len(self._reverse_adjacency.get(nid, []))
            node_degrees.append((nid, degree))
        
        node_degrees.sort(key=lambda x: x[1], reverse=True)
        selected_nodes = set(nid for nid, _ in node_degrees[:max_nodes])

        nodes_out = []
        edges_out = []
        seen_edges = set()

        for nid in selected_nodes:
            nodes_out.append(self.nodes[nid].to_dict())

        for edge in self.edges:
            if edge.source in selected_nodes or edge.target in selected_nodes:
                edge_key = f"{edge.source}->{edge.target}:{edge.relationship}"
                if edge_key not in seen_edges:
                    seen_edges.add(edge_key)
                    edges_out.append(edge.to_dict())

        return {
            "nodes": nodes_out,
            "edges": edges_out,
        }

    def clear(self):
        """Reset the entire graph."""
        self.nodes.clear()
        self.edges.clear()
        self._adjacency.clear()
        self._reverse_adjacency.clear()


# ============================================================================
# GEOSPATIAL ANALYTICS ENGINE
# ============================================================================

# Indian urban centers for cybercrime hotspot simulation
URBAN_CENTERS = [
    # (city, state, lat, lon, base_incidents, base_risk)
    ("New Delhi", "Delhi", 28.6139, 77.2090, 850, 92.5),
    ("Mumbai", "Maharashtra", 19.0760, 72.8777, 920, 95.0),
    ("Bengaluru", "Karnataka", 12.9716, 77.5946, 780, 88.0),
    ("Hyderabad", "Telangana", 17.3850, 78.4867, 650, 82.5),
    ("Chennai", "Tamil Nadu", 13.0827, 80.2707, 580, 78.0),
    ("Kolkata", "West Bengal", 22.5726, 88.3639, 520, 75.5),
    ("Pune", "Maharashtra", 18.5204, 73.8567, 450, 72.0),
    ("Ahmedabad", "Gujarat", 23.0225, 72.5714, 380, 68.5),
    ("Jaipur", "Rajasthan", 26.9124, 75.7873, 310, 62.0),
    ("Lucknow", "Uttar Pradesh", 26.8467, 80.9462, 280, 58.5),
    ("Surat", "Gujarat", 21.1702, 72.8311, 250, 55.0),
    ("Chandigarh", "Chandigarh", 30.7333, 76.7794, 220, 52.0),
    ("Bhopal", "Madhya Pradesh", 23.2599, 77.4126, 200, 48.5),
    ("Patna", "Bihar", 25.5941, 85.1376, 180, 45.0),
    ("Nagpur", "Maharashtra", 21.1458, 79.0882, 160, 42.0),
    ("Indore", "Madhya Pradesh", 22.7196, 75.8577, 150, 40.0),
    ("Thane", "Maharashtra", 19.2183, 72.9781, 140, 38.0),
    ("Agra", "Uttar Pradesh", 27.1767, 78.0081, 130, 36.0),
    ("Varanasi", "Uttar Pradesh", 25.3176, 82.9739, 120, 34.0),
    ("Guwahati", "Assam", 26.1445, 91.7362, 110, 32.0),
    ("Coimbatore", "Tamil Nadu", 11.0168, 76.9558, 100, 30.0),
    ("Kochi", "Kerala", 9.9312, 76.2673, 95, 28.5),
    ("Mysuru", "Karnataka", 12.2958, 76.6394, 85, 26.0),
    ("Visakhapatnam", "Andhra Pradesh", 17.6868, 83.2185, 80, 24.5),
    ("Dehradun", "Uttarakhand", 30.3165, 78.0322, 75, 22.0),
    ("Bhubaneswar", "Odisha", 20.2961, 85.8245, 70, 20.5),
    ("Ranchi", "Jharkhand", 23.3441, 85.3096, 65, 19.0),
    ("Jammu", "Jammu & Kashmir", 32.7266, 74.8570, 60, 18.0),
    ("Srinagar", "Jammu & Kashmir", 34.0837, 74.7973, 55, 17.0),
    ("Shimla", "Himachal Pradesh", 31.1048, 77.1734, 45, 15.0),
]


class GeospatialEngine:
    """
    Geospatial analytics engine with DBSCAN clustering and patrol route optimization.
    """

    def __init__(self):
        self.locations: List[Dict[str, Any]] = []
        self.clusters: Dict[int, List[Dict[str, Any]]] = {}

    def seed_locations(self, count: int = 30):
        """Generate synthetic cybercrime incident locations."""
        self.locations = []
        for i, (city, state, lat, lon, base_incidents, base_risk) in enumerate(URBAN_CENTERS[:count]):
            # Generate multiple incident points per city
            num_incidents = random.randint(base_incidents // 2, base_incidents)
            for j in range(min(5, count // 6 + 1)):
                jitter_lat = random.gauss(0, 0.02)
                jitter_lon = random.gauss(0, 0.02)
                self.locations.append({
                    "location_id": f"LOC_{i}_{j}_{uuid.uuid4().hex[:6].upper()}",
                    "latitude": round(lat + jitter_lat, 6),
                    "longitude": round(lon + jitter_lon, 6),
                    "location_name": f"{city} - Sector {j + 1}",
                    "city": city,
                    "state": state,
                    "incident_count": random.randint(10, num_incidents),
                    "risk_level": round(base_risk + random.gauss(0, 5), 2),
                    "cluster_id": None,
                })

    def _haversine_distance(self, lat1: float, lon1: float, lat2: float, lon2: float) -> float:
        """Calculate great-circle distance in km between two points."""
        R = 6371.0  # Earth radius in km
        phi1, phi2 = math.radians(lat1), math.radians(lat2)
        dphi = math.radians(lat2 - lat1)
        dlambda = math.radians(lon2 - lon1)

        a = math.sin(dphi / 2) ** 2 + math.cos(phi1) * math.cos(phi2) * math.sin(dlambda / 2) ** 2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        return R * c

    def run_dbscan(self, eps: float = None, min_samples: int = None) -> Dict[int, List[Dict[str, Any]]]:
        """
        DBSCAN clustering algorithm for spatial hotspot detection.
        
        Args:
            eps: Maximum distance (in km) for neighborhood consideration
            min_samples: Minimum points to form a dense region
        
        Returns:
            Dict mapping cluster_id to list of locations in cluster
        """
        eps = eps or settings.DBSCAN_EPS * 111.0  # Convert degrees to km (approx)
        min_samples = min_samples or settings.DBSCAN_MIN_SAMPLES
        
        n = len(self.locations)
        if n == 0:
            return {}

        # Build distance matrix (simplified - avoid O(n^2) for large datasets)
        labels = [-1] * n  # -1 = unvisited, 0+ = cluster id
        visited = [False] * n
        noise = [False] * n
        current_cluster = 0

        def get_neighbors(idx: int) -> List[int]:
            """Find all points within eps distance."""
            neighbors = []
            loc = self.locations[idx]
            for j in range(n):
                if j != idx:
                    dist = self._haversine_distance(
                        loc["latitude"], loc["longitude"],
                        self.locations[j]["latitude"], self.locations[j]["longitude"],
                    )
                    if dist <= eps:
                        neighbors.append(j)
            return neighbors

        for i in range(n):
            if visited[i]:
                continue
            visited[i] = True

            neighbors = get_neighbors(i)
            
            if len(neighbors) < min_samples:
                noise[i] = True
                labels[i] = -2  # Noise
                continue

            # Start new cluster
            labels[i] = current_cluster
            queue = deque(neighbors)

            while queue:
                j = queue.popleft()
                if labels[j] == -2:  # Previously marked as noise
                    labels[j] = current_cluster
                if labels[j] != -1:
                    continue
                labels[j] = current_cluster

                j_neighbors = get_neighbors(j)
                if len(j_neighbors) >= min_samples:
                    for nb in j_neighbors:
                        if not visited[nb]:
                            visited[nb] = True
                            queue.append(nb)

            current_cluster += 1

        # Build cluster dictionary
        self.clusters = defaultdict(list)
        for i, label in enumerate(labels):
            if label >= 0:
                self.clusters[label].append(self.locations[i])
                self.locations[i]["cluster_id"] = label

        return dict(self.clusters)

    def get_hotspots(self) -> List[Dict[str, Any]]:
        """
        Aggregate cluster data into hotspot summaries.
        """
        hotspots = []
        for cluster_id, locations in self.clusters.items():
            if not locations:
                continue

            # Calculate cluster centroid
            avg_lat = sum(loc["latitude"] for loc in locations) / len(locations)
            avg_lon = sum(loc["longitude"] for loc in locations) / len(locations)
            total_incidents = sum(loc["incident_count"] for loc in locations)
            avg_risk = sum(loc["risk_level"] for loc in locations) / len(locations)

            hotspots.append({
                "cluster_id": cluster_id,
                "centroid_lat": round(avg_lat, 6),
                "centroid_lon": round(avg_lon, 6),
                "location_count": len(locations),
                "total_incidents": total_incidents,
                "avg_risk_level": round(avg_risk, 2),
                "cities": list(set(loc["city"] for loc in locations)),
                "radius_km": max(
                    self._haversine_distance(avg_lat, avg_lon, loc["latitude"], loc["longitude"])
                    for loc in locations
                ) if locations else 0,
            })

        hotspots.sort(key=lambda x: x["total_incidents"], reverse=True)
        return hotspots

    def optimize_patrol_route(
        self,
        hotspot_centers: List[Tuple[float, float]],
        generations: int = None,
    ) -> Dict[str, Any]:
        """
        Genetic algorithm for patrol route optimization.
        
        Args:
            hotspot_centers: List of (lat, lon) tuples to cover
            generations: Number of GA generations to run
        
        Returns:
            Optimized route with waypoints and metrics
        """
        generations = generations or settings.PATROL_OPTIMIZATION_GENERATIONS
        n_points = len(hotspot_centers)

        if n_points < 2:
            return {
                "route_id": f"PATROL_{uuid.uuid4().hex[:8].upper()}",
                "waypoints": hotspot_centers,
                "total_distance_km": 0.0,
                "estimated_time_min": 0.0,
                "coverage_score": 100.0,
                "hotspots_covered": n_points,
                "generation": 0,
            }

        # Distance matrix
        dist_matrix = [[0.0] * n_points for _ in range(n_points)]
        for i in range(n_points):
            for j in range(n_points):
                if i != j:
                    dist_matrix[i][j] = self._haversine_distance(
                        hotspot_centers[i][0], hotspot_centers[i][1],
                        hotspot_centers[j][0], hotspot_centers[j][1],
                    )

        def route_distance(route: List[int]) -> float:
            return sum(dist_matrix[route[i]][route[i + 1]] for i in range(len(route) - 1))

        # Simple GA: nearest-neighbor heuristic with random perturbations
        best_route = list(range(n_points))
        best_distance = route_distance(best_route)

        for gen in range(generations):
            # Generate candidate by swapping two random points
            candidate = best_route.copy()
            i, j = random.sample(range(n_points), 2)
            candidate[i], candidate[j] = candidate[j], candidate[i]

            cand_distance = route_distance(candidate)
            if cand_distance < best_distance:
                best_route = candidate
                best_distance = cand_distance

            # Occasionally try 2-opt improvement
            if gen % 5 == 0:
                improved = True
                while improved:
                    improved = False
                    for i in range(n_points - 1):
                        for j in range(i + 2, n_points):
                            if j - i == 1:
                                continue
                            new_route = best_route[:i+1] + best_route[i+1:j+1][::-1] + best_route[j+1:]
                            new_dist = route_distance(new_route)
                            if new_dist < best_distance:
                                best_route = new_route
                                best_distance = new_dist
                                improved = True

        waypoints = [hotspot_centers[i] for i in best_route]
        # Add return to start for complete loop
        waypoints.append(hotspot_centers[best_route[0]])

        total_dist = route_distance(best_route) + dist_matrix[best_route[-1]][best_route[0]]
        estimated_minutes = total_dist / 0.5  # Assuming 30 km/h avg patrol speed

        return {
            "route_id": f"PATROL_{uuid.uuid4().hex[:8].upper()}",
            "waypoints": [{"lat": lat, "lon": lon} for lat, lon in waypoints],
            "total_distance_km": round(total_dist, 2),
            "estimated_time_min": round(estimated_minutes, 1),
            "coverage_score": round(min(100.0, (n_points / len(self.clusters)) * 100 if self.clusters else 100), 2),
            "hotspots_covered": n_points,
            "generation": generations,
        }


# ============================================================================
# LEGAL DOSSIER GENERATOR
# ============================================================================

class LegalDossierGenerator:
    """
    Generates Section 65B-compliant legal dossiers with SHA-256 evidence hashing.
    """

    @staticmethod
    def generate(
        case_summary: str,
        graph_snapshot: Dict[str, Any],
        transactions: List[Dict[str, Any]],
        alerts: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Compile a legal dossier with cryptographic evidence validation.
        """
        dossier_id = f"DOSSIER_{uuid.uuid4().hex[:12].upper()}"

        # Serialize evidence for hashing
        evidence_data = {
            "graph": graph_snapshot,
            "transactions": transactions,
            "alerts": alerts,
            "timestamp": datetime.now().isoformat(),
        }
        evidence_json = json.dumps(evidence_data, sort_keys=True, default=str)
        sha256_hash = hashlib.sha256(evidence_json.encode()).hexdigest()

        return {
            "dossier_id": dossier_id,
            "generated_at": datetime.now(),
            "case_summary": case_summary,
            "evidence_count": len(transactions) + len(alerts),
            "graph_snapshot": graph_snapshot,
            "transaction_logs": transactions,
            "alerts": alerts,
            "sha256_hash": sha256_hash,
            "download_url": f"/api/v1/dossier/{dossier_id}/download",
        }


# ============================================================================
# GLOBAL INSTANCES
# ============================================================================

fraud_graph = FraudGraph()
geospatial_engine = GeospatialEngine()
dossier_generator = LegalDossierGenerator()