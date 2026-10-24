export type JarvisState =
  | 'idle'
  | 'listening'
  | 'processing'
  | 'thinking'
  | 'speaking'
  | 'executing_tool'
  | 'awaiting_approval'
  | 'success'
  | 'error';

export type ScreenView =
  | 'command'
  | 'chat'
  | 'tools'
  | 'memory'
  | 'desktop'
  | 'settings';

export interface ToolDefinition {
  name: string;
  description: string;
  parameters: Record<string, any>;
  requires_approval: boolean;
  connected: boolean;
  category: string;
}

export interface ToolCallDetail {
  id: string;
  name: string;
  arguments: Record<string, any>;
  result?: any;
  status: 'success' | 'failed' | 'awaiting_approval';
}

export interface ChatMessage {
  id: string;
  role: 'user' | 'assistant' | 'system' | 'tool';
  content: string;
  created_at: string;
  tool_calls?: ToolCallDetail[];
  status?: 'sending' | 'streaming' | 'complete' | 'error';
  error?: string;
}

export interface ConversationSummary {
  id: string;
  title: string;
  created_at: string;
  updated_at: string;
  message_count: number;
}

export interface MemoryItem {
  id: string;
  category: 'preference' | 'project' | 'fact' | 'general';
  key: string;
  content: string;
  approved: boolean;
  created_at: string;
  updated_at: string;
}

export interface TaskItem {
  id: string;
  title: string;
  description?: string;
  due_date?: string;
  status: 'pending' | 'in_progress' | 'completed' | 'cancelled';
  priority: 'low' | 'medium' | 'high' | 'critical';
  created_at: string;
  completed_at?: string;
}

export interface SystemInfo {
  os?: string;
  hostname?: string;
  cpu_percent?: number;
  cpu_cores?: number;
  memory_percent?: number;
  memory_used_gb?: number;
  memory_total_gb?: number;
  disk_percent?: number;
  disk_free_gb?: number;
  battery?: {
    percent?: number;
    charging?: boolean;
    power_plugged?: boolean;
  };
  uptime?: string;
  top_processes?: Array<{
    name: string;
    cpu: number;
    memory: number;
  }>;
}

export interface ApprovedApp {
  id: string;
  name: string;
  description: string;
  requires_approval: boolean;
}

export interface DesktopStatus {
  connected: boolean;
  service_url: string;
  system_info?: SystemInfo;
  approved_apps: ApprovedApp[];
  allowed_directories: string[];
  pending_approvals: number;
}

export interface ActivityLogItem {
  id: string;
  action_type: string;
  tool_name?: string;
  summary: string;
  status: string;
  details?: string;
  created_at: string;
}

export interface SafeSettings {
  assistant_name: string;
  assistant_voice: string;
  ai_provider: string;
  ai_model: string;
  has_openai_key: boolean;
  masked_key: string;
  has_gemini_key?: boolean;
  masked_gemini_key?: string;
  openai_base_url?: string;
  desktop_agent_enabled: boolean;
  desktop_agent_url: string;
  has_desktop_token: boolean;
  search_provider: string;
  authorized_user?: string;
  biometric_enforcement?: boolean;
}
