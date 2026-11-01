interface Props {
  fields: [label: string, value: string | null | undefined][];
}

/** Label-over-value pairs, the way a classic CRM record shows its details. */
export function FieldGrid({ fields }: Props) {
  return (
    <dl className="fields">
      {fields.map(([label, value]) => (
        <div key={label} className="fields__item">
          <dt>{label}</dt>
          <dd>{value || <span className="muted">Not provided</span>}</dd>
        </div>
      ))}
    </dl>
  );
}
