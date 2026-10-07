import { useEffect, useState } from 'react'

// Holds a generated image as an object URL and frees the previous one when it is replaced.
export default function useImageResult() {
  const [result, setResult] = useState(null)

  useEffect(() => () => {
    if (result) URL.revokeObjectURL(result.url)
  }, [result])

  function show(blob, filename) {
    setResult({ url: URL.createObjectURL(blob), filename })
  }

  return [result, show]
}
