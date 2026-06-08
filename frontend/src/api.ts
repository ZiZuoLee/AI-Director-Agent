import type { GenerationMode, PlanResult, ProgressEvent, TaskSnapshot } from "./types";

const API_BASE = "";

async function parseJson<T>(response: Response): Promise<T> {
  if (!response.ok) {
    const detail = await response.text();
    throw new Error(detail || `Request failed with status ${response.status}`);
  }
  return response.json() as Promise<T>;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const response = await fetch(`${API_BASE}/api/health`);
    return response.ok;
  } catch {
    return false;
  }
}

export async function createPlan(text: string, shotCount: number): Promise<PlanResult> {
  const response = await fetch(`${API_BASE}/api/plan`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, shot_count: shotCount }),
  });
  return parseJson<PlanResult>(response);
}

export async function startGeneration(
  text: string,
  shotCount: number,
  mode: GenerationMode,
): Promise<string> {
  const response = await fetch(`${API_BASE}/api/generate`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, shot_count: shotCount, mode }),
  });
  const data = await parseJson<{ task_id: string }>(response);
  return data.task_id;
}

export async function fetchTask(taskId: string): Promise<TaskSnapshot> {
  const response = await fetch(`${API_BASE}/api/tasks/${taskId}`);
  return parseJson<TaskSnapshot>(response);
}

export function subscribeTaskEvents(
  taskId: string,
  onEvent: (event: ProgressEvent) => void,
  onError?: (error: Error) => void,
): () => void {
  const source = new EventSource(`${API_BASE}/api/tasks/${taskId}/events`);

  source.onmessage = (message) => {
    try {
      const payload = JSON.parse(message.data) as ProgressEvent;
      onEvent(payload);
    } catch (error) {
      onError?.(error instanceof Error ? error : new Error("Invalid SSE payload"));
    }
  };

  const eventTypes = ["planning", "planned", "generating", "shot_done", "agent_done", "merging", "done", "error"];
  for (const eventType of eventTypes) {
    source.addEventListener(eventType, (raw) => {
      const event = raw as MessageEvent<string>;
      try {
        const payload = JSON.parse(event.data) as ProgressEvent;
        onEvent(payload);
      } catch (error) {
        onError?.(error instanceof Error ? error : new Error("Invalid SSE payload"));
      }
    });
  }

  source.onerror = () => {
    onError?.(new Error("SSE connection interrupted"));
    source.close();
  };

  return () => source.close();
}
