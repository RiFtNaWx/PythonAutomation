import React, { useCallback, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  ReactFlow,
  Background,
  Controls,
  MiniMap,
  addEdge,
  useEdgesState,
  useNodesState,
  Handle,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import "./canvas.css";

const OPCODES = [
  "sweep",
  "for_corners",
  "for_list",
  "if_else",
  "pause",
  "psu_set",
  "awg_out",
  "dmm_read",
  "scope_detect",
  "screenshot",
  "measure",
  "end",
];

function OpNode({ data }) {
  return (
    <div className="ate-op-node">
      <Handle type="target" position={Position.Top} />
      <strong>{data.op}</strong>
      {data.hint ? <div className="ate-op-hint">{data.hint}</div> : null}
      <Handle type="source" position={Position.Bottom} />
    </div>
  );
}

const nodeTypes = { op: OpNode };

function hintFor(op, data) {
  if (op === "for_corners") return `n=${data.n ?? 2}`;
  if (op === "for_list" || op === "sweep") return data.var || "vcc";
  if (op === "measure" || op === "dmm_read") return data.measure_id || "";
  if (op === "psu_set") return `CH${data.ch || 1}`;
  return "";
}

function toFlow(graph) {
  const nodes = [];
  const edges = [];
  let y = 0;
  function walk(list, parentId) {
    (list || []).forEach((n, i) => {
      const id = String(n.id || `n${y}`);
      const op = String(n.op || n.type || "measure");
      nodes.push({
        id,
        type: "op",
        position: { x: 80 + (parentId ? 40 : 0), y: y * 70 },
        data: { ...n, op, hint: hintFor(op, n) },
      });
      if (parentId) {
        edges.push({ id: `e-${parentId}-${id}`, source: parentId, target: id });
      }
      y += 1;
      if (Array.isArray(n.children) && n.children.length) {
        walk(n.children, id);
      }
    });
  }
  if (Array.isArray(graph?.nodes)) {
    // Prefer nested children; also honor flat edges
    walk(graph.nodes, null);
    (graph.edges || []).forEach((e, i) => {
      if (!e || !e.source || !e.target) return;
      const eid = e.id || `edge-${i}`;
      if (!edges.some((x) => x.source === e.source && x.target === e.target)) {
        edges.push({ id: eid, source: e.source, target: e.target });
      }
    });
  }
  if (!nodes.length) {
    nodes.push({
      id: "n1",
      type: "op",
      position: { x: 80, y: 40 },
      data: { op: "for_corners", n: 2, levels: [0, 5.5], hint: "n=2" },
    });
    nodes.push({
      id: "n2",
      type: "op",
      position: { x: 80, y: 120 },
      data: { op: "measure", measure_id: "CORNER_V", unit: "V", hint: "CORNER_V" },
    });
    edges.push({ id: "e-n1-n2", source: "n1", target: "n2" });
  }
  return { nodes, edges };
}

function fromFlow(nodes, edges) {
  const byId = {};
  nodes.forEach((n) => {
    byId[n.id] = {
      id: n.id,
      op: n.data?.op || "measure",
      ...Object.fromEntries(
        Object.entries(n.data || {}).filter(
          ([k]) => !["op", "hint", "label"].includes(k)
        )
      ),
    };
  });
  const targets = new Set(edges.map((e) => e.target));
  const childrenOf = {};
  edges.forEach((e) => {
    (childrenOf[e.source] ||= []).push(e.target);
  });
  function build(id, seen) {
    if (seen.has(id)) return byId[id];
    seen.add(id);
    const node = { ...byId[id] };
    const kids = childrenOf[id] || [];
    if (kids.length) {
      node.children = kids.map((k) => build(k, seen));
    }
    return node;
  }
  const roots = nodes.map((n) => n.id).filter((id) => !targets.has(id));
  const top = (roots.length ? roots : nodes.map((n) => n.id)).map((id) =>
    build(id, new Set())
  );
  return {
    nodes: top,
    edges: edges.map((e) => ({ id: e.id, source: e.source, target: e.target })),
  };
}

function CanvasApp({ initialGraph, onChange }) {
  const seed = useMemo(() => toFlow(initialGraph || {}), []);
  const [nodes, setNodes, onNodesChange] = useNodesState(seed.nodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(seed.edges);

  useEffect(() => {
    if (!onChange) return;
    onChange(fromFlow(nodes, edges));
  }, [nodes, edges, onChange]);

  const onConnect = useCallback(
    (conn) => setEdges((eds) => addEdge(conn, eds)),
    [setEdges]
  );

  const addOp = (op) => {
    const id = `n${Date.now().toString(36)}`;
    setNodes((ns) => [
      ...ns,
      {
        id,
        type: "op",
        position: { x: 60 + ns.length * 12, y: 40 + ns.length * 48 },
        data: {
          op,
          n: op === "for_corners" ? 2 : undefined,
          levels: op === "for_corners" ? [0, 5.5] : undefined,
          measure_id: op === "measure" || op === "dmm_read" ? "MEAS" : undefined,
          unit: op === "measure" || op === "dmm_read" ? "V" : undefined,
          ch: op === "psu_set" || op === "awg_out" ? 1 : undefined,
          hint: hintFor(op, { n: 2, measure_id: "MEAS", ch: 1 }),
        },
      },
    ]);
  };

  return (
    <div className="ate-canvas-wrap">
      <div className="ate-palette">
        {OPCODES.map((op) => (
          <button key={op} type="button" className="ate-palette-btn" onClick={() => addOp(op)}>
            {op}
          </button>
        ))}
      </div>
      <div className="ate-flow">
        <ReactFlow
          nodes={nodes}
          edges={edges}
          onNodesChange={onNodesChange}
          onEdgesChange={onEdgesChange}
          onConnect={onConnect}
          nodeTypes={nodeTypes}
          fitView
        >
          <Background />
          <Controls />
          <MiniMap />
        </ReactFlow>
      </div>
    </div>
  );
}

function mount(el, opts = {}) {
  if (!el) throw new Error("recipe canvas mount: missing element");
  const root = createRoot(el);
  let latest = opts.graph || {};
  const onChange = (g) => {
    latest = g;
    if (typeof opts.onChange === "function") opts.onChange(g);
  };
  root.render(<CanvasApp initialGraph={opts.graph} onChange={onChange} />);
  return {
    getGraph: () => latest,
    setGraph: (g) => {
      latest = g || {};
      root.render(<CanvasApp initialGraph={latest} onChange={onChange} />);
    },
    destroy: () => root.unmount(),
  };
}

const api = { mount, OPCODES };
if (typeof window !== "undefined") {
  window.ATERecipeCanvas = api;
}

export default api;
