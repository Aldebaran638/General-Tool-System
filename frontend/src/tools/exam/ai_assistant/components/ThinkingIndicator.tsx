import { AetherSpectrum } from "./AetherSpectrum"

interface ThinkingIndicatorProps {
  state?: "thinking" | "tool-calling"
  label?: string
}

export function ThinkingIndicator({
  state = "thinking",
  label = state === "thinking" ? "NEURAL_THINKING" : "TOOL_RUNNING",
}: ThinkingIndicatorProps) {
  return (
    <div className="flex items-center gap-2 py-2">
      <AetherSpectrum state={state} size={28} />
      <span className="text-[10px] font-mono text-primary uppercase tracking-wider">
        {label}
      </span>
    </div>
  )
}
