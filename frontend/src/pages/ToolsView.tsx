import React, { useState } from 'react';
import {
  Wrench,
  Search,
  Calculator,
  Cpu,
  Clock,
  FolderSearch,
  FileText,
  FilePlus,
  Monitor,
  Globe,
  Play,
  CheckCircle2,
  AlertTriangle,
  Code
} from 'lucide-react';
import { ToolDefinition } from '../types';

interface ToolsViewProps {
  tools: ToolDefinition[];
  onExecuteTool: (name: string, args: Record<string, any>) => Promise<any>;
}

export const ToolsView: React.FC<ToolsViewProps> = ({ tools, onExecuteTool }) => {
  const [selectedTool, setSelectedTool] = useState<ToolDefinition | null>(tools[0] || null);
  const [paramInput, setParamInput] = useState<string>('{}');
  const [executionResult, setExecutionResult] = useState<any>(null);
  const [executing, setExecuting] = useState(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  const getToolIcon = (name: string) => {
    switch (name) {
      case 'calculate':
        return <Calculator className="w-5 h-5 text-cyan-400" />;
      case 'get_system_status':
        return <Cpu className="w-5 h-5 text-cyan-400" />;
      case 'get_current_time':
        return <Clock className="w-5 h-5 text-cyan-400" />;
      case 'search_web':
        return <Search className="w-5 h-5 text-cyan-400" />;
      case 'search_allowed_files':
        return <FolderSearch className="w-5 h-5 text-cyan-400" />;
      case 'read_selected_file':
        return <FileText className="w-5 h-5 text-cyan-400" />;
      case 'create_note':
        return <FilePlus className="w-5 h-5 text-cyan-400" />;
      case 'open_approved_app':
        return <Monitor className="w-5 h-5 text-cyan-400" />;
      case 'open_website':
        return <Globe className="w-5 h-5 text-cyan-400" />;
      default:
        return <Wrench className="w-5 h-5 text-cyan-400" />;
    }
  };

  const handleSelectTool = (tool: ToolDefinition) => {
    setSelectedTool(tool);
    setExecutionResult(null);
    setErrorMsg(null);

    // Populate sample arguments
    if (tool.name === 'calculate') {
      setParamInput(JSON.stringify({ expression: '256 * 16 + sqrt(144)' }, null, 2));
    } else if (tool.name === 'search_web') {
      setParamInput(JSON.stringify({ query: 'latest artificial intelligence innovations' }, null, 2));
    } else if (tool.name === 'open_approved_app') {
      setParamInput(JSON.stringify({ app_id: 'notepad' }, null, 2));
    } else if (tool.name === 'open_website') {
      setParamInput(JSON.stringify({ url: 'https://github.com' }, null, 2));
    } else if (tool.name === 'create_note') {
      setParamInput(JSON.stringify({ title: 'System Notes', content: 'Subsystems verified nominal.' }, null, 2));
    } else if (tool.name === 'search_allowed_files') {
      setParamInput(JSON.stringify({ query: 'py' }, null, 2));
    } else {
      setParamInput('{}');
    }
  };

  const handleRun = async () => {
    if (!selectedTool) return;
    setExecuting(true);
    setErrorMsg(null);
    try {
      const parsedArgs = JSON.parse(paramInput || '{}');
      const res = await onExecuteTool(selectedTool.name, parsedArgs);
      setExecutionResult(res);
    } catch (err: any) {
      setErrorMsg(err.message || 'Execution error');
    } finally {
      setExecuting(false);
    }
  };

  return (
    <div className="w-full max-w-7xl mx-auto p-4 flex flex-col gap-6">
      {/* Header */}
      <div className="flex items-center justify-between pb-3 border-b border-cyan-500/20 font-mono">
        <div>
          <h2 className="text-base font-bold text-cyan-300 tracking-wider flex items-center gap-2">
            <Wrench className="w-5 h-5 text-cyan-400" /> CAPABILITIES & TOOL REGISTRY
          </h2>
          <p className="text-slate-400 text-xs">
            Directly test and inspect authenticated system tool integrations.
          </p>
        </div>
        <div className="text-xs text-cyan-400">
          REGISTERED: <span className="font-bold text-cyan-200">{tools.length}</span>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6">
        {/* Tools Catalog (5 cols) */}
        <div className="lg:col-span-5 space-y-3">
          {tools.map((tool) => {
            const isSelected = selectedTool?.name === tool.name;
            return (
              <div
                key={tool.name}
                onClick={() => handleSelectTool(tool)}
                className={`p-4 rounded-xl border cursor-pointer font-mono transition-all jarvis-panel-interactive ${
                  isSelected
                    ? 'border-cyan-400 bg-cyan-950/40 shadow-[0_0_15px_rgba(0,240,255,0.2)]'
                    : 'border-cyan-500/20 bg-slate-900/60 hover:border-cyan-500/40'
                }`}
              >
                <div className="flex items-start gap-3">
                  <div className="p-2.5 rounded-lg bg-slate-900 border border-cyan-500/30">
                    {getToolIcon(tool.name)}
                  </div>
                  <div className="flex-1">
                    <div className="flex items-center justify-between">
                      <span className="text-sm font-bold text-cyan-200">{tool.name}</span>
                      <span className="text-[10px] px-2 py-0.5 rounded border border-emerald-500/30 text-emerald-400 bg-emerald-950/30 flex items-center gap-1">
                        <CheckCircle2 className="w-2.5 h-2.5" /> ACTIVE
                      </span>
                    </div>
                    <p className="text-slate-400 text-xs mt-1 line-clamp-2">{tool.description}</p>
                    <div className="flex items-center gap-2 mt-2 text-[10px]">
                      <span className="px-1.5 py-0.5 rounded bg-slate-800 text-cyan-400 border border-cyan-500/20">
                        {tool.category.toUpperCase()}
                      </span>
                      {tool.requires_approval && (
                        <span className="px-1.5 py-0.5 rounded bg-amber-950/40 text-amber-300 border border-amber-500/30 flex items-center gap-1">
                          <AlertTriangle className="w-2.5 h-2.5" /> REQUIRES APPROVAL
                        </span>
                      )}
                    </div>
                  </div>
                </div>
              </div>
            );
          })}
        </div>

        {/* Selected Tool Inspector & Execution Sandbox (7 cols) */}
        <div className="lg:col-span-7">
          {selectedTool ? (
            <div className="jarvis-panel rounded-2xl p-6 flex flex-col gap-5 tech-corner">
              {/* Tool Header */}
              <div className="flex items-center justify-between border-b border-cyan-500/20 pb-4">
                <div className="flex items-center gap-3">
                  <div className="p-3 rounded-xl bg-cyan-950/50 border border-cyan-400/40">
                    {getToolIcon(selectedTool.name)}
                  </div>
                  <div>
                    <h3 className="text-base font-mono font-bold text-cyan-300">{selectedTool.name}</h3>
                    <p className="text-xs text-slate-400 font-mono">{selectedTool.description}</p>
                  </div>
                </div>
              </div>

              {/* JSON Parameter Editor */}
              <div className="space-y-2">
                <div className="flex items-center justify-between text-xs font-mono text-cyan-400">
                  <span className="flex items-center gap-1.5">
                    <Code className="w-3.5 h-3.5" /> ARGUMENT PAYLOAD (JSON)
                  </span>
                  <span className="text-slate-500 text-[10px]">EDITABLE</span>
                </div>
                <textarea
                  rows={4}
                  value={paramInput}
                  onChange={(e) => setParamInput(e.target.value)}
                  className="w-full bg-slate-950/80 border border-cyan-500/30 rounded-xl p-3 font-mono text-xs text-cyan-200 focus:outline-none focus:border-cyan-400"
                />
              </div>

              {/* Run Trigger */}
              <button
                onClick={handleRun}
                disabled={executing}
                className="px-6 py-2.5 rounded-xl bg-cyan-500/20 border border-cyan-400/50 text-cyan-300 hover:bg-cyan-500/30 font-mono text-xs flex items-center justify-center gap-2 transition disabled:opacity-40 shadow-[0_0_15px_rgba(0,240,255,0.15)]"
              >
                <Play className="w-4 h-4 text-cyan-400" />
                <span className="font-bold">{executing ? 'EXECUTING DIRECTIVE...' : 'DISPATCH TOOL EXECUTION'}</span>
              </button>

              {/* Error Output */}
              {errorMsg && (
                <div className="p-3 rounded-xl bg-red-950/40 border border-red-500/40 text-red-300 font-mono text-xs">
                  {errorMsg}
                </div>
              )}

              {/* Execution Result Output */}
              {executionResult && (
                <div className="space-y-2 pt-2 border-t border-cyan-500/20">
                  <div className="text-xs font-mono text-cyan-400 font-semibold tracking-wider">
                    TELEMETRY RESPONSE:
                  </div>
                  <pre className="bg-slate-950/90 border border-cyan-500/20 rounded-xl p-4 text-xs font-mono text-emerald-300 overflow-x-auto max-h-72">
                    {JSON.stringify(executionResult, null, 2)}
                  </pre>
                </div>
              )}
            </div>
          ) : (
            <div className="jarvis-panel rounded-2xl p-12 text-center text-xs font-mono text-slate-500">
              Select a capability from the registry to inspect parameters.
            </div>
          )}
        </div>
      </div>
    </div>
  );
};
