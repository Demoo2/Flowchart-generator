export default function Result({ title, result }) {
  return (
    <div className="result-card">
      <div className="result-header">
        <h3>{title}</h3>
        <a className="download-button" href={result.url} download={result.filename}>
          <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
            <path d="M10 3v10m0 0 3.5-3.5M10 13 6.5 9.5" />
            <path d="M4 13v3a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-3" />
          </svg>
          Download
        </a>
      </div>
      <a href={result.url} target="_blank" rel="noreferrer" title="Open full size">
        <img className="result-image" src={result.url} alt={title} />
      </a>
    </div>
  )
}
