'use client';
import type { CopilotMessage } from '@/types';
import { Bot, User, BookOpen } from 'lucide-react';
import { AgentReasoningPanel } from './AgentReasoningPanel';

interface CopilotChatProps {
  messages: CopilotMessage[];
  loading: boolean;
  stage?: string | null;
  onFollowUpClick?: (question: string) => void;
}

/** Lightweight markdown→HTML for copilot responses. */
function renderMarkdown(text: string): string {
  let html = text
    // Code blocks
    .replace(/```(\w*)\n([\s\S]*?)```/g, '<pre><code>$2</code></pre>')
    // Inline code
    .replace(/`([^`]+)`/g, '<code>$1</code>')
    // Bold
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    // Italic
    .replace(/\*(.*?)\*/g, '<em>$1</em>')
    // Headers
    .replace(/^### (.*$)/gm, '<h3>$1</h3>')
    .replace(/^## (.*$)/gm, '<h2>$1</h2>')
    .replace(/^# (.*$)/gm, '<h1>$1</h1>')
    // Unordered lists
    .replace(/^[-*] (.*$)/gm, '<li>$1</li>')
    // Ordered lists
    .replace(/^\d+\. (.*$)/gm, '<li>$1</li>')
    // Blockquotes
    .replace(/^> (.*$)/gm, '<blockquote>$1</blockquote>')
    // Paragraphs (double newline)
    .replace(/\n\n/g, '</p><p>')
    // Single newlines → br
    .replace(/\n/g, '<br/>');

  // Wrap in paragraph if not already wrapped
  if (!html.startsWith('<')) {
    html = `<p>${html}</p>`;
  }

  return html;
}

export function CopilotChat({ messages, loading, stage, onFollowUpClick }: CopilotChatProps) {
  return (
    <div className="flex flex-col gap-4">
      {messages.map((msg) => (
        <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : 'justify-start'}`}>
          {msg.role === 'assistant' && (
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-1"
              style={{ background: 'rgba(99,102,241,0.15)' }}
            >
              <Bot size={16} style={{ color: '#818cf8' }} />
            </div>
          )}

          <div className={msg.role === 'user' ? 'copilot-msg-user' : 'copilot-msg-ai'}>
            {msg.role === 'user' ? (
              <div className="text-sm" style={{ color: 'var(--text-primary)' }}>{msg.content}</div>
            ) : (
              <div
                className="text-sm copilot-markdown"
                style={{ color: 'var(--text-secondary)' }}
                dangerouslySetInnerHTML={{ __html: renderMarkdown(msg.content) }}
              />
            )}

            {/* Citations */}
            {msg.citations && msg.citations.length > 0 && (
              <div className="flex flex-wrap gap-2 mt-3">
                {msg.citations.map((citation, i) => (
                  <span key={i} className="citation-card">
                    <BookOpen size={10} />
                    {citation.source}
                    {citation.collection && (
                      <span style={{ opacity: 0.6 }}>({citation.collection})</span>
                    )}
                  </span>
                ))}
              </div>
            )}

            {msg.role === 'assistant' && (
              <AgentReasoningPanel
                data={msg}
                sourcesConsulted={msg.sources_consulted}
                safetyAlerts={msg.safety_alerts}
                followUpQuestions={msg.follow_up_questions}
                onFollowUpClick={onFollowUpClick}
              />
            )}

            <div className="text-[9px] mt-2 font-mono" style={{ color: 'var(--text-muted)' }}>
              {new Date(msg.timestamp).toLocaleTimeString()}
            </div>
          </div>

          {msg.role === 'user' && (
            <div
              className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-1"
              style={{ background: 'rgba(6,182,212,0.15)' }}
            >
              <User size={16} style={{ color: '#06b6d4' }} />
            </div>
          )}
        </div>
      ))}

      {/* Loading indicator */}
      {loading && (
        <div className="flex gap-3 justify-start">
          <div
            className="w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 mt-1"
            style={{ background: 'rgba(99,102,241,0.15)' }}
          >
            <Bot size={16} style={{ color: '#818cf8' }} />
          </div>
          <div className="copilot-msg-ai flex items-center gap-3" style={{ padding: '16px 24px' }}>
            <div className="flex gap-1.5">
              <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '0ms' }} />
              <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '150ms' }} />
              <div className="w-2 h-2 rounded-full bg-indigo-400 animate-bounce" style={{ animationDelay: '300ms' }} />
            </div>
            {stage && (
              <span className="text-xs" style={{ color: 'var(--text-muted)' }}>{stage}</span>
            )}
          </div>
        </div>
      )}
    </div>
  );
}
