import React from 'react'
import Header from './Components/Header'
import Body from './Components/Body'

export default function App() {
  const [isLightTheme, setIsLightTheme] = React.useState(false)

  return (
    <div className={`app-shell${isLightTheme ? ' theme-light' : ''}`}>
      <Header
        isLightTheme={isLightTheme}
        onToggleTheme={() => setIsLightTheme((currentTheme) => !currentTheme)}
      />
      <Body />
    </div>
  )
}
