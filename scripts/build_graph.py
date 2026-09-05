#!/usr/bin/env python3
"""
Sentinel Linked-Entity Graph Analytics Engine (Phase 3)
======================================================
Constructs a heterogeneous entity graph from real IEEE-CIS transaction attributes
using NetworkX and computes deterministic structural risk analytics:

1. Entity Graph Construction:
   - Node Types: Transaction, Card, Address, EmailDomain, Device.
   - Edge Types: uses_card, uses_addr, uses_email, uses_device.
   - Strict Anti-Leakage: Zero fabricated fields, zero label density in scoring path.

2. Deterministic Graph Analytics:
   - Connected Components (clustering multi-transaction syndicates).
   - Degree Centrality (identifying hub cards, devices, and shared identifiers).
   - Per-Transaction Graph Context (cluster ID, cluster size, shared entities).

3. Visualization Payload:
   - Exports graph summary metrics and force-directed subgraph to `data/processed/graph_analytics.json`.

Usage:
    python scripts/build_graph.py --train-path data/processed/train.parquet --output-json data/processed/graph_analytics.json
"""

from __future__ import annotations

import argparse
import json
import logging
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

# Ensure root in sys.path
_project_root = Path(__file__).resolve().parent.parent
if str(_project_root) not in sys.path:
    sys.path.insert(0, str(_project_root))

import networkx as nx
import numpy as np
import pandas as pd

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s - %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger("sentinel.build_graph")


def is_valid_value(val: Any) -> bool:
    """Check if attribute value is not null, NaN, or placeholder."""
    if val is None:
        return False
    if isinstance(val, float) and (np.isnan(val) or np.isinf(val)):
        return False
    s = str(val).strip()
    return bool(s and s.lower() not in ("nan", "none", "null", "__missing__", "undefined"))


def build_ieee_cis_graph(df: pd.DataFrame) -> nx.Graph:
    """
    Build heterogeneous NetworkX graph from IEEE-CIS transaction DataFrame.
    """
    logger.info("Building NetworkX heterogeneous graph from %d transactions...", len(df))
    G = nx.Graph()

    for _, row in df.iterrows():
        txn_id = int(row["TransactionID"]) if "TransactionID" in row else int(row.name)
        txn_node = f"txn_{txn_id}"

        # Add transaction node
        amt = float(row.get("TransactionAmt", 0.0)) if is_valid_value(row.get("TransactionAmt")) else 0.0
        dt = int(row.get("TransactionDT", 0)) if is_valid_value(row.get("TransactionDT")) else 0
        G.add_node(
            txn_node,
            node_type="transaction",
            txn_id=txn_id,
            amount=amt,
            dt=dt,
            label=f"Txn #{txn_id}",
        )

        # 1. Card entity (card1, card2, card4)
        c1 = row.get("card1")
        if is_valid_value(c1):
            c1_str = str(int(c1) if isinstance(c1, (int, float)) and not np.isnan(c1) else c1)
            card_node = f"card_{c1_str}"
            if not G.has_node(card_node):
                card4 = str(row.get("card4", "card")).lower() if is_valid_value(row.get("card4")) else "card"
                G.add_node(card_node, node_type="card", card_id=c1_str, brand=card4, label=f"Card {c1_str}")
            G.add_edge(txn_node, card_node, relation="uses_card")

        # 2. Address entity (addr1, addr2)
        a1 = row.get("addr1")
        a2 = row.get("addr2")
        if is_valid_value(a1):
            a1_str = str(int(a1) if isinstance(a1, (int, float)) and not np.isnan(a1) else a1)
            a2_str = str(int(a2) if isinstance(a2, (int, float)) and not np.isnan(a2) else "NA")
            addr_node = f"addr_{a1_str}_{a2_str}"
            if not G.has_node(addr_node):
                G.add_node(addr_node, node_type="address", addr1=a1_str, addr2=a2_str, label=f"Addr {a1_str}-{a2_str}")
            G.add_edge(txn_node, addr_node, relation="uses_address")

        # 3. Email domain entity (P_emaildomain)
        p_email = row.get("P_emaildomain")
        if is_valid_value(p_email):
            p_email_str = str(p_email).strip().lower()
            email_node = f"email_{p_email_str}"
            if not G.has_node(email_node):
                G.add_node(email_node, node_type="email_domain", domain=p_email_str, label=f"Email @{p_email_str}")
            G.add_edge(txn_node, email_node, relation="uses_email")

        # 4. Device entity (DeviceInfo or DeviceType)
        device_info = row.get("DeviceInfo")
        device_type = row.get("DeviceType")
        if is_valid_value(device_info):
            d_str = str(device_info).strip()
            dev_node = f"device_{d_str}"
            if not G.has_node(dev_node):
                G.add_node(dev_node, node_type="device", device_info=d_str, device_type=str(device_type or "unknown"), label=f"Device {d_str}")
            G.add_edge(txn_node, dev_node, relation="uses_device")
        elif is_valid_value(device_type):
            dt_str = str(device_type).strip()
            dev_node = f"devicetype_{dt_str}"
            if not G.has_node(dev_node):
                G.add_node(dev_node, node_type="device", device_info=dt_str, device_type=dt_str, label=f"DeviceType {dt_str}")
            G.add_edge(txn_node, dev_node, relation="uses_device")

    logger.info(
        "Graph construction complete: %d nodes, %d edges.",
        G.number_of_nodes(),
        G.number_of_edges(),
    )
    return G


def compute_graph_analytics(G: nx.Graph, max_clusters_to_export: int = 20) -> Dict[str, Any]:
    """
    Perform deep structural graph analysis:
    - Degree centrality & top hub identification
    - Connected components detection & cluster extraction
    - Per-transaction lookup table
    - Force-directed visualization subgraph
    """
    logger.info("Computing degree centrality and connected components...")

    # 1. Degree Centrality
    degrees = dict(G.degree())
    degree_centrality = nx.degree_centrality(G)

    # Node count breakdown by type
    node_types: Dict[str, int] = {}
    for node, data in G.nodes(data=True):
        ntype = data.get("node_type", "unknown")
        node_types[ntype] = node_types.get(ntype, 0) + 1

    # Hub entities (non-transaction nodes with highest degree)
    entity_nodes = [
        (n, degrees[n], degree_centrality[n], G.nodes[n].get("node_type"), G.nodes[n].get("label"))
        for n in G.nodes()
        if G.nodes[n].get("node_type") != "transaction"
    ]
    entity_nodes.sort(key=lambda x: x[1], reverse=True)

    top_hubs = [
        {
            "node_id": n,
            "degree": deg,
            "centrality": round(float(cent), 6),
            "type": ntype,
            "label": label,
        }
        for n, deg, cent, ntype, label in entity_nodes[:25]
    ]

    # 2. Connected Components
    components = list(nx.connected_components(G))
    components.sort(key=len, reverse=True)

    total_components = len(components)
    comp_sizes = [len(c) for c in components]

    # Extract multi-transaction clusters
    cluster_list: List[Dict[str, Any]] = []
    transaction_lookup: Dict[str, Any] = {}

    for idx, comp in enumerate(components):
        cluster_id = f"CLUSTER-{idx + 1:03d}"
        comp_nodes = list(comp)
        txn_nodes = [n for n in comp_nodes if G.nodes[n].get("node_type") == "transaction"]
        entity_subnodes = [n for n in comp_nodes if G.nodes[n].get("node_type") != "transaction"]

        txn_ids = [int(G.nodes[n].get("txn_id", n.replace("txn_", ""))) for n in txn_nodes]
        shared_attributes = [
            G.nodes[n].get("label", n) for n in entity_subnodes[:8]
        ]

        for t_node in txn_nodes:
            t_id = str(G.nodes[t_node].get("txn_id", t_node.replace("txn_", "")))
            transaction_lookup[t_id] = {
                "cluster_id": cluster_id,
                "cluster_size": len(txn_nodes),
                "total_connected_entities": len(entity_subnodes),
                "shared_attributes": shared_attributes,
                "is_multi_transaction_cluster": len(txn_nodes) > 1,
            }

        if len(txn_nodes) > 1 and len(cluster_list) < max_clusters_to_export:
            # Build sample nodes & links for this cluster
            sub_G = G.subgraph(comp_nodes[:30])
            sub_nodes = [
                {
                    "id": n,
                    "label": sub_G.nodes[n].get("label", n),
                    "type": sub_G.nodes[n].get("node_type", "entity"),
                    "degree": degrees.get(n, 1),
                    "amount": sub_G.nodes[n].get("amount"),
                }
                for n in sub_G.nodes()
            ]
            sub_links = [
                {
                    "source": u,
                    "target": v,
                    "relation": sub_G.edges[u, v].get("relation", "connected_to"),
                }
                for u, v in sub_G.edges()
            ]

            cluster_list.append({
                "cluster_id": cluster_id,
                "transaction_count": len(txn_nodes),
                "total_node_count": len(comp_nodes),
                "sample_transaction_ids": txn_ids[:15],
                "shared_entities": shared_attributes,
                "subgraph": {
                    "nodes": sub_nodes,
                    "links": sub_links,
                },
            })

    # 3. Create a Representative Demo Subgraph for UI (largest multi-entity cluster)
    demo_nodes: List[Dict[str, Any]] = []
    demo_links: List[Dict[str, Any]] = []
    if cluster_list:
        demo_nodes = cluster_list[0]["subgraph"]["nodes"]
        demo_links = cluster_list[0]["subgraph"]["links"]

    summary_stats = {
        "total_nodes": G.number_of_nodes(),
        "total_edges": G.number_of_edges(),
        "total_transactions": node_types.get("transaction", 0),
        "total_entities": G.number_of_nodes() - node_types.get("transaction", 0),
        "node_types": node_types,
        "connected_components_count": total_components,
        "multi_transaction_clusters_count": sum(1 for c in cluster_list if c["transaction_count"] > 1),
        "largest_cluster_size": comp_sizes[0] if comp_sizes else 0,
        "avg_component_size": round(float(np.mean(comp_sizes)), 2) if comp_sizes else 0.0,
        "median_component_size": float(np.median(comp_sizes)) if comp_sizes else 0.0,
        "density": round(float(nx.density(G)), 6),
    }

    analytics_payload = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "methodology": "Deterministic entity linkage on real IEEE-CIS native attributes (cards, addrs, emails, devices)",
        "summary": summary_stats,
        "top_hub_entities": top_hubs,
        "top_clusters": cluster_list,
        "transaction_lookup": transaction_lookup,
        "demo_subgraph": {
            "nodes": demo_nodes,
            "links": demo_links,
        },
    }

    logger.info("Graph Analytics Summary:")
    logger.info("  Total Nodes: %d (Transactions: %d, Entities: %d)",
                summary_stats["total_nodes"], summary_stats["total_transactions"], summary_stats["total_entities"])
    logger.info("  Total Edges: %d | Total Components: %d | Largest: %d nodes",
                summary_stats["total_edges"], summary_stats["connected_components_count"], summary_stats["largest_cluster_size"])
    return analytics_payload


def main():
    parser = argparse.ArgumentParser(description="Sentinel Linked-Entity Graph Analytics")
    parser.add_argument("--train-path", type=str, default="data/processed/train.parquet", help="Path to train.parquet")
    parser.add_argument("--output-json", type=str, default="data/processed/graph_analytics.json", help="Path to save graph analytics JSON")
    parser.add_argument("--max-clusters", type=int, default=20, help="Number of multi-transaction clusters to export")

    args = parser.parse_args()

    project_root = Path(__file__).resolve().parent.parent
    train_path = project_root / args.train_path if not Path(args.train_path).is_absolute() else Path(args.train_path)
    output_path = project_root / args.output_json if not Path(args.output_json).is_absolute() else Path(args.output_json)

    logger.info("Loading training data for graph construction: %s", train_path)
    train_df = pd.read_parquet(train_path)

    G = build_ieee_cis_graph(train_df)
    analytics = compute_graph_analytics(G, max_clusters_to_export=args.max_clusters)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    logger.info("Writing graph analytics JSON to: %s", output_path)
    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(analytics, f, indent=2)

    logger.info("Graph analytics successfully built and saved!")


if __name__ == "__main__":
    main()
