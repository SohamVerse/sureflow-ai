'use client';
import { useState, useRef, useCallback } from 'react';
import { industrialApi } from '@/lib/api';
import type { DocumentUploadResult } from '@/types';
import {
  Upload, FileText, CheckCircle, Loader2,
  ChevronDown, Network, Database, BookOpen,
  AlertTriangle, X,
} from 'lucide-react';

const DOC_TYPES = [
  { value: 'oem_manual', label: 'OEM Manual' },
  { value: 'sop', label: 'Standard Operating Procedure' },
  { value: 'safety_report', label: 'Safety Report' },
  { value: 'inspection_report', label: 'Inspection Report' },
  { value: 'maintenance_log', label: 'Maintenance Log' },
  { value: 'incident_report', label: 'Incident Report' },
  { value: 'unknown', label: 'Auto-detect' },
];

type UploadStep = 'idle' | 'uploading' | 'extracting' | 'analyzing' | 'embedding' | 'graphing' | 'done' | 'error';

const PIPELINE_STEPS = [
  { key: 'extracting', label: 'Extracting text', icon: FileText },
  { key: 'analyzing', label: 'AI Document Analysis', icon: BookOpen },
  { key: 'embedding', label: 'Embedding into Vector Store', icon: Database },
  { key: 'graphing', label: 'Updating Knowledge Graph', icon: Network },
];

export default function DocumentUploadPage() {
  const [file, setFile] = useState<File | null>(null);
  const [docType, setDocType] = useState('unknown');
  const [step, setStep] = useState<UploadStep>('idle');
  const [result, setResult] = useState<DocumentUploadResult | null>(null);
  const [error, setError] = useState('');
  const [dragging, setDragging] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleDrop = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(false);
    const droppedFile = e.dataTransfer.files[0];
    if (droppedFile) setFile(droppedFile);
  }, []);

  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
    setDragging(true);
  }, []);

  const handleDragLeave = useCallback(() => {
    setDragging(false);
  }, []);

  const handleFileSelect = (e: React.ChangeEvent<HTMLInputElement>) => {
    const selected = e.target.files?.[0];
    if (selected) setFile(selected);
  };

  const handleUpload = async () => {
    if (!file) return;
    setError('');
    setResult(null);
    setStep('uploading');

    try {
      // Real backend-driven progress (Phase 5 SSE) — each step below fires
      // only once that pipeline stage has actually completed server-side.
      const res = await industrialApi.uploadDocumentStream(file, docType, event => {
        if (event.event === 'stage') setStep(event.stage as UploadStep);
      });
      setResult(res);
      setStep('done');
    } catch (e: unknown) {
      const msg = e instanceof Error ? e.message : 'Upload failed';
      setError(msg);
      setStep('error');
    }
  };

  const reset = () => {
    setFile(null);
    setStep('idle');
    setResult(null);
    setError('');
  };

  const getStepStatus = (stepKey: string): 'done' | 'active' | 'pending' => {
    const stepOrder = ['extracting', 'analyzing', 'embedding', 'graphing'];
    const currentIdx = stepOrder.indexOf(step);
    const thisIdx = stepOrder.indexOf(stepKey);

    if (step === 'done') return 'done';
    if (step === 'error') return thisIdx <= stepOrder.indexOf('extracting') ? 'done' : 'pending';
    if (thisIdx < currentIdx) return 'done';
    if (thisIdx === currentIdx) return 'active';
    return 'pending';
  };

  const formatSize = (bytes: number) => {
    if (bytes < 1024) return `${bytes} B`;
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`;
    return `${(bytes / (1024 * 1024)).toFixed(1)} MB`;
  };

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      {/* Header */}
      <div className="mb-8 animate-fade-in-up">
        <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          <Upload size={28} className="inline mr-2" style={{ color: '#a855f7' }} />
          Document<span className="gradient-text"> Upload</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>
          Upload industrial documents for AI-powered extraction, embedding, and knowledge graph integration.
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
        {/* Left: Upload Area */}
        <div className="animate-fade-in-up" style={{ animationDelay: '0.1s' }}>
          {/* Dropzone */}
          <div
            className={`upload-dropzone mb-6 ${dragging ? 'dragging' : ''}`}
            onDrop={handleDrop}
            onDragOver={handleDragOver}
            onDragLeave={handleDragLeave}
            onClick={() => fileInputRef.current?.click()}
          >
            <input
              ref={fileInputRef}
              type="file"
              className="hidden"
              accept=".pdf,.txt,.doc,.docx,.md,.csv"
              onChange={handleFileSelect}
            />
            <Upload size={40} className="mx-auto mb-4" style={{ color: 'var(--text-muted)', opacity: 0.4 }} />
            <p className="text-sm font-medium" style={{ color: 'var(--text-secondary)' }}>
              {dragging ? 'Drop file here...' : 'Drag & drop or click to upload'}
            </p>
            <p className="text-xs mt-2" style={{ color: 'var(--text-muted)' }}>
              Supports PDF, TXT, DOC, DOCX, MD, CSV
            </p>
          </div>

          {/* Selected File */}
          {file && (
            <div
              className="industrial-card p-4 mb-4 flex items-center justify-between"
            >
              <div className="flex items-center gap-3">
                <FileText size={20} style={{ color: '#a855f7' }} />
                <div>
                  <div className="text-sm font-medium" style={{ color: 'var(--text-primary)' }}>{file.name}</div>
                  <div className="text-xs" style={{ color: 'var(--text-muted)' }}>{formatSize(file.size)}</div>
                </div>
              </div>
              <button onClick={() => setFile(null)} className="p-1 rounded-lg hover:bg-white/5">
                <X size={16} style={{ color: 'var(--text-muted)' }} />
              </button>
            </div>
          )}

          {/* Doc Type Selector */}
          <div className="mb-6">
            <label className="text-xs font-semibold mb-2 block" style={{ color: 'var(--text-muted)' }}>Document Type</label>
            <div className="relative">
              <select
                id="doc-type-select"
                value={docType}
                onChange={e => setDocType(e.target.value)}
                className="w-full px-4 py-3 rounded-xl text-sm outline-none appearance-none cursor-pointer"
                style={{
                  background: 'rgba(255,255,255,0.04)',
                  border: '1px solid var(--border)',
                  color: 'var(--text-primary)',
                }}
              >
                {DOC_TYPES.map(dt => (
                  <option key={dt.value} value={dt.value}>{dt.label}</option>
                ))}
              </select>
              <ChevronDown size={14} className="absolute right-3 top-1/2 -translate-y-1/2 pointer-events-none" style={{ color: 'var(--text-muted)' }} />
            </div>
          </div>

          {/* Upload Button */}
          <button
            id="upload-doc-btn"
            className="btn-primary w-full justify-center"
            onClick={handleUpload}
            disabled={!file || step === 'uploading' || step === 'extracting' || step === 'analyzing' || step === 'embedding' || step === 'graphing'}
            style={{ padding: '14px' }}
          >
            {step !== 'idle' && step !== 'done' && step !== 'error' ? (
              <><Loader2 size={16} className="animate-spin" /> Processing...</>
            ) : (
              <><Upload size={16} /> Upload & Process</>
            )}
          </button>

          {step === 'done' && (
            <button onClick={reset} className="btn-ghost w-full justify-center mt-3">
              Upload Another
            </button>
          )}
        </div>

        {/* Right: Pipeline Progress + Results */}
        <div className="animate-fade-in-up" style={{ animationDelay: '0.15s' }}>
          {/* Pipeline Steps */}
          <div className="industrial-card p-6 mb-6">
            <h3 className="font-semibold text-sm mb-4" style={{ color: 'var(--text-primary)' }}>
              Ingestion Pipeline
            </h3>
            <div className="space-y-2">
              {PIPELINE_STEPS.map(({ key, label, icon: Icon }) => {
                const status = step === 'idle' ? 'pending' : getStepStatus(key);
                return (
                  <div key={key} className={`upload-step ${status}`}>
                    {status === 'done' ? (
                      <CheckCircle size={16} style={{ color: '#22c55e' }} />
                    ) : status === 'active' ? (
                      <Loader2 size={16} className="animate-spin" style={{ color: '#6366f1' }} />
                    ) : (
                      <Icon size={16} style={{ color: 'var(--text-muted)' }} />
                    )}
                    <span>{label}</span>
                  </div>
                );
              })}
            </div>
          </div>

          {/* Error */}
          {error && (
            <div className="p-4 rounded-xl mb-6" style={{ background: 'rgba(239,68,68,0.08)', border: '1px solid rgba(239,68,68,0.2)' }}>
              <div className="text-sm flex items-center gap-2" style={{ color: '#ef4444' }}>
                <AlertTriangle size={16} />
                {error}
              </div>
            </div>
          )}

          {/* Results */}
          {result && (
            <div className="industrial-card p-6 animate-fade-in-up">
              <h3 className="font-semibold text-sm mb-4 flex items-center gap-2" style={{ color: '#22c55e' }}>
                <CheckCircle size={16} />
                Processing Complete
              </h3>

              <div className="grid grid-cols-2 gap-3 mb-4">
                {[
                  { label: 'Pages Extracted', value: result.pages_extracted, color: '#3b82f6' },
                  { label: 'Entities Found', value: result.entities_found, color: '#a855f7' },
                  { label: 'Chunks Embedded', value: result.chunks_embedded, color: '#06b6d4' },
                  { label: 'Graph Nodes', value: result.graph_nodes_created, color: '#22c55e' },
                ].map(({ label, value, color }) => (
                  <div key={label} className="p-3 rounded-xl" style={{ background: 'rgba(255,255,255,0.02)', border: '1px solid var(--border)' }}>
                    <div className="text-xl font-bold" style={{ color }}>{value}</div>
                    <div className="text-[10px]" style={{ color: 'var(--text-muted)' }}>{label}</div>
                  </div>
                ))}
              </div>

              <div className="space-y-3">
                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  <span className="font-semibold">Document Type:</span> {result.doc_type}
                </div>
                <div className="text-xs" style={{ color: 'var(--text-muted)' }}>
                  <span className="font-semibold">Collection:</span> {result.collection}
                </div>
                {result.summary && (
                  <div>
                    <div className="text-xs font-semibold mb-1" style={{ color: 'var(--text-muted)' }}>AI Summary:</div>
                    <p className="text-sm" style={{ color: 'var(--text-secondary)', lineHeight: '1.6' }}>
                      {result.summary}
                    </p>
                  </div>
                )}
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
