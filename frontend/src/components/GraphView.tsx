"use client";

import React, { useState } from "react";
import { Network, Share2, ShieldAlert, Laptop, Mail, Sparkles } from "lucide-react";
import { GraphData } from "@/types";

interface GraphViewProps {
  graphData: GraphData;
  clusterId?: string;
  clusterSize?: number;
  sharedAttributes?: string[];
}

export const GraphView: React.FC<GraphViewProps> = ({
  graphData,
  clusterId = "CLUSTER-77X",
  clusterSize = 12,
  sharedAttributes = ["device_hash_123", "email_domain_xyz.com"],
}) => {
  const [selectedNode, setSelectedNode] = useState<string | null>("TXN-98234-A");

  const getNodeColor = (group: string) => {
    switch (group) {
      case "transaction":
        return {
          fill: "#6366F1", // brand-500
          stroke: "#EEF2FF",
          label: "Current Alert",
          icon: ShieldAlert,
          badge: "bg-brand-50 text-brand-700 border-brand-200",
        };
      case "transaction_prior_fraud":
        return {
          fill: "#EF4444", // danger
          stroke: "#FEF2F2",
          label: "Known Prior Fraud",
          icon: ShieldAlert,
          badge: "bg-danger-light text-danger-dark border-danger/20",
        };
      case "device":
        return {
          fill: "#3B82F6", // blue-500
          stroke: "#EFF6FF",
          label: "Device Identifier",
          icon: Laptop,
          badge: "bg-info-light text-info-dark border-info/20",
        };
      case "email":
        return {
          fill: "#8B5CF6", // purple-500
          stroke: "#F5F3FF",
          label: "Email Domain Entity",
          icon: Mail,
          badge: "bg-purple-50 text-purple-700 border-purple-200",
        };
      default:
        return {
          fill: "#64748B",
          stroke: "#F8FAFC",
          label: "Entity Node",
          icon: Share2,
          badge: "bg-page text-text-secondary border-card-border",
        };
    }
  };

  // Coordinates for the 4 nodes in a balanced visual constellation
  const nodePositions: Record<string, { x: number; y: number }> = {
    "TXN-98234-A": { x: 180, y: 140 },
    "device_hash_123": { x: 320, y: 80 },
    "email_domain_xyz.com": { x: 320, y: 210 },
    "TXN-99999-Z": { x: 450, y: 80 },
  };

  const selectedNodeData = graphData.nodes.find((n) => n.id === selectedNode);

  return (
    <div className="bg-card rounded-card border border-card-border shadow-card p-6 md:p-8">
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-6">
        <div className="flex items-center gap-3">
          <div className="w-10 h-10 rounded-xl bg-brand-50 text-brand-500 flex items-center justify-center shrink-0">
            <Network className="w-5 h-5" />
          </div>
          <div>
            <h4 className="text-base font-semibold text-text-primary">
              Layer 3: Linked-Entity Graph & Cluster Context
            </h4>
            <p className="text-xs text-text-secondary">
              Deterministic attribute co-occurrence graph (No synthetic attributes)
            </p>
          </div>
        </div>
        <div className="flex items-center gap-2.5 self-start sm:self-auto">
          <span className="text-xs font-mono font-medium bg-brand-50 text-brand-700 border border-brand-200 px-3 py-1 rounded-badge">
            Cluster: {clusterId}
          </span>
          <span className="text-xs font-mono font-medium bg-page text-text-secondary border border-card-border px-3 py-1 rounded-badge">
            Size: {clusterSize} Entities
          </span>
        </div>
      </div>

      {/* Graph Visual Area */}
      <div className="relative w-full h-72 my-4 bg-page rounded-xl border border-card-border overflow-hidden flex items-center justify-center">
        <svg className="w-full h-full max-w-[600px] max-h-[300px]">
          {/* Links */}
          {graphData.links.map((link, idx) => {
            const src = nodePositions[link.source] || { x: 100, y: 100 };
            const tgt = nodePositions[link.target] || { x: 200, y: 200 };
            return (
              <g key={idx}>
                <line
                  x1={src.x}
                  y1={src.y}
                  x2={tgt.x}
                  y2={tgt.y}
                  stroke="#CBD5E1"
                  strokeWidth="1.5"
                  strokeDasharray="4 3"
                />
                <circle
                  cx={(src.x + tgt.x) / 2}
                  cy={(src.y + tgt.y) / 2}
                  r="3"
                  fill="#94A3B8"
                />
              </g>
            );
          })}

          {/* Nodes */}
          {graphData.nodes.map((node) => {
            const pos = nodePositions[node.id] || { x: 150, y: 150 };
            const styling = getNodeColor(node.group);
            const isSelected = selectedNode === node.id;

            return (
              <g
                key={node.id}
                className="cursor-pointer transition-transform duration-200"
                onClick={() => setSelectedNode(node.id)}
              >
                {isSelected && (
                  <circle
                    cx={pos.x}
                    cy={pos.y}
                    r={22}
                    fill="none"
                    stroke="#6366F1"
                    strokeWidth="2"
                    className="animate-ping opacity-30"
                  />
                )}
                <circle
                  cx={pos.x}
                  cy={pos.y}
                  r={isSelected ? 16 : 13}
                  fill={styling.fill}
                  stroke={isSelected ? "#4338CA" : styling.stroke}
                  strokeWidth={isSelected ? 3 : 2}
                  className="transition-all"
                />
                <text
                  x={pos.x}
                  y={pos.y + 24}
                  textAnchor="middle"
                  fill="#1E293B"
                  fontSize="11"
                  fontWeight="600"
                  fontFamily="Inter, sans-serif"
                  className="select-none"
                >
                  {node.id.length > 14 ? `${node.id.slice(0, 12)}...` : node.id}
                </text>
              </g>
            );
          })}
        </svg>

        {/* Legend Overlay */}
        <div className="absolute top-3 left-3 flex flex-wrap gap-2.5 text-[11px] bg-white/95 backdrop-blur-md px-3 py-1.5 rounded-badge border border-card-border shadow-sm">
          <span className="flex items-center gap-1.5 text-text-secondary font-medium">
            <span className="w-2 h-2 rounded-full bg-brand-500" /> Current Alert
          </span>
          <span className="flex items-center gap-1.5 text-text-secondary font-medium">
            <span className="w-2 h-2 rounded-full bg-blue-500" /> Device ID
          </span>
          <span className="flex items-center gap-1.5 text-text-secondary font-medium">
            <span className="w-2 h-2 rounded-full bg-purple-500" /> Email Domain
          </span>
          <span className="flex items-center gap-1.5 text-text-secondary font-medium">
            <span className="w-2 h-2 rounded-full bg-danger" /> Prior Fraud
          </span>
        </div>
      </div>

      {/* Node Inspector & Cluster Attributes */}
      <div className="mt-6 grid grid-cols-1 md:grid-cols-2 gap-6">
        {/* Selected Entity Inspector */}
        <div className="p-5 bg-page rounded-xl border border-card-border text-xs">
          <span className="text-xs font-semibold text-text-primary uppercase tracking-wider block mb-3">
            Selected Entity Details
          </span>
          {selectedNodeData ? (
            <div className="space-y-2.5 font-sans">
              <div className="flex items-center justify-between py-1 border-b border-card-border/60">
                <span className="text-text-secondary">Identifier:</span>
                <span className="text-text-primary font-mono font-semibold">{selectedNodeData.id}</span>
              </div>
              <div className="flex items-center justify-between py-1 border-b border-card-border/60">
                <span className="text-text-secondary">Entity Type:</span>
                <span className={`text-[11px] font-semibold px-2 py-0.5 rounded-badge border ${getNodeColor(selectedNodeData.group).badge}`}>
                  {getNodeColor(selectedNodeData.group).label}
                </span>
              </div>
              <div className="flex items-center justify-between py-1">
                <span className="text-text-secondary">Connected Degree:</span>
                <span className="text-brand-600 font-semibold">{selectedNodeData.val} Edges</span>
              </div>
            </div>
          ) : (
            <p className="text-text-muted mt-2">Click any node to inspect graph metadata.</p>
          )}
        </div>

        {/* Shared Attributes in Cluster */}
        <div className="p-5 bg-page rounded-xl border border-card-border text-xs">
          <span className="text-xs font-semibold text-text-primary uppercase tracking-wider block mb-3">
            Cluster Shared Keys ({sharedAttributes.length})
          </span>
          <div className="flex flex-wrap gap-2 mb-3">
            {sharedAttributes.map((attr, i) => (
              <span
                key={i}
                className="px-2.5 py-1 rounded-badge bg-white text-brand-600 font-mono text-xs border border-card-border flex items-center gap-1.5 shadow-sm"
              >
                <Sparkles className="w-3.5 h-3.5 text-brand-500" />
                {attr}
              </span>
            ))}
          </div>
          <p className="text-[11px] text-text-muted leading-relaxed">
            Detected via real attribute co-occurrence across transactions.
          </p>
        </div>
      </div>
    </div>
  );
};
