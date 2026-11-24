
export default function Card({ children, className = "" }) {
  return (
    <div className={`bg-card border border-semantic rounded shadow-md p-4 ${className}`.trim()}>
      {children}
    </div>
  );
}
