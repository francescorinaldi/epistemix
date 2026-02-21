"use client";

import { useEffect, useRef } from "react";
import type { FindingData } from "@/lib/types";

interface Props {
  findings: FindingData[];
}

/**
 * Interactive force-directed citation graph using D3.
 * Shows scholars as nodes, citations as edges.
 * Node size = citation count. Color = finding type.
 */
export default function CitationGraph({ findings }: Props) {
  const svgRef = useRef<SVGSVGElement>(null);

  useEffect(() => {
    if (!svgRef.current || findings.length === 0) return;

    // Dynamic import to avoid SSR issues
    import("d3").then((d3) => {
      const svg = d3.select(svgRef.current);
      svg.selectAll("*").remove();

      const width = svgRef.current!.clientWidth;
      const height = 300;

      // Build nodes and links from findings
      const nodeMap = new Map<string, { id: string; type: string; citations: number }>();
      const links: { source: string; target: string }[] = [];

      for (const f of findings) {
        const id = f.name.toLowerCase().trim();
        if (!nodeMap.has(id)) {
          nodeMap.set(id, { id: f.name, type: f.finding_type, citations: 0 });
        }
        for (const cited of f.citations || []) {
          const citedId = cited.toLowerCase().trim();
          if (!nodeMap.has(citedId)) {
            nodeMap.set(citedId, { id: cited, type: "scholar", citations: 0 });
          }
          nodeMap.get(citedId)!.citations++;
          links.push({ source: id, target: citedId });
        }
      }

      const nodes = Array.from(nodeMap.values());
      if (nodes.length === 0) return;

      const colorScale: Record<string, string> = {
        scholar: "var(--chart-1)",
        theory: "var(--chart-2)",
        institution: "var(--chart-3)",
        evidence: "var(--chart-5)",
        publication: "var(--chart-4)",
        method: "var(--chart-6)",
      };

      const simulation = d3
        .forceSimulation(nodes as any)
        .force("link", d3.forceLink(links as any).id((d: any) => d.id.toLowerCase().trim()).distance(60))
        .force("charge", d3.forceManyBody().strength(-100))
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collision", d3.forceCollide().radius(20));

      const link = svg
        .append("g")
        .selectAll("line")
        .data(links)
        .join("line")
        .attr("stroke", "rgba(255,255,255,0.04)")
        .attr("stroke-width", 0.5);

      const node = svg
        .append("g")
        .selectAll("circle")
        .data(nodes)
        .join("circle")
        .attr("r", (d: any) => Math.max(4, Math.min(12, 4 + d.citations * 2)))
        .attr("fill", (d: any) => colorScale[d.type] || "var(--text-tertiary)")
        .attr("stroke", "var(--bg-page)")
        .attr("stroke-width", 1);

      const label = svg
        .append("g")
        .selectAll("text")
        .data(nodes)
        .join("text")
        .text((d: any) => d.id.length > 15 ? d.id.slice(0, 15) + "..." : d.id)
        .attr("font-size", 7)
        .attr("font-family", "var(--font-body)")
        .attr("fill", "var(--text-ghost)")
        .attr("dx", 10)
        .attr("dy", 3);

      // Add tooltip on hover
      node.append("title").text((d: any) => `${d.id} (${d.type}, ${d.citations} citations)`);

      simulation.on("tick", () => {
        link
          .attr("x1", (d: any) => d.source.x)
          .attr("y1", (d: any) => d.source.y)
          .attr("x2", (d: any) => d.target.x)
          .attr("y2", (d: any) => d.target.y);
        node.attr("cx", (d: any) => d.x).attr("cy", (d: any) => d.y);
        label.attr("x", (d: any) => d.x).attr("y", (d: any) => d.y);
      });
    });
  }, [findings]);

  if (findings.length === 0) {
    return <div className="empty">No findings to graph yet.</div>;
  }

  return (
    <div className="graph-container">
      <h3>Citation Network</h3>
      <svg ref={svgRef} width="100%" height={300} />

      <style jsx>{`
        .graph-container {
          background: var(--bg-card);
          border: 1px solid var(--border-subtle);
          border-radius: var(--radius-lg);
          padding: 2rem;
          overflow: hidden;
        }
        h3 {
          font-family: var(--font-display);
          font-size: 1rem;
          color: var(--text-heading);
          margin: 0 0 1.25rem 0;
          font-weight: 400;
        }
        .empty {
          color: var(--text-ghost);
          font-family: var(--font-body);
          font-size: 0.8125rem;
          text-align: center;
          padding: 3rem 2rem;
        }
      `}</style>
    </div>
  );
}
