import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import LearnerProgress from "./LearnerProgress";
import Home from "./pages/Home";
import LearningWorkspace from "./pages/LearningWorkspace";
import "./index.css";

function App() {
  return (
    <Router>
      <nav className="p-4 bg-gray-100 flex gap-4">
        <Link to="/" className="text-indigo-600 font-medium">Home</Link>
        <Link to="/learn" className="text-indigo-600 font-medium">Learn</Link>
        <Link to="/progress" className="text-indigo-600 font-medium">Progress</Link>
      </nav>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/learn" element={<LearningWorkspace />} />
        <Route path="/progress" element={<LearnerProgress />} />
      </Routes>
    </Router>
  );
}

export default App;
