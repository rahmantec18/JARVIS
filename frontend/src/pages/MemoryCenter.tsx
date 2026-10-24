import React, { useState } from 'react';
import {
  Database,
  Search,
  Plus,
  Trash2,
  Edit2,
  Check,
  X,
  AlertTriangle,
  Bookmark,
  ShieldCheck,
  FolderGit2
} from 'lucide-react';
import { MemoryItem } from '../types';

interface MemoryCenterProps {
  memories: MemoryItem[];
  onAddMemory: (data: Partial<MemoryItem>) => Promise<void>;
  onUpdateMemory: (id: string, data: Partial<MemoryItem>) => Promise<void>;
  onDeleteMemory: (id: string) => Promise<void>;
  onClearAll: () => Promise<void>;
}

export const MemoryCenter: React.FC<MemoryCenterProps> = ({
  memories,
  onAddMemory,
  onUpdateMemory,
  onDeleteMemory,
  onClearAll
}) => {
  const [activeTab, setActiveTab] = useState<string>('all');
  const [searchQuery, setSearchQuery] = useState('');
  const [isAdding, setIsAdding] = useState(false);
  const [showWipeConfirm, setShowWipeConfirm] = useState(false);

  // Form states
  const [newKey, setNewKey] = useState('');
  const [newCategory, setNewCategory] = useState<'preference' | 'project' | 'fact' | 'general'>('preference');
  const [newContent, setNewContent] = useState('');

  // Editing state
  const [editingId, setEditingId] = useState<string | null>(null);
  const [editContent, setEditContent] = useState('');

  const handleCreate = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!newKey.trim() || !newContent.trim()) return;
    await onAddMemory({
      key: newKey.trim(),
      category: newCategory,
      content: newContent.trim(),
      approved: true
    });
    setNewKey('');
    setNewContent('');
    setIsAdding(false);
  };

  const handleStartEdit = (item: MemoryItem) => {
    setEditingId(item.id);
    setEditContent(item.content);
  };

  const handleSaveEdit = async (id: string) => {
    await onUpdateMemory(id, { content: editContent });
    setEditingId(null);
  };

  const filtered = memories.filter((m) => {
    const matchesTab = activeTab === 'all' || m.category === activeTab;
    const matchesSearch =
      m.key.toLowerCase().includes(searchQuery.toLowerCase()) ||
      m.content.toLowerCase().includes(searchQuery.toLowerCase());
    return matchesTab && matchesSearch;
  });

  const getCategoryIcon = (category: string) => {
    switch (category) {
      case 'preference':
        return <Bookmark className="w-4 h-4 text-cyan-400" />;
      case 'project':
        return <FolderGit2 className="w-4 h-4 text-blue-400" />;
      case 'fact':
        return <ShieldCheck className="w-4 h-4 text-emerald-400" />;
      default:
        return <Database className="w-4 h-4 text-slate-400" />;
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-4 flex flex-col gap-6">
      {/* Top Banner */}
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 pb-3 border-b border-cyan-500/20 font-mono">
        <div>
          <h2 className="text-base font-bold text-cyan-300 tracking-wider flex items-center gap-2">
            <Database className="w-5 h-5 text-cyan-400" /> PERSISTENT MEMORY VAULT
          </h2>
          <p className="text-slate-400 text-xs">
            Explicitly curated user preferences, architectural context, and verified facts.
          </p>
        </div>

        <div className="flex items-center gap-2">
          <button
            onClick={() => setIsAdding(true)}
            className="px-3.5 py-1.5 rounded-xl bg-cyan-500/20 border border-cyan-400/40 text-cyan-300 hover:bg-cyan-500/30 text-xs font-mono flex items-center gap-1.5 transition"
          >
            <Plus className="w-3.5 h-3.5" />
            <span>RECORD MEMORY</span>
          </button>
          <button
            onClick={() => setShowWipeConfirm(true)}
            className="px-3.5 py-1.5 rounded-xl bg-red-950/40 border border-red-500/30 text-red-300 hover:bg-red-900/40 text-xs font-mono flex items-center gap-1.5 transition"
          >
            <Trash2 className="w-3.5 h-3.5" />
            <span>PURGE VAULT</span>
          </button>
        </div>
      </div>

      {/* Confirmation Modal for Memory Wipe */}
      {showWipeConfirm && (
        <div className="jarvis-panel border border-red-500/40 bg-red-950/20 p-4 rounded-xl flex items-center justify-between font-mono text-xs">
          <div className="flex items-center gap-2 text-red-300">
            <AlertTriangle className="w-4 h-4" />
            <span>PURGE CONFIRMATION: Erase all persistent memories? This cannot be undone.</span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={() => {
                onClearAll();
                setShowWipeConfirm(false);
              }}
              className="px-3 py-1 rounded bg-red-600 text-white font-bold hover:bg-red-500 transition"
            >
              CONFIRM WIPE
            </button>
            <button
              onClick={() => setShowWipeConfirm(false)}
              className="px-3 py-1 rounded bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
            >
              CANCEL
            </button>
          </div>
        </div>
      )}

      {/* Add Memory Modal / Box */}
      {isAdding && (
        <form onSubmit={handleCreate} className="jarvis-panel rounded-2xl p-5 border border-cyan-400/40 space-y-4 tech-corner">
          <div className="flex items-center justify-between font-mono text-xs text-cyan-400 font-bold">
            <span>STORE EXPLICIT MEMORY RECORD</span>
            <button type="button" onClick={() => setIsAdding(false)} className="text-slate-500 hover:text-slate-300">
              <X className="w-4 h-4" />
            </button>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-3 font-mono text-xs">
            <div>
              <label className="text-slate-400 mb-1 block">Key / Subject:</label>
              <input
                type="text"
                placeholder="e.g. primary_programming_language"
                value={newKey}
                onChange={(e) => setNewKey(e.target.value)}
                className="w-full bg-slate-900 border border-cyan-500/30 rounded-xl p-2.5 text-cyan-200 focus:outline-none focus:border-cyan-400"
                required
              />
            </div>
            <div>
              <label className="text-slate-400 mb-1 block">Classification:</label>
              <select
                value={newCategory}
                onChange={(e: any) => setNewCategory(e.target.value)}
                className="w-full bg-slate-900 border border-cyan-500/30 rounded-xl p-2.5 text-cyan-200 focus:outline-none focus:border-cyan-400"
              >
                <option value="preference">User Preference</option>
                <option value="project">Project Context</option>
                <option value="fact">Approved Fact</option>
                <option value="general">General</option>
              </select>
            </div>
          </div>

          <div className="font-mono text-xs">
            <label className="text-slate-400 mb-1 block">Memory Content:</label>
            <textarea
              rows={3}
              placeholder="Detailed fact or persistent preference to retain..."
              value={newContent}
              onChange={(e) => setNewContent(e.target.value)}
              className="w-full bg-slate-900 border border-cyan-500/30 rounded-xl p-2.5 text-cyan-200 focus:outline-none focus:border-cyan-400"
              required
            />
          </div>

          <div className="flex justify-end gap-2 font-mono text-xs">
            <button
              type="button"
              onClick={() => setIsAdding(false)}
              className="px-4 py-2 rounded-xl bg-slate-800 text-slate-300 hover:bg-slate-700 transition"
            >
              Cancel
            </button>
            <button
              type="submit"
              className="px-5 py-2 rounded-xl bg-cyan-500 text-slate-950 font-bold hover:bg-cyan-400 transition shadow-[0_0_15px_rgba(0,240,255,0.4)]"
            >
              Commit to Vault
            </button>
          </div>
        </form>
      )}

      {/* Tabs & Search Filter */}
      <div className="flex flex-col sm:flex-row items-center justify-between gap-3 font-mono text-xs">
        <div className="flex items-center gap-1 bg-slate-900/60 p-1 rounded-xl border border-cyan-500/20">
          {['all', 'preference', 'project', 'fact', 'general'].map((tab) => (
            <button
              key={tab}
              onClick={() => setActiveTab(tab)}
              className={`px-3 py-1.5 rounded-lg capitalize transition ${
                activeTab === tab
                  ? 'bg-cyan-500/20 text-cyan-300 border border-cyan-400/40 font-semibold'
                  : 'text-slate-400 hover:text-cyan-200'
              }`}
            >
              {tab === 'all' ? 'All Records' : tab}
            </button>
          ))}
        </div>

        <div className="relative w-full sm:w-64">
          <Search className="w-3.5 h-3.5 absolute left-3 top-2.5 text-slate-500" />
          <input
            type="text"
            placeholder="Search memory entries..."
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            className="w-full bg-slate-900/80 border border-cyan-500/20 rounded-xl pl-9 pr-3 py-1.5 text-xs text-cyan-200 placeholder-slate-500 focus:outline-none focus:border-cyan-400"
          />
        </div>
      </div>

      {/* Memory Cards Grid */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {filtered.length === 0 ? (
          <div className="col-span-full jarvis-panel rounded-2xl p-12 text-center text-xs font-mono text-slate-500">
            No memories match current filters.
          </div>
        ) : (
          filtered.map((item) => {
            const isEditing = editingId === item.id;
            return (
              <div
                key={item.id}
                className="jarvis-panel rounded-2xl p-4 flex flex-col justify-between gap-3 border border-cyan-500/20 hover:border-cyan-500/40 transition font-mono tech-corner"
              >
                <div>
                  <div className="flex items-center justify-between pb-2 border-b border-cyan-500/10">
                    <div className="flex items-center gap-2">
                      {getCategoryIcon(item.category)}
                      <span className="text-xs font-bold text-cyan-200 truncate max-w-[160px]">{item.key}</span>
                    </div>
                    <span className="text-[10px] px-2 py-0.5 rounded bg-slate-900 border border-cyan-500/20 text-cyan-400 capitalize">
                      {item.category}
                    </span>
                  </div>

                  {isEditing ? (
                    <div className="mt-2 space-y-2">
                      <textarea
                        rows={3}
                        value={editContent}
                        onChange={(e) => setEditContent(e.target.value)}
                        className="w-full bg-slate-950 border border-cyan-400 rounded-lg p-2 text-xs text-cyan-100 focus:outline-none"
                      />
                      <div className="flex justify-end gap-1">
                        <button
                          onClick={() => handleSaveEdit(item.id)}
                          className="p-1 rounded bg-emerald-500/20 text-emerald-400 hover:bg-emerald-500/30"
                          title="Save"
                        >
                          <Check className="w-3.5 h-3.5" />
                        </button>
                        <button
                          onClick={() => setEditingId(null)}
                          className="p-1 rounded bg-slate-800 text-slate-400 hover:bg-slate-700"
                          title="Cancel"
                        >
                          <X className="w-3.5 h-3.5" />
                        </button>
                      </div>
                    </div>
                  ) : (
                    <p className="mt-2 text-xs text-slate-300 font-sans leading-relaxed select-text">
                      {item.content}
                    </p>
                  )}
                </div>

                <div className="flex items-center justify-between pt-2 border-t border-cyan-500/10 text-[10px] text-slate-500">
                  <span>
                    Stored:{' '}
                    {new Date(item.created_at).toLocaleDateString([], {
                      month: 'short',
                      day: 'numeric'
                    })}
                  </span>
                  <div className="flex items-center gap-1.5">
                    <button
                      onClick={() => handleStartEdit(item)}
                      className="p-1 text-slate-400 hover:text-cyan-300 transition"
                      title="Edit memory"
                    >
                      <Edit2 className="w-3.5 h-3.5" />
                    </button>
                    <button
                      onClick={() => onDeleteMemory(item.id)}
                      className="p-1 text-slate-400 hover:text-red-400 transition"
                      title="Delete memory"
                    >
                      <Trash2 className="w-3.5 h-3.5" />
                    </button>
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
};
