import React, { useState, useEffect } from "react";

export default function ThemeToggle() {
  const [theme, setTheme] = useState(
    () => localStorage.getItem("knowa-theme") || "autumn-light"
  );

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    localStorage.setItem("knowa-theme", theme);
  }, [theme]);

  const changePalette = () => {
    setTheme((current) =>
      current.startsWith("autumn")
        ? current.replace("autumn", "spring")
        : current.replace("spring", "autumn")
    );
  };

  const changeMode = () => {
    setTheme((current) =>
      current.endsWith("light")
        ? current.replace("light", "dark")
        : current.replace("dark", "light")
    );
  };

  const buttonStyle = {
    backgroundColor: "var(--color-card-bg)",
    color: "var(--color-primary-text)",
    borderColor: "var(--color-border)"
  };

  return (
    <div className="ml-auto flex items-center gap-2 flex-wrap">
      <button
        type="button"
        onClick={changePalette}
        style={buttonStyle}
        className="px-3 py-2 text-sm rounded border shadow-sm transition-colors"
      >
        {theme.startsWith("autumn") ? "Spring palette" : "Autumn palette"}
      </button>

      <button
        type="button"
        onClick={changeMode}
        style={buttonStyle}
        className="px-3 py-2 text-sm rounded border shadow-sm transition-colors"
      >
        {theme.endsWith("light") ? "Dark mode" : "Light mode"}
      </button>
    </div>
  );
}
