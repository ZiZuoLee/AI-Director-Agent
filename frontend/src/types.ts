export type GenerationMode = "simple" | "agentic";

export type TaskStatus =
  | "pending"
  | "planning"
  | "generating"
  | "merging"
  | "done"
  | "error";

export interface ParsedInfo {
  raw_text: string;
  sentences: string[];
  actions: string[];
  emotions: string[];
  locations: string[];
  characters: string[];
  themes: string[];
}

export interface ShotPlan {
  id: number;
  type: string;
  description: string;
  camera_movement: string;
  raw_prompt: string;
  prompt: string;
  reason: string;
  llm_json?: Record<string, unknown>;
}

export interface PlanResult {
  input_text: string;
  parsed: ParsedInfo;
  shots: ShotPlan[];
}

export interface GeneratedImage {
  shot_id: number;
  prompt: string;
  negative_prompt: string;
  image_path: string;
  image_url?: string;
  seed: number;
  steps: number;
  guidance_scale: number;
  backend: string;
  model_id: string;
  width: number;
  height: number;
  metadata?: Record<string, unknown>;
  critic_score?: Record<string, unknown>;
  vision_analysis?: Record<string, unknown>;
}

export interface DirectorReflection {
  shot_id: number;
  attempt: number;
  strategy: string;
  issue: string;
  action: string;
  score: number;
  rationale: string[];
}

export interface DirectorShotResult {
  shot_id: number;
  selected_image: GeneratedImage;
  candidates: GeneratedImage[];
  reflections: DirectorReflection[];
}

export interface AgentResult {
  memory: Record<string, unknown>;
  shots: DirectorShotResult[];
}

export interface PipelineResult {
  input_text: string;
  mode: GenerationMode;
  plan: PlanResult;
  images: GeneratedImage[];
  agent_result: AgentResult | null;
  storyboard_path: string | null;
  storyboard_url: string | null;
}

export interface TaskSnapshot {
  task_id: string;
  status: TaskStatus;
  message: string;
  percent: number;
  created_at: string;
  updated_at: string;
  plan: PlanResult | null;
  images: GeneratedImage[];
  agent_result: AgentResult | null;
  storyboard_url: string | null;
  result: PipelineResult | null;
  error: string | null;
}

export interface ProgressEvent {
  stage: string;
  message?: string;
  percent?: number;
  plan?: PlanResult;
  shot_id?: number;
  images?: GeneratedImage[];
  agent_result?: AgentResult;
  result?: PipelineResult;
  error?: string;
}
