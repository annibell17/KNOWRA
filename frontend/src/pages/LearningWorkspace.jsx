import React, { useEffect, useState } from "react";
import { apiFetch } from "../apiConfig";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorMessage from "../components/ErrorMessage";

function LearningWorkspace() {
  const [questions, setQuestions] = useState([]);
  const [currentIdx, setCurrentIdx] = useState(0);
  const [status, setStatus] = useState("loading"); // loading|ready|submitting|error
  const [error, setError] = useState("");
  const [selectedOption, setSelectedOption] = useState("");
  const [feedback, setFeedback] = useState(null);
  const [learnerId, setLearnerId] = useState("");

  // Load questions on mount
  useEffect(() => {
    const load = async () => {
      setStatus("loading");
      try {
        const resp = await apiFetch("/cognitive/questions");
        if (!resp.ok) throw new Error(`HTTP ${resp.status}`);
        const json = await resp.json();
        setQuestions(json.questions);
        setStatus("ready");
      } catch (e) {
        setError(e.message);
        setStatus("error");
      }
    };
    load();
  }, []);

  const submitAnswer = async (e) => {
    e.preventDefault();
    if (!learnerId.trim()) {
      setError("Enter Learner ID before answering.");
      return;
    }
    if (!selectedOption) {
      setError("Select an option.");
      return;
    }
    // Prevent duplicate submissions
    if (status === "submitting") return;
    setStatus("submitting");
    setError("");
    const q = questions[currentIdx];
    try {
      const resp = await apiFetch("/cognitive/answer/submit", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          learner_id: learnerId.trim(),
          question_id: q.question_id,
          selected_option_id: selectedOption,
        }),
      });
      if (!resp.ok) {
        const err = await resp.json();
        throw new Error(err.detail || `HTTP ${resp.status}`);
      }
      const result = await resp.json();

      const fb = {
        isCorrect: result.diagnosis?.is_correct ?? false,
        message: result.diagnosis?.message ?? null,
        misconception: result.diagnosis?.diagnosis ?? null,
        knowledgeProb: result.state_update?.knowledge_probability ?? null,
        retention: result.recommendation?.estimated_retention ?? null,
        recommendation: result.recommendation?.recommended_concept_id ?? null,
        processedAt: result.processed_at,
      };
      setFeedback(fb);
      setStatus("ready");
    } catch (e) {
      setError(e.message);
      setStatus("ready");
    }
  };

  if (status === "loading") return <LoadingSpinner />;
  if (status === "error") return <ErrorMessage msg={error} />;
  if (!questions.length) return <p className="p-8">No questions available.</p>;

  const q = questions[currentIdx];

  return (
    <div className="p-8 max-w-3xl mx-auto">
      <h2 className="text-2xl font-semibold mb-4 text-primary">Learning Workspace</h2>

      {/* Learner ID entry */}
      <div className="mb-4">
        <label className="block text-sm font-medium text-primary">Learner ID</label>
        <input
          type="text"
          className="mt-1 block w-full border rounded px-3 py-2"
          placeholder="e.g. demo_learner_01"
          value={learnerId}
          onChange={(e) => setLearnerId(e.target.value)}
        />
      </div>

      <form onSubmit={submitAnswer} className="space-y-6">
        <fieldset className="border border-semantic p-4 rounded bg-card">
          <legend className="text-lg font-medium text-primary">{q.prompt}</legend>
          <div className="mt-2 space-y-2">
            {q.options.map((opt) => (
              <label key={opt.option_id} className="flex items-center space-x-2">
                <input
                  type="radio"
                  name="option"
                  value={opt.option_id}
                  checked={selectedOption === opt.option_id}
                  onChange={() => setSelectedOption(opt.option_id)}
                />
                <span>{opt.text}</span>
              </label>
            ))}
          </div>
        </fieldset>
        <button
          type="submit"
          disabled={status === "submitting"}
          className="bg-primary-action text-white rounded px-4 py-2 hover:bg-primary-action/90"
        >
          {status === "submitting" ? "Submitting…" : "Submit Answer"}
        </button>
      </form>

      {/* Show submission errors when not in loading/error state */}
      {error && status !== "error" && <ErrorMessage msg={error} />}

      {feedback && (
        <section className="mt-6 p-4 border border-semantic rounded bg-card">
          <h3 className="font-medium text-primary mb-2">Feedback</h3>
          <p><strong>Correct?</strong> {feedback.isCorrect ? "Yes" : "No"}</p>
          {feedback.message && (
            <p><strong>Message:</strong> {feedback.message}</p>
          )}
          {feedback.misconception && (
            <p><strong>Misconception:</strong> {feedback.misconception}</p>
          )}
          {feedback.knowledgeProb !== null && (
            <p><strong>Knowledge probability:</strong> {(feedback.knowledgeProb * 100).toFixed(1)}%</p>
          )}
          {feedback.retention !== null && (
            <p><strong>Retention (est.):</strong> {(feedback.retention * 100).toFixed(1)}%</p>
          )}
          {feedback.recommendation && (
            <p><strong>Recommended next concept:</strong> {feedback.recommendation}</p>
          )}
          <p className="text-sm text-primary mt-2">
            Processed at: {new Date(feedback.processedAt).toLocaleString()}
          </p>
        </section>
      )}

      {currentIdx < questions.length - 1 && (
        <button
          className="mt-4 text-indigo-600 underline"
          onClick={() => {
            setCurrentIdx(currentIdx + 1);
            setSelectedOption("");
            setFeedback(null);
            setError("");
          }}
        >
          Next question →
        </button>
      )}
    </div>
  );
}

export default LearningWorkspace;
