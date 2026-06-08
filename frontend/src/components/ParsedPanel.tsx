import type { ParsedInfo } from "../types";

interface ParsedPanelProps {
  parsed: ParsedInfo | null;
}

function TagList({ label, items }: { label: string; items: string[] }) {
  if (!items.length) {
    return null;
  }

  return (
    <div>
      <p className="mb-2 text-xs uppercase tracking-wide text-gray-500">{label}</p>
      <div className="flex flex-wrap gap-2">
        {items.map((item) => (
          <span
            key={item}
            className="rounded-full border border-white/10 bg-cinema-950 px-3 py-1 text-xs text-gray-200"
          >
            {item}
          </span>
        ))}
      </div>
    </div>
  );
}

export default function ParsedPanel({ parsed }: ParsedPanelProps) {
  if (!parsed) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-white/10 bg-cinema-900/70 p-5">
      <h3 className="text-base font-semibold text-white">语义解析</h3>
      <p className="mt-1 text-sm text-gray-400">规则引擎从剧本中提取的结构化语义。</p>
      <div className="mt-4 grid gap-4 sm:grid-cols-2">
        <TagList label="动作" items={parsed.actions} />
        <TagList label="情绪" items={parsed.emotions} />
        <TagList label="场景" items={parsed.locations} />
        <TagList label="角色" items={parsed.characters} />
        <TagList label="主题" items={parsed.themes} />
      </div>
    </section>
  );
}
