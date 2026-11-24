import React from "react";

export default function SectionHeader({ title }) {
  return (
    <h2 className="text-3xl font-bold mb-4 border-b border-semantic pb-2" style={{ fontFamily: "'Lora', serif" }}>
      {title}
    </h2>
  );
}

