import { Plus, X } from "lucide-react";
import { useState } from "react";
import ErrorMessage from "./ErrorMessage";

const MAX_ITEMS = 20;
const MAX_ITEM_LENGTH = 80;

export default function TagInput({
  id,
  label,
  value,
  onChange,
  placeholder,
  description,
  suggestions = [],
  error,
  disabled = false,
}) {
  const [inputValue, setInputValue] = useState("");
  const [inputError, setInputError] = useState("");
  const errorId = `${id}-error`;

  const addItem = (rawValue) => {
    const item = rawValue.trim().replace(/\s+/g, " ");
    if (!item) {
      return;
    }
    if (item.length > MAX_ITEM_LENGTH) {
      setInputError(`Each item must be ${MAX_ITEM_LENGTH} characters or fewer.`);
      return;
    }
    if (value.length >= MAX_ITEMS) {
      setInputError(`You can add up to ${MAX_ITEMS} items.`);
      return;
    }
    if (value.some((existing) => existing.toLowerCase() === item.toLowerCase())) {
      setInputError("This item has already been added.");
      return;
    }

    onChange([...value, item]);
    setInputValue("");
    setInputError("");
  };

  const removeItem = (itemToRemove) => {
    onChange(value.filter((item) => item !== itemToRemove));
    setInputError("");
  };

  const handleKeyDown = (event) => {
    if (event.key === "Enter" || event.key === ",") {
      event.preventDefault();
      addItem(inputValue);
    }
  };

  const availableSuggestions = suggestions.filter(
    (suggestion) =>
      !value.some((item) => item.toLowerCase() === suggestion.toLowerCase()),
  );

  return (
    <div>
      <label htmlFor={id} className="block text-sm font-semibold text-slate-800">
        {label}
      </label>
      {description ? (
        <p className="mt-1 text-sm leading-6 text-slate-600">{description}</p>
      ) : null}

      <div className="mt-2 flex gap-2">
        <input
          id={id}
          type="text"
          value={inputValue}
          onChange={(event) => {
            setInputValue(event.target.value);
            setInputError("");
          }}
          onKeyDown={handleKeyDown}
          placeholder={placeholder}
          disabled={disabled}
          aria-invalid={error || inputError ? "true" : "false"}
          aria-describedby={error || inputError ? errorId : undefined}
          className="min-w-0 flex-1 rounded-lg border border-slate-300 bg-white px-3 py-3 text-sm text-slate-950 shadow-sm outline-none transition placeholder:text-slate-400 focus:border-brand-600 focus:ring-4 focus:ring-brand-100 disabled:bg-slate-50"
        />
        <button
          type="button"
          onClick={() => addItem(inputValue)}
          disabled={disabled || !inputValue.trim()}
          aria-label={`Add ${label.toLowerCase()} item`}
          className="inline-flex h-11 w-11 shrink-0 items-center justify-center rounded-lg border border-brand-600 text-brand-700 transition hover:bg-brand-50 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600 disabled:cursor-not-allowed disabled:border-slate-200 disabled:text-slate-400"
        >
          <Plus aria-hidden="true" className="h-5 w-5" />
        </button>
      </div>

      {value.length ? (
        <ul className="mt-3 flex flex-wrap gap-2" aria-label={`${label} entries`}>
          {value.map((item) => (
            <li
              key={item.toLowerCase()}
              className="inline-flex min-w-0 items-center gap-2 rounded-lg bg-brand-50 px-3 py-2 text-sm font-medium text-brand-700"
            >
              <span className="break-words">{item}</span>
              <button
                type="button"
                onClick={() => removeItem(item)}
                disabled={disabled}
                aria-label={`Remove ${item}`}
                className="shrink-0 rounded text-brand-700 hover:text-red-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
              >
                <X aria-hidden="true" className="h-4 w-4" />
              </button>
            </li>
          ))}
        </ul>
      ) : null}

      {availableSuggestions.length ? (
        <div className="mt-3 flex flex-wrap gap-2" aria-label={`Suggested ${label}`}>
          {availableSuggestions.map((suggestion) => (
            <button
              key={suggestion}
              type="button"
              onClick={() => addItem(suggestion)}
              disabled={disabled}
              className="rounded-lg border border-slate-300 bg-white px-3 py-2 text-xs font-semibold text-slate-700 transition hover:border-brand-500 hover:text-brand-700 focus-visible:outline focus-visible:outline-2 focus-visible:outline-offset-2 focus-visible:outline-brand-600"
            >
              + {suggestion}
            </button>
          ))}
        </div>
      ) : null}

      <ErrorMessage id={errorId} message={error || inputError} />
    </div>
  );
}
