interface ProgressBarProps {
  percent: number;
  message: string;
  status: string;
}

export default function ProgressBar({ percent, message, status }: ProgressBarProps) {
  if (status === "idle") {
    return null;
  }

  return (
    <section className="rounded-2xl border border-white/10 bg-cinema-900/70 p-4">
      <div className="mb-2 flex items-center justify-between text-sm">
        <span className="text-gray-300">{message}</span>
        <span className="font-medium text-cinema-accent">{percent}%</span>
      </div>
      <div className="h-2 overflow-hidden rounded-full bg-cinema-800">
        <div
          className="h-full rounded-full bg-gradient-to-r from-cinema-accent-dim to-cinema-accent transition-all duration-500"
          style={{ width: `${Math.min(100, Math.max(0, percent))}%` }}
        />
      </div>
    </section>
  );
}
