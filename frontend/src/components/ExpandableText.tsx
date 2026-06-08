import { useState } from "react";

interface ExpandableTextProps {
  text: string;
  collapsedLines?: number;
  className?: string;
  expandLabel?: string;
  collapseLabel?: string;
}

export default function ExpandableText({
  text,
  collapsedLines = 3,
  className = "",
  expandLabel = "展开全文",
  collapseLabel = "收起",
}: ExpandableTextProps) {
  const [expanded, setExpanded] = useState(false);
  const isLong = text.length > 120;

  if (!isLong) {
    return <p className={className}>{text}</p>;
  }

  return (
    <div>
      <p
        className={className}
        style={
          expanded
            ? undefined
            : {
                display: "-webkit-box",
                WebkitLineClamp: collapsedLines,
                WebkitBoxOrient: "vertical",
                overflow: "hidden",
              }
        }
      >
        {text}
      </p>
      <button
        type="button"
        onClick={() => setExpanded((value) => !value)}
        className="mt-2 text-xs text-cinema-accent hover:text-cinema-accent-dim"
      >
        {expanded ? collapseLabel : expandLabel}
      </button>
    </div>
  );
}
