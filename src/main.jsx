import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App.jsx'
import { createGlobalStyle, ThemeProvider } from 'styled-components'
import original from 'react95/dist/themes/original'
import ms_sans_serif from 'react95/dist/fonts/ms_sans_serif.woff2'
import ms_sans_serif_bold from 'react95/dist/fonts/ms_sans_serif_bold.woff2'

const GlobalStyles = createGlobalStyle`
  @font-face {
    font-family: 'ms_sans_serif';
    src: url('${ms_sans_serif}') format('woff2');
    font-weight: 400;
    font-style: normal
  }
  @font-face {
    font-family: 'ms_sans_serif';
    src: url('${ms_sans_serif_bold}') format('woff2');
    font-weight: bold;
    font-style: normal
  }
  body {
    font-family: 'ms_sans_serif';
    margin: 0;
    padding: 0;
    background: linear-gradient(45deg, #008080 25%, transparent 25%),
                linear-gradient(-45deg, #008080 25%, transparent 25%),
                linear-gradient(45deg, transparent 75%, #008080 75%),
                linear-gradient(-45deg, transparent 75%, #008080 75%);
    background-size: 2px 2px;
    background-position: 0 0, 0 1px, 1px -1px, -1px 0px;
    min-height: 100vh;
  }
`

ReactDOM.createRoot(document.getElementById('root')).render(
  <React.StrictMode>
    <GlobalStyles />
    <ThemeProvider theme={original}>
      <App />
    </ThemeProvider>
  </React.StrictMode>
)