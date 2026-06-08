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

      <div className="mt-5 grid gap-4 sm:grid-cols-2">
        <label className="block text-sm text-gray-300">
          镜头数量
          <input
            type="range"
            min={1}
            max={5}
            value={shotCount}
            onChange={(event) => onShotCountChange(Number(event.target.value))}
            className="mt-2 w-full accent-cinema-accent"
          />
          <span className="mt-1 inline-block text-cinema-accent">{shotCount} 镜</span>
        </label>

        <fieldset className="text-sm text-gray-300">
          <legend className="mb-2">生成模式</legend>
          <div className="flex gap-3">
            <label className="flex flex-1 cursor-pointer items-center gap-2 rounded-xl border border-white/10 bg-cinema-950 px-3 py-2">
              <input
                type="radio"
                name="mode"
                value="simple"
                checked={mode === "simple"}
                onChange={() => onModeChange("simple")}
              />
              <span>
                <span className="block font-medium text-white">简单模式</span>
                <span className="text-xs text-gray-500">快速出图</span>
              </span>
            </label>
            <label className="flex flex-1 cursor-pointer items-center gap-2 rounded-xl border border-white/10 bg-cinema-950 px-3 py-2">
              <input
                type="radio"
                name="mode"
                value="agentic"
                checked={mode === "agentic"}
                onChange={() => onModeChange("agentic")}
              />
              <span>
                <span className="block font-medium text-white">导演模式</span>
                <span className="text-xs text-gray-500">记忆 + 评分 + 重试</span>
              </span>
            </label>
          </div>
        </fieldset>
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
