import { useRef, useState } from 'react'
import { MAX_UPLOAD_MB, createFlowchart } from '../api'
import ChartForm from './ChartForm'
import useImageResult from '../useImageResult'
import Result from './Result'

function fileProblem(file) {
  if (!/\.(py|ipynb)$/i.test(file.name)) return 'Only Python files (.py) and Jupyter notebooks (.ipynb) are supported.'
  if (file.size > MAX_UPLOAD_MB * 1024 * 1024) return `The file is bigger than ${MAX_UPLOAD_MB} MB.`
  return ''
}

export default function Body() {
  const [selectedFile, setSelectedFile] = useState(null)
  const [isDragging, setIsDragging] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [flowchart, showFlowchart] = useImageResult()
  const fileInputRef = useRef(null)

  const baseName = selectedFile?.name.replace(/\.(py|ipynb)$/i, '')

  function handleFile(file) {
    if (!file) return
    setSelectedFile(file)
    setError(fileProblem(file))
  }

  async function sendFile() {
    const problem = fileProblem(selectedFile)
    setError(problem)
    if (problem) return

    setIsLoading(true)
    try {
      const blob = await createFlowchart(selectedFile)
      showFlowchart(blob, `${baseName}.png`)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <main className="main-content">
      <section className="hero" aria-labelledby="page-title">
        <div className="eyebrow">
          <span className="eyebrow-dot" />
          CODE IN, FLOWCHART OUT
        </div>
        <h1 id="page-title">Make your code <span>visual.</span></h1>
        <p className="hero-copy">
          Turn your source files into clear, easy-to-follow flowcharts.
          <br className="desktop-break" /> Upload a file to get started.
        </p>

        <div
          className={`upload-card${isDragging ? ' is-dragging' : ''}${selectedFile ? ' has-file' : ''}`}
          onDragOver={(event) => {
            event.preventDefault()
            setIsDragging(true)
          }}
          onDragLeave={(event) => {
            if (!event.currentTarget.contains(event.relatedTarget)) setIsDragging(false)
          }}
          onDrop={(event) => {
            event.preventDefault()
            setIsDragging(false)
            handleFile(event.dataTransfer.files[0])
          }}
        >
          <input
            ref={fileInputRef}
            className="file-input"
            type="file"
            accept=".py,.ipynb"
            onChange={(event) => {
              handleFile(event.target.files[0])
              event.target.value = ''  // lets the same file be picked again after editing it
            }}
            aria-label="Choose a source code file"
          />
          <div className="upload-icon" aria-hidden="true">
            {selectedFile ? (
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M13 2H6a2 2 0 0 0-2 2v16a2 2 0 0 0 2 2h12a2 2 0 0 0 2-2V9z" />
                <path d="M13 2v7h7M8 15h8m-8 4h8" />
              </svg>
            ) : (
              <svg viewBox="0 0 24 24" fill="none">
                <path d="M12 16V4m0 0L7.5 8.5M12 4l4.5 4.5" />
                <path d="M20 15v4a2 2 0 0 1-2 2H6a2 2 0 0 1-2-2v-4" />
              </svg>
            )}
          </div>
          <h2>{selectedFile ? selectedFile.name : 'Drop your file here'}</h2>
          <p>
            {selectedFile
              ? `${(selectedFile.size / 1024).toFixed(1)} KB · ${isLoading ? 'Creating flowchart…' : 'Press the arrow to create the flowchart'}`
              : 'or click below to browse from your computer'}
          </p>
          <button
            className="choose-file-button"
            type="button"
            onClick={() => fileInputRef.current?.click()}
          >
            <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
              <path d="M10 13V3m0 0L6.5 6.5M10 3l3.5 3.5" />
              <path d="M4 11v5a1 1 0 0 0 1 1h10a1 1 0 0 0 1-1v-5" />
            </svg>
            {selectedFile ? 'Choose another file' : 'Choose a file'}
          </button>
          <span className="file-types">Python (.py) and Jupyter notebooks (.ipynb) · Max {MAX_UPLOAD_MB} MB</span>
          <button
            className="send-file-button"
            type="button"
            aria-label="Create flowchart"
            title="Create flowchart"
            disabled={!selectedFile || isLoading}
            aria-busy={isLoading}
            onClick={sendFile}
          >
            {isLoading ? (
              <span className="spinner" aria-hidden="true" />
            ) : (
              <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
                <path d="m3 9 13-6-4.5 14-2.5-6-6-2Z" />
                <path d="m9 11 4-4" />
              </svg>
            )}
          </button>
        </div>

        {error && <p className="form-error" role="alert">{error}</p>}

        <div className="privacy-note">
          <svg viewBox="0 0 18 18" fill="none" aria-hidden="true">
            <rect x="3.5" y="7.5" width="11" height="8" rx="2" />
            <path d="M6 7.5V5a3 3 0 0 1 6 0v2.5m-3 3v2" />
          </svg>
          Your files stay private and are only used to create your flowchart.
        </div>

        {flowchart && <Result title="Flowchart" result={flowchart} />}

        <ChartForm baseName={baseName} />
      </section>
    </main>
  )
}
