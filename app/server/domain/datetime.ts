// SQLite keeps DATETIME columns as free-form text ('YYYY-MM-DD HH:MM:SS', with a
// fractional part and/or a ' +00:00' offset on rows written by SQLAlchemy), while the
// legacy backend handed pydantic a real datetime and serialised it with pydantic's
// RFC 3339 writer. To keep the JSON byte-identical this reproduces that writer:
//   naive                    -> 2026-05-29T02:44:49.324074
//   naive, zero microseconds -> 2026-02-19T15:15:56
//   UTC aware                -> 2022-12-27T03:39:45Z
//   UTC aware + microseconds -> 2023-06-05T16:44:09.620540Z
//   other offset             -> 2023-06-05T16:44:09.620540+08:00

const TIMESTAMP = /^(\d{4}-\d{2}-\d{2})[ T](\d{2}:\d{2}:\d{2})(?:\.(\d+))?\s*(Z|[+-]\d{2}:?\d{2})?$/;

export function toIso(value: string | null | undefined): string | null {
  if (value === null || value === undefined) return null;
  const m = TIMESTAMP.exec(value);
  if (!m) return value; // unknown shape: pass the stored text through untouched

  const [, date, time, fraction, offset] = m;
  // Python prints microseconds only when non-zero, and always as exactly 6 digits.
  const micros = (fraction ?? '').padEnd(6, '0').slice(0, 6);
  const tail = micros === '' || /^0{6}$/.test(micros) ? '' : `.${micros}`;

  let zone = '';
  if (offset) {
    if (offset === 'Z' || offset === '+00:00' || offset === '-00:00' || offset === '+0000') zone = 'Z';
    else if (/^[+-]\d{4}$/.test(offset)) zone = `${offset.slice(0, 3)}:${offset.slice(3)}`;
    else zone = offset;
  }
  return `${date}T${time}${tail}${zone}`;
}
