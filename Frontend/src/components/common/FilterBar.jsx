import React from 'react';

const FILTER_FIELDS = [
  { label: 'Ministry / Dept', key: 'ministry', defaultLabel: 'All Ministries' },
  { label: 'Sector', key: 'sector', defaultLabel: 'All Sectors' },
  { label: 'State / UT', key: 'state', defaultLabel: 'All States / UTs' },
  { label: 'Project Status', key: 'projectStatus', defaultLabel: 'All Projects' },
  { label: 'PRAHARI Review Status', key: 'reviewStatus', defaultLabel: 'All Review Statuses' },
  { label: 'Reporting Month', key: 'reportingMonth', defaultLabel: 'February, 2025' },
];

/**
 * Dashboard filter bar.
 *
 * @param {Object}   props
 * @param {import('../../services/types').FilterOptions} [props.options]   - Dynamic options from backend
 * @param {import('../../services/types').ActiveFilters} [props.filters]   - Controlled filter state
 * @param {function} [props.onChange]   - Called with { key, value } when a filter changes
 * @param {function} [props.onSubmit]   - Called when "Show Data" is clicked
 * @param {function} [props.onReset]    - Called when "Reset" is clicked
 */
export default function FilterBar({ options = {}, filters = {}, onChange, onSubmit, onReset }) {
  function handleChange(key, value) {
    onChange?.({ key, value });
  }

  function handleSubmit(e) {
    e.preventDefault();
    onSubmit?.();
  }

  function handleReset() {
    onReset?.();
  }

  return (
    <form className="pr-filters" onSubmit={handleSubmit} onReset={handleReset}>
      {FILTER_FIELDS.map(({ label, key, defaultLabel }) => {
        const optionList = options[key + 's'] ?? [defaultLabel];
        return (
          <label key={key}>
            {label}
            <select
              value={filters[key] ?? ''}
              onChange={(e) => handleChange(key, e.target.value)}
              aria-label={label}
            >
              <option value="">{defaultLabel}</option>
              {optionList
                .filter((o) => o !== defaultLabel)
                .map((o) => (
                  <option key={o} value={o}>
                    {o}
                  </option>
                ))}
            </select>
          </label>
        );
      })}
      <button className="pr-primary" type="submit">
        ⌕ Show Data
      </button>
      <button className="pr-secondary" type="reset">
        RESET FILTERS
      </button>
    </form>
  );
}
