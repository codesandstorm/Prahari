import React from 'react';

export default function Badge({ value = 'WITHHELD' }) {
  const className = `pr-badge pr-${String(value).toLowerCase().replace(/[^a-z]+/g, '-')}`;
  return <span className={className}>{value}</span>;
}
