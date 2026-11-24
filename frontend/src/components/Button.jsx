import React from "react";

export default function Button({ children, variant = "primary", onClick, disabled }) {
  const base = "px-4 py-2 rounded focus:outline-none focus:ring-2 focus:ring-offset-2";
  const styles = variant === "primary"
    ? "bg-primary-action text-white hover:bg-primary-action/90 disabled:opacity-50"
    : "bg-secondary-action text-white hover:bg-secondary-action/90 disabled:opacity-50";
  return (
    <button
      className={`${base} ${styles}`}
      onClick={onClick}
      disabled={disabled}
    >
      {children}
    </button>
  );
}
