import type { GenerationMode } from "../types";

interface PromptPanelProps {
  text: string;
  shotCount: number;
  mode: GenerationMode;
  loading: boolean;
  onTextChange: (value: string) => void;
  onShotCountChange: (value: number) => void;
  onModeChange: (value: GenerationMode) => void;
  onSubmit: () => void;
}

const SAMPLE_TEXT =
  "主角在黑暗的城市小巷中奔跑，被神秘身影追赶。他满脸惊恐，然后转身面对追击者。";

const MODE_OPTIONS: Array<{
  id: GenerationMode;
  title: string;
  description: string;
  badge: string;
}> = [
  {
    id: "simple",
    title: "简单模式",
    description: "按分镜逐镜出图，速度更快，适合先验证效果。",
    badge: "推荐",
  },
  {
    id: "agentic",
    title: "导演模式",
    description: "启用跨镜记忆、候选评分与自动重试，质量更高但更慢。",
    badge: "高级",
  },
];

export default function PromptPanel({
  text,
  shotCount,
  mode,
  loading,
  onTextChange,
  onShotCountChange,
  onModeChange,
  onSubmit,
}: PromptPanelProps) {
  return (
    <section className="rounded-2xl border border-white/10 bg-cinema-900/80 p-5 shadow-xl backdrop-blur">
      <div className="mb-4">
        <h2 className="text-lg font-semibold text-white">剧本输入</h2>
        <p className="mt-1 text-sm text-gray-400">输入中文故事文本，系统将自动规划分镜并生成图像。</p>
      </div>

      <textarea
        value={text}
        onChange={(event) => onTextChange(event.target.value)}
        rows={8}
        placeholder="例如：主角在雨夜小巷中被追击……"
        className="w-full resize-y rounded-xl border border-white/10 bg-cinema-950 px-4 py-3 text-sm leading-6 text-gray-100 outline-none transition focus:border-cinema-accent/60"
      />

      <button
        type="button"
        onClick={() => onTextChange(SAMPLE_TEXT)}
        className="mt-2 text-xs text-cinema-accent hover:text-cinema-accent-dim"
      >
        填入示例剧本
      </button>

      <div className="mt-5 space-y-5">
        <label className="block text-sm text-gray-300">
          <span className="font-medium text-white">镜头数量</span>
          <input
            type="range"
            min={1}
            max={5}
            value={shotCount}
            onChange={(event) => onShotCountChange(Number(event.target.value))}
            className="mt-3 w-full accent-cinema-accent"
          />
          <span className="mt-2 inline-flex rounded-full border border-cinema-accent/30 bg-cinema-accent/10 px-3 py-1 text-sm text-cinema-accent">
            {shotCount} 镜
          </span>
        </label>

        <div>
          <p className="text-sm font-medium text-white">生成模式</p>
          <div className="mt-3 space-y-2">
            {MODE_OPTIONS.map((option) => {
              const selected = mode === option.id;
              return (
                <button
                  key={option.id}
                  type="button"
                  onClick={() => onModeChange(option.id)}
                  className={`w-full rounded-xl border p-4 text-left transition ${
                    selected
                      ? "border-cinema-accent/60 bg-cinema-accent/10 shadow-[0_0_0_1px_rgba(232,184,109,0.15)]"
                      : "border-white/10 bg-cinema-950 hover:border-white/20"
                  }`}
                >
                  <div className="flex items-start justify-between gap-3">
                    <div className="min-w-0">
                      <div className="flex items-center gap-2">
                        <span
                          className={`inline-block h-2.5 w-2.5 rounded-full ${
                            selected ? "bg-cinema-accent" : "bg-gray-600"
                          }`}
                        />
                        <span className="font-medium text-white">{option.title}</span>
                      </div>
                      <p className="mt-2 text-xs leading-5 text-gray-400">{option.description}</p>
                    </div>
                    <span
                      className={`shrink-0 rounded-full px-2 py-0.5 text-[10px] uppercase tracking-wide ${
                        selected
                          ? "bg-cinema-accent text-cinema-950"
                          : "border border-white/10 text-gray-500"
                      }`}
                    >
                      {option.badge}
                    </span>
                  </div>
                </button>
              );
            })}
          </div>
        </div>
      </div>

      <button
        type="button"
        disabled={loading || !text.trim()}
        onClick={onSubmit}
        className="mt-6 w-full rounded-xl bg-cinema-accent px-4 py-3 text-sm font-semibold text-cinema-950 transition hover:bg-cinema-accent-dim disabled:cursor-not-allowed disabled:opacity-50"
      >
        {loading ? "生成中…" : "开始生成分镜"}
      </button>
    </section>
  );
}
