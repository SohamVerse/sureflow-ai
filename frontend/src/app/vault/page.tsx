'use client';
import { useEffect, useRef, useState } from 'react';
import { useSureflowStore } from '@/lib/store';
import { Upload, Search, Database, FileText, CheckCircle } from 'lucide-react';
import { vaultApi } from '@/lib/api';

const COLLECTION_ICONS: Record<string, string> = {
  '01-voice':          '🎙️',
  '02-icp':            '🎯',
  '03-seven-stages':   '📊',
  '04-content-pillars':'🏛️',
  '05-research':       '🔬',
  '06-what-works':     '✅',
};

export default function KnowledgeVault() {
  const { vaultCollections, fetchVaultStats } = useSureflowStore();
  const [selected, setSelected] = useState<string | null>(null);
  const [query, setQuery] = useState('');
  const [queryResults, setQueryResults] = useState<{ content: string; metadata: Record<string, unknown>; relevance_score: number }[]>([]);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);

  useEffect(() => { fetchVaultStats(); }, [fetchVaultStats]);

  const handleUpload = async (e: React.ChangeEvent<HTMLInputElement>) => {
    if (!e.target.files?.[0] || !selected) return;
    setUploading(true);
    try {
      await vaultApi.ingest(selected, e.target.files[0]);
      setUploadSuccess(true);
      await fetchVaultStats();
      setTimeout(() => setUploadSuccess(false), 3000);
    } catch (err) {
      console.error(err);
    } finally {
      setUploading(false);
    }
  };

  const handleQuery = async () => {
    if (!selected || !query.trim()) return;
    const result = await vaultApi.query(selected, query);
    setQueryResults(result.results);
  };

  return (
    <div className="p-8 min-h-screen" style={{ background: 'var(--bg-primary)' }}>
      <div className="mb-8">
        <h1 className="text-3xl font-bold mb-1" style={{ color: 'var(--text-primary)' }}>
          Knowledge <span className="gradient-text">Vault</span>
        </h1>
        <p style={{ color: 'var(--text-secondary)' }}>ChromaDB-powered RAG for your company's institutional knowledge</p>
      </div>

      {/* Collection Grid */}
      <div className="grid grid-cols-3 gap-4 mb-8">
        {vaultCollections.map(col => (
          <button
            key={col.id}
            id={`vault-col-${col.id}`}
            onClick={() => setSelected(col.id)}
            className="glass-card glass-card-hover p-5 text-left transition-all"
            style={{
              borderColor: selected === col.id ? 'rgba(99,102,241,0.5)' : 'var(--border)',
              boxShadow: selected === col.id ? '0 0 20px rgba(99,102,241,0.15)' : 'none',
            }}
          >
            <div className="text-2xl mb-3">{COLLECTION_ICONS[col.id] || '📁'}</div>
            <div className="font-semibold text-sm mb-1" style={{ color: 'var(--text-primary)' }}>
              {col.name}
            </div>
            <div className="text-xs mb-3" style={{ color: 'var(--text-muted)' }}>{col.description}</div>
            <div className="flex items-center gap-1.5">
              <FileText size={12} style={{ color: '#818cf8' }} />
              <span className="text-xs font-semibold" style={{ color: '#818cf8' }}>
                {col.document_count} chunks
              </span>
            </div>
          </button>
        ))}
      </div>

      {/* Upload & Query Panel */}
      {selected && (
        <div className="grid grid-cols-2 gap-6">
          {/* Upload */}
          <div className="glass-card p-6">
            <h3 className="font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <Upload size={16} style={{ color: '#6366f1' }} /> Ingest Document
            </h3>
            <p className="text-xs mb-4" style={{ color: 'var(--text-muted)' }}>
              Collection: <strong style={{ color: '#818cf8' }}>{selected}</strong>
            </p>
            <input
              ref={fileInputRef}
              id="vault-file-input"
              type="file"
              accept=".txt,.pdf,.md"
              className="hidden"
              onChange={handleUpload}
            />
            <button
              id="vault-upload-btn"
              className="btn-primary w-full justify-center"
              onClick={() => fileInputRef.current?.click()}
              disabled={uploading}
            >
              {uploading ? (
                <span className="flex items-center gap-2"><div className="status-dot-working" /> Embedding...</span>
              ) : uploadSuccess ? (
                <span className="flex items-center gap-2"><CheckCircle size={14} /> Ingested!</span>
              ) : (
                <><Upload size={14} /> Upload & Embed</>
              )}
            </button>
            <p className="text-xs mt-2 text-center" style={{ color: 'var(--text-muted)' }}>
              Supports .txt, .pdf, .md
            </p>
          </div>

          {/* Semantic Search */}
          <div className="glass-card p-6">
            <h3 className="font-semibold mb-4 flex items-center gap-2" style={{ color: 'var(--text-primary)' }}>
              <Search size={16} style={{ color: '#06b6d4' }} /> Semantic Search
            </h3>
            <div className="flex gap-2 mb-4">
              <input
                id="vault-query-input"
                type="text"
                placeholder="Search the vault..."
                value={query}
                onChange={e => setQuery(e.target.value)}
                onKeyDown={e => { if (e.key === 'Enter') handleQuery(); }}
                className="flex-1 px-3 py-2 rounded-xl text-sm outline-none"
                style={{ background: 'rgba(255,255,255,0.04)', border: '1px solid var(--border)', color: 'var(--text-primary)' }}
              />
              <button id="vault-search-btn" className="btn-ghost px-3" onClick={handleQuery}>
                <Search size={14} />
              </button>
            </div>
            <div className="space-y-2 max-h-60 overflow-y-auto">
              {queryResults.map((r, i) => (
                <div key={i} className="p-3 rounded-xl text-xs" style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid var(--border)' }}>
                  <div className="flex items-center justify-between mb-1">
                    <span style={{ color: 'var(--text-muted)' }}>{String(r.metadata?.source || '')}</span>
                    <span className="font-bold" style={{ color: '#10b981' }}>{(r.relevance_score * 100).toFixed(0)}%</span>
                  </div>
                  <p style={{ color: 'var(--text-secondary)' }}>{r.content}</p>
                </div>
              ))}
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
