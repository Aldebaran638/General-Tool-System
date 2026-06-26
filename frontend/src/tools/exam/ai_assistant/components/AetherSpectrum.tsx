import { useEffect, useRef } from "react"

export type AetherState = "idle" | "thinking" | "tool-calling"

interface AetherSpectrumProps {
  state?: AetherState
  direction?: 1 | -1
  theme?: "dark" | "light"
  size?: number
  barsCount?: number
  innerRadius?: number
  centerRadius?: number
  idleSpeed?: number
  idleGlow?: number
  idleBarBrightness?: number
  thinkingSpeed?: number
  thinkingGlow?: number
  thinkingAmplitude?: number
  thinkingSync?: number
  toolCallingSpeed?: number
  toolCallingGlow?: number
  toolCallingCompression?: number
  className?: string
}

export function AetherSpectrum({
  state = "idle",
  direction = 1,
  theme = "dark",
  size = 75,
  barsCount = 16,
  innerRadius = 13.0,
  centerRadius = 6.0,
  idleSpeed = 5.0,
  idleGlow = 0.45,
  idleBarBrightness = 1.0,
  thinkingSpeed = 1.6,
  thinkingGlow = 2.0,
  thinkingAmplitude = 12.0,
  thinkingSync = 1.0,
  toolCallingSpeed = 2.5,
  toolCallingGlow = 2.5,
  toolCallingCompression = 44,
  className = "",
}: AetherSpectrumProps) {
  const canvasRef = useRef<HTMLCanvasElement>(null)

  const stateRef = useRef({
    currentHeights: Array(barsCount).fill(8),
    targetHeights: Array(barsCount).fill(8),
    centerPulse: 1.0,
    targetCenterPulse: 1.0,
    time: 0,
    lastTimestamp: 0,
    currentState: state,
    currentBarsCount: barsCount,
    currentSpeed: idleSpeed,
    currentGlow: idleGlow,
    currentCompressionRad: (toolCallingCompression * Math.PI) / 180,
    currentBarBrightness: idleBarBrightness,
    currentAmplitude: thinkingAmplitude,
    currentSync: thinkingSync,
  })

  useEffect(() => {
    stateRef.current.currentState = state
    stateRef.current.currentBarsCount = barsCount
    stateRef.current.currentAmplitude = thinkingAmplitude
    stateRef.current.currentSync = thinkingSync

    if (stateRef.current.currentHeights.length !== barsCount) {
      stateRef.current.currentHeights = Array(barsCount).fill(8)
      stateRef.current.targetHeights = Array(barsCount).fill(8)
    }
  }, [state, barsCount, thinkingAmplitude, thinkingSync])

  useEffect(() => {
    const canvas = canvasRef.current
    if (!canvas) return
    const ctx = canvas.getContext("2d")
    if (!ctx) return

    let animationFrameId: number
    stateRef.current.lastTimestamp = performance.now()

    const getIdleHeight = (index: number, totalBars: number) => {
      const angle = (index * 2 * Math.PI) / totalBars
      const harmonic1 = Math.sin(angle * 3) * 2.8
      const harmonic2 = Math.cos(angle * 5) * 1.8
      const harmonic3 = Math.sin(angle * 7) * 0.8
      const base = 9.0
      return Math.max(3.5, base + harmonic1 + harmonic2 + harmonic3)
    }

    const render = (timestamp: number) => {
      const dt = Math.max(0, Math.min(0.1, (timestamp - stateRef.current.lastTimestamp) / 1000))
      stateRef.current.lastTimestamp = timestamp

      const info = stateRef.current
      const totalBars = info.currentBarsCount || barsCount

      let targetSpeed = idleSpeed
      let targetGlow = idleGlow
      let targetCompressionRad = (toolCallingCompression * Math.PI) / 180
      let targetBarBrightness = idleBarBrightness

      if (info.currentState === "idle") {
        targetSpeed = idleSpeed
        targetGlow = idleGlow
        targetBarBrightness = idleBarBrightness
      } else if (info.currentState === "thinking") {
        targetSpeed = thinkingSpeed
        targetGlow = thinkingGlow
        targetBarBrightness = 1.0
      } else if (info.currentState === "tool-calling") {
        targetSpeed = toolCallingSpeed
        targetGlow = toolCallingGlow
        targetBarBrightness = 0.9
      }

      const transitionRate = 4.0
      const paramLerpFactor = 1.0 - Math.exp(-transitionRate * dt)
      info.currentSpeed += (targetSpeed - info.currentSpeed) * paramLerpFactor
      info.currentGlow += (targetGlow - info.currentGlow) * paramLerpFactor
      info.currentCompressionRad += (targetCompressionRad - info.currentCompressionRad) * paramLerpFactor
      info.currentBarBrightness += (targetBarBrightness - info.currentBarBrightness) * paramLerpFactor

      info.time += dt * info.currentSpeed
      const t = info.time

      if (info.currentState === "idle") {
        for (let i = 0; i < totalBars; i++) {
          const baseH = getIdleHeight(i, totalBars)
          const angle = (i * 2 * Math.PI) / totalBars
          const breath1 = Math.sin(angle * 2 - t * 0.6) * 1.2
          const breath2 = Math.cos(angle * 3 + t * 0.3) * 0.6
          info.targetHeights[i] = Math.max(3.0, baseH + breath1 + breath2)
        }
        info.targetCenterPulse = 1.0 + Math.sin(t * 1.5) * 0.04
      } else if (info.currentState === "thinking") {
        for (let i = 0; i < totalBars; i++) {
          const baseH = getIdleHeight(i, totalBars)
          const phaseOffset = i * info.currentSync * 2.0
          const audioWave = Math.sin(t * 3.5 - phaseOffset) * 0.5 + 0.5
          info.targetHeights[i] = Math.max(2.0, baseH * 0.4 + audioWave * info.currentAmplitude)
        }
        info.targetCenterPulse = 1.02 + Math.abs(Math.sin(t * 3.0)) * 0.06
      } else if (info.currentState === "tool-calling") {
        const sweepAngle = (t * 2.2 * direction) % (Math.PI * 2)
        for (let i = 0; i < totalBars; i++) {
          const barAngle = (i * 2 * Math.PI) / totalBars
          let diff = Math.abs(barAngle - sweepAngle)
          if (diff > Math.PI) diff = Math.PI * 2 - diff

          const cosFactor = (Math.cos(diff) + 1.0) / 2.0
          const tideHeight = 4.0 + cosFactor * 10.5
          const jitter = Math.sin(i * 1.2 + t * 4.5) * 0.6
          info.targetHeights[i] = Math.max(2.5, tideHeight + jitter)
        }
        info.targetCenterPulse = 1.05 + Math.sin(t * 5.0) * 0.08
      }

      const heightLerpFactor = 1.0 - Math.exp(-(transitionRate * 2.0) * dt)
      for (let i = 0; i < totalBars; i++) {
        const curr = info.currentHeights[i]
        const target = info.targetHeights[i]
        info.currentHeights[i] = curr + (target - curr) * heightLerpFactor
      }
      info.centerPulse += (info.targetCenterPulse - info.centerPulse) * heightLerpFactor

      const logicalSize = 80
      const cx = logicalSize / 2
      const cy = logicalSize / 2

      ctx.clearRect(0, 0, canvas.width, canvas.height)
      const isDark = theme === "dark"
      const glowColor = isDark ? "rgba(99, 102, 241, 0.85)" : "rgba(79, 70, 229, 0.65)"

      if (info.currentGlow > 0.05) {
        ctx.save()
        const auraRadius = innerRadius * 2.4
        const auraGrad = ctx.createRadialGradient(cx, cy, innerRadius * 0.4, cx, cy, auraRadius)
        if (isDark) {
          auraGrad.addColorStop(0, `rgba(99, 102, 241, ${0.14 * info.currentGlow})`)
          auraGrad.addColorStop(1, "rgba(99, 102, 241, 0)")
        } else {
          auraGrad.addColorStop(0, `rgba(79, 70, 229, ${0.18 * info.currentGlow})`)
          auraGrad.addColorStop(0.5, `rgba(168, 85, 247, ${0.08 * info.currentGlow})`)
          auraGrad.addColorStop(1, "rgba(79, 70, 229, 0)")
        }
        ctx.fillStyle = auraGrad
        ctx.beginPath()
        ctx.arc(cx, cy, auraRadius, 0, Math.PI * 2)
        ctx.fill()
        ctx.restore()
      }

      ctx.save()
      const dotRadius = centerRadius * info.centerPulse

      if (info.currentGlow > 0.05) {
        ctx.shadowBlur = (isDark ? 12 : 14) * info.currentGlow
        ctx.shadowColor = glowColor
      }

      const dotGrad = ctx.createRadialGradient(cx - 0.5, cy - 0.5, 0, cx, cy, dotRadius)
      if (isDark) {
        dotGrad.addColorStop(0, "#ffffff")
        dotGrad.addColorStop(0.25, "#c7d2fe")
        dotGrad.addColorStop(0.7, "#6366f1")
        dotGrad.addColorStop(1, "#4338ca")
      } else {
        dotGrad.addColorStop(0, "#ffffff")
        dotGrad.addColorStop(0.3, "#818cf8")
        dotGrad.addColorStop(0.85, "#4f46e5")
        dotGrad.addColorStop(1, "#3730a3")
      }

      ctx.fillStyle = dotGrad
      ctx.beginPath()
      ctx.arc(cx, cy, dotRadius, 0, Math.PI * 2)
      ctx.fill()
      ctx.restore()

      ctx.save()
      ctx.lineCap = "round"
      ctx.lineWidth = 1.8

      for (let i = 0; i < totalBars; i++) {
        const angle = (i * 2 * Math.PI) / totalBars
        const h = info.currentHeights[i]
        const outerRadius = innerRadius + h

        const cos = Math.cos(angle)
        const sin = Math.sin(angle)

        const x1 = cx + innerRadius * cos
        const y1 = cy + innerRadius * sin
        const x2 = cx + outerRadius * cos
        const y2 = cy + outerRadius * sin

        let opacity = 0.25
        let strokeStyle: string | CanvasGradient = isDark ? "#3f3f46" : "#cbd5e1"

        if (info.currentState === "idle") {
          const baseOpacity = 0.35 + (h / 15) * 0.65
          opacity = baseOpacity * info.currentBarBrightness
          strokeStyle = isDark ? "#525252" : "#a3a3a3"
        } else {
          opacity = (0.22 + 0.65) * Math.min(1.5, info.currentGlow * 0.85 + 0.5) * info.currentBarBrightness

          const lineGrad = ctx.createLinearGradient(x1, y1, x2, y2)
          if (isDark) {
            lineGrad.addColorStop(0, "#4f46e5")
            lineGrad.addColorStop(0.5, "#6366f1")
            lineGrad.addColorStop(1, "#a5b4fc")
          } else {
            lineGrad.addColorStop(0, "#312e81")
            lineGrad.addColorStop(0.4, "#4f46e5")
            lineGrad.addColorStop(0.8, "#6366f1")
            lineGrad.addColorStop(1, "#a5b4fc")
          }
          strokeStyle = lineGrad

          const ratio = Math.min(1.0, Math.max(0.0, (h - 6.0) / 10.0))
          if (ratio > 0.6 && info.currentGlow > 0) {
            ctx.shadowColor = glowColor
            ctx.shadowBlur = (isDark ? 4 : 6) * ratio * info.currentGlow
          } else {
            ctx.shadowBlur = 0
          }
        }

        ctx.strokeStyle = strokeStyle
        ctx.globalAlpha = opacity

        ctx.beginPath()
        ctx.moveTo(x1, y1)
        ctx.lineTo(x2, y2)
        ctx.stroke()
      }
      ctx.restore()

      animationFrameId = requestAnimationFrame(render)
    }

    const resizeCanvas = () => {
      const dpr = window.devicePixelRatio || 1
      const logicalSize = 80
      canvas.width = logicalSize * dpr
      canvas.height = logicalSize * dpr
      ctx.scale(dpr, dpr)
    }

    resizeCanvas()
    window.addEventListener("resize", resizeCanvas)
    animationFrameId = requestAnimationFrame(render)

    return () => {
      cancelAnimationFrame(animationFrameId)
      window.removeEventListener("resize", resizeCanvas)
    }
  }, [
    state,
    direction,
    theme,
    barsCount,
    innerRadius,
    centerRadius,
    idleSpeed,
    idleGlow,
    idleBarBrightness,
    thinkingSpeed,
    thinkingGlow,
    thinkingAmplitude,
    thinkingSync,
    toolCallingSpeed,
    toolCallingGlow,
    toolCallingCompression,
  ])

  return (
    <div
      className={`relative flex items-center justify-center select-none ${className}`}
      style={{ width: `${size}px`, height: `${size}px` }}
    >
      <canvas
        ref={canvasRef}
        style={{ width: "100%", height: "100%" }}
        className="overflow-visible"
      />
    </div>
  )
}
