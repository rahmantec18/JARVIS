import {
  ChatMessage,
  ConversationSummary,
  DesktopStatus,
  MemoryItem,
  SafeSettings,
  TaskItem,
  ToolCallDetail,
  ToolDefinition,
  ActivityLogItem
} from '../types';

const API_BASE = import.meta.env.VITE_API_BASE || '/api';

async function request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const url = `${API_BASE}${endpoint}`;
  const headers = {
    'Content-Type': 'application/json',
    ...(options.headers || {})
  };

  try {
    const res = await fetch(url, { ...options, headers });
    if (!res.ok) {
      const errBody = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(errBody.detail || `Request failed with status ${res.status}`);
    }
    return await res.json();
  } catch (err: any) {
    console.error(`API error on ${endpoint}:`, err);
    throw err;
  }
}

export const api = {
  // Health
  getHealth: () => request<any>('/health'),

  // Chat
  sendChat: (message: string, conversation_id?: string) =>
    request<{
      conversation_id: string;
      message: string;
      tool_calls: ToolCallDetail[];
      status: string;
      suggested_actions?: string[];
    }>('/chat', {
      method: 'POST',
      body: JSON.stringify({ message, conversation_id })
    }),

  // Conversations
  listConversations: () => request<ConversationSummary[]>('/conversations'),
  getConversation: (id: string) => request<any>(`/conversations/${id}`),
  deleteConversation: (id: string) =>
    request<{ status: string }>(`/conversations/${id}`, { method: 'DELETE' }),

  // Memory
  listMemories: (category?: string, query?: string) => {
    const params = new URLSearchParams();
    if (category) params.append('category', category);
    if (query) params.append('query', query);
    const qs = params.toString() ? `?${params.toString()}` : '';
    return request<MemoryItem[]>(`/memory${qs}`);
  },
  createMemory: (data: Partial<MemoryItem>) =>
    request<MemoryItem>('/memory', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  updateMemory: (id: string, data: Partial<MemoryItem>) =>
    request<MemoryItem>(`/memory/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
  deleteMemory: (id: string) =>
    request<{ status: string }>(`/memory/${id}`, { method: 'DELETE' }),
  clearMemories: () =>
    request<{ status: string }>('/memory', { method: 'DELETE' }),

  // Tools
  listTools: () => request<ToolDefinition[]>('/tools'),
  executeTool: (tool_name: string, args: Record<string, any>) =>
    request<{
      tool_name: string;
      success: boolean;
      result: any;
      error?: string;
      requires_approval: boolean;
    }>('/tools/execute', {
      method: 'POST',
      body: JSON.stringify({ tool_name, arguments: args })
    }),

  // Tasks
  listTasks: (status?: string) => {
    const qs = status ? `?status=${encodeURIComponent(status)}` : '';
    return request<TaskItem[]>(`/tasks${qs}`);
  },
  createTask: (data: Partial<TaskItem>) =>
    request<TaskItem>('/tasks', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  updateTask: (id: string, data: Partial<TaskItem>) =>
    request<TaskItem>(`/tasks/${id}`, {
      method: 'PUT',
      body: JSON.stringify(data)
    }),
  deleteTask: (id: string) =>
    request<{ status: string }>(`/tasks/${id}`, { method: 'DELETE' }),

  // Desktop Agent
  getDesktopStatus: () => request<DesktopStatus>('/desktop/status'),
  executeDesktopAction: (action: string, parameters: Record<string, any> = {}, confirmed = false) =>
    request<{
      action: string;
      success: boolean;
      result?: any;
      error?: string;
      requires_confirmation?: boolean;
      approval_id?: string;
    }>('/desktop/action', {
      method: 'POST',
      body: JSON.stringify({ action, parameters, confirmed })
    }),
  approveDesktopAction: (approval_id: string, approved: boolean) =>
    request<any>(`/desktop/approve/${approval_id}`, {
      method: 'POST',
      body: JSON.stringify({ approved })
    }),

  // Activity Log
  getActivity: (limit = 25) =>
    request<ActivityLogItem[]>(`/activity?limit=${limit}`),

  // Settings
  getSettings: () => request<SafeSettings>('/settings'),
  updateSettings: (data: Partial<SafeSettings> & { openai_api_key?: string; desktop_agent_token?: string; gemini_api_key?: string }) =>
    request<SafeSettings>('/settings', {
      method: 'POST',
      body: JSON.stringify(data)
    }),
  testGemini: (key?: string) =>
    request<{ online: boolean; status: string; message: string; available_models?: string[] }>('/settings/test-gemini', {
      method: 'POST',
      body: JSON.stringify(key ? { key } : {})
    }),

  // Authentication & Security
  login: (password: string) =>
    request<{ success: boolean; token: string; message: string; user: string }>('/auth/login', {
      method: 'POST',
      body: JSON.stringify({ password })
    }),
  verifySession: (token: string) =>
    request<{ authenticated: boolean; user: string }>('/auth/verify', {
      method: 'GET',
      headers: { Authorization: `Bearer ${token}` }
    }),
  logout: (token?: string) =>
    request<{ success: boolean; message: string }>('/auth/logout', {
      method: 'POST',
      headers: token ? { Authorization: `Bearer ${token}` } : {}
    }),
  getVoiceProfile: () =>
    request<{ enrolled: boolean; enrolled_at?: string; user: string }>('/auth/voice-profile'),
  saveVoiceProfile: (data: { enrolled: boolean; phrase?: string; voiceprint_metadata?: any }) =>
    request<{ success: boolean; message: string }>('/auth/voice-profile', {
      method: 'POST',
      body: JSON.stringify(data)
    })
};
