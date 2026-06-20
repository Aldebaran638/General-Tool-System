import type { ContractField, PreviewSegment } from "../types"

interface DocxPreviewProps {
  segments: PreviewSegment[]
  fields: ContractField[]
  values: Record<string, string>
  onChange: (values: Record<string, string>) => void
}

type TextFragment =
  | { type: "text"; value: string }
  | { type: "field"; key: string }

const FIELD_MARKER_REGEX = /\{\{([a-zA-Z0-9_]+)\}\}/g

function parseMarkedText(text: string): TextFragment[] {
  const fragments: TextFragment[] = []
  let lastIndex = 0
  let match: RegExpExecArray | null

  FIELD_MARKER_REGEX.lastIndex = 0
  while ((match = FIELD_MARKER_REGEX.exec(text)) !== null) {
    if (match.index > lastIndex) {
      fragments.push({ type: "text", value: text.slice(lastIndex, match.index) })
    }
    fragments.push({ type: "field", key: match[1] })
    lastIndex = match.index + match[0].length
  }

  if (lastIndex < text.length) {
    fragments.push({ type: "text", value: text.slice(lastIndex) })
  }

  return fragments
}

interface InlineFieldProps {
  fieldKey: string
  field?: ContractField
  value: string
  onChange: (key: string, value: string) => void
}

function InlineField({ fieldKey, field, value, onChange }: InlineFieldProps) {
  const placeholder = field?.label || fieldKey
  const isDate = field?.type === "date"
  const isTextarea = field?.type === "textarea"

  const commonClassName = `
    inline-block align-baseline mx-0.5 px-1 rounded-sm
    border-b-2 border-dashed transition-colors
    focus:outline-none focus:border-primary focus:bg-primary/5
    ${value ? "bg-transparent border-gray-400" : "bg-yellow-100 border-yellow-500"}
  `

  const handleChange = (
    e: React.ChangeEvent<HTMLInputElement | HTMLTextAreaElement>,
  ) => {
    onChange(fieldKey, e.target.value)
  }

  if (isDate) {
    return (
      <input
        type="date"
        value={value || ""}
        onChange={handleChange}
        title={placeholder}
        className={`${commonClassName} min-w-[130px]`}
      />
    )
  }

  if (isTextarea) {
    return (
      <textarea
        value={value || ""}
        onChange={handleChange}
        placeholder={placeholder}
        rows={1}
        title={placeholder}
        className={`${commonClassName} min-w-[200px] resize-none overflow-hidden`}
        onInput={(e) => {
          const target = e.currentTarget as HTMLTextAreaElement
          target.style.height = "auto"
          target.style.height = `${target.scrollHeight}px`
        }}
      />
    )
  }

  const displayValue = value || placeholder
  return (
    <input
      type="text"
      value={value || ""}
      onChange={handleChange}
      placeholder={placeholder}
      title={placeholder}
      className={`${commonClassName} min-w-[60px]`}
      size={Math.max(4, displayValue.length)}
    />
  )
}

export function DocxPreview({
  segments,
  fields,
  values,
  onChange,
}: DocxPreviewProps) {
  const fieldMap = new Map(fields.map((f) => [f.key, f]))

  const handleFieldChange = (key: string, value: string) => {
    onChange({ ...values, [key]: value })
  }

  const renderMarkedText = (text: string) => {
    const fragments = parseMarkedText(text)
    return fragments.map((fragment, idx) => {
      if (fragment.type === "text") {
        return <span key={idx}>{fragment.value}</span>
      }
      return (
        <InlineField
          key={idx}
          fieldKey={fragment.key}
          field={fieldMap.get(fragment.key)}
          value={values[fragment.key] || ""}
          onChange={handleFieldChange}
        />
      )
    })
  }

  return (
    <div className="border rounded-lg p-8 bg-white min-h-[600px] font-serif text-sm leading-relaxed overflow-auto max-h-[calc(100vh-200px)]">
      {segments.map((segment, idx) => {
        if (segment.type === "paragraph" && segment.text) {
          return (
            <p
              key={idx}
              className={`mb-2 whitespace-pre-wrap ${
                segment.style === "Heading 1"
                  ? "text-xl font-bold text-center"
                  : segment.style === "Heading 2"
                    ? "text-lg font-bold mt-4"
                    : ""
              }`}
            >
              {renderMarkedText(segment.text)}
            </p>
          )
        }

        if (segment.type === "table" && segment.rows) {
          return (
            <table key={idx} className="w-full border-collapse my-4">
              <tbody>
                {segment.rows.map((row, ridx) => (
                  <tr key={ridx}>
                    {row.map((cell, cidx) => (
                      <td
                        key={cidx}
                        className="border border-gray-300 px-2 py-1"
                      >
                        {renderMarkedText(cell)}
                      </td>
                    ))}
                  </tr>
                ))}
              </tbody>
            </table>
          )
        }

        return null
      })}
    </div>
  )
}
