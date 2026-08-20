export const DISCLOSURE =
  "For education and research only. Not investment advice. Past or simulated performance does not guarantee future results.";

export default function Disclosure({
  children = DISCLOSURE,
  compact = false,
}: {
  children?: React.ReactNode;
  compact?: boolean;
}) {
  return (
    <div
      className="disclosure"
      style={compact ? { padding: ".7rem" } : undefined}
    >
      {children}
    </div>
  );
}
