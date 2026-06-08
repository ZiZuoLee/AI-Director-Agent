import { useEffect, useState } from "react";
import { checkHealth, fetchTask, startGeneration, subscribeTaskEvents } from "./api";
import AgentPanel from "./components/AgentPanel";
import ImageGallery from "./components/ImageGallery";
import ParsedPanel from "./components/ParsedPanel";
import ProgressBar from "./components/ProgressBar";
import PromptPanel from "./components/PromptPanel";
import ShotPlanPanel from "./components/ShotPlanPanel";
import StoryboardView from "./components/StoryboardView";
import type {
  AgentResult,
  GeneratedImage,
  GenerationMode,
  PlanResult,
  ProgressEvent,
  TaskStatus,
} from "./types";

type UiStatus = "idle" | TaskStatus;

const INITIAL_TEXT =
  "主角在黑暗的城市小巷中奔跑，被神秘身影追赶。他满脸惊恐，然后转身面对追击者。";

export default function App() {
  const [text, setText] = useState(INITIAL_TEXT);
  const [shotCount, setShotCount] = useState(3);
  const [mode, setMode] = useState<GenerationMode>("simple");
  const [loading, setLoading] = useState(false);
  const [status, setStatus] = useState<UiStatus>("idle");
  const [message, setMessage] = useState("");
  const [percent, setPercent] = useState(0);
  const [error, setError] = useState<string | null>(null);
  const [apiOnline, setApiOnline] = useState<boolean | null>(null);

  const [plan, setPlan] = useState<PlanResult | null>(null);
  const [images, setImages] = useState<GeneratedImage[]>([]);
  const [agentResult, setAgentResult] = useState<AgentResult | null>(null);
  const [storyboardUrl, setStoryboardUrl] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<"plan" | "images" | "agent">("plan");

  useEffect(() => {
    checkHealth().then(setApiOnline);
  }, []);

  const applyProgress = (event: ProgressEvent) => {
    if (event.message) {
      setMessage(event.message);
    }
    if (typeof event.percent === "number") {
      setPercent(event.percent);
    }
    if (event.plan) {
      setPlan(event.plan);
    }
    if (event.images?.length) {
      setImages((current) => {
        const merged = [...current];
        for (const image of event.images ?? []) {
          const index = merged.findIndex((item) => item.shot_id === image.shot_id);
          if (index >= 0) {
            merged[index] = image;
          } else {
            merged.push(image);
          }
        }
        return merged.sort((a, b) => a.shot_id - b.shot_id);
      });
      setActiveTab("images");
    }
    if (event.agent_result) {
      setAgentResult(event.agent_result);
      setActiveTab("agent");
    }
    if (event.result) {
      setPlan(event.result.plan);
      setImages(event.result.images);
      setAgentResult(event.result.agent_result);
      setStoryboardUrl(event.result.storyboard_url);
      setPercent(100);
      setStatus("done");
      setMessage("全部分镜生成完成");
      setLoading(false);
    }
    if (event.stage === "error") {
      setError(event.error ?? "生成失败");
      setStatus("error");
      setLoading(false);
    } else if (event.stage && event.stage !== "done") {
      setStatus(event.stage as UiStatus);
    }
  };

  const handleGenerate = async () => {
    setLoading(true);
    setError(null);
    setStatus("pending");
    setMessage("任务已提交，正在排队…");
    setPercent(0);
    setPlan(null);
    setImages([]);
    setAgentResult(null);
    setStoryboardUrl(null);
    setActiveTab("plan");

    try {
      const taskId = await startGeneration(text.trim(), shotCount, mode);
      let finished = false;

      const finish = () => {
        if (finished) {
          return;
        }
        finished = true;
        window.clearInterval(poll);
        unsubscribe();
      };

      const unsubscribe = subscribeTaskEvents(
        taskId,
        (event) => {
          applyProgress(event);
          if (event.stage === "done" || event.stage === "error") {
            finish();
          }
        },
        async () => {
          try {
            const snapshot = await fetchTask(taskId);
            if (snapshot.result) {
              applyProgress({ stage: "done", result: snapshot.result, percent: 100 });
              finish();
            } else if (snapshot.error) {
              applyProgress({ stage: "error", error: snapshot.error });
              finish();
            }
          } catch (fetchError) {
            setError(fetchError instanceof Error ? fetchError.message : "无法获取任务状态");
            setStatus("error");
            setLoading(false);
            finish();
          }
        },
      );

      const poll = window.setInterval(async () => {
        if (finished) {
          return;
        }
        try {
          const snapshot = await fetchTask(taskId);
          if (snapshot.status === "done" && snapshot.result) {
            applyProgress({ stage: "done", result: snapshot.result, percent: 100 });
            finish();
          }
          if (snapshot.status === "error") {
            applyProgress({ stage: "error", error: snapshot.error ?? "生成失败" });
            finish();
          }
        } catch {
          // Keep polling until SSE or manual fetch succeeds.
        }
      }, 4000);
    } catch (submitError) {
      setError(submitError instanceof Error ? submitError.message : "提交任务失败");
      setStatus("error");
      setLoading(false);
    }
  };

  return (
    <div className="min-h-screen px-4 py-6 sm:px-6 lg:px-8">
      <header className="mx-auto mb-6 max-w-7xl">
        <div className="flex flex-wrap items-end justify-between gap-4">
          <div>
            <p className="text-sm uppercase tracking-[0.2em] text-cinema-accent">Fudan CG · Storyboard Agent</p>
            <h1 className="mt-2 text-3xl font-bold text-white">AI Director Agent</h1>
            <p className="mt-2 max-w-2xl text-sm text-gray-400">
              从中文剧本到电影分镜图：语义解析、镜头规划、图像生成与导演级 Agent 决策。
            </p>
          </div>
          <div className="rounded-full border border-white/10 px-3 py-1 text-xs text-gray-400">
            API {apiOnline === null ? "检测中" : apiOnline ? "在线" : "离线"}
          </div>
        </div>
      </header>

      <main className="mx-auto grid max-w-7xl gap-6 lg:grid-cols-[360px_1fr]">
        <div className="space-y-4">
          <PromptPanel
            text={text}
            shotCount={shotCount}
            mode={mode}
            loading={loading}
            onTextChange={setText}
            onShotCountChange={setShotCount}
            onModeChange={setMode}
            onSubmit={handleGenerate}
          />
          <ProgressBar percent={percent} message={message} status={status} />
          {error && (
            <div className="rounded-xl border border-red-500/30 bg-red-950/40 p-4 text-sm text-red-200">
              {error}
            </div>
          )}
        </div>

        <div className="space-y-4">
          <div className="flex gap-2 rounded-2xl border border-white/10 bg-cinema-900/50 p-2">
            {([
              ["plan", "分镜规划"],
              ["images", "生成图像"],
              ["agent", "Agent 日志"],
            ] as const).map(([key, label]) => (
              <button
                key={key}
                type="button"
                onClick={() => setActiveTab(key)}
                className={`flex-1 rounded-xl px-3 py-2 text-sm transition ${
                  activeTab === key
                    ? "bg-cinema-accent text-cinema-950 font-semibold"
                    : "text-gray-400 hover:text-white"
                }`}
              >
                {label}
              </button>
            ))}
          </div>

          {activeTab === "plan" && (
            <>
              <ParsedPanel parsed={plan?.parsed ?? null} />
              <ShotPlanPanel shots={plan?.shots ?? []} />
            </>
          )}

          {activeTab === "images" && (
            <>
              <StoryboardView storyboardUrl={storyboardUrl} />
              <ImageGallery images={images} />
            </>
          )}

          {activeTab === "agent" && <AgentPanel agentResult={agentResult} />}

          {!plan && !loading && (
            <section className="rounded-2xl border border-dashed border-white/10 p-10 text-center text-sm text-gray-500">
              输入剧本并点击「开始生成分镜」，结果将在这里展示。
            </section>
          )}
        </div>
      </main>
    </div>
  );
}
