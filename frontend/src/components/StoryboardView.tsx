interface StoryboardViewProps {
  storyboardUrl: string | null;
}

export default function StoryboardView({ storyboardUrl }: StoryboardViewProps) {
  if (!storyboardUrl) {
    return null;
  }

  return (
    <section className="rounded-2xl border border-white/10 bg-cinema-900/70 p-5">
      <h3 className="text-base font-semibold text-white">分镜板预览</h3>
      <p className="mt-1 text-sm text-gray-400">所有镜头横向拼接后的 Storyboard。</p>
      <div className="cinema-scroll mt-4 overflow-x-auto rounded-xl border border-white/10 bg-black/30 p-3">
        <img src={storyboardUrl} alt="Storyboard" className="max-h-[420px] w-auto min-w-full object-contain" />
      </div>
    </section>
  );
}
