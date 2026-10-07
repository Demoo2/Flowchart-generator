export default function Header({ isLightTheme, onToggleTheme }) {
  return (
    <header className="site-header">
      <a className="brand" href="#" aria-label="Flowchart Generator home">
        <svg className="brand-mark" viewBox="0 0 40 32" fill="none" aria-hidden="true">
          <path d="M5 22 14 12l8 7L33 6" />
          <path d="M27 6h6v6" />
          <circle cx="5" cy="22" r="2.5" />
          <circle cx="14" cy="12" r="2.5" />
          <circle cx="22" cy="19" r="2.5" />
          <circle cx="33" cy="6" r="2.5" />
          <circle cx="35" cy="24" r="2.5" />
          <path d="M22 19h9l4 5" />
        </svg>
        <span>Flowchart Generator</span>
      </a>

      <button
        className="theme-toggle"
        type="button"
        onClick={onToggleTheme}
        aria-label={`Switch to ${isLightTheme ? 'dark' : 'light'} theme`}
        title={`Switch to ${isLightTheme ? 'dark' : 'light'} theme`}
      >
        {isLightTheme ? (
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <circle cx="12" cy="12" r="4" />
            <path d="M12 2v2m0 16v2M4.93 4.93l1.42 1.42m11.3 11.3 1.42 1.42M2 12h2m16 0h2M4.93 19.07l1.42-1.42m11.3-11.3 1.42-1.42" />
          </svg>
        ) : (
          <svg viewBox="0 0 24 24" fill="none" aria-hidden="true">
            <path d="M20.2 15.6A8.7 8.7 0 0 1 8.4 3.8 8.8 8.8 0 1 0 20.2 15.6Z" />
          </svg>
        )}
      </button>
    </header>
  )
}
