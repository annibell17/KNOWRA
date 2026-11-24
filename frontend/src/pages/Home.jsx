import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../apiConfig";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorMessage from "../components/ErrorMessage";

function Home() {
  const [modules, setModules] = useState(null);
  const [status, setStatus] = useState("idle"); // idle|loading|error
  const [error, setError] = useState("");

  useEffect(() => {
    const fetchModules = async () => {
      setStatus("loading");
      try {
        const resp = await apiFetch("/cognitive/modules");
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const json = await resp.json();
        setModules(json);
        setStatus("idle");
      } catch (e) {
        setError(e.message);
        setStatus("error");
      }
    };
    fetchModules();
  }, []);

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h1 className="text-4xl font-bold mb-6 text-gray-800">Welcome to KNOWRA</h1>

      {status === "loading" && <LoadingSpinner />}
      {status === "error" && <ErrorMessage msg={error} />}

      {modules && (
        <section className="mt-8">
          <h2 className="text-2xl font-semibold mb-4 text-indigo-700">
            Available Learning Module
          </h2>
          <div className="p-4 border border-gray-200 rounded bg-white">
            <h3 className="text-xl font-medium text-gray-900">
              {modules.title}
            </h3>
            <p className="text-gray-600 mb-2">{modules.description}</p>
            <Link
              to="/learn"
              className="inline-block mt-2 text-indigo-600 hover:underline"
            >
              Start Learning →
            </Link>
          </div>
        </section>
      )}

      <section className="mt-12">
        <Link to="/progress" className="text-indigo-600 font-medium underline">
          View your progress →
        </Link>
      </section>
    </div>
  );
}

export default Home;
