import { useState } from 'react'
import { Search } from "lucide-react";
import './App.css'

const BACKEND_API_URL = 'http://localhost:8000/'
const DEFAULT_RESPONSE = 'Search for anything you need. Toggle on to enhance results with RAG'

function App() {
  const [query, setQuery] = useState("");
  const [useRag, setUseRag] = useState(false);
  const [results, setResults] = useState([]);
  const [response, setResponse] = useState(DEFAULT_RESPONSE);
  const [loading, setLoading] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    setResults([]);
    setResponse('');
    
    try {
      const response = await fetch(`${BACKEND_API_URL}answer_question?query=${query}&useRag=${useRag}`, {
        method: "GET",
        redirect: "follow",
      });
      
      var data = await response.json();
      if (['NONE', 'NONE\n', 'none', 'none\n'].includes(data.message)){
        setResponse('No records found');
      }
      else{
        setResponse(data.message);
        setResults(data.sources);
      }
    } catch (error) {
      console.error("Error fetching quiz:", error);
    }
    setLoading(false);
  };

  console.log('useRag', useRag);

  return (
    <div className="container">
      <div className='heading-title'>
      <img width="100" height="100" src="./../public/logo_white.svg"/>
      <h1>Carolina GPT</h1>
      </div>
      <div className="search-box">
        <input
          className="search-input"
          placeholder="Ask me anything..."
          value={query}
          onChange={(e) => !loading && setQuery(e.target.value)}
          onKeyDown={(e) => e.key === "Enter" && handleSearch()}
        />
        <label class="switch">
          <input type="checkbox" value={useRag} onChange={(e) => !loading && setUseRag(e.target.checked)}/>
          <span class="slider round"></span>
        </label>
        
        <button onClick={handleSearch} className="search-button">
          <Search size={20} />
        </button>
      </div>
      <h5>{response}</h5>
      <div className="results-container">
        {loading && <p className="loading-text">Searching...</p>}
        {results.map((result, index) => {
          let split_id = result.doc_id.split("::");
          let link = split_id[0], heading = split_id[1];
          console.log('link', link, heading);
          return (<div key={index} className="result-card">
            <h3 className="result-title"><a class='btn btn-link' href={link} target="_blank">{heading.replaceAll('_', ' ')}</a></h3>
            <p className="result-description">{result.text}</p>
          </div>
        )})}
      </div>
    </div>
  );
}

export default App
