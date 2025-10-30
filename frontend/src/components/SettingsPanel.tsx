import { useEffect, useMemo, useState } from "react";

import type { AgentSettings } from "@/types";
import { CopyIcon, EditIcon, TrashIcon } from "./Icons";

const SUPPORTED_TYPES = ["string", "number", "integer", "boolean", "array"] as const;
type SupportedType = (typeof SUPPORTED_TYPES)[number];

const createFieldId = () =>
  typeof crypto !== "undefined" && typeof crypto.randomUUID === "function"
    ? crypto.randomUUID()
    : Math.random().toString(36).slice(2);

interface SchemaField {
  id: string;
  name: string;
  type: SupportedType;
  description: string;
  enumValues: string;
  required: boolean;
}

interface SettingsPanelProps {
  isOpen: boolean;
  settings: AgentSettings;
  onClose: () => void;
  onSave: (settings: AgentSettings) => void;
  onReset: () => void;
}

interface SchemaFieldEditorProps {
  initial: Omit<SchemaField, "id">;
  onSave: (field: Omit<SchemaField, "id">) => void;
  onCancel: () => void;
}

function SchemaFieldEditor({ initial, onSave, onCancel }: SchemaFieldEditorProps) {
  const [field, setField] = useState(initial);

  const handleChange = <K extends keyof typeof field>(key: K, value: (typeof field)[K]) => {
    setField(prev => ({ ...prev, [key]: value }));
  };

  const handleSubmit = () => {
    if (!field.name.trim()) {
      window.alert("Назва поля не може бути порожньою.");
      return;
    }
    onSave({ ...field, name: field.name.trim() });
  };

  return (
    <div className="schema-editor-overlay" role="dialog" aria-modal="true">
      <div className="schema-editor">
        <header className="schema-editor__header">
          <h3 className="settings-section__title">
            {initial.name === "newField" ? "Додавання нового поля" : `Редагування поля: ${initial.name}`}
          </h3>
          <button type="button" className="icon-button" onClick={onCancel} aria-label="Close editor">
            ×
          </button>
        </header>
        <div className="schema-editor__body">
          <div className="settings-field">
            <label htmlFor="field-name">Назва поля (ключ JSON)</label>
            <input
              id="field-name"
              type="text"
              value={field.name}
              onChange={event => handleChange("name", event.target.value)}
              placeholder="eventType"
            />
          </div>
          <div className="settings-field">
            <label htmlFor="field-type">Тип даних</label>
            <select
              id="field-type"
              value={field.type}
              onChange={event => handleChange("type", event.target.value as SupportedType)}
            >
              {SUPPORTED_TYPES.map(type => (
                <option key={type} value={type}>
                  {type}
                </option>
              ))}
            </select>
          </div>
          <div className="settings-field">
            <label htmlFor="field-desc">Опис поля (для AI)</label>
            <input
              id="field-desc"
              type="text"
              value={field.description}
              onChange={event => handleChange("description", event.target.value)}
              placeholder="Опишіть призначення поля"
            />
          </div>
          {field.type === "string" ? (
            <div className="settings-field">
              <label htmlFor="field-enum">Допустимі значення (через кому)</label>
              <input
                id="field-enum"
                type="text"
                value={field.enumValues}
                onChange={event => handleChange("enumValues", event.target.value)}
                placeholder="value1, value2, value3"
              />
            </div>
          ) : null}
          <div className="settings-field" style={{ alignItems: "center" }}>
            <label>
              <input
                type="checkbox"
                checked={field.required}
                onChange={event => handleChange("required", event.target.checked)}
              />
              <span style={{ marginLeft: 8 }}>Обов'язкове поле</span>
            </label>
          </div>
        </div>
        <footer className="schema-editor__footer">
          <button type="button" className="button-secondary" onClick={onCancel}>
            Скасувати
          </button>
          <button type="button" className="button-primary" onClick={handleSubmit}>
            Зберегти поле
          </button>
        </footer>
      </div>
    </div>
  );
}

const NEW_FIELD_TEMPLATE: Omit<SchemaField, "id"> = {
  name: "newField",
  type: "string",
  description: "",
  enumValues: "",
  required: true,
};

function parseSchema(schemaString: string): SchemaField[] {
  try {
    const schema = JSON.parse(schemaString) as {
      type?: string;
      properties?: Record<string, { type?: string; description?: string; enum?: string[]; items?: { type?: string } }>;
      required?: string[];
    };

    if (!schema || schema.type !== "object" || !schema.properties) {
      return [];
    }

    const requiredSet = new Set(schema.required ?? []);

    return Object.entries(schema.properties).map(([name, value]) => ({
      id: createFieldId(),
      name,
      type: (value.type ?? "string") as SupportedType,
      description: value.description ?? "",
      enumValues: Array.isArray(value.enum) ? value.enum.join(", ") : "",
      required: requiredSet.has(name),
    }));
  } catch (error) {
    console.error("Unable to parse schema", error);
    return [];
  }
}

function buildSchema(fields: SchemaField[]) {
  const properties = Object.fromEntries(
    fields.map(field => {
      const entry: Record<string, unknown> = {
        type: field.type,
        description: field.description,
      };
      if (field.type === "string" && field.enumValues.trim().length > 0) {
        entry.enum = field.enumValues.split(",").map(value => value.trim()).filter(Boolean);
      }
      if (field.type === "array") {
        entry.items = { type: "string" };
      }
      return [field.name, entry];
    }),
  );

  const required = fields.filter(field => field.required).map(field => field.name);

  return {
    type: "object" as const,
    properties,
    required,
  };
}

function buildPrompt(basePrompt: string, fields: SchemaField[]) {
  const fieldDescriptions = fields
    .map(field => `- ${field.name}: ${field.description || "(опис відсутній)"}`)
    .join("\n");

  return `${basePrompt.trim()}\n\n${fieldDescriptions}`.trim();
}

export function SettingsPanel({ isOpen, settings, onClose, onSave, onReset }: SettingsPanelProps) {
  const [basePrompt, setBasePrompt] = useState(settings.systemPrompt);
  const [fields, setFields] = useState<SchemaField[]>([]);
  const [editorTarget, setEditorTarget] = useState<SchemaField | null>(null);
  const [isAddingField, setIsAddingField] = useState(false);

  useEffect(() => {
    if (!isOpen) {
      return;
    }

    const lines = settings.systemPrompt.split("\n");
    const firstFieldIndex = lines.findIndex(line => /^-\s+/.test(line));
    const prompt = firstFieldIndex > -1 ? lines.slice(0, firstFieldIndex).join("\n").trim() : settings.systemPrompt;
    setBasePrompt(prompt);
    setFields(parseSchema(settings.jsonSchema));
  }, [isOpen, settings]);

  const schemaPreview = useMemo(() => JSON.stringify(buildSchema(fields), null, 2), [fields]);

  const handleRemoveField = (id: string) => {
    setFields(current => current.filter(field => field.id !== id));
  };

  const handleSaveField = (fieldData: Omit<SchemaField, "id">) => {
    if (isAddingField) {
      const finalName = fieldData.name.trim();
      const uniqueName = fields.some(field => field.name === finalName)
        ? `${finalName}_${fields.length}`
        : finalName;
      setFields(current => [...current, { ...fieldData, name: uniqueName, id: createFieldId() }]);
      setIsAddingField(false);
    } else if (editorTarget) {
      setFields(current => current.map(field => (field.id === editorTarget.id ? { ...field, ...fieldData } : field)));
      setEditorTarget(null);
    }
  };

  const handleSaveSettings = () => {
    try {
      const schema = buildSchema(fields);
      const nextSettings: AgentSettings = {
        systemPrompt: buildPrompt(basePrompt, fields),
        jsonSchema: JSON.stringify(schema, null, 2),
      };
      onSave(nextSettings);
      onClose();
    } catch (error) {
      console.error("Failed to build settings", error);
      window.alert("Не вдалося зберегти налаштування. Перевірте правильність полів.");
    }
  };

  const handleCopySchema = async () => {
    if (!navigator.clipboard) {
      window.alert("Копіювання не підтримується у цьому середовищі.");
      return;
    }
    try {
      await navigator.clipboard.writeText(schemaPreview);
      window.alert("JSON-схема скопійована в буфер обміну.");
    } catch (error) {
      console.error("Failed to copy schema", error);
      window.alert("Не вдалося скопіювати схему.");
    }
  };

  if (!isOpen) {
    return null;
  }

  return (
    <div className="settings-overlay" role="dialog" aria-modal="true">
      <div className="settings-panel">
        <header className="settings-panel__header">
          <h2 className="settings-section__title">Налаштування агента-аналітика</h2>
          <button type="button" className="icon-button" onClick={onClose} aria-label="Close settings">
            ×
          </button>
        </header>

        <div className="settings-panel__body">
          <section className="settings-section">
            <div>
              <h3 className="settings-section__title">Конструктор полів</h3>
              <p className="settings-section__helper">
                Побудуйте JSON-схему, яку використовує аналітик для класифікації повідомлень.
              </p>
            </div>

            <button
              type="button"
              className="button-secondary"
              onClick={() => {
                setIsAddingField(true);
                setEditorTarget(null);
              }}
            >
              + Додати нове поле
            </button>

            <div className="settings-card settings-card__list">
              {fields.length === 0 ? (
                <p className="empty-state" style={{ marginTop: 0 }}>
                  Додайте перше поле, щоб почати.
                </p>
              ) : (
                fields.map(field => (
                  <div key={field.id} className="schema-field">
                    <div className="schema-field__meta">
                      <span className="schema-field__name">{field.name}</span>
                      <span className="schema-field__description">{field.description || "Опис відсутній"}</span>
                      <div className="schema-field__badges">
                        <span className="badge">{field.type}</span>
                        {field.required ? <span className="badge badge--warning">required</span> : null}
                      </div>
                    </div>
                    <div className="schema-field__actions">
                      <button
                        type="button"
                        className="icon-button"
                        onClick={() => {
                          setEditorTarget(field);
                          setIsAddingField(false);
                        }}
                        aria-label="Edit field"
                      >
                        <EditIcon width={18} height={18} />
                      </button>
                      <button
                        type="button"
                        className="icon-button"
                        onClick={() => handleRemoveField(field.id)}
                        aria-label="Remove field"
                      >
                        <TrashIcon width={18} height={18} />
                      </button>
                    </div>
                  </div>
                ))
              )}
            </div>
          </section>

          <section className="settings-section">
            <div className="settings-card">
              <div className="settings-field">
                <label htmlFor="base-prompt">Базова інструкція</label>
                <textarea
                  id="base-prompt"
                  className="textarea-mono"
                  value={basePrompt}
                  rows={8}
                  onChange={event => setBasePrompt(event.target.value)}
                />
                <p className="settings-section__helper">
                  Опис полів буде додано автоматично під час збереження налаштувань.
                </p>
              </div>

              <div className="settings-field">
                <label htmlFor="schema-preview">
                  Підсумкова JSON-схема
                  <button
                    type="button"
                    className="icon-button"
                    style={{ marginLeft: 12 }}
                    onClick={handleCopySchema}
                    aria-label="Copy schema"
                  >
                    <CopyIcon width={18} height={18} />
                  </button>
                </label>
                <pre id="schema-preview" className="analysis-card__json" style={{ maxHeight: 320 }}>
                  {schemaPreview}
                </pre>
              </div>
            </div>
          </section>
        </div>

        <footer className="settings-panel__footer">
          <button type="button" className="button-secondary" onClick={onReset}>
            Скинути до початкових
          </button>
          <button type="button" className="button-secondary" onClick={onClose}>
            Скасувати
          </button>
          <button type="button" className="button-primary" onClick={handleSaveSettings}>
            Зберегти
          </button>
        </footer>
      </div>

      {isAddingField ? (
        <SchemaFieldEditor
          initial={NEW_FIELD_TEMPLATE}
          onSave={handleSaveField}
          onCancel={() => setIsAddingField(false)}
        />
      ) : null}

      {editorTarget ? (
        <SchemaFieldEditor
          initial={{
            name: editorTarget.name,
            type: editorTarget.type,
            description: editorTarget.description,
            enumValues: editorTarget.enumValues,
            required: editorTarget.required,
          }}
          onSave={handleSaveField}
          onCancel={() => setEditorTarget(null)}
        />
      ) : null}
    </div>
  );
}

