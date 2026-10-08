import { useState } from 'react'
import { COMPLEXITIES, MAX_TEXT, createChart, parseNumbers } from '../api'
import useImageResult from '../useImageResult'
import Result from './Result'

const MAX_POINTS = 1000

export default function ChartForm({ baseName }) {
  const [isOpen, setIsOpen] = useState(false)
  const [sizesText, setSizesText] = useState('')
  const [stepsText, setStepsText] = useState('')
  const [timeChart, setTimeChart] = useState(true)
  const [complexity, setComplexity] = useState('O(n**2)')
  const [label, setLabel] = useState('')
  const [title, setTitle] = useState('')
  const [xLabel, setXLabel] = useState('')
  const [yLabel, setYLabel] = useState('')
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState('')
  const [chart, showChart] = useImageResult()

  const sizes = parseNumbers(sizesText)
  const steps = parseNumbers(stepsText)

  function validate() {
    if (sizes.length < 2) return 'Enter at least 2 input sizes.'
    if (steps.length !== sizes.length) {
      return `You entered ${sizes.length} input sizes but ${steps.length} step counts. They must match.`
    }
    if (sizes.length > MAX_POINTS) return `Use at most ${MAX_POINTS} values.`
    return ''
  }

  async function handleSubmit(event) {
    event.preventDefault()
    const problem = validate()
    setError(problem)
    if (problem) return

    setIsLoading(true)
    try {
      const blob = await createChart({
        x: sizes,
        y: steps,
        time_chart: timeChart,
        time_complexity: complexity,
        label,
        title,
        x_label: xLabel,
        y_label: yLabel,
      })
      showChart(blob, `${baseName || 'time-complexity'}-chart.png`)
    } catch (requestError) {
      setError(requestError.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="chart-section">
      <button
        className={`chart-toggle${isOpen ? ' is-open' : ''}`}
        type="button"
        aria-expanded={isOpen}
        aria-controls="chart-form"
        onClick={() => setIsOpen((open) => !open)}
      >
        <svg viewBox="0 0 20 20" fill="none" aria-hidden="true">
          <path d="M3 17h14M5 14l3.5-4 3 2.5L16 6" />
        </svg>
        {isOpen ? 'Hide time-complexity chart' : 'Add time-complexity chart'}
        <svg className="chevron" viewBox="0 0 20 20" fill="none" aria-hidden="true">
          <path d="m6 8 4 4 4-4" />
        </svg>
      </button>

      {isOpen && (
        <form id="chart-form" className="chart-card" onSubmit={handleSubmit} noValidate>
          <p className="chart-intro">
            Run your program for a few input sizes and paste what it printed. You can paste a
            Python list like <code>[14, 2282, 65236]</code> as it is.
          </p>

          <div className="field-grid">
            <label className="field">
              <span className="field-label">Input sizes (n)</span>
              <textarea
                rows="2"
                value={sizesText}
                onChange={(event) => setSizesText(event.target.value)}
                placeholder="[10, 100, 1000, 2000]"
                spellCheck="false"
              />
              <span className="field-hint">{sizes.length} values</span>
            </label>

            <label className="field">
              <span className="field-label">Number of steps</span>
              <textarea
                rows="2"
                value={stepsText}
                onChange={(event) => setStepsText(event.target.value)}
                placeholder="[14, 2282, 258631, 1024480]"
                spellCheck="false"
              />
              <span className={`field-hint${steps.length && steps.length !== sizes.length ? ' is-warning' : ''}`}>
                {steps.length} values
              </span>
            </label>
          </div>

          <div className="field-grid">
            <div className="field">
              <label className="checkbox">
                <input
                  type="checkbox"
                  checked={timeChart}
                  onChange={(event) => setTimeChart(event.target.checked)}
                />
                Compare with Big-O curve
              </label>
              <select
                value={complexity}
                onChange={(event) => setComplexity(event.target.value)}
                disabled={!timeChart}
                aria-label="Big-O complexity to compare with"
              >
                {COMPLEXITIES.map((option) => (
                  <option key={option.value} value={option.value}>{option.label}</option>
                ))}
              </select>
              <span className="field-hint">
                {timeChart ? 'The curve is scaled to your data automatically.' : 'Only your measured line will be drawn.'}
              </span>
            </div>

            <label className="field">
              <span className="field-label">Algorithm name <em>(optional)</em></span>
              <input
                type="text"
                maxLength={MAX_TEXT}
                value={label}
                onChange={(event) => setLabel(event.target.value)}
                placeholder="Bubble sort"
              />
            </label>
          </div>

          <details className="more-options">
            <summary>Chart texts (optional)</summary>
            <div className="field-grid three">
              <label className="field">
                <span className="field-label">Title</span>
                <input type="text" maxLength={MAX_TEXT} value={title} onChange={(event) => setTitle(event.target.value)} placeholder="Time Complexity: O(n**2)" />
              </label>
              <label className="field">
                <span className="field-label">X axis</span>
                <input type="text" maxLength={MAX_TEXT} value={xLabel} onChange={(event) => setXLabel(event.target.value)} placeholder="Input size (n)" />
              </label>
              <label className="field">
                <span className="field-label">Y axis</span>
                <input type="text" maxLength={MAX_TEXT} value={yLabel} onChange={(event) => setYLabel(event.target.value)} placeholder="Number of steps" />
              </label>
            </div>
          </details>

          {error && <p className="form-error" role="alert">{error}</p>}

          <button className="choose-file-button create-chart-button" type="submit" disabled={isLoading} aria-busy={isLoading}>
            {isLoading && <span className="spinner" aria-hidden="true" />}
            {isLoading ? 'Creating chart…' : 'Create chart'}
          </button>
        </form>
      )}

      {chart && <Result title="Time-complexity chart" result={chart} />}
    </div>
  )
}
