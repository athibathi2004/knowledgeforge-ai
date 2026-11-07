/**
 * KnowledgeForge AI - Frontend Application Controller
 */

const API_BASE = '/api/v1';
let currentConversationId = null;

// Initialize on DOM load
document.addEventListener('DOMContentLoaded', () => {
  setupTabs();
  checkSystemHealth();
  loadDocuments();
  setupChatHandlers();
  setupUploadHandlers();
  setupRetrievalPlayground();
  setupEvaluationHandlers();
  setInterval(checkSystemHealth, 30000); // Periodic health ping
});

/* ==========================================================================
   Tab Navigation
   ========================================================================== */
function setupTabs() {
  const navItems = document.querySelectorAll('.nav-item');
  const panes = document.querySelectorAll('.tab-pane');

  navItems.forEach(item => {
    item.addEventListener('click', () => {
      const targetId = item.getAttribute('data-tab');
      navItems.forEach(n => n.classList.remove('active'));
      panes.forEach(p => p.classList.remove('active'));

      item.classList.add('active');
      const targetPane = document.getElementById(targetId);
      if (targetPane) targetPane.classList.add('active');

      if (targetId === 'docs-tab') loadDocuments();
    });
  });
}

/* ==========================================================================
   System Health Check
   ========================================================================== */
async function checkSystemHealth() {
  try {
    const res = await fetch(`${API_BASE}/health`);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    const dot = document.getElementById('system-status-dot');
    const text = document.getElementById('system-status-text');
    const badgeDb = document.getElementById('badge-db');
    const badgeEmb = document.getElementById('badge-emb');
    const badgeLlm = document.getElementById('badge-llm');

    if (data.status === 'healthy') {
      dot.className = 'status-dot healthy';
      text.innerText = 'System Online';
    } else {
      dot.className = 'status-dot';
      text.innerText = `Degraded (${data.status})`;
    }

    badgeDb.innerText = `DB: ${data.components.database.status === 'healthy' ? 'OK' : 'ERR'}`;
    badgeEmb.innerText = `EMB: ${data.components.embedding_service.provider}`;
    badgeLlm.innerText = `LLM: ${data.components.llm_gateway.provider}`;
  } catch (err) {
    const dot = document.getElementById('system-status-dot');
    const text = document.getElementById('system-status-text');
    dot.className = 'status-dot';
    text.innerText = 'API Disconnected';
  }
}

/* ==========================================================================
   Chat Assistant
   ========================================================================== */
function setupChatHandlers() {
  const input = document.getElementById('chat-input');
  const sendBtn = document.getElementById('btn-send-chat');
  const clearBtn = document.getElementById('btn-clear-chat');

  sendBtn.addEventListener('click', submitChatQuery);
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      submitChatQuery();
    }
  });

  clearBtn.addEventListener('click', () => {
    currentConversationId = null;
    const viewport = document.getElementById('chat-viewport');
    viewport.innerHTML = `
      <div class="chat-message assistant welcome-msg">
        <div class="msg-avatar">AI</div>
        <div class="msg-body">
          <p>Conversation thread cleared. What would you like to explore next?</p>
        </div>
      </div>
    `;
  });
}

function setQuery(text) {
  const input = document.getElementById('chat-input');
  input.value = text;
  input.focus();
}

async function submitChatQuery() {
  const input = document.getElementById('chat-input');
  const query = input.value.trim();
  if (!query) return;

  const topK = parseInt(document.getElementById('chat-topk').value) || 5;
  const enableRerank = document.getElementById('chat-rerank').checked;

  input.value = '';
  appendUserMessage(query);

  const pendingMsgEl = appendAssistantPending();

  try {
    const res = await fetch(`${API_BASE}/chat`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        conversation_id: currentConversationId,
        top_k: topK,
        enable_reranking: enableRerank,
      }),
    });

    if (!res.ok) {
      const errData = await res.json().catch(() => ({}));
      throw new Error(errData.detail || `HTTP ${res.status}`);
    }

    const data = await res.json();
    currentConversationId = data.conversation_id;
    updateAssistantMessage(pendingMsgEl, data);
  } catch (err) {
    pendingMsgEl.querySelector('.msg-body').innerHTML = `
      <p style="color:var(--danger)"><strong>Error:</strong> ${escapeHtml(err.message)}</p>
    `;
  }
}

function appendUserMessage(text) {
  const viewport = document.getElementById('chat-viewport');
  const div = document.createElement('div');
  div.className = 'chat-message user';
  div.innerHTML = `
    <div class="msg-avatar">You</div>
    <div class="msg-body">${escapeHtml(text)}</div>
  `;
  viewport.appendChild(div);
  viewport.scrollTop = viewport.scrollHeight;
}

function appendAssistantPending() {
  const viewport = document.getElementById('chat-viewport');
  const div = document.createElement('div');
  div.className = 'chat-message assistant';
  div.innerHTML = `
    <div class="msg-avatar">AI</div>
    <div class="msg-body">
      <p><em>Retrieving knowledge context and generating answer...</em></p>
    </div>
  `;
  viewport.appendChild(div);
  viewport.scrollTop = viewport.scrollHeight;
  return div;
}

function updateAssistantMessage(msgEl, data) {
  const bodyEl = msgEl.querySelector('.msg-body');
  let citationsHtml = '';

  if (data.citations && data.citations.length > 0) {
    citationsHtml = `
      <div class="citations-list">
        ${data.citations.map(c => `
          <div class="citation-card">
            <div class="citation-header">
              <span>[Doc: ${escapeHtml(c.document_title)}, Chunk: ${c.chunk_index}${c.page_number ? `, Page: ${c.page_number}` : ''}]</span>
              <span>Relevance: ${(c.relevance_score * 100).toFixed(0)}%</span>
            </div>
            <div class="citation-snippet">"${escapeHtml(c.snippet)}"</div>
          </div>
        `).join('')}
      </div>
    `;
  }

  const groundedText = data.is_grounded ? '<span class="grounded-badge">&#10003; Grounded in Context</span>' : '<span style="color:var(--warning)">Insufficient Evidence</span>';

  bodyEl.innerHTML = `
    <p>${escapeHtml(data.answer)}</p>
    ${citationsHtml}
    <div class="msg-meta">
      ${groundedText}
      <span>&bull;</span>
      <span>Retrieval: ${data.latency.retrieval_ms}ms</span>
      <span>&bull;</span>
      <span>Rerank: ${data.latency.rerank_ms}ms</span>
      <span>&bull;</span>
      <span>Total: ${data.latency.total_ms}ms</span>
    </div>
  `;

  const viewport = document.getElementById('chat-viewport');
  viewport.scrollTop = viewport.scrollHeight;
}

/* ==========================================================================
   Document Management Hub
   ========================================================================== */
function setupUploadHandlers() {
  const dropZone = document.getElementById('drop-zone');
  const fileInput = document.getElementById('file-input');
  const refreshBtn = document.getElementById('btn-refresh-docs');
  const modalClose = document.getElementById('modal-close');

  dropZone.addEventListener('click', () => fileInput.click());
  refreshBtn.addEventListener('click', loadDocuments);

  dropZone.addEventListener('dragover', (e) => {
    e.preventDefault();
    dropZone.classList.add('dragover');
  });

  dropZone.addEventListener('dragleave', () => dropZone.classList.remove('dragover'));

  dropZone.addEventListener('drop', (e) => {
    e.preventDefault();
    dropZone.classList.remove('dragover');
    if (e.dataTransfer.files.length > 0) {
      handleFileUpload(e.dataTransfer.files[0]);
    }
  });

  fileInput.addEventListener('change', () => {
    if (fileInput.files.length > 0) {
      handleFileUpload(fileInput.files[0]);
    }
  });

  modalClose.addEventListener('click', () => {
    document.getElementById('chunk-modal').classList.remove('active');
  });
}

async function handleFileUpload(file) {
  const progressContainer = document.getElementById('upload-progress-container');
  const progressBar = document.getElementById('upload-progress-bar');
  const progressText = document.getElementById('upload-progress-text');

  const chunkSize = document.getElementById('upload-chunk-size').value;
  const chunkOverlap = document.getElementById('upload-chunk-overlap').value;
  const strategy = document.getElementById('upload-strategy').value;

  progressContainer.style.display = 'block';
  progressBar.style.width = '35%';
  progressText.innerText = `Parsing and embedding ${file.name}...`;

  const formData = new FormData();
  formData.append('file', file);
  formData.append('chunk_size', chunkSize);
  formData.append('chunk_overlap', chunkOverlap);
  formData.append('chunking_strategy', strategy);

  try {
    const res = await fetch(`${API_BASE}/documents/upload`, {
      method: 'POST',
      body: formData,
    });

    progressBar.style.width = '100%';
    if (!res.ok) {
      const err = await res.json().catch(() => ({}));
      throw new Error(err.detail || `Upload failed with status ${res.status}`);
    }

    const doc = await res.json();
    progressText.innerText = `Indexed ${doc.title} (${doc.chunk_count} chunks generated)`;
    setTimeout(() => {
      progressContainer.style.display = 'none';
      progressBar.style.width = '0%';
    }, 2500);

    loadDocuments();
  } catch (err) {
    progressBar.style.backgroundColor = 'var(--danger)';
    progressText.innerText = `Error: ${err.message}`;
  }
}

async function loadDocuments() {
  try {
    const res = await fetch(`${API_BASE}/documents`);
    const data = await res.json();

    document.getElementById('doc-count').innerText = data.total;
    const tbody = document.getElementById('docs-table-body');

    if (!data.documents || data.documents.length === 0) {
      tbody.innerHTML = `<tr><td colspan="7" class="empty-cell">No documents indexed yet. Upload sample documents above.</td></tr>`;
      return;
    }

    tbody.innerHTML = data.documents.map(doc => `
      <tr>
        <td><strong>${escapeHtml(doc.title)}</strong><br><small style="color:var(--text-muted)">${escapeHtml(doc.filename)}</small></td>
        <td><span class="comp-badge">${doc.file_type.toUpperCase()}</span></td>
        <td>${(doc.file_size / 1024).toFixed(1)} KB</td>
        <td><strong>${doc.chunk_count}</strong></td>
        <td><span class="badge-tag">${doc.status}</span></td>
        <td>${new Date(doc.created_at).toLocaleDateString()}</td>
        <td>
          <button class="btn-secondary btn-sm" onclick="viewDocumentChunks('${doc.id}', '${escapeHtml(doc.title)}')">Chunks</button>
          <button class="btn-danger btn-sm" onclick="deleteDocument('${doc.id}')">Delete</button>
        </td>
      </tr>
    `).join('');
  } catch (err) {
    console.error('Failed to load documents:', err);
  }
}

async function viewDocumentChunks(docId, title) {
  const modal = document.getElementById('chunk-modal');
  const titleEl = document.getElementById('modal-doc-title');
  const bodyEl = document.getElementById('modal-chunks-body');

  titleEl.innerText = `Chunks for: ${title}`;
  bodyEl.innerHTML = '<p>Loading extracted chunks...</p>';
  modal.classList.add('active');

  try {
    const res = await fetch(`${API_BASE}/documents/${docId}`);
    const data = await res.json();

    if (!data.chunks || data.chunks.length === 0) {
      bodyEl.innerHTML = '<p>No chunks recorded for this document.</p>';
      return;
    }

    bodyEl.innerHTML = data.chunks.map(c => `
      <div style="background:var(--bg-primary); border:1px solid var(--border); border-radius:var(--radius-sm); padding:12px; margin-bottom:12px;">
        <div style="display:flex; justify-content:space-between; color:var(--accent); font-weight:600; font-size:0.8rem; margin-bottom:6px;">
          <span>Chunk #${c.chunk_index} ${c.chunk_metadata && c.chunk_metadata.page_number ? `(Page ${c.chunk_metadata.page_number})` : ''}</span>
          <span>Tokens: ${c.token_count}</span>
        </div>
        <div style="color:var(--text-secondary); line-height:1.5;">${escapeHtml(c.content)}</div>
      </div>
    `).join('');
  } catch (err) {
    bodyEl.innerHTML = `<p style="color:var(--danger)">Error loading chunks: ${err.message}</p>`;
  }
}

async function deleteDocument(docId) {
  if (!confirm('Are you sure you want to delete this document and all its indexed chunks?')) return;
  try {
    const res = await fetch(`${API_BASE}/documents/${docId}`, { method: 'DELETE' });
    if (res.ok) {
      loadDocuments();
    } else {
      alert('Failed to delete document');
    }
  } catch (err) {
    alert(`Error: ${err.message}`);
  }
}

/* ==========================================================================
   Retrieval Playground
   ========================================================================== */
function setupRetrievalPlayground() {
  const alphaSlider = document.getElementById('retrieval-alpha');
  const alphaVal = document.getElementById('alpha-val');
  const searchBtn = document.getElementById('btn-test-retrieval');
  const queryInput = document.getElementById('retrieval-query-input');

  alphaSlider.addEventListener('input', () => {
    alphaVal.innerText = parseFloat(alphaSlider.value).toFixed(2);
  });

  searchBtn.addEventListener('click', executeRetrievalTest);
  queryInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter') executeRetrievalTest();
  });
}

async function executeRetrievalTest() {
  const query = document.getElementById('retrieval-query-input').value.trim();
  if (!query) return;

  const alpha = parseFloat(document.getElementById('retrieval-alpha').value);
  const topK = parseInt(document.getElementById('retrieval-topk').value) || 5;
  const enableRerank = document.getElementById('retrieval-rerank').checked;

  const container = document.getElementById('retrieval-cards');
  container.innerHTML = '<p>Querying hybrid vector & BM25 indices...</p>';

  try {
    const res = await fetch(`${API_BASE}/retrieval/search`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query,
        top_k: topK,
        hybrid_alpha: alpha,
        enable_reranking: enableRerank,
      }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    document.getElementById('retrieval-meta').style.display = 'block';
    document.getElementById('retrieval-time').innerText = data.latency_ms;
    document.getElementById('retrieval-count').innerText = data.total_retrieved;

    if (data.results.length === 0) {
      container.innerHTML = '<div class="empty-state"><p>No relevant chunks retrieved for this query.</p></div>';
      return;
    }

    container.innerHTML = data.results.map((r, idx) => `
      <div class="candidate-card">
        <div class="candidate-header">
          <span class="candidate-title">#${idx + 1} &bull; ${escapeHtml(r.document_title)} (Chunk #${r.chunk_index}${r.page_number ? `, Page ${r.page_number}` : ''})</span>
          <div class="candidate-scores">
            <span class="score-tag">Total: ${(r.score * 100).toFixed(1)}%</span>
            <span class="score-tag">Vector: ${r.vector_score ? (r.vector_score * 100).toFixed(1) + '%' : 'N/A'}</span>
            <span class="score-tag">BM25: ${r.bm25_score ? (r.bm25_score * 100).toFixed(1) + '%' : 'N/A'}</span>
            ${r.rerank_score ? `<span class="score-tag" style="color:var(--accent)">Rerank: ${(r.rerank_score * 100).toFixed(1)}%</span>` : ''}
          </div>
        </div>
        <div class="candidate-content">${escapeHtml(r.content)}</div>
      </div>
    `).join('');
  } catch (err) {
    container.innerHTML = `<p style="color:var(--danger)">Search error: ${err.message}</p>`;
  }
}

/* ==========================================================================
   Evaluation Benchmark
   ========================================================================== */
function setupEvaluationHandlers() {
  const runBtn = document.getElementById('btn-run-eval');
  runBtn.addEventListener('click', runEvaluationBenchmark);
}

async function runEvaluationBenchmark() {
  const runBtn = document.getElementById('btn-run-eval');
  runBtn.disabled = true;
  runBtn.innerHTML = '<span>Running Benchmark...</span>';

  try {
    const res = await fetch(`${API_BASE}/evaluations/run`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        top_k: 5,
        enable_reranking: true,
      }),
    });

    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    const data = await res.json();

    document.getElementById('metric-precision').innerText = data.context_precision.toFixed(2);
    document.getElementById('metric-recall').innerText = data.context_recall.toFixed(2);
    document.getElementById('metric-faithfulness').innerText = data.faithfulness.toFixed(2);
    document.getElementById('metric-relevance').innerText = data.answer_relevance.toFixed(2);
    document.getElementById('eval-run-id').innerText = `Run: ${data.id.substring(0, 8)}... (${data.sample_count} samples)`;

    const tbody = document.getElementById('eval-table-body');
    const samples = data.detailed_results ? data.detailed_results.samples : [];

    if (samples && samples.length > 0) {
      tbody.innerHTML = samples.map(s => `
        <tr>
          <td><strong>${escapeHtml(s.question)}</strong></td>
          <td><small>${escapeHtml(s.ground_truth_answer)}</small></td>
          <td><small>${escapeHtml(s.generated_answer)}</small></td>
          <td><strong>${s.context_precision.toFixed(2)}</strong></td>
          <td><strong>${s.context_recall.toFixed(2)}</strong></td>
          <td><strong>${s.faithfulness.toFixed(2)}</strong></td>
          <td>${s.retrieval_latency_ms.toFixed(0)}ms</td>
        </tr>
      `).join('');
    }
  } catch (err) {
    alert(`Evaluation benchmark error: ${err.message}`);
  } finally {
    runBtn.disabled = false;
    runBtn.innerHTML = `
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polygon points="5 3 19 12 5 21 5 3"/></svg>
      <span>Run Benchmark</span>
    `;
  }
}

/* Helper Utilities */
function escapeHtml(text) {
  if (!text) return '';
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#039;');
}

