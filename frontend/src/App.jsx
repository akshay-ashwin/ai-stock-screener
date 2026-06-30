import { useState } from 'react'
import './App.css'

function App() {
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [loading, setLoading] = useState(false)

  const handleSearch = async () => {
    setLoading(true)
    try {
      const response = await fetch('http://127.0.0.1:8000/api/screener/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ query }),
      })
      const data = await response.json()
      setResults(data)
    } catch (error) {
      console.error('Error:', error)
    }
    setLoading(false)
  }

  return (
    <div className="app">
      <div className="gradient-bg" />
      
      <div className="container">
        <header className="header">
          <div className="logo">📊</div>
          <h1 className="title">AI Stock Screener</h1>
          <p className="subtitle">Find your next investment opportunity with natural language</p>
        </header>

        <div className="search-container">
          <div className="input-wrapper">
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Try: 'Find undervalued banking stocks with high ROE'..."
              className="search-input"
            />
            <div className="input-glow" />
          </div>

          <button
            onClick={handleSearch}
            disabled={loading || !query}
            className={`search-button ${loading || !query ? 'disabled' : ''}`}
          >
            {loading ? (
              <>
                <div className="spinner" />
                <span>Analyzing...</span>
              </>
            ) : (
              <>
                <span>Search Stocks</span>
                <span className="arrow">→</span>
              </>
            )}
          </button>
        </div>

        {results && results.results && results.results.length > 0 && (
          <div className="results-section">
            <div className="results-header">
              <h2 className="results-title">
                Found <span className="highlight">{results.count}</span> stocks
              </h2>
              <p className="query-text">"{results.query}"</p>
            </div>

            <div className="stocks-grid">
              {results.results.map((stock, index) => (
                <div key={index} className="stock-card">
                  <div className="stock-header">
                    <div>
                      <h3 className="stock-symbol">{stock.symbol}</h3>
                      <p className="stock-name">{stock.name}</p>
                    </div>
                    <div className="stock-price">₹{stock.price?.toFixed(2) || 'N/A'}</div>
                  </div>

                  <div className="stock-metrics">
                    {stock.pe_ratio && (
                      <div className="metric">
                        <span className="metric-label">P/E Ratio</span>
                        <span className="metric-value">{stock.pe_ratio.toFixed(2)}</span>
                      </div>
                    )}
                    {stock.roe && (
                      <div className="metric">
                        <span className="metric-label">ROE</span>
                        <span className="metric-value">{stock.roe.toFixed(2)}%</span>
                      </div>
                    )}
                    {stock.market_cap && (
                      <div className="metric">
                        <span className="metric-label">Market Cap</span>
                        <span className="metric-value">₹{(stock.market_cap / 100000).toFixed(2)}L Cr</span>
                      </div>
                    )}
                  </div>

                  {stock.sector && (
                    <div className="stock-sector">{stock.sector}</div>
                  )}
                </div>
              ))}
            </div>
          </div>
        )}

        {results && (!results.results || results.results.length === 0) && (
          <div className="no-results">
            <div className="no-results-icon">🔍</div>
            <h3>No stocks found</h3>
            <p>Try adjusting your search criteria</p>
          </div>
        )}
      </div>
    </div>
  )
}

export default App