import React from 'react';

/**
 * Page shell — wraps every PRAHARI page with a consistent heading and source badge.
 *
 * @param {Object}  props
 * @param {string}  props.title
 * @param {string}  [props.subtitle]
 * @param {boolean} [props.synthetic=false]  - true → show "SYNTHETIC CUF SANDBOX" badge
 * @param {React.ReactNode} props.children
 */
export default function PageShell({ title, subtitle, synthetic = false, children }) {
  return (
    <section className="prahari-shell">
      <div className="pr-heading">
        <div>
          <p className="pr-eyebrow">PAIMANA + PRAHARI INTELLIGENCE</p>
          <h1>{title}</h1>
          {subtitle && <p>{subtitle}</p>}
        </div>
        <div className="pr-source">
          <b>{synthetic ? 'SYNTHETIC CUF SANDBOX' : 'REAL HISTORICAL DATA'}</b>
          <span>
            {synthetic
              ? 'Demonstration data, not official project evidence.'
              : 'Data is retrieved from the PRAHARI service.'}
          </span>
        </div>
      </div>
      {children}
    </section>
  );
}
