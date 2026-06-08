import type { AgentResult } from "../types";

interface AgentPanelProps {
  agentResult: AgentResult | null;
}

export default function AgentPanel({ agentResult }: AgentPanelProps) {
  if (!agentResult) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-white/10 bg-cinema-900/70 p-5">
      <h3 className="text-base font-semibold text-white">导演 Agent 日志</h3>
      <p className="mt-1 text-sm text-gray-400">跨镜头记忆、候选评分与重试策略。</p>

      <div className="mt-4 space-y-4">
        {agentResult.shots.map((shot) => (
          <article key={shot.shot_id} className="rounded-xl border border-white/10 bg-cinema-950 p-4">
            <div className="flex flex-wrap items-center justify-between gap-2">
              <h4 className="font-medium text-white">镜头 {shot.shot_id}</h4>
              <div className="flex gap-2 text-xs">
                {shot.selected_image.critic_score && (
                  <span className="rounded-full bg-cinema-800 px-2 py-1 text-cinema-accent">
                    评分 {(shot.selected_image.critic_score as { total?: number }).total?.toFixed(2) ?? "—"}
                  </span>
                )}
                {shot.selected_image.vision_analysis && (
                  <span className="rounded-full bg-cinema-800 px-2 py-1 text-gray-300">
                    Vision{" "}
                    {(shot.selected_image.vision_analysis as { score?: number }).score?.toFixed(2) ?? "—"}
                  </span>
                )}
              </div>
            </div>

            {shot.reflections.length > 0 && (
              <div className="mt-3 space-y-2">
                {shot.reflections.map((reflection, index) => (
                  <div key={`${reflection.shot_id}-${reflection.attempt}-${index}`} className="rounded-lg bg-cinema-900 p-3 text-xs text-gray-300">
                    <p>
                      尝试 {reflection.attempt} · 策略 {reflection.strategy} · 分数 {reflection.score.toFixed(2)}
                    </p>
                    <p className="mt-1 text-gray-500">
                      {reflection.issue} → {reflection.action}
                    </p>
                    {reflection.rationale.length > 0 && (
                      <ul className="mt-2 list-disc pl-4 text-gray-500">
                        {reflection.rationale.map((line) => (
                          <li key={line}>{line}</li>
                        ))}
                      </ul>
                    )}
                  </div>
                ))}
              </div>
            )}

            {shot.candidates.length > 1 && (
              <details className="mt-3 text-xs text-gray-400">
                <summary className="cursor-pointer text-cinema-accent">查看 {shot.candidates.length} 个候选</summary>
                <div className="mt-2 grid gap-2 sm:grid-cols-2">
                  {shot.candidates.map((candidate) => (
                    <div key={candidate.image_path} className="rounded-lg border border-white/5 p-2">
                      {candidate.image_url && (
                        <img
                          src={candidate.image_url}
                          alt={`候选 ${shot.shot_id}`}
                          className="aspect-video w-full rounded object-cover"
                        />
                      )}
                    </div>
                  ))}
                </div>
              </details>
            )}
          </article>
        ))}
      </div>

      <details className="mt-4 text-xs text-gray-400">
        <summary className="cursor-pointer text-cinema-accent">查看跨镜头记忆 JSON</summary>
        <pre className="cinema-scroll mt-2 max-h-64 overflow-auto rounded-lg border border-white/5 bg-black/40 p-3">
          {JSON.stringify(agentResult.memory, null, 2)}
        </pre>
      </details>
    </section>
  );
}
