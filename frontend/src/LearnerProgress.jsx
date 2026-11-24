import React, { useState } from "react";
import { apiFetch } from "./apiConfig";

function LearnerProgress() {
  const [learnerId, setLearnerId] = useState("");
  const [status, setStatus] = useState("idle"); // idle | loading | success | error | notfound | empty
  const [data, setData] = useState(null);
  const [errorMsg, setErrorMsg] = useState("");

  const fetchProgress = async (id) => {
    if (!id) return;
    setStatus("loading");
    setErrorMsg("");
    setData(null);
    try {
      const resp = await apiFetch(`/cognitive/learners/${encodeURIComponent(id)}/progress`);
      if (resp.status === 404) {
        setStatus("notfound");
        return;
      }
      if (!resp.ok) {
        setStatus("error");
        setErrorMsg(`HTTP ${resp.status}`);
        return;
      }
      const json = await resp.json();
      // Empty state when no concepts returned (should be caught earlier but guard anyway)
      if (!json.concepts || json.concepts.length === 0) {
        setStatus("empty");
      } else {
        setData(json);
        setStatus("success");
      }
    } catch (e) {
      setStatus("error");
      setErrorMsg(e.message);
    }
  };

  const handleSubmit = (e) => {
    e.preventDefault();
    fetchProgress(learnerId.trim());
  };

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h1 className="text-3xl font-bold mb-4 text-center text-indigo-800">Learner Progress</h1>
      <form onSubmit={handleSubmit} className="flex gap-2 mb-6">
        <input
          type="text"
          placeholder="Learner ID"
          value={learnerId}
          onChange={(e) => setLearnerId(e.target.value)}
          className="flex-1 border rounded px-3 py-2"
          required
        />
        <button type="submit" className="bg-indigo-600 text-white rounded px-4 py-2">
          Load
        </button>
      </form>

      {status === "loading" && <p className="text-gray-600">Loading...</p>}
      {status === "error" && <p className="text-red-600">Error: {errorMsg}</p>}
      {status === "notfound" && <p className="text-yellow-600">Learner progress not found.</p>}
      {status === "empty" && <p className="text-gray-600">No progress data available.</p>}

      {status === "success" && data && (
        <div className="space-y-4">
          <p><strong>Learner ID:</strong> {data.learner_id}</p>
          <p><strong>Total Concepts Attempted:</strong> {data.total_concepts_attempted}</p>
          <table className="w-full table-auto border-collapse border border-gray-300">
            <thead className="bg-gray-200">
              <tr>
                <th className="border p-2">Concept</th>
                <th className="border p-2">Knowledge %</th>
                <th className="border p-2">Attempts</th>
                <th className="border p-2">Correct</th>
                <th className="border p-2">Retention</th>
              </tr>
            </thead>
            <tbody>
              {data.concepts.map((c) => (
                <tr key={c.concept_id} className="odd:bg-white even:bg-gray-50">
                  <td className="border p-2">{c.concept_name}</td>
                  <td className="border p-2">{(c.knowledge_probability * 100).toFixed(1)}%</td>
                  <td className="border p-2">{c.attempts}</td>
                  <td className="border p-2">{c.correct_attempts}</td>
                  <td className="border p-2">
  {typeof c.retention?.estimated_retention === "number"
    ? `${(c.retention.estimated_retention * 100).toFixed(1)}%`
    : "-"}
</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </div>
  );
}

export default LearnerProgress;
