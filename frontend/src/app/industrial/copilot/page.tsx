'use client';
import { useState, useRef, useEffect } from 'react';
import { useSureflowStore } from '@/lib/store';
import { useAuth } from '@/lib/AuthContext';
import { CopilotChat } from '@/components/industrial/CopilotChat';
import { Send, Sparkles, Trash2, MessageSquare } from 'lucide-react';

const SUGGESTED_PROMPTS = [
  'Show maintenance history for pump P-101',
  'What are the compliance gaps in Area A?',
  'Explain the root cause of the bearing failure',
  'Which equipment has the highest failure rate?',
  'Summarize all open work orders',
  'What lessons have we learned from recent incidents?',
];

export default function CopilotPage() {
  const { copilotMessages, copilotLoading, copilotStage, sendCopilotMessage, clearCopilotMessages } = useSureflowStore();
  const { targetPlantId } = useAuth();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLInputElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [copilotMessages, copilotLoading]);

  // Clear context when switching plants so the Copilot doesn't mix state.
  useEffect(() => {
    clearCopilotMessages();
  }, [targetPlantId, clearCopilotMessages]);

  const handleSend = () => {
    if (!input.trim() || copilotLoading) return;
    sendCopilotMessage(input.trim());
    setInput('');
  };

  const handlePromptClick = (prompt: string) => {
    if (copilotLoading) return;
    sendCopilotMessage(prompt);
  };

  return (
    <div className="flex flex-col h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* Header */}
      <div className="flex items-center justify-between px-8 py-5 border-b" style={{ borderColor: 'var(--border)' }}>
        <div className="flex items-center gap-3">
          <div
            className="w-10 h-10 rounded-xl flex items-center justify-center"
            style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.2), rgba(6,182,212,0.1))' }}
          >
            <MessageSquare size={20} style={{ color: '#818cf8' }} />
          </div>
          <div>
            <h1 className="text-xl font-bold" style={{ color: 'var(--text-primary)' }}>
              Industrial <span className="gradient-text">Copilot</span>
            </h1>
            <p className="text-xs" style={{ color: 'var(--text-muted)' }}>
              AI-powered search across documents, knowledge graph, and operational data
            </p>
          </div>
        </div>
        {copilotMessages.length > 0 && (
          <button
            onClick={clearCopilotMessages}
            className="btn-ghost text-xs"
          >
            <Trash2 size={14} />
            Clear
          </button>
        )}
      </div>

      {/* Messages Area */}
      <div className="flex-1 overflow-y-auto px-8 py-6">
        {copilotMessages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div
              className="w-16 h-16 rounded-2xl flex items-center justify-center mb-6"
              style={{ background: 'linear-gradient(135deg, rgba(99,102,241,0.15), rgba(6,182,212,0.1))' }}
            >
              <Sparkles size={28} style={{ color: '#818cf8' }} />
            </div>
            <h2 className="text-xl font-semibold mb-2" style={{ color: 'var(--text-primary)' }}>
              How can I help?
            </h2>
            <p className="text-sm mb-8 text-center max-w-md" style={{ color: 'var(--text-muted)' }}>
              Ask me anything about your plant, equipment, maintenance history, compliance status, or operational data.
            </p>
            <div className="flex flex-wrap gap-2 max-w-2xl justify-center">
              {SUGGESTED_PROMPTS.map((prompt) => (
                <button
                  key={prompt}
                  className="suggested-prompt"
                  onClick={() => handlePromptClick(prompt)}
                >
                  <Sparkles size={10} />
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <>
            <CopilotChat
              messages={copilotMessages}
              loading={copilotLoading}
              stage={copilotStage}
              onFollowUpClick={handlePromptClick}
            />
            <div ref={messagesEndRef} />
          </>
        )}
      </div>

      {/* Input Area */}
      <div className="px-8 py-5 border-t" style={{ borderColor: 'var(--border)' }}>
        <div className="flex gap-3 max-w-4xl mx-auto">
          <input
            ref={inputRef}
            id="copilot-input"
            type="text"
            value={input}
            onChange={e => setInput(e.target.value)}
            placeholder="Ask about equipment, maintenance, compliance, incidents..."
            className="flex-1 px-5 py-3 rounded-xl text-sm outline-none transition-all"
            style={{
              background: 'rgba(255,255,255,0.04)',
              border: '1px solid var(--border)',
              color: 'var(--text-primary)',
            }}
            onKeyDown={e => { if (e.key === 'Enter') handleSend(); }}
            disabled={copilotLoading}
          />
          <button
            id="copilot-send-btn"
            className="btn-primary"
            onClick={handleSend}
            disabled={copilotLoading || !input.trim()}
          >
            <Send size={16} />
          </button>
        </div>
      </div>
    </div>
  );
}
