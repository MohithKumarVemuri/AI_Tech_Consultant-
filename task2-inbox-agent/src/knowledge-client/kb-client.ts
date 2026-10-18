export interface KBSourceItem {
  title: string;
  url: string;
  score: number;
  image_refs?: string[];
  heading?: string;
}

export interface KBQueryResponse {
  request_id: string;
  status: "answered" | "insufficient_evidence" | "error";
  answer: string | null;
  sources: KBSourceItem[];
  needs_human: boolean;
  escalation_id: string | null;
  model: string;
  prompt_version: string;
}

export interface KBClientConfig {
  baseUrl?: string;
  apiKey?: string;
  timeoutMs?: number;
  maxRetries?: number;
}

export class KnowledgeBrainClient {
  private baseUrl: string;
  private apiKey: string;
  private timeoutMs: number;
  private maxRetries: number;

  constructor(config?: KBClientConfig) {
    this.baseUrl =
      config?.baseUrl ||
      process.env.KB_BASE_URL ||
      process.env.NEXT_PUBLIC_KB_BASE_URL ||
      "http://localhost:8000/v1";
    this.apiKey =
      config?.apiKey ||
      process.env.KB_API_KEY ||
      process.env.NEXT_PUBLIC_KB_API_KEY ||
      "kb_secret_dev_key_2026";
    this.timeoutMs = config?.timeoutMs || 25000;
    this.maxRetries = config?.maxRetries || 2;
  }

  async checkHealth(): Promise<boolean> {
    try {
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 4000);
      const res = await fetch(`${this.baseUrl}/health`, {
        signal: controller.signal,
      });
      clearTimeout(timeoutId);
      return res.ok;
    } catch {
      return false;
    }
  }

  async query(question: string, topK: number = 5): Promise<KBQueryResponse | null> {
    let attempt = 0;
    while (attempt <= this.maxRetries) {
      attempt++;
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), this.timeoutMs);

        const res = await fetch(`${this.baseUrl}/query`, {
          method: "POST",
          headers: {
            "Content-Type": "application/json",
            "X-API-Key": this.apiKey,
          },
          body: JSON.stringify({ question, top_k: topK }),
          signal: controller.signal,
        });
        clearTimeout(timeoutId);

        if (res.ok) {
          const data = (await res.json()) as KBQueryResponse;
          return data;
        }

        if (res.status === 401) {
          console.error("[KnowledgeBrainClient] 401 Unauthorized - Check KB_API_KEY");
          return null;
        }
      } catch (err) {
        if (attempt > this.maxRetries) {
          console.warn(`[KnowledgeBrainClient] T1 query failed after ${attempt} attempts: ${err}`);
          return null;
        }
        await new Promise((r) => setTimeout(r, 800 * attempt));
      }
    }
    return null;
  }
}

export const kbClient = new KnowledgeBrainClient();
