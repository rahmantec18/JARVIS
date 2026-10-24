import React, { useState, useRef, useEffect } from 'react';
import {
  Send,
  Plus,
  Trash2,
  Copy,
  Check,
  RotateCw,
  Search,
  MessageSquare,
  Sparkles,
  Bot,
  User,
  Wrench,
  AlertCircle
} from 'lucide-react';
import { ChatMessage, ConversationSummary } from '../types';

interface ChatViewProps {
  conversations: ConversationSummary[];
  activeConversationId: string | null;
  messages: ChatMessage[];
  onSelectConversation: (id: string) => void;
  onNewConversation: () => void;
  onDeleteConversation: (id: string) => void;
  onSendMessage: (text: string) => void;
  onRetryMessage?: (text: string) => void;
  isGenerating: boolean;
  onStopGeneration?: () => void;
}

export const ChatView: React.FC<ChatViewProps> = ({
  conversations,
  activeConversationId,
  messages,
  onSelectConversation,
  onNewConversation,
  onDeleteConversation,
  onSendMessage,
  onRetryMessage,
  isGenerating,
  onStopGeneration
}) => {
  const [inputText, setInputText] = useState('');
  const [searchQuery, setSearchQuery] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!inputText.trim() || isGenerating) return;
    onSendMessage(inputText.trim());
    setInputText('');
  };

  const handleCopy = (id: string, text: string) => {
    navigator.clipboard.writeText(text);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  const filteredConversations = conversations.filter((c) =>
    c.title.toLowerCase().includes(searchQuery.toLowerCase())
  );

  return (
    <div className="w-full max-w-7xl mx-auto h-[calc(100vh-100px)] p-4 flex gap-4">
      {/* Left Sidebar: Conversations History & Search */}
      <div className="w-72 hidden md:flex flex-col jarvis-panel rounded-2xl p-4 tech-corner">
        <div className="flex items-center justify-between pb-3 border-b border-cyan-500/20">
          <span className="text-xs font-mono font-bold text-cyan-400 tracking-wider">ARCHIVED LOGS</span>
          <button
            onClick={onNewConversation}
            className="p-1.5 rounded-lg bg-cyan-500/20 border border-cyan-400/30 text-cyan-300 hover:bg-cyan-500/30 transition text-xs flex items-center gap-1 font-mono"
            title="New Dialogue"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>NEW</span>
          </button>
        </div>

        {/* Search */}
        <div className="my-3 relative">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search logs..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900/80 border border-cyan-500/20 rounded-xl pl-9 pr-3 py-1.5 text-xs text-cyan-200 placeholder-slate-500 font-mono focus:outline-none focus:border-cyan-400"
          />
        </div>

        {/* Conversation List */}
        <div className="flex-1 overflow-y-auto space-y-1.5 pr-1">
          {filteredConversations.length === 0 ? (
            <div className="text-center text-xs font-mono text-slate-500 py-8">
              No recorded logs found.
            </div>
          ) : (
            filteredConversations.map((conv) => {
              const isActive = conv.id === activeConversationId;
              return (
                <div
                  key={conv.id}
                  onClick={() => onSelectConversation(conv.id)}
                  className={`group p-2.5 rounded-xl border cursor-pointer font-mono text-xs flex items-center justify-between transition-all ${
                    isActive
                      ? 'bg-cyan-500/20 border-cyan-400/50 text-cyan-200 shadow-[0_0_12px_rgba(0,240,255,0.15)] font-semibold'
                      : 'border-cyan-500/10 text-slate-400 hover:bg-slate-900/60 hover:text-slate-200'
                  }`}
                >
                  <div className="flex items-center gap-2 truncate">
                    <MessageSquare className="w-3.5 h-3.5 text-cyan-400 shrink-0" />
                    <span className="truncate">{conv.title}</span>
                  </div>
                  <button
                    onClick={(e) => {
                      e.stopPropagation();
                      onDeleteConversation(conv.id);
                    }}
                    className="opacity-0 group-hover:opacity-100 p-1 text-slate-500 hover:text-red-400 transition"
                    title="Delete log"
                  >
                    <Trash2 className="w-3.5 h-3.5" />
                  </button>
                </div>
              );
            })
          )}
        </div>
      </div>

      {/* Right Chat Terminal */}
      <div className="flex-1 flex flex-col jarvis-panel rounded-2xl overflow-hidden tech-corner">
        {/* Terminal Header */}
        <div className="p-4 border-b border-cyan-500/20 flex items-center justify-between font-mono text-xs">
          <div className="flex items-center gap-2 text-cyan-400">
            <Sparkles className="w-4 h-4" />
            <span className="font-bold tracking-wider">NEURAL DIALOGUE MATRIX</span>
          </div>
          {isGenerating && onStopGeneration && (
            <button
              onClick={onStopGeneration}
              className="px-2.5 py-1 rounded bg-amber-500/20 border border-amber-400/40 text-amber-300 hover:bg-amber-500/30 transition text-[11px] animate-pulse"
            >
              HALT GENERATION
            </button>
          )}
        </div>

        {/* Message Stream */}
        <div className="flex-1 overflow-y-auto p-4 space-y-4">
          {messages.length === 0 ? (
            <div className="h-full flex flex-col items-center justify-center text-center p-8 space-y-3 font-mono">
              <Bot className="w-12 h-12 text-cyan-400/40 animate-pulse" />
              <div className="text-cyan-300 font-semibold text-sm">J.A.R.V.I.S. DIALOGUE SYSTEM INITIALIZED</div>
              <p className="text-slate-400 text-xs max-w-md">
                Directives, analytical inquiries, or system automation commands may be entered below or spoken aloud.
              </p>
            </div>
          ) : (
            messages.map((msg) => {
              const isUser = msg.role === 'user';
              return (
                <div
                  key={msg.id}
                  className={`flex gap-3 max-w-3xl ${isUser ? 'ml-auto flex-row-reverse' : 'mr-auto'}`}
                >
                  {/* Avatar Icon */}
                  <div
                    className={`w-8 h-8 rounded-lg flex items-center justify-center shrink-0 border ${
                      isUser
                        ? 'bg-slate-800 border-cyan-400/30 text-cyan-300'
                        : 'bg-cyan-950/60 border-cyan-400/50 text-cyan-400 shadow-[0_0_10px_rgba(0,240,255,0.2)]'
                    }`}
                  >
                    {isUser ? <User className="w-4 h-4" /> : <Bot className="w-4 h-4" />}
                  </div>

                  {/* Message Bubble */}
                  <div
                    className={`rounded-2xl p-4 font-mono text-xs space-y-2 border ${
                      isUser
                        ? 'bg-cyan-950/30 border-cyan-400/30 text-cyan-100'
                        : 'bg-slate-900/80 border-cyan-500/20 text-slate-200'
                    }`}
                  >
                    {/* Tool Calls Pill if any */}
                    {msg.tool_calls && msg.tool_calls.length > 0 && (
                      <div className="space-y-1.5 pb-2 border-b border-cyan-500/10">
                        {msg.tool_calls.map((tc, idx) => (
                          <div
                            key={idx}
                            className="flex items-center gap-2 p-1.5 rounded bg-cyan-950/40 border border-cyan-500/30 text-[11px] text-cyan-300"
                          >
                            <Wrench className="w-3 h-3 text-cyan-400" />
                            <span>Tool Dispatched:</span>
                            <span className="font-bold">{tc.name}</span>
                            <span className="text-[10px] text-slate-400">({tc.status})</span>
                          </div>
                        ))}
                      </div>
                    )}

                    {/* Content */}
                    <div className="whitespace-pre-wrap leading-relaxed select-text font-sans text-sm">
                      {msg.content}
                    </div>

                    {/* Footer Actions */}
                    <div className="flex items-center justify-between pt-1 text-[10px] text-slate-500">
                      <span>
                        {msg.created_at
                          ? new Date(msg.created_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
                          : ''}
                      </span>
                      <div className="flex items-center gap-2">
                        <button
                          onClick={() => handleCopy(msg.id, msg.content)}
                          className="hover:text-cyan-400 transition"
                          title="Copy text"
                        >
                          {copiedId === msg.id ? <Check className="w-3 h-3 text-emerald-400" /> : <Copy className="w-3 h-3" />}
                        </button>
                        {isUser && onRetryMessage && (
                          <button
                            onClick={() => onRetryMessage(msg.content)}
                            className="hover:text-cyan-400 transition"
                            title="Resend prompt"
                          >
                            <RotateCw className="w-3 h-3" />
                          </button>
                        )}
                      </div>
                    </div>
                  </div>
                </div>
              );
            })
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input Bar */}
        <form onSubmit={handleSubmit} className="p-4 border-t border-cyan-500/20 flex gap-2">
          <input
            type="text"
            value={inputText}
            onChange={(e) => setInputText(e.target.value)}
            placeholder="Type directive to J.A.R.V.I.S..."
            className="flex-1 bg-slate-900/80 border border-cyan-500/30 rounded-xl px-4 py-2.5 text-xs text-cyan-100 placeholder-slate-500 font-mono focus:outline-none focus:border-cyan-400"
            disabled={isGenerating}
          />
          <button
            type="submit"
            disabled={!inputText.trim() || isGenerating}
            className="px-5 py-2.5 rounded-xl bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 hover:bg-cyan-500/30 font-mono text-xs flex items-center gap-2 transition disabled:opacity-40"
          >
            <Send className="w-4 h-4" />
            <span className="font-semibold">SEND</span>
          </button>
        </form>
      </div>
    </div>
  );
};
