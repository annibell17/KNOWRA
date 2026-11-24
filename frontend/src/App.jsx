import React from "react";
import { BrowserRouter as Router, Routes, Route, Link } from "react-router-dom";
import LearnerProgress from "./LearnerProgress";
import Home from "./pages/Home";
import LearningWorkspace from "./pages/LearningWorkspace";
import ThemeToggle from "./components/ThemeToggle";
import "./index.css";

function App() {
  return (
    <Router>
      <nav className="p-4 bg-page flex gap-4 items-center">
        <Link to="/" className="text-primary font-medium">Home</Link>
        <Link to="/learn" className="text-primary font-medium">Learn</Link>
        <Link to="/progress" className="text-primary font-medium">Progress</Link>
        <ThemeToggle />
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

