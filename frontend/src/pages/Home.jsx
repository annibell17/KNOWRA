import React, { useEffect, useState } from "react";
import { Link } from "react-router-dom";
import { apiFetch } from "../apiConfig";
import LoadingSpinner from "../components/LoadingSpinner";
import ErrorMessage from "../components/ErrorMessage";
import Button from "../components/Button";
import Card from "../components/Card";
import SectionHeader from "../components/SectionHeader";

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
    <div className="p-8 max-w-5xl mx-auto space-y-12">
      {/* Hero Section */}
      <section className="bg-hero text-hero border border-semantic rounded-lg p-8 text-center space-y-4">
          <h1 className="text-5xl font-bold" style={{ fontFamily: "'Lora', serif" }}>
            KNOWRA
          </h1>
          <p className="text-xl" style={{ fontFamily: "'Inter', sans-serif" }}>
            Welcome, learner. Discover adaptive learning tailored to you.
          </p>
          <p className="text-lg" style={{ fontFamily: "'Inter', sans-serif" }}>
            KNOWRA uses cognitive science to identify gaps and recommend personalised pathways.
          </p>
          {/* Botanical decorative SVG with accent colour */}
          <svg viewBox="0 0 100 20" className="mx-auto mb-4" width="200" height="40" fill="none" stroke="currentColor" strokeWidth="1">
            <path d="M10 10 C 20 0, 30 20, 40 10 S 70 0, 80 10" />
          </svg>
          <Button variant="primary" onClick={() => { window.location.href = "/learn"; }}>
            Continue Learning
          </Button>
        </section>
      {/* Modules Section */}
      {status === "loading" && <LoadingSpinner />}
      {status === "error" && <ErrorMessage msg={error} />}

      {modules && (
        <section className="space-y-8">
          <SectionHeader title="Available Learning Module" />
          <div className="grid md:grid-cols-2 gap-6">
            <Card className="bg-secondary-surface text-secondary p-6 flex flex-col justify-between h-full">
              <div>
                <h3 className="text-2xl font-semibold mb-2" style={{ fontFamily: "'Lora', serif" }}>
                  {modules.title}
                </h3>
                <p className="mb-4" style={{ fontFamily: "'Inter', sans-serif" }}>
                  {modules.description}
                </p>
              </div>
              <Link
                to="/learn"
                className="mt-auto text-primary-action underline font-medium"
              >
                Start Learning →
              </Link>
            </Card>
          </div>
        </section>
      )}

      {/* Philosophy Section */}
      <section className="bg-philosophy text-primary border border-semantic rounded-lg p-8 space-y-4">
        <SectionHeader title="Our Learning Philosophy" />
        <p style={{ fontFamily: "'Inter', sans-serif" }}>
          KNOWRA blends cognitive research with modern technology to create a thoughtful, data‑driven learning experience. We focus on understanding each learner’s knowledge state, identifying misconceptions, and guiding them towards deeper mastery.
        </p>
      </section>

      {/* Progress link */}
      <section className="text-center">
        <Link
          to="/progress"
          className="text-primary-action underline font-medium"
        >
          View your progress →
        </Link>
      </section>
    </div>
  );
}

export default Home;

