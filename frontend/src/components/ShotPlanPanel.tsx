import { useState } from "react";
import type { ShotPlan } from "../types";
import ExpandableText from "./ExpandableText";

interface ShotPlanPanelProps {
  shots: ShotPlan[];
}

function ShotCard({ shot }: { shot: ShotPlan }) {
  const [jsonExpanded, setJsonExpanded] = useState(false);

  return (
    <article className="rounded-xl border border-white/10 bg-cinema-950/80 p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs text-cinema-accent">镜头 {shot.id}</p>
          <h4 className="mt-1 text-base font-semibold text-white">{shot.type}</h4>
        </div>
        <span className="shrink-0 rounded-full border border-white/10 px-2 py-1 text-xs text-gray-400">
          {shot.camera_movement}
        </span>
      </div>

      <p className="mt-3 text-sm leading-6 text-gray-300">{shot.description}</p>
      <p className="mt-3 text-xs text-gray-500">规则理由：{shot.reason}</p>

      <div className="mt-4 rounded-lg bg-cinema-900 p-3">
        <p className="text-xs uppercase tracking-wide text-gray-500">Diffusion Prompt</p>
        <div className="mt-2">
          <ExpandableText
            text={shot.prompt}
            className="text-sm leading-6 text-gray-200"
            expandLabel="展开完整 Prompt"
            collapseLabel="收起 Prompt"
          />
        </div>
      </div>

      <button
        type="button"
        onClick={() => setJsonExpanded((value) => !value)}
        className="mt-3 text-xs text-cinema-accent hover:text-cinema-accent-dim"
      >
        {jsonExpanded ? "收起 LLM JSON" : "查看 LLM JSON"}
      </button>

      {jsonExpanded && (
        <pre className="cinema-scroll mt-2 max-h-64 overflow-auto rounded-lg border border-white/5 bg-black/40 p-3 text-xs leading-5 text-gray-300">
          {JSON.stringify(shot.llm_json ?? {}, null, 2)}
        </pre>
      )}
    </article>
  );
}

export default function ShotPlanPanel({ shots }: ShotPlanPanelProps) {
  if (!shots.length) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-white/10 bg-cinema-900/70 p-5">
      <h3 className="text-base font-semibold text-white">分镜规划</h3>
      <p className="mt-1 text-sm text-gray-400">Agent 层输出的镜头列表与电影语言推理。</p>
      <div className="mt-4 grid gap-4">
        {shots.map((shot) => (
          <ShotCard key={shot.id} shot={shot} />
        ))}
      </div>
    </section>
  );
}
