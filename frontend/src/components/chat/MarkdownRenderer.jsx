import React from 'react';
import DOMPurify from 'dompurify';

export function parseMarkdownToHtml(str) {
  if (!str) return '';
  const lines = str.split('\n');
  let inTable = false;
  let tableHeaders = [];
  let tableRows = [];
  let outputLines = [];

  const renderCurrentTable = () => {
    if (tableHeaders.length === 0 && tableRows.length === 0) return '';
    const headers = tableHeaders.length > 0 ? tableHeaders : (tableRows.length > 0 ? tableRows.shift() : []);
    let tHtml = '<div class="table-responsive"><table class="chat-md-table"><thead><tr>';
    headers.forEach(h => { tHtml += `<th>${h}</th>`; });
    tHtml += '</tr></thead><tbody>';
    tableRows.forEach(row => {
      tHtml += '<tr>';
      for (let cIdx = 0; cIdx < headers.length; cIdx++) {
        tHtml += `<td>${row[cIdx] !== undefined ? row[cIdx] : ''}</td>`;
      }
      tHtml += '</tr>';
    });
    tHtml += '</tbody></table></div>';
    tableHeaders = [];
    tableRows = [];
    inTable = false;
    return tHtml;
  };

  for (let i = 0; i < lines.length; i++) {
    const line = lines[i].trim();
    
    if (/^\|?[-:\s|]+\|?$/.test(line) && line.includes('-') && (line.includes('|') || line.includes(':'))) {
      inTable = true;
      continue;
    }
    
    if (line.includes('|')) {
      const cells = line.split('|').map(c => c.trim()).filter((c, idx, arr) => {
        if ((idx === 0 || idx === arr.length - 1) && c === '') return false;
        return true;
      });
      if (cells.length >= 2) {
        if (!inTable && tableHeaders.length === 0) {
          tableHeaders = cells;
        } else {
          tableRows.push(cells);
        }
        inTable = true;
        continue;
      }
    }
    
    if (inTable || tableHeaders.length > 0 || tableRows.length > 0) {
      outputLines.push(renderCurrentTable());
    }
    outputLines.push(line);
  }
  
  if (inTable || tableHeaders.length > 0 || tableRows.length > 0) {
    outputLines.push(renderCurrentTable());
  }

  let html = outputLines.join('\n')
    .replace(/\[([^\]]+)\]\((https?:\/\/[^\s)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer" class="chat-markdown-link">🔗 $1 ↗</a>')
    .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
    .replace(/(?<!\*)\*(?!\*)(.*?)\*/g, '<em>$1</em>')
    .replace(/\n\*/g, '<br/> • ')
    .replace(/\n-/g, '<br/> • ')
    .replace(/\n/g, '<br/>');
    
  return DOMPurify.sanitize(html, { ADD_ATTR: ['target', 'rel'] });
}

export default function MarkdownRenderer({ content }) {
  if (!content) return null;
  
  const sections = content.split(/(?=###? )/);
  return (
    <>
      {sections.map((section, idx) => {
        if (section.trim() === '#' || section.trim() === '##' || section.trim() === '') return null;
        
        if (!section.startsWith('#')) {
          return (
            <div key={idx} className="chat-normal-text" dangerouslySetInnerHTML={{ 
              __html: parseMarkdownToHtml(section)
            }} />
          );
        }
        
        const lines = section.split('\n');
        const header = lines[0].replace(/###? /, '');
        const body = lines.slice(1).join('\n');
        
        return (
          <div key={idx} className="chat-card">
            <h4>{header}</h4>
            <div className="card-body" dangerouslySetInnerHTML={{ __html: parseMarkdownToHtml(body) }} />
          </div>
        );
      })}
    </>
  );
}
